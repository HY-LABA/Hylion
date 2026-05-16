# TODO-02 — Code Test

> 작성: 2026-05-16 | code-tester | cycle: 2

## Verdict

**`READY_TO_SHIP`**

Critical 0건. Recommended 1건 (minor, non-blocking).

---

## 단위 테스트 결과

```
AST:    python3 -c "import ast; ast.parse(open('dgx/finetune/leftarm_v2/convert_to_image.py').read()); print('AST OK')"
        -> AST OK (통과)

--help: python3 dgx/finetune/leftarm_v2/convert_to_image.py --help
        -> 정상 출력 (통과). lerobot import 없이 동작 — lazy import 유지 확인.

cycle 1 통과 항목 회귀 없음:
  - ffmpeg subprocess 격리 패턴 유지
  - IMAGE_PATH_PATTERN 상수 일치
  - --skip-existing / --episodes 구현 유지
  - du -sh target_root 디스크 사용량 보고 유지
```

---

## Lint·Type 결과

```
ruff check dgx/finetune/leftarm_v2/convert_to_image.py
-> All checks passed!

mypy: 미실행 (lerobot 코드 스타일상 strict mypy 미적용 영역)
```

---

## DOD 정합성

| DOD 항목 | 충족 | 메모 |
|---|---|---|
| (a) `convert_to_image.py` 신규 작성 | ✅ | 794줄 |
| (a) 원본 무손상 (source_root 에 write 없음) | ✅ | 코드 추적: source_root 에 mkdir/write 호출 0건 |
| (a) lerobot 형식 정확 (DEFAULT_IMAGE_PATH 준수) | ✅ | IMAGE_PATH_PATTERN 상수 일치. parquet image 컬럼 embed 포함 (Critical #1 수정 확인) |
| (a) video leak 회피 (ffmpeg subprocess 격리) | ✅ | subprocess.run + capture_output=True. pyav 미사용. |
| (a) resumable (--skip-existing) | ✅ | out_dir.exists() + frame 수 확인 후 skip |
| (a) incremental (--episodes 0-9, 100-109, 5) | ✅ | parse_episode_range 구현 — range/single 모두 파싱 |
| (b) DGX 실행 (원본→신규 110ep 전체) | 미해당 | prod-test-runner 역할 |
| (c) 디스크 사용량 측정·기록 | ✅ | `du -sh target_root` (subprocess, L737) |
| 테스트: LeRobotDataset 로드 가능 | ✅ | `rewrite_data_parquet` 에서 Image() schema + embed_images() + to_parquet() 적용. 추가로 L748-763 에 LeRobotDataset 로드 자동 검증 코드 포함 (예외 시 warning — 부분 변환 대비). |
| Coupled Rule §6: 구조 변경 시 README 갱신 | ✅ | cycle 1 에서 확인 완료. 추가 변경 없음. |

---

## Critical #1 수정 확인 (cycle 1 MAJOR_REVISIONS 사유)

### rewrite_data_parquet — image 컬럼 embed 패턴 검증

수정 후 `rewrite_data_parquet` (L396-468) 의 핵심 경로:

1. `df[image_key] = image_paths` — episode_index + frame_index 기반 PNG 경로 문자열 컬럼 추가 (L437-449). `IMAGE_PATH_PATTERN` 상수 직접 사용.
2. `image_features = {key: hf_datasets.Image() for key in video_keys}` — Image() 스키마 정의 (L459).
3. `hf_features = hf_datasets.Features(image_features)` — image key 만 포함하는 Features (나머지 컬럼은 자동 추론). `Dataset.from_dict` 의 features 는 전체 스키마를 강제하지 않고 지정 컬럼만 override — 동작 정상.
4. `ds = hf_datasets.Dataset.from_dict(data_dict, features=hf_features)` — HF Dataset 생성 (L463). Image() feature 지정 → 경로 문자열을 PIL 이미지로 자동 디코딩.
5. `ds = embed_images(ds)` — lerobot io_utils.py:98-115 패턴 그대로 (L467). PIL 이미지를 Arrow bytes로 embed.
6. `ds.to_parquet(str(dst_parquet))` — bytes-embedded parquet 저장 (L468).

레퍼런스 일치 확인:
- `dataset_writer.py:374-377` 패턴 (`Dataset.from_dict(features=get_hf_features_from_features)` + `embed_images()`) 과 동일 흐름.
- `io_utils.py:282-296` 의 `to_parquet_with_hf_images` 는 embed_images 미호출이지만, `_save_episode_data` 는 embed_images 호출. 본 코드는 _save_episode_data 패턴을 따름 — 올바름.
- `_import_lerobot_embed()` lazy import 헬퍼로 `--help` 시 lerobot 없이도 동작 유지 (L68-71).

실행 순서 정합:
- Step 2 (ffmpeg frame extraction, L581-638) 가 먼저 PNG 생성
- Step 4 (`rewrite_data_parquet` 호출, L683-698) 에서 PNG 경로가 실제 존재하는 상태에서 embed_images 실행
- 순서 문제 없음.

**Critical #1: 해결 확인.**

---

## Recommended 수정 확인

### Recommended #1 — total_frames 갱신 (cycle 1)

L653-667 에서 episode metadata 순회 후 frame count 합산:
- 우선순위: `length` → `frame_count` → `dataset_to_index - dataset_from_index` → fallback (total_frames_extracted, break)
- `if converted_frame_count > 0: new_info["total_frames"] = converted_frame_count` (L666-667)

합리적 우선순위. fallback (break) 처리도 단일 video_key 데이터셋 한정으로 명시됨. **해결 확인.**

### Recommended #2 — source==target 가드 (cycle 1)

L485-498:
- `source_root == target_root` 동일 경로 체크 + `log.error` + `return 1`
- `target_root.is_relative_to(source_root)` 또는 `source_root.is_relative_to(target_root)` 부모-자식 관계 체크
- 양쪽 방향 모두 확인. **해결 확인.**

---

## Recommended 개선 사항 (신규)

| # | 위치 | 권장 |
|---|---|---|
| 1 | `rewrite_data_parquet` L399-401 | `episode_frame_offsets: dict[int, int]` 인자가 "unused, kept for API compat" 주석으로 남아 있음. 실제 미사용 인자를 시그니처에 유지하는 것은 코드 스타일상 minor 이슈. 제거 또는 `_` 표기 권장. non-blocking. |

Recommended 1건 → 2건 이하 → **READY_TO_SHIP** 기준 충족.

---

## CLAUDE.md 준수 체크

| Category | 체크 | 메모 |
|---|---|---|
| A (절대 금지 영역) | ✅ | `docs/reference/lerobot/` 미변경 (read-only 참조만). `.claude/` 미변경. |
| B (자동 재시도 X) | ✅ | `orin/lerobot/`, `orin/pyproject.toml`, `setup_env.sh`, `deploy_*.sh` 미변경. |
| C (사용자 동의 필수) | ✅ | 새 디렉터리 생성 없음. 의존성 추가 없음 (기존 lerobot 환경 활용). |
| D (절대 금지 명령) | ✅ | `rm -rf`, `sudo`, `chmod 777`, `curl|bash` 코드 내 없음. |
| Coupled File Rule §6 | ✅ | 구조 변경 없음 (신규 파일은 cycle 1 에서 README 갱신 완료). |
| 옛 룰 (docs/storage 예시 추가 X) | ✅ | docs/storage 미변경. |

---

## 배포 권장

- **yes** — READY_TO_SHIP. prod-test-runner 진입 권장.
- Critical 0건. cycle 1 의 MAJOR_REVISIONS 사유 (parquet image 컬럼 미포함) 가 올바른 lerobot 패턴으로 수정됨.
- Recommended #1 (unused parameter) 은 non-blocking. prod-test 후 필요 시 즉석 수정 가능.
