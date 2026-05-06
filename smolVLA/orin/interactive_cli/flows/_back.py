"""interactive_cli 공통 뒤로가기 helper.

TODO-N1 (08_final_e2e, 2026-05-04):
  모든 prompt 분기점에 b/back 뒤로가기 패턴을 일관 적용하기 위한 내부 모듈.

위치 결정 사유:
  - Category C 회피: interactive_cli/common/ 등 신규 디렉터리 생성 금지이므로
    flows/ 하위 `_back.py` (밑줄 prefix 내부 모듈 컨벤션) 로 배치.
  - 규모: is_back() 단일 함수 — 각 flow 에 인라인 중복 삽입 대신 공유 모듈 사용.
  - dgx/flows/_back.py 와 orin/flows/_back.py 는 동일 코드 (두 노드 독립 설치 구조).
"""


def is_back(raw: str) -> bool:
    """사용자 입력이 뒤로가기 요청인지 확인.

    Args:
        raw: input().strip() 결과 문자열

    Returns:
        True: 'b' 또는 'back' (대소문자 무시)
    """
    return raw.lower() in ("b", "back")
