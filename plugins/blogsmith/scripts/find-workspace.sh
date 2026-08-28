#!/bin/bash
# 작업공간을 찾는다. blog.config.json 이 있는 디렉토리가 작업공간이다.
#
#   find-workspace.sh              현재 디렉토리부터 위로 거슬러 찾는다
#   find-workspace.sh <경로>        그 경로를 작업공간으로 쓴다
#
# 찾으면 절대 경로를 출력하고 0 을 반환한다.
# 못 찾으면 사유를 출력하고 1 을 반환한다.

set -u

if [ $# -gt 0 ] && [ -n "$1" ]; then
  target="$1"
  if [ ! -d "$target" ]; then
    echo "지정한 경로가 없습니다: $target" >&2
    exit 1
  fi
  if [ ! -f "$target/blog.config.json" ]; then
    echo "작업공간이 아닙니다: $target (blog.config.json 없음)" >&2
    exit 1
  fi
  cd "$target" && pwd
  exit 0
fi

d="$PWD"
while :; do
  if [ -f "$d/blog.config.json" ]; then
    echo "$d"
    exit 0
  fi
  [ "$d" = "/" ] && break
  d="$(dirname "$d")"
done

# 위로 못 찾았으면 아래를 두 단계까지 훑어 후보를 낸다.
# 하네스 소스와 작업공간이 한 저장소에 같이 있으면 작업공간이 아래에 있다.
#
# **찾아도 고르지 않는다.** 후보만 내고 1 을 반환한다.
# 추측한 경로에 산출물을 쓰면 엉뚱한 곳에 파일이 생긴다. 고르는 것은 사람 몫이다.
#
# **후보는 절대 경로로 낸다.** 상대 경로로 내면 그 값을 --workspace 로 다시 넘기는 쪽의
# cwd 가 여기와 달라야 할 이유가 없는데도 달라질 수 있고, 그러면
# "지정한 경로가 없습니다" 로 떨어진다. 낸 값을 그대로 되돌려받을 수 있어야 한다.
found=$(find . -maxdepth 2 -name blog.config.json -not -path '*/.*' 2>/dev/null | sed 's|/blog.config.json$||;s|^\./||')

if [ -n "$found" ]; then
  echo "작업공간을 찾지 못했습니다. $PWD 부터 위로 올라가며 blog.config.json 을 찾았습니다." >&2
  echo "아래에서 후보를 찾았습니다. --workspace 로 지정하세요." >&2
  printf '%s\n' "$found" | while IFS= read -r d; do
    echo "  $PWD/$d" >&2
  done
  exit 1
fi

echo "작업공간을 찾지 못했습니다. $PWD 부터 위로 올라가며 blog.config.json 을 찾았습니다." >&2
echo "아래 두 단계에도 없습니다. --workspace 로 지정하거나 /blogsmith:init 을 실행하세요." >&2
exit 1
