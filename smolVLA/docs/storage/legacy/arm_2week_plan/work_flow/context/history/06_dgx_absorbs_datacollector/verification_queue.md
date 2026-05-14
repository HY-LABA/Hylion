# Phase 3 검증 대기 큐

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

## 06_dgx_absorbs_datacollector

### [TODO-V1] DGX 시연장 이동 후 SO-ARM·카메라 직결 하드웨어 검증

- **상태**: 사용자 무시 결정 (2026-05-03, BACKLOG 이관) — DGX·Orin 시연장 환경 떨어짐. devPC 정적 통과 후 다음 사이클 처리. 04 BACKLOG #7 + 05 ANOMALIES #4 fallback 패턴
- **사용자 검증 필요 사항**:
  1. DGX 시연장 이동 + USB 직결 — SO-ARM follower(12V) + leader(7.4V) + 카메라 top + wrist. USB 포트 부족 시 hub 준비
  2. dialout 그룹 권한 확인 — `groups` 로 dialout 포함 여부. 미포함 시 `sudo usermod -aG dialout $USER` 후 재로그인
  3. v4l2 인식 확인 — `ls /dev/video*` 카메라 2대 인식. v4l-utils 미설치 시 `sudo apt install v4l-utils`
  4. lerobot-find-port 비대화형 — venv 활성화 후 `python3 -c "from pathlib import Path; print(sorted(Path('/dev').glob('ttyACM*'))[:2])"` 로 `/dev/ttyACM0`, `/dev/ttyACM1` 발견
  5. lerobot-find-cameras opencv — venv 활성화 후 `python3 -c "from lerobot.cameras.opencv import OpenCVCamera; print(OpenCVCamera.find_cameras())"` 카메라 2개 인덱스 발견
  6. check_hardware.sh 5-step 모두 PASS — `bash dgx/scripts/check_hardware.sh` 실행, `[DONE] 모든 점검 PASS (5단계)` + JSON `summary.fail == 0` 확인
- **prod-test-runner 결과 요약**: devPC 정적 검증 — bash -n exit 0, check_hardware.sh 5-step 구성 (venv·dialout·soarm_port·v4l2·cameras) 정합, orin 04 G1 패턴 미러 7항목 정합. DGX SSH 불가로 실물 6항목 모두 사용자 위임
- **참고 파일**: `context/todos/V1/03_prod-test.md`

### [TODO-V2] dgx/interactive_cli/ 수집 mode flow 0~7 완주 검증

- **상태**: 사용자 무시 결정 (2026-05-03, BACKLOG 이관) — DGX·Orin 시연장 환경 떨어짐. devPC 정적 통과 후 다음 사이클 처리
- **사용자 검증 필요 사항**:
  1. **DGX 배포**: devPC 에서 `bash scripts/deploy_dgx.sh` + `bash scripts/deploy_orin.sh` 실행 → DGX VSCode remote-ssh 터미널에서 `bash dgx/interactive_cli/main.sh`
  2. **flow 0**: 환경 확인 prompt `"DGX 맞나요? [Y/n]"` 표시 → Y 응답 → flow 1 진입 확인
  3. **flow 1**: 장치 선택 메뉴에서 `orin / dgx` 2 옵션만 표시 (datacollector 옵션 제거 확인) → `dgx` 선택
  4. **flow 2**: preflight + 수집 환경 체크 — `preflight_check.sh` PASS + `_check_hardware_collect()` 항목 6~9 (USB 포트·dialout·v4l2·SO-ARM 포트 응답) PASS 확인. 04 BACKLOG #14 실물 확인: 항목 9 serial.Serial context manager 실행 시 NoneType 에러 없이 PASS 또는 SKIP 메시지 출력 확인
  5. **flow 3**: mode 메뉴 `(1) 수집 / (2) 학습 / (3) 종료` 정확 표시 확인 → `(1)` 선택
  6. **flow 4 (수집 mode)**: `lerobot-calibrate follower` + `lerobot-calibrate leader` 실 수행. 04 BACKLOG #10 (id_=3 elbow_flex Torque_Enable 실패 간헐) 재발 시 1~2회 재실행. 포트: `/dev/ttyACM0` follower, `/dev/ttyACM1` leader 확인
  7. **flow 5**: 학습 종류 선택 5 옵션 표시 확인 → `옵션 1 단순 pick-place` 권장 선택
  8. **flow 6**: `lerobot-record` dummy episode 수집 (`--dataset.num_episodes=2` 권장). 카메라 인덱스 wrist_left=0/overview=1 실환경 정합 확인. SO-ARM follower leader 추종 동작 육안 관찰
  9. **flow 7 분기 (1) 로컬 저장만**: `(1)` 선택 → `"~/smolvla/dgx/data/<dataset_name>"` 저장 안내 메시지 + 학습 전환 prompt 표시 확인
  10. **flow 7 분기 (2) HF Hub 백업**: `(2)` 선택 → `push_dataset_hub.sh` 호출 + 업로드 완료 확인. 학교 WiFi huggingface.co 타임아웃 시 다른 네트워크 권고. private=y 선택 권장
  11. **G-4 학습 전환 prompt**: `"수집 완료. 바로 학습으로 진행할까요? [Y/n]"` 표시 확인. Y 선택 시 flow 3~ 학습 mode 자동 진입 + 방금 수집 `dataset_name` 자동 선택 확인 (V3 통합 검증 가능). n 선택 시 저장 안내 + 종료 확인
  12. **04 BACKLOG #14 실물 확인**: flow 2 항목 9 실행 시 NoneType 에러 발생 없음 확인. 정적 분석 결과 `serial.Serial` context manager 패턴으로 재현 불가 예측 — 실물에서 PASS/SKIP 어느 쪽이든 크래시 없으면 PASS
- **prod-test-runner 결과 요약**: devPC 정적 검증 완료 — py_compile 9/9 OK, ruff All checks passed (9파일), bash -n 3/3 OK. G-4 인계 체인 4단계 코드 직접 확인 (완전). H-(b) rsync 제거 grep 0건 확인. record.py data_root line 206·384 `~/smolvla/dgx/data/` 확인. 04 BACKLOG #14 사전 진단: serial.Serial context manager 패턴으로 NoneType 재현 불가 구조 확인
- **참고 파일**: `context/todos/V2/03_prod-test.md`

### [TODO-V3] dgx/interactive_cli/ 학습 mode 회귀 검증 (05 X3 통합)

- **상태**: 사용자 무시 결정 (2026-05-03, BACKLOG 이관) — DGX·Orin 시연장 환경 떨어짐. devPC 정적 통과 후 다음 사이클 처리
- **사용자 검증 필요 사항**:
  1. **DGX 배포**: `bash scripts/deploy_dgx.sh` 실행 후 DGX VSCode remote-ssh 터미널에서 `bash dgx/interactive_cli/main.sh`
  2. **flow 0~3 진입**: 장치 선택 (dgx) → 환경 체크 → flow 3 mode 선택 메뉴 출력 확인 `(1) 수집 / (2) 학습 / (3) 종료`
  3. **학습 mode 진입**: `(2) 학습` 선택 — 또는 V2 수집 완료 후 G-4 전환 prompt 에서 Y 입력
  4. **preflight 5단계 PASS**: `preflight_check.sh` (venv·메모리·Walking RL·Ollama·디스크) 모두 통과 확인
  5. **데이터셋 선택**: V2 수집 dataset_name 자동 인계 확인 또는 HF Hub `lerobot/svla_so100_pickplace` 입력
  6. **smoke_test 동의 게이트**: 프롬프트 "5~15분 소요, ~100MB 다운로드 가능" 출력 확인 → Y 입력 → smoke_test.sh 5~15분 실행 → "체크포인트를 저장하지 않습니다" 완료 메시지 확인. 주의: 학교 WiFi 에서 svla_so100_pickplace 다운로드 (~100MB) 차단 시 다른 네트워크 사용
  7. **save_dummy_checkpoint 실행**: `bash dgx/scripts/save_dummy_checkpoint.sh` 직접 실행 → `dgx/outputs/train/dummy_ckpt/checkpoints/` 생성 확인
  8. **ckpt 케이스 4건 출력**: flow 5 ckpt 관리 메뉴에서 (1) 케이스 1·2 Orin 네트워크, (2) 케이스 3 차기 사이클 안내 메시지, (3) 나중에, (4) USB 4건 출력 확인
  9. **G-4 단발 종료**: 학습 완료 후 mode 메뉴 재진입 없이 종료 확인
  10. **05 X3 통합 완료**: 위 6~8 항목 통과 시 05 spec X3 NEEDS_USER_VERIFICATION (smoke_test + save_dummy_ckpt + ckpt 케이스) 흡수 완료로 처리
- **prod-test-runner 결과 요약**: devPC 정적 검증 17건 전부 PASS. sync_ckpt 7라인 실행 코드 0건 확인, run_training_flow_with_dataset 시그니처 신규 + 기존 run_training_flow 공존, smoke 동의 게이트 코드 존재, CKPT_CASES 4건(케이스 3 = 차기 사이클 안내) 정합. dgx/scripts 3종(preflight/smoke/save_dummy) 미접촉 확인.
- **참고 파일**: `context/todos/V3/03_prod-test.md`
