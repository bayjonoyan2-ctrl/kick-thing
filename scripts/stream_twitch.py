import os
import subprocess
import sys
import time
import re
import urllib.request
import json

INPUT_FILE = "video.mp4"
STREAM_URL = "rtmp://ingest.global-contribute.live-video.net/app"
STREAM_KEY = os.environ.get("TWITCH_STREAM_KEY", "")
GH_TOKEN   = os.environ.get("GH_TOKEN", "")
REPO       = os.environ.get("REPO", "")

if not STREAM_KEY: sys.exit(1)
RTMP_URL = f"{STREAM_URL}/{STREAM_KEY}"

TRIGGER_AT_SECONDS = (3 * 3600) - (30 * 60) 
HANDOVER_AT_SECONDS = (3 * 3600) + (5 * 60) 

def get_duration(path):
    cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try: return float(r.stdout.strip())
    except: return 0.0

def get_fps(path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "default=noprint_wrappers=1:nokey=1", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try:
        num, den = r.stdout.strip().split("/")
        return float(num) / float(den)
    except: return 30.0

def get_height(path):
    cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=height", "-of", "default=noprint_wrappers=1:nokey=1", path]
    r = subprocess.run(cmd, capture_output=True, text=True)
    try: return int(r.stdout.strip())
    except: return 720

def build_vf(path):
    h = get_height(path)
    fps = get_fps(path)
    if h == 720 and fps < 50: 
        base = "scale=1280:720,fps=30,format=yuv420p"
    else: 
        base = "scale=1280:720,fps=60,format=yuv420p"
    
    vf_filter = (
        f"{base}[base];"
        "color=c=black@0.4:s=144x92,format=rgba[bg_box];"
        "[base][bg_box]overlay=x=2:y=143[base_with_box];"
        "movie=scripts/qr.png,scale=144:92[qr];"
        "[base_with_box][qr]overlay=x=2:y=143[out]"
    )
    return vf_filter, (30 if "fps=30" in base else 60)

def trigger_next(start_offset):
    print(f"\n🚀 Triggering next Twitch stream from {start_offset:.0f}s ...")
    url = f"https://api.github.com/repos/{REPO}/actions/workflows/stream_twitch.yml/dispatches"
    headers = {"Accept": "application/vnd.github+json", "Authorization": f"Bearer {GH_TOKEN}", "X-GitHub-Api-Version": "2022-11-28"}
    data = json.dumps({"ref": "main", "inputs": {"start_offset": str(int(start_offset))}}).encode()
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req) as r: print(f"✅ Next workflow triggered ({r.status})")
    except Exception as e: print(f"❌ Trigger failed: {e}")

def stream():
    total = get_duration(INPUT_FILE)
    if total <= 0: return

    seek = float(os.environ.get("START_OFFSET", "0.0") or "0.0")
    vf_complex, fps = build_vf(INPUT_FILE)
    
    while seek < total:
        remaining = total - seek
        max_run = min(HANDOVER_AT_SECONDS, remaining)
        print(f"\n▶️ Streaming to Twitch from {seek:.1f}s for max {max_run:.1f}s")

        cmd = [
            "ffmpeg", "-re", "-ss", f"{seek}", "-i", INPUT_FILE, "-t", f"{max_run}",
            "-filter_complex", vf_complex, "-map", "[out]", "-map", "0:a",
            "-c:v", "libx264", "-preset", "ultrafast", "-tune", "zerolatency",
            "-b:v", "4500k", "-maxrate", "4500k", "-bufsize", "9000k", "-g", str(fps * 2),
            "-c:a", "aac", "-b:a", "160k", "-ar", "48000", "-f", "flv", RTMP_URL
        ]
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        start_t = time.time()
        last_t = 0.0
        stall = 0
        triggered = False

        for line in proc.stdout:
            if "time=" in line: sys.stdout.write(line); sys.stdout.flush()
            m = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
            if m:
                hh, mm, ss = m.groups()
                cur = int(hh) * 3600 + int(mm) * 60 + float(ss)
                if cur > last_t: last_t = cur; stall = 0
                else: stall += 1
                if not triggered and cur >= TRIGGER_AT_SECONDS and remaining > max_run:
                    triggered = True
                    trigger_next(seek + TRIGGER_AT_SECONDS)
            if stall > 300: break

        if proc.poll() is None: proc.kill()
        played = last_t if last_t > 0 else (time.time() - start_t)

        if triggered:
            print(f"⏹️ Handover at {seek + played:.1f}s")
            break

        seek += max(1.0, played - 2.0)
        if seek >= total - 5: break
        time.sleep(3)

if __name__ == "__main__":
    start_off = float(os.environ.get("START_OFFSET", "0.0") or "0.0")
    if start_off > 0:
        print("⏳ Handover detected. Waiting 30 minutes for overlap...")
        time.sleep(30 * 60)
    stream()