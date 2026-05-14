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
  - ① 인형(doll) 을 집어 상자에 넣기
  - ② 캔(can) 을 집어 상자에 넣기
- 한 SmolVLA 모델이 instruction 으로 두 task 를 구분해 수행 (학습은 M2 / spec 02).
- 에피소드: **task 당 100, 총 200** (fresh 수집).
- 환경 정합 결정 포인트: **"최소 파라미터만 기록"** (2026-05-14) — 카메라·조명·작업영역 핵심값만 기록하고 dev 환경 그대로 수집. 시연장 정합은 본 로드맵 이후.
- DGX 측 수집 운영 상세: `~/smolvla/dgx/docs/data_collection.md`, 진행 현황: `~/smolvla/dgx/docs/status.md`.

---

## Todo

### [ ] TODO-01: leftarm_v2 dataset 설계 확정

- DOD: leftarm_v2 dataset 설계가 문서로 확정됨 — (a) task instruction 문자열 2종 확정 (b) dataset 구조 결정: 단일 `leftarm_v2` repo 내 2 task vs task 별 분리 (c) HF repo id 명명 (d) 에피소드 배분 100/100 + 수집 차수 계획.
- 구현 대상: dataset 설계 결정 문서 (DGX `dgx/docs/` 또는 본 spec 부속) + `dgx/config/dataset_repos.json` 에 leftarm_v2 등록.
- 테스트: 설계 문서 정합성 검토 (lerobot dataset 포맷·multi-task 표현 방식이 `docs/reference/lerobot/` 와 일치하는지).
- 제약: `docs/reference/` 수정 금지. lerobot dataset 포맷 준수.
- 잔여 리스크: task instruction 문구가 모델 성능에 직접 영향 — leftarm_v1 에서 `"left/right"` 구분 불가로 dataset 재시작한 이력 있음 (DGX `status.md` §3 인시던트). instruction 은 모호성 없이 작성.

### [ ] TODO-02: 수집 환경 최소 파라미터 기록 + 좌측팔 하드웨어 재검증

- DOD: (a) 카메라 위치·조명·작업영역 핵심 파라미터가 기록 문서로 남음 (시연장 재현용 최소 셋) (b) 좌측 SO-101 follower/leader 포트 + top/wrist 카메라 인덱스 재확인 (c) 좌측팔 calibration 유효성 확인.
- 구현 대상: 환경 파라미터 기록 문서 (신규). 하드웨어 재검증은 `dgx/scripts/check_hardware.sh` + `lerobot-find-port` 활용.
- 테스트: `ssh dgx` read-only 하드웨어 점검 (SSH_AUTO) + 환경 파라미터 실측 (PHYS_REQUIRED — 사용자).
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
| 3 | `dgx/config/dataset_repos.json` 가 placeholder(`example_dataset`)만 등록 — leftarm_v1/v2 메타 반영 | DGX status.md §3 | 낮음 |
