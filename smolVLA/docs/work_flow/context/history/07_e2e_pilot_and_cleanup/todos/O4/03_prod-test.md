# TODO-O4 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`NEEDS_USER_VERIFICATION`**

AUTO_LOCAL + SSH_AUTO 전 항목 PASS. 실 카메라 연결 상태에서의 `_auto_discover_cameras()` 동작 + 인덱스 정합 확인은 PHYS_REQUIRED.

---

## 배포 대상

- orin

## 배포 결과

- 명령: `bash scripts/deploy_orin.sh`
- 결과: 성공
- 로그 요약: `sent 5,440 bytes / received 45 bytes / speedup 229.54` — 변경된 파일만 증분 전송됨. 파일 목록 출력 없음 = 이미 최신 상태 또는 증분 없음. 배포 후 Orin 측 `/home/laba/smolvla/orin/inference/hil_inference.py` 존재 + 타임스탬프 2026-05-04 13:01 확인.
- Category B 해당 여부: 없음 (orin/lerobot·pyproject.toml·setup_env.sh·deploy_*.sh 미변경) → 자율 실행

---

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| devPC py_compile | `python3 -m py_compile orin/inference/hil_inference.py` | PASS |
| devPC ruff | `ruff check orin/inference/hil_inference.py` | All checks passed! |
| Orin py_compile | `ssh orin "python3 -m py_compile ~/smolvla/orin/inference/hil_inference.py"` | PASS |
| Orin --help 출력 | `ssh orin "source .hylion_arm/bin/activate && python3 hil_inference.py --help"` | 정상 출력. `lerobot-find-cameras opencv` 안내 + `--flip-cameras wrist` 안내 포함 확인 |
| Orin _auto_discover_cameras import | `ssh orin "python3 -c 'from orin.inference.hil_inference import _auto_discover_cameras; ...'"` | import OK |
| Orin OpenCVCamera.find_cameras 접근 | `ssh orin "python3 -c 'from lerobot.cameras.opencv import OpenCVCamera; ...'` | import OK, `<class 'function'>` |
| Orin _auto_discover_cameras() 실행 (카메라 미연결) | `ssh orin "python3 -c '... _auto_discover_cameras()'` | None 반환 + `[camera] 연결된 카메라를 찾지 못했습니다. lerobot-find-cameras opencv 로 확인하세요.` 출력 — graceful 처리 확인 |
| Orin README 섹션 확인 | `ssh orin "grep -n '사전 단계\|lerobot-find-cameras\|wrist 카메라 플립' README.md"` | L47 사전 단계 섹션 + L79 wrist 카메라 플립 섹션 존재 확인 |
| BACKLOG #15·#16 마킹 | `grep -n '완료.*07.*O4' BACKLOG.md` | L72·L73 각각 "완료 (07 O4, 2026-05-03)..." 형식 확인 |

---

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. argparse 또는 README 에 `lerobot-find-cameras opencv` 사전 발견 단계 명시 | yes (grep + Orin --help 출력 확인) | ✅ L282 argparse help + L36 모듈 docstring + README.md L47 섹션 |
| 2. wrist flip 필요 시 `--flip-cameras wrist` 안내 명시 | yes (grep + Orin --help 출력 확인) | ✅ L292 argparse help + L43–45 모듈 docstring + README.md L79 섹션 |
| 3. hil_inference.py 진입 시 카메라 자동 발견 fallback 추가 | yes (import OK + 미연결 graceful 확인) | ✅ `_auto_discover_cameras()` L137–190, 우선순위: CLI > gate-json > 자동 발견 > 기본값 |
| 4. 03 BACKLOG #15·#16 "완료 (07 O4, 2026-05-03)" 마킹 | yes (grep) | ✅ BACKLOG.md L72·L73 확인 |

DOD 4항 자동 검증 모두 충족. 실 카메라 연결 상태 검증만 사용자 실물 필요.

---

## 사용자 실물 검증 필요 사항 (verification_queue 추가됨)

| # | 항목 | 환경 레벨 | 절차 |
|---|---|---|---|
| O4-1 | 실 카메라 2대 연결 시 `_auto_discover_cameras()` 정상 발견 + 인덱스 정합 확인 | PHYS_REQUIRED | 시연장: SO-ARM + 카메라 2대 USB 직결 Orin 환경에서 `source .hylion_arm/bin/activate && lerobot-find-cameras opencv` 결과 확인 후 `python3 orin/inference/hil_inference.py --mode dry-run --gate-json ... --output-json /tmp/test.json --max-steps 1` (또는 `--cameras` 생략) 실행. 자동 발견 메시지 `[camera] 자동 발견 성공 — top:N, wrist:M (2대 발견)` + 인덱스가 `lerobot-find-cameras opencv` 출력과 일치하는지 확인 |

---

## CLAUDE.md 준수

- Category B 영역 변경 배포: 없음 (orin/inference/hil_inference.py + README.md + BACKLOG.md 만 변경 — 모두 Category B 외)
- 자율 영역만 사용: yes (deploy_orin.sh 자율 실행, ssh read-only·py_compile·import 검증 자율 실행)
- 동의 필요 영역 해당 없음
