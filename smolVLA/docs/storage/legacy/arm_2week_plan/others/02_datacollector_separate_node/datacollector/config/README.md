# datacollector/config

DataCollector 하드웨어 설정 캐시 위치.

`orin/config/` 패턴 미러 (SO-ARM 포트 + 카메라 인덱스 저장).

## 파일

| 파일 | 내용 | 생성 시점 |
|---|---|---|
| `ports.json` | SO-ARM 리더·팔로워 포트 (lerobot-find-port 결과 캐시) | TODO-G3 first-time 모드 |
| `cameras.json` | 카메라 인덱스/flip/slot 매핑 (lerobot-find-cameras 결과 캐시) | TODO-G3 first-time 모드|

## git 추적 정책

placeholder 파일 (`ports.json`, `cameras.json`) 은 git 추적.
실 캐시 값 (시연장 배치 후 확정) 은 사용자가 커밋 여부 결정.

시연장 이동 시 포트·카메라 인덱스 변동 가능:
- `lerobot-find-port` 재실행으로 포트 재확인
- `lerobot-find-cameras opencv` 재실행으로 카메라 인덱스 재확인
