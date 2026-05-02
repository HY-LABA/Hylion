# TODO-M1 — Code Test

> 작성: 2026-05-01 | code-tester | cycle: 1

## Verdict

**`MAJOR_REVISIONS`**

Critical 2건 발견:
1. BACKLOG.md [04_infra_setup] 섹션에 자동 미러링 검증 항목 미추가 (DOD §4 검증 항목 요건 미충족)
2. §5 lerobot-record dry-run 예시 명령어가 레퍼런스 실제 CLI 와 불일치 (추측 작성 — lerobot-reference-usage 위반)

---

## 단위 테스트 결과

```
N/A — study 타입 (코드 없음). pytest 불필요.
```

## Lint·Type 결과

```
N/A — .py 파일 없음. ruff / mypy 대상 없음.
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| §1 시연장 환경 측정 항목 (책상·조명·카메라·토르소·작업영역 카테고리) | ✅ | 1-1~1-6 표 형식, 단위·기준·도구 모두 명시 |
| §2 측정 도구 (줄자·조도계·색온도계·사진 — 사용자 책임) | ✅ | §2 표 + "사용자 책임" 명시 |
| §3 DataCollector 측 재현 절차 (체크리스트 형태) | ✅ | 3-1~3-7 체크리스트 7개 단위 |
| §4 미러링 검증 방법 (육안+사진 비교 핵심, 자동 검증 BACKLOG 명시) | ⚠️ | §4 본문 내 BACKLOG 메모 존재하나 BACKLOG.md [04_infra_setup] 에 항목 미추가 — Critical #1 |
| §5 05_leftarmVLA 진입 전 점검 항목 list | ✅ | 환경미러링·하드웨어·소프트웨어 3개 게이트 체크리스트 |

---

## Critical 이슈

### Critical #1 — BACKLOG.md 미갱신

- 위치: `docs/work_flow/specs/BACKLOG.md` § [04_infra_setup]
- 사유: task-executor 보고에서 "자동 검증 스크립트를 BACKLOG 04 으로 명시"했다고 기재했고, `11_demo_site_mirroring.md` §4-3 에 내부 메모 형식으로 존재한다. 그러나 실제 `BACKLOG.md` [04_infra_setup] 섹션은 항목 #1~#5 로 마무리되며 자동 미러링 검증 항목이 추가되지 않았다. BACKLOG.md 는 워크플로우의 중앙 잔여 추적 문서이므로, 문서 내 메모만으로는 요건을 충족하지 못한다.
- 수정 요청: `BACKLOG.md` [04_infra_setup] 섹션에 항목 #6 신규 추가. 형식 예시:

  ```
  | 6 | 자동 미러링 검증 스크립트 — 시연장·DataCollector 카메라 영상 자동 비교 (히스토그램·SSIM·KL-divergence 등). 트리거: 05_leftarmVLA 추론 성능 부족 → 환경 미러링 원인 진단 시. | TODO-M1 §4 | 낮음 | 미완 |
  ```

### Critical #2 — §5 lerobot-record dry-run 명령어 CLI 불일치 (추측 작성)

- 위치: `docs/storage/11_demo_site_mirroring.md:263-274` (§5 소프트웨어 게이트)
- 사유: 제시된 dry-run 명령어가 `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` 의 실제 CLI 와 불일치한다. 구체적으로:
  - `--robot-path` — 레퍼런스에 없음 (실제: `--robot.type`, `--robot.port` 등 draccus dataclass 방식)
  - `--cameras top,wrist` — 레퍼런스에 없음 (실제: `--robot.cameras="{...}"` JSON 형식)
  - `--num-frames` — 레퍼런스에 없음 (`DatasetRecordConfig` 에 `num_frames` 필드 없음)
  - `--dry-run` — 레퍼런스에 없음 (`RecordConfig` 에 `dry_run` 필드 없음)
  - task-executor 는 `lerobot_record.py` 를 참조했다고 명시했으나, 실제 레퍼런스 인터페이스를 반영하지 않은 추측 작성에 해당한다. `lerobot-reference-usage` 위반 → Critical.
- 수정 요청: 두 가지 방향 중 하나 선택.
  - (a) 레퍼런스 실제 CLI 를 기반으로 올바른 예시 명령어로 교체 (단 `--dry-run` 플래그가 없으므로 dry-run 개념 자체를 재검토해야 함)
  - (b) 구체적 명령어 예시를 제거하고 "DataCollector 환경 셋업 완료 후 `lerobot-record` 로 테스트 에피소드 1회 수집 가능 여부 확인" 수준의 기술로 대체 (TODO-D3 진입 후 확정 가능)

---

## Recommended 개선 사항

| # | 위치 | 권장 |
|---|---|---|
| R1 | `11_demo_site_mirroring.md §0` | "형제 문서" 로 `09_dgx_structure.md` 도 추가 가능 (현재 `09_datacollector_setup.md` 만 명시). 단 study 성격 다르므로 선택적 |
| R2 | `11_demo_site_mirroring.md §3-6` | BACKLOG 03 #15 링크가 포트 확인 항목에 연결되어 있으나, #15 는 카메라 인덱스 관련 백로그. 포트 변동은 BACKLOG 01 #1 이 정확한 참조. §3-6 에 `BACKLOG 01 #1` 을 추가 언급하는 것이 더 정확함 |

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/` 미변경 확인. `.claude/` 미변경 확인 |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `pyproject.toml`, `setup_env.sh`, `deploy_*.sh` 미변경 확인 |
| Coupled File Rules | ✅ | pyproject.toml 미변경 → `02_orin_pyproject_diff.md` 갱신 불필요. `orin/lerobot/` 미변경 → `03_orin_lerobot_diff.md` 갱신 불필요 |
| C (사용자 동의 필수) | ✅ | 신규 디렉터리 없음. `docs/` 하위 파일 신규 → Category C 해당 없음 |
| D (절대 금지 명령) | ✅ | 해당 없음 |
| 옛 룰 (docs/storage/ bash 예시) | ⚠️ | `11_demo_site_mirroring.md §5` 에 bash 명령 예시가 포함되어 있음. 단 이는 사용자 수행 지침으로서 필요한 예시이며 "bash 명령 예시 추가 X" 룰 (docs/storage/ 에 불필요한 bash 예시 삽입 금지 취지) 의 위반 의도와 다르다고 판단 — CONSTRAINT_AMBIGUITY 등록 참조 |

### ANOMALIES

| TYPE | 내용 |
|---|---|
| `CONSTRAINT_AMBIGUITY` | CLAUDE.md 옛 룰 "docs/storage/ 하위에는 사용자 명시 요청 없으면 bash 명령 예시 추가 X" 의 적용 범위 모호. §5 의 dry-run 명령어는 사용자 수행 안내 목적이나, 본 룰이 이 케이스에 적용되는지 불명확. Critical #2 (CLI 불일치) 로 이미 수정 대상이므로 실질 영향은 없음. |

---

## 배포 권장

- **MAJOR: no** — task-executor 재호출 필요.
- Category B 영역 변경 없음 → 자동 재시도 가능 (2 cycle 제한 내).
- 수정 우선순위: Critical #1 (BACKLOG.md 갱신) + Critical #2 (§5 dry-run 명령어 교체 또는 제거) 처리 후 재검증.
- cycle 2 재검증 시 본 02_code-test.md 를 overwrite.

---

## cycle 2 재검증 (2026-05-01)

### Critical #1 해소: BACKLOG #6 — 검증 결과

`BACKLOG.md` [04_infra_setup] 섹션을 직접 Read 하여 90줄 확인:

```
| 6 | 시연장 미러링 자동 검증 스크립트 — DataCollector 측 사진·조도·색온도 자동 측정·비교
    (사용자 답 E: 본 사이클은 육안+사진 결정. 05/06 학습 결과로 미러링 부족 진단 시 트리거)
    | TODO-M1 | 낮음 (05·06 트리거 시 중간) | 미완 |
```

- 행 존재: ✅ 확인 (BACKLOG.md 90번째 줄)
- 발견 출처: `TODO-M1` ✅
- 우선순위: `낮음 (05·06 트리거 시 중간)` ✅
- 상태: `미완` ✅
- 형식: 기존 04 섹션 표 형식 준수 ✅

git diff 에서도 `+| 6 | 시연장 미러링 자동 검증 스크립트 ...` 신규 행이 확인됨. **Critical #1 해소 확인**.

### Critical #2 해소: §5 draccus 안내 — 검증 결과

`11_demo_site_mirroring.md` §5 소프트웨어 게이트 (261~272줄) 직접 확인:

**추측 플래그 제거 확인:**
- `--robot-path`: 제거 ✅
- `--cameras top,wrist`: 제거 ✅
- `--num-frames`: 제거 ✅
- `--dry-run`: 제거 ✅
- 추측 bash 블록 전체 없음 ✅

**draccus 구조 일치 확인 (레퍼런스 직접 대조):**

`docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py` 를 직접 Read 하여 확인:
- `RecordConfig` 는 `robot: RobotConfig`, `dataset: DatasetRecordConfig` 를 draccus dataclass 방식으로 받음
- 실제 CLI 예시 (파일 상단 docstring):
  ```
  lerobot-record \
      --robot.type=so100_follower \
      --robot.port=/dev/tty.usbmodem58760431541 \
      --robot.cameras="{laptop: {type: opencv, index_or_path: 0, ...}}" \
      --robot.id=black \
      --dataset.repo_id=<my_username>/<my_dataset_name> \
      ...
  ```
- `DatasetRecordConfig` 에 `repo_id`, `single_task`, `num_episodes` 등 있음 (`num_frames` 없음 — cycle 1 Critical 지적 정확)
- `RecordConfig` 에 `dry_run` 필드 없음 — cycle 1 지적 정확

**cycle 2 산출물의 §5 draccus 안내 메모 (270줄):**
> "구체 `lerobot-record` 호출은 draccus dataclass 인자 (`--robot.type`, `--robot.cameras`, `--dataset.repo_id` 등) 방식이라 환경별 조합 필요. 레퍼런스: `docs/reference/lerobot/src/lerobot/scripts/lerobot_record.py`. 실 호출 명령은 TODO-D3 prod 검증 시 사용자가 환경 맞춰 결정."

레퍼런스 실제 인자 구조와 비교:
- `--robot.type` ✅ (실제 사용: `--robot.type=so100_follower`)
- `--robot.cameras` ✅ (실제 사용: `--robot.cameras="{...}"`)
- `--dataset.repo_id` ✅ (실제 사용: `--dataset.repo_id=<my_username>/...`)
- 추상 기술 수준 유지 (구체 값 없음) + 레퍼런스 경로 명시 ✅
- TODO-D3 결정 위임 메모 존재 ✅

**4개 체크박스 형식 확인 (§5 소프트웨어 게이트 263~269줄):**
- `- [ ] DataCollector 측 venv 활성화 + lerobot import OK` ✅
- `- [ ] lerobot-record --help 정상 출력 (entrypoint 등록 확인)` ✅
- `- [ ] 1회 테스트 에피소드 수집 가능 여부 확인 (실 명령어는 SO-ARM·카메라 연결 시 TODO-D3 결정)` ✅
- `- [ ] 수집된 dataset 의 카메라 frame shape·dtype 확인` ✅

**Critical #2 해소 확인.**

lerobot-reference-usage 위반 답습 여부: 안내 메모가 레퍼런스의 실제 인자 이름을 정확히 반영하고 구체 값을 추측하지 않음. ✅

### §1~§4 회귀 X 확인

`11_demo_site_mirroring.md` 전체를 직접 Read (302줄):
- §1 측정 항목 표 (1-1~1-6): 변경 없음 ✅
- §2 측정 도구: 변경 없음 ✅
- §3 DataCollector 재현 체크리스트 (3-1~3-7): 변경 없음 ✅
  - §3-6 BACKLOG 03 #15 연계: 그대로 ✅
  - §3-7 BACKLOG 03 #15 연계: 그대로 ✅
- §4 미러링 검증 방법 (육안+사진 + 자동 검증 BACKLOG 내부 메모): 변경 없음 ✅
- §7 변경 이력: cycle 2 수정 행 추가 ✅
  - "2026-05-01 (cycle 2) | §5 소프트웨어 게이트 lerobot-record dry-run 추측 CLI 교체 ..." ✅

DOD §1~§5 모두 충족 유지:
- §4 는 cycle 1 에서 ⚠️ (BACKLOG.md 미추가) 였으나 cycle 2 에서 BACKLOG #6 추가로 ✅ 전환

### lerobot-reference-usage 답습 X 검증

레퍼런스 `lerobot_record.py` 직접 Read 결과:
- `RecordConfig` 구조: `robot: RobotConfig`, `dataset: DatasetRecordConfig`, `teleop`, `policy`, `display_data` 등
- `DatasetRecordConfig` 주요 필드: `repo_id`, `single_task`, `fps`, `num_episodes`, `push_to_hub` 등 (`num_frames` 없음)
- CLI는 draccus 방식: `--robot.type=`, `--robot.cameras=`, `--dataset.repo_id=`, `--dataset.num_episodes=` 형태

cycle 2 §5 안내 메모가 언급한 `--robot.type`, `--robot.cameras`, `--dataset.repo_id` 는 레퍼런스 docstring (5~30줄) 의 실제 예시 명령어와 정확히 일치. 추측 없음. ✅

---

## Verdict (cycle 2): READY_TO_SHIP

**근거:**
- Critical #1 (BACKLOG.md #6 미추가): BACKLOG.md 90줄에 정확한 형식으로 신규 행 추가 확인 — 해소
- Critical #2 (§5 추측 CLI): 추측 플래그 4종 모두 제거, draccus 안내 메모가 레퍼런스 실제 인자와 일치, TODO-D3 결정 위임 명시 — 해소
- §1~§4 미변경 (회귀 없음) 확인
- lerobot-reference-usage 위반 답습 없음 확인
- Category A·B·C·D Hard Constraints 위반 없음

Recommended 사항 2건 (R1, R2 — cycle 1 에서 이월) 은 미해소이나 Critical 0건, Recommended 2건 이하 → READY_TO_SHIP 조건 충족.

## 다음 단계

- READY_TO_SHIP → study 타입 (코드 없음) 이라 prod-test-runner 배포 무관.
- TODO-M1 완료 마킹. TODO-M2 (시연장 1차 미러링 셋업) 는 사용자 직접 수행 항목.
- verification_queue 에 TODO-M1 NEEDS_USER_VERIFICATION 추가 권장: "사용자가 11_demo_site_mirroring.md 가이드대로 시연장 측정 + DataCollector 인근 재현 + §4 육안 비교 완료."
