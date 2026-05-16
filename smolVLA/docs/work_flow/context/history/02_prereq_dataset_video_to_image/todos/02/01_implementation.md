# TODO-02 — Implementation

> 작성: 2026-05-16 | task-executor | cycle: 2

## 목표

`dgx/finetune/leftarm_v2/convert_to_image.py` — code-tester MAJOR_REVISIONS (cycle 1) 수정.
Critical 1건 (parquet image 컬럼 미포함) + Recommended 2건 모두 적용.

## 변경 파일

| 경로 | 변경 종류 | 한 줄 요약 |
|---|---|---|
| `dgx/finetune/leftarm_v2/convert_to_image.py` | M | Critical #1 parquet image 컬럼 embed + Recommended #1 total_frames 갱신 + Recommended #2 source==target 가드 |

## 적용 룰

- CLAUDE.md Hard Constraints Category A: `docs/reference/` 미변경 (read-only 참조만) ✓
- Category B: `pyproject.toml`, `orin/lerobot/` 등 미변경 ✓
- Category D: 금지 명령 미사용 ✓
- 레퍼런스 직접 Read 완료:
  - `docs/reference/lerobot/src/lerobot/datasets/feature_utils.py` L50-51 — `dtype=="image"` → `datasets.Image()` schema
  - `docs/reference/lerobot/src/lerobot/datasets/dataset_writer.py` L374-377 — `embed_images(ep_dataset)` 패턴
  - `docs/reference/lerobot/src/lerobot/datasets/io_utils.py` L61-80 — `load_nested_dataset` → `Dataset.from_parquet(features=features)` 로 Image() 스키마 전달
  - `docs/reference/lerobot/src/lerobot/datasets/io_utils.py` L98-115 — `embed_images` 구현 (embed_table_storage)
  - `docs/reference/lerobot/src/lerobot/datasets/io_utils.py` L282-296 — `to_parquet_with_hf_images` 패턴 (Dataset.from_dict + Image features + to_parquet)
  - `docs/reference/lerobot/src/lerobot/datasets/dataset_reader.py` L126-131 — `_load_hf_dataset`: features=get_hf_features_from_features → load_nested_dataset 확인

## 변경 내용 요약

### Critical #1 — rewrite_data_parquet 에 image 컬럼 embed 추가

기존 `rewrite_data_parquet` 는 video 컬럼을 drop 만 하고 image 컬럼을 추가하지 않았다. lerobot 이 image dataset 을 load 할 때 `load_nested_dataset(root/"data", features=get_hf_features_from_features(meta.features))` 를 호출하며, `features` 에는 image key 가 `datasets.Image()` 타입으로 포함된다. 따라서 parquet 에 해당 컬럼이 bytes-embedded 형태로 있어야 load 가 성공한다.

수정 패턴 (`io_utils.py:to_parquet_with_hf_images` + `dataset_writer.py:_save_episode_data` 직접 참조):
1. `df[image_key] = [str(target_root / IMAGE_PATH_PATTERN.format(...))]` — 행별 PNG 경로 문자열
2. `hf_datasets.Features({key: hf_datasets.Image() for key in video_keys})` — Image 스키마 정의
3. `ds = hf_datasets.Dataset.from_dict(data_dict, features=hf_features)` — HuggingFace Dataset 생성 (Image() feature 지정 시 경로 문자열을 PIL 이미지로 자동 디코딩)
4. `ds = embed_images(ds)` — PIL 이미지를 Arrow table 내 bytes 로 embed (io_utils.py:98-115 패턴 그대로)
5. `ds.to_parquet(str(dst_parquet))` — bytes-embedded parquet 저장

`_import_lerobot_embed()` 헬퍼를 추가하여 `--help` 시 lerobot 없이도 동작하도록 lazy import 유지.

함수 시그니처에 `target_root: Path` 인자 추가, 호출 측에도 동일하게 전달.

### Recommended #1 — total_frames 부분 변환 시 갱신

`run_conversion` 에서 `new_info["total_episodes"] = len(episode_indices)` 이후, episode metadata 를 순회하여 변환 대상 episode 들의 frame count 합계를 `new_info["total_frames"]` 에 기록. episode metadata 키 우선순위: `length` → `frame_count` → `dataset_to_index - dataset_from_index` → fallback (total_frames_extracted).

### Recommended #2 — source==target 가드

`run_conversion` 초입에 `source_root == target_root` 및 부모-자식 관계 체크 추가. 동일하거나 중첩된 경우 `log.error` + `return 1`.

## code-tester 입장에서 검증 권장 사항

- AST: `python3 -c "import ast; ast.parse(open('dgx/finetune/leftarm_v2/convert_to_image.py').read()); print('OK')"` — 통과 확인됨
- argparse: `python3 dgx/finetune/leftarm_v2/convert_to_image.py --help` — 정상 출력 확인됨
- ruff: `ruff check dgx/finetune/leftarm_v2/convert_to_image.py` — All checks passed 확인됨
- 핵심 검증: `rewrite_data_parquet` 가 `Image()` features 로 Dataset 생성 후 `embed_images` 호출 → `to_parquet` 저장하는 경로 확인
- DOD 항목:
  1. parquet image 컬럼 embed (Critical #1) ✓ — datasets.Image() + embed_images 패턴
  2. total_frames 부분 변환 시 갱신 (Recommended #1) ✓
  3. source==target 가드 (Recommended #2) ✓
  4. 기존 DOD (원본 무손상, DEFAULT_IMAGE_PATH, ffmpeg subprocess, resumable, incremental) 유지 ✓

## cycle 2 직전 피드백 반영

| Critical 이슈 | 수정 |
|---|---|
| parquet image 컬럼 미포함 — LeRobotDataset load 실패 (L390-428) | `rewrite_data_parquet` 전면 재작성: image_key 컬럼 경로 추가 → `Dataset.from_dict(features=Image())` → `embed_images()` → `to_parquet()` |

| Recommended 이슈 | 수정 |
|---|---|
| `total_frames` 부분 변환 시 미갱신 | episode metadata 순회 후 `new_info["total_frames"]` 갱신 |
| source==target 가드 없음 | `run_conversion` 초입에 동일 경로·부모-자식 관계 체크 추가 |
