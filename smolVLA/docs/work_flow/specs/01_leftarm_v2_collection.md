# 01_leftarm_v2_collection

> 목표: leftarm_v2 학습용 dataset (2 task, 총 200 episodes) 을 dev 환경에서 수집·검증
> 환경: DGX Spark 단일 노드 (수집 + Hub push), venv `~/smolvla/dgx/.arm_finetune`
> 접근: devPC → `ssh dgx`
> 코드 경로: DGX `~/smolvla/dgx/` (rsync 배포 기준)
> 하드웨어: SO-101 좌측 follower + leader (calibration 완료 — DGX `docs/status.md` §2)
> 로드맵: `realplaying.md` M1
> 작성: 2026-05-14

---

## 배경

- **leftarm_v1** (40 episodes, task `"Pick up the doll and reach forward"`) 은 **동결** — 개념적 체크포인트로 보존. 본 spec 에서 끌어오지 않음.
- **leftarm_v2** = 본 spec 작업 대상. 신규 **2 task 멀티태스크** dataset:
  - ① 파랑+노랑 인형을 테이블 왼쪽에 놓기 — `Pick up the blue and yellow doll and place it on the left side of the table`
  - ② 노란 캔을 사람에게 건네기 (hand-over) — `Hand the yellow can to the person`
  - (옛 "노란 플라스틱 상자" pick-and-place 설계는 top view 가동범위 제약 + task 다양성 확보 차원에서 2026-05-15 폐기. 상세 `docs/storage/01_collection_scenario.md` §2c.)
- 한 SmolVLA 모델이 instruction 으로 두 task 를 구분해 수행 (학습은 M2 / spec 02).
- 에피소드: **task 당 100, 총 200** (fresh 수집).
- 환경 정합 결정 포인트: **"최소 파라미터만 기록"** (2026-05-14) — 카메라·조명·작업영역 핵심값만 기록하고 dev 환경 그대로 수집. 시연장 정합은 본 로드맵 이후.
- DGX 측 수집 운영 상세: `~/smolvla/dgx/docs/data_collection.md`, 진행 현황: `~/smolvla/dgx/docs/status.md`. 차수별 실 수집 로그: `~/smolvla/dgx/docs/finetune/leftarm_v2/collection_log.md`.

---

## Todo

### [x] TODO-01: leftarm_v2 dataset 설계 확정 + config 확정 + 래퍼 — **완료 (2026-05-14)**

> 사전 설계 (Phase 1): `dgx/finetune/` 디렉터리 신설 — `leftarm_v1/`(frozen 기록), `leftarm_v2/`, `README.md`. config 설계 = **데이터셋 폴더당 `config/{base,record,train}_config.yaml` 3파일 + 래퍼 스크립트군**. **모든 lerobot-cli 인자는 config 출처** (래퍼 하드코딩 0). **세션값(포트·카메라 인덱스)은 `base_config.yaml` 의 `hardware` 섹션에 직접 입력** — 확인 전엔 `null` → 래퍼가 무조건 에러 (env 변수도 fallback 도 아님; 잘못 캐시된 값 사고 방지, 사용자 결정 2026-05-14).

**완료 (2026-05-14)**: config 3파일 + 래퍼 4파일 확정, DGX 배포 후 `run_teleop.py` 실검증 통과 + `run_record.py` dry-run 정합 확인.

- DOD: (a) `leftarm_v2/config/{base,record}_config.yaml` M1 값 확정 — **완료** (b) 단일 `leftarm_v2` repo 내 2 task 구조 확정 — **완료** (c) config → `lerobot-record`/`lerobot-teleoperate` 명령 구성 래퍼 작성·동작 확인 — **완료 (dry-run + DGX 실검증)**.
- 산출물:
  - `dgx/finetune/leftarm_v2/config/{base,record}_config.yaml` — `base_config.yaml`(셋업 컨텍스트: 식별·paths·accounts·robot/teleop/cameras·calibration·hardware), `record_config.yaml`(수집 job: dataset 옵션·record_opts·tasks). `train_config.yaml` 은 `[TBD-M2]` skeleton.
  - `dgx/finetune/leftarm_v2/_lib.py` — 래퍼 공용 헬퍼 (config 로드·경로 전개·hardware null 검사·calibration 존재 확인·robot/teleop/camera 인자 구성).
  - `dgx/finetune/leftarm_v2/check_port_and_camera_index.py` — `lerobot-find-port` ×2 + `lerobot-find-cameras opencv` 순차 실행 (hardware 값 확인용, yaml 자동 기록 X).
  - `dgx/finetune/leftarm_v2/run_teleop.py` — `lerobot-teleoperate` 래퍼 (수집 전 셋업 검증, `--no-cameras`/`--dry-run`).
  - `dgx/finetune/leftarm_v2/run_record.py` — `lerobot-record` 래퍼. `--task`/`--episodes` 런타임 인자, resume 자동감지, `--dry-run`, HF_USER 주입.
  - 데이터셋 메타 관리 = `dgx/finetune/<name>/config/` per-dataset 방식으로 확정 (구 `dgx/config/dataset_repos.json` placeholder-only 로 2026-05-14 삭제 — Backlog #3 해결).
- 검증: `lerobot-record` 23/23 · `lerobot-teleoperate` 8/8 인자 `--help` 대조 정합. DGX 배포 후 `run_teleop.py` 실검증 통과 (사용자 확인 2026-05-14). `deploy_dgx.sh` 는 `base_config.yaml`(세션 hardware 보존)·`outputs`·`gestures/*/` 제외.
- 제약: `docs/reference/` 수정 금지. lerobot dataset 포맷·draccus 인자 준수. 세션값은 `base_config.yaml` hardware 직접 입력 — `null` 시 무조건 에러 (구 `dgx/config/` 실패 교훈).
- 잔여 리스크: task instruction 문구가 모델 성능에 직접 영향 — leftarm_v1 에서 `"left/right"` 구분 불가로 dataset 재시작한 이력 있음 (DGX `status.md` §3 인시던트). v2 instruction 은 색상 기반 grounding 으로 모호성 제거.

### [ ] TODO-02: 수집 환경 최소 파라미터 기록 + 좌측팔 하드웨어 재검증

> **자동화 완료, 실측 기입 대기 (2026-05-14)**: (b)·(c) 완료 — `check_port_and_camera_index.py` 로 포트·카메라 인덱스 확인 후 `base_config.yaml` hardware 기입, `run_teleop.py` 실검증 통과로 calibration 유효성 확인. (a) 환경 파라미터 기록 문서 골격 작성 — `docs/storage/01_collection_scenario.md` §4. 카메라 물리 배치·조명·작업영역 실측값은 leftarm_v2 수집을 진행하며 `[수집 중 실측 기입]` 항목에 채우면 (a) 완료 → 본 todo `[x]` 전환.

- DOD: (a) 카메라 위치·조명·작업영역 핵심 파라미터가 기록 문서로 남음 (시연장 재현용 최소 셋) — **문서 골격 완료, 실측 기입 대기** (b) 좌측 SO-101 follower/leader 포트 + top/wrist 카메라 인덱스 재확인 — **완료** (c) 좌측팔 calibration 유효성 확인 — **완료 (run_teleop.py 실검증)**.
- 구현 대상: 환경 파라미터 기록 문서 → `docs/storage/01_collection_scenario.md` (leftarm 수집 시나리오 + §4 환경 파라미터). 하드웨어 재검증은 `dgx/finetune/leftarm_v2/check_port_and_camera_index.py` (`lerobot-find-port` ×2 + `lerobot-find-cameras opencv`).
- 테스트: `check_port_and_camera_index.py` interactive 확인 + `run_teleop.py` 실검증 (PHYS_REQUIRED — 사용자, 통과 확인 2026-05-14).
- 제약: 좌측팔 calibration 파일 보존 (유효하면 재calibration 불필요). calibration 위치: `${HF_HOME}/lerobot/calibration/`.
- 잔여 리스크: 우측팔 추가로 4 devices 환경 — `/dev/ttyACM*` enumeration 이 부팅마다 변동 가능 (DGX `status.md` §2 권고: serial 기반 udev rule). 수집 직전 재확인 필수.

### [ ] TODO-03: leftarm_v2 데이터 수집 (200 episodes)

- DOD: task ① 100 + task ② 100 = 200 episodes teleoperation 수집 완료 + HF Hub push 완료.
- 구현 대상: 수집 명령/스크립트 (`lerobot-record` 기반, DGX `dgx/docs/data_collection.md` 절차 따름). 실제 수집은 사용자 physical 작업.
- 테스트: PHYS_REQUIRED — 사용자가 직접 teleoperation 으로 수집 (차수별 resume 권장).
- 제약: 그리퍼(motor id=6) overload 방지 — 종료 시 그리퍼 살짝 열고 끝내기 (leftarm_v1 overload 크래시 이력). 차수별 분할 수집 + 휴식.
- 잔여 리스크: `push_to_hub` 크래시 가능 (leftarm_v1 이력 — disconnect 크래시로 push skip → 수동 `LeRobotDataset(...).push_to_hub(...)` 복구 필요). 수집 중 USB enumeration 변동.

### [ ] TODO-04: leftarm_v2 dataset 검증

- DOD: leftarm_v2 가 200 episodes (task 분포 100/100) 로 수집 완료됨이 확인되고, frame shape·dtype·fps 가 학습 입력으로 유효하며, HF Hub repo 와 로컬이 정합함.
- 구현 대상: 검증 점검 (meta/info.json 파싱, task 분포 카운트).
- 테스트: `ssh dgx` 로 `meta/info.json` + task 분포 확인 (SSH_AUTO) + HF Hub repo 확인.
- 제약: 없음.
- 잔여 리스크: 없음.

---

## Backlog

> 스펙 진행 중 발견된 추후 과제. 현재 워크플로우를 블로킹하지 않으나 향후 대응 필요.

| # | 항목 | 발견 출처 | 우선순위 |
|---|------|-----------|----------|
| 1 | DGX `~/smolvla/dgx/docs/` 운영 문서(status·training·data_collection·backlog)와 devPC repo `dgx/docs/` 간 drift — 동기화 정책 결정 필요 | M1 작성 (2026-05-14) | 중간 |
| 2 | 4 devices 환경 `/dev/ttyACM*` enumeration 안정화 — serial 기반 udev rule 채택 검토 | DGX status.md §2 | 중간 |
| 3 | 데이터셋 메타 관리 방식 재설계 — 구 `dgx/config/dataset_repos.json` 은 placeholder-only 로 삭제됨 (2026-05-14). 레지스트리 파일이 필요한지·형태를 TODO-01 에서 결정 | M1 작성 (2026-05-14) | 낮음 |
