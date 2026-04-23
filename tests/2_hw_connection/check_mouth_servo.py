import Jetson.GPIO as GPIO
import time

# 우리가 꽂은 핀 번호 (32번 또는 33번, 현재 꽂혀있는 곳으로 맞춰주세요)
SERVO_PIN = 33

def main():
    # 이전 에러로 남은 귀찮은 경고 메시지 무시하기
    GPIO.setwarnings(False)
    GPIO.setmode(GPIO.BOARD)
    
    # PWM 모드가 아닌 일반 출력(OUT) 모드로 설정하여 에러 원천 차단!
    GPIO.setup(SERVO_PIN, GPIO.OUT)

    # 파이썬으로 직접 만드는 소프트웨어 PWM 함수
    def set_angle(pulse_ms, duration_sec):
        # 50Hz 주파수 (1주기 = 20ms = 0.02초)
        cycles = int(duration_sec * 50)
        for _ in range(cycles):
            GPIO.output(SERVO_PIN, GPIO.HIGH)
            time.sleep(pulse_ms / 1000.0)
            GPIO.output(SERVO_PIN, GPIO.LOW)
            time.sleep((20.0 - pulse_ms) / 1000.0)

    print("🤖 운영체제 락을 우회하여 서보모터 테스트를 시작합니다.")

    try:
        print("입술 닫기 (약 0도)")
        set_angle(1.0, 1.0) # 1.0ms 펄스를 1초 동안 쏴줌

        print("입술 반쯤 열기 (약 90도)")
        set_angle(1.5, 1.0) # 1.5ms 펄스를 1초 동안 쏴줌

        print("입술 크게 열기 (약 180도)")
        set_angle(2.0, 1.0) # 2.0ms 펄스를 1초 동안 쏴줌

    except KeyboardInterrupt:
        print("\n테스트를 종료합니다.")
    finally:
        GPIO.cleanup()
        print("GPIO 핀 정리가 완료되었습니다.")

if __name__ == '__main__':
    main()