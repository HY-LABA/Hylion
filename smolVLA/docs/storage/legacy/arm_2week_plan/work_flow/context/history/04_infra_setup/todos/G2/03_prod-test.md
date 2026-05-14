# TODO-G2 — Prod Test

> 작성: 2026-05-01 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

자동 검증: 정적 분석 기반 6단계 모두 이상 없음 (Bash 도구 차단으로 실 SSH 실행 불가).
사용자 실물 검증 항목 3건 → verification_queue 추가.

---

## 검증 환경

- **Bash 도구 차단 여부**: 차단됨 (SKILL_GAP #1 prod-test-runner 환경 재현 확인).
  - `ssh orin "..."` 포함 모든 Bash 명령 실행 불가.
  - 대체: Read 직독 + 정적 AST·논리 분석으로 6단계 수행.
- **Orin SSH 가능 여부**: 확인 불가 (Bash 차단). ANOMALIES.md #1 재현.

---

## 배포 대상

- orin (G2 변경: `orin/inference/hil_inference.py` 1개 파일)

## 배포 결과

- 명령: `bash scripts/deploy_orin.sh`
- 결과: **실 실행 불가** (Bash 도구 차단). 정적 확인으로 대체.
- 정적 확인 결과:
  - `scripts/deploy_orin.sh` Read 직독 완료 — rsync 패턴 이상 없음.
  - 변경 파일 `orin/inference/hil_inference.py` 는 Category B 외 → 자율 배포 조건 충족.
  - `--exclude '.hylion_arm'` 등 적절한 exclude 패턴 포함, rsync `--delete` 사용.
- 로그: N/A (실 실행 불가)

---

## 자동 비대화형 검증 결과 (6단계 — 정적 분석)

| # | 검증 | 명령 (의도) | 결과 (정적 분석) |
|---|---|---|---|
| 1 | deploy_orin.sh 실행 | `bash scripts/deploy_orin.sh` | Bash 차단 — 정적 확인: rsync 패턴 이상 없음, Category B 외 변경 |
| 2 | check_hardware.sh 문법 검증 | `ssh orin "bash -n ~/smolvla/orin/tests/check_hardware.sh"` | Bash 차단 — Read 직독 정적 분석: set -uo pipefail, case/while 패턴, heredoc quoting, 함수 return 0/1 패턴 모두 이상 없음 |
| 3 | check_hardware.sh --help | `ssh orin "bash ~/smolvla/orin/tests/check_hardware.sh --help"` | Bash 차단 — 정적 확인: usage() 함수 존재, -h|--help 분기에서 usage 호출 + exit 2 |
| 4 | check_hardware.sh resume + output-json | `ssh orin "bash ... --mode resume --quiet --output-json /tmp/hw_gate.json"` | Bash 차단 — 정적 추적: placeholder null 상태에서 soarm_port PASS (cache null 건너뜀) + cameras PASS (cache null 건너뜀) → exit=0 예상, JSON 생성 가능 |
| 5 | hil_inference.py --help (--gate-json 확인) | `ssh orin "source ... && python ... --help"` | Bash 차단 — 정적 확인: line 236-245 `--gate-json` argparse 등록 확인 (type=str, default=None, help 텍스트 포함) |
| 6 | hil_inference.py --gate-json + --follower-port 명시 | `ssh orin "source ... && python ... --gate-json ... --follower-port /dev/ttyACM0 --cameras top:0,wrist:1 2>&1 \| head -20"` | Bash 차단 — 정적 추적: load_gate_config 실행 경로 확인. cameras.json placeholder null → `top_idx is not None` False → cameras 자동채움 스킵, `[gate]` cameras 로그 미출력 (null placeholder 예상 동작). follower_port 명시로 parser.error 회피. 이후 model load 또는 SO-ARM 연결 시도 단계에서 종료 예상 (정상) |

### 정적 분석 상세 — check_hardware.sh

- `set -uo pipefail` (set -e 미사용 — 의도적, 개별 step 실패가 전체 중단 방지)
- 인자 파싱: `while [[ $# -gt 0 ]]; do case "$1" in` 패턴 정상
- heredoc: `<<'PYEOF'` single-quote quoting 으로 bash 변수 확장 차단 — Python 코드 안전
- 환경변수 경유 Python 호출 패턴: `STEP_NAME="$step_name" ... python3 -c "..."` — 특수문자 안전
- `step_venv`: `source "$VENV_ACTIVATE"` 후 `cusparseLt LD_LIBRARY_PATH` fallback 포함 (BACKLOG 03 #14 해소 패턴 확인)
- `step_soarm_port` resume 분기: `cached_follower=""` (null) → `record_step "soarm_port" "PASS" "cache follower_port=null"` 분기 진입 — placeholder 상태에서 PASS
- `step_cameras` resume 분기: `cached_top_idx=""` (null) → `[[ -n "$cached_top_idx" ]]` False → 비교 건너뜀 → PASS
- `finalize_output`: `cp "${TMP_RESULT_JSON}" "${OUTPUT_JSON}"` — output-json 지정 시 복사
- `trap 'rm -f "${TMP_RESULT_JSON}"' EXIT` — 임시 파일 정리

### 정적 분석 상세 — hil_inference.py (cycle 2 반영 확인)

- line 37: `from pathlib import Path` import 존재 확인
- line 158-162: `_to_idx` 함수 — `int(v)` 시도 → `except (ValueError, TypeError): return Path(v)` — str 반환 없음, Path 반환 확인 (Recommended #1 해소)
- line 164-175: 외부 `try/except Exception` 블록 없음 — `_to_idx` 내부 예외 처리만 존재 (Recommended #2 해소)
- line 249-251: `if args.gate_json is not None:` → `load_gate_config(args.gate_json)` → `apply_gate_config(args, ports_data, cameras_data, parser)` 흐름 정상
- `apply_gate_config` line 141: `if args.follower_port is None and ports_data is not None:` — CLI 명시 시 스킵 (하위 호환)
- `apply_gate_config` line 152: `if cameras_data is not None and args.cameras == default_cameras:` — 기본값 비교 로직 정상
- `apply_gate_config` line 168: `if cameras_data is not None and not args.flip_cameras:` — 빈 set 비교 정상

### ANOMALIES.md #1 (SKILL_GAP) 재현 결과

- 6단계 모두 Bash 도구 차단으로 실 실행 불가 — SKILL_GAP #1 prod-test-runner 환경에서도 재현 확인.
- 정적 분석으로 대체 가능 영역: 코드 구조·분기·인자 파싱·JSON schema.
- 정적 분석으로 대체 불가 영역: 실 Orin 환경 동적 검증 (venv 경로 존재, CUDA 동작, SO-ARM 연결, 카메라 발견).
- **#1 직접 해소 결과**: Bash 차단으로 `bash -n` 실행 불가 → Orin SSH 에서의 실 실행 검증은 사용자 실물 검증 단계(Phase 3)로 위임.

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 가능 | 결과 |
|---|---|---|
| 1. check_hardware.sh first-time + resume 두 모드 PASS | no (실 하드웨어 + Orin 환경 필요) | → verification_queue |
| 2. hil_inference.py 가 게이트 결과 JSON 으로 자동 인자 받아 동작 | 부분 (정적 코드 분석만, 실 동작 확인 불가) | → verification_queue |

DOD #2 정적 확인 완료 항목:
- `--gate-json` argparse 등록: ✅ (line 236-245)
- `load_gate_config` 경로 처리 (is_dir/p.parent): ✅
- `apply_gate_config` CLI 우선 로직: ✅
- `_to_idx` Path 반환 (cycle 2 Recommended #1): ✅
- dead catch 제거 (cycle 2 Recommended #2): ✅
- 하위 호환 (`--gate-json` 미지정 시 기존 동작 동일): ✅

DOD #2 정적 확인 불가 항목 (사용자 실물 필요):
- 실 ports.json/cameras.json 값 채워진 상태에서 자동 인자 적용 동작 확인
- `--gate-json` 로 `--cameras`, `--flip-cameras` 자동채움 동작 확인

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가)

1. **Orin 콘솔 first-time 모드** — 카메라 2대 + SO-ARM follower 연결 후 직접 실행:
   ```bash
   bash ~/smolvla/orin/tests/check_hardware.sh --mode first-time
   ```
   - 4단계 (venv → CUDA → soarm_port → cameras) 모두 PASS 확인
   - ports.json·cameras.json 에 실 값 갱신 확인

2. **Orin 콘솔 resume 모드** — first-time 완료 후 cache 기반 재검증:
   ```bash
   bash ~/smolvla/orin/tests/check_hardware.sh --mode resume --output-json /tmp/hw_resume.json
   ```
   - exit=0 + 4단계 PASS 확인
   - `/tmp/hw_resume.json` JSON 파싱 가능 확인

3. **hil_inference.py --gate-json 실 동작** — first-time 완료 후 (SO-ARM + 카메라 연결 상태):
   ```bash
   source ~/smolvla/orin/.hylion_arm/bin/activate
   python ~/smolvla/orin/inference/hil_inference.py \
     --gate-json ~/smolvla/orin/config/ports.json \
     --mode dry-run --output-json /tmp/hil_gate_test.json --max-steps 5
   ```
   - `[gate] follower_port ←` 로그 출력 (ports.json 자동채움) 확인
   - `[gate] cameras ←` 로그 출력 (cameras.json 자동채움) 확인
   - `[gate] flip_cameras ←` 로그 출력 (wrist flip 자동채움) 확인 (wrist.flip=true 인 경우)
   - 5 step dry-run 완료 + action JSON 저장 확인

---

## CLAUDE.md 준수

- **Category B 영역 변경된 deploy**: 해당 없음 — `orin/inference/hil_inference.py` 는 Category B 외. 자율 배포 조건 충족 (Bash 차단으로 실 실행 불가였지만 조건 자체는 충족).
- **Category A 영역 미변경**: `docs/reference/`, `.claude/` 미변경 확인.
- **Bash 차단 SKILL_GAP #1**: 정적 분석으로 대체. 사용자 실물 검증으로 동적 검증 위임.
- **자율 영역만 사용**: 코드 수정 없음 (배포·검증 역할만).

## 다음 단계

- Verdict `NEEDS_USER_VERIFICATION` → Phase 3 사용자 실물 검증 (verification_queue 3건)
- 사용자가 Orin 콘솔에서 직접 check_hardware.sh + hil_inference.py 실행 후 `/verify-result` 입력
