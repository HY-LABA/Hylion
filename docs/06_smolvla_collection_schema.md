# SmolVLA 수집 스키마 (간단 버전)

> 기준: 2026-04-15

복잡한 중첩 구조를 없애고, 실제 수집에 꼭 필요한 필드만 남긴 버전이다.

---

## 1. 세션 스키마

파일: `shared/schemas/smolvla_session.schema.json`

필수:
- `session_id`
- `created_at`

선택:
- `operator`
- `control_mode` (`teleop|scripted|assist`)
- `notes`

예시:

```json
{
  "session_id": "sess_2026_04_15_a",
  "created_at": "2026-04-15T09:00:00Z",
  "operator": "epsilon2",
  "control_mode": "teleop",
  "notes": "week3 cup/tumbler collection"
}
```

---

## 2. 에피소드 스키마

파일: `shared/schemas/smolvla_episode.schema.json`

필수:
- `episode_id`
- `session_id`
- `object_class`
- `image_dir`
- `actions_file`
- `success`

선택:
- `recorded_at`
- `rotation_deg` (`0|90|180`)
- `approach` (`front|side`)
- `failure_reason` (`none|misgrip|drop|collision|other`)
- `notes`

예시:

```json
{
  "episode_id": "ep_000123",
  "session_id": "sess_2026_04_15_a",
  "recorded_at": "2026-04-15T10:30:00Z",
  "object_class": "starbucks_cup",
  "rotation_deg": 90,
  "approach": "front",
  "image_dir": "datasets/ep_000123/images",
  "actions_file": "datasets/ep_000123/actions.json",
  "success": true,
  "failure_reason": "none",
  "notes": "clean run"
}
```

---

## 3. 사용 순서

1. 세션 시작 시 `session.json` 1개 저장.
2. 에피소드마다 `episode_*.json` 저장.
3. 학습 로더는 `session_id`로 두 파일을 연결해 읽는다.

---

## 4. 세션 분할 기준 (고정 규칙)

아래 중 하나라도 바뀌면 새 세션을 시작한다.

1. 날짜가 바뀜 (기본: 하루 1세션)
2. 수집자 변경 (`operator` 변경)
3. 수집 방식 변경 (`control_mode` 변경)
4. 카메라/테이블/조명 중 하나라도 변경
5. 하드웨어/펌웨어/로깅 코드 변경
6. 품질 이슈 발생 후 재시작 (프레임 드랍, 타임스탬프 꼬임 등)

운영 원칙:

- 애매하면 분리한다.
- 세션은 길게 끌지 말고, 조건이 바뀌는 경계에서 끊는다.
- 세션 노트(`notes`)에 변경 사유를 1줄로 남긴다.

---

## 5. 세션 내부 에피소드 변형 규칙

세션 내부에서는 환경은 고정하고, 태스크 변형만 바꾼다.

고정(세션 내 유지):

- `operator`
- `control_mode`
- 카메라 위치/각도/해상도
- 테이블/조명

변형(에피소드마다 변경):

- `object_class`: `starbucks_cup | tumbler | doll`
- `rotation_deg`: `0 | 90 | 180`
- `approach`: `front | side`
- 물체 시작 위치: 마커 기준 소범위 이동

권장 분포(세션당):

- 물체 클래스 균형: 각 클래스 비율이 한쪽으로 치우치지 않게 유지
- 회전 균형: `0/90/180`이 고르게 포함되도록 수집
- 접근 균형: `front/side`가 모두 포함되도록 수집
- 성공/실패 기록: 실패도 `failure_reason`과 함께 저장

---

## 6. 학습용 데이터 구성 규칙

학습 직전에는 에피소드를 세션 단위로 먼저 나누고, 그다음 split을 만든다.

1. 품질 필터링
- 파일 누락, 손상, 비정상 길이 에피소드 제외
- `success=false` 데이터는 별도 태그 후 유지/제외 정책 적용

2. 세션 단위 split
- 같은 세션의 에피소드는 가능한 한 같은 split으로 묶는다.
- train/val/test 간 세션이 섞여 누수되지 않게 한다.

3. 커버리지 점검
- 각 split에 물체/회전/접근 조합이 최소한으로 포함되는지 확인

4. 학습 실행
- 로더가 `session_id`로 `session.json`과 `episode_*.json`을 결합
- 결합 결과를 기준으로 이미지/액션을 읽어 SmolVLA 학습

---

## 7. Week3 운영안 (권장)

1. 오전 세션: `teleop`, 컵/텀블러 중심
2. 오후 세션: `teleop`, 인형 + 어려운 각도 보강
3. 세션 종료 시 품질 점검 후 다음 세션 설계

핵심:

- 세션은 "조건 고정 묶음"
- 에피소드는 "변형 실험 단위"
- 학습 split은 "세션 경계 존중"으로 누수 방지
