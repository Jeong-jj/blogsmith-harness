# Changelog

## Unreleased

실사용 검증 후 `0.2.0`으로 올린다.

- `/blogsmith:learn-style` 추가. 블로그 글 URL을 받아 문체를 분석하고
  `styles/<이름>.md`에 규칙 문서로 저장한다
- `/blogsmith:write` 추가. 사진과 메모를 원천으로 학습한 문체에 맞춰 아티클을 쓴다
- `style-analyst` 서브에이전트 추가. 글 본문이 메인 대화로 들어오지 않도록
  격리된 컨텍스트에서 읽고 요약만 돌려준다
- `naver-seo`, `google-seo`, `geo-aeo` 지식 스킬 추가.
  셋 다 `user-invocable: false`로 두어 필요할 때 자동으로 참조된다
- `natural-voice` 지식 스킬과 `audit.py` 검사기 추가.
  네이버가 자동 생성 패턴이 감지된 문서를 검색결과에서 제외하므로
  문체 자연스러움이 품질이 아니라 생존 조건이다
- 본문 수집을 `fetch-post.py`로 교체. 신분을 밝히고 요청하며 막히면 물러난다

## 0.1.0

플러그인 골격과 작업공간 초기화.

- `/blogsmith:init` 추가. 현재 디렉토리에 `sources/`, `styles/`, `output/`과
  `blog.config.json`을 만든다
- 입력 형식 예시 `sources/_sample/notes.md` 포함
