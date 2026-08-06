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

## 지켜야 할 것

- **이 파일을 늘리지 않는다.** 200줄이 상한이고 지금이 적정선이다.
  하네스 지식과 절차는 전부 `plugins/blogsmith/skills/`로 간다.
  플러그인 루트의 CLAUDE.md는 배포되지 않기 때문이다.
- `plugin.json`에 `version`을 반드시 유지한다. 빼면 모든 커밋이 사용자에게 전파된다.
- SKILL.md 본문은 500줄 미만. 상세 내용은 같은 디렉토리의 별도 파일로 뺀다.
- 문서 작성 규칙은 `.claude/rules/writing-style.md`에 있다. em dash를 쓰지 않는다.
- 커밋 메시지에 AI 공동저자 트레일러를 넣지 않는다.

## 커밋과 브랜치

```
<type>(<scope>): <제목, 한글, 50자 내>
```

type은 `feat` `fix` `docs` `refactor` `chore` `release`.
scope는 디렉토리 이름.

작업은 브랜치에서 하고 PR로 머지한다. PR 단위는 완결된 능력 하나다.
제목에 "그리고"가 들어가면 쪼갠다.

## 개발 중 설치

로컬 마켓플레이스로 자기 자신을 설치해서 배포물 그대로 검증한다.

```
/plugin marketplace add ./
/plugin install blogsmith@jj-tools
```
