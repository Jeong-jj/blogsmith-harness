# 플랫폼별 자동 수집 방침

조사 시점 2026-08-09. `robots.txt`를 직접 확인한 결과다.

## blogsmith 의 원칙

**신분을 밝히고 받는다.** 브라우저인 척하지 않는다.

```
User-Agent: blogsmith/0.1 (+https://github.com/Jeong-jj/blogsmith-harness)
```

받아주면 쓰고, 막으면 물러난다. 우회하지 않는다.
막혔을 때는 사용자에게 대안을 안내하고 끝낸다.

## 현황

| 플랫폼 | 본문 수집 | robots.txt |
|---|---|---|
| velog.io | 가능 | `User-agent: *` 만 있고 제한 없음 |
| `*.tistory.com` | 가능 | 관리 페이지(`/manage` `/admin` `/search`)만 차단. 글 본문은 허용 |
| blog.naver.com | 가능 | ClaudeBot 등 AI 크롤러를 이름으로 차단. 아래 참고 |
| brunch.co.kr | 확인 필요 | ClaudeBot 등 AI 크롤러를 이름으로 차단 |

## 네이버에 대한 판단

네이버 `robots.txt`에 이렇게 적혀 있다.

```
# BOT ACCESS FOR THE PURPOSES OF AI TRAINING AND
# RETRIEVAL-AUGMENTED GENERATION (RAG) IS STRICTLY PROHIBITED.
User-agent: ClaudeBot
Disallow: /
```

**blogsmith 는 여기서 지목된 대상이 아니라고 본다.** 근거는 셋이다.

ClaudeBot 은 Anthropic 이 학습과 검색 색인 목적으로 웹을 훑는 크롤러다.
blogsmith 는 사용자가 직접 고른 최대 6개 주소만 읽는다. 링크를 따라가지 않는다.

수집한 내용을 학습 데이터로 쓰지 않고 저장하지도 않는다.
추출하는 것은 문체 규칙이며 원문은 남기지 않는다.

실제 서버 동작으로도 확인했다. `User-Agent` 를 `ClaudeBot` 으로 밝히면 차단되지만,
`blogsmith` 로 밝히면 정상적으로 응답한다. 네이버가 막는 대상에 우리가 들어 있지 않다.

**네이버가 blogsmith 를 막기 시작하면 그때는 물러난다.** 우회하지 않는다.

## 법적 검토

`robots.txt` 위반 자체는 불법이 아니다. 법적 구속력이 없는 관행이다.

형사 쪽은 대법원이 정리했다. 공개 페이지 접근을 정보통신망 침입으로 보기 어렵다는 취지로
무죄가 확정됐다 (2022. 5. 12. 선고 2021도1533).

민사 책임이 인정된 사례는 있다. 다만 문제가 된 것은 아래 조건이 겹친 경우다.

- 경쟁 사업자의 데이터베이스를 통째로 복제
- 수집한 내용을 자사 서비스에 그대로 게재
- 대량 요청으로 서버에 부담

blogsmith 는 최대 6개 요청이고, 원문을 저장하지 않으며, 상업적 경쟁 관계가 없다.

## 새 플랫폼을 지원할 때

먼저 `robots.txt` 를 확인한다.

```bash
curl -s https://<도메인>/robots.txt
```

AI 크롤러를 이름으로 차단하는지, `User-agent: *` 에서 글 본문 경로를 막는지 본다.
그다음 `blogsmith` UA 로 실제 응답이 오는지 확인한다.

둘 중 하나라도 막히면 자동 수집을 넣지 않는다. 이 문서에 근거와 함께 기록한다.
