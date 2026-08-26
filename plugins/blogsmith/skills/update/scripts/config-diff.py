#!/usr/bin/env python3
"""템플릿과 사용자 설정을 맞대어 형식 차이를 낸다.

  python3 config-diff.py <템플릿 config> <사용자 config>

출력은 탭으로 나눈 줄이다.

  version<탭><설정 번호><탭><템플릿 번호>
  notation<탭><설정에 적힌 그대로>
  missing<탭><키><탭><기본값 JSON>
  extra<탭><키><탭><설정에 든 값 JSON>

`version` 줄은 항상 낸다. 번호는 `x.y.z` 로 정규화한 값이다.
`notation` 줄은 설정에 적힌 값이 `x.y.z` 문자열이 아닐 때만 낸다.
정수 `1` 이나 키가 아예 없는 경우다. 번호가 같아도 표기는 맞춰야 하므로 따로 알린다.
`missing` 줄은 빠진 키마다 하나씩이고 없으면 안 낸다.
`extra` 줄은 템플릿에 없는데 설정에 있는 키다. **지우라는 뜻이 아니다.**
형식에서 빠진 것인지 사용자가 직접 넣은 것인지 여기서는 갈리지 않는다.
`migrations.md` 의 `항목 제거` 기록이 그 답을 갖고 있고 `update` 가 맞대어 본다.

번호는 `x.y.z` 다. 자리마다 뜻이 있어 숫자만 보고 무엇이 바뀌었는지 알 수 있다.
major 는 키 이름이나 값의 의미가 바뀐 것이고 옛 설정을 그대로 못 쓴다.
minor 는 항목이 는 것, patch 는 기본값이 바뀐 것이라 옛 설정이 그대로 동작한다.

빠진 키를 찾는 것과 값을 옮기는 것은 담당이 다르다.
어떤 키가 있어야 하고 기본값이 무엇인지는 템플릿에 적혀 있어서 여기서 계산된다.
값이 어디서 왔는지는 템플릿이 모른다. 그건 `migrations.md` 가 답한다.
"""
import json
import sys

OLDEST = (1, 0, 0)


def load(path, label):
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        sys.exit(f"{label}을 찾지 못했다: {path}")
    except json.JSONDecodeError as e:
        sys.exit(f"{label}이 올바른 JSON 이 아니다: {path}\n  {e}")
    if not isinstance(data, dict):
        sys.exit(f"{label}이 객체가 아니다: {path}")
    return data


def canonical(raw):
    """설정에 적힌 값이 이미 `x.y.z` 문자열인가."""
    if not isinstance(raw, str):
        return False
    parts = raw.split(".")
    return len(parts) == 3 and all(p.isdigit() for p in parts)


def parse_version(raw, label):
    """`x.y.z` 로 읽는다. 빠진 자리는 0 으로 채운다.

    `version` 은 최초 템플릿부터 있었다. 없는 설정은 손으로 지운 것이고
    우리가 아는 가장 오래된 형식이 `1.0.0` 이라 그것으로 본다.
    `0.0.0` 으로 보면 있지도 않은 `1.0.0` 기록을 찾다가 멈춘다.

    정수 `1` 은 `1.0.0` 이다. 형식을 `x.y.z` 로 바꾸기 전에 쓰던 표기다.
    """
    if raw is None:
        return OLDEST
    if isinstance(raw, int) and not isinstance(raw, bool):
        return (raw, 0, 0)
    if isinstance(raw, str):
        parts = raw.split(".")
        if 1 <= len(parts) <= 3 and all(p.isdigit() for p in parts):
            nums = [int(p) for p in parts]
            return tuple(nums + [0] * (3 - len(nums)))
    sys.exit(f"{label}의 version 을 읽지 못했다: {raw!r}\n"
             "  x.y.z 형식이어야 한다. 짐작해서 고치지 않는다.")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    template = load(sys.argv[1], "템플릿 설정")
    target = load(sys.argv[2], "작업공간 설정")

    tpl_v = parse_version(template.get("version"), "템플릿 설정")
    raw = target.get("version")
    cfg_v = parse_version(raw, "작업공간 설정")
    print("version\t{}\t{}".format(".".join(map(str, cfg_v)),
                                   ".".join(map(str, tpl_v))))

    # 번호가 같아도 표기가 옛것이면 남는다. 그 사실을 따로 알린다.
    if not canonical(raw):
        print("notation\t{}".format("(없음)" if raw is None else json.dumps(raw, ensure_ascii=False)))

    # version 은 빼고 센다. 번호를 올리는 것은 변환을 다 돌린 뒤에 할 일이다.
    for key, default in template.items():
        if key != "version" and key not in target:
            print(f"missing\t{key}\t{json.dumps(default, ensure_ascii=False)}")

    # 템플릿에 없는 키를 낸다. 판정은 하지 않는다.
    # 형식에서 뺀 키와 사용자가 넣은 키를 파일만 봐서는 가를 수 없다.
    # 마이그레이션 기록을 아는 쪽이 판단한다.
    for key, value in target.items():
        if key != "version" and key not in template:
            print(f"extra\t{key}\t{json.dumps(value, ensure_ascii=False)}")
