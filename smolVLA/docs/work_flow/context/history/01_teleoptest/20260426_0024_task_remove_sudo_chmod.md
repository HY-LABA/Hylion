# Current Task
<!-- /handoff-task 으로 업데이트. 이전 기록: docs/work_flow/context/history/ -->

> 2026-04-26 00:20 | 스펙: `docs/work_flow/specs/01_teleoptest.md` | TODO: 02

## 작업 목표

`run_teleoperate.sh` 에서 `sudo chmod 666 /dev/ttyACM*` 제거 — `laba` 사용자가 `dialout` 그룹에 포함되어 포트 접근 권한이 이미 충족됨. sudo 불필요.

## DOD (완료 조건)

- `run_teleoperate.sh` 에서 `chmod_ports()` 함수 및 모든 호출 제거
- 각 서브커맨드(`calibrate-follower`, `calibrate-leader`, `teleoperate`, `all`)가 `sudo` 없이 바로 lerobot 명령을 실행하도록 수정
- `bash -n run_teleoperate.sh` 문법 검증 통과

## 구현 대상

- `orin/scripts/run_teleoperate.sh` — `chmod_ports()` 함수 및 호출 제거

## 현재 문제 코드

```bash
# 이 함수와
chmod_ports() {
  echo "[1/4] Granting serial device permissions"
  sudo chmod 666 /dev/ttyACM*
}

# 각 case에서의 이 호출들을 모두 제거
chmod_ports
```

## 건드리지 말 것

- `docs/reference/` 하위 전체 (read-only)
- 포트 변수(`FOLLOWER_PORT`, `LEADER_PORT`) 및 lerobot 커맨드 — 수정 불필요

## 업데이트
- `orin/scripts/run_teleoperate.sh`에서 `chmod_ports()` 함수와 모든 호출을 제거했고, `calibrate-follower` / `calibrate-leader` / `teleoperate` / `all` 경로가 모두 `sudo` 없이 바로 `lerobot` 명령을 실행하도록 정리함.
- `bash -n orin/scripts/run_teleoperate.sh`로 문법 검증을 통과함.
- 추가 prod 검증은 필요하지 않으며, 실제 디바이스 권한은 이미 `dialout` 그룹 구성을 전제로 함.

## 배포
- 일시: 2026-04-26 00:24
- 결과: 완료 (`scripts/run_teleoperate.sh` Orin 전송 확인)
