# dgx/interactive_cli

smolVLA Interactive CLI — dgx 노드 (학습 + 데이터 수집 책임)

## 개요

<!-- 정정 (2026-05-02): 06_dgx_absorbs_datacollector 결정으로 3-노드 → 2-노드 (orin / dgx) 전환.
     datacollector 노드 운영 종료 — DGX 가 데이터 수집 책임 흡수.
     flow 1 장치 옵션·flow 3 mode 분기 갱신은 X2 todo 에서 처리. -->
본 디렉터리는 2 노드 (orin / dgx) CLI 의 dgx 측입니다.
~~3 노드 (orin / dgx / datacollector)~~ → **06 결정으로 datacollector 제거 + DGX 가 학습·수집 두 책임 흡수.**
devPC 에서 한 곳 수정 후 deploy_orin, deploy_dgx 2 번으로 동기화하세요.

## 호출법

```bash
bash dgx/interactive_cli/main.sh
```

VSCode remote-ssh 로 DGX 에 SSH 연결 후 터미널에서 실행.

## 디렉터리 구조

```
dgx/interactive_cli/
├── README.md                  # 본 파일
├── main.sh                    # bash 진입점 (venv activate + python 호출, cusparseLt 패치 없음)
├── flows/
│   ├── __init__.py
│   ├── entry.py               # flow 0 (진입 확인) + flow 1 (orin/dgx 선택) <- F1/F2 + X2 갱신
│   ├── env_check.py           # flow 2 (학습 + 수집 통합 환경 체크)           <- X2 갱신
│   ├── mode.py                # flow 3 (수집/학습/종료 mode 분기 — G-4)       <- X2 신규
│   ├── teleop.py              # 수집 flow 3·4 (텔레오퍼레이션)                <- X2 신규 (이식)
│   ├── data_kind.py           # 수집 flow 5 (학습 종류 선택)                  <- X2 신규 (이식)
│   ├── record.py              # 수집 flow 6 (lerobot-record)                 <- X2 신규 (이식)
│   ├── transfer.py            # 수집 flow 7 (전송 — H-(b) 재정의)             <- X2 신규 (이식)
│   └── training.py            # 학습 flow 3~5 (학습 + ckpt 관리)              <- X2 갱신
└── configs/
    └── node.yaml              # 노드 식별자 (node: dgx) + venv 경로 + responsibilities
```

## 노드별 차이점 (2 노드 — 06 결정으로 datacollector 제거)

<!-- 정정 (2026-05-02): datacollector 열 삭제. 역사적 맥락은 아래 주석으로 보존. -->
<!-- datacollector: venv ~/smolvla/datacollector/.hylion_collector, node.yaml node=datacollector,
     flow 0 "이 환경 맞나요?" Y/n, flow 3+ teleop/record/transfer (D2). 운영 종료 2026-05-02. -->

| 항목 | orin | dgx |
|---|---|---|
| venv | `~/smolvla/orin/.hylion_arm` | `~/smolvla/dgx/.arm_finetune` |
| cusparseLt 패치 | main.sh 에 포함 | 없음 |
| node.yaml node 값 | `orin` | `dgx` |
| flow 0 확인 단계 | 없음 (VSCode remote-ssh) | 없음 (VSCode remote-ssh) |
| flow 3+ 모듈 | inference.py (O2 구현) | mode.py + training.py/teleop.py 등 (X2 구현 — 학습/수집 분기) |

## deploy 동기화 절차

공통 코드 수정 후 2 노드 동기화 (06 결정 — datacollector 제거):

```bash
bash scripts/deploy_orin.sh
bash scripts/deploy_dgx.sh
# deploy_datacollector.sh → legacy 이관 완료 (2026-05-02)
```

각 deploy 스크립트가 devPC → 해당 노드로 rsync 수행합니다.

## 수집 mode flow (X2 구현 — 2026-05-02)

```
bash dgx/interactive_cli/main.sh
  └─ flow 0·1: 진입 + orin/dgx 장치 선택
       └─ flow 2: env_check (preflight + 수집 mode 시 USB·카메라 체크)
            └─ flow 3: mode 선택 (G-4 결정)
                 ├─ (1) 수집 → flow 3(teleop) → flow 4(confirm) → flow 5(data_kind)
                 │          → flow 6(record) → flow 7(transfer H-(b): 로컬/HF Hub)
                 │          → "수집 완료. 바로 학습으로 진행할까요? [Y/n]"
                 │               Y → 학습 flow 자동 진입 (dataset 자동 선택)
                 │               n → 종료
                 ├─ (2) 학습 → flow 3(scenario) → flow 4(dataset) → flow 5(train+ckpt)
                 └─ (3) 종료
```

## UX — 뒤로가기 (b/back)

모든 prompt 분기점에서 `b` 또는 `back` 입력 시 직전 분기점으로 복귀합니다.

| 분기점 | b/back 동작 |
|---|---|
| flow 1 장치 선택 (entry.py) | 종료 (최상위 — 되돌아갈 상위 없음) |
| 환경 모드 선택 (entry.py) | 자동 검출값으로 진행 (최상위이므로 종료 대신 기본값 적용) |
| flow 3 mode 선택 (mode.py) | 종료 (CLI 재시작 안내) |
| teleop 사전 점검 (precheck.py) | 수집 mode 취소 |
| flow 5 학습 종류 선택 (data_kind.py) | teleop 사전 점검으로 복귀 |
| flow 6 task 텍스트 / repo_id / num_episodes (record.py) | 직전 입력 단계로 복귀 |
| flow 6 lerobot-record 실행 전 (record.py) | 실행 전 취소 |
| flow 3 시나리오 선택 (training.py) | mode 선택으로 복귀 |
| flow 4 데이터셋 선택 (training.py) | 시나리오 선택으로 복귀 |
| 시작 ckpt 선택 (training.py) | 데이터셋 선택으로 복귀 |
| ckpt 관리 전송 선택 (training.py) | 건너뜀 (로컬 저장 유지) |
| flow 7 전송 방식 선택 (transfer.py) | 건너뜀 (로컬 저장 유지) |

**subprocess 실행 중에는 뒤로가기 불가** — Ctrl+C 로만 종료 가능:
- lerobot-record (flow 6)
- run_teleoperate.sh (flow 3 teleop)
- lerobot-train (flow 5 실 학습)

helper: `flows/_back.py` — `is_back(raw)` 단일 함수 (Category C 회피: flows/ 기존 디렉터리 내 배치)

## 후행 todo

- X1 study: dgx flow 3+ 재설계 (학습 + 수집 통합) — **완료 (2026-05-02)**. `docs/storage/14_dgx_cli_flow.md` 갱신됨.
- X2 task: flow 1 (orin/dgx 2 옵션) + mode.py 신규 + 수집 flow 이식 (teleop/data_kind/record/transfer) — **완료 (2026-05-02)**.
- N1 task: dgx + orin interactive_cli 뒤로가기 b/back 패턴 일괄 적용 — **완료 (2026-05-04)**.
- X3 task: dgx/scripts/ 수집 책임 스크립트 이식 (run_teleoperate.sh 등) — 진행 중
- X4 task: dgx/pyproject.toml record + hardware + feetech extras 추가 (Category B — awaits_user)
- X5 task: dgx/scripts/setup_env.sh record extras 설치 추가 (Coupled File Rule 1)
- V1·V2·V3 prod: DGX 시연장 이동 후 SO-ARM·카메라·수집 flow·학습 flow 검증

