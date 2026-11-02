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

# Single priority chain: yt-dlp picks FIRST match.
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