#!/usr/bin/env python3
"""
간단한 대답 테스트: 스피커로 음성 출력
"""

import sys
import os
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from jetson.expression.speaker import build_tts_backend, DEFAULT_CLOVA_SPEAKER

def test_simple_reply():
    """간단한 대답 테스트"""
    
    # TTS 백엔드 생성
    print("=== 스피커 테스트 ===")
    tts = build_tts_backend(is_online=True, speaker=DEFAULT_CLOVA_SPEAKER)
    print(f"✅ TTS 백엔드 생성: {tts.__class__.__name__}")
    
    # 테스트 대답들
    replies = [
        "네, 말씀하세요!",
        "작업을 마쳤고, 다음 지시를 기다릴게요.",
        "안녕하세요! 나는 하이리온입니다."
    ]
    
    for reply in replies:
        print(f"\n대답: {reply}")
        try:
            elapsed = tts.speak_with_lipsync(reply)
            print(f"✅ 재생 완료 ({elapsed:.2f}초)")
        except Exception as e:
            print(f"❌ 재생 실패: {e}")

if __name__ == "__main__":
    test_simple_reply()
