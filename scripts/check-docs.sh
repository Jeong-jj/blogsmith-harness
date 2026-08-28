#!/usr/bin/env bash
#
# 문서 규칙 중 기계가 판정할 수 있는 것을 검사한다.
# PR 체크리스트에는 사람만 판단할 수 있는 것만 두고 나머지를 여기로 내렸다.
#
#   scripts/check-docs.sh          추적 중인 문서 전부
#   scripts/check-docs.sh a.md b.md  지정한 파일만
#
# 종료 코드 0 통과, 1 위반.

set -uo pipefail
cd "$(git rev-parse --show-toplevel)" || exit 1

fail=0
say() { printf '%s\n' "$*" >&2; }

# ── 검사에서 빼는 자리 ───────────────────────────────────────
#
# 규칙 자체를 설명하거나 검출 패턴을 담은 파일은 위반이 아니다.
# natural-voice/scripts/_core.py 가 같은 이유로 자기 자신을 예외로 둔다.
#
# examples/ 의 원문과 산출물은 블로그 글이라 이 규칙의 대상이 아니다.
# writing-style.md 는 README, ADR, SKILL.md, 가이드에 적용된다고 스스로 밝힌다.
skip() {
  case "$1" in
    .claude/rules/writing-style.md) return 0 ;;
    plugins/blogsmith/skills/natural-voice/*) return 0 ;;
    examples/*/output/*|examples/*/sources/*|examples/*/style/*) return 0 ;;
  esac
  return 1
}

# ── 1. 금지 표현 ────────────────────────────────────────────
#
# .claude/rules/writing-style.md 의 금지 표 아홉 행을 정규식으로 옮겼다.
# `이해를 높이는 것` 처럼 예시로만 적힌 것은 그 자리에서 일반화한 형태를 쓴다.
PATTERNS=$(cat <<'EOF'
em dash	—
번역투 에 대한	에 대한
번역투 에 있어서	에 있어서
번역투 을 통해	[을를] 통해
번역투 로 인해	[으]?로 인해
단정 회피	라고 할 수 있|하는 것이 중요
명사화 통한	[을를] 통한
피동 되어지	되어[지진집]
피동 여겨지	여겨[지진집]
과장 형용사	놀라운|강력한|혁신적인|획기적인
메타 화법	살펴보겠|알아보겠
마무리 상투구	결론적으로|정리하자면
EOF
)

if [ $# -gt 0 ]; then
  file_list=$(printf '%s\n' "$@")
else
  file_list=$(git ls-files '*.md')
fi

hits=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  [ -f "$f" ] || continue
  skip "$f" && continue
  while IFS=$'\t' read -r name re; do
    [ -z "${re:-}" ] && continue
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      say "  $f:${line%%:*}  [$name]"
      say "      $(echo "${line#*:}" | cut -c1-80)"
      hits=$((hits + 1))
    done < <(grep -nE "$re" "$f" 2>/dev/null)
  done <<< "$PATTERNS"

  # 이모지 소제목. BSD grep 에 -P 가 없어 perl 로 본다
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    say "  $f:${line%%:*}  [이모지 소제목]"
    say "      $(echo "${line#*:}" | cut -c1-80)"
    hits=$((hits + 1))
  done < <(perl -CSD -ne 'print "$.:$_" if /^#+ .*[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{FE0F}]/' "$f" 2>/dev/null)
done <<EOF_FILES
$file_list
EOF_FILES

if [ "$hits" -gt 0 ]; then
  say "금지 표현 ${hits}건"
  fail=1
else
  say "금지 표현 없음"
fi

# ── 2. plugin.json 의 version ───────────────────────────────
#
# 빼면 모든 커밋이 사용자에게 전파된다. 있는지만 본다.
for pj in $(git ls-files '*/plugin.json'); do
  if grep -q '"version"' "$pj"; then
    say "version 있음  $pj"
  else
    say "version 없음  $pj"
    fail=1
  fi
done

# ── 3. SKILL.md 500줄, CLAUDE.md 200줄 ──────────────────────
over=0
for f in $(git ls-files '*/SKILL.md'); do
  n=$(wc -l < "$f" | tr -d ' ')
  if [ "$n" -ge 500 ]; then say "  $f  ${n}줄 (상한 500)"; over=$((over + 1)); fi
done
[ "$over" -gt 0 ] && fail=1
say "SKILL.md 상한 초과 ${over}건"

if [ -f CLAUDE.md ]; then
  n=$(wc -l < CLAUDE.md | tr -d ' ')
  if [ "$n" -ge 200 ]; then
    say "CLAUDE.md ${n}줄 (상한 200)"
    fail=1
  else
    say "CLAUDE.md ${n}줄"
  fi
fi

exit "$fail"
