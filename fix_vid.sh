# ~/.local/bin/fix_nvr.sh
#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob nocaseglob

IN_DIR="${1:-.}"
OUT_DIR="${2:-$IN_DIR/fixed}"
CRF="${CRF:-20}"                 # 18–23 reasonable
IFRAME_SEC="${IFRAME_SEC:-1}"    # I-frame every N seconds

command -v ffmpeg >/dev/null || { echo "ffmpeg not found"; exit 1; }
mkdir -p "$OUT_DIR"

for f in "$IN_DIR"/*.{mp4,mov,mkv,avi,flv,ts,264,265,h264,h265}; do
  [[ -f "$f" ]] || continue
  base="$(basename "$f")"
  out="$OUT_DIR/${base%.*}_fixed.mp4"
  [[ -e "$out" ]] && { echo "skip: $out exists"; continue; }

  echo ">> fixing: $base"
  # Re-encode video only; drop audio; frequent keyframes; repair timestamps
  nice -n 10 ionice -c2 -n7 ffmpeg \
    -hide_banner -loglevel warning -y \
    -probesize 200M -analyzeduration 200M \
    -fflags +discardcorrupt+genpts \
    -err_detect ignore_err \
    -i "$f" \
    -map 0:v:0 \
    -c:v libx264 -preset fast -crf "$CRF" \
    -force_key_frames "expr:gte(t,n_forced*${IFRAME_SEC})" \
    -pix_fmt yuv420p -movflags +faststart \
    -vsync 2 -an -threads 0 \
    "$out" || {
      echo "  !! encode failed, trying copy-only remux (no audio)"
      ffmpeg -hide_banner -loglevel warning -y \
        -probesize 200M -analyzeduration 200M \
        -fflags +discardcorrupt+genpts \
        -err_detect ignore_err \
        -i "$f" -map 0:v:0 -c copy -an -movflags +faststart "$out" \
        || echo "  !! remux failed: $base"
    }
done

echo "Done → $OUT_DIR"
