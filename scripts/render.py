import subprocess
import sys

print("🎨 Rendering QR overlay...")
filter_complex = (
    "[0:v]scale=1280:720:force_original_aspect_ratio=increase,crop=1280:720[base];"
    "color=c=black@0.4:s=144x92,format=rgba[bg_box];"
    "[base][bg_box]overlay=x=2:y=143[base_with_box];"
    "movie=scripts/qr.png,scale=144:92[qr];"
    "[base_with_box][qr]overlay=x=2:y=143[out]"
)

cmd_render = [
    "ffmpeg", "-y", "-i", "video.mp4",
    "-filter_complex", filter_complex,
    "-map", "[out]", "-map", "0:a",
    "-c:v", "libx264", "-preset", "ultrafast", "-threads", "0", "-crf", "28", "-pix_fmt", "yuv420p",
    "-c:a", "copy", "-shortest", "rendered.mp4"
]

if subprocess.run(cmd_render).returncode != 0:
    print("❌ Rendering failed.")
    sys.exit(1)
print("✅ Rendering complete!")