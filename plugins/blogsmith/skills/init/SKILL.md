---
description: 현재 디렉토리에 blogsmith 작업공간을 만든다. sources, styles, output 디렉토리와 blog.config.json을 생성한다
disable-model-invocation: true
argument-hint: "[대상 디렉토리, 생략하면 현재 위치]"
allowed-tools: Bash(ls *), Bash(test *), Bash(mkdir *), Bash(cp *), Bash(find *)
---

# 작업공간 초기화

대상 디렉토리는 `$ARGUMENTS`다. 비어 있으면 현재 작업 디렉토리를 쓴다.

## 절차

1. 대상 디렉토리에 `blog.config.json`이 이미 있는지 확인한다.
   있으면 **아무것도 하지 않고** 이미 초기화된 작업공간이라고 알린 뒤 종료한다.

2. 템플릿을 복사한다. 숨김 파일이 포함되도록 `.` 을 붙인다.

   ```
   cp -R "${CLAUDE_SKILL_DIR}/template/." "<대상 디렉토리>/"
   ```

3. 생성된 구조를 보여주고 다음 할 일을 안내한다.

## 생성되는 구조

```
<대상>/
├── blog.config.json     기본 스타일과 플랫폼 설정
├── .gitignore
├── sources/             입력: 사진과 메모
│   ├── README.md
│   └── _sample/         입력 형식 예시
├── styles/              학습한 문체 문서
└── output/              완성 아티클
```

## 안내할 다음 단계

- `sources/_sample/notes.md`를 열어 입력 형식을 확인한다
- 참고할 블로그 주소를 모아 `/blogsmith:learn-style`로 문체를 학습한다
- `blog.config.json`에서 `defaultStyle`과 `defaultPlatform`을 지정한다

## 주의

- 기존 파일을 덮어쓰지 않는다. `blog.config.json` 존재 여부로 판단한다.
- 대상 디렉토리가 없으면 만든다.
