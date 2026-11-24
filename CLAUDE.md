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
.dev-log/                         비공개 개발 일지, gitignore. README 부터 읽는다
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

- **이 파일을 늘리지 않는다.** 200줄이 상한이다.
  하네스 지식과 절차는 `plugins/blogsmith/skills/`로, 개발 규약은 `.claude/rules/`로 간다.
  플러그인 루트의 CLAUDE.md는 배포되지 않기 때문이다.
- `plugin.json`에 `version`을 반드시 유지한다. 빼면 모든 커밋이 사용자에게 전파된다.
- SKILL.md 본문은 500줄 미만. 상세 내용은 같은 디렉토리의 별도 파일로 뺀다.
- 문서 작성 규칙은 `.claude/rules/writing-style.md`에 있다. em dash를 쓰지 않는다.
- 커밋 메시지와 PR 본문은 평서형과 명사형으로 쓴다. 구어체 존댓말을 쓰지 않는다.
- 커밋 메시지에 AI 공동저자 트레일러를 넣지 않는다.

## 커밋과 PR

규약은 `.claude/rules/git-conventions.md` 에 있다.
제목 형식, PR 본문, 머지 정책, 리베이스, 강제 푸시, 저장소 설정이다.

**커밋하기 전과 PR 을 열기 전에 검사한다.**

```bash
scripts/check-title.sh "<제목>"
scripts/check-docs.sh
```

제목은 체언으로 끝낸다. PR 단위는 완결된 능력 하나고 스쿼시 머지만 쓴다.

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
