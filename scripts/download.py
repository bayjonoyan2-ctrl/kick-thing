import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

video_url = os.environ.get("VIDEO_URL")
start_in_hours = os.environ.get("START_IN_HOURS", "0")

if not video_url:
    print("❌ VIDEO_URL missing")
    sys.exit(1)

# Single priority chain: yt-dlp picks FIRST match, does not download all.
FORMAT = (
    "bv*[height=720][fps>=50]+ba/"
    "b[height=720][fps>=50]/"
    "bv*[height=720]+ba/"
    "b[height=720]/"
    "bv*[height=1080][fps<50]+ba/"
    "b[height=1080][fps<50]/"
    "bv*[height=1080][fps>=50]+ba/"
    "b[height=1080][fps>=50]/"
    "b"
)

print(f"⬇️ Downloading with priority selector:\n{FORMAT}\n")

cmd = [
    "yt-dlp",
    "--cookies", "cookies.txt",
    "--js-runtimes", "deno",
    "--remote-components", "ejs:github",
    "-f", FORMAT,
    "--merge-output-format", "mp4",
    "--no-part",
    "--no-playlist",
    "-o", "video.mp4",
    video_url,
]

res = subprocess.run(cmd)
if res.returncode != 0 or not os.path.exists("video.mp4"):
    print("❌ Download failed.")
    sys.exit(1)

probe = subprocess.run(
    ["ffprobe", "-v", "error", "-select_streams", "v:0",
     "-show_entries", "stream=width,height,r_frame_rate",
     "-of", "default=noprint_wrappers=1", "video.mp4"],
    capture_output=True, text=True
)
print("✅ Final format:\n" + probe.stdout)

# --- Write schedule timestamp for scheduler.py ---
try:
    hours = float(start_in_hours)
except ValueError:
    hours = 0.0

start_at = datetime.now(timezone.utc) + timedelta(hours=hours)
with open("schedule.txt", "w", encoding="utf-8") as f:
    f.write(start_at.strftime("%Y-%m-%dT%H:%M:%SZ"))
print(f"⏰ Stream scheduled to start at: {start_at.isoformat()}")