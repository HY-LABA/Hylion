# orin/inference/ — 시연 환경 추론 운영 entry point

> 책임: 시연장 Orin 에서 호출되는 SmolVLA 추론 entry point. 학습된 정책 ckpt + 실 SO-ARM + 실 카메라로 hardware-in-the-loop 추론 수행.
> 신설: 04_infra_setup TODO-O2b (2026-04-30)
> 형제: `orin/tests/` (검증·측정 스크립트), `orin/examples/tutorial/smolvla/` (upstream 미러)

---

## 책임 — 단순 검증/측정과 구분

| 디렉터리 | 책임 | 호출 시점 |
|---|---|---|
| **`orin/inference/`** (본 디렉터리) | **시연 환경 추론** — 운영 entry point | 시연 시 호출됨 |
| `orin/tests/` | 환경 검증·호환성·baseline·latency 측정 | 개발·검증 단계에서 호출 |
| `orin/examples/tutorial/smolvla/` | upstream lerobot 미러 — 사용법 학습용 | 참조만 |

본 디렉터리는 **사용자가 시연 시 직접 호출하는 운영 스크립트** 만 담음.

---

## 자산 (현재)

| 파일 | 책임 | 출처 |
|---|---|---|
| `hil_inference.py` | SmolVLA 사전학습 ckpt (`lerobot/smolvla_base`) 로 실 SO-ARM hardware-in-the-loop 추론. dry-run / live 두 모드 + 안전 장치 (n_action_steps=5, SIGINT 핸들러, try/finally disconnect, `--flip-cameras`). **사전학습 ckpt 책임 보존 — 갱신 X** | 03_smolvla_test_on_orin TODO-07 산출물 (2026-04-29 작성, 04 TODO-O2b 에서 `orin/examples/tutorial/smolvla/` 로부터 이관) |
| `lego_v1_inference.py` | BaboGaeguri/lego_v1 fine-tune ckpt (lerobot/smolvla_base fine-tune) HIL 추론. fourcc=MJPG (USB 2.0 hub), overview/wrist 카메라 키, GATE_CAMERA_ALIAS. | 08_final_e2e TODO 산출물 |
| `leftarm_v2_inference.py` | v2 학습 ckpt (`BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`) + LoRA adapter + rename_map 추론. task1/task2 CLI 인자로 instruction 분기. USER_OVERRIDE 2026-05-18 옵션 W 결과 (lerobot-record 폐기 → 신규 entry 작성). peft>=0.10.0 필요. | 02_leftarm_v2_finetune TODO-03-F (2026-05-18) |
| `leftarm_base_inference.py` | **zero-shot 추론 전용** — `lerobot/smolvla_base` 사전학습 모델만 로딩 (LoRA adapter 없음, peft 의존 X). leftarm_v2_inference.py 와 *동일 환경* (rename_map, camera config, task1/task2 instruction, gate-json) 으로 *base VLM 의 우리 환경 응답성* 정성 측정. 가설 분리 검증 사이클 작업 1 — A2 의 0% 결과가 (α) VLM LoRA 손상 인지 (β) 데이터 부족 인지 분리 위함 (learning_log §M1.5 추론 후 가설 분리 검증 사이클). | M1.5 분리 검증 사이클 (2026-05-18, 책임 분리 결정으로 leftarm_v2_inference.py 변경 X) |

## 자산 (예정 — 후속 마일스톤별 추가)

본 디렉터리는 **마일스톤별 추론 정책 진화 추적** 의 역할도 가짐. 향후 후보:

| 시점 | 자산 | 사유 |
|---|---|---|
| 향후 | `archive/` 디렉터리 또는 `<milestone>/` 하위 디렉터리 | 정책 버전 분기 시 (지금은 단일 entry 라 불필요. 다음 milestone 진입 시 검토) |

---

## 외부 의존성

- `orin/checkpoints/<run_name>/<step>/pretrained_model/` — 학습된 ckpt 로드 위치 (05 TODO-13 시점부터)
- `orin/config/{ports,cameras}.json` — SO-ARM·카메라 설정 cache
- `orin/tests/check_hardware.sh --mode resume` — 운영 진입 직전 게이트 (TODO-G1 구현 후 hil_inference.py 가 sub-call)
- `orin/lerobot/` — SmolVLA 추론 모듈 (정책 + 카메라 + robot 추상화)

---

## 사전 단계 — 카메라 인덱스 발견 (03 BACKLOG #15)

`orin/config/cameras.json` 에는 `index` 외에도 `rotation`, `width`, `height`, `fps`, `fourcc` 필드가 있으며, `leftarm_v2_inference.py` 가 이를 읽어 `OpenCVCameraConfig` 를 구성한다 (수집/학습 base_config.yaml 의 카메라 설정과 정합 — TODO-03-H 2026-05-18). 시연 전 `cameras.json` 의 `index` 만 채우면 되고, 나머지 필드는 기본값이 기재돼 있어 변경 불필요.

hil_inference.py 실행 전 **반드시** 카메라 인덱스를 확인하라.
Linux 에서 카메라 인덱스(/dev/videoN)는 재부팅·USB 재연결 시 변경될 수 있다.

```bash
source ~/smolvla/orin/.hylion_arm/bin/activate
lerobot-find-cameras opencv
```

출력 예시:

```
--- Detected Cameras ---
Camera #0:
  Name: OpenCV Camera @ /dev/video2
  Type: OpenCV
  Id: /dev/video2
  ...
Camera #1:
  Name: OpenCV Camera @ /dev/video4
  Type: OpenCV
  Id: /dev/video4
  ...
```

위 결과를 바탕으로 `--cameras top:2,wrist:4` (또는 해당하는 인덱스) 를 명시한다.

**자동 발견 fallback**: `--cameras` 를 생략하면 `OpenCVCamera.find_cameras()` 로 자동 발견.
발견 수가 정확히 2 대일 때만 자동 적용 (첫 번째 → top, 두 번째 → wrist).
자동 발견 실패 또는 2 대가 아니면 기본값 `top:0,wrist:1` 로 후퇴하며 경고를 출력한다.

## wrist 카메라 플립 (03 BACKLOG #16)

wrist 카메라를 거꾸로 장착한 경우 `--flip-cameras wrist` 를 추가하라.
이미지가 수직 반전되어 policy 에 전달된다.

사전학습 분포(svla_so100_pickplace)의 wrist 카메라 방향과의 정합 여부는
08_leftarmVLA 진입 시 확인 예정 (03 BACKLOG #11).

`--gate-json` 으로 `orin/config/cameras.json` 을 지정하면 `wrist.flip: true` 설정이
자동 반영된다 (`check_hardware.sh` 생성 cache).

---

## 사용 예시

### Step 1 — 카메라 인덱스 확인

```bash
source ~/smolvla/orin/.hylion_arm/bin/activate
lerobot-find-cameras opencv
```

### dry-run 모드 (action 만 dump, follower 미동작)

```bash
source ~/smolvla/orin/.hylion_arm/bin/activate
python ~/smolvla/orin/inference/hil_inference.py \
    --mode dry-run \
    --follower-port /dev/ttyACM1 \
    --cameras top:2,wrist:0 \
    --flip-cameras wrist \
    --max-steps 5 \
    --output-json /tmp/hil_dryrun.json
```

### live 모드 (실 SO-ARM action 송신)

```bash
python ~/smolvla/orin/inference/hil_inference.py \
    --mode live \
    --follower-port /dev/ttyACM1 \
    --cameras top:2,wrist:0 \
    --flip-cameras wrist \
    --n-action-steps 5 \
    --max-steps 50
```

비상정지: Ctrl+C — SIGINT 핸들러가 현재 step 마무리 후 graceful disconnect.

### gate-json 통합 (자동 인자 채우기)

`orin/config/` 에 `ports.json` + `cameras.json` 이 있으면:

```bash
python ~/smolvla/orin/inference/hil_inference.py \
    --mode dry-run \
    --gate-json ~/smolvla/orin/config/ \
    --max-steps 5 \
    --output-json /tmp/hil_dryrun.json
```

`--follower-port`, `--cameras`, `--flip-cameras` 를 자동으로 채운다 (CLI 직접 지정이 우선).

---

## 참고

- `docs/storage/07_orin_structure.md` §2 (inference/ 컴포넌트 책임)
- `docs/storage/legacy/arm_2week_plan/work_flow/specs/history/04_infra_setup.md` TODO-O2b (본 디렉터리 신설 사유)
- `docs/storage/legacy/arm_2week_plan/work_flow/specs/history/03_smolvla_test_on_orin.md` TODO-07 / TODO-07b (hil_inference.py 의 출처 + prod 검증 결과)
