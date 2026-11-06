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
    "-o", "video.mp4", video_url,
]

if subprocess.run(cmd).returncode != 0:
    print("❌ Download failed.")
    sys.exit(1)

# Write schedules
now = datetime.now(timezone.utc)
if float(kick_hours_raw) > 0:
    with open("schedule_kick.txt", "w") as f:
        f.write((now + timedelta(hours=float(kick_hours_raw))).strftime("%Y-%m-%dT%H:%M:%SZ"))
if float(twitch_hours_raw) > 0:
    with open("schedule_twitch.txt", "w") as f:
        f.write((now + timedelta(hours=float(twitch_hours_raw))).strftime("%Y-%m-%dT%H:%M:%SZ"))
print("✅ Download complete.")