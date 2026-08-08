---
description: blogsmith 작업공간을 만든다. 지정한 디렉토리에 sources, styles, output 과 blog.config.json 을 생성한다
disable-model-invocation: true
argument-hint: "<대상 디렉토리>"
allowed-tools: Bash(ls *), Bash(test *), Bash(mkdir *), Bash(cp *), Bash(find *)
---

# 작업공간 초기화

대상 디렉토리는 `$ARGUMENTS`다.

## 절차

1. 인자가 비어 있으면 **현재 디렉토리를 대상으로 삼을지 사용자에게 먼저 확인한다.**
   확인 없이 진행하지 않는다. 답을 받은 뒤 다음으로 넘어간다.

2. 대상 디렉토리에 `blog.config.json`이 이미 있는지 확인한다.
   있으면 **아무것도 하지 않고** 이미 초기화된 작업공간이라고 알린 뒤 종료한다.

3. 대상 디렉토리가 없으면 만든다.

   ```
   mkdir -p "<대상 디렉토리>"
   ```

4. 템플릿을 복사한다. 숨김 파일이 포함되도록 `.` 을 붙인다.

   ```
   cp -R "${CLAUDE_SKILL_DIR}/template/." "<대상 디렉토리>/"
   ```

5. 생성된 구조를 보여주고 다음 할 일을 안내한다.

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
- 대상 디렉토리 안에 다른 파일이 있어도 상관없다. 템플릿을 얹기만 한다.
- **인자가 없을 때 현재 디렉토리에 바로 만들지 않는다.**
  사용자가 자기 프로젝트 루트에서 실행하면 `sources`, `styles`, `output`이 그 안에 섞인다.
  되돌리려면 디렉토리를 하나씩 지워야 하므로 한 번 더 묻는 비용이 싸다.
