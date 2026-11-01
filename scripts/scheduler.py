import os
import sys
import json
import urllib.request
from datetime import datetime, timezone

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO     = os.environ.get("REPO", "")

SCHEDULE_FILE = "schedule.txt"

if not GH_TOKEN or not REPO:
    print("❌ Missing GH_TOKEN or REPO")
    sys.exit(1)

if not os.path.exists(SCHEDULE_FILE):
    print("⏭️ No schedule.txt found. Nothing to do.")
    sys.exit(0)

raw = open(SCHEDULE_FILE, "r", encoding="utf-8").read().strip()
if not raw:
    print("⏭️ schedule.txt is empty. Nothing to do.")
    sys.exit(0)

try:
    start_at = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
except ValueError:
    print(f"❌ Cannot parse schedule.txt: '{raw}'")
    sys.exit(1)

now = datetime.now(timezone.utc)

if now < start_at:
    mins = (start_at - now).total_seconds() / 60.0
    print(f"⏳ Not yet. {mins:.0f} minutes remaining until {start_at.isoformat()}.")
    sys.exit(0)

print(f"✅ Time reached ({now.isoformat()} >= {start_at.isoformat()}). Triggering stream...")

url = f"https://api.github.com/repos/{REPO}/actions/workflows/stream.yml/dispatches"
data = json.dumps({
    "ref": "main",
    "inputs": {"start_offset": "0"}
}).encode()
req = urllib.request.Request(
    url, data=data,
    headers={
        "Accept": "application/vnd.github+json",
        "Authorization": f"Bearer {GH_TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28",
    },
    method="POST",
)
try:
    with urllib.request.urlopen(req) as r:
        print(f"🚀 Stream workflow triggered ({r.status})")
except Exception as e:
    print(f"❌ Trigger failed: {e}")
    sys.exit(1)

# Clear schedule so the same file doesn't fire again next cron tick
with open(SCHEDULE_FILE, "w", encoding="utf-8") as f:
    f.write("")
print("🧹 schedule.txt cleared.")

# Commit the cleared file back
os.system('git config user.email "actions@github.com"')
os.system('git config user.name "github-actions"')
os.system(f'git add {SCHEDULE_FILE}')
os.system('git commit -m "Clear schedule after stream started" || true')
os.system('git push')