# datacollector

smolVLA 의 DataCollector 커스텀 레이어.

## 단일 책임

- SO-ARM 직접 연결 (리더 암 + 팔로워 암)
- 카메라 입력 (시연장 카메라)
- `lerobot-record` / `lerobot-teleoperate` / `lerobot-calibrate` 실행 (데이터 수집)
- 수집 데이터셋 → HF Hub 또는 rsync 로 DGX 전달

**담당하지 않는 것**: 추론 (Orin), 학습 (DGX), 코드 배포 허브 (devPC)

## 환경

| 항목 | 값 |
|---|---|
| OS | Ubuntu 22.04 LTS (x86_64) |
| Python | 3.12 |
| venv | `.hylion_collector` |
| lerobot extras | `record + hardware + feetech` |

## 셋업

```bash
# DataCollector 머신에서 실행
cd ~/smolvla/datacollector
bash scripts/setup_env.sh
source .hylion_collector/bin/activate
```

## 디렉터리 구조

```text
datacollector/
├── README.md
├── pyproject.toml          # 의존성 정의 (record + hardware + feetech)
├── lerobot/                # upstream curated subset (옵션 B: 파일 변경 X)
├── scripts/
│   ├── setup_env.sh        # venv 생성 + lerobot editable install
│   └── run_teleoperate.sh  # SO-ARM teleop 실행
├── tests/
│   └── README.md           # 환경 점검 (TODO-G3 이식 예정)
├── config/
│   ├── README.md
│   ├── ports.json          # SO-ARM 포트 캐시 (lerobot-find-port 결과)
│   └── cameras.json        # 카메라 인덱스 캐시 (lerobot-find-cameras 결과)
└── data/                   # 수집된 dataset (.gitignore)
    └── README.md
```

런타임 생성 자산 (git 추적 안 함):
- `.hylion_collector/` — venv
- `data/` — 수집 dataset (수백 MB ~ GB)

## 관련 문서

- `docs/storage/09_datacollector_setup.md` — DataCollector 노드 설계 기준 (TODO-D1 산출물)
- `docs/storage/lerobot_upstream_check/05_datacollector_lerobot_diff.md` — upstream 대비 변경 이력
- `docs/storage/04_devnetwork.md` — devPC ↔ DataCollector 네트워크 (SSH/rsync)
- 형제 디렉터리: `orin/README.md`, `dgx/README.md`
