# TODO-V3 — Prod Test

> 작성: 2026-05-02 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

## 배포 대상

- DGX (변경 파일: `dgx/interactive_cli/flows/training.py`)
- devPC 정적 검증만 수행 (DGX·Orin SSH 접근 불가 — 사용자 명시 환경 제약)

## 배포 결과

- SSH 불가 — 배포 스크립트(`bash scripts/deploy_dgx.sh`) 실행 불가
- devPC 정적 코드 검증 + verification_queue Phase 3 명세로 대체

## 자동 비대화형 검증 결과

| 검증 항목 | 방법 | 결과 |
|---|---|---|
| sync_ckpt_dgx_to_datacollector 실행 코드 0건 확인 | `grep subprocess + sync_ckpt` | PASS — 주석·docstring 만 잔존, 실행 코드 0건 |
| L15 (docstring 모듈 갱신 기록) | 직접 Read L16~20 | PASS — 인용 제거 기록 주석 확인 |
| L54 (SCENARIOS dict 정상) | Read L53~56 | PASS — lora 시나리오 정상 |
| L70 (케이스 1·2 guide — sync_ckpt_dgx_to_orin 인용) | Read L69~73 | PASS — `sync_ckpt_dgx_to_orin.sh` 로 정정, datacollector 인용 없음 |
| L72 (케이스 3 DataCollector 우회 → 차기 사이클 안내) | Read L76~85 | PASS — "DGX → DataCollector 우회 무효, 07_leftarmVLA 신규 예정" 메시지 확인 |
| L92 (케이스 3 안내 guide) | Read L91~93 | PASS — "DataCollector 우회 무효 — 차기 사이클 신규 예정" 문자열 확인 |
| L494·L497 (ckpt 관리 함수 docstring 갱신) | Read L494~506 | PASS — `sync_ckpt_dgx_to_datacollector.sh` → `ckpt_transfer_scenarios.md` 출처 변경 주석 확인 |
| `run_training_flow_with_dataset` 시그니처 신규 | grep def | PASS — L679 신규 함수 존재, `dataset_name: str | None = None` 파라미터 |
| `run_training_flow` 기존 함수 공존 | grep def | PASS — L644 기존 함수 그대로 공존 |
| mode.py G-4 학습 전환 시 `run_training_flow_with_dataset` 호출 | grep mode.py | PASS — L163~164 `from flows.training import run_training_flow_with_dataset` + `return run_training_flow_with_dataset(script_dir, dataset_name=dataset_name)` |
| mode.py (2) 학습 직접 진입 시 `run_training_flow` 호출 | grep mode.py | PASS — L227~228 기존 `run_training_flow` 호출 |
| smoke 동의 게이트 코드 존재 | grep `_smoke_consent_gate` | PASS — `_smoke_consent_gate()` 함수 L333~354, `flow5_train_and_manage_ckpt` 내 L599 호출 |
| smoke_test.sh 미접촉 (X3 책임 보존) | Read header + git log | PASS — 04 X3 스크립트 그대로 (preflight 5단계 포함) |
| save_dummy_checkpoint.sh 미접촉 | Read header + L23~27, L60~65 | PASS — OUTPUT_DIR 경로·save_checkpoint=true 인용 정상 |
| preflight_check.sh 미접촉 | Read header | PASS — 학습 사전 점검 5단계 스크립트 원형 보존 |
| CKPT_CASES 4건 출력 | grep key | PASS — key "1"·"2"·"3"·"4" 4건. 케이스 3 = 차기 사이클 안내 메시지 (H-(b) 결정 정합) |
| smoke_test.sh `--save_checkpoint=false` (line 75) | Read L74 | PASS — 확인 (flow 5 코드의 "smoke 는 ckpt 없음" 주석과 정합) |

## DOD 자동 부합

| DOD 항목 | 자동 검증 가능 | 결과 |
|---|---|---|
| 기존 학습 flow (preflight → 데이터셋 선택 → 학습+ckpt) 회귀 없는지 | 부분 (정적) | 코드 정합 ✅ — 실 실행은 Phase 3 |
| sync_ckpt 7라인 정정 (실행 코드 0건) | yes (grep) | ✅ |
| `run_training_flow_with_dataset` 시그니처 신규 + 기존 공존 | yes (grep) | ✅ |
| smoke_test 5~15분 동의 게이트 코드 존재 | yes (grep) | ✅ |
| smoke_test 실 실행 (5~15분) | no (SSH 불가 + >5분) | → verification_queue |
| save_dummy_checkpoint 실 실행 | no (SSH 불가) | → verification_queue |
| ckpt 케이스 4건 출력 정합 | yes (코드 Read) | ✅ (케이스 3 = 차기 사이클 안내 확인) |
| svla_so100_pickplace HF Hub 다운로드 (~100MB) | no (SSH 불가 + >100MB) | → verification_queue |
| 04 X3·T1·T2 + 05 X3 verification_queue 통합 | no (사용자 실물) | → verification_queue |

## 정적 검증 핵심 요약 (7건)

1. **sync_ckpt 7라인 정정**: L15·L54·L70·L72·L92·L494·L497 모두 주석·docstring·guide 문자열 내 안내 메시지로만 잔존. `subprocess.run` 등 실행 코드 0건 확인.
2. **케이스 3 (DataCollector 우회)**: `"DGX → DataCollector 우회 경로 무효, 차기 사이클 신규"` 안내 메시지로 교체 (H-(b) 결정 정합).
3. **`run_training_flow_with_dataset` 신규**: L679. `dataset_name: str | None = None` 파라미터로 G-4 학습 전환 인계 지원.
4. **기존 `run_training_flow` 공존**: L644. 직접 학습 mode 진입 시 mode.py L228 에서 기존 함수 호출. 회귀 없음.
5. **smoke 동의 게이트**: `_smoke_consent_gate()` 함수 존재 + `flow5_train_and_manage_ckpt` 내 smoke 분기에서 호출 확인. CLAUDE.md `>100MB 다운로드 동의` 정책 코드 반영 정합.
6. **dgx/scripts 3종 미접촉**: `preflight_check.sh`·`smoke_test.sh`·`save_dummy_checkpoint.sh` X3 당시 구조 그대로. `save_dummy_checkpoint=false` (smoke), `=true` (dummy) 분리 정합.
7. **CKPT_CASES 4건**: key "1"~"4" 구조 정상. 사용자 출력 번호와 dict key 일치.

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

DGX SSH 불가 + 다음 항목은 실 실행·환경 의존으로 자동 검증 불가:

1. **DGX 배포 + main.sh 실행** — `bash scripts/deploy_dgx.sh` 후 `bash dgx/interactive_cli/main.sh`
2. **flow 0~3**: 진입 → 장치 선택 → 환경 체크 → mode 선택
3. **flow 3 mode = (2) 학습 선택** — 또는 V2 G-4 수집 완료 후 학습 전환 Y
4. **flow 4 (학습 mode 내부) preflight**: `preflight_check.sh` 5단계 (venv·메모리·Walking RL·Ollama·디스크) PASS
5. **flow 5 데이터셋 선택**: V2 수집 dataset_name 자동 인계 또는 HF Hub `svla_so100_pickplace` 선택
6. **flow 6 smoke_test 실행**:
   - 동의 게이트 프롬프트 출력 확인 ("5~15분 소요, ~100MB 다운로드 가능" 메시지)
   - 사용자 Y → smoke_test.sh 실 실행 (5~15분)
   - 완료 후 "smoke test 는 체크포인트를 저장하지 않습니다" 메시지 확인
   - 주의: 학교 WiFi 환경 시 `svla_so100_pickplace` (~100MB) 다운로드 가능 여부 확인 — 차단 시 다른 네트워크
7. **flow 7 save_dummy_checkpoint**:
   - `dgx/scripts/save_dummy_checkpoint.sh` 직접 실행 (smoke 경로 외 별도 — save_checkpoint=true)
   - ckpt 케이스 4건 출력 확인: (1) 케이스 1·2, (2) 케이스 3 차기 사이클 안내, (3) 나중에, (4) USB
8. **G-4 단발 종료**: 학습 완료 후 mode 메뉴 재진입 X — 종료 확인
9. **04 X3·T1·T2 + 05 X3 통합**: 05 spec X3 NEEDS_USER_VERIFICATION 항목 (smoke_test + save_dummy_ckpt) 본 검증으로 완료 처리

## CLAUDE.md 준수

- Category B 영역 변경: training.py 는 `dgx/interactive_cli/flows/` — Category B 비해당 (lerobot 디렉터리 외)
- SSH 불가 → devPC 정적 검증으로 대체 (NEEDS_USER_VERIFICATION 보수적 판단)
- 자율 영역만 사용: Read·grep 정적 검증 (ssh 실행 X)
- 큰 다운로드 (>100MB) + 긴 실행 (>5분) → 사용자 동의 필요 → verification_queue 에 게이트 포함
