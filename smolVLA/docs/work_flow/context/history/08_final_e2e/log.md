# Orchestrator Log

> 오케스트레이터의 매 dispatch·완료·분기 이벤트 timeline. 한 줄 한 이벤트.

## 형식

```
YYYY-MM-DD HH:MM:SS | EVENT_TYPE | key=value, key=value, ...
```

이벤트 타입: `START` / `DISPATCH` / `VERDICT` / `WAIT_USER` / `GATE` / `WAVE_DONE` / `PHASE2_DONE` / `END_A` / `END_B` / `ANOMALY`

---

2026-05-04 19:55:00 | START | spec=08_final_e2e, todos=16, parallel_groups=5, awaits_user=0
2026-05-04 19:55:01 | DISPATCH | wave=1, todos=[S1,S2,R1,H1,N1], worker=task-executor x5 (parallel)
2026-05-04 20:03:30 | TASK_EXECUTOR_DONE | todo=S1, files=1, residual=none
2026-05-04 20:03:30 | TASK_EXECUTOR_DONE | todo=S2, files=1, residual=none
2026-05-04 20:03:30 | TASK_EXECUTOR_DONE | todo=R1, files=2 (incl 16_so100_vs_so101.md new), decision=SO101_adopt, residual=calibration_json_path_dep
2026-05-04 20:03:30 | TASK_EXECUTOR_DONE | todo=H1, files=1, residual=none
2026-05-04 20:03:30 | TASK_EXECUTOR_DONE | todo=N1, files=14 (12 mod + 2 new _back.py), residual=teleop_returncode_2+ckpt_back_success_false
2026-05-04 20:03:31 | DISPATCH | wave=1, todos=[S1,S2,R1,H1,N1], worker=code-tester x5 (parallel)
2026-05-04 20:08:00 | VERDICT | todo=S1, code-tester=READY_TO_SHIP
2026-05-04 20:08:00 | VERDICT | todo=S2, code-tester=READY_TO_SHIP
2026-05-04 20:08:00 | VERDICT | todo=R1, code-tester=READY_TO_SHIP (recommended=1: 파일수 오기, R2 영향 X)
2026-05-04 20:08:00 | VERDICT | todo=H1, code-tester=READY_TO_SHIP (recommended=1: §7 수량 1대 갱신, 비차단)
2026-05-04 20:08:00 | VERDICT | todo=N1, code-tester=MINOR_REVISIONS (recommended=3: teleop_returncode_2_ambiguity + ckpt_back_show_mgmt + ruff_E402_pre_existing)
2026-05-04 20:08:01 | DISPATCH | wave=1, todos=[S1,S2,R1,H1], worker=prod-test-runner x4 (parallel) + todo=[N1], worker=task-executor (MINOR cycle 1)
2026-05-04 20:13:00 | VERDICT | todo=S1, prod-test=AUTOMATED_PASS
2026-05-04 20:13:00 | VERDICT | todo=S2, prod-test=AUTOMATED_PASS
2026-05-04 20:13:00 | VERDICT | todo=R1, prod-test=AUTOMATED_PASS
2026-05-04 20:13:00 | VERDICT | todo=H1, prod-test=AUTOMATED_PASS
2026-05-04 20:13:00 | TODO_DONE | todos=[S1,S2,R1,H1], spec_marked=[x]
2026-05-04 20:13:00 | TASK_EXECUTOR_DONE | todo=N1 (MINOR cycle 1), changes=teleop_sentinel_-1+training_CANCELED
2026-05-04 20:13:01 | DISPATCH | todos=[N1], worker=prod-test-runner | todos=[R2,H2], worker=task-executor (parallel — R1+H1 PASS, deps satisfied)
2026-05-04 20:18:30 | VERDICT | todo=N1, prod-test=AUTOMATED_PASS
2026-05-04 20:18:30 | TODO_DONE | todo=N1, spec_marked=[x]
2026-05-04 20:18:30 | TASK_EXECUTOR_DONE | todo=R2, files=13 (active=6 + cat_B=5 docstring + docs=2), residual=calibration_json_robot_type_dep
2026-05-04 20:18:30 | TASK_EXECUTOR_DONE | todo=H2, files=2 (code=0 — both cams MJPG 640x480 OK), backlog_added=2 (wrist_distribution+wrist_flip), anomaly=dgx_orin_camera_key_mismatch
2026-05-04 20:18:31 | DISPATCH | todos=[R2,H2], worker=code-tester (parallel) | todos=[N2], worker=prod-test-runner (SSH_AUTO regression)
2026-05-04 20:22:00 | VERDICT | todo=N2, prod-test=AUTOMATED_PASS (orin+dgx deploy OK, _back assert PASS, entry import OK, headless walkthrough b→종료 양쪽 확인)
2026-05-04 20:22:00 | TODO_DONE | todo=N2, spec_marked=[x]
2026-05-04 20:22:00 | VERDICT | todo=R2, code-tester=READY_TO_SHIP (recommended=2: hil_inference follower_so100 default + smoke_test ruff F841/F401 pre-existing)
2026-05-04 20:22:00 | VERDICT | todo=H2, code-tester=READY_TO_SHIP (recommended=1: dgx_camera_key_mismatch BACKLOG 미등록)
2026-05-04 20:22:01 | DISPATCH | todos=[R2,H2], worker=prod-test-runner x2 (parallel)
2026-05-04 20:22:01 | NOTE | orchestrator-direct: BACKLOG.md 08_final_e2e #3 (camera_key_mismatch) 추가 (H2 Recommended 흡수)
2026-05-04 20:22:01 | NOTE | worker-anomaly: N2 prod-test-runner 가 spec_mark + log_append 직접 수행 (정책상 orchestrator 책임) — reflection 추적 항목
2026-05-04 20:28:00 | VERDICT | todo=R2, prod-test=AUTOMATED_PASS (SO100잔재=0, svla_so100_pickplace=19보존, orin SO101 import OK, dgx record.py ROBOT_TYPE so101_follower OK)
2026-05-04 20:28:00 | VERDICT | todo=H2, prod-test=AUTOMATED_PASS (코드 변경 0 정당, BACKLOG 2건 등록 확인, H1 Recommended 흡수 PASS)
2026-05-04 20:28:00 | TODO_DONE | todos=[R2,H2], spec_marked=[x]
2026-05-04 20:28:00 | NOTE | orchestrator-direct: BACKLOG #3 (camera_key_mismatch), #4 (hil_inference follower-id default), #5 (smoke_test ruff) 등록 완료
2026-05-04 20:28:01 | DISPATCH | todos=[R3], worker=prod-test-runner (SSH_AUTO regression — task-executor skip, spec type=test)
2026-05-04 20:35:00 | VERDICT | todo=R3, prod-test=AUTOMATED_PASS (orin+dgx SSH OK, deploy OK, import 6 모듈 OK, SO100 잔재 0)
2026-05-04 20:35:00 | TODO_DONE | todo=R3, spec_marked=[x]
2026-05-04 20:35:00 | NOTE | orchestrator-direct: BACKLOG #6 (calibration_json_robot_type) 등록 (R2 잔여 리스크 흡수)
2026-05-04 20:35:00 | WAVE_DONE | wave=1, todos_completed=[S1,S2,R1,R2,R3,H1,H2,N1,N2] (9/9)
2026-05-04 20:35:01 | GATE | gate=1, status=READY_FOR_USER_VERIFICATION, next=DGX 시연장 이동 후 Wave 2 진입
2026-05-04 20:42:00 | AD_HOC | walkthrough=gate_1, type=file_relocation, change=docs/storage/16_so100_vs_so101.md → docs/lerobot_study/08_so100_vs_so101.md, reason=lerobot_study 컨벤션 정합, scope=spec R1 cross-ref 갱신 + context history 보존
2026-05-04 20:42:01 | GATE | gate=1, status=PASSED (사용자 승인 — 정합 통과 + 시연장 이동 진행)
2026-05-04 20:42:02 | DISPATCH | wave=2, todo=C1, env=PHYS_REQUIRED, owner=user_operation (DGX 시연장 운반·셋업), prod-test-runner=stand-by SSH 가용 시 검증
2026-05-04 21:21:00 | C1_PROGRESS | overview cheese capture 분석 — Seeed 매트 + SO-101 follower + 분홍 lego (pick) + 갈색 박스 (place) + leader (frame 우측) + USB hub 고정. PCB 보드 작업영역 침범 — 정리 권장
2026-05-04 21:32:00 | C1_PROGRESS | wrist cheese capture 분석 — lego 큐브 정합 ✅, 90° 회전 의심 (Seeed 로고 세로). 사용자 결정 A (그대로 진행) → BACKLOG #8 사후 재검토 등록
2026-05-04 21:35:00 | C1_PROGRESS | 미러링 §7 갱신 — §7-1 USB 토폴로지 (USB 3.0 포트 + 디바이스 USB 2.0 only → USB 2.0 path enum), §7-2 작업영역 42×30 cm Seeed 매트, §7-4 형광등, §7-5 overview 카메라 스탠드 고정, §7-6 wrist (rotate 결정 A), §7-7 SO-101 follower 책상 mount + leader 우측 고정 + USB hub
2026-05-04 21:38:00 | NOTE | orchestrator-direct: BACKLOG #6 (calibration JSON robot_type) 기각 — upstream lerobot/robots/robot.py:49-50 의 self.calibration_dir 가 클래스 self.name="so_follower" 사용 (robot_type 문자열 무관). SO100/101 alias 통합 확인.
2026-05-04 21:40:00 | NOTE | orchestrator-direct: 카메라 모델 정정 — overview = OV5648 sensor + YJX-C5 USB 모듈 동일 카메라. 02_hardware §7 USB descriptor 한 단락 추가.
2026-05-04 21:55:00 | AD_HOC | walkthrough=C1, type=interactive_cli_fix, finding=record.py episode_time_s/reset_time_s 60s 누락 + training.py rename_map 본 사이클 카메라 키 불일치 (BACKLOG #3 본 사이클 처리) + steps default 10000 (spec T1 결정 C 2000과 불일치). 사용자 결정: A(b)=12s+5s, B(a)=overview→camera1/wrist_left→camera2, C=메뉴 4 옵션 default 2000. 시각화 점검: tqdm 기본+wandb 옵션 (DGX 0.24.2 설치, login 필요)
2026-05-04 21:55:01 | DISPATCH | todo=C0 (ad-hoc), worker=task-executor (4 파일: data_kind.py + record.py + training.py + mode.py)
2026-05-04 21:59:30 | TASK_EXECUTOR_DONE | todo=C0, files=4, residual=svla_so100_pickplace smoke 데이터셋 학습 시 rename_map top/wrist 불일치 (BACKLOG #3 그대로 09 처리)
2026-05-04 21:59:31 | DISPATCH | todo=C0, worker=code-tester (AUTO_LOCAL grep + py_compile + ruff)
2026-05-04 22:01:00 | VERDICT | todo=C0, code-tester=READY_TO_SHIP (DOD 14/14 PASS, recommended=0)
2026-05-04 22:01:01 | DISPATCH | todo=C0, worker=prod-test-runner (SSH_AUTO — dgx deploy + import 회귀)
2026-05-04 22:04:00 | VERDICT | todo=C0, prod-test=AUTOMATED_PASS (py_compile + dgx deploy + 4모듈 import + build_record_args CLI 인자 정합 + DataKindResult 5 옵션 정합 모두 PASS)
2026-05-04 22:04:00 | TODO_DONE | todo=C0 (ad-hoc), interactive-cli 학습 설정 정정 완료 — record episode_time_s=data_kind.default(12s) + reset_time_s=5s, training rename_map 본 사이클 카메라 키 정합, steps 메뉴 4 옵션 default 2000
2026-05-04 22:04:01 | NOTE | cheese 종료 + 카메라 free 확인 — interactive-cli main.sh 진입 준비 완료
2026-05-04 22:30:00 | C1_PROGRESS | 사용자 보고 — calibrate 재실행 시 lerobot-calibrate 의 default prompt 가 "기존 사용" (so_follower.py:111-115) 라 Enter 누르다 그냥 기존 calibration 로드 문제 + 모터·카메라 포트 매번 재발견 부담 + 카메라 매핑 검증 부재
2026-05-04 22:30:01 | AD_HOC | walkthrough=C1, type=precheck_usability_fix, decision=라이브 카메라 검증 (ssh-x11 ffplay 포함) + calibration.json default 저장 + 옵션 (2) 분기 재구성
2026-05-04 22:30:02 | DISPATCH | todo=C0b (ad-hoc), worker=task-executor (precheck.py 단일 파일 ~120줄)
2026-05-04 22:35:00 | TASK_EXECUTOR_DONE | todo=C0b, files=1, residual=ffplay v4l2 점유 시 빈 화면 가능성 + cv2 캡처 warm-up 부재
2026-05-04 22:35:01 | DISPATCH | todo=C0b, worker=code-tester (AUTO_LOCAL grep + py_compile + ruff)
2026-05-04 22:37:00 | VERDICT | todo=C0b, code-tester=READY_TO_SHIP (DOD 6/6 PASS, recommended=0)
2026-05-04 22:37:01 | DISPATCH | todo=C0b, worker=prod-test-runner (SSH_AUTO — dgx deploy + import + ffplay 가용 + display_mode 분기)
2026-05-04 22:40:00 | VERDICT | todo=C0b, prod-test=AUTOMATED_PASS (py_compile + dgx deploy + 5심볼 import + ffplay 6.1.1 가용 + /dev/video0~3 + detect_display_mode 정합)
2026-05-04 22:40:01 | TODO_DONE | todo=C0b (ad-hoc), precheck 사용성 정정 완료 — 라이브 카메라 검증 + calibration.json default + 옵션 (2) 흐름 재구성
2026-05-04 22:55:00 | C1_PROGRESS | 사용자 보고 — 옵션 (1) 의 USB 분리/재연결 강제 + 'c'+Enter 안내 불명확. 메뉴 구조 재설계 결정.
2026-05-04 22:55:01 | AD_HOC | walkthrough=C1, type=precheck_menu_redesign, decision=메뉴 (1)/(2)/(3) 폐기 → 3단계 sequential [a/b] 분기 (모터포트/카메라/calibrate). force_new_id=True 시 timestamp 새 ID 자동 → lerobot prompt 회피.
2026-05-04 22:55:02 | DISPATCH | todo=C0c (ad-hoc), worker=task-executor (precheck.py +86줄, 신규 함수 3 + force_new_id 인자)
2026-05-04 23:00:00 | TASK_EXECUTOR_DONE | todo=C0c, files=1, residual=cameras null + streamable<2 시 cancel (D13 정책 동일)
2026-05-04 23:00:01 | DISPATCH | todo=C0c, worker=code-tester+prod-test (통합)
2026-05-04 23:03:00 | VERDICT | todo=C0c, code-tester=READY_TO_SHIP + prod-test=AUTOMATED_PASS (DOD 전항 + dgx deploy + force_new_id import 검증 모두 PASS)
2026-05-04 23:03:01 | TODO_DONE | todo=C0c (ad-hoc), precheck 메뉴 단계별 분기 완료
2026-05-04 23:30:00 | C1_PROGRESS | 사용자 보고 — calibrate 새로 했는데 teleop/record 가 옛 ID JSON 사용 + wrist_roll 안 됨 의문
2026-05-04 23:30:01 | NOTE | 원인 분석: (1) record.py/run_teleoperate.sh hardcoded FOLLOWER_ID — 버그. (2) wrist_roll = lerobot upstream full_turn_motor 자동 처리 (so_follower.py:131-132) — 정상.
2026-05-04 23:30:02 | DISPATCH | todo=C0d (ad-hoc), worker=task-executor (5 파일 — record + teleop + run_teleoperate.sh + mode + precheck)
2026-05-04 23:35:00 | TASK_EXECUTOR_DONE | todo=C0d, files=5, residual=flow6_record + mode.py 의 calibration.json 이중 로드 (실 운영 영향 X)
2026-05-04 23:35:01 | DISPATCH | todo=C0d, worker=code-tester+prod-test (통합)
2026-05-04 23:38:00 | VERDICT | todo=C0d, code-tester=READY_TO_SHIP + prod-test=AUTOMATED_PASS (DOD 7/7, dgx deploy + import + 시그니처 + calibration 통합 테스트 ALL PASS)
2026-05-04 23:38:01 | TODO_DONE | todo=C0d (ad-hoc), calibration ID 자동 로드 + wrist_roll 안내 완료
2026-05-05 00:10:00 | C1_PROGRESS | 사용자 보고 — calibrate 실행 후에도 teleop 에 새 ID 전달 안 됨. 진단 결과: calibration.json 에 새 ID 저장됐으나 실 lerobot JSON 파일 미생성 (~/.cache/.../so_follower/<new_id>.json 없음, 옛 my_so101.json 만). _run_calibrate 가 JSON 실존 확인 X 라 비정상 종료에도 calibration.json 갱신.
2026-05-05 00:10:01 | NOTE | b/back 멈춤 — 단계별 stack 관리 필요, BACKLOG #9 등록 (사용자 동의)
2026-05-05 00:10:02 | DISPATCH | todo=C0e (ad-hoc), worker=task-executor (precheck.py _run_calibrate JSON 실존 검증 추가)
2026-05-05 00:13:00 | TASK_EXECUTOR_DONE | todo=C0e, files=1, residual=for loop 중간 'n' 시 follower JSON 잔재 (BACKLOG 범위)
2026-05-05 00:13:01 | DISPATCH | todo=C0e, worker=code-tester+prod-test (통합)
2026-05-05 00:15:00 | VERDICT | todo=C0e, code-tester=READY_TO_SHIP + prod-test=AUTOMATED_PASS (DOD 7/7, dgx deploy + import + 시그니처 확인 모두 PASS)
2026-05-05 00:15:01 | TODO_DONE | todo=C0e (ad-hoc), calibration JSON 실존 검증 완료
2026-05-05 00:30:00 | SESSION_PAUSE | C1 walkthrough 진행 중 세션 정리 (사용자 요청). 다음 세션 진입 가이드: spec 본문 §"진행 노트" 섹션 참조. dgx tmp/cheese·ffplay 프로세스 정리 + /tmp 임시 파일 삭제 완료. 미완 todo: C1·C2·T1·T2·I1·I2·W1·W2 (Wave 2~5).
2026-05-05 03:19:51 | RESUME | spec=08_final_e2e Wave 1.5 진입 — 사용자 결정 J 적용 (interactive-cli audit). 그룹 U 신규 (Wave 2 차단). U2~Un placeholder (Phase 1 재진입 후 정의).
2026-05-05 03:19:52 | START | spec=08_final_e2e, todos=9 활성 (U1·C1잔여·C2·T1·T2·I1·I2·W1·W2), parallel_groups=1 (U1 단독 dispatch — 나머지 8 직렬 의존)
2026-05-05 03:19:53 | DISPATCH | todo=U1, worker=task-executor (audit 보고서 작성 — dgx flows 10 + orin flows 4 + main.sh 2 + README 2 + configs/, 분류 6 컬럼)
2026-05-05 03:27:30 | TASK_EXECUTOR_DONE | todo=U1, files=2 신규 (interactive_cli_audit.md + 01_implementation.md), 발견=33건 (Critical 3 / Major 16 / Minor 10 / Nit 4), 카테고리: UX·UI·정합성. 핵심: #1 precheck b/back stack 부재 (BACKLOG #9), #21 record.py 카메라 키 wrist_left/overview vs Orin wrist/overview (BACKLOG #3), #2 orin entry detect_display_mode 부재, #25 calibration JSON 경로 robot_type 반영 미상.
2026-05-05 03:27:31 | DISPATCH | todo=U1, worker=code-tester (보고서 형식·커버리지·인용 정확성 검증)
2026-05-05 03:31:30 | VERDICT | todo=U1, code-tester=MINOR_REVISIONS (4축 PASS — 샘플 인용 4/5=80%, 6컬럼·§1~§5·DOD 모두 정합), Recommended 3건: (1) #17 inference.py:157-158 → :201 오인용, (2) §3 분포표 33↔34 수치 불일치, (3) #21·#2 Critical 재고 (rename_map 으로 차단 X → Major 권장)
2026-05-05 03:31:31 | DISPATCH | todo=U1, worker=task-executor (MINOR cycle 1 — Recommended 3건 적용, 재검증 X)
2026-05-05 03:33:30 | TASK_EXECUTOR_DONE | todo=U1 cycle 1, files=2 (interactive_cli_audit.md + 01_implementation.md MINOR 섹션). Critical 3 → 1 (#1 precheck b/back stack 만 유지), Major 16 → 17 (#2·#21 하향), §3 분포 합계 34 정정, #17 라인 :201 정정.
2026-05-05 03:33:31 | DISPATCH | todo=U1, worker=prod-test-runner (AUTO_LOCAL — 보고서 파일 정합·형식 정적 검증)
2026-05-05 03:36:30 | VERDICT | todo=U1, prod-test=AUTOMATED_PASS (a 파일 실존 + b §1~§5 형식 + c §3 합계 34 일관 + d Critical 1건 + e 코드 변경 X — 모두 PASS). 비차단 관찰: 01_implementation.md L7/L24 "33건" 잔존 (audit.md 본체는 34 정확).
2026-05-05 03:36:31 | TODO_DONE | todo=U1 (audit 보고서 작성 완료, 발견 34건 — Critical 1 / Major 17 / Minor 12 / Nit 4)
2026-05-05 03:36:32 | PHASE1_REENTRY_PROMPT | spec 08 그룹 U — 메인이 사용자에게 §2 표 + §3 분포 + §4 prompt 제시 → 사용자 우선순위 결정 (즉시 / BACKLOG 이관 / 기각) → U2~Un 묶음 분해 → /start-spec 재호출
2026-05-05 04:07:41 | USER_DECISION_K | 큰 구조 리팩토링 우선 (audit 발견 정정 전). dgx 먼저 완전 정리 → orin 동일 흐름 답습. U2 dgx 주석 → legacy/03, U3 14_dgx_cli_flow 정리, U4 dgx utils 선제 추출 + audit #6·#9·#10·#17·#18·#25 흡수, U5 잔여 정정 (Phase 1 재진입). Category C 동의 (utils 디렉터리). BACKLOG #1·#21 기존 결정 유지.
2026-05-05 04:07:42 | TASK_REGISTERED | task #10 (U2) #11 (U3) #12 (U4) #13 (U5). 의존성: U3 ← U2, U4 ← U3, U5 ← U4, C1잔여 (#2) ← U5.
2026-05-05 04:07:43 | DISPATCH | todo=U2, worker=task-executor (dgx 갱신 주석 → legacy/03 이관 + AI 검색 친화 형식)
2026-05-05 04:19:30 | TASK_EXECUTOR_DONE | todo=U2, files=신규 1 (legacy/03) + 수정 11 (.py 10 + README). §3 timeline 11건 (X2/D2/D4/D6/D7/D8/C0/C0b/C0c/C0d/C0e/N1/N2 등) + §4 파일별 인덱스 11 파일 + §5·§7 placeholder. py_compile 전 파일 PASS. 보수적 유지 2건 (precheck docstring D7·D8, README HTML 주석 datacollector 제거 history) — §4 메모.
2026-05-05 04:19:31 | DISPATCH | todo=U2, worker=code-tester (legacy/03 형식 + 주석 grep 0 + py_compile + 코드 동작 영향 0)
