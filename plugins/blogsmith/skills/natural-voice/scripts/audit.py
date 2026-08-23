#!/usr/bin/env python3
"""블로그 아티클의 AI 생성 패턴 검사기.

  python3 audit.py article.md [article2.md ...]

전처리와 문장 통계, 어디서나 통하는 절대 규칙과 금지 어휘는 `_core.py`에 있다.
글 종류를 가리지 않는 계산부라 여기서 고치지 않는다.

이 파일에는 블로그에만 해당하는 것을 둔다.
문체 문서(styles/)가 정하는 것은 판정하지 않는다.
종결어미, 존댓말, 이모지는 사람마다 다르므로 여기서 옳고 그름을 가릴 수 없다.
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _core as core

# 임계값은 코어에 박지 않고 여기서 넘긴다.
# 블로그에 맞춰 조정할 값이라 계산부가 아니라 판정부에 있어야 한다.
CV_MIN = 0.35        # 문장 길이 변동계수(표준편차/평균) 하한
RATIO_MIN = 3.0      # 최장 문장 / 최단 문장
BOLD_RATIO_MAX = 12.0

# 절대 규칙 중 문체 문서의 소관인 것. 위반으로 세지 않고 보고만 한다.
# 이모지를 쓸지 말지는 그 사람의 문체다. 종결 분포와 같은 이유로 여기서 판정하지 않는다.
HARD_REPORT_ONLY = {"장식 이모지"}

# 코어 목록에 블로그 리뷰 표현만 더한다.
BANNED = dict(core.BANNED)
BANNED["뻔한 수식"] = r"(맛있는 (?:커피|음식)|아늑한 분위기|친절한 직원|가성비가 좋)"

# 문두 접속사는 블로그에서만 밀도로 다룬다. 구어체라 여유를 둔다. 의도된 차이다.
DENSITY = dict(core.DENSITY)
DENSITY["문두 접속사"] = (
    r"(?m)^\s*(?:[-*>]\s*)?(?:그리고|그러나|또한|하지만|따라서|즉|한편)[ ,]", 3)

# 대제목으로 본 인용블록의 길이 상한. 학습한 문체의 관찰값이 5~26자였다.
HEADING_MAX = 45


def quoted_line(q):
    """인용블록 한 줄이 남의 말인가.

    블로그에서 `>` 는 남의 말이라는 보장이 없다. 네이버 인용 컴포넌트가
    대제목으로 쓰이고 속마음을 감싸기도 한다. 그래서 기호가 아니라 모양으로 가른다.

    남의 말은 문장이라 종결어미와 마침표로 닫힌다.
    대제목은 명사구나 의문문이라 마침표로 닫지 않는다.
    """
    return (q.startswith("출처:")
            or q.endswith(".")
            or bool(re.search(r"(?:습니다|입니다|이다|한다|했다|이에요|예요)\.?$", q))
            or len(q) > HEADING_MAX)


def split_blockquotes(prose):
    """(남의 말 줄을 뺀 글, 뺀 줄 목록). 판정을 화면에 찍어 눈에 보이게 한다."""
    keep, theirs = [], []
    for ln in prose.split("\n"):
        s = ln.lstrip()
        if s.startswith(">"):
            q = s.lstrip("> ").strip()
            if q and quoted_line(q):
                theirs.append(q)
                continue
        keep.append(ln)
    return "\n".join(keep), theirs


def audit(path):
    """검사마다 보는 범위가 다르다. 넷을 만들어 두고 골라 쓴다.

    raw        파일 그대로. 절대 규칙과 목록 구조가 쓴다.
               em dash 는 인용 안에 있어도 위반이다. 붙여넣은 것 자체가 증거다.
    prose      표, 코드, 헤딩, 링크를 뺀 것. 서식 검사가 쓴다.
    body       인용블록까지 뺀 것. 문단 단위 판정인 구체성이 쓴다.
    own_words  큰따옴표 대사를 뺀 것. 줄 단위로 훑는 어휘와 밀도가 쓴다.

    **블로그에서 `>` 는 남의 말이라는 보장이 없다.** 네이버 인용 컴포넌트가
    대제목으로 쓰이고 속마음을 인용으로 감싸기도 한다. 학습해 둔 문체에서도
    인용 블록 대부분이 대제목이었고 진짜 인용은 5편 통틀어 1건이었다.

    그래서 기호로 자르지 않고 `quoted_line` 이 모양을 보고 가른다.
    통째로 빼면 대제목에 넣은 상투구가 면제되고, 통째로 남기면 진짜 인용이
    오탐으로 잡힌다. 둘 다 피하려면 줄마다 판정해야 한다.

    판정 결과는 화면에 찍는다. 휴리스틱이라 틀릴 수 있는데,
    무엇을 뺐는지 보이지 않으면 조용히 면제되는 것과 같아진다.

    구체성은 인용블록을 전부 뺀다. 문단 단위 판정이라 대제목은 60자 문턱에
    걸리지 않고, 남의 말을 옮긴 문단에서 숫자를 빌려오면 안 되기 때문이다.
    """
    raw = open(path, encoding="utf-8").read()
    prose = core.strip_meta(raw)
    body = core.prose_only(raw)
    kept, theirs = split_blockquotes(prose)
    own_words = core.drop_quoted(kept)

    sents = core.sentences(body)
    problems = []

    print(f"\n{'=' * 66}\n{path}\n{'=' * 66}")

    probs, detail = core.check_burstiness(sents, CV_MIN, RATIO_MIN)
    problems += probs
    print(f"  {'[X]' if probs else '[o]'} 구조 다양성{'':<12} {detail}")

    # 밀도 배수는 실제로 훑는 분량으로 잰다. 훑지 않는 대사까지 분모에 넣으면
    # 배수만 커지고 범위는 그대로라 상한이 헐거워진다. 분자와 분모가 같은 글이어야 한다.
    scale = core.density_scale(own_words)
    chars = len(re.sub(r"\s", "", own_words)) or 1
    print(f"  [ ] 분량{'':<17} {chars}자 (남의 말 제외)  밀도 상한 배수 x{scale}")

    if theirs:
        print(f"  [ ] 인용 판정{'':<13} {len(theirs)}줄을 남의 말로 보고 어휘·밀도에서 제외")
        for q in theirs[:2]:
            print(f"        {q[:52]}")

    for name, n in core.hard_hits(raw):
        if name in HARD_REPORT_ONLY:
            print(f"  [ ] {name:<20} {n}건  (문체 문서가 정함)")
            continue
        problems.append(f"[서식] {name} {n}건")
        print(f"  [X] {name:<20} {n}건  1건이라도 있으면 위반")

    # 굵게는 prose 로 잰다. 인용 안의 굵게도 필자가 넣은 서식이기 때문이다.
    # 인용문을 가져올 때 굵게까지 그대로 옮기는 사람은 없다. 강조는 옮긴 사람이 한다.
    ratio, emph, _label, _chars = core.bold_ratio(prose)
    if ratio > BOLD_RATIO_MAX:
        problems.append(f"[서식] 문중 굵게 {ratio:.1f}% (상한 {BOLD_RATIO_MAX}%)")
    print(f"  {'[X]' if ratio > BOLD_RATIO_MAX else '[o]'} 굵게 밀도{'':<14} "
          f"{ratio:4.1f}%  (문중 {len(emph)}개)  상한 {BOLD_RATIO_MAX}%")

    probs, sizes = core.check_list_sizes(raw)
    problems += probs
    if sizes:
        print(f"  {'[X]' if probs else '[o]'} 목록 항목 수{'':<11} {sizes}")

    # 구체성은 필자가 쓴 산문에 검증 가능한 요소가 있는지를 묻는다.
    # 남의 말을 옮긴 부분에서 숫자를 빌려오면 안 된다.
    empty, total = core.check_concreteness(body)
    if empty:
        problems.append(f"[구체성] 숫자와 고유명사가 없는 문단 {len(empty)}/{total}건")
        print(f"  [X] 구체성{'':<16} {len(empty)}/{total} 문단에 숫자와 고유명사 없음")
        for e in empty[:3]:
            print(f"        {e}...")
    elif total:
        print(f"  [o] 구체성{'':<16} {total} 문단 모두 검증 가능한 요소 있음")

    # 금지 어휘에서 대사만 뺀다. 잡히면 고치라는 뜻인데 남의 말은 고칠 수 없고
    # 다듬으면 오인용이 된다. 인용블록은 남긴다. 위 독스트링의 이유다.
    for name, pat in BANNED.items():
        found = re.findall(pat, own_words)
        if found:
            problems.append(f"[어휘] {name} {len(found)}건")
            print(f"  [X] {name:<20} {len(found)}건  {sorted(set(map(str, found)))[:4]}")

    for name, (pat, cap) in DENSITY.items():
        n = len(re.findall(pat, own_words))
        lim = cap * scale
        if n > lim:
            problems.append(f"[밀도] {name} {n}건 (상한 {lim})")
            print(f"  [X] {name:<20} {n}건  상한 {cap}x{scale}={lim}")

    # 종결 분포는 보고만 한다. 판정은 문체 문서가 할 몫이다.
    # 인용 안의 어미는 화자의 말이라 필자의 종결로 세지 않는다.
    hon = len(re.findall(r"(?:습니다|입니다|해요|예요|네요)[.\s]*$", own_words, re.M))
    pla = len(re.findall(r"(?:했다|한다|된다|이다|없다|같다)[.\s]*$", own_words, re.M))
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
