#!/usr/bin/env python3
"""
입 서보 모터 대화형 테스트 도구
터미널에서 각도나 명령어를 입력하면 모터가 어떻게 동작하는지 확인 가능
"""

import sys
import time
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from jetson.expression.mouth_servo import MouthServoController
import threading


def print_servo_info(servo: MouthServoController) -> None:
    """현재 서보 파라미터 출력"""
    print("\n📋 현재 서보 설정:")
    print(f"  Pin: {servo.pin}")
    print(f"  PWM 주파수: {servo.pwm_hz} Hz")
    print(f"  서보 모델: {servo.servo_model}")
    print(f"  최소 펄스: {servo.min_pulse_ms} ms")
    print(f"  최대 펄스: {servo.max_pulse_ms} ms")
    print(f"  닫힌 상태 각도: {servo.closed_angle}°")
    print(f"  열린 상태 범위: {servo.open_angle_min}° ~ {servo.open_angle_max}°")
    print(f"  이동 간격: {servo.move_interval_sec} sec")
    print(f"  하드웨어 사용 가능: {servo.is_available}")


def angle_to_pulse_ms(angle: float, servo: MouthServoController) -> float:
    """각도를 펄스 시간(ms)으로 변환"""
    angle = max(0.0, min(180.0, angle))
    pulse_ms = servo.min_pulse_ms + (angle / 180.0) * (servo.max_pulse_ms - servo.min_pulse_ms)
    return pulse_ms


def print_angle_info(angle: float, servo: MouthServoController) -> None:
    """각도에 대한 상세 정보 출력"""
    pulse_ms = angle_to_pulse_ms(angle, servo)
    period_ms = 1000.0 / servo.pwm_hz
    duty_cycle = (pulse_ms / period_ms) * 100.0
    
    print(f"\n📐 각도: {angle}°")
    print(f"  펄스 시간: {pulse_ms:.3f} ms")
    print(f"  듀티 사이클: {duty_cycle:.1f}%")
    print(f"  기간: {period_ms:.2f} ms")


def test_angle_sequence(servo: MouthServoController) -> None:
    """각도 시퀀스 테스트"""
    sequence = [
        (servo.closed_angle, "닫힘"),
        (servo.open_angle_min, "최소 열림"),
        (servo.open_angle_max, "최대 열림"),
        (servo.closed_angle, "닫힘"),
    ]
    
    print("\n▶️  각도 시퀀스 테스트 시작...\n")
    
    for angle, label in sequence:
        print(f"  {label}: {angle}°", end=" → ", flush=True)
        print_angle_info(angle, servo)
        
        if servo.is_available:
            print(f"  🔧 모터 제어 중...", flush=True)
            servo.move_to_angle(angle)
            print(f"  ✅ 완료")
        else:
            print(f"  ⚠️  (하드웨어 없음 - 시뮬레이션 모드)")
        
        time.sleep(0.5)
    
    print("\n✨ 시퀀스 테스트 완료\n")


def test_lipsync(servo: MouthServoController, duration: float = 2.0) -> None:
    """립싱크 테스트"""
    print(f"\n▶️  립싱크 테스트 시작 ({duration}초)...\n")
    
    if servo.is_available:
        print(f"  🔧 서보 초기화 중...")
        servo.initialize()
    
    stop_event = threading.Event()
    start = time.time()
    
    try:
        servo.run_lipsync_for_duration(duration, stop_event)
        elapsed = time.time() - start
        print(f"\n✅ 완료 (실제 소요: {elapsed:.2f}초)")
    except Exception as e:
        print(f"\n❌ 오류: {e}")
    finally:
        if servo.is_available:
            try:
                servo.cleanup()
            except:
                pass


def interactive_mode():
    """대화형 모드"""
    servo = MouthServoController()
    
    print("\n" + "="*50)
    print("🤖 입 서보 모터 대화형 테스트 도구")
    print("="*50)
    
    if not servo.is_available:
        print("\n⚠️  경고: Jetson.GPIO를 찾을 수 없습니다.")
        print("   하드웨어 없이 시뮬레이션 모드로 실행됩니다.")
        print("   (각도 변환 계산만 수행됩니다)\n")
    
    print_servo_info(servo)
    
    print("\n" + "-"*50)
    print("💡 사용 가능한 명령어:")
    print("-"*50)
    print("  angle <숫자>    : 특정 각도로 모터 이동 (예: angle 15)")
    print("  close           : 닫힘 (0°)")
    print("  open_min        : 최소 열림 (" + f"{servo.open_angle_min}°)")
    print("  open_max        : 최대 열림 (" + f"{servo.open_angle_max}°)")
    print("  sequence        : 각도 시퀀스 테스트")
    print("  lipsync <초>    : 립싱크 테스트 (기본값: 2초)")
    print("  info            : 현재 설정 확인")
    print("  help            : 도움말")
    print("  exit/quit       : 종료")
    print("-"*50 + "\n")
    
    while True:
        try:
            user_input = input(">>> ").strip().lower()
            
            if not user_input:
                continue
            
            parts = user_input.split()
            command = parts[0]
            
            if command in ("exit", "quit"):
                print("\n👋 종료합니다.\n")
                if servo.is_available:
                    try:
                        servo.cleanup()
                    except:
                        pass
                break
            
            elif command == "help":
                print("\n💡 명령어:")
                print("  angle <숫자>    : 특정 각도로 모터 이동")
                print("  close           : 닫힘")
                print("  open_min        : 최소 열림")
                print("  open_max        : 최대 열림")
                print("  sequence        : 시퀀스 테스트")
                print("  lipsync <초>    : 립싱크 테스트")
                print("  info            : 설정 확인")
                print("")
            
            elif command == "info":
                print_servo_info(servo)
            
            elif command == "angle":
                if len(parts) < 2:
                    print("❌ 사용법: angle <숫자> (예: angle 15)")
                    continue
                try:
                    angle = float(parts[1])
                    if not (0 <= angle <= 180):
                        print(f"❌ 각도는 0~180° 사이여야 합니다")
                        continue
                    
                    print_angle_info(angle, servo)
                    
                    if servo.is_available:
                        print(f"\n  🔧 모터를 {angle}°로 이동 중...")
                        servo.move_to_angle(angle)
                        print(f"  ✅ 완료")
                    else:
                        print(f"  ⚠️  (하드웨어 없음)")
                
                except ValueError:
                    print(f"❌ 올바른 숫자를 입력하세요 (예: 15.5)")
            
            elif command == "close":
                angle = servo.closed_angle
                print(f"\n🔽 닫는 중 ({angle}°)...")
                print_angle_info(angle, servo)
                if servo.is_available:
                    servo.move_to_angle(angle)
                    print("✅ 완료")
                else:
                    print("⚠️  (하드웨어 없음)")
            
            elif command == "open_min":
                angle = servo.open_angle_min
                print(f"\n🔼 최소 열기 ({angle}°)...")
                print_angle_info(angle, servo)
                if servo.is_available:
                    servo.move_to_angle(angle)
                    print("✅ 완료")
                else:
                    print("⚠️  (하드웨어 없음)")
            
            elif command == "open_max":
                angle = servo.open_angle_max
                print(f"\n🔼 최대 열기 ({angle}°)...")
                print_angle_info(angle, servo)
                if servo.is_available:
                    servo.move_to_angle(angle)
                    print("✅ 완료")
                else:
                    print("⚠️  (하드웨어 없음)")
            
            elif command == "sequence":
                test_angle_sequence(servo)
            
            elif command == "lipsync":
                duration = 2.0
                if len(parts) > 1:
                    try:
                        duration = float(parts[1])
                    except ValueError:
                        pass
                test_lipsync(servo, duration)
            
            else:
                print(f"❌ 알 수 없는 명령어: {command}")
                print("   'help'를 입력하여 사용 가능한 명령어를 확인하세요.")
        
        except KeyboardInterrupt:
            print("\n\n👋 종료합니다.\n")
            if servo.is_available:
                try:
                    servo.cleanup()
                except:
                    pass
            break
        except Exception as e:
            print(f"❌ 오류: {e}")


if __name__ == "__main__":
    interactive_mode()
