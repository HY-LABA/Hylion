# orin/inference/ — 시연 환경 추론 운영 entry point

> 책임: 시연장 Orin 에서 호출되는 SmolVLA 추론 entry point. 학습된 정책 ckpt + 실 SO-ARM + 실 카메라로 hardware-in-the-loop 추론 수행.
> 형제: `orin/tests/` (검증·측정 스크립트), `orin/docs/legacy/` (옛 era 추론 entry 보존)

---

## 책임 — 단순 검증/측정과 구분

| 디렉터리 | 책임 | 호출 시점 |
|---|---|---|
| **`orin/inference/`** (본 디렉터리) | **현행 era 추론 운영 entry** | 시연 시 호출됨 |
| `orin/tests/` | 환경 검증·호환성·baseline·latency 측정 | 개발·검증 단계에서 호출 |
| `orin/docs/legacy/` | 옛 era 추론 entry 보존 (lego_v1 era 등) | 직접 호출 안 함, 참조만 |

본 디렉터리는 **사용자가 시연 시 직접 호출하는 현행 era 운영 스크립트** 만 담음.

---

## 자산 (현행 — leftarm_v2 era)

| 파일 | 책임 |
|---|---|
| `leftarm_v2_inference.py` | leftarm_v2 era 학습 ckpt + LoRA adapter + rename_map 추론. task1/task2 CLI 인자로 instruction 분기. `CKPT_REPO_ID` env override 로 분기 ckpt 선택 (default = 001 분기, `BaboGaeguri/leftarm_v2_A2_pc_2026-05-17`). peft>=0.10.0 필요 |
| `leftarm_base_inference.py` | **zero-shot 추론 전용** — `lerobot/smolvla_base` 사전학습 모델만 로딩 (LoRA adapter 없음, peft 의존 X). leftarm_v2_inference.py 와 *동일 환경* (rename_map, camera config, task1/task2 instruction, gate-json) 으로 *base VLM 의 우리 환경 응답성* 정성 측정. 분리 검증용 자산. |

> *분기 종속 X*: 두 entry 는 *era 단위* 또는 *검증 유형 단위*. 학습 분기 인덱스 (001/002/003/004) 마다 별도 파일 만들지 않음. `leftarm_v2_inference.py` 한 파일이 *leftarm_v2 era 의 모든 분기 ckpt* 추론에 사용 — ckpt 선택은 `CKPT_REPO_ID` env override.

---

## Legacy 자산 (참조용 — `orin/docs/legacy/`)

| 파일 | 옛 책임 |
|---|---|
| `orin/docs/legacy/hil_inference.py` | (era 무관) SmolVLA 사전학습 ckpt 로 Orin 환경 셋업 동작 검증. dry-run / live 두 모드. *현 era 에서는 `leftarm_base_inference.py` 가 zero-shot 검증 책임 흡수* |
| `orin/docs/legacy/lego_v1_inference.py` | lego_v1 era 의 fine-tune ckpt HIL 추론. *옛 era 산출물 보존용* |

→ 현 era 시연·평가에서는 호출 X. 코드 패턴 참조용으로만 잔존.

---

## 외부 의존성

- `orin/checkpoints/<repo_id>/` — 학습된 ckpt 로드 위치 (HF Hub `hf download` 캐시)
- `orin/config/udev/99-hylion.rules` — 디바이스 심볼릭 링크 (`/dev/cam_top`, `/dev/cam_wrist`, `/dev/so_arm_left`, `/dev/so_arm_right`)
- `orin/config/cameras.json` — 카메라 부가 설정 (rotation/width/height/fps/fourcc/flip)
- `orin/lerobot/` — SmolVLA 추론 모듈 (정책 + 카메라 + robot 추상화)

---

## 디바이스 매핑 — udev rule 도입 (2026-05-24)

이전엔 `lerobot-find-cameras opencv` 로 인덱스 발견 + `cameras.json` 의 `index` 필드 cache 갱신이 필수였다. udev rule 도입 후엔 다음 4개 심볼릭 링크가 시리얼 기반으로 영속 생성된다:

| 링크 | 대상 디바이스 |
|---|---|
| `/dev/cam_top` | YJX-C5 카메라 |
| `/dev/cam_wrist` | Innomaker U20CAM-720P 카메라 |
| `/dev/so_arm_left` | SO-ARM follower (좌암) |
| `/dev/so_arm_right` | SO-ARM follower (우암) |

추론 entry default 가 위 path 로 일원화. 재부팅·USB 재연결과 무관하게 동일 path. 설치 + 실측 절차는 [`orin/config/README.md`](../config/README.md) 참조.

CLI 인자로 override 가능:

```bash
# 우암으로 전환
python leftarm_v2_inference.py --follower-port /dev/so_arm_right ...
# 정수 인덱스도 하위 호환
python leftarm_v2_inference.py --cameras top:2,wrist:0 ...
```

## wrist 카메라 플립

wrist 카메라를 거꾸로 장착한 경우 `--flip-cameras wrist` 를 추가하라.
이미지가 수직 반전되어 policy 에 전달된다.

`--gate-json` 으로 `orin/config/cameras.json` 을 지정하면 `wrist.flip: true` 설정이
자동 반영된다.

---

## 사용 예시

본 디렉터리 entry 는 `orin/scripts/run_inference_leftarm_v2.sh` wrapper 를 통해 호출하는 게 표준이다. 직접 호출도 가능.

### Step 1 — udev 노드 확인

```bash
ls -la /dev/cam_top /dev/cam_wrist /dev/so_arm_left /dev/so_arm_right
```

→ 4개 모두 존재하면 OK. 미존재 시 [`orin/config/README.md`](../config/README.md) 의 설치 절차로 udev rule 재적용.

### LoRA ckpt 추론 (현행 sequence)

```bash
# wrapper 경유 (권장)
CKPT_REPO_ID=BaboGaeguri/leftarm_v2_003_a2_310ep_empty1_sched_sync_bf16_b6 \
  ~/smolvla/orin/scripts/run_inference_leftarm_v2.sh live task1
```

### zero-shot 검증 (base VLM)

```bash
~/smolvla/orin/scripts/run_inference_leftarm_v2.sh zero-shot task1
```

→ 내부적으로 `leftarm_base_inference.py` 호출. LoRA adapter 미적용, base smolvla_base 로만 추론.

비상정지: Ctrl+C — SIGINT 핸들러가 현재 step 마무리 후 graceful disconnect.

---

## 참고

- 추론 평가 시트: `orin/docs/leftarm_v2/{000_base,001,002,003}_eval_*.md`
- 학습 ckpt 출처: `prof_computer/finetune/leftarm_v2/branches/<NNN>_<방법>_<인자>/`
- 명명 컨벤션: [`prof_computer/README.md` §7](../../prof_computer/README.md)
- Legacy entry: [`orin/docs/legacy/`](../docs/legacy/)
