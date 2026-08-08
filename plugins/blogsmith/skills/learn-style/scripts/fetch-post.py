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
  [P] 문단 한 줄
  [IMG] 사진 (캡션: ...)
  [HR] 구분선
  [QUOTE] 인용
  [LIST] 목록 항목
  [CARD] 링크 카드나 지도

네이버는 WebFetch 로 접근할 수 없어 curl 로 받는다.
본문이 iframe 안이라 PostView.naver 주소로 바꿔 요청한다.
"""
import html
import re
import subprocess
import sys
from urllib.parse import urlparse, parse_qs

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


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


def main_container(doc):
    """본문 영역만 남긴다. 못 찾으면 전체를 쓴다."""
    for pat in (r'<div[^>]*class="[^"]*se-main-container[^"]*"[^>]*>(.*)',
                r'<div[^>]*id="postViewArea"[^>]*>(.*)',
                r'<article[^>]*>(.*?)</article>'):
        m = re.search(pat, doc, re.S | re.I)
        if m:
            return m.group(1)
    return doc


def clean(s):
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s).replace("​", "")
    return re.sub(r"[ \t ]+", " ", s).strip()


def extract(doc):
    body = main_container(doc)
    body = re.sub(r"<(script|style)\b.*?</\1>", " ", body, flags=re.S | re.I)

    out = []
    # 컴포넌트 단위로 자른다. 스마트에디터는 se-component 로 문단을 감싼다.
    chunks = re.split(r'(?=<div[^>]*class="[^"]*se-component[^"]*")', body)
    if len(chunks) < 3:
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
        if re.search(r"se-image|<img\b|<figure\b", low):
            n = len(re.findall(r"<img\b", low))
            cap = ""
            m = re.search(r'class="[^"]*se-caption[^"]*"[^>]*>(.*?)</', c, re.S | re.I)
            if m:
                cap = clean(m.group(1))
            out.append(f"[IMG x{max(n,1)}]" + (f" (캡션: {cap})" if cap else ""))
            continue
        if "se-oglink" in low or "se-map" in low or "se-placesMap" in low:
            out.append(f"[CARD] {clean(c)[:80]}")
            continue
        if re.search(r"<li\b", low):
            for li in re.findall(r"<li\b[^>]*>(.*?)</li>", c, re.S | re.I):
                t = clean(li)
                if t:
                    out.append(f"[LIST] {t[:200]}")
            continue

        text = clean(c)
        if not text:
            continue
        # 굵게 표시가 있으면 남긴다. 볼드 사용 습관도 문체다.
        if re.search(r"<(b|strong)\b|font-weight:\s*bold", low):
            out.append(f"[P*] {text}")
        else:
            out.append(f"[P] {text}")
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
