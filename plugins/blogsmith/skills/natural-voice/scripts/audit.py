#!/usr/bin/env python3
"""블로그 아티클의 AI 생성 패턴 검사기.

  python3 audit.py article.md [article2.md ...]

문체 문서(styles/)가 정하는 것은 검사하지 않는다.
이모지, 종결어미, 존댓말 여부는 사람마다 다르므로 여기서 판정할 수 없다.
이 스크립트가 보는 것은 문체와 무관하게 AI 티가 나는 지점이다.
"""
import re
import sys
import statistics

# 문장 길이 편차. 구조 다양성(burstiness)이 가장 크게 갈리는 지표다.
CV_MIN = 0.35        # 변동계수(표준편차/평균) 하한
RATIO_MIN = 3.0      # 최장 문장 / 최단 문장

EMDASH_PER_1000 = 1.0
BOLD_RATIO_MAX = 12.0

BANNED = {
    "번역투": r"(에 대한|에 있어서|을 통해|를 통해|로 인해|되어지|하게 되었)",
    "헤지": r"(라고 할 수 있|인 것 같습니다|로 보입니다|하는 듯합니다)",
    "공허한 부사": r"(성공적으로|효과적으로|효율적으로|체계적으로|적극적으로|지속적으로)",
    "부풀리기": r"(놀라운|완벽한|최고의|강력한|혁신적|획기적|압도적|무려)",
    "얼버무린 출처": r"(일반적으로|대부분의 경우|흔히 |전문가들은|알려져 있)",
    "서두 상투구": r"(살펴보겠습니다|알아보겠습니다|소개해 ?드리겠습니다)",
    "마무리 상투구": r"(결론적으로|정리하자면|마무리하며|이상으로)",
    "뻔한 수식": r"(맛있는 (?:커피|음식)|아늑한 분위기|친절한 직원|가성비가 좋)",
}

DENSITY = {
    "~뿐만 아니라": (r"(?:뿐(?:만)? 아니라|에 그치지 않)", 1),
    "대조 구문 (X가 아니라 Y)": (r"(?:가|이|은|는|을|를)\s*아니(?:라|고|며)", 2),
    "문두 접속사": (r"(?m)^\s*(?:[-*>]\s*)?(?:그리고|그러나|또한|하지만|따라서|즉|한편)[ ,]", 3),
}


def strip_code(text):
    """코드블록과 인라인 코드를 뺀다.

    인라인 코드는 산문이 아니라 표기 대상이다.
    금지 패턴을 설명하는 문서에서 `—` 같은 예시를 위반으로 세면 안 된다.
    """
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", " ", text)


def strip_meta(text):
    """표, 코드, HTML, 헤딩, 이미지, 링크 URL 을 뺀 산문."""
    text = strip_code(text)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\]\([^)]*\)", "] ", text)
    lines = [l for l in text.split("\n")
             if not l.lstrip().startswith(("|", "#", "---", "==="))]
    return "\n".join(lines)


def sentences(prose):
    """문장 단위로 쪼갠다. 목록 항목은 문장으로 세지 않는다."""
    out = []
    for line in prose.split("\n"):
        s = line.strip()
        if not s or s.startswith(("-", "*", ">", "|")):
            continue
        for seg in re.split(r"(?<=[.!?])\s+", s):
            seg = re.sub(r"[*_`]", "", seg).strip()
            if len(seg) >= 8:
                out.append(seg)
    return out


def check_burstiness(sents):
    """문장 길이가 고르면 AI 신호다. 사람은 짧게 끊었다가 길게 쓴다."""
    if len(sents) < 5:
        return [], "문장 5개 미만이라 판정하지 않음"
    lens = [len(s) for s in sents]
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    ratio = max(lens) / min(lens)
    problems = []
    if cv < CV_MIN:
        problems.append(f"[편차] 문장 길이 변동계수 {cv:.2f} (하한 {CV_MIN})")
    if ratio < RATIO_MIN:
        problems.append(f"[편차] 최장/최단 비율 {ratio:.1f}배 (하한 {RATIO_MIN}배)")
    detail = (f"평균 {mean:.0f}자, 변동계수 {cv:.2f}, "
              f"최단 {min(lens)}자 최장 {max(lens)}자 ({ratio:.1f}배)")
    return problems, detail


def check_list_sizes(raw):
    """목록 항목 수가 전부 3개면 AI 신호다."""
    sizes, cur = [], 0
    for line in raw.split("\n") + [""]:
        if re.match(r"^\s*(?:[-*]|\d+\.)\s+\S", line):
            cur += 1
        else:
            if cur:
                sizes.append(cur)
            cur = 0
    if len(sizes) >= 3 and len(set(sizes)) == 1 and sizes[0] == 3:
        return [f"[구조] 목록 {len(sizes)}개가 전부 3항목"], sizes
    return [], sizes


def check_concreteness(prose):
    """숫자와 고유명사가 없는 문단은 추상적이다. 예측 용이성이 높아진다."""
    empty, total = [], 0
    for para in re.split(r"\n\s*\n", prose):
        p = para.strip()
        if len(p) < 60 or p.startswith(("-", "*", ">", "|")):
            continue
        total += 1
        if not re.search(r"[0-9]|[A-Za-z]{2,}", p):
            empty.append(p[:50])
    return empty, total


def audit(path):
    raw = open(path, encoding="utf-8").read()
    prose = strip_meta(raw)
    sents = sentences(prose)
    problems = []

    print(f"\n{'=' * 66}\n{path}\n{'=' * 66}")

    probs, detail = check_burstiness(sents)
    problems += probs
    print(f"  {'[X]' if probs else '[o]'} 구조 다양성{'':<12} {detail}")

    chars = len(re.sub(r"\s", "", prose)) or 1

    n = len(re.findall(r"[—–]", strip_code(raw)))
    per1000 = n / chars * 1000
    if per1000 > EMDASH_PER_1000:
        problems.append(f"[서식] em dash {n}건 (1000자당 {per1000:.1f})")
        print(f"  [X] em dash{'':<17} {n}건  1000자당 {per1000:.1f}  상한 {EMDASH_PER_1000}")
    elif n:
        print(f"  [!] em dash{'':<17} {n}건")

    # 줄 맨 앞 굵게는 항목 라벨이라 산문 강조로 세지 않는다.
    emph = []
    for ln in prose.split("\n"):
        s = ln.strip()
        for m in re.finditer(r"\*\*(.+?)\*\*", s):
            if s[:m.start()].strip(" -·*>0123456789."):
                emph.append(m.group(1))
    ratio = len(re.sub(r"\s", "", "".join(emph))) / chars * 100
    if ratio > BOLD_RATIO_MAX:
        problems.append(f"[서식] 문중 굵게 {ratio:.1f}% (상한 {BOLD_RATIO_MAX}%)")
    print(f"  {'[X]' if ratio > BOLD_RATIO_MAX else '[o]'} 굵게 밀도{'':<14} "
          f"{ratio:4.1f}%  (문중 {len(emph)}개)  상한 {BOLD_RATIO_MAX}%")

    probs, sizes = check_list_sizes(raw)
    problems += probs
    if sizes:
        print(f"  {'[X]' if probs else '[o]'} 목록 항목 수{'':<11} {sizes}")

    empty, total = check_concreteness(prose)
    if empty:
        problems.append(f"[구체성] 숫자와 고유명사가 없는 문단 {len(empty)}/{total}건")
        print(f"  [X] 구체성{'':<16} {len(empty)}/{total} 문단에 숫자와 고유명사 없음")
        for e in empty[:3]:
            print(f"        {e}...")
    elif total:
        print(f"  [o] 구체성{'':<16} {total} 문단 모두 검증 가능한 요소 있음")

    for name, pat in BANNED.items():
        found = re.findall(pat, prose)
        if found:
            problems.append(f"[어휘] {name} {len(found)}건")
            print(f"  [X] {name:<20} {len(found)}건  {sorted(set(map(str, found)))[:4]}")

    for name, (pat, cap) in DENSITY.items():
        n = len(re.findall(pat, prose))
        if n > cap:
            problems.append(f"[밀도] {name} {n}건 (상한 {cap})")
            print(f"  [X] {name:<20} {n}건  상한 {cap}")

    # 종결 분포는 보고만 한다. 판정은 문체 문서가 할 몫이다.
    hon = len(re.findall(r"(?:습니다|입니다|해요|예요|네요)[.\s]*$", prose, re.M))
    pla = len(re.findall(r"(?:했다|한다|된다|이다|없다|같다)[.\s]*$", prose, re.M))
    if hon or pla:
        print(f"  [ ] 종결 분포{'':<13} 존댓말 {hon} / 평서 {pla}  (문체 문서가 정함)")

    print(f"\n  == {'통과' if not problems else str(len(problems)) + '건 검토 필요'}")
    return problems


if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(1)
    total = sum(len(audit(f)) for f in args)
    print(f"\n{'=' * 66}\n전체 {len(args)}개 문서 / 검토 항목 {total}건")
    sys.exit(1 if total else 0)
