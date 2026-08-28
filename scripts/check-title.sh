#!/bin/bash
# 커밋과 PR 의 제목이 규칙을 지키는지 본다.
#
#   scripts/check-title.sh "<제목>"
#
# 통과하면 0, 걸리면 사유를 내고 1 을 반환한다.
#
# **이것은 개발용이다.** plugins/ 가 아니라 저장소 루트에 있는 이유다.
# 배포되지 않고 사용자가 부를 일이 없다.
#
# 왜 훅이 아닌가. 스쿼시 머지라 main 에 남는 제목은 PR 제목인데
# commit-msg 훅은 커밋만 본다. 커밋과 PR 을 만드는 자리에서 이것을 부른다.

set -u

if [ $# -lt 1 ] || [ -z "${1:-}" ]; then
  echo "제목을 인자로 주세요." >&2
  echo "  scripts/check-title.sh \"fix(skills): 무엇 무엇 수정\"" >&2
  exit 1
fi

t="$1"
fail=0

say() { echo "  $1" >&2; fail=1; }

# 1. 형식
# scope 는 있으면 좋지만 없어도 통과시킨다. main 에 `docs:` 형태가 이미 있다.
if ! echo "$t" | grep -qE '^(feat|fix|docs|refactor|chore|release)(\([a-z-]+\))?: .+'; then
  say "형식이 <type>(<scope>): <제목> 이 아닙니다."
fi

# 2. 길이. 제목 부분만 센다
body="${t#*: }"
n=$(echo -n "$body" | wc -m | tr -d ' ')
if [ "$n" -gt 50 ]; then
  say "제목이 ${n}자입니다. 50자 안으로 줄이세요."
fi

# 3. 종결형. 제목은 문장이 아니라 라벨이다
last="${body##* }"
case "$last" in
  *게|*함|*됨|*임|*음|*다|*했다|*한다)
    say "제목이 서술형으로 끝납니다: '$last'"
    say "체언으로 끝내세요. 추가 수정 제거 변경 분리 반영 보완 명시 완화 갱신 같은 명사입니다."
    ;;
esac

# 4. 쪼갤 신호
if echo "$body" | grep -qE '그리고|및 '; then
  say "제목에 '그리고' 나 '및' 이 있습니다. PR 을 쪼개는 것을 먼저 생각하세요."
fi

[ "$fail" -eq 0 ] && exit 0
echo "제목: $t" >&2
exit 1
