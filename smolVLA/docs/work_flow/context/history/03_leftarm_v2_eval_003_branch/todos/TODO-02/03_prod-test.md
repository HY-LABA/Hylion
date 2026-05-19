# TODO-02 — Prod Test

> 작성: 2026-05-19 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`** (devPC AUTO_LOCAL 검증 전부 통과 + Orin 시연장 사용자 위임 등록 완료)

---

## 배포 대상

- 해당 없음 — TODO-02 산출물은 `orin/docs/leftarm_v2/003_eval_2026-05-19.md` (문서 파일 신규 작성). 코드 변경 없으므로 `deploy_orin.sh` 실행 불필요.
- Category B (`run_inference_leftarm_v2.sh`) 수정 없음 확정 — Category B 미발동.

---

## 자동 비대화형 검증 결과

### A. AUTO_LOCAL (devPC 자율)

| 검증 항목 | 명령 / 방법 | 결과 |
|---|---|---|
| `003_eval_2026-05-19.md` 헤더·구조 | Python `re` 헤더 파싱 | **OK** — H1/H2/H3 모두 well-formed |
| `[TODO-01 완료 후 인용]` 마커 위치 | Python `re.finditer` | **OK** — 메타 섹션 `final loss` / `학습 시간` 2곳에 정확히 위치 |
| Trial 기록 행 수 (20행 골격) | Python `re` 행 파싱 | **OK** — 20행 (task1×front 5, task1×back 5, task2×front 5, task2×back 5) 완전 |
| 결과 집계 + 종합 정성 메모 빈 골격 | Python substring 검증 | **OK** — 집계 표·비교 표·종합 정성·다음 단계 모두 존재, `(현재: 빈 골격)` 마커 정확 |
| HF Hub siblings 수 | `curl HF API` | **OK** — siblings: 10 (code-tester 보고치 일치) |
| `config.json.empty_cameras` | `curl /raw/main/config.json` | **OK** — `empty_cameras: 1` (003 분기 정합) |
| `config.json.n_action_steps` | `curl /raw/main/config.json` | **OK** — `n_action_steps: 50` (wrapper line 256 일치) |
| wrapper 코드 수정 여부 | `git status orin/scripts/run_inference_leftarm_v2.sh` | **OK** — `nothing to commit, working tree clean` |
| wrapper 본 spec 사이클 커밋 여부 | `git log -3 orin/scripts/run_inference_leftarm_v2.sh` | **OK** — 최신 커밋 `ac49fc7 update(M1.5): camera_empty...` (M1.5 사이클 M. 본 spec 03 커밋 없음) |

**AUTO_LOCAL 결과: 9/9 통과**

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 가능 | 결과 |
|---|---|---|
| (a) Orin 003 ckpt 다운로드 + smoke 1회 | NO (SSH 차단 — Orin 시연장 이동 상태) | → verification_queue PHYS_REQUIRED |
| (b) `003_eval_2026-05-19.md` 신설 — camera_empty_eval 양식 mirror | YES (devPC 파일 존재 + 구조 검증) | **자동 충족** |
| (b) Trial 기록 20행 골격 완전성 | YES (Python grep) | **자동 충족** — 20행 확인 |
| (b) 결과 집계·종합 정성 빈 골격 | YES (Python substring) | **자동 충족** |
| (c) HF Hub 파일 구조 (empty_cameras=1, n_action_steps=50, adapter 44MB) | YES (curl HF API) | **자동 충족** |
| (c) wrapper 환경 변수 override 정합 확인 | YES (git status + code-tester 분석 재확인) | **자동 충족** |
| (c) Orin 실측 config (ports/cameras null 여부) 확인 | NO (SSH 차단) | → verification_queue |
| (c) Orin 측 empty_cameras 패치 실행 로그 확인 | NO (SSH 차단) | → verification_queue |

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

1. **Orin 003 ckpt 다운로드** — `bash run_inference_leftarm_v2.sh download`로 HF Hub → Orin 로컬 다운로드
2. **dry-run smoke** — `bash run_inference_leftarm_v2.sh dry-run task1` 실행 + `empty_cameras=1` 강제 적용 로그 확인
3. **Orin 실측 config 정합** — `ports.json` / `cameras.json` null 여부 확인 + 필요 시 환경 변수 override
4. **live trial (TODO-03 PHYS_REQUIRED 와 합산)** — 20 trial 진행

→ 항목 1~3 은 TODO-02 DOD 범위, 항목 4 는 TODO-03 으로 흡수. 단일 세션 연속 진행 권고.

---

## CLAUDE.md 준수

| Category | 결과 | 메모 |
|---|---|---|
| A (절대 금지 영역) | **통과** | `docs/reference/`, `.claude/` 미변경 |
| B (자동 재시도 X) | **통과 — 미발동** | `run_inference_leftarm_v2.sh` 코드 변경 없음. `deploy_orin.sh` 실행 불필요 (문서 파일만). `orin/lerobot/`, `orin/pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 전부 미변경. |
| C (사용자 동의 필수) | **통과** | `orin/docs/leftarm_v2/` 기존 디렉터리 내 신규 파일 — Category C 미해당 |
| D (절대 금지 명령) | **통과** | `rm -rf`, `sudo` 등 미사용 |
| Coupled File Rules | **해당 없음** | Category B 영역 미변경 |
| prod-test-runner 자율성 | **자율 영역만 사용** | SSH 불가 = 환경 차단. devPC AUTO_LOCAL + verification_queue 등록만 수행 |

---

## 잔여 리스크

1. **Orin SSH 불가 (현재)**: devPC → 172.16.134.117 ping 100% loss / SSH timeout. 사용자가 Orin 있는 환경에서 직접 실행해야 함. SSH 가용 시 재시도 원칙 상 자율 검증 가능 영역이나 현재 미가능.
2. **ports.json / cameras.json null 가능성**: Orin 실 값 미확인. null 이면 wrapper 가 환경 변수 override 안내 — 003_eval 시트 §trial 시작 전 체크리스트에 override 명령 포함됨.
3. **TODO-01 메타 마커 미완**: `[TODO-01 완료 후 인용]` 2곳 — TODO-04 에서 채움. verification_queue 항목 미포함 (TODO-01 AUTOMATED_PASS 로 처리됨).

---

## 다음 단계

1. 사용자가 시연장 Orin 콘솔에서 verification_queue TODO-02 항목 순차 실행 (download → dry-run → config 확인)
2. dry-run 통과 후 TODO-03 PHYS_REQUIRED 영역 (live 20 trial) 연속 진행
3. trial 완료 후 `003_eval_2026-05-19.md` 시트 직접 기입 + `/verify-result` 자연어 보고
4. orchestrator 가 TODO-02 + TODO-03 합쳐서 최종 통과 마킹 + TODO-04 진입
