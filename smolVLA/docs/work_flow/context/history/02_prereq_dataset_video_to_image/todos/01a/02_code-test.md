# TODO-1a — Code Test

> 작성: 2026-05-15 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 이슈 0건. Recommended 개선 사항 2건.

---

## 단위 테스트 결과

```
bash -n dgx/finetune/leftarm_v2/experiments/cleanup_helper.sh
→ 문법 오류 없음 (SYNTAX_OK)

shellcheck: 미설치 — 스킵
```

---

## Lint·Type 결과

```
대상 파일: cleanup_helper.sh (bash), exp_a_cleanup_attempt3.md, training_log.md, dgx/finetune/README.md
Python 파일 없음 — ruff/mypy 해당 없음

Category D 패턴 grep:
  grep -n 'rm -rf|sudo|git push --force|chmod 777|curl.*| bash' cleanup_helper.sh
  → sudo 관련 라인 확인:
    line 96: echo "  sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'"  (echo 출력만, 실행 X)
    line 97: echo "  (sudo 가능 시 ..." (echo 출력만)
    line 109: echo "    sudo 가 가능하면 ..."  (echo 출력만)
    line 110: echo "      sudo sh -c 'echo 3 > /proc/sys/vm/drop_caches'"  (echo 출력만)
  → sudo 명령 직접 실행 없음. echo 로 안내만. Category D 위반 없음.
```

---

## DOD 정합성

### cleanup_helper.sh DOD (a)~(h)

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| (a) `pkill -9 -f code` — VSCode | ✅ | line 32: `run_cmd "pkill -9 -f code 2>/dev/null || true"` |
| (b) `pkill -9 -f 'claude'` — Claude Code | ✅ | line 36: `run_cmd "pkill -9 -f 'claude' 2>/dev/null || true"` |
| (c) `pkill -9 -f firefox` | ✅ | line 40: `run_cmd "pkill -9 -f firefox 2>/dev/null || true"` |
| (d) 3초 대기 후 `pgrep` 잔존 확인 + 경고 | ✅ | lines 43-67: sleep 3 후 pgrep × 3 + RESIDUAL 배열로 경고 출력 |
| (e) `sync` | ✅ | line 72: `run_cmd "sync"` |
| (f) `free -h` 출력 | ✅ | lines 76-81: `free -h` 직접 실행 (dry-run 시 DRY-RUN 표시) |
| (g) MemAvailable 100GB+ 검증 (미만이면 exit 1) | ✅ | lines 85-104: `/proc/meminfo` awk 로 kB 추출, 104857600 kB (=100GB) 미만 시 exit 1 |
| (h) `echo 3 > /proc/sys/vm/drop_caches` — 실행 X, echo 안내만 | ✅ | lines 107-112: echo 로 안내 문자열만 출력, 실제 실행 없음 |
| `--dry-run` 옵션 분기 | ✅ | lines 7-10: `${1:-}` 파싱, run_cmd 래퍼 전 분기 |
| `set -euo pipefail` | ✅ | line 5: `set -euo pipefail` |
| Category D 명령 미포함 | ✅ | sudo/rm -rf/chmod 777/curl\|bash 직접 실행 없음 |

### TODO-1a DOD (a)~(e) 전체 매핑

| spec DOD | 항목 | 충족 | 메모 |
|---|---|---|---|
| (a) | `exp_a_cleanup_attempt3.md` 신규 — 단계별 절차 문서 | ✅ | 파일 존재, 7단계 실행 순서 + 판정 기준 포함 |
| (b) | `cleanup_helper.sh` — pkill × 3 + free -h + MemAvailable 100GB+ 검증 + exit 1 | ✅ | 모든 항목 충족 확인 |
| (c) | memory monitor 명령 + wandb 가이드 | ✅ | `watch -n 30 'free -h | grep -E "Mem|Swap" | tee -a /tmp/exp_a_mem.log'` 5단계에 포함. wandb 모니터링 언급 있음 |
| (d) | 학습 명령 시도 2 와 동일 + train_config.yaml 무변경 | ✅ | 변수 분리 표 명시. 6단계 명령 `python run_train.py train --pass 2a` |
| (e) | training_log.md "시도 3" 섹션 추가 (빈 기록 양식) | ✅ | 232줄 이후 섹션 추가됨. 항목: 사전점유/cleanup후/학습실행/30분결과/판정 |

### exp_a_cleanup_attempt3.md 필수 섹션 점검

| 필수 섹션 | 존재 | 비고 |
|---|---|---|
| 배경 (시도 1·2 OOM-kill 증거 인용) | ✅ | dmesg VSCode 2회 kill, 누수율 1805→1254 MB/min 인용 |
| 변수 분리 표 (시도 2 와 동일 명시) | ✅ | 6개 변수 표, cleanup 외 모두 "동일" 명시 |
| 사전 조건 체크리스트 | ✅ | DGX 접속·학습 프로세스 없음·디스크 여유·venv 활성화 4항목 |
| 실행 순서 1~7 (명령 시퀀스 + 예상 출력) | ✅ | 7단계. 3단계에 예상 출력 블록 포함 |
| 성공 판정 기준 | ✅ | MemAvailable > 70 GB, step 500+, dmesg OOM 없음 |
| 실패 판정 | ✅ | OOM SIGKILL / MemAvailable < 30 GB / dmesg oom-kill |
| 결과 기록 가이드 (training_log.md 시도 3 섹션 가리킴) | ✅ | "dgx/docs/finetune/leftarm_v2/training_log.md" 명시 |
| 다음 단계 (성공/실패 분기) | ✅ | 성공: TODO-1b 폐기 / 실패: TODO-1b 진입 |

### training_log.md 시도 3 섹션 양식 점검

| 양식 항목 | 존재 | 메모 |
|---|---|---|
| 사전 점유 (cleanup 전) | ✅ | "(사용자 기록 — free -h 출력 또는 MemAvailable 수치)" |
| cleanup 후 (kill 결과·MemAvailable·drop_caches Yes/No) | ✅ | 종료된 프로세스·MemAvailable·page cache drop 수행 여부 3항목 |
| 학습 실행 (시작 시각·명령·wandb URL) | ✅ | 시작 시각·명령·wandb run URL 3항목 |
| 30분 시점 결과 (peak·min·step·step_time·누수율 비교) | ✅ | MemAvailable peak/min·도달 step·step_time 평균·누수율(시도 1·2와 비교) 5항목 |
| 판정 (성공/실패·dmesg OOM·후속 액션) | ✅ | 성공/실패·dmesg OOM 메시지 유무·후속 액션 3항목 |
| 기존 시도 1·2 내용 손상 여부 | ✅ | git diff 확인: 기존 내용 무변경, 끝에 새 섹션만 append |

---

## Critical 이슈

없음.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `cleanup_helper.sh` line 32: `run_cmd "pkill -9 -f code 2>/dev/null \|\| true"` | `pkill -9 -f code` 는 `lerobot-train` 등 "code" 가 포함된 다른 프로세스도 kill 할 수 있음. 예: `/home/.../code_xxx` 형태의 경로. 운영상 위험은 낮으나 `pkill -9 -f 'code-server\|code --'` 등으로 더 정확한 패턴 사용 권장. (단 DGX 에서 VSCode server 프로세스명 확인 후 결정할 사안이므로 Recommended) |
| 2 | `exp_a_cleanup_attempt3.md` 성공 판정 기준 — MemAvailable > 70 GB | researcher 보고서 §5 실험 A 확인 기준은 "MemAvailable 이 90 GB 이상 유지되면 성공"으로 기술되어 있으나, 본 문서는 70 GB 기준을 사용. 기준 불일치가 있음. 70 GB 기준도 합리적이나 (시도 1·2 가 30분 내 OOM zone 진입 대비 완화), 보고서 §5 의 90 GB 와 일치시키거나 낮은 기준의 근거를 명시하는 편이 사용자 판단에 도움됨. |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/` 미변경. |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/`, `orin/pyproject.toml`, `setup_env.sh`, `deploy_*.sh`, `.gitignore` 미변경. |
| Coupled File Rules §6 | ✅ | `dgx/finetune/README.md` 본문 구조 트리에 `experiments/` 및 두 파일 직접 등록됨. 박스 누적이 아닌 본문 정정. |
| Category D 명령 | ✅ | sudo 는 echo 안내 문자열에만 포함, 직접 실행 없음. rm -rf·chmod 777·curl\|bash 없음. |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | docs/storage/ 미변경. |

---

## 독자 수행 가능성 평가

exp_a_cleanup_attempt3.md 만으로 DGX 에서 사용자가 독자 수행 가능한지:

- 사전 조건 체크리스트 4항목 — 명확
- 7단계 명령 시퀀스 — 각 단계 명령 + 예상 출력 있음
- 5단계 `watch` 명령과 6단계 `python run_train.py` 명령 순서가 명확 (5단계: 새 터미널에서 명시)
- 판정 기준 (성공/실패) — 수치 기준 명확
- 결과 기록 위치 (`training_log.md` 시도 3 섹션) — 명확

평가: **독자 수행 가능**. 사용자가 본 문서만으로 실험 A 를 완결하게 수행할 수 있음.

---

## 배포 권장

**yes** — prod-test-runner 진입 권장.

Recommended 2건 (패턴 정밀도, 판정 수치 불일치) 은 사용자 수행에 장애 없음. READY_TO_SHIP.
