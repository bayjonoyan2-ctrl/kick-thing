import os
import subprocess
import sys

video_url = os.environ.get("VIDEO_URL")
if not video_url:
    print("❌ VIDEO_URL missing")
    sys.exit(1)

# Priority: 720p60 -> 720p30 -> 1080p30 -> 1080p60
FORMAT_CHAIN = [
    "bv*[height=720][fps>=50]+ba/b[height=720][fps>=50]",
    "bv*[height=720]+ba/b[height=720]",
    "bv*[height=1080][fps<50]+ba/b[height=1080][fps<50]",
    "bv*[height=1080][fps>=50]+ba/b[height=1080][fps>=50]",
    "b",
]

def try_download(fmt):
    print(f"⬇️ Trying format: {fmt}")
    cmd = [
        "yt-dlp",
        "--cookies", "cookies.txt",
        "--js-runtimes", "deno",
        "--remote-components", "ejs:github",
        "-f", fmt,
        "--merge-output-format", "mp4",
        "-o", "video.mp4",
        video_url,
    ]
    return subprocess.run(cmd).returncode == 0

for fmt in FORMAT_CHAIN:
    if try_download(fmt):
        if os.path.exists("video.mp4"):
            print(f"✅ Downloaded with format: {fmt}")
            sys.exit(0)

print("❌ All format attempts failed.")
sys.exit(1)