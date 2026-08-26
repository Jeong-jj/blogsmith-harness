#!/usr/bin/env python3
"""템플릿의 안내문과 작업공간 사본을 맞대어 낡은 것을 낸다.

  python3 template-diff.py <템플릿 디렉토리> <작업공간>

출력은 탭으로 나눈 줄이다.

  stale<탭><상대 경로>      내용이 다르다
  missing<탭><상대 경로>    작업공간에 없다

**`blog.config.json` 은 보지 않는다.** 그쪽은 `config-diff.py` 담당이다.
설정은 사용자가 값을 정하는 파일이라 키 단위로 견주고 사용자 값을 지켜야 한다.
안내문은 하네스가 제공하는 문서라 통째로 견주고 통째로 덮는다.

낡았다고 판정만 하고 고치지는 않는다. 덮는 것은 `update` 가 확인받고 한다.
"""
import filecmp
import sys
from pathlib import Path

SKIP = {"blog.config.json"}


def main():
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    tpl, ws = Path(sys.argv[1]), Path(sys.argv[2])
    if not tpl.is_dir():
        sys.exit(f"템플릿 디렉토리가 없습니다: {tpl}")
    if not ws.is_dir():
        sys.exit(f"작업공간이 없습니다: {ws}")

    for src in sorted(p for p in tpl.rglob("*") if p.is_file()):
        rel = src.relative_to(tpl)
        if rel.name in SKIP:
            continue
        dst = ws / rel
        if not dst.exists():
            print(f"missing\t{rel}")
        elif not filecmp.cmp(src, dst, shallow=False):
            print(f"stale\t{rel}")


if __name__ == "__main__":
    main()
