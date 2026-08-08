# styles

학습한 문체 문서가 저장되는 곳입니다.

`/blogsmith:learn-style`에 블로그 글 주소를 주면 그 글들을 읽고
문장 길이, 어미, 소제목 배치, 사진과 글의 비율, 도입부와 마무리 습관을 분석해서
규칙 문서로 만들어 여기에 저장합니다.

```
styles/
├── casual-review.md      친근한 후기체
├── info-dense.md         정보 위주 정리체
└── storytelling.md       서사 중심
```

## 쓰는 법

글을 쓸 때 스타일 이름으로 지정합니다.

```
/blogsmith:write "2026-08-03 성수동 카페" --style casual-review
```

`blog.config.json`의 `defaultStyle`에 이름을 적어두면 생략할 수 있습니다.

## 여러 개를 만들어 두세요

글 성격마다 어울리는 문체가 다릅니다.
맛집 후기와 제품 리뷰와 여행기가 같은 문체일 이유가 없습니다.

몇 개를 만들어 두고 글마다 골라 쓰는 편이 낫습니다.
