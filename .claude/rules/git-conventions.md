# 커밋과 PR 규약

이 저장소의 커밋 메시지, 브랜치, PR, 머지, 저장소 설정 규칙이다.
`CLAUDE.md` 에서 분리했다. 그 파일은 하네스 구조와 배치 규칙만 둔다.

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
