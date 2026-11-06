import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

video_url = os.environ.get("VIDEO_URL")
kick_hours_raw = os.environ.get("SCHEDULE_KICK_HOURS", "0") or "0"
twitch_hours_raw = os.environ.get("SCHEDULE_TWITCH_HOURS", "0") or "0"

if not video_url:
    print("❌ VIDEO_URL missing")
    sys.exit(1)

# 1. Attempt 720p60
# 2. Attempt 720p30
# 3. Attempt 1080p30
# 4. Attempt 1080p60
# 5. Attempt best available (but explicitly avoid low quality if possible)
FORMAT = (
    "bv*[height=720][fps>=50]+ba/b[height=720][fps>=50]/"
    "bv*[height=720]+ba/b[height=720]/"
    "bv*[height=1080][fps<50]+ba/b[height=1080][fps<50]/"
    "bv*[height=1080][fps>=50]+ba/b[height=1080][fps>=50]/"
    "b"
)

print(f"⬇️ Downloading with priority selector...")
cmd = [
    "yt-dlp", "--cookies", "cookies.txt", "--js-runtimes", "deno",
    "--remote-components", "ejs:github", "-f", FORMAT,
    "--merge-output-format", "mp4", "--no-part", "--no-playlist",
    "-o", "raw_video.mp4", video_url,
]

if subprocess.run(cmd).returncode != 0:
    print("❌ Download failed. YouTube might be blocking the request (403 Error). Try using different cookies.")
    sys.exit(1)

# Check the downloaded video resolution to ensure it's not a forced 360p fallback
probe_cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "default=noprint_wrappers=1:nokey=1", "raw_video.mp4"]
height_out = subprocess.run(probe_cmd, capture_output=True, text=True).stdout.strip()
try:
    h = int(height_out)
    if h < 720:
        print(f"⚠️ WARNING: Downloaded video is only {h}p. YouTube forced a lower quality due to bot protection. The quality will be low.")
except ValueError:
    pass

print("🎨 Rendering QR overlay (this takes a minute)...")

# Use ultrafast, CRF 28, and threads 0 for max CPU speed
filter_complex = (
    "[0:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720[base];"
    "color=c=black@0.4:s=144x92,format=rgba[bg_box];"
    "[base][bg_box]overlay=x=2:y=143[base_with_box];"
    "movie=scripts/qr.png,scale=144:92[qr];"
    "[base_with_box][qr]overlay=x=2:y=143[out]"
)

cmd_render = [
    "ffmpeg", "-y", "-i", "raw_video.mp4",
    "-filter_complex", filter_complex,
    "-map", "[out]", "-map", "0:a",
    "-c:v", "libx264", "-preset", "ultrafast", "-threads", "0", "-crf", "28", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "video.mp4"
]

if subprocess.run(cmd_render).returncode != 0:
    print("❌ Rendering failed.")
    sys.exit(1)

if os.path.exists("raw_video.mp4"):
    os.remove("raw_video.mp4")

print("✅ Video downloaded and QR overlay rendered!")

# --- Write schedule timestamps for both platforms ---
now = datetime.now(timezone.utc)

try:
    kick_hours = float(kick_hours_raw)
except ValueError:
    kick_hours = 0.0

try:
    twitch_hours = float(twitch_hours_raw)
except ValueError:
    twitch_hours = 0.0

if kick_hours > 0:
    kick_at = now + timedelta(hours=kick_hours)
    with open("schedule_kick.txt", "w", encoding="utf-8") as f:
        f.write(kick_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
    print(f"⏰ Kick stream scheduled for: {kick_at.isoformat()}")
else:
    print("⏭️ Kick not scheduled (0 hours).")

if twitch_hours > 0:
    twitch_at = now + timedelta(hours=twitch_hours)
    with open("schedule_twitch.txt", "w", encoding="utf-8") as f:
        f.write(twitch_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
    print(f"⏰ Twitch stream scheduled for: {twitch_at.isoformat()}")
else:
    print("⏭️ Twitch not scheduled (0 hours).")