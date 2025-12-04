# ~/.local/bin/fix_nvr.sh
#!/usr/bin/env bash
set -euo pipefail
shopt -s nullglob nocaseglob

CRF="${CRF:-20}"                 # 18–23 reasonable
IFRAME_SEC="${IFRAME_SEC:-1}"    # I-frame every N seconds

command -v ffmpeg >/dev/null || { echo "ffmpeg not found"; exit 1; }

# Function to process a single video file
process_video_file() {
  local f="$1"
  local out="$2"
  local rel_path="${3:-$(basename "$f")}"
  
  [[ -e "$out" ]] && { echo "skip: $out exists"; return 0; }
  
  echo ">> fixing: $rel_path"
  # Re-encode video only; drop audio; frequent keyframes; repair timestamps
  nice -n 10 ionice -c2 -n7 ffmpeg \
    -nostdin -hide_banner -loglevel error -y \
    -probesize 200M -analyzeduration 200M \
    -fflags +discardcorrupt+genpts \
    -err_detect ignore_err \
    -i "$f" \
    -map 0:v:0 \
    -c:v libx264 -preset fast -crf "$CRF" \
    -force_key_frames "expr:gte(t,n_forced*${IFRAME_SEC})" \
    -pix_fmt yuv420p -movflags +faststart \
    -fps_mode passthrough -an -threads 0 \
    "$out" 2>&1 | grep -v "Enter command:" | grep -v "Queuing commands" >&2 || {
    ffmpeg_exit=${PIPESTATUS[0]}
    if [[ $ffmpeg_exit -ne 0 ]]; then
      echo "  !! encode failed, trying copy-only remux (no audio)"
      ffmpeg -nostdin -hide_banner -loglevel error -y \
        -probesize 200M -analyzeduration 200M \
        -fflags +discardcorrupt+genpts \
        -err_detect ignore_err \
        -i "$f" -map 0:v:0 -c copy -an -movflags +faststart "$out" 2>&1 | grep -v "Enter command:" | grep -v "Queuing commands" >&2 \
        || echo "  !! remux failed: $rel_path"
    fi
  }
}

# Check if first argument is a file or directory
if [[ -n "${1:-}" ]] && [[ -f "$1" ]]; then
  # Process single file
  IN_FILE="$1"
  IN_DIR="$(dirname "$IN_FILE")"
  base="$(basename "$IN_FILE")"
  
  # Output directory: use second arg if provided, otherwise same dir as input
  if [[ -n "${2:-}" ]]; then
    OUT_DIR="$2"
    mkdir -p "$OUT_DIR"
    out="$OUT_DIR/${base%.*}_fixed.mp4"
  else
    OUT_DIR="$IN_DIR"
    out="$OUT_DIR/${base%.*}_fixed.mp4"
  fi
  
  process_video_file "$IN_FILE" "$out" "$(basename "$IN_FILE")"
  echo "Done → $out"
else
  # Process directory (existing behavior)
  IN_DIR="${1:-.}"
  OUT_DIR="${2:-$IN_DIR/fixed}"
  mkdir -p "$OUT_DIR"
  
  # Recursively find all video files
  while IFS= read -r -d '' f; do
    [[ -f "$f" ]] || continue
    
    # Calculate relative path from IN_DIR to preserve directory structure
    rel_path="${f#$IN_DIR/}"
    rel_dir="$(dirname "$rel_path")"
    base="$(basename "$f")"
    
    # Create output directory structure if needed
    if [[ "$rel_dir" != "." ]]; then
      mkdir -p "$OUT_DIR/$rel_dir"
      out="$OUT_DIR/$rel_dir/${base%.*}_fixed.mp4"
    else
      out="$OUT_DIR/${base%.*}_fixed.mp4"
    fi
    
    process_video_file "$f" "$out" "$rel_path"
  done < <(find "$IN_DIR" -type f \( -iname "*.mp4" -o -iname "*.mov" -o -iname "*.mkv" -o -iname "*.avi" -o -iname "*.flv" -o -iname "*.ts" -o -iname "*.264" -o -iname "*.265" -o -iname "*.h264" -o -iname "*.h265" \) -print0)
  
  echo "Done → $OUT_DIR"
fi
