#!/usr/bin/env python3
"""
스피커 재생 진단: MP3 생성 및 재생 테스트
"""

import os
import subprocess
import sys
from pathlib import Path

# 프로젝트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
os.chdir(project_root)

def test_speaker_playback():
    """스피커 재생 진단"""
    
    print("=== 스피커 재생 진단 ===\n")
    
    # 1. 오디오 기기 확인
    print("[1] 오디오 기기 확인...")
    result = subprocess.run(["pactl", "list", "short", "sinks"], capture_output=True, text=True)
    print(result.stdout)
    
    result = subprocess.run(["aplay", "-l"], capture_output=True, text=True)
    if "P5HD" in result.stdout or "USB" in result.stdout:
        print("✅ USB 스피커 감지됨\n")
    else:
        print("⚠️ USB 스피커 미감지\n")
    
    # 2. MP3 파일 생성
    print("[2] MP3 파일 생성 중...")
    try:
        from gtts import gTTS
        
        test_text = "스피커 재생 테스트입니다."
        output_file = "/tmp/speaker_test.mp3"
        
        tts = gTTS(text=test_text, lang="ko", slow=False)
        tts.save(output_file)
        
        print(f"✅ MP3 생성 완료: {output_file}")
        print(f"   파일 크기: {os.path.getsize(output_file)} bytes\n")
        
    except Exception as e:
        print(f"❌ MP3 생성 실패: {e}\n")
        return False
    
    # 3. mpg123으로 직접 재생 테스트
    print("[3] mpg123으로 직접 재생 테스트...")
    print("   (5초 내에 소리가 나야 합니다)")
    
    try:
        result = subprocess.run(
            ["mpg123", "-q", output_file],
            capture_output=True,
            timeout=10
        )
        
        if result.returncode == 0:
            print("✅ mpg123 재생 완료\n")
        else:
            print(f"❌ mpg123 재생 실패 (exit code: {result.returncode})")
            print(f"   stderr: {result.stderr.decode()}\n")
            return False
            
    except subprocess.TimeoutExpired:
        print("❌ mpg123 재생 타임아웃\n")
        return False
    except Exception as e:
        print(f"❌ mpg123 실행 실패: {e}\n")
        return False
    
    # 4. Speaker 클래스로 재생 테스트
    print("[4] Speaker 클래스로 재생 테스트...")
    
    try:
        from jetson.expression.speaker import Speaker
        
        speaker = Speaker()
        
        # MP3 파일을 play_audio_blocking으로 재생
        success = speaker.play_audio_blocking(output_file)
        
        if success:
            print("✅ Speaker.play_audio_blocking() 재생 완료\n")
        else:
            print("❌ Speaker.play_audio_blocking() 재생 실패\n")
            return False
            
    except Exception as e:
        print(f"❌ Speaker 클래스 재생 실패: {e}\n")
        return False
    
    # 5. 음성 생성 및 재생 테스트
    print("[5] 음성 생성 + 재생 통합 테스트...")
    
    try:
        from jetson.expression.speaker import Speaker
        
        speaker = Speaker()
        test_replies = [
            "첫 번째 테스트입니다.",
            "두 번째 테스트입니다.",
        ]
        
        for reply in test_replies:
            print(f"   재생: '{reply}'")
            elapsed = speaker.speak_with_lipsync(reply)
            print(f"   ✅ 완료 ({elapsed:.2f}초)\n")
        
    except Exception as e:
        print(f"❌ 통합 테스트 실패: {e}\n")
        return False
    
    # 6. 오디오 출력 경로 확인
    print("[6] 오디오 출력 경로 확인...")
    result = subprocess.run(["pactl", "get-default-sink"], capture_output=True, text=True)
    default_sink = result.stdout.strip()
    print(f"   기본 싱크: {default_sink}")
    
    if "platform-sound" in default_sink:
        print("   ℹ️  Jetson 내장 오디오로 출력 중")
    elif "usb" in default_sink.lower():
        print("   ✅ USB 스피커로 출력 중")
    else:
        print(f"   ⚠️  기본값: {default_sink}")
    
    print("\n✅ 모든 테스트 완료!")
    return True

if __name__ == "__main__":
    success = test_speaker_playback()
    sys.exit(0 if success else 1)
