"""
스피커 팩토리: Real/Mock 선택
"""

import logging
from typing import Literal

logger = logging.getLogger(__name__)


def create_speaker(
    mode: Literal["real", "mock"] = "real",
    device: str = "default",
    enable_lipsync: bool = True
):
    """
    스피커 인스턴스 생성
    
    Args:
        mode: 'real' 또는 'mock'
        device: ALSA 장치명 (real 모드에서만 사용)
        enable_lipsync: 입 서보 동기화 사용 여부
    
    Returns:
        Speaker 또는 MockSpeaker 인스턴스
    """
    if mode == "mock":
        from jetson.expression.speaker import MockSpeaker
        logger.info("✅ MockSpeaker 생성")
        return MockSpeaker(device=device, enable_lipsync=enable_lipsync)
    else:  # real
        from jetson.expression.speaker import Speaker
        logger.info(f"✅ Speaker 생성 (device: {device})")
        return Speaker(device=device, enable_lipsync=enable_lipsync)


# 기본값 설정
DEFAULT_MODE = "real"
DEFAULT_DEVICE = "default"
DEFAULT_ENABLE_LIPSYNC = True


def create_speaker_auto(use_mock: bool = False, **kwargs):
    """편의 함수"""
    mode = "mock" if use_mock else "real"
    return create_speaker(mode=mode, **kwargs)
