#!/usr/bin/env python3
"""Convert lerobot video dataset to image dataset.

Converts BaboGaeguri/leftarm_v2 (video, mp4) to BaboGaeguri/leftarm_v2_image
(image, PNG) to eliminate video-decode memory leak during training.

Background
----------
Experiment A (TODO-1a-fix) confirmed pyav backend leaks ~1.07 GB/min at the
OS buffer level (libav shmem) — identical to torchcodec's 1.25 GB/min.
Since the leak occurs in the video decode layer itself (not in DataLoader
workers), converting to pre-extracted PNG frames is the only root-level fix.

References (read-only)
----------------------
- lerobot utils.py DEFAULT_IMAGE_PATH   (line 90)  — image path convention
- lerobot utils.py DEFAULT_VIDEO_PATH   (line 89)  — video path convention
- lerobot dataset_tools.py convert_image_to_video_dataset (line 1648) — inverse
- lerobot io_utils.py embed_images      (line 98)  — parquet serialization
- lerobot dataset_metadata.py video_keys / image_keys (line 314/309)

Usage
-----
# Dry-run (no files written):
python convert_to_image.py \\
    --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \\
    --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \\
    --dry-run

# Convert first 10 episodes only (validation run):
python convert_to_image.py \\
    --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \\
    --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \\
    --episodes 0-9 --skip-existing

# Full conversion (all 110 episodes):
python convert_to_image.py \\
    --source-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2 \\
    --target-root ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image \\
    --skip-existing
"""

from __future__ import annotations

import argparse
import copy
import json
import logging
import shutil
import subprocess
import sys
import time
from pathlib import Path

# ---------------------------------------------------------------------------
# Lazy-import heavy deps so --help always works even if env is partial.
# ---------------------------------------------------------------------------
def _import_heavy():
    """Import pandas, pyarrow, datasets, tqdm at call time (not module load)."""
    import datasets as hf_datasets
    import pandas as pd
    import pyarrow as pa
    import pyarrow.parquet as pq
    from tqdm import tqdm
    return hf_datasets, pd, pa, pq, tqdm


def _import_lerobot_embed():
    """Import lerobot embed_images — lazy so --help works without lerobot installed."""
    from lerobot.datasets.io_utils import embed_images
    return embed_images


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants — from lerobot/datasets/utils.py (read-only reference)
# DEFAULT_IMAGE_PATH = "images/{image_key}/episode-{episode_index:06d}/frame-{frame_index:06d}.png"
# DEFAULT_VIDEO_PATH = "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4"
# ---------------------------------------------------------------------------
IMAGE_PATH_PATTERN = "images/{image_key}/episode-{episode_index:06d}/frame-{frame_index:06d}.png"
# Video path in leftarm_v2 follows the default lerobot v3 pattern:
#   videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4
# We also keep the legacy single-file fallback:
#   videos/{video_key}/episode_XXXXXX.mp4  (older recording format)
VIDEO_PATH_CHUNK = "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4"
VIDEO_PATH_LEGACY = "videos/{video_key}/episode_{episode_index:06d}.mp4"

INFO_PATH = "meta/info.json"
DATA_CHUNK_PATTERN = "data/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet"
EPISODES_CHUNK_PATTERN = "meta/episodes/chunk-{chunk_index:03d}/file-{file_index:03d}.parquet"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Convert lerobot video dataset to image dataset (PNG frames).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    p.add_argument(
        "--source-root",
        required=True,
        type=Path,
        help="Root directory of the source video dataset (e.g. ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2)",
    )
    p.add_argument(
        "--target-root",
        required=True,
        type=Path,
        help="Root directory for the new image dataset (e.g. ~/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_image)",
    )
    p.add_argument(
        "--episodes",
        default=None,
        type=str,
        help=(
            "Episode range to convert. Examples: '0-9' (first 10), '100-109' (incremental), "
            "'5' (single). Default: all episodes."
        ),
    )
    p.add_argument(
        "--skip-existing",
        action="store_true",
        help="Skip episodes whose output frame directory already exists. Enables resumable runs.",
    )
    p.add_argument(
        "--codec",
        default="auto",
        choices=["auto", "h264", "libsvtav1", "libx264", "hevc"],
        help=(
            "Hint for source video codec. 'auto' (default) lets ffmpeg probe the file — "
            "no manual codec specification needed. Useful only if ffprobe detection fails."
        ),
    )
    p.add_argument(
        "--image-format",
        default="png",
        choices=["png", "jpg"],
        help="Output image format. PNG = lossless (default, lerobot standard). JPG = smaller.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be done without writing any files.",
    )
    p.add_argument(
        "--fail-fast",
        action="store_true",
        help="Stop immediately on the first episode-level error (default: log and continue).",
    )
    p.add_argument(
        "--loglevel",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Episode range parser
# ---------------------------------------------------------------------------

def parse_episode_range(spec: str, total: int) -> list[int]:
    """Parse '--episodes' string into sorted list of episode indices.

    Examples
    --------
    '0-9'   -> [0,1,...,9]
    '100'   -> [100]
    None    -> [0, 1, ..., total-1]
    """
    if spec is None:
        return list(range(total))
    if "-" in spec:
        parts = spec.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid episode range: '{spec}'. Use 'start-end' (e.g. '0-99').")
        start, end = int(parts[0]), int(parts[1])
        if start > end or start < 0 or end >= total:
            raise ValueError(
                f"Episode range {start}-{end} is out of bounds [0, {total - 1}]."
            )
        return list(range(start, end + 1))
    return [int(spec)]


# ---------------------------------------------------------------------------
# Video path resolution (supports both chunk-file and legacy episode formats)
# ---------------------------------------------------------------------------

def resolve_video_path(
    source_root: Path,
    video_key: str,
    episode_idx: int,
    episode_meta: dict | None,
) -> Path:
    """Find the actual .mp4 file for this episode + video_key.

    Tries in order:
    1. Chunk/file path from episode metadata  (lerobot v3 standard)
    2. Glob for any .mp4 under videos/{video_key}/ whose stem matches episode
    3. Legacy single-file path
    """
    # 1. Metadata-driven chunk path (most reliable)
    if episode_meta is not None:
        chunk_key = f"videos/{video_key}/chunk_index"
        file_key = f"videos/{video_key}/file_index"
        if chunk_key in episode_meta and file_key in episode_meta:
            chunk_idx = int(episode_meta[chunk_key])
            file_idx = int(episode_meta[file_key])
            candidate = source_root / VIDEO_PATH_CHUNK.format(
                video_key=video_key, chunk_index=chunk_idx, file_index=file_idx
            )
            if candidate.exists():
                return candidate

    # 2. Glob — flexible fallback (handles any chunk layout)
    video_dir = source_root / "videos" / video_key
    if video_dir.exists():
        # Try episode-number-in-filename glob
        candidates = sorted(video_dir.rglob(f"*{episode_idx:06d}*.mp4"))
        if candidates:
            return candidates[0]
        # Try file-based: pick first .mp4 that corresponds to episode ordering
        all_mp4 = sorted(video_dir.rglob("*.mp4"))
        if all_mp4 and episode_idx < len(all_mp4):
            return all_mp4[episode_idx]

    # 3. Legacy flat layout
    legacy = source_root / VIDEO_PATH_LEGACY.format(
        video_key=video_key, episode_index=episode_idx
    )
    if legacy.exists():
        return legacy

    raise FileNotFoundError(
        f"Cannot locate video for episode {episode_idx}, key '{video_key}' "
        f"under {source_root / 'videos' / video_key}"
    )


# ---------------------------------------------------------------------------
# ffmpeg frame extraction
# ---------------------------------------------------------------------------

def extract_frames_ffmpeg(
    video_path: Path,
    out_dir: Path,
    image_format: str = "png",
    dry_run: bool = False,
) -> int:
    """Extract all frames from video_path into out_dir using ffmpeg CLI.

    ffmpeg is run in a subprocess — completely isolated from the Python process,
    so libav OS buffers are freed when the subprocess exits. This is the key
    mechanism that eliminates the memory leak seen in pyav/torchcodec.

    Returns number of extracted frames.
    """
    if not dry_run:
        out_dir.mkdir(parents=True, exist_ok=True)

    ext = "png" if image_format == "png" else "jpg"
    out_pattern = str(out_dir / f"frame-%06d.{ext}")

    cmd = [
        "ffmpeg",
        "-i", str(video_path),
        "-start_number", "0",
        "-loglevel", "warning",
    ]
    if image_format == "jpg":
        cmd += ["-q:v", "2"]  # High-quality JPEG (scale 1–31, 2=near-lossless)
    cmd.append(out_pattern)

    log.debug("ffmpeg cmd: %s", " ".join(cmd))

    if dry_run:
        log.info("  [dry-run] would run: %s", " ".join(cmd))
        # Probe frame count without extracting
        return _probe_frame_count(video_path)

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"ffmpeg failed for {video_path}:\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    ext_lower = ext.lower()
    frames = sorted(out_dir.glob(f"frame-*.{ext_lower}"))
    return len(frames)


def _probe_frame_count(video_path: Path) -> int:
    """Use ffprobe to count frames (dry-run only)."""
    cmd = [
        "ffprobe",
        "-v", "error",
        "-select_streams", "v:0",
        "-count_packets",
        "-show_entries", "stream=nb_read_packets",
        "-of", "csv=p=0",
        str(video_path),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not result.stdout.strip():
        return -1  # Unknown in dry-run
    return int(result.stdout.strip())


# ---------------------------------------------------------------------------
# Parquet data file handling
# ---------------------------------------------------------------------------

def find_data_parquet_files(source_root: Path) -> list[Path]:
    """Return sorted list of data parquet files under data/."""
    data_dir = source_root / "data"
    if not data_dir.exists():
        return []
    return sorted(data_dir.rglob("*.parquet"))


def find_episodes_parquet_files(source_root: Path) -> list[Path]:
    """Return sorted list of episode metadata parquet files under meta/episodes/."""
    ep_dir = source_root / "meta" / "episodes"
    if not ep_dir.exists():
        return []
    return sorted(ep_dir.rglob("*.parquet"))


def load_all_episode_metadata(source_root: Path) -> dict[int, dict]:
    """Load all episode metadata rows keyed by episode_index.

    Supports both parquet-based (lerobot v3) and jsonl-based (legacy) formats.
    """
    _, pd, _, pq, _ = _import_heavy()

    ep_dir = source_root / "meta" / "episodes"
    legacy_jsonl = source_root / "meta" / "episodes.jsonl"

    result = {}

    if ep_dir.exists():
        for pq_file in sorted(ep_dir.rglob("*.parquet")):
            df = pd.read_parquet(pq_file)
            for _, row in df.iterrows():
                ep_idx = int(row["episode_index"])
                result[ep_idx] = row.to_dict()
    elif legacy_jsonl.exists():
        import json as _json
        with open(legacy_jsonl) as f:
            for line in f:
                line = line.strip()
                if line:
                    ep = _json.loads(line)
                    result[int(ep["episode_index"])] = ep

    return result


# ---------------------------------------------------------------------------
# info.json transformation
# ---------------------------------------------------------------------------

def transform_info(source_info: dict, video_keys: list[str]) -> dict:
    """Return a copy of info.json with video dtype changed to image.

    - features[key]["dtype"] = "video" -> "image"
    - Removes "video" sub-dict (codec info) from image features
    - Keeps shape (height, width, channels), fps, episode_count, frame_count
    """
    new_info = copy.deepcopy(source_info)
    for key in video_keys:
        if key in new_info.get("features", {}):
            new_info["features"][key]["dtype"] = "image"
            # Remove video-specific codec metadata if present
            new_info["features"][key].pop("info", None)
    return new_info


# ---------------------------------------------------------------------------
# Parquet column transformation (video reference -> image path reference)
# ---------------------------------------------------------------------------

def rewrite_data_parquet(
    src_parquet: Path,
    dst_parquet: Path,
    video_keys: list[str],
    target_root: Path,
    episode_frame_offsets: dict[int, int],  # unused, kept for API compat
    image_format: str = "png",
    dry_run: bool = False,
) -> None:
    """Copy a data parquet file, replacing video columns with embedded image bytes.

    lerobot image datasets require image columns stored as HuggingFace
    datasets.Image() (bytes-embedded) in parquet, so that
    ``Dataset.from_parquet(features=Features({key: Image()}))`` can decode
    them back to PIL images at load time (see io_utils.py:load_nested_dataset,
    io_utils.py:hf_transform_to_torch, feature_utils.py:50-51).

    Strategy (mirrors dataset_writer.py:371-377 and io_utils.py:282-296):
    1. Read source parquet (video columns may be absent — video dtype is skipped
       by get_hf_features_from_features, so source parquet has no video cols).
    2. For each image_key, derive the on-disk PNG path from episode_index and
       frame_index columns using DEFAULT_IMAGE_PATH pattern, and add it as a
       column of file-path strings.
    3. Build HuggingFace Dataset with Image() features for image columns.
    4. Call embed_images() to embed bytes into Arrow table (identical to how
       dataset_writer.py saves image parquet files).
    5. Save to parquet via Dataset.to_parquet().
    """
    hf_datasets, pd, pa, pq, _ = _import_heavy()
    embed_images = _import_lerobot_embed()

    df = pd.read_parquet(src_parquet)

    # Drop any video columns that somehow survived in source parquet.
    cols_to_drop = [k for k in video_keys if k in df.columns]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)

    # Build image path strings and add as columns.
    # Path pattern: images/{image_key}/episode-{episode_index:06d}/frame-{frame_index:06d}.png
    # This matches DEFAULT_IMAGE_PATH in lerobot/datasets/utils.py L90.
    for image_key in video_keys:
        image_paths = [
            str(
                target_root
                / IMAGE_PATH_PATTERN.format(
                    image_key=image_key,
                    episode_index=int(ep_idx),
                    frame_index=int(fr_idx),
                )
            )
            for ep_idx, fr_idx in zip(df["episode_index"], df["frame_index"])
        ]
        df[image_key] = image_paths

    if dry_run:
        return

    dst_parquet.parent.mkdir(parents=True, exist_ok=True)

    # Build HuggingFace Features: Image() for image keys, auto-infer the rest.
    # Pattern from io_utils.py:to_parquet_with_hf_images (L282-296) and
    # dataset_writer.py:_save_episode_data (L374-377).
    image_features = {key: hf_datasets.Image() for key in video_keys}
    hf_features = hf_datasets.Features(image_features)

    data_dict = df.to_dict(orient="list")
    ds = hf_datasets.Dataset.from_dict(data_dict, features=hf_features)

    # embed_images converts PIL/path-encoded image columns to bytes in Arrow
    # table storage before parquet serialization (io_utils.py:98-115).
    ds = embed_images(ds)
    ds.to_parquet(str(dst_parquet))


# ---------------------------------------------------------------------------
# Main conversion logic
# ---------------------------------------------------------------------------

def run_conversion(args: argparse.Namespace) -> int:
    """Main conversion routine. Returns exit code (0=success, 1=partial failure)."""
    hf_datasets, pd, pa, pq, tqdm = _import_heavy()

    source_root = args.source_root.expanduser().resolve()
    target_root = args.target_root.expanduser().resolve()

    # ------------------------------------------------------------------
    # Recommended #2: source/target identity guard — prevent data corruption.
    # ------------------------------------------------------------------
    if source_root == target_root:
        log.error(
            "--source-root and --target-root are the same path (%s). "
            "This would overwrite the source dataset. Exiting.",
            source_root,
        )
        return 1
    if target_root.is_relative_to(source_root) or source_root.is_relative_to(target_root):
        log.error(
            "--source-root and --target-root are in a parent-child relationship "
            "(%s vs %s). Risk of source corruption. Exiting.",
            source_root, target_root,
        )
        return 1

    # ------------------------------------------------------------------
    # 1. Pre-flight checks
    # ------------------------------------------------------------------
    log.info("=== convert_to_image.py ===")
    log.info("Source: %s", source_root)
    log.info("Target: %s", target_root)

    if not source_root.exists():
        log.error("Source root does not exist: %s", source_root)
        return 1

    info_path = source_root / INFO_PATH
    if not info_path.exists():
        log.error("meta/info.json not found at %s", info_path)
        return 1

    # Check ffmpeg available
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path is None:
        log.error(
            "ffmpeg not found in PATH. Install with: conda install -c conda-forge ffmpeg  "
            "or: apt-get install ffmpeg"
        )
        return 1
    log.info("ffmpeg: %s", ffmpeg_path)

    # Load source info.json
    with open(info_path) as f:
        source_info = json.load(f)

    # Identify video feature keys
    features = source_info.get("features", {})
    video_keys = [k for k, ft in features.items() if ft.get("dtype") == "video"]
    if not video_keys:
        log.error("No video features found in %s. Already an image dataset?", info_path)
        return 1

    log.info("Video keys: %s", video_keys)

    total_episodes = source_info.get("total_episodes", 0)
    if total_episodes == 0:
        log.error("total_episodes=0 in info.json — dataset seems empty.")
        return 1

    log.info("Total episodes in source: %d", total_episodes)

    # Parse episode range
    try:
        episode_indices = parse_episode_range(args.episodes, total_episodes)
    except ValueError as e:
        log.error("Invalid --episodes argument: %s", e)
        return 1

    log.info(
        "Episodes to convert: %d  (indices %d .. %d)",
        len(episode_indices), episode_indices[0], episode_indices[-1],
    )

    # Target root guard
    if target_root.exists() and not args.skip_existing and not args.dry_run:
        log.error(
            "Target root already exists: %s\n"
            "Use --skip-existing to resume, or remove it manually.",
            target_root,
        )
        return 1

    if args.dry_run:
        log.info("[DRY-RUN] No files will be written.")

    # Load all episode metadata (for chunk/file lookup)
    ep_metadata = load_all_episode_metadata(source_root)
    log.info("Loaded episode metadata for %d episodes", len(ep_metadata))

    # ------------------------------------------------------------------
    # 2. Frame extraction: episode × camera
    # ------------------------------------------------------------------
    failed_episodes: list[int] = []
    total_frames_extracted = 0
    t_start = time.monotonic()

    for ep_idx in tqdm(episode_indices, desc="Episodes"):
        ep_meta = ep_metadata.get(ep_idx, None)

        for video_key in video_keys:
            # image_key replaces '.' with '/' in the directory name convention.
            # lerobot DEFAULT_IMAGE_PATH uses image_key directly as path segment.
            image_key = video_key  # e.g. "observation.images.top"

            out_dir = target_root / IMAGE_PATH_PATTERN.format(
                image_key=image_key,
                episode_index=ep_idx,
                frame_index=0,
            )
            # out_dir should be the *directory*, strip the filename part
            out_dir = (target_root / "images" / image_key / f"episode-{ep_idx:06d}")

            # Skip-existing check
            if args.skip_existing and out_dir.exists():
                existing_frames = len(list(out_dir.glob(f"frame-*.{args.image_format}")))
                if existing_frames > 0:
                    log.debug(
                        "Skip episode %d key '%s' — %d frames already exist",
                        ep_idx, video_key, existing_frames,
                    )
                    total_frames_extracted += existing_frames
                    continue

            try:
                video_path = resolve_video_path(source_root, video_key, ep_idx, ep_meta)
            except FileNotFoundError as e:
                log.warning("Episode %d key '%s': %s", ep_idx, video_key, e)
                if args.fail_fast:
                    log.error("--fail-fast: aborting.")
                    return 1
                failed_episodes.append(ep_idx)
                continue

            try:
                n_frames = extract_frames_ffmpeg(
                    video_path, out_dir,
                    image_format=args.image_format,
                    dry_run=args.dry_run,
                )
                total_frames_extracted += max(n_frames, 0)
                log.debug("Episode %d key '%s': %d frames", ep_idx, video_key, n_frames)
            except RuntimeError as e:
                log.warning("Episode %d key '%s' extraction failed: %s", ep_idx, video_key, e)
                if args.fail_fast:
                    log.error("--fail-fast: aborting.")
                    return 1
                failed_episodes.append(ep_idx)

    elapsed = time.monotonic() - t_start
    log.info(
        "Frame extraction complete. %d frames in %.1f s  (%.1f fps)",
        total_frames_extracted, elapsed,
        total_frames_extracted / max(elapsed, 0.001),
    )

    if failed_episodes:
        unique_failed = sorted(set(failed_episodes))
        log.warning("Failed episodes: %s", unique_failed)

    # ------------------------------------------------------------------
    # 3. meta/info.json — rewrite with dtype: image
    # ------------------------------------------------------------------
    new_info = transform_info(source_info, video_keys)
    new_info["total_episodes"] = len(episode_indices)

    # Recommended #1: update total_frames for partial conversion.
    # Sum frame counts for the converted episodes from episode metadata.
    # Falls back to total_frames_extracted if metadata is unavailable.
    converted_frame_count = 0
    for ep_idx in episode_indices:
        ep_meta = ep_metadata.get(ep_idx)
        if ep_meta is not None and "length" in ep_meta:
            converted_frame_count += int(ep_meta["length"])
        elif ep_meta is not None and "frame_count" in ep_meta:
            converted_frame_count += int(ep_meta["frame_count"])
        elif ep_meta is not None and "dataset_to_index" in ep_meta and "dataset_from_index" in ep_meta:
            converted_frame_count += int(ep_meta["dataset_to_index"]) - int(ep_meta["dataset_from_index"])
        else:
            # Fallback: use extracted frame count (only valid for single video_key datasets)
            converted_frame_count = total_frames_extracted
            break
    if converted_frame_count > 0:
        new_info["total_frames"] = converted_frame_count

    if not args.dry_run:
        target_root.mkdir(parents=True, exist_ok=True)
        new_info_path = target_root / INFO_PATH
        new_info_path.parent.mkdir(parents=True, exist_ok=True)
        with open(new_info_path, "w") as f:
            json.dump(new_info, f, indent=2)
        log.info("Wrote %s", new_info_path)
    else:
        log.info("[dry-run] Would write meta/info.json with video->image dtype change")
        log.debug("New info sample features: %s", {k: v.get("dtype") for k, v in new_info["features"].items()})

    # ------------------------------------------------------------------
    # 4. Parquet data files — copy without video columns
    # ------------------------------------------------------------------
    data_pq_files = find_data_parquet_files(source_root)
    if data_pq_files:
        log.info("Copying %d data parquet file(s)...", len(data_pq_files))
        for src_pq in data_pq_files:
            rel = src_pq.relative_to(source_root)
            dst_pq = target_root / rel
            rewrite_data_parquet(
                src_pq, dst_pq,
                video_keys=video_keys,
                target_root=target_root,
                episode_frame_offsets={},
                image_format=args.image_format,
                dry_run=args.dry_run,
            )
            log.debug("  %s", rel)
        log.info("Parquet data files done.")
    else:
        log.warning("No data parquet files found under %s/data/", source_root)

    # ------------------------------------------------------------------
    # 5. Episode metadata parquet — copy as-is
    # ------------------------------------------------------------------
    ep_pq_files = find_episodes_parquet_files(source_root)
    if ep_pq_files:
        log.info("Copying %d episode metadata parquet file(s)...", len(ep_pq_files))
        for src_pq in ep_pq_files:
            rel = src_pq.relative_to(source_root)
            dst_pq = target_root / rel
            if not args.dry_run:
                dst_pq.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_pq, dst_pq)
            log.debug("  %s", rel)
    else:
        log.warning("No episode metadata parquet files found under %s/meta/episodes/", source_root)

    # ------------------------------------------------------------------
    # 6. Copy other meta files (tasks.parquet, stats.json, etc.)
    # ------------------------------------------------------------------
    for meta_file in (source_root / "meta").glob("*"):
        if meta_file.name in ("info.json", "episodes"):
            continue  # Already handled
        dst_file = target_root / "meta" / meta_file.name
        if not args.dry_run:
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            if meta_file.is_file():
                shutil.copy2(meta_file, dst_file)
            elif meta_file.is_dir():
                shutil.copytree(meta_file, dst_file, dirs_exist_ok=True)
        log.debug("  Copied meta/%s", meta_file.name)

    # ------------------------------------------------------------------
    # 7. Disk usage report
    # ------------------------------------------------------------------
    if not args.dry_run and target_root.exists():
        result = subprocess.run(
            ["du", "-sh", str(target_root)],
            capture_output=True, text=True,
        )
        if result.returncode == 0:
            log.info("Target dataset size: %s", result.stdout.strip())

    # ------------------------------------------------------------------
    # 8. Quick load test (verify LeRobotDataset can open the result)
    # ------------------------------------------------------------------
    if not args.dry_run:
        log.info("Running quick LeRobotDataset load test...")
        try:
            # Import lerobot — available in DGX venv
            from lerobot.datasets.lerobot_dataset import LeRobotDataset
            ds = LeRobotDataset(
                repo_id="BaboGaeguri/leftarm_v2_image",
                root=target_root,
            )
            log.info(
                "LeRobotDataset load OK — %d episodes, %d frames, image_keys=%s",
                ds.meta.total_episodes, ds.meta.total_frames, ds.meta.image_keys,
            )
        except Exception as e:
            log.warning(
                "LeRobotDataset load test failed (may be OK if partial conversion): %s", e
            )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------
    log.info("=" * 60)
    log.info("CONVERSION SUMMARY")
    log.info("  Source    : %s", source_root)
    log.info("  Target    : %s", target_root)
    log.info("  Episodes  : %d converted (%d requested)", len(episode_indices) - len(set(failed_episodes)), len(episode_indices))
    log.info("  Frames    : %d extracted", total_frames_extracted)
    log.info("  Video keys: %s -> dtype=image", video_keys)
    if failed_episodes:
        log.warning("  FAILED episodes: %s", sorted(set(failed_episodes)))
        return 1

    log.info("Done. Next step: run training with --dataset.repo_id=BaboGaeguri/leftarm_v2_image")
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    logging.getLogger().setLevel(args.loglevel)
    sys.exit(run_conversion(args))


if __name__ == "__main__":
    main()
