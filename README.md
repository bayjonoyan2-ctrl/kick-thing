# kick-thing

Download a YouTube video and stream it to Kick, all on GitHub Actions.

## Workflows

1. **Download Video** — paste a YouTube URL. Downloads with priority:
   720p60 → 720p30 → 1080p30 → 1080p60.
2. **Stream to Kick** — pulls the latest downloaded video and streams it.

## Stream behavior

- 720p30 source → streamed as-is (720p30)
- 1080p30, 1080p60, 720p60 → forced to 720p60

## Long videos

Handover at 3h10m; next workflow starts at +3h30m. Works for 24h+ videos
across multiple 6h Actions runs.

## Required secrets

- `YOUTUBE_COOKIES` — cookies.txt contents
- `KICK_STREAM_URL` — from Kick Creator Dashboard
- `KICK_STREAM_KEY` — from Kick Creator Dashboard
- `PAT_FOR_TRIGGER` — GitHub PAT with `workflow` scope (for handover)