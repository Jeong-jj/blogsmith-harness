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

echo "작업공간을 찾지 못했습니다. $PWD 부터 위로 올라가며 blog.config.json 을 찾았습니다." >&2
exit 1
