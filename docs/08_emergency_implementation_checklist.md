# HYlion Emergency Implementation Checklist (One Pager)

기준일: 2026-04-21  
대상: Emergency 신호 송신/수신 구현 담당자

---

## 1) 반드시 읽어야 하는 기준 파일

- `comm/protocol.py`
- `configs/schemas/emergency_event.schema.json`
- `comm/schema_validator.py`
- `docs/07_non_ros2_pipeline_master_plan.md` (Phase 6)

요약:

- 통신은 UDP
- 메시지 형식은 JSON
- 공통 헤더 + payload 규약 준수
- emergency 우선순위는 최상위

---

## 2) Emergency 이벤트 최소 요구사항

아래 필드는 반드시 포함:

- `event_id`
- `timestamp`
- `session_id`
- `source` (`imu|so_arm|bhl|watchdog|manual`)
- `schema_version`
- `level` (`warning|critical`)
- `reason`
- `active` (true/false)

권장:

- `details` (센서 값, 오류코드, 장치 상태)

### 2.1 필드별 가이드 (무엇을 넣고, 왜 필요한가)

| 필드 | 어떤 값을 넣나 | 왜 필요한가 |
|---|---|---|
| `event_id` | 이벤트마다 유일한 ID (예: UUID, `evt-...`) | 중복 수신/재전송 상황에서 같은 이벤트인지 식별하기 위해 필요 |
| `timestamp` | UTC ISO8601 문자열 (예: `2026-04-21T12:34:56.000Z`) | 이벤트 발생 시점 추적, 로그 정렬, 장애 분석에 필요 |
| `session_id` | 현재 실행 세션 ID (예: `sess-001`) | 어떤 세션에서 발생한 emergency인지 추적하기 위해 필요 |
| `source` | `imu`, `so_arm`, `bhl`, `watchdog`, `manual` 중 하나 | 신호 발생 주체별 대응 정책(자동 해제 금지 등)을 다르게 적용하기 위해 필요 |
| `schema_version` | 현재 계약 버전 문자열 (예: `1.0`) | 송신/수신 코드가 같은 스키마를 쓰는지 호환성 검증에 필요 |
| `level` | `warning` 또는 `critical` | 즉시 정지 여부/재전송 강도/알람 정책의 우선순위를 결정하기 위해 필요 |
| `reason` | 짧고 명확한 원인 코드 또는 설명 (예: `fall_detected`, `joint_overcurrent`) | 운영 로그, 통계, 장애 리포트에서 원인 집계를 위해 필요 |
| `active` | `true`(비상 상태 활성), `false`(해제) | 래치 활성/해제 상태 전환을 명확히 표현하기 위해 필요 |
| `details` (권장) | 센서값/오류코드/추가 컨텍스트 객체 | 디버깅과 사후 분석 정확도를 높이기 위해 필요 |

### 2.2 필드 작성 규칙 (권장)

- `timestamp`는 반드시 UTC 기준으로 기록
- `reason`은 사람이 읽는 문장보다 코드형 키를 우선 사용 (예: `imu_tilt_exceeded`)
- `details`에는 민감정보 대신 진단 가능한 최소 데이터만 포함
- `critical`일 때는 `reason`과 `details`를 최대한 구체적으로 작성

---

## 3) 구현 체크리스트 (송신 측)

- [ ] `MessageType.EMERGENCY_EVENT`를 사용해 메시지 생성
- [ ] `seq`를 단조 증가로 관리
- [ ] payload를 `emergency_event.schema.json`으로 검증 후 송신
- [ ] `critical`일 때 즉시 송신 (배치 금지)
- [ ] `active=true` 발생 시 주기 재통지 정책 정의
- [ ] `active=false` 해제 이벤트를 별도로 송신
- [ ] 로그(JSONL)에 원본 payload 저장

권장 송신 정책:

- `critical`: 즉시 + ACK 미수신 시 재전송
- `warning`: 즉시 송신, 재전송 정책은 환경 설정 기반

---

## 4) 구현 체크리스트 (수신/오케스트레이터 측)

- [ ] 수신 즉시 스키마 검증 실패 여부 확인
- [ ] 검증 실패 시 실행 차단 + 에러 로그 남김
- [ ] `critical` + `active=true`면 현재 task 중단
- [ ] EmergencyLatch 활성화 (해제 전 명령 차단)
- [ ] 우선순위 적용: `emergency > stop > task`
- [ ] `active=false` 해제 조건/권한 규칙 적용
- [ ] 해제 후 상태 전이 규칙(IDLE 등) 적용

---

## 5) 테스트 체크리스트

기능 테스트:

- [ ] IMU 기반 emergency 송신 시 task 즉시 중단
- [ ] SO-ARM/BHL/watchdog/manual source별 수신 확인
- [ ] `warning`과 `critical` 분기 동작 확인
- [ ] `active=false` 해제 이벤트 처리 확인

통신/장애 테스트:

- [ ] UDP 유실 상황에서 `critical` 전달 보장 확인
- [ ] UDP 중복 수신 시 idempotent 처리 확인
- [ ] UDP 역순 도착 시 최신 `seq` 우선 처리 확인

스키마 테스트:

- [ ] 필수 필드 누락 payload 거부
- [ ] enum 위반(`level`, `source`) payload 거부

---

## 6) 빠른 샘플 payload

```json
{
  "event_id": "evt-9d5a0f56",
  "timestamp": "2026-04-21T12:34:56.000Z",
  "session_id": "sess-001",
  "source": "imu",
  "schema_version": "1.0",
  "level": "critical",
  "reason": "fall_detected",
  "active": true,
  "details": {
    "pitch_deg": 48.2,
    "roll_deg": 31.4
  }
}
```

---

## 7) 완료 기준 (DoD)

아래를 모두 만족하면 Emergency 구현 완료로 간주:

- [ ] schema-compliant payload만 송수신
- [ ] `critical` 발생 시 1회성 이벤트 누락 없이 오케스트레이터 차단
- [ ] 해제 이벤트 처리 후 정상 상태 복귀
- [ ] 장애 테스트(유실/중복/역순) 통과
- [ ] 운영 로그에서 event 추적 가능 (`event_id`, `seq`, `session_id`)
