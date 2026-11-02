import os
import sys
import json
import urllib.request
from datetime import datetime, timezone

GH_TOKEN = os.environ.get("GH_TOKEN", "")
REPO     = os.environ.get("REPO", "")

if not GH_TOKEN or not REPO:
    print("❌ Missing GH_TOKEN or REPO")
    sys.exit(1)

def check_and_trigger(schedule_file, workflow_file, platform_name):
    if not os.path.exists(schedule_file):
        print(f"⏭️ No {schedule_file} found. Skipping {platform_name}.")
        return False

    raw = open(schedule_file, "r", encoding="utf-8").read().strip()
    if not raw:
        print(f"⏭️ {schedule_file} is empty. Skipping {platform_name}.")
        return False

    try:
        start_at = datetime.strptime(raw, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    except ValueError:
        print(f"❌ Cannot parse {schedule_file}: '{raw}'")
        return False

    now = datetime.now(timezone.utc)

    if now < start_at:
        mins = (start_at - now).total_seconds() / 60.0
        print(f"⏳ [{platform_name}] Not yet. {mins:.0f} minutes remaining.")
        return False

    print(f"✅ [{platform_name}] Time reached. Triggering {workflow_file}...")

    url = f"https://api.github.com/repos/{REPO}/actions/workflows/{workflow_file}/dispatches"
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
            print(f"🚀 [{platform_name}] Workflow triggered ({r.status})")
            # Clear schedule so it doesn't fire again
            with open(schedule_file, "w", encoding="utf-8") as f:
                f.write("")
            print(f"🧹 Cleared {schedule_file}.")
            return True
    except Exception as e:
        print(f"❌ [{platform_name}] Trigger failed: {e}")
        return False

kick_triggered   = check_and_trigger("schedule_kick.txt", "stream.yml", "Kick")
twitch_triggered = check_and_trigger("schedule_twitch.txt", "stream_twitch.yml", "Twitch")

if kick_triggered or twitch_triggered:
    print("💾 Committing cleared schedule files...")
    os.system('git config user.email "actions@github.com"')
    os.system('git config user.name "github-actions"')
    os.system('git add schedule_*.txt')
    os.system('git commit -m "Clear schedule after stream started" || true')
    os.system('git push')
else:
    print("🛑 Nothing triggered this cycle.")