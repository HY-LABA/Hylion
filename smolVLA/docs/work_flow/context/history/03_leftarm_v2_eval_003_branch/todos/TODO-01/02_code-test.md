# TODO-01 — Code Test

> 작성: 2026-05-19 | code-tester | cycle: 1

## Verdict

**`READY_TO_SHIP`**

Critical 0건. Recommended 2건 이하 (2건).

---

## 단위 테스트 결과

```
대상 변경 파일: prof_computer/docs/leftarm_v2/learning_log.md (문서 전용 변경)
코드 변경 없음 — pytest 실행 대상 없음.
```

AUTO_LOCAL 범위: HF Hub API 조회 + 파일 구조 확인. 아래 E항 참조.

## Lint·Type 결과

```
대상 파일: prof_computer/docs/leftarm_v2/learning_log.md (.md 파일)
ruff / mypy 미적용 영역 (Python 코드 없음).
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| (a) wandb run 40kzxlmq 학습 metric 추출 → §003 entry 추가 | ✅ 부분 충족 (합리적) | train_config.json + smoke commit 기반 항목 모두 채움. wandb 직접 접근 필요 항목(final loss, loss band, grad_norm 후반, 시스템 차트) 만 `[wandb run 40kzxlmq 확인]` 마커 처리 — 후속 채움 경로 명시됨 |
| (b) M1.5·002·003 비교 표 | ✅ | line 660–715: 학습 설정·학습 메트릭·시스템 메트릭·추론 평가 4개 하위 표로 구성 |
| (c) HF Hub repo 파일 구조 검증 — adapter·config·preprocessor·postprocessor + `config.json.empty_cameras=1` | ✅ | siblings 10개 모두 확인. `config.json.empty_cameras=1` code-tester 직접 재검증 완료 |

---

## A. DOD 충족

- **(a) wandb metric 추출**: 부분 성공 — 합리적. train_config.json 에서 추출 가능한 항목 (steps, batch_size, epoch, lr final, scheduler_decay_steps, ckpt 수, save_freq) + smoke commit 5715da5 에서 추출 가능한 항목 (step time ~0.48s, VRAM peak 79.52%) 은 모두 채워짐. wandb API 또는 페이지 직접 접근이 아니면 알 수 없는 항목 (final loss, loss steady band, grad_norm 후반, GPU power/util/temp steady, System Memory, Disk 학습 후) 은 `[wandb run 40kzxlmq 확인]` 마커로 처리 — 이 항목들은 devPC 에 wandb 패키지 미설치 + wandb 페이지 JS 렌더링 (WebFetch 접근 불가) 상황에서 자동 추출 *불가능한 항목* 이므로 마커 처리는 합리적.
- **(b) 비교 표**: 3-way 표 신설 확인. 학습 설정·학습 메트릭·시스템 메트릭·추론 평가 4개 하위 표. 양식은 §camera_empty 내 `### M1.5 (001) 와의 비교` 표의 확장 형식으로 일관.
- **(c) HF Hub 검증**: code-tester 가 `curl -L https://huggingface.co/BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6/resolve/main/config.json` 로 직접 재검증. `empty_cameras=1`, `n_action_steps=50`, `chunk_size=50` 확인. HF API 로 siblings 10개 독립 확인.

---

## B. 양식 mirror 검증

§003 entry 구조:

| 섹션 | §camera_empty 존재 | §003 존재 | 판정 |
|---|---|---|---|
| `#### smoke 검증` | ✅ | ✅ | 일치 |
| `#### 본 학습` (메트릭 표 포함) | ✅ | ✅ | 일치 |
| `#### HF Hub 검증` | ✅ (§002 본 학습 내 inline) | ✅ (독립 섹션) | 동등 (003 이 더 명시적) |
| `#### 추론 평가 결과 메모` | ✅ (§002 `다음 단계` 내 추론 평가 언급) | ✅ (독립 섹션, 빈 값 placeholder) | 일치 |
| `#### 다음 단계` | ✅ | ❌ 미존재 | Recommended (아래 #1) |
| `#### best ckpt 선정` | ✅ | ❌ 미존재 | Recommended (아래 #2) |
| `#### 본 사이클 의의` | ✅ | ❌ 미존재 | Recommended (아래 #2) |

spec 제약 ("본 entry 는 본 학습 metric 위주") 과 TODO-04 에서 집계 완성 예정이라는 점에서 `다음 단계`·`best ckpt 선정`·`본 사이클 의의` 생략은 *비합리적 누락은 아님*. 단 DOD 가 "양식 동일" 을 명시했으므로 Recommended 로 분류.

비교 표 양식 vs §camera_empty `### M1.5 (001) 와의 비교`: 003 비교 표는 §camera_empty 2-way 표를 3-way 로 확장한 형식 — 정합 확인.

---

## C. wandb metric 누락 처리 평가

- **마커 처리 합리성**: 합리적. devPC 에 `wandb` 패키지 미설치 + wandb 페이지 JS 렌더링 의존으로 WebFetch 불가. train_config.json + smoke commit 에서 추출 불가능한 항목 (final loss, loss band, grad_norm 후반, 시스템 차트 실측값) 만 마커 처리.
- **후속 채움 경로 명시**: 명시됨. `01_implementation.md` §잔여 리스크 에 "사용자가 wandb.ai/.../runs/40kzxlmq 에서 직접 확인 후 [...] 갱신 필요. TODO-04 (결과 집계 보고) 에서 처리 권장" 명기. learning_log.md §003 본 학습 섹션 내 wandb 메트릭 미추출 사유 주석도 포함됨 (line 622).
- **결론**: MINOR_REVISIONS 사유 불필요 — 마커 처리 합리적 + 후속 채움 경로 명시 완료. N/A (Critical·MINOR 발동 불필요).

---

## D. Hard Constraints

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경. `.claude/agents/*.md`, `.claude/skills/**/*.md`, `.claude/settings.json` 미변경. |
| B (자동 재시도 X 영역) | ✅ | `orin/lerobot/`, `orin/pyproject.toml`, `orin/scripts/setup_env.sh`, `scripts/deploy_*.sh`, `.gitignore` 미변경. |
| C (사용자 동의 필수) | ✅ | 새 디렉터리 생성 없음. 외부 의존성 추가 없음. |
| D (절대 금지 명령) | ✅ | Bash rm -rf / sudo 등 미사용. |
| Coupled Rules §6 | ✅ | `learning_log.md` 본문 직접 entry 추가 (line 570~715 append). 박스 누적 패턴 없음 — 본문 정정 원칙 준수. |
| 옛 룰 (docs/storage/ bash 예시) | ✅ | `docs/storage/` 미변경. |

4 카테고리 모두 통과.

---

## E. HF 정합

code-tester 직접 재검증 결과:

| 검증 항목 | task-executor 보고 | 재검증 결과 | 판정 |
|---|---|---|---|
| siblings 수 | 10개 | 10개 독립 확인 | ✅ 정합 |
| spec 요구 9개 파일 | 모두 존재 | siblings 목록에서 확인 | ✅ 정합 |
| `config.json.empty_cameras` | 1 | curl -L 직접 확인: `1` | ✅ 정합 |
| `config.json.n_action_steps` | 50 | 직접 확인: `50` | ✅ 정합 |
| `config.json.chunk_size` | 50 | 직접 확인: `50` | ✅ 정합 |

siblings: `.gitattributes` + `README.md` + `adapter_config.json` + `adapter_model.safetensors` + `config.json` + `policy_postprocessor.json` + `policy_postprocessor_step_0_unnormalizer_processor.safetensors` + `policy_preprocessor.json` + `policy_preprocessor_step_5_normalizer_processor.safetensors` + `train_config.json`. spec 명시 9개 ⊂ 10개 정합 확인.

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| 1 | `learning_log.md` §003 entry | `#### 다음 단계` 섹션 (placeholder 1-2줄) 추가 — §camera_empty 양식 완전 mirror 목적. TODO-04 완료 후 갱신 형태로 placeholder 처리 가능. 학습 흐름 추적 시 다음 사이클 연결 포인트가 없음. |
| 2 | `learning_log.md` §003 entry | `#### best ckpt 선정` 또는 `#### 본 사이클 의의` 섹션 (brief placeholder) 추가 — §M1.5·§camera_empty 구조와의 일관성 목적. `save_freq=2000` 변경으로 ckpt 선정 기준도 달라졌으므로 메모 가치 있음. |

두 항목 모두 Recommended 수준 (Critical 아님). 003 entry 자체는 DOD 핵심 항목 (a)(b)(c) 모두 충족. READY_TO_SHIP 기준 충족 (Critical 0건 + Recommended 2건 이하).

---

## 배포 권장

**yes — 즉시 prod-test-runner 진입 권장**.

## prod-test-runner 검증 가능 영역

| 항목 | 방법 | 환경 레벨 |
|---|---|---|
| HF Hub repo 파일 구조 재확인 | `curl https://huggingface.co/api/models/BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6` | AUTO_LOCAL |
| `config.json.empty_cameras=1` 최종 확인 | `curl -L .../resolve/main/config.json` | AUTO_LOCAL |
| `learning_log.md` line 수 + entry 위치 정합 | `wc -l` + `grep -n "### 003"` | AUTO_LOCAL |
| train_config.json HF Hub 값 (steps, batch_size, scheduler_decay_steps) | `curl -L .../resolve/main/train_config.json` | AUTO_LOCAL |
| adapter_config.json LoRA r=16 확인 | `curl -L .../resolve/main/adapter_config.json` | AUTO_LOCAL |
