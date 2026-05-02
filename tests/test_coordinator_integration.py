#!/usr/bin/env python3
"""
Coordinator 통합 테스트: 대답 생성 → 스피커 출력
"""

import sys
import os
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timezone

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

from jetson.expression.speaker import build_tts_backend, DEFAULT_CLOVA_SPEAKER
from jetson.expression.mouth_servo import MouthServoController

def simulate_coordinator_flow():
    """Coordinator의 대답 출력 흐름 시뮬레이션"""
    
    print("=== Coordinator 통합 테스트 ===\n")
    
    # 1. TTS 백엔드 생성
    print("[1] TTS 백엔드 초기화...")
    tts_backend = build_tts_backend(is_online=True, speaker=DEFAULT_CLOVA_SPEAKER)
    print(f"✅ TTS 백엔드: {tts_backend.__class__.__name__}\n")
    
    # 2. Mouth Servo 초기화 (선택사항)
    print("[2] Mouth Servo 초기화...")
    mouth_servo = MouthServoController(pin=33)
    print(f"✅ Mouth Servo 생성 (available: {mouth_servo.is_available})\n")
    
    # 3. 시뮬레이션: 대답 출력 (Coordinator의 _speak_reply_if_any와 동일)
    def speak_reply_if_any(reply_text, stage):
        """Coordinator의 _speak_reply_if_any와 동일한 로직"""
        if not reply_text or not reply_text.strip():
            print(f"[Speaker] {stage} -> no reply_text; skip")
            return
        
        try:
            elapsed = tts_backend.speak_with_lipsync(reply_text, mouth_servo=mouth_servo)
            print(f"[Speaker] {stage} -> done ({elapsed:.2f}s)")
        except Exception as exc:
            print(f"[Speaker] {stage} -> failed: {exc}")
    
    # 4. 테스트 시나리오
    print("[3] 테스트 시나리오 실행...\n")
    
    # Greeting (wake word 감지 후)
    greeting = "네, 말씀하세요!"
    print(f"[GREETING] {greeting}")
    speak_reply_if_any(greeting, stage="greeting")
    print()
    
    # Chat reply (사용자 질문에 대한 응답)
    chat_reply = "안녕하세요! 현재 오늘 날씨는 맑습니다."
    print(f"[CHAT] {chat_reply}")
    speak_reply_if_any(chat_reply, stage="before_chat")
    print()
    
    # Standby (대화 종료)
    standby = "작업을 마쳤고, 다음 지시를 기다릴게요."
    print(f"[STANDBY] {standby}")
    speak_reply_if_any(standby, stage="after_standby")
    print()
    
    # Cleanup
    if mouth_servo:
        try:
            mouth_servo.cleanup()
            print("✅ Mouth Servo cleanup 완료")
        except Exception as e:
            print(f"⚠️ Mouth Servo cleanup 실패: {e}")
    
    print("\n✅ 통합 테스트 완료!")
    print("coordinator.py를 실행하면 LLM 대답이 자동으로 스피커로 재생됩니다.")

if __name__ == "__main__":
    simulate_coordinator_flow()
