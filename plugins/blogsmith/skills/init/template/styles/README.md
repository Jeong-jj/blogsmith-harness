# styles

학습한 문체 문서가 저장되는 곳입니다.

`/blogsmith:learn-style`에 블로그 주소를 주면 해당 블로그의 아티클을 읽고
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
/blogsmith:write 2026-08-성수동카페 --style casual-review
```

`blog.config.json`의 `defaultStyle`에 이름을 적어두면 생략할 수 있습니다.

## 커밋

내용물은 `.gitignore`로 제외됩니다.
분석 대상이 남의 블로그이므로 결과물을 공개 저장소에 올리지 않는 편이 안전합니다.
