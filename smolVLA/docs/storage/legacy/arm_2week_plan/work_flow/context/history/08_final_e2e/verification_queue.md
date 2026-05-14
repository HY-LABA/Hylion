# Phase 3 검증 대기 큐 — placeholder

> Phase 2 진행 중 prod-test-runner 가 완료한 항목 + 사용자 실물 검증이 필요한 항목을 누적. 모든 todo 자동화 종료 시 메인이 본 큐를 사용자에게 일괄 제시.

## 형식

각 항목:

```markdown
### [TODO-XX] (제목)

- **상태**: 자동 검증 통과 / 실패 / N.A.
- **사용자 검증 필요 사항**:
  1. (구체 절차)
  2. ...
- **prod-test-runner 결과 요약**: ...
- **참고 파일**: `context/todos/XX/03_prod-test.md`
```

---

### [TODO-R1] SO100 vs SO101 Study

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음
- **prod-test-runner 결과 요약**: docs/storage/16_so100_vs_so101.md 파일 존재 확인, §1~§8 섹션 구조 정합, SO101Follower 언급 16건, svla_so100_pickplace 보존 명시 6건, calibration 언급 11건, upstream L232/233 alias 실 확인 — 전 항목 통과.
- **참고 파일**: `context/todos/R1/03_prod-test.md`

---

### [TODO-H1] 02_hardware §7-1 U20CAM-720P 신규 추가 + §8 갱신

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (AUTO_LOCAL — docs/storage 문서 변경)
- **prod-test-runner 결과 요약**: grep 9종 전 항목 통과. U20CAM-720P ≥3건, INNO-MAKER ≥2건, FOV-D+120° 교차 확인, §7-1 신규 헤더 존재, §8 혼합 구성 갱신, OV5648 §7 보존 3건. DOD 12항목 전 자동 충족.
- **비차단 잔여**: §7 수량 "2대" → "1대" 갱신 (code-tester Recommended, DOD 외) — BACKLOG 이관 가능.
- **참고 파일**: `context/todos/H1/03_prod-test.md`

---

### [TODO-N1] interactive_cli 뒤로가기 b/back 일괄 적용

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (AUTO_LOCAL — interactive_cli Python flow 코드 변경)
- **prod-test-runner 결과 요약**: py_compile 14개 파일 전체 OK. teleop -1 sentinel (return -1 1건, == -1 2건, return 2 잔재 0건). training CANCELED sentinel 4건 (반환 + early return 분기). Category C 회피 (common/ 미생성). DOD 5항목 + MINOR #2/#3 전 자동 충족.
- **비차단 잔재**: orin/entry.py `# noqa: E402` 미적용 (BACKLOG 이관 예정), run_teleoperate.sh exit 2 미확인 (SKILL_GAP, -1 sentinel 로 위험 제거됨).
- **참고 파일**: `context/todos/N1/03_prod-test.md`

---

### [TODO-N2] 뒤로가기 회귀 검증

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (SSH_AUTO 검증 전 항목 통과)
- **prod-test-runner 결과 요약**: orin + dgx 양쪽 배포 성공. `_back.py` is_back() assert 전 항목 통과 (orin SSH python, dgx SSH python3). entry.py import OK. 헤드리스 stdin pipe walkthrough: orin + dgx 양쪽 `b` 입력 시 "종료합니다." 정상 종료. DOD 4항목 전 자동 충족. 비차단 관찰: orin main.sh LD_LIBRARY_PATH 경고 (기존 동작, N1 무관) + dgx 상대 경로 직접 호출 시 preflight 경로 해석 실패 (main.sh 경유 시 정상, DOD 범위 외).
- **참고 파일**: `context/todos/N2/03_prod-test.md`

---

### [TODO-R2] 활성 코드 SO100 → SO101 일괄 마이그레이션

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (AUTO_LOCAL + SSH_AUTO 전 항목 통과)
- **prod-test-runner 결과 요약**: SO100 잔재 0건 (svla_so100_pickplace 19건 보존), py_compile 활성 6파일 exit 0, orin 배포 + SO101Follower import OK, dgx 배포 + record.py ROBOT_TYPE = so101_follower 확인. Coupled File Rule (03_orin_lerobot_diff.md) 3건 grep 통과. DOD 10항목 전 자동 충족.
- **비차단 잔재**: hil_inference.py:271 `--follower-id` default `"follower_so100"` (spec DOD 외 — CLI 명시 지정으로 우회 가능, 다음 사이클 갱신 권장).
- **참고 파일**: `context/todos/R2/03_prod-test.md`

---

### [TODO-H2] overview vs wrist 카메라 영향 검토 + H1 Recommended 흡수

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (AUTO_LOCAL — 문서 변경만, 코드 변경 0)
- **prod-test-runner 결과 요약**: grep 8종 전 항목 통과. overview 1대 표기 1건, "Camera: 2대" 잔재 0건, §9 신규 섹션 존재, BACKLOG 08_final_e2e 섹션 1건, wrist 광각 3건, wrist flip 2건, MJPG 7건. record.py H2 미변경 확인 (235217a). DOD 8항목 전 자동 충족.
- **비차단 잔여**: DGX record.py 카메라 키 불일치 (`wrist_left`/`overview` vs `top`/`wrist`) BACKLOG #3 orchestrator 추가 예정.
- **참고 파일**: `context/todos/H2/03_prod-test.md`

---

### [TODO-R3] SO101 마이그레이션 회귀 검증

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (SSH_AUTO 검증 전 항목 통과)
- **prod-test-runner 결과 요약**: orin + dgx 양쪽 SSH 가용. orin 배포 성공 (1.9MB) + 4개 모듈 import OK (smoke_test import 시 SmolVLAPolicy 더미 추론까지 통과). dgx 배포 성공 (14MB) + flows.record / flows.training import OK. SO100 잔재 grep 0건. DOD 5항목 전 자동 충족.
- **비차단 관찰**: dgx `interactive_cli/` 에 `__init__.py` 없음 — `cd interactive_cli && python -c "from flows.record import ..."` 방식이 올바른 import 패턴 (R2 기준 일치).
- **참고 파일**: `context/todos/R3/03_prod-test.md`

---

### [TODO-C0] interactive-cli 학습 설정 정합성 정정

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (SSH_AUTO 전 항목 통과)
- **prod-test-runner 결과 요약**: dgx 배포 성공 (4파일 전송). DGX 4모듈 import OK. build_record_args CLI 인자 `--dataset.episode_time_s=12` + `--dataset.reset_time_s=5` 포함 확인. DATA_KIND_OPTIONS 5개 옵션 모두 두 필드 존재 (opt 1~5: 12/5, 8/5, 15/7, 10/5, 10/5). DataKindResult._fields 5개 정합. DOD 14항목 전 자동 충족.
- **참고 파일**: `context/todos/C0/03_prod-test.md`

---

### [TODO-C0b] precheck 사용성 정정

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (AUTO_LOCAL + SSH_AUTO 전 항목 통과)
- **prod-test-runner 결과 요약**: devPC py_compile exit 0. dgx 배포 성공 (rsync speedup 33.83). DGX 5 심볼 import OK (`teleop_precheck`, `_verify_camera_mapping_live`, `_run_calibrate`, `_CALIBRATION_FILENAME`, `_CALIBRATION_DEFAULT`). `_CALIBRATION_DEFAULT` 5필드 전부 확인. ffplay 가용 (`/usr/bin/ffplay` v6.1.1). `/dev/video0~3` 4장치 존재. mode + entry 통합 import OK, `detect_display_mode()` = `ssh-file` 정상. DOD 6항목 전 자동 충족.
- **참고 파일**: `context/todos/C0b/03_prod-test.md`

---

### [TODO-U1] interactive_cli audit 보고서 작성

- **상태**: AUTOMATED_PASS (사용자 실물 검증 불요)
- **사용자 검증 필요 사항**: 없음 (AUTO_LOCAL — 보고서 산출물 정적 검증)
- **prod-test-runner 결과 요약**: 산출물 3파일 실존 확인 (interactive_cli_audit.md 161줄, 01_implementation.md 80줄, 02_code-test.md 98줄). §1~§5 헤더 전 존재. §2 6컬럼 표 정합 (카테고리/severity/영향/현상/권장 정정/우선순위). §3 합계 34 = §2 데이터 행 34건 일치. Critical 1건 정확 (MINOR cycle 1 적용 후 3→1). git status 상 코드 변경 없음 확인 (modified 전부 U1 이전 기존 변경, untracked 신규는 보고서 파일만). DOD 5항목 전 자동 충족.
- **다음 단계 안내**: §4 사용자 우선순위 결정 prompt 제시 필요 — 메인이 사용자에게 audit.md §4 내용 전달 후 Phase 1 재진입 (U2~Un todo 분해).
- **참고 파일**: `context/todos/U1/03_prod-test.md`
