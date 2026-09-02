# blogsmith-harness

Claude Code 플러그인 형태의 블로그 아티클 작성 하네스를 개발하는 저장소다.
여기서 만드는 것은 앱이 아니라 AI가 쓸 작업 환경이다.

## 구조

```
.claude-plugin/marketplace.json   마켓플레이스 카탈로그 (name: jj-tools)
plugins/blogsmith/                배포되는 플러그인
  .claude-plugin/plugin.json      name: blogsmith, version 필수
  skills/                         스킬
  agents/                         서브에이전트
  hooks/hooks.json                훅
examples/                         포폴용 쇼케이스, 회귀 테스트 픽스처
workspace/                        dogfooding 작업장, gitignore
.dev-log/                         비공개 개발 일지, gitignore
```

## 배치 규칙

새 기능을 어디에 넣을지 판단하는 기준이다.

| 성격 | 배치처 |
|---|---|
| 파일이나 웹을 많이 읽고 요약만 돌려주는 역할 | `agents/` |
| 순수 지식 (SEO 규칙, 문체 지침) | `skills/` + `user-invocable: false` |
| 부작용이 있는 절차 (init, write, publish) | `skills/` + `disable-model-invocation: true` |
| 매번 예외 없이 실행돼야 하는 것 | `hooks/` |

**에이전트는 성격 말고 조건이 둘 더 있다.**

```
읽을 수 있어야 한다     robots.txt 가 막으면 성격이 맞아도 못 만든다
읽는 양이 커야 한다      제목 50줄이나 URL 두 개는 띄우는 값이 더 크다
```

**착수 전에 받아본다.** 2026-09 에 후보 셋 중 둘이 이것 때문에 접혔다.
자기 지난 글 목록과 검색 결과가 둘 다 `Disallow` 였다.
성격만 보고 설계까지 갔다가 되돌렸다. 근거는 `learn-style/domains.md` 에 있다.

## 지켜야 할 것

- **이 파일을 늘리지 않는다.** 200줄이 상한이고 지금이 적정선이다.
  하네스 지식과 절차는 전부 `plugins/blogsmith/skills/`로 간다.
  플러그인 루트의 CLAUDE.md는 배포되지 않기 때문이다.
- `plugin.json`에 `version`을 반드시 유지한다. 빼면 모든 커밋이 사용자에게 전파된다.
- SKILL.md 본문은 500줄 미만. 상세 내용은 같은 디렉토리의 별도 파일로 뺀다.
- 문서 작성 규칙은 `.claude/rules/writing-style.md`에 있다. em dash를 쓰지 않는다.
- 커밋 메시지에 AI 공동저자 트레일러를 넣지 않는다.

## 커밋과 브랜치

커밋 메시지와 PR 제목 **둘 다** 같은 형식을 쓴다.

```
<type>(<scope>): <제목, 한글, 50자 내>
```

type은 `feat` `fix` `docs` `refactor` `chore` `release`.
scope는 디렉토리 이름.

**제목은 체언으로 끝낸다.** `추가` `수정` `제거` `변경` `분리` 같은 명사다.
`~함` `~했다` `~하게 함` 같은 서술형 종결을 쓰지 않는다.
제목은 문장이 아니라 라벨이다. 본문은 평서형이지만 제목은 다르다.

```
나쁨  fix(skills): init 이 인자 없이 실행될 때 확인을 거치게 함
좋음  fix(skills): init 인자 없을 때 확인 절차 추가
```

**커밋하기 전과 PR 을 열기 전에 제목을 검사한다.**

```bash
scripts/check-title.sh "<제목>"
```

형식, 50자, 서술형 종결, `그리고` 를 본다. 훅으로 안 건 이유는 스쿼시 머지 때문이다.
`main` 에 남는 것은 PR 제목인데 `commit-msg` 훅은 커밋만 본다.

**문서를 고쳤으면 문서도 검사한다.**

```bash
scripts/check-docs.sh
```

`writing-style.md` 의 금지 표현과 예시 이름, `plugin.json` 의 `version`,
`SKILL.md` 500줄, `CLAUDE.md` 200줄을 본다.

**예시 이름은 허용 목록으로 본다.** 금지 목록을 손으로 세면 학습할 때마다 늘어난다.
허용은 `casual-review` 와 `examples/*/style/` 에서 읽고, 무시 대상은 `.gitignore` 에서 읽는다.
**글감 이름은 문장 안에 그냥 나와서 못 잡는다.** 사람이 본다.

**PR 체크리스트에는 사람만 판단할 수 있는 것만 두고 기계가 볼 것을 여기로 내렸다.**
체크박스는 안 봐도 눌리기 때문이다.

본문에 주제가 둘 이상이면 `-`로 항목화한다. 이어지는 줄은 두 칸 들여쓴다.
항목 사이는 빈 줄로 띄운다. 주제가 하나면 그냥 문단으로 쓴다.

```
docs(claude): main 최신화는 리베이스로 한다는 규칙 추가

- 작업 브랜치가 뒤처졌을 때 머지하면 브랜치에 머지 커밋이 남고,
  스쿼시할 때 그 잡음까지 커밋 메시지에 들어간다.

- 강제 푸시는 --force-with-lease 만 쓴다.
  --force 는 원격의 다른 변경을 말없이 덮는다.
```

스쿼시 커밋 본문이 브랜치 커밋 메시지를 이어붙인 것이라,
항목화해두면 머지 후에도 어느 근거가 어디에 속하는지 구분된다.

PR 제목까지 형식을 지키는 이유는 스쿼시 머지 때문이다.
PR 제목이 그대로 main의 커밋 제목이 되므로 안 지키면 git log가 깨진다.

작업은 브랜치에서 하고 PR로 머지한다. PR 단위는 완결된 능력 하나다.
제목에 "그리고"가 들어가면 쪼갠다.

## 머지 정책

**스쿼시 머지만 쓴다.** main에 PR 하나당 커밋 하나가 남는다.
PR 단위가 완결된 능력 하나이므로 main의 커밋 하나도 능력 하나가 된다.
되돌릴 때 커밋 하나만 revert 하면 되고 `git bisect`도 능력 단위로 걸린다.
작업 중의 중간 커밋은 main에 남지 않지만 PR 페이지에 보존되므로 잃는 것이 없다.

**머지한 브랜치는 삭제한다.** GitHub이 커밋을 유지하고 필요하면 복원할 수 있다.

## main 최신화는 리베이스

작업 브랜치가 main보다 뒤처졌을 때 **머지하지 않고 리베이스한다.**
머지하면 브랜치에 머지 커밋이 남고, 스쿼시할 때 그 잡음까지 커밋 메시지에 들어간다.

```bash
git checkout main && git pull
git checkout <작업 브랜치>
git rebase main
git push --force-with-lease
```

충돌이 나면 그 자리에서 해결하고 `git rebase --continue`로 넘어간다.
포기하려면 `git rebase --abort`.

저장소에 다음이 설정돼 있어 `git pull`이 항상 리베이스로 동작한다.

```bash
git config pull.rebase true      # merge 대신 rebase
git config rebase.autoStash true # 미커밋 변경을 자동으로 넣었다 뺀다
```

리베이스는 커밋 해시를 다시 만들므로 푸시할 때 강제 푸시가 필요하다.
반드시 `--force-with-lease`를 쓴다. 그냥 `--force`는 원격의 다른 변경을 말없이 덮는다.

## 강제 푸시를 언제 하는가

| 상황 | 방식 |
|---|---|
| PR 열기 전 | `--amend`로 커밋을 합쳐도 된다 |
| PR 연 후 | 커밋을 새로 쌓는다. amend 하지 않는다 |
| main과 뒤처짐 | 리베이스 후 `--force-with-lease` |

PR이 열린 뒤 amend 하고 강제 푸시하면 PR에 force-pushed 기록이 남고
그 시점까지의 리뷰 흐름이 끊긴다. 고칠 것이 있으면 커밋을 하나 더 쌓는다.
어차피 스쿼시 머지라 main에는 커밋 하나로 남는다.

리베이스는 예외다. main을 따라가려면 강제 푸시 말고 방법이 없다.

## 저장소 설정

맞춰둘 것:

- Allow squash merging만 켜고 merge commit과 rebase merge는 끈다
- 스쿼시 커밋 메시지는 `Pull request title and commit details`로 둔다.
  PR 본문에는 체크리스트와 주석이 섞여 있어 git log에 넣기에 적합하지 않다.
- Automatically delete head branches를 켠다

## 개발 중 설치

로컬 마켓플레이스로 자기 자신을 설치해서 배포물 그대로 검증한다.

```
/plugin marketplace add ./
/plugin install blogsmith@jj-tools
```

**스킬을 고쳤으면 세션을 재시작하고 검증한다.**
플러그인 본문은 세션 시작 시점으로 고정된다. 파일을 고쳐도 그 세션에서는 옛 내용이 실행된다.
재시작 없이 검증하면 고치기 전 코드를 검증하게 되고, 통과해도 아무것도 증명하지 못한다.

디스크와 세션이 어긋났는지는 이렇게 본다.

```bash
grep -n "<방금 고친 문구>" plugins/blogsmith/skills/<이름>/SKILL.md
```

디스크에만 있고 로드된 본문에 없으면 재시작 전이다.
