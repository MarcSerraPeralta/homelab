#!/usr/bin/env bash
set -euo pipefail

INPUT_DIR="${1:-.}"
SUFFIX="_hevc"

# Video extensions to process
EXTENSIONS=("mp4" "mov" "mkv" "avi" "wmv" "flv" "m4v")

find "$INPUT_DIR" -type f | while read -r FILE; do
    EXT="${FILE##*.}"
    EXT_LOWER=$(echo "$EXT" | tr '[:upper:]' '[:lower:]')

    # Skip non-video files
    if [[ ! " ${EXTENSIONS[*]} " =~ " ${EXT_LOWER} " ]]; then
        continue
    fi

    DIR=$(dirname "$FILE")
    BASE=$(basename "$FILE" ".$EXT")
    OUTFILE="${DIR}/${BASE}${SUFFIX}.mp4"

    # Skip if output already exists
    if [[ -f "$OUTFILE" ]]; then
        echo "Skipping (already transcoded): $FILE"
        continue
    fi

    # Skip if already H.265
    echo $(ffprobe -v error -select_streams v:0 -show_entries stream=codec_name -of default=nw=1:nk=1 "$FILE")
    if ffprobe -v error -select_streams v:0 -show_entries stream=codec_name \
        -of default=nw=1:nk=1 "$FILE" | grep -qi "hevc"; then
        echo "Skipping (already H.265 / HEVC): $FILE"
        continue
    fi

    echo "Transcoding: $FILE → $OUTFILE"

    ffmpeg -hide_banner -loglevel quiet -i "$FILE" \
        -c:v libx265 -preset medium -crf 23 \
        -pix_fmt yuv420p \
        -c:a aac -b:a 192k \
        "$OUTFILE" \
        2>&1 | grep --line-buffered -E "time="
done
