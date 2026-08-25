#!/usr/bin/env python3
"""블로그 글 하나를 받아 구조를 남긴 텍스트로 뽑는다.

  python3 fetch-post.py <url>

문체 분석에는 본문 글자만으로 부족하다.
소제목의 계층, 사진이 몇 번째 문단 뒤에 오는지, 캡션이 달렸는지,
구분선이 몇 번 나오는지가 전부 문체의 일부다.
그래서 태그를 지우지 않고 마커로 바꿔 남긴다.

출력 형식:

  [H1] 대제목
  [H2] 소제목
  [P] 문단 첫 줄
  [P-] 같은 문단의 이어지는 줄
  [BR] 문단 안의 빈 줄
  [IMG] 사진 (캡션: ...)
  [HR] 구분선
  [QUOTE] 인용
  [LIST] 목록 항목
  [CARD] 링크 카드나 지도
  [STICKER] 스티커

## 신분을 밝히고 받는다

브라우저인 척하지 않는다. blogsmith 라고 밝히고 저장소 주소를 함께 보낸다.
받아주면 쓰고, 막으면 물러난다. 판단 기준을 단순하게 두려는 것이다.

플랫폼별 방침은 같은 디렉토리의 domains.md 에 정리해 뒀다.

네이버는 본문이 iframe 안이라 PostView.naver 주소로 바꿔 요청한다.
"""
import html
import re
import subprocess
import sys
from urllib.parse import urlparse, parse_qs

UA = "blogsmith/0.1 (+https://github.com/Jeong-jj/blogsmith-harness)"


def to_fetchable(url):
    """네이버 블로그 주소를 본문이 담긴 주소로 바꾼다."""
    u = urlparse(url)
    if "blog.naver.com" not in u.netloc:
        return url
    if "PostView" in u.path:
        return url
    parts = [p for p in u.path.split("/") if p]
    if len(parts) >= 2 and parts[-1].isdigit():
        return (f"https://blog.naver.com/PostView.naver"
                f"?blogId={parts[-2]}&logNo={parts[-1]}")
    q = parse_qs(u.query)
    if "blogId" in q and "logNo" in q:
        return (f"https://blog.naver.com/PostView.naver"
                f"?blogId={q['blogId'][0]}&logNo={q['logNo'][0]}")
    return url


def fetch(url):
    r = subprocess.run(["curl", "-sL", "-A", UA, url],
                       capture_output=True, text=True, timeout=30)
    if r.returncode != 0 or len(r.stdout) < 500:
        raise RuntimeError(f"받지 못했습니다: {url}")
    return r.stdout


def close_of(doc, start):
    """start 위치에서 열린 div 의 짝이 되는 </div> 앞까지의 끝 위치를 준다.

    `(.*)` 로 잡으면 문서 끝까지 딸려온다. 본문 뒤의 CCL 고지, 태그 입력란,
    공감 버튼이 전부 본문으로 세어져서 사진 수와 문단 수가 부풀었다.
    """
    depth = 0
    for m in re.finditer(r"<div\b|</div\s*>", doc[start:], re.I):
        if m.group(0)[1] != "/":
            depth += 1
        else:
            depth -= 1
            if depth == 0:
                return start + m.start()
    return len(doc)


def main_container(doc):
    """본문 영역만 남긴다. 못 찾으면 전체를 쓴다."""
    for pat in (r'<div[^>]*class="[^"]*se-main-container[^"]*"[^>]*>',
                r'<div[^>]*id="postViewArea"[^>]*>'):
        m = re.search(pat, doc, re.I)
        if m:
            return doc[m.end():close_of(doc, m.start())]
    m = re.search(r'<article[^>]*>(.*?)</article>', doc, re.S | re.I)
    if m:
        return m.group(1)
    return doc


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("​", "")
    return re.sub(r"\s+", " ", s).strip()


BOLD = r"<(b|strong)\b|font-weight:\s*bold"


def text_lines(c):
    """텍스트 컴포넌트를 눈에 보이는 줄 단위로 쪼갠다.

    스마트에디터 ONE 은 화면의 한 줄이 se-text-paragraph 하나다.
    줄 정보가 개행 문자가 아니라 태그에 들어 있어서,
    clean() 이 태그를 지우기 전에 여기서 먼저 갈라야 한다.

    빈 p 는 엔터 두 번이다. 문단 안에서 덩어리를 나누는 간격이라 버리지 않는다.
    굵게는 줄마다 따로 본다. 한 문단의 앞 절반만 굵은 경우가 흔하다.
    """
    parts = re.findall(
        r'<p[^>]*class="[^"]*(?<![\w-])se-text-paragraph(?![\w-])[^"]*"[^>]*>(.*?)</p>',
        c, re.S | re.I)
    if not parts:
        parts = re.findall(r"<p\b[^>]*>(.*?)</p>", c, re.S | re.I)
    if not parts:
        parts = [c]

    # p 안의 br 도 줄이다. 네이버는 한 줄이 p 하나지만 마크다운 계열은
    # 한 문단이 p 하나고 그 안을 br 로 끊는다. 여기서 갈라야 양쪽이 같아진다.
    lines = []
    for x in parts:
        pieces = [(clean(y), bool(re.search(BOLD, y, re.I)))
                  for y in re.split(r"<br\s*/?>", x, flags=re.I)]
        # 통째로 빈 p 는 빈 줄 하나다. br 로 갈라 둘로 세지 않는다.
        if any(t for t, _ in pieces):
            lines.extend(pieces)
        else:
            lines.append(("", any(b for _, b in pieces)))
    return lines


def extract(doc):
    body = main_container(doc)
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", body, flags=re.S | re.I)

    out = []
    # 컴포넌트 단위로 자른다. 스마트에디터는 se-component 로 문단을 감싼다.
    # se-component 를 정확히 그 클래스 이름일 때만 잡는다.
    # 경계가 없으면 안쪽의 se-component-content 에도 걸려 컴포넌트가 둘로 잘리고,
    # 앞 조각이 img 없이 클래스만 남아 [IMG x1] 유령을 만든다.
    chunks = re.split(
        r'(?=<div[^>]*class="[^"]*(?<![\w-])se-component(?![\w-])[^"]*")', body)
    # 컴포넌트가 하나도 없을 때만 물러난다. 네이버가 아닌 HTML 이다.
    # 하나라도 잡혔으면 그것이 문단이다. 조각 수로 재면 컴포넌트 하나짜리 글이
    # 폴백으로 빠져 se-text-paragraph 하나하나가 문단으로 잡힌다.
    if len(chunks) < 2:
        chunks = re.split(r"(?=<(?:p|h[1-6]|hr|blockquote|figure|table)\b)",
                          body, flags=re.I)

    for c in chunks:
        low = c.lower()
        # 인용을 소제목처럼 쓰는 블로그가 있다. 그 판단은 분석가 몫이라
        # 스크립트는 원래 컴포넌트 종류만 남긴다.
        if "se-quotation" in low or re.search(r"<blockquote\b", low):
            t = clean(c)
            if t:
                out.append(f"[QUOTE] {t[:200]}")
            continue
        if re.search(r"se-sectiontitle|<h1\b", low):
            t = clean(c)
            if t:
                out.append(f"[H1] {t[:120]}")
            continue
        if re.search(r"<h[23]\b|se-title-text", low):
            t = clean(c)
            if t:
                out.append(f"[H2] {t[:120]}")
            continue
        if "se-horizontalline" in low or re.search(r"<hr\b", low):
            if out and out[-1] == "[HR]":
                continue    # 중첩 요소를 두 번 세지 않는다
            out.append("[HR]")
            continue
        if "se-sticker" in low:
            out.append("[STICKER]")
            continue
        # 카드를 이미지보다 먼저 본다. 링크 카드와 지도 카드가 썸네일 img 를
        # 품고 있어서 순서가 반대면 전부 사진으로 세어진다.
        if re.search(r"se-oglink|se-map|se-placesmap|se-mapinfo", low):
            out.append(f"[CARD] {clean(c)[:80]}")
            continue
        if re.search(r"se-image|<img\b|<figure\b", low):
            n = len(re.findall(r"<img\b", low))
            cap = ""
            m = re.search(r'class="[^"]*se-caption[^"]*"[^>]*>(.*?)</', c, re.S | re.I)
            if m:
                cap = clean(m.group(1))
            out.append(f"[IMG x{max(n,1)}]" + (f" (캡션: {cap})" if cap else ""))
            continue
        if re.search(r"<li\b", low):
            for li in re.findall(r"<li\b[^>]*>(.*?)</li>", c, re.S | re.I):
                t = clean(li)
                if t:
                    out.append(f"[LIST] {t[:200]}")
            continue

        if not clean(c):
            continue
        # 줄 단위로 낸다. 한 문장을 두 줄로 자르는 습관이 문체의 핵심이라
        # 문단으로 뭉치면 그 습관이 통째로 사라진다.
        block = []
        for text, bold in text_lines(c):
            if not text:
                if block:               # 문단 앞머리의 빈 줄은 버린다
                    block.append("[BR]")
                continue
            tag = "[P*" if bold else "[P"
            block.append(f"{tag}{'' if not block else '-'}] {text}")
        while block and block[-1] == "[BR]":
            block.pop()                 # 문단 끝의 빈 줄도 버린다
        out.extend(block)
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(1)
    src = sys.argv[1]
    target = to_fetchable(src)
    if target != src:
        print(f"# 원본: {src}")
    print(f"# 요청: {target}\n")
    lines = extract(fetch(target))
    if len(lines) < 3:
        print("본문을 찾지 못했습니다.", file=sys.stderr)
        sys.exit(1)
    print("\n".join(lines))
