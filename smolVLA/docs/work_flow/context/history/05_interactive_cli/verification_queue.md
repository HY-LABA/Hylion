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

## 활성 spec: 05_interactive_cli

### [TODO-X3] dgx/interactive_cli/ prod 검증 (04 BACKLOG #7 X3·T1·T2 통합)

- **상태**: 자동 검증 통과 (NEEDS_USER_VERIFICATION)
- **사용자 검증 필요 사항**:
  1. DGX SSH 진입: `ssh dgx` 또는 VSCode remote-ssh → DGX 터미널
  2. `bash ~/smolvla/dgx/interactive_cli/main.sh` 실행
  3. flow 0~2: 진입·노드 선택·preflight (env_check 결과 확인)
  4. flow 3: 시나리오 선택 — smoke 권장 (메모리 20GB 요구, 현재 가용 114GB)
  5. flow 4: 데이터셋 선택 — smoke 기본값 `lerobot/svla_so100_pickplace` 채택
  6. flow 5: smoke test 동의 게이트 Y 입력 후 `smoke_test.sh` 실행
     - 소요 시간: 5~15분 (1 step 학습)
     - 최초 실행 시 svla_so100_pickplace ~100MB 이상 다운로드 동의 필요
  7. smoke_test 완료 후 ckpt 케이스 목록(1~4) 출력 확인
  8. (선택·04 T1 통합) HF Hub push 실 검증 — 데이터셋 다운로드 분기 확인
  9. (선택·04 T2 통합) ckpt 케이스 중 하나 선택 → 전송 안내 출력 확인
- **prod-test-runner 결과 요약**:
  - devPC 정적 검증: `py_compile` 3파일 통과, `bash -n main.sh` 통과, `ruff` All checks passed (F401·F541 0건), entry.py --help ImportError 없음
  - 구조 검증: CKPT_CASES ['1','2','3','4'] 확인, SCENARIOS ['smoke','s1','s3','lora'] 확인, _smoke_consent_gate Y/n 정상, _show_ckpt_management 자동 감지 없음
  - DGX 배포: `bash scripts/deploy_dgx.sh` 성공 (7개 파일 신규 sync)
  - DGX 원격 검증: py_compile 3파일 통과, bash -n 통과, --help 정상, training.py import 구조 확인
  - DGX 환경: 디스크 3.3T 가용, 메모리 114GB 가용, GPU idle (NVIDIA GB10)
- **참고 파일**: `context/todos/X3/03_prod-test.md`

### [TODO-D3] datacollector/interactive_cli/ prod 검증 (04 BACKLOG #7·#8·#9 통합)

- **상태**: 자동 정적 검증 통과 (NEEDS_USER_VERIFICATION)
- **사용자 검증 필요 사항**:
  1. **DataCollector 머신 셋업** (04 BACKLOG #7) — `docs/storage/07_datacollector_venv_setting.md` + `docs/storage/10_datacollector_structure.md` 기준 16단계 완료 (Ubuntu 22.04 LTS x86_64, .hylion_collector venv, lerobot editable 설치)
  2. **SO-ARM 임시 연결** — follower `/dev/ttyACM1`, leader `/dev/ttyACM0` 등록 확인
  3. **카메라 임시 연결** — wrist + overview (OpenCV index 0·1 probe 성공)
  4. **deploy 실행** — `bash scripts/deploy_datacollector.sh` (SSH alias 'datacollector' 등록 후)
  5. **main.sh 실행 + flow 0~7 완주** — `bash ~/smolvla/datacollector/interactive_cli/main.sh` → flow 2 env check 전 항목 PASS → flow 3 teleop → flow 4 teleop 확인 → flow 5 옵션 1 채택 → flow 6 5 episodes dummy dataset 수집
  6. **flow 7 분기 3건 모두 검증**:
     - 분기 1 (HF Hub): `export HF_TOKEN=hf_xxx` 설정 후 업로드 (또는 `--private`)
     - 분기 2 (rsync): "devPC 에서 bash smolVLA/scripts/sync_dataset_collector_to_dgx.sh --dataset <name>" 안내 메시지 출력 확인 → devPC 에서 직접 실행
     - 분기 3 (안함): 로컬 저장만 유지 (`~/smolvla/datacollector/data/<dataset>/` 존재 확인)
  7. **04 BACKLOG #9 G4 prod 검증** — flow 2 env_check 5단계 `[PASS]` 출력 실물 확인
- **prod-test-runner 결과 요약**:
  - devPC 정적 검증: `py_compile` 6파일 통과, `bash -n main.sh` 통과, `python3 entry.py --help` ImportError 없음 (cycle 2 Critical #1 정정 확인)
  - 안전 검사: transfer.py rsync subprocess 호출 없음 (안내 메시지만), record.py `_validate_camera_indices` 2-param (자기비교 제거), `_validate_data_kind_choice` 단일 호출(line 317), env_check.py 5단계 순서 D1 §1 정합 (venv→USB→camera→lerobot→data_dir)
  - 배포 스크립트 정적 확인: `deploy_datacollector.sh` 가 `datacollector/` 전체 rsync 대상으로 포함, `interactive_cli/` exclude 없음
  - 04 BACKLOG #8 G3 check_hardware 이식 코드 확인 완료 (env_check.py 5단계, 04 G1 패턴 미러)
  - DataCollector 머신 실 deploy: SSH alias 미등록 상태 — 사용자 환경 셋업 후 가능
- **참고 파일**: `context/todos/D3/03_prod-test.md`

### [TODO-O3] orin/interactive_cli/ prod 검증 (04 BACKLOG #7 G2 통합)

- **상태**: 자동 정적 검증 통과 (NEEDS_USER_VERIFICATION) — Orin SSH 불통으로 원격 검증 미수행
- **사용자 검증 필요 사항**:
  1. **Orin 네트워크 연결 확인** — devPC ↔ Orin SSH 연결 확립 (`docs/storage/04_devnetwork.md`)
  2. **deploy 실행** — `bash scripts/deploy_orin.sh` (devPC 에서, SSH 연결 후, Category B 외 → 자율 실행 가능)
  3. **check_hardware.sh --mode first-time** 완료 — `orin/config/ports.json` + `cameras.json` 생성 확인
  4. **카메라 2대 + SO-ARM follower 물리 연결** — top 카메라 + wrist 카메라 + follower 포트
  5. **VSCode remote-ssh → Orin → `bash ~/smolvla/orin/interactive_cli/main.sh`**:
     - flow 1: orin [*] 선택 (번호 1 입력)
     - flow 2: env_check.py — `check_hardware.sh --mode resume` exit 0 확인
     - flow 3: 기본값 (3) 선택 → `lerobot/smolvla_base`
     - flow 4: dry-run (1) 선택 → hil_inference subprocess 실행 확인
     - flow 5: `/tmp/hil_dryrun.json` 생성 + 결과 출력 확인
  6. **04 G2 통합 — first-time/resume 환경 검증** (`check_hardware.sh` 양방향 모드 확인)
  7. **04 G2 통합 — hil_inference 50-step 실행** (live 모드, max-steps=50, SO-ARM follower 동작 확인)
  8. **03 사이클 회귀 확인** — 인자 미전달 직접 호출 시 `smolvla_base` 모델 로드 동일 동작
- **prod-test-runner 결과 요약**:
  - devPC 정적 검증: `py_compile` 4파일 통과 (env_check·inference·entry·hil_inference), `bash -n main.sh` 통과, entry.py importlib 로드 ImportError 없음
  - AST parse 4파일 전부 SyntaxError 없음
  - hil_inference.py `--model-id` (line 247) + `--ckpt-path` (line 257) 존재 확인
  - effective_model 우선순위 시뮬레이션: 인자 미전달 → `"lerobot/smolvla_base"` (03 사이클 회귀 없음)
  - deploy_orin.sh 정적 검토: `orin/` 전체 sync, `interactive_cli/` exclude 없음 → 배포 시 포함 확인
  - Orin SSH 상태: Connection timed out (172.16.137.232:22) — 네트워크 연결 필요
- **참고 파일**: `context/todos/O3/03_prod-test.md`
