#!/usr/bin/env python3
"""템플릿과 사용자 설정을 맞대어 형식 차이를 낸다.

  python3 config-diff.py <템플릿 config> <사용자 config>

출력은 탭으로 나눈 줄이다.

  version<탭><설정 번호><탭><템플릿 번호>
  missing<탭><키><탭><기본값 JSON>

`version` 줄은 항상 낸다. `missing` 줄은 빠진 키마다 하나씩이고 없으면 안 낸다.

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
    cfg_v = parse_version(target.get("version"), "작업공간 설정")
    print("version\t{}\t{}".format(".".join(map(str, cfg_v)),
                                   ".".join(map(str, tpl_v))))

    # version 은 빼고 센다. 번호를 올리는 것은 변환을 다 돌린 뒤에 할 일이다.
    # 사용자가 직접 넣은 키는 내지 않는다. 지울 대상이 아니다.
    for key, default in template.items():
        if key != "version" and key not in target:
            print(f"missing\t{key}\t{json.dumps(default, ensure_ascii=False)}")
