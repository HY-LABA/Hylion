# TODO-O5 — Prod Test

> 작성: 2026-05-03 | prod-test-runner | cycle: 1

## Verdict

**`AUTOMATED_PASS`**

---

## 배포 대상

- Orin

## 배포 결과

- 명령: `bash scripts/deploy_orin.sh`
- 결과: 성공 (rsync speedup 131.95)
- 갱신 파일: `scripts/run_python.sh`, `tests/inference_baseline.py`
- **주의 사항**: deploy_orin.sh 의 `--delete` 옵션이 Orin 측 `checkpoints/07_pilot_2k/` 를 삭제함. devPC 에 checkpoints 디렉터리가 없으므로 rsync --delete 가 제거. `sync_ckpt_dgx_to_orin.sh --run 07_pilot_2k --step 002000` 로 즉시 복구 완료 (7파일 865M, safetensors 헤더 OK).

## Step 1 — Orin SSH 가용성 + ckpt 확인

| 항목 | 결과 |
|---|---|
| SSH 가용 | ubuntu [SSH OK] |
| checkpoints 7파일 | deploy --delete 로 삭제됨 → sync_ckpt 재실행으로 복구 |
| 복구 후 7파일 | config.json / model.safetensors (865M) / policy_postprocessor*.json·safetensors / policy_preprocessor*.json·safetensors / train_config.json |
| safetensors 헤더 | 8 byte OK |
| run_python.sh 권한 | -rwxr-xr-x (755) |
| inference_baseline.py 갱신 | 2026-05-04 14:10 (배포 후 타임스탬프 확인) |

## Step 2 — 배포 후 ckpt 복구

```bash
# deploy --delete 로 삭제된 ckpt 복구
bash scripts/sync_ckpt_dgx_to_orin.sh --run 07_pilot_2k --step 002000
# DGX → devPC: 709MB 수신 (12.5 MB/s) → Orin: 709MB 전송 (5.1 MB/s)
# 결과: Orin /home/laba/smolvla/orin/checkpoints/07_pilot_2k/002000/ 7파일 865M 복구
```

## Step 3 — run_python.sh wrapper 버그 발견

run_python.sh 직접 실행 시 실패:
```
ssh orin "~/smolvla/orin/scripts/run_python.sh ~/smolvla/orin/tests/inference_baseline.py --ckpt-path ..."
# exit 1: /home/laba/smolvla/orin/.hylion_arm/bin/activate: 줄 133: LD_LIBRARY_PATH: 바인딩 해제한 변수
```

**원인**: run_python.sh 의 `set -euo pipefail` 중 `-u` 플래그가 source 한 activate 스크립트 내부에도 적용됨. activate L133 에서 `export LD_LIBRARY_PATH=...:$LD_LIBRARY_PATH` 시 `$LD_LIBRARY_PATH` 가 unset 상태이면 `-u` 위반 → exit 1.

**우회**: `export LD_LIBRARY_PATH=''` 사전 설정 후 실행 (또는 venv 직접 activate) 으로 통과.

**분류**: O2 (run_python.sh) 산출물 버그. O5 코드 (inference_baseline.py) 자체 문제 아님. BACKLOG 추가 처리.

## Step 4 — 핵심 검증 — T3 ckpt 로드 + 더미 obs forward

```bash
# 우회: LD_LIBRARY_PATH 사전 초기화
ssh orin "export LD_LIBRARY_PATH='' && \
    ~/smolvla/orin/scripts/run_python.sh \
    ~/smolvla/orin/tests/inference_baseline.py \
    --ckpt-path ~/smolvla/orin/checkpoints/07_pilot_2k/002000 2>&1"
```

실제 출력:
```
[load] 로컬 ckpt 경로: /home/laba/smolvla/orin/checkpoints/07_pilot_2k/002000
[device] cuda
[load] SmolVLAPolicy.from_pretrained 시작...
Loading  HuggingFaceTB/SmolVLM2-500M-Video-Instruct weights ...
Loading weights: 100%|██████████| 489/489 [00:02<00:00, 224.73it/s]
Reducing the number of VLM layers to 16 ...
Loading weights from local directory
[load] 완료
[input_features]
  observation.state: PolicyFeature(type=<FeatureType.STATE: 'STATE'>, shape=(6,))
  observation.images.camera1: PolicyFeature(type=<FeatureType.VISUAL: 'VISUAL'>, shape=(3, 256, 256))
  observation.images.camera2: PolicyFeature(type=<FeatureType.VISUAL: 'VISUAL'>, shape=(3, 256, 256))
  observation.images.camera3: PolicyFeature(type=<FeatureType.VISUAL: 'VISUAL'>, shape=(3, 256, 256))
[dummy_obs keys] ['observation.state', 'observation.images.camera1', 'observation.images.camera2', 'observation.images.camera3']
[result] Action shape: (1, 6)
[result] Action dtype: torch.float32
[result] Action min:   6.802454
[result] Action max:   78.516670
[DOD] action shape (1, 6) OK
[done] exit 0
```

결과: exit 0 확인.

## 보조 검증 — venv 직접 activate 방식

```bash
ssh orin "source ~/smolvla/orin/.hylion_arm/bin/activate && \
    python3 ~/smolvla/orin/tests/inference_baseline.py \
    --ckpt-path ~/smolvla/orin/checkpoints/07_pilot_2k/002000 2>&1"
```

동일 결과 — cuSPARSELt ImportError X, `[DOD] action shape (1, 6) OK`, exit 0 확인.

## 자동 비대화형 검증 결과

| 검증 | 명령 | 결과 |
|---|---|---|
| ckpt 존재 (7파일) | `ssh orin ls checkpoints/007_pilot_2k/002000` | sync_ckpt 복구 후 7파일 865M 확인 |
| run_python.sh 권한 | `ssh orin ls -la run_python.sh` | -rwxr-xr-x 755 확인 |
| inference_baseline.py 갱신 | 배포 후 타임스탬프 | 2026-05-04 14:10 (6260 bytes) |
| ckpt 로드 (로컬 경로) | run_python.sh wrapper + LD_LIBRARY_PATH='' | Loading weights from local directory + 완료 |
| 더미 obs forward | select_action + action.shape | (1, 6) 확인 |
| DOD 출력 | stdout | `[DOD] action shape (1, 6) OK` |
| exit code | echo $? | 0 |
| cuSPARSELt ImportError | stderr 없음 확인 | X (ImportError 없음) |
| input_features 자동 추출 | stdout [input_features] | state(6,) + camera1/2/3(3,256,256) 3슬롯 |
| T3 ckpt camera key | config 반영 | camera1/camera2/camera3 — smolvla_base 동일 구조 (shape 불일치 없음) |

## DOD 자동 부합

| DOD 항목 | 자동 검증 | 결과 |
|---|---|---|
| 1. T3 ckpt 또는 fallback lerobot/smolvla_base 로드 | yes (SSH — 로컬 ckpt 로드 성공) | ✅ |
| 2. inference_baseline.py 패턴으로 더미 obs forward 1회 | yes (SSH — select_action 호출 성공) | ✅ |
| 3. exit 0 + action shape (1, 6) 정상 출력 | yes (SSH — `[DOD] action shape (1, 6) OK` + exit 0) | ✅ |
| 4. SO-ARM 직결 hil_inference 50-step BACKLOG 마킹 | N/A (PHYS_REQUIRED — verification_queue 추가) | → BACKLOG |
| 5. --ckpt-path / --model-id 충돌 방지 | yes (code-tester 단위 검증 완료) | ✅ |

## 사용자 실물 검증 필요 사항

없음 — DOD 4 (SO-ARM 직결 hil_inference 50-step) 는 본 todo 범위 외 (PHYS_REQUIRED, 기존 BACKLOG #1 으로 유지).

## BACKLOG 추가 항목

1. **run_python.sh `-u` 플래그 버그** — `set -euo pipefail` 의 `-u` 가 source 한 activate 내 `$LD_LIBRARY_PATH` unset 참조 시 exit 1. 우회: `export LD_LIBRARY_PATH=''` 사전 설정. 수정 방향: activate 전 `set +u` 일시 해제 후 재활성화, 또는 `export LD_LIBRARY_PATH="${LD_LIBRARY_PATH:-}"` 패턴 적용.
2. **deploy_orin.sh --delete 와 Orin-only 리소스 충돌** — checkpoints/, calibration/ 등 Orin 측 데이터 디렉터리가 devPC 에 없으면 --delete 로 삭제됨. calibration 은 기존 exclude 처리됨. checkpoints 도 exclude 추가 검토 필요.

## CLAUDE.md 준수

- Category B 영역 (orin/lerobot/ 등) 변경된 배포: 없음 — 해당 없음
- 자율 영역만 사용: deploy_orin.sh (Category B 외), ssh read-only, sync_ckpt (5분 미만 rsync 2-hop)
- sync_ckpt 실행 시간: DGX→devPC ~57초 + devPC→Orin ~140초 = 총 약 3.5분 (5분 미만 — 자율)
