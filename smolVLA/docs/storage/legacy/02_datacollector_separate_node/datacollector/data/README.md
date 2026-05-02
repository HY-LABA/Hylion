# datacollector/data

lerobot-record 가 생성하는 수집 데이터셋 저장 위치.

이 디렉터리는 `.gitignore` 에 등록되어 git 추적에서 제외된다 (수백 MB ~ GB).

## 데이터 전송 (TODO-T1 결정 완료: 양방향 지원)

| 방식 | 시나리오 | 명령 |
|---|---|---|
| HF Hub | 인터넷 가용 환경 | `lerobot-record --push-to-hub --repo-id=<HF_USER>/...` |
| rsync 직접 | 인터넷 격리 / 대용량 | `scripts/sync_dataset_collector_to_dgx.sh` (TODO-T1) |

## 주의

- 데이터 수집 전 `df -h` 로 디스크 여유 공간 확인 (에피소드당 수백 MB 가능)
- 시연 종료 후 DGX 또는 HF Hub 전송 완료 여부 확인
