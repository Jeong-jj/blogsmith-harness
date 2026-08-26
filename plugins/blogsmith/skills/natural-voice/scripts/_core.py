#!/usr/bin/env python3
"""AI 문체 검사 계산부.

여기에는 **글 종류를 가리지 않는 것**만 둔다.
텍스트 전처리, 문장 통계, 어디서나 통하는 절대 규칙과 금지 어휘가 해당된다.

무엇을 위반으로 볼지는 판정부인 `audit.py`가 정한다.
임계값도 여기 박지 않고 인자로 받는다. 블로그에 맞춰 조정할 값을 여기 두면
조정할 때마다 계산부를 건드리게 되기 때문이다.

여기를 고치면 검사 전체의 판정값이 움직인다. 고치기 전에 리팩터 전후를 대조한다.
"""
import re
import statistics

# ---------- 절대 규칙: 1건이라도 있으면 위반 ----------
# em dash 는 한국어 타자 환경에서 자연 입력되지 않는다. 문서에 있다는 것 자체가
# 생성 도구를 거쳤다는 증거다. 곡선 따옴표도 같은 이유다.
HARD = {
    "em dash —": r"—",
    "en dash –": r"–",
    "곡선 따옴표 “ ”": r"[“”]",
    "곡선 아포스트로피 ’": r"[‘’]",
    "줄임표 …": r"…",
    "장식 이모지": r"[\U0001F300-\U0001FAFF☀-➿]",
}
# 의미가 고정된 기능 마커는 장식이 아니다. 같은 뜻으로 일관되게 쓰이면 허용한다.
# 📎 상세링크 · 💡 설계판단 · ✅ 완료 · ⏳ 대기 · ⬜🔲 미완 · ⚠ 주의 · ❌ 나쁜예 · ★ 선정
EMOJI_OK = set("📎💡✅⏳⬜🔲⚠❌★")

# ---------- 금지 어휘 ----------
# 문장에서 지워도 뜻이 안 변하면 그 단어는 없어도 된다.
# 한 번이라도 걸린 표현은 전부 여기 모은다. 글 종류가 달라도 안 쓸 이유가 없다.
BANNED = {
    "공허한 부사": r"(성공적으로|효과적으로|효율적으로|체계적으로|적극적으로|지속적으로|원활[히하]|손쉽게)",
    "부풀리기": r"(혁신적|획기적|핵심적인 역할|결정적인|극대화|압도적|비약적|무려|놀라운|완벽한|최고의|강력한)",
    "헤지": r"(라고 할 수 있|인 편입니다|인 것 같습니다|로 보입니다|것으로 사료|하는 듯합니다)",
    "얼버무린 출처": r"(일반적으로|대부분의 경우|흔히 |전문가들은|알려져 있)",
    "서두 상투구": r"(살펴보겠습니다|알아보겠습니다|소개해 ?드리겠습니다|상상해 ?보세요|정리해 ?보겠습니다)",
    # `이상으로` 는 문장을 닫을 때만 상투구다. "5개 이상으로 늘고" 같은 수량 표현을
    # 잡지 않도록 뒤따르는 마무리 동사까지 함께 본다.
    "마무리 상투구": r"(결론적으로|이를 통해|시사하는 바가|기대됩니다|중요합니다\.|정리하자면|마무리하며|이상으로 (?:마치|줄이|글을))",
    # `에 대한` 은 넣지 않는다. 너무 넓어 정상 문장을 잡는다.
    "번역투": r"(에 있어서|에 대한 이해|을 통해|를 통해|로 인해|되어지|하게 되었)",
    "다양한+개수없음": r"다양한 [가-힣]+(?![0-9])",
}

# ---------- 밀도 규칙: (패턴, 2,000자당 상한) ----------
# 구문 자체가 나쁜 게 아니라 밀도가 문제다. 상한은 분량에 비례해 환산한다.
DENSITY = {
    "대조 구문 (X가 아니라 Y)": (r"(?:가|이|은|는|을|를|에|로|도|게|것)\s*아니(?:라|다|고|며|었|지만)", 2),
    "~뿐만 아니라 / ~에 그치지 않": (r"(?:뿐(?:만)? 아니라|에 그치지 않|단순히)", 1),
}


# ---------- 전처리 ----------

def strip_code(text):
    """코드블록과 인라인 코드를 뺀다.

    인라인 코드는 산문이 아니라 표기 대상이다.
    금지 패턴을 설명하는 문서에서 `—` 같은 예시를 위반으로 세면 안 된다.
    """
    text = re.sub(r"```.*?```", " ", text, flags=re.S)
    return re.sub(r"`[^`\n]*`", " ", text)


def strip_frontmatter(text):
    """맨 앞 YAML 프론트매터를 뺀다.

    `---` 구분선은 헤딩 필터에 걸려 사라지지만 `key: value` 줄은 산문으로 남는다.
    프론트매터는 메타데이터지 필자가 쓴 문장이 아니고, 여러 줄이 빈 줄 없이
    붙어 있어 문장 분리에서 하나의 긴 문장으로 합쳐진다. 그러면 최장 문장 길이가
    부풀어 문장 길이 편차가 실제보다 높게 나온다.
    """
    return re.sub(r"\A---\r?\n.*?\r?\n---\r?\n", "", text, flags=re.S)


def strip_meta(text):
    """표, 코드, HTML, 헤딩, 이미지, 링크 URL 을 뺀 산문."""
    text = strip_code(strip_frontmatter(text))
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[[^\]]*\]\([^)]*\)", " ", text)
    text = re.sub(r"\]\([^)]*\)", "] ", text)
    lines = [l for l in text.split("\n")
             if not l.lstrip().startswith(("|", "#", "---", "==="))]
    return "\n".join(lines)


def drop_quoted(text):
    """따옴표로 감싼 대사를 뺀다. 인용 안의 어미는 화자의 말이지 필자의 문체가 아니다.

    **`prose_only` 와 지우는 대상이 다르다.** 이쪽은 줄 안의 `"..."` 구간만 도려내고
    `>` 로 시작하는 인용블록은 그대로 남긴다. 반대로 `prose_only` 는 `>` 줄을 통째로
    없애고 따옴표는 건드리지 않는다. 인용 전반을 빼려면 둘을 겹쳐 써야 한다.

        drop_quoted(prose_only(raw))

    `[^"\n]` 이 줄바꿈과 다음 따옴표를 막으므로 한 구간이 줄을 넘거나 서로 다른
    인용을 삼키지 않는다. 길이 상한을 두지 않는 이유가 이것이다. 예전에 80자로
    막아뒀더니 긴 인용문이 필자 글로 세어졌다.
    """
    text = re.sub(r"\*\"[^\"\n]*\"\s*\*", " ", text)
    return re.sub(r"\"[^\"\n]{2,}\"", " ", text)


def prose_only(text):
    """인용블록까지 뺀 순수 본문."""
    return "\n".join(l for l in strip_meta(text).split("\n")
                     if not l.lstrip().startswith(">"))


# ---------- 통계 ----------

def sentences(body):
    """문장 단위로 쪼갠다. 목록 항목과 표는 문장으로 세지 않는다.

    **문단 안의 줄을 먼저 합친 뒤** 문장으로 나눈다. 산문을 80~90칸에서 접어 쓰면
    줄 단위로 세었을 때 한 문장이 여러 개로 쪼개져, 문장 길이가 아니라
    줄바꿈 폭을 재게 된다.
    """
    out = []
    for para in re.split(r"\n\s*\n", body):
        lines = [l.strip() for l in para.split("\n")
                 if l.strip() and not l.strip().startswith(("-", "*", ">", "|", "#"))]
        if not lines:
            continue
        for seg in re.split(r"(?<=[.!?])\s+", " ".join(lines)):
            seg = re.sub(r"[*_`]", "", seg).strip()
            if len(seg) >= 8:
                out.append(seg)
    return out


def check_burstiness(sents, cv_min, ratio_min):
    """문장 길이가 고르면 기계가 쓴 신호다. 사람은 짧게 끊었다가 길게 쓴다."""
    if len(sents) < 5:
        return [], "문장 5개 미만이라 판정하지 않음"
    lens = [len(s) for s in sents]
    mean = statistics.mean(lens)
    cv = statistics.pstdev(lens) / mean if mean else 0
    ratio = max(lens) / min(lens)
    problems = []
    if cv < cv_min:
        problems.append(f"[편차] 문장 길이 변동계수 {cv:.2f} (하한 {cv_min})")
    if ratio < ratio_min:
        problems.append(f"[편차] 최장/최단 비율 {ratio:.1f}배 (하한 {ratio_min}배)")
    detail = (f"평균 {mean:.0f}자, 변동계수 {cv:.2f}, "
              f"최단 {min(lens)}자 최장 {max(lens)}자 ({ratio:.1f}배)")
    return problems, detail


def check_list_sizes(raw):
    """목록 항목 수가 전부 3개면 기계가 쓴 신호다."""
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


def bold_ratio(body):
    """문중 굵게 비율(%)과 (문중, 라벨) 목록.

    줄 맨 앞의 굵게는 항목 라벨(`**Frontend** Vue 3`)이라 헤딩에 준하는 구조
    표시이므로 산문 강조로 세지 않는다. 문장 중간에서 시작하는 것만 센다.
    """
    emph, label = [], []
    for ln in body.split("\n"):
        s = ln.strip()
        for m in re.finditer(r"\*\*(.+?)\*\*", s):
            head = s[:m.start()].strip(" -·*>0123456789.")
            (label if head == "" else emph).append(m.group(1))
    chars = len(re.sub(r"\s", "", body)) or 1
    return len(re.sub(r"\s", "", "".join(emph))) / chars * 100, emph, label, chars


# 화제가 바뀌는 자리. 여기서 이어붙이기를 끊는다.
BLOCK_START = ("-", "*", ">", "|", "#", "!")


def check_concreteness(body, floor=60):
    """숫자도 고유명사도 없는 문단은 비어 있다. 예측 가능한 말만 남는다.

    영문은 **한 글자부터** 센다. `M` `O` 같은 사이즈 표기와 등급, 모델명이
    한 글자로 온다. 한국어 산문에서 단독 라틴 문자는 대개 그런 값이다.
    두 글자로 잡으면 `M은 미디엄, O는 오리지널이다` 가 빈 문단으로 잡힌다.

    **빈 줄로 갈린 덩어리를 그대로 문단으로 보지 않는다.**
    문단 안을 빈 줄로 다시 나누는 문체가 있다. 그런 글은 덩어리가 1~2줄이라
    거의 전부가 문턱 아래로 떨어져 검사가 비어버린다.
    실제 산출물에서 덩어리 37개 중 33개가 검사 밖이었다.

    그래서 짧은 덩어리를 문턱에 닿을 때까지 이어붙여 한 단위로 본다.
    소제목, 사진, 구분선, 목록, 표를 만나면 거기서 끊는다.

    **문턱을 낮추는 것과 다르다.** 낮추면 `안쪽은 바삭하고 바깥은 부드럽다` 같은
    짧은 감각 묘사가 단독으로 걸려 오탐이 쏟아진다. 이어붙이면 앞뒤와 함께 판정된다.

    반환값은 (비어 있는 단위 목록, 검사 대상 수)다. 분모를 함께 주는 이유는
    9건이 많은지 적은지가 전체 수에 달렸기 때문이고, 호출부가 분모를 따로
    세면 여기 거르는 기준과 어긋난다.

    **한글 고유명사는 여전히 못 센다.** `고든램지` 가 든 단위가 비어 있다고 잡힌다.
    사전 없이는 일반 명사와 갈리지 않는다. 에이전트가 결과를 읽고 거른다.
    """
    empty, total, buf = [], 0, []

    def close():
        nonlocal total
        if not buf:
            return
        unit = " ".join(buf)
        buf.clear()
        if len(unit) < floor:
            return
        total += 1
        if not re.search(r"[0-9]|[A-Za-z]", unit):
            empty.append(unit[:60])

    for para in re.split(r"\n\s*\n", body):
        p = " ".join(l.strip() for l in para.strip().split("\n") if l.strip())
        if not p:
            continue
        if p.startswith(BLOCK_START):
            close()
            continue
        buf.append(p)
        if len(" ".join(buf)) >= floor:
            close()
    close()
    return empty, total


def hard_hits(raw):
    """절대 규칙 위반. 인라인 코드 안의 표기 예시는 위반이 아니다."""
    nocode = strip_code(raw)
    out = []
    for name, pat in HARD.items():
        hits = [m for m in re.findall(pat, nocode) if m not in EMOJI_OK]
        if hits:
            out.append((name, len(hits)))
    return out


def density_scale(prose):
    """밀도 상한 배수. 기준은 제출본 1장(약 2,000자)."""
    return max(1, round(len(re.sub(r"\s", "", prose)) / 2000))


def overlap_ratio(a_text, b_text, n=14):
    """a 가 b 와 겹치는 비율(%)과 연속 구간 목록. 계층 문서 프랙탈 반복 검사용."""
    def norm(t):
        return re.sub(r"\s+", "", re.sub(r"[*`>|#\-]", " ", strip_meta(t)))
    A, B = norm(a_text), norm(b_text)
    g = {B[i:i + n] for i in range(len(B) - n)}
    hit = [i for i in range(len(A) - n) if A[i:i + n] in g]
    pct = len(hit) / max(len(A) - n, 1) * 100
    runs, cur = [], 0
    for i in range(len(A) - n):
        if A[i:i + n] in g:
            cur += 1
        else:
            if cur > 40:
                runs.append((A[i - cur:i + n], cur))
            cur = 0
    return pct, runs
