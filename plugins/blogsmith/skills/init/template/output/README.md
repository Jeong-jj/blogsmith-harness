# output

완성된 아티클이 저장되는 곳입니다. 글감 하나당 디렉토리 하나가 생깁니다.

```
output/
└── 2026-08-성수동카페/
    ├── article.md         마크다운 원본
    ├── naver.html         네이버 블로그 붙여넣기용
    ├── velog.md           velog 붙여넣기용
    └── meta.md            제목 후보, 태그, 메타 설명
```

플랫폼은 글을 쓸 때 고릅니다.

```
/blogsmith:write 2026-08-성수동카페 --platform naver
```

지원 값은 `markdown`, `naver`, `tistory`, `velog`입니다.
`blog.config.json`의 `defaultPlatform`으로 기본값을 정할 수 있습니다.

## 커밋

내용물은 `.gitignore`로 제외됩니다. 발행처가 원본이고 여기는 작업본입니다.
