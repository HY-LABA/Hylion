"""interactive_cli 공통 뒤로가기 helper.

모든 prompt 분기점에 b/back 뒤로가기 패턴을 일관 적용하기 위한 내부 모듈.
flows/ 하위 `_back.py` 배치 (밑줄 prefix 내부 모듈 컨벤션).
is_back() 단일 함수 — 각 flow 에 인라인 중복 삽입 대신 공유 모듈 사용.
"""


def is_back(raw: str) -> bool:
    """사용자 입력이 뒤로가기 요청인지 확인.

    Args:
        raw: input().strip() 결과 문자열

    Returns:
        True: 'b' 또는 'back' (대소문자 무시)
    """
    return raw.lower() in ("b", "back")
