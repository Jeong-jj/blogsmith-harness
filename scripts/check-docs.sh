#!/usr/bin/env bash
#
# 문서 규칙 중 기계가 판정할 수 있는 것을 검사한다.
# PR 체크리스트에는 사람만 판단할 수 있는 것만 두고 나머지를 여기로 내렸다.
#
#   scripts/check-docs.sh            저장소의 문서 전부
#   scripts/check-docs.sh a.md b.md  지정한 파일만
#
# 아직 add 하지 않은 새 문서도 본다. 새로 쓴 것이 빠지면 통과가 아무것도 뜻하지 않는다.
# gitignore 대상은 빠진다. workspace/ 와 .dev-log/ 가 그렇다.
#
# 종료 코드 0 통과, 1 위반.
#
# bash 로 돌린다. 프로세스 치환과 <<< 를 쓰므로 sh 로는 안 된다.
# sh 는 파일 전체를 먼저 파싱해서 실행 전에 죽으므로 안에서 막을 수가 없다.

set -uo pipefail

fail=0
say() { printf '%s\n' "$*"; }

# 저장소 밖에서 돌면 git 이 전부 빈 값을 내고 검사 0개로 통과한다.
# cd "" 는 bash 에서 성공하므로 || exit 1 이 안 걸린다. 먼저 받아서 본다.
root=$(git rev-parse --show-toplevel 2>/dev/null) || root=""
if [ -z "$root" ]; then
  say "git 저장소 안에서 실행해야 한다"
  exit 1
fi
# 인자는 저장소 루트가 아니라 사용자가 있던 자리 기준이다.
# cd 하기 전에 풀어서 루트 기준 상대 경로로 바꾼다.
# 그래야 하위 디렉토리에서 준 상대 경로가 열리고, 절대 경로도 제외 규칙에 걸린다.
arg_list=""
for a in "$@"; do
  _d=$(dirname -- "$a"); _b=$(basename -- "$a")
  _rd=$(cd "$_d" 2>/dev/null && pwd -P) || _rd=""
  [ -n "$_rd" ] && a="$_rd/$_b"
  case "$a" in "$root"/*) a=${a#"$root"/} ;; esac
  arg_list="$arg_list$a
"
done

cd "$root" || exit 1

# 이모지 소제목 검사는 perl 로 돈다. BSD grep 에 -P 가 없어서다.
# 없으면 그 검사만 못 도는데, 조용히 통과하면 안 본 것을 본 것으로 센다.
have_perl=1
command -v perl >/dev/null 2>&1 || have_perl=0

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
# 예시로만 적힌 것은 그 자리에서 일반화한 형태를 쓴다.
#
# **아홉 행을 다 덮지는 못한다. 통과가 규칙 전부를 지켰다는 뜻은 아니다.**
#
#   문장 중간의 명사화   `활용을 통한` 만 본다. `이해를 높이는 것` 꼴은 못 본다.
#                     안전하게 기계화할 방법이 없다. 정상 문장이 너무 많이 걸린다
#   과장 형용사        표에 적힌 넷만 본다. 뛰어난, 최고의 같은 것은 사람이 본다
#   종결 규칙          내부 문서의 구어체 존댓말은 안 본다.
#                     README 와 가이드는 존댓말이 맞아서 문서 종류를 알아야 갈린다
PATTERNS='em dash	—
번역투 에 대한	에 대한
번역투 에 있어서	에 있어서
번역투 을 통해	[을를] 통해
번역투 로 인해	으?로 인해
단정 회피	고 할 수 있|하는 것이 중요
명사화 통한	[을를] 통한
피동 되어지	되어[지진집]
피동 여겨지	여겨[지진집]|[보쓰불잊][여려혀][지진집]|나뉘어[지진집]
과장 형용사	놀라운|강력한|혁신적인|획기적인
메타 화법	이 글에서는|살펴보겠|알아보겠|소개하겠|정리해보겠
마무리 상투구	결론적으로|정리하자면'

# 패턴이 비면 검사가 안 도는데 통과로 보인다. 개수를 못 박아 둔다.
n_pat=0
while IFS= read -r _l; do
  [ -n "$_l" ] && n_pat=$((n_pat + 1))
done <<EOF_COUNT
$PATTERNS
EOF_COUNT
if [ "$n_pat" -ne 12 ]; then
  say "패턴이 12개여야 하는데 ${n_pat}개다. 검사를 못 돌린다"
  exit 1
fi

if [ $# -gt 0 ]; then
  file_list=$arg_list
else
  file_list=$(git -c core.quotepath=false ls-files -co --exclude-standard '*.md')
fi

hits=0
scanned=0
skipped=0
missing=0
binary=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  # -f 만 보면 읽기 권한 없는 파일이 검사한 것으로 세어진다.
  # grep 실패는 2>/dev/null 이 삼키므로 0건으로 통과한다.
  if [ ! -f "$f" ] || [ ! -r "$f" ]; then
    say "  파일을 못 읽음: $f"
    missing=$((missing + 1))
    continue
  fi
  if skip "$f"; then skipped=$((skipped + 1)); continue; fi
  if [ "$(wc -c < "$f")" != "$(tr -d '\000' < "$f" | wc -c)" ]; then
    say "  NUL 이 들어 있어 검사할 수 없음: $f"
    binary=$((binary + 1))
    continue
  fi
  scanned=$((scanned + 1))
  while IFS=$'\t' read -r name re; do
    [ -z "${re:-}" ] && continue
    while IFS= read -r line; do
      [ -z "$line" ] && continue
      say "  $f:${line%%:*}  [$name]"
      say "      $(echo "${line#*:}" | cut -c1-80)"
      hits=$((hits + 1))
    done < <(grep -anE "$re" -- "$f" 2>/dev/null)
  done <<< "$PATTERNS"

  # 이모지 소제목. BSD grep 에 -P 가 없어 perl 로 본다.
  # 2B00-2BFF 를 넣은 것은 ⭐ (U+2B50) 이 2600-27BF 밖이라서다.
  # 화살표(2190-21FF)는 넣지 않는다. 이 저장소가 → 를 산문에서 쓴다.
  [ "$have_perl" = 0 ] && continue
  while IFS= read -r line; do
    [ -z "$line" ] && continue
    say "  $f:${line%%:*}  [이모지 소제목]"
    say "      $(echo "${line#*:}" | cut -c1-80)"
    hits=$((hits + 1))
  done < <(perl -CSD -ne 'print "$.:$_" if /^#+ .*[\x{1F000}-\x{1FAFF}\x{2600}-\x{27BF}\x{2B00}-\x{2BFF}\x{FE0F}]/' -- "$f" 2>/dev/null)
done <<EOF_FILES
$file_list
EOF_FILES

say "금지 표현 ${hits}건  (검사 ${scanned}개, 제외 ${skipped}개)"
# 볼 것이 하나도 없으면 목록 만들기가 깨진 것이다. 통과로 세지 않는다.
if [ $# -eq 0 ] && [ $((scanned + skipped)) -eq 0 ]; then
  say "검사할 문서를 하나도 못 찾았다. 목록 만들기가 깨졌다"
  fail=1
fi
if [ "$have_perl" = 0 ]; then
  say "perl 이 없어 이모지 소제목 검사를 건너뛰었다. 나머지 열둘만 봤다"
fi
[ "$hits" -gt 0 ] && fail=1
if [ "$missing" -gt 0 ]; then
  say "못 연 파일 ${missing}개"
  fail=1
fi
if [ "$binary" -gt 0 ]; then
  say "NUL 이 든 문서 ${binary}개"
  fail=1
fi

# ── 2. 예시 이름 ────────────────────────────────────────────
#
# writing-style.md 의 `개발 흔적을 남기지 않는다` 를 기계가 볼 수 있는 만큼 본다.
#
# **유출만 잡는 것이 아니다.** 허용 목록 밖이면 표기가 안 맞는 것도 걸린다.
# casual 처럼 새는 것이 아닌데 이름만 다른 자리가 그렇다. 그래서 이름이 `예시 이름` 이다.
#
# **금지 목록을 안 만든다.** 무엇이 개발 흔적인지 손으로 세면 학습할 때마다 늘어난다.
# 허용 쪽을 저장소에서 읽어 만들고 형식이 고정된 자리만 본다.
#
#   허용 이름   casual-review 와 examples/*/style/style.md 의 name.  픽스처가 늘면 따라 는다
#   무시 대상   .gitignore 를 읽는다. 무시 대상이 늘면 검사도 따라 는다
#
# 글감 이름은 문장 안에 그냥 나와서 못 잡는다. 사람이 본다.

allow="casual-review"
while IFS= read -r d; do
  [ -z "$d" ] && continue
  n=$(grep -m1 '^name:' "$d" 2>/dev/null | sed 's/^name: *//')
  [ -n "$n" ] && allow="$allow|$n"
done <<EOF_STYLES
$(ls examples/*/style/style.md 2>/dev/null)
EOF_STYLES

# 규칙을 설명하는 파일은 그 규칙을 본문에 담아야 한다
trace_skip() {
  case "$1" in
    scripts/check-docs.sh|.claude/rules/writing-style.md|.gitignore) return 0 ;;
    plugins/blogsmith/skills/learn-style/raw.md) return 0 ;;
  esac
  return 1
}

trace=0
EX="--exclude-dir=.git --exclude-dir=.dev-log --exclude-dir=workspace"

# (1) gitignore 대상 안쪽 경로
#     마지막 조각이 허용 이름이거나 자리 표시면 넘어간다
while IFS= read -r pat; do
  case "$pat" in ""|\#*) continue ;; esac
  case "$pat" in */) d=${pat%/} ;; *) continue ;; esac
  case "$d" in .*|workspace) ;; *) continue ;; esac
  while IFS= read -r hit; do
    [ -z "$hit" ] && continue
    f=${hit%%:*}; rest=${hit#*:}; ln=${rest%%:*}; body=${rest#*:}
    skip "$f" && continue
    trace_skip "$f" && continue
    case "$body" in *"<"*) continue ;; esac
    leaf=$(printf '%s' "$body" | grep -oE "$d/[A-Za-z0-9_./-]+" | head -1 \
           | sed -E "s|^$d/||; s|/\$||; s|.*/||; s|\\.md\$||")
    printf '%s' "$leaf" | grep -qE "^($allow)\$" && continue
    say "  $f:$ln  [$d 안쪽 경로]"
    trace=$((trace + 1))
  done < <(grep -rnE "$d/[A-Za-z0-9_.-]+[/.]" --include='*.md' --include='*.py' --include='*.sh' \
             $EX . 2>/dev/null | sed 's|^\./||')
done <<EOF_IGN
$(cat .gitignore 2>/dev/null)
EOF_IGN

# (2) 문체 이름. --style X 와 `문체 X` 의 X
while IFS= read -r hit; do
  [ -z "$hit" ] && continue
  f=${hit%%:*}; rest=${hit#*:}; ln=${rest%%:*}; body=${rest#*:}
  skip "$f" && continue
  trace_skip "$f" && continue
  tail=$(printf '%s' "$body" | sed -E 's/.*(--style|문체) +`?//')
  name=$(printf '%s' "$tail" | sed -E 's/[^A-Za-z0-9_-].*//')
  [ -z "$name" ] && continue
  # 경로면 문체 이름이 아니다. 문체  style/_raw/ 같은 표 칸
  [ "$(printf '%s' "$tail" | cut -c$((${#name} + 1)))" = "/" ] && continue
  printf '%s' "$name" | grep -qE "^($allow)\$" && continue
  say "  $f:$ln  [문체 이름 $name]"
  trace=$((trace + 1))
done < <(grep -rnE '(--style|문체) +`?[A-Za-z][A-Za-z0-9_-]*' --include='*.md' \
           $EX . 2>/dev/null | sed 's|^\./||')

say "예시 이름 ${trace}건  (허용 문체 ${allow})"
[ "$trace" -gt 0 ] && fail=1

# ── 3. plugin.json 의 version ───────────────────────────────
#
# 빼면 모든 커밋이 사용자에게 전파된다. 있는지만 본다.
n_pj=0
while IFS= read -r pj; do
  [ -z "$pj" ] && continue
  n_pj=$((n_pj + 1))
  if grep -q '"version"' -- "$pj"; then
    say "version 있음  $pj"
  else
    say "version 없음  $pj"
    fail=1
  fi
done <<EOF_PJ
$(git -c core.quotepath=false ls-files -co --exclude-standard '*/plugin.json')
EOF_PJ
if [ "$n_pj" -eq 0 ]; then
  say "plugin.json 을 하나도 못 찾았다"
  fail=1
fi

# ── 4. SKILL.md 500줄, CLAUDE.md 200줄 ──────────────────────
#
# 두 규칙의 문구가 다르므로 경계도 다르다.
#   SKILL.md   "500줄 미만"      500 은 위반
#   CLAUDE.md  "200줄이 상한"     200 은 허용, 201 부터 위반
#
# 줄 수는 frontmatter 를 포함한 파일 전체다. 본문만 세면 세는 기준이 또 갈린다.
over=0
n_skill=0
while IFS= read -r f; do
  [ -z "$f" ] && continue
  n_skill=$((n_skill + 1))
  n=$(wc -l < "$f" 2>/dev/null | tr -d ' ')
  if [ -z "$n" ]; then say "  줄 수를 못 셈: $f"; fail=1; continue; fi
  if [ "$n" -ge 500 ]; then say "  $f  ${n}줄 (상한 500)"; over=$((over + 1)); fi
done <<EOF_SKILLS
$(git -c core.quotepath=false ls-files -co --exclude-standard '*/SKILL.md')
EOF_SKILLS
[ "$over" -gt 0 ] && fail=1
say "SKILL.md 상한 초과 ${over}건  (검사 ${n_skill}개)"
if [ "$n_skill" -eq 0 ]; then
  say "SKILL.md 를 하나도 못 찾았다"
  fail=1
fi

if [ -f CLAUDE.md ]; then
  n=$(wc -l < CLAUDE.md 2>/dev/null | tr -d ' ')
  if [ -z "$n" ]; then
    say "CLAUDE.md 줄 수를 못 셈"
    fail=1
  elif [ "$n" -gt 200 ]; then
    say "CLAUDE.md ${n}줄 (상한 200)"
    fail=1
  else
    say "CLAUDE.md ${n}줄"
  fi
fi

exit "$fail"
