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

print(f"⬇️ Downloading with priority selector...")
cmd = [
    "yt-dlp", "--cookies", "cookies.txt", "--js-runtimes", "deno",
    "--remote-components", "ejs:github", "-f", FORMAT,
    "--merge-output-format", "mp4", "--no-part", "--no-playlist",
    "-o", "raw_video.mp4", video_url,
]

if subprocess.run(cmd).returncode != 0:
    print("❌ Download failed.")
    sys.exit(1)

print("🎨 Rendering QR overlay (this takes a minute)...")

# We use ultrafast and CRF 28 to make rendering as fast as possible
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
    "-c:v", "libx264", "-preset", "ultrafast", "-crf", "28", "-pix_fmt", "yuv420p",
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