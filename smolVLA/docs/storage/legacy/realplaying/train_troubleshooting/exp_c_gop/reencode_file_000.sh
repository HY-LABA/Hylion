#!/usr/bin/env bash
# reencode_file_000.sh — file-000.mp4 (top + wrist) 만 GOP=2 로 재인코딩
#
# 사전: leftarm_v2_gopcheck dataset 사본이 symlink 로 만들어져 있어야 함.
#   cd ~/smolvla/.hf_cache/lerobot/BaboGaeguri
#   cp -as $PWD/leftarm_v2/. $PWD/leftarm_v2_gopcheck/
#
# 본 스크립트:
#   - leftarm_v2_gopcheck/videos/<view>/chunk-000/file-000.mp4 의 symlink 해제
#   - 원본 (readlink) 을 GOP=2 로 재인코딩하여 그 위치에 새 파일 저장
#   - 나머지 mp4 들은 symlink 그대로 (원본 GOP=250 유지)

set -euo pipefail

DATASET_ROOT="${1:-${HOME}/smolvla/.hf_cache/lerobot/BaboGaeguri/leftarm_v2_gopcheck}"

if [[ ! -d "$DATASET_ROOT" ]]; then
    echo "ERROR: dataset 사본 없음 — 먼저 cp -as 로 leftarm_v2_gopcheck 만드세요" >&2
    echo "  cd ~/smolvla/.hf_cache/lerobot/BaboGaeguri" >&2
    echo "  cp -as \$PWD/leftarm_v2/. \$PWD/leftarm_v2_gopcheck/" >&2
    exit 1
fi

log() { echo "[reencode] $*"; }

# 두 카메라 view 의 file-000.mp4 처리
for view in observation.images.top observation.images.wrist; do
    LINK_PATH="${DATASET_ROOT}/videos/${view}/chunk-000/file-000.mp4"

    if [[ ! -L "$LINK_PATH" ]]; then
        log "⚠️ ${LINK_PATH} 가 symlink 아님 — 이미 재인코딩됐거나 사본 구조 이상. 건너뜀."
        continue
    fi

    ORIG=$(readlink -f "$LINK_PATH")
    log "원본: $ORIG"

    # 원본 크기 출력
    SIZE_ORIG=$(stat -c %s "$ORIG")
    log "원본 크기: $(numfmt --to=iec "$SIZE_ORIG")"

    # 임시 출력 → 검증 → symlink 해제 + mv
    TMP_OUT="${LINK_PATH}.gop2.tmp.mp4"
    rm -f "$TMP_OUT"

    log "재인코딩 (libx264, GOP=2, keyint_min=2)..."
    ffmpeg -y -i "$ORIG" \
        -c:v libx264 \
        -g 2 -keyint_min 2 \
        -preset fast -crf 23 \
        -an \
        -loglevel error \
        "$TMP_OUT"

    SIZE_NEW=$(stat -c %s "$TMP_OUT")
    log "재인코딩 후 크기: $(numfmt --to=iec "$SIZE_NEW")"
    log "비율: $(echo "scale=2; $SIZE_NEW * 1.0 / $SIZE_ORIG" | bc)x"

    # GOP 확인 — 첫 10 keyframes 의 frame index 출력 (1, 3, 5, ... 이어야 함)
    log "재인코딩 후 keyframe 간격 확인 (앞 10개):"
    ffprobe -loglevel error -select_streams v -show_frames \
        -show_entries frame=pict_type -of csv "$TMP_OUT" 2>/dev/null \
        | head -50 | awk -F"," '/I/{print NR}' | head -10 | tr '\n' ' '
    echo

    # symlink 해제 + 실파일 이동
    rm "$LINK_PATH"
    mv "$TMP_OUT" "$LINK_PATH"
    log "✅ ${view}: ${LINK_PATH} 갱신 완료"
    echo
done

log "===== 완료 ====="
log "결과 dataset: $DATASET_ROOT"
log "재인코딩된 파일: 2개 (top + wrist 의 file-000.mp4)"
log "나머지 mp4: symlink 유지 (원본 GOP=250)"
log ""
log "다음: ep [0..9] 만 학습 → file-000.mp4 만 디코딩 → GOP=2 효과 측정"
