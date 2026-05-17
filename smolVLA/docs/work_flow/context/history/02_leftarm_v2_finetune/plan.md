# Execution Plan — 02_leftarm_v2_finetune (TODO-03 사이클)

> 작성: 2026-05-17 | planner
> spec: `docs/work_flow/specs/02_leftarm_v2_finetune.md`
> 활성 todo: **TODO-03 only**

---

## spec 본문 언급 파일·경로 실존 검증

| 파일·경로 | 상태 | 비고 |
|---|---|---|
| `orin/config/cameras.json` | 실존 확인 | `{"top": {"index": null, "flip": false}, "wrist": {"index": null, "flip": false}}` — index 미설정 (null) |
| `orin/config/ports.json` | 실존 확인 | `{"follower_port": null, "leader_port": null}` — port 미설정 (null) |
| `orin/checkpoints/` | 실존 확인 | README.md 만 존재 — 실 ckpt 없음 (정상, 다운로드 대상) |
| `orin/inference/hil_inference.py` | 실존 확인 | 기존 파일 |
| `orin/scripts/` | 실존 확인 | `run_python.sh`, `setup_env.sh` 존재 |
| `prof_computer/docs/orin_eval_2026-05-17.md` | 미존재 (신규) | TODO-03 task-executor 작성 대상 — 정상 |
| `prof_computer/docs/learning_log.md` | 실존 확인 | M1.5 학습 사이클 완전 기록 |
| `docs/storage/prof_train_setting.md` | 실존 확인 | §5-2 ckpt 다운로드 절차 + §5-3 추론 절차 + §7-5 n_action_steps 함정 |
| `dgx/docs/finetune/leftarm_v2/collection_log.md` | 실존 확인 | task1·task2 instruction 본문 확인 완료 (아래 가정 섹션 참조) |
| HF Hub `BaboGaeguri/leftarm_v2_A2_pc_2026-05-17` | 외부 확인 필요 | learning_log §M1.5 + prof_train_setting §10 기록. LoRA adapter 125MB, public. Orin 에서 다운로드 가능 여부는 prod-test-runner SSH_AUTO 점검 대상 |

### 오기재 정정 메모

- spec 본문 §TODO-03 "ckpt 다운로드 명령" 에 `<run>` placeholder 포함 (`~/smolvla/orin/checkpoints/<run>/config.json`) — 실제 다운로드 경로는 `~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17/` (repo 이름 고정). task-executor 가 이 정확한 경로를 사용할 것.
- `orin/config/cameras.json`, `orin/config/ports.json` 모두 `null` 상태 — Orin 실 환경에서 실제 값이 설정돼있을 가능성 있으나 devPC repo 버전은 null. Orin SSH 접속 후 `cat ~/smolvla/orin/config/cameras.json` 로 실 값 확인 필요 (prod-test-runner SSH_AUTO 자율 점검).

---

## 활성 todo 목록

| TODO | 상태 | 담당 사이클 |
|---|---|---|
| TODO-01 | `[x]` 완료 (2026-05-15) | — |
| TODO-02 | `[x]` 완료 (2026-05-17, M1.5 prof_computer 대체) | — |
| **TODO-03** | `[ ]` **활성 — 본 사이클 plan 대상** | 본 사이클 |
| TODO-04 | **본 사이클 범위 외** | M1 잔여 100ep 수집 완성 후 별도 사이클 |
| TODO-05 | **본 사이클 범위 외** | TODO-04 이후 진입 |

---

## DAG

TODO-03 은 단일 todo 이나 내부가 다단계 + 환경 레벨 혼합이므로 sub-step 으로 쪼개 DAG 구성.

### Group 1 (병렬 가능 — devPC 자율)

- **TODO-03-A** (평가 시트 작성) → task-executor
  - 산출: `prof_computer/docs/orin_eval_2026-05-17.md` (신규)
  - trial 번호 × {task, orientation, 성공/실패, 실패 원인 메모} 표 + 평가 기준 안내
  - Category B 영향 없음 (신규 파일, `prof_computer/docs/` 내부 실존 디렉터리)
  - Category C 체크: `prof_computer/docs/` 는 실존 디렉터리 — 신규 생성 X, 자율 가능

- **TODO-03-B** (추론 명령 wrapper + 점검 절차 문서) → task-executor
  - 산출: `orin/scripts/run_inference_leftarm_v2.sh` (신규) — thin shell script, lerobot-record CLI 호출 래퍼
  - 내용:
    1. ckpt 다운로드 명령 (`huggingface-cli download BaboGaeguri/leftarm_v2_A2_pc_2026-05-17 --local-dir ~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17`)
    2. n_action_steps 점검·수정 절차 (`grep "n_action_steps" config.json` → 1이면 50으로 수정)
    3. rename_map 정합 점검 절차 (`top→camera1`, `wrist→camera2` 학습 시 적용 → 추론 시 lerobot-record 키 일치 확인)
    4. lerobot-record eval 명령 구성 (task1·task2 instruction 별, `--policy.path`, `--policy.device`)
    5. dry-run (1-2 step) 명령 포함
  - task instruction 본문 (`collection_log.md` 확인 완료):
    - task1: `"Pick up the blue and yellow doll and place it on the left side of the table"`
    - task2: `"Hand the yellow can to the person"`
  - 추론 명령 인자 참조: `docs/reference/lerobot/` lerobot-record `--policy.path` 패턴 (Category A read-only 참조)
  - Category B 체크: `orin/scripts/` 에 신규 스크립트 추가 — `setup_env.sh` 수정 X, `deploy_*.sh` 아님 → Category B 미해당, 자율 가능
  - `orin/lerobot/` 코드 변경 X 확인 — hil_inference.py 코드 변경 X

### Group 2 (Group 1 완료 후 — 검증 단계)

- **code-tester** (TODO-03-A, TODO-03-B 산출물 검증) → AUTO_LOCAL
  - `bash -n orin/scripts/run_inference_leftarm_v2.sh` 문법 확인
  - 평가 시트 문서 구조 확인 (20 trial 표 존재, task/orientation 분류)
  - instruction 문자열 정합 확인 (collection_log 기준 task1·task2 일치)
  - lerobot-record 인자 구조 확인 (`--policy.path`, `--policy.device` 패턴)

- **prod-test-runner** (Orin SSH 점검 시퀀스) → SSH_AUTO
  - Orin SSH 접속: `cat ~/smolvla/orin/config/cameras.json` + `cat ~/smolvla/orin/config/ports.json` 실 값 확인
  - HF Hub 다운로드: `huggingface-cli download BaboGaeguri/leftarm_v2_A2_pc_2026-05-17 --local-dir ~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17`
  - config.json n_action_steps 확인: `grep "n_action_steps" ~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17/config.json`
  - 1이면 수정: `python3 -c "import json, pathlib; p=pathlib.Path('config.json'); d=json.loads(p.read_text()); d['n_action_steps']=50; p.write_text(json.dumps(d,indent=2))"`
  - rename_map 정합: `grep -i "camera" ~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17/config.json`
  - lerobot venv dry-run: `source ~/smolvla/orin/.hylion_arm/bin/activate && lerobot-record --help` (CLI 인식 확인)
  - ⚠️ `deploy_orin.sh` 호출 X (BACKLOG #1 미해결)

### Group 3 (Group 2 통과 후 — PHYS_REQUIRED 위임)

- **TODO-03-D** (20 trial live 추론) → verification_queue 등록 → Phase 3 사용자
  - 시나리오: task1 5회 × {front, back} + task2 5회 × {front, back} = 총 20 trial
  - 사용자가 `prof_computer/docs/orin_eval_2026-05-17.md` 평가 시트에 기록
  - 환경 레벨: `PHYS_REQUIRED`

---

## 병렬 그룹 요약

```
[Group 1 — devPC 자율, 병렬 가능]
  TODO-03-A  task-executor: 평가 시트 작성  →  prof_computer/docs/orin_eval_2026-05-17.md
  TODO-03-B  task-executor: 추론 wrapper + 점검 절차  →  orin/scripts/run_inference_leftarm_v2.sh

       ↓ (Group 1 완료 후)

[Group 2 — 검증 단계]
  code-tester: TODO-03-A, TODO-03-B 산출물 (AUTO_LOCAL)
  prod-test-runner: Orin SSH 점검 시퀀스 (SSH_AUTO)
    ├── cameras.json / ports.json 실 값 확인
    ├── ckpt 다운로드 + config.json 점검·수정
    └── dry-run (lerobot-record --help + 1-2 step)

       ↓ (Group 2 통과 후)

[Group 3 — PHYS_REQUIRED]
  verification_queue 등록 → Phase 3 사용자 위임
  사용자: 실 Orin + 좌측 SO-101 + 카메라로 20 trial
```

---

## 확신 가정 (병렬 진행 OK)

- **가정 1**: task1·task2 instruction 본문 — `collection_log.md` 직접 확인 완료. awaits_user 불필요.
  - task1: `"Pick up the blue and yellow doll and place it on the left side of the table"`
  - task2: `"Hand the yellow can to the person"`
- **가정 2**: `orin/scripts/` 에 신규 스크립트 추가는 Category B 미해당. `setup_env.sh` 수정 X, `deploy_*.sh` 신규 생성 X. task-executor 자율 가능.
- **가정 3**: `prof_computer/docs/` 디렉터리 실존 확인됨 — 신규 파일 추가 Category C 미해당 (기존 디렉터리 내부).
- **가정 4**: `orin/checkpoints/` 내 신규 하위 디렉터리 생성 (`leftarm_v2_A2_pc_2026-05-17/`) 은 `orin/` 내부 — Category C 미해당.
- **가정 5**: HF Hub ckpt (`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`) 는 public repo — Orin 에서 인증 없이 다운로드 가능 가능성 높음. 단 Orin 의 HF 토큰 상태는 prod-test-runner SSH_AUTO 점검 대상.
- **가정 6**: n_action_steps 함정 (prof_train_setting §7-5) — smolvla_base ckpt 기반 학습 후 push 된 ckpt 는 config.json 에 n_action_steps=1 포함 가능성 높음. prod-test-runner SSH_AUTO 로 점검 + 수정.
- **가정 7**: rename_map (`top→camera1`, `wrist→camera2`) 은 학습 시 적용됨 (learning_log + prof_train_setting §3-1 확인). 추론 시 lerobot-record 가 `observation.images.camera1/camera2` 키를 기대 — 카메라 설정과 정합 점검 필요.
- **가정 8**: `orin/lerobot/` 코드 변경 X. 추론은 기존 lerobot-record CLI 호출만 (Category B 미해당).
- **가정 9**: `deploy_orin.sh` 호출 X (BACKLOG #1 미해결). ckpt 다운로드는 Orin SSH 직접 실행.
- **가정 10**: `orin/config/cameras.json`, `orin/config/ports.json` 의 devPC repo 버전은 null 이나, Orin 실 환경에 실제 값이 설정돼있을 가능성 있음 — SSH_AUTO 점검에서 확인.
- **가정 11**: code-tester 가 `bash -n` 으로 shell script 문법 검사 가능 — devPC 에 bash 있음.

---

## 확인 필요 가정 (awaits_user)

| TODO | 질문 | 영향 | 분류 |
|---|---|---|---|
| TODO-03-C (cameras) | Orin 실 `cameras.json` 에 index 가 null 이면 `--cameras top:N,wrist:M` 인자를 사용자가 직접 지정 필요. SSH_AUTO 점검 시 null 발견 → prod-test-runner 가 사용자에게 인덱스 확인 요청 분기. | TODO-03-D live 추론 명령 완성 여부 | `awaits_user` (SSH_AUTO 점검 후 null 이면 분기) |
| TODO-03-C (ports) | Orin 실 `ports.json` 에 follower_port 가 null 이면 `--follower-port` 인자 직접 지정 필요. | 동상 | `awaits_user` (SSH_AUTO 점검 후 null 이면 분기) |
| TODO-03-D (일정) | 시연장 이동 일정 — 소요 1-2시간 예상. spec §제약 "시연장 이동 일정과 충돌 회피" 명시. | Phase 3 시작 시점 | `awaits_user` (Phase 3 진입 시 사용자 일정 확인) |

---

## Phase 3 검증 큐 후보

| Sub-step | 환경 레벨 | 검증 방식 | 비고 |
|---|---|---|---|
| TODO-03-A (평가 시트 문서) | `AUTO_LOCAL` | code-tester: Markdown 문서 형식 + trial 표 구조 (20 trial, task/orientation/성공·실패/메모 열) 확인 | Phase 3 검증 불요 |
| TODO-03-B (wrapper 스크립트 + 절차) | `AUTO_LOCAL` | code-tester: `bash -n` 문법 + instruction 문자열 정합 + lerobot-record 인자 구조 확인 | Phase 3 검증 불요 |
| TODO-03-C (Orin SSH 점검 + dry-run) | `SSH_AUTO` | prod-test-runner 자율 — ckpt 다운로드 + config.json n_action_steps 점검·수정 + rename_map 확인 + lerobot-record dry-run 1-2 step 동작 | 자율 검증, 통과 시 Group 3 진입 |
| **TODO-03-D (20 trial live 추론)** | **`PHYS_REQUIRED`** | 사용자 실물 — 실 Orin + 좌측 SO-101 + 카메라. task1/task2 × front/back × 5회 = 20 trial. 평가 시트 기록 + `/verify-result` 로 결과 보고 | Phase 3 최종 사용자 검증 |

### PHYS_REQUIRED 상세 절차 (TODO-03-D)

사용자가 Phase 3 에서 수행:

1. Orin 에 SSH 접속 → venv 활성화 (`source ~/smolvla/orin/.hylion_arm/bin/activate`)
2. ckpt 확인 (`ls ~/smolvla/orin/checkpoints/leftarm_v2_A2_pc_2026-05-17/`)
3. `prof_computer/docs/orin_eval_2026-05-17.md` 평가 시트 준비 (devPC 에서 보면서 기록)
4. task1 instruction `"Pick up the blue and yellow doll and place it on the left side of the table"` 으로 lerobot-record 실행
   - front orientation 5회 → 성공/실패 기록
   - back orientation 5회 → 성공/실패 기록
5. task2 instruction `"Hand the yellow can to the person"` 으로 lerobot-record 실행
   - front orientation 5회 → 성공/실패 기록
   - back orientation 5회 → 성공/실패 기록
6. success rate (M/N) per task per orientation + 실패 원인 메모 → `/verify-result` 로 결과 보고
7. 결과로 M2 본 학습 (200ep) 진입 가치 정량 판단:
   - 50%+ → 데이터 추가 가치 명확, M1 잔여 수집 + M2 본 학습 진입
   - 0~20% → 데이터·하이퍼파라미터·추론 환경 병목 재정렬 필요

---

## Hard Constraints 점검 결과

| 영역 | 적용 여부 | 판단 |
|---|---|---|
| Category A (`docs/reference/`, `.claude/`) | 미해당 | 변경 대상 없음 (참조만) |
| Category B (`orin/lerobot/`, `orin/pyproject.toml`, `orin/scripts/setup_env.sh`, `scripts/deploy_*.sh`) | 미해당 | `setup_env.sh` 수정 X, 신규 `run_inference_leftarm_v2.sh` 는 `deploy_*.sh` 아님 |
| Category C (새 디렉터리, 외부 의존성, 환경 변경) | cameras/ports null 시 부분 해당 | `awaits_user` 분류 처리 (SSH_AUTO 점검 후 null 이면 사용자 확인 요청) |
| Category D (rm -rf, sudo, git push --force 등) | 미해당 | 해당 명령 사용 계획 없음 |
| BACKLOG #1 (`deploy_orin.sh --delete`) | 주의 필요 | 본 사이클 `deploy_orin.sh` 호출 X. ckpt 는 Orin SSH 직접 다운로드로 대체. |

---

## 본 사이클 외 — M2 본 학습 이후

| TODO | 진입 조건 | 비고 |
|---|---|---|
| TODO-04: 2B 학습 구성 갱신 + 200ep 학습 실행 | M1 잔여 100ep 수집 완성 후 별도 사이클 | 2A 추론 결과 반영해 하이퍼파라미터 조정 |
| TODO-05: 2B 체크포인트 Orin 추론 (M2 최종) | TODO-04 이후 진입 | 2A vs 2B 성능 비교 메모 포함 |
