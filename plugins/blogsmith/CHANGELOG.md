# Changelog

## Unreleased

문체 학습과 검색 노출 지식. 실사용 검증 후 `0.2.0`으로 올린다.

- `naver-seo`, `google-seo`, `geo-aeo` 지식 스킬 추가.
  셋 다 `user-invocable: false`로 두어 필요할 때 자동으로 참조된다

- `/blogsmith:learn-style` 추가. 블로그 글 URL을 받아 문체를 분석하고
  `styles/<이름>.md`에 규칙 문서로 저장한다
- `style-analyst` 서브에이전트 추가. 글 본문이 메인 대화로 들어오지 않도록
  격리된 컨텍스트에서 읽고 요약만 돌려준다
- 문체 문서 스키마를 `skills/learn-style/schema.md`에 정의

## 0.1.0

플러그인 골격과 작업공간 초기화.

- `/blogsmith:init` 추가. 현재 디렉토리에 `sources/`, `styles/`, `output/`과
  `blog.config.json`을 만든다
- 입력 형식 예시 `sources/_sample/notes.md` 포함
- 각 디렉토리에 `.gitignore`를 넣어 개인 자료가 저장소에 올라가지 않게 한다
