# TODO-01 — prod-test-runner 검증

> 작성: 2026-05-19 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

## 환경 레벨

AUTO_LOCAL — devPC 자율 검증, 사용자 추가 검증 불요

## 배포 대상

없음 — 본 todo 는 문서 정리 + HF Hub 원격 검증. orin/dgx 배포 없음.

---

## 검증 결과

### A. learning_log.md §003 entry sanity

- **markdown well-formed**: OK
  - 헤더·표·링크 구조 파싱 이상 없음
  - line 570~657: §003 entry. line 660~715: M1.5/002/003 비교 표 (총 715 line, `wc -l` 확인)
- **헤더 깊이 일관성**: OK
  - §M1.5 중간점검 학습 (line 188): `### M1.5 중간점검 학습 (PC) — ...` (H3)
  - §camera_empty (line 393): `### camera_empty 분기 학습 — ...` (H3)
  - §003 (line 570): `### 003 분기 학습 — ...` (H3)
  - 하위 섹션 모두 `####` (H4): smoke 검증·본 학습·HF Hub 검증·추론 평가 결과 메모 — 3 entry 간 동일 패턴
- **표 컬럼 일관성**: OK
  - 비교 표 4개 하위 표 (`학습 설정`, `학습 메트릭`, `시스템 메트릭`, `추론 평가`) 모두 `지표/설정 항목 | M1.5 (001) | 002 (camera_empty) | 003 (5변수 종합)` 3-column 구조 일관
- **§camera_empty entry 대비 누락 항목 (Recommended, 비Critical)**:
  - `#### 다음 단계`, `#### best ckpt 선정`, `#### 본 사이클 의의` 섹션 미존재
  - code-tester Recommended #1/#2 와 동일 — TODO-04 완료 후 갱신 예정. 본 verdict 영향 없음.

### B. wandb 마커 후속 경로

- **마커 위치 명확**: OK
  - 총 18개 `[wandb run 40kzxlmq 확인]` 또는 `[wandb 40kzxlmq]` 마커 확인
  - 본 학습 메트릭 표 (line 614~617): dataloading_s, final loss, loss steady, grad_norm 후반
  - 시스템 메트릭 표 (line 629~633): VRAM steady, GPU power/util/temp, System Memory
  - 비교 표 (line 687~703): final loss, loss steady, grad_norm, GPU power/util/temp, System Memory, RAM 누수
  - 각 마커는 사용자가 `wandb.ai/babogaeguri-hanyang-university/leftarm_v2/runs/40kzxlmq` 에서 직접 확인 후 갱신 가능 위치 (셀 내 인라인)
- **사용자 후속 채움 경로 명시**: OK
  - `01_implementation.md` §잔여 리스크 (line 67-68): "사용자가 wandb.ai/.../40kzxlmq 에서 직접 확인 후 [...] 갱신 필요. TODO-04 (결과 집계 보고) 에서 처리 권장" 명기
  - `learning_log.md` line 622: wandb 메트릭 미추출 사유 주석 존재
  - wandb 는 TODO-04 단계 사용자 작업으로 명확히 위임됨

### C. HF Hub 재검증 (prod-test-runner 직접 curl 실행)

- **siblings**: 10개, 정합 ✅
  - `.gitattributes`, `README.md`, `adapter_config.json`, `adapter_model.safetensors`, `config.json`, `policy_postprocessor.json`, `policy_postprocessor_step_0_unnormalizer_processor.safetensors`, `policy_preprocessor.json`, `policy_preprocessor_step_5_normalizer_processor.safetensors`, `train_config.json`
  - spec 요구 9개 파일 전부 ⊂ 10개 siblings 확인
- **`config.json.empty_cameras`**: **1** ✅ (003 분기 정합)
- **`config.json.n_action_steps`**: **50** ✅ (M1.5/002 동일값 — Hub 함정 회피 정합)
- **`config.json.chunk_size`**: **50** ✅
- **`adapter_config.json.r`**: **16** ✅ (LoRA r=16 all-linear 정합)
- **`train_config.json.steps`**: **120000** ✅
- **`train_config.json.batch_size`**: **6** ✅
- **`train_config.json.scheduler` (구조 주의)**: `train_config.json` 에서 `scheduler_decay_steps` 는 최상위 키 아님. 실제 구조: `scheduler.num_decay_steps = 120000`. 값 자체(120000) 는 정합이나 task-executor/code-tester 보고서의 "train_config.json.scheduler_decay_steps = 120000" 표현은 키 경로 오류. 본 verdict 에 영향 없음 (값 정합). 사후 참고용으로 기록.

### D. Hard Constraints

- **Category A**: OK — `docs/reference/` 미변경, `.claude/` 미변경
- **Category B**: OK — `orin/lerobot/`, `orin/pyproject.toml`, `scripts/deploy_*.sh`, `.gitignore` 미변경
- **Category C**: OK — 새 디렉터리 생성 없음, 외부 의존성 추가 없음
- **Category D**: OK — 금지 명령 미사용
- **Coupled Rules §6**: OK — `learning_log.md` 본문 직접 entry 추가 (line 570~715 append). ⚠️ 박스 누적 패턴 없음. 본문 정정 원칙 준수.
- 4 카테고리 모두 통과

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 여부 | 결과 |
|---|---|---|
| (a) wandb metric 추출 → §003 entry 추가 | yes (파일 구조·마커·주석 확인) | ✅ (부분 충족 — 마커 처리 합리적, 후속 경로 명시) |
| (b) M1.5·002·003 비교 표 작성 | yes (파일 내용 직접 확인) | ✅ |
| (c) HF Hub repo 파일 구조 검증 — siblings 10개 + empty_cameras=1 | yes (curl 직접 재검증) | ✅ |

---

## verification_queue 등록 항목

없음 — AUTO_LOCAL 전용 todo. 사용자 추가 검증 항목 없음.

참고: wandb metric 후속 채움 (사용자가 wandb 페이지 보고 `[wandb run 40kzxlmq 확인]` 마커 갱신) 은 TODO-04 단계 사용자 작업으로 위임. 본 verdict 와 무관.

---

## 보조 발견 사항 (비Critical)

- `train_config.json` 의 `scheduler_decay_steps` 키 경로 오류: 보고서에서 `train_config.json.scheduler_decay_steps` 로 참조했으나 실제 HF Hub JSON 에서는 `scheduler.num_decay_steps` 로 중첩 구조. 값(120000) 은 정합이므로 기능 무관. 사후 참고용 기록.

## 잔여 리스크

- wandb 실측 메트릭 (final loss, grad_norm 후반, GPU steady chart) 미채움 — TODO-04 단계 사용자 직접 기입으로 위임. 본 spec DOD 블로킹 없음.

## CLAUDE.md 준수

- Category B 영역 변경된 배포: 해당 없음 (코드 변경·배포 없음)
- AUTO_LOCAL 자율 영역만 사용: yes (curl·grep·wc-l 만)
- SSH 호출: 없음
