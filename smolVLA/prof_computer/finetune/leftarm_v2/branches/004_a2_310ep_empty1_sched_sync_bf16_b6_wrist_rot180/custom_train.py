"""004 분기 — LeRobotDataset.__getitem__ monkey-patch 로 wrist selective 180° rotation 적용.

lerobot upstream 무수정 (옵션 B 보존) + lerobot-train 의 학습 흐름 그대로 재사용.
본 entry 는 Python 프로세스 *시작 시점* 에 LeRobotDataset.__getitem__ 을 monkey-patch
한 다음 lerobot_train.train() 을 직접 호출. CLI 인자 파싱은 lerobot 의 @parser.wrap()
데코레이터가 자동 처리.

배경 (구현 경로 선택):
- lerobot 의 image_transforms API 는 *카메라별 selective* 미지원 (DatasetReader.__getitem__
  의 image_transforms(item[cam]) 가 cam 키 정보 전달 X — research_wrist_orientation §Q2)
- 자체 train loop 작성 (~150줄) 보다 monkey-patch (~5줄) 가 *짧고 안전* —
  lerobot 의 모든 기능 (PEFT, accelerate, wandb, ckpt save, scheduler 등) 무변화 재사용

사용: run_train.py 가 본 모듈을 import 한 뒤 lerobot.scripts.lerobot_train.train() 호출.
정확한 진입 방식은 run_train.py 의 cmd_train() 함수 참조.

Wrist 카메라 키 결정:
- base_config.yaml.cameras 의 *두 번째 키* = wrist (top, wrist 순)
- run_train.py 의 rename_map 이 'observation.images.wrist' → 'observation.images.camera2' 변환
- 따라서 patch 대상 키 = 'observation.images.camera2'

검증: smoke test 시작 시 sanity check 출력 (patch 활성 + wrist 카메라 키 확인).
"""
import sys
import torch
from torchvision.transforms.v2 import functional as TF
from lerobot.datasets.lerobot_dataset import LeRobotDataset


# ── Monkey-patch 대상 카메라 키 ──
# rename_map 은 LeRobotDataset.__getitem__ *밖* (학습 파이프라인의 collator/preprocessor 단계)
# 에서 적용됨 — __getitem__ 시점엔 *원본 키* 그대로. 실측 확인 (2026-05-21):
#   ds = LeRobotDataset('BaboGaeguri/leftarm_v2', episodes=[0])
#   item = ds[0]
#   list(item.keys()) → ['observation.images.top', 'observation.images.wrist', ...]
# 따라서 patch 대상은 원본 키 'observation.images.wrist'.
_WRIST_KEY = "observation.images.wrist"
_ROTATION_DEG = 180

# ── 원본 __getitem__ 보존 + monkey-patch 적용 ──
_ORIG_GETITEM = LeRobotDataset.__getitem__


def _patched_getitem(self, idx):
    """원본 __getitem__ 결과의 wrist 카메라만 180° 회전 추가 적용."""
    item = _ORIG_GETITEM(self, idx)
    if _WRIST_KEY in item:
        img = item[_WRIST_KEY]
        if isinstance(img, torch.Tensor):
            item[_WRIST_KEY] = TF.rotate(img, angle=_ROTATION_DEG)
    return item


def apply_wrist_rotation_patch():
    """LeRobotDataset.__getitem__ 에 wrist 회전 patch 적용.

    멱등 — 여러 번 호출해도 한 번만 적용. 본 함수가 호출되기 전까지 patch 비활성.
    """
    if getattr(LeRobotDataset.__getitem__, "_wrist_patched", False):
        print(f"[004_custom_train] wrist rotation patch 이미 적용됨", file=sys.stderr)
        return
    _patched_getitem._wrist_patched = True
    LeRobotDataset.__getitem__ = _patched_getitem
    print(f"[004_custom_train] LeRobotDataset.__getitem__ patch 적용 — "
          f"key='{_WRIST_KEY}' rotation={_ROTATION_DEG}°", file=sys.stderr)


def sanity_check(dataset_meta):
    """patch 대상 카메라 키가 실제 dataset 의 camera_keys 에 존재하는지 검증.

    Args:
        dataset_meta: LeRobotDataset.meta 또는 유사 객체 (camera_keys 속성 필요)

    Raises:
        RuntimeError: _WRIST_KEY 가 dataset camera_keys 에 없으면 (rename_map mismatch)
    """
    keys = list(getattr(dataset_meta, "camera_keys", []))
    if _WRIST_KEY not in keys:
        raise RuntimeError(
            f"[004_custom_train] sanity check 실패 — wrist patch 대상 키 '{_WRIST_KEY}' 가 "
            f"dataset camera_keys 에 없음. 실제 키: {keys}. "
            f"base_config.cameras 순서 또는 rename_map 확인 필요."
        )
    print(f"[004_custom_train] sanity check 통과 — camera_keys={keys}, "
          f"wrist patch 적용 대상='{_WRIST_KEY}'", file=sys.stderr)


if __name__ == "__main__":
    # 직접 실행 시 — lerobot-train 의 train() 함수를 호출.
    # patch 적용 → lerobot 의 @parser.wrap() 이 sys.argv 파싱 → train() 실행
    apply_wrist_rotation_patch()

    # lerobot_train.train() 의 @parser.wrap() 데코레이터가 sys.argv 를 직접 파싱.
    # 본 entry 의 sys.argv 는 run_train.py 가 sys.argv 를 lerobot-train 인자로 구성해 넘김.
    from lerobot.scripts.lerobot_train import train
    train()
