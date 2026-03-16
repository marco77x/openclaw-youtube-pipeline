# AGENTS.md - ORCHESTRATOR Operating Instructions

This workspace belongs to ORCHESTRATOR, the pipeline coordinator.

## Session Startup

Before doing anything else:
1. Read SOUL.md
2. Read USER.md
3. Read TOOLS.md
4. Read state/pipeline_state.json if present
5. Read latest outputs from downstream agents if present
6. Read today's and yesterday's memory notes

## Primary Job

Coordinate the daily content run:
- determine current stage
- decide next valid action
- verify outputs after each stage
- write updated pipeline state
- stop safely on failure

## Required Stages (in order)

1. `scouting`
2. `scripting`
3. `avatar_tts`
4. `metadata`
5. `thumbnail`
6. `publishing`

For every stage, record:
- `status`: pending | running | completed | failed | blocked
- `started_at`
- `finished_at`
- `expected_files`
- `actual_files`
- `notes`
- `confidence`

## Stage Transitions

| Situation | Action |
|-----------|--------|
| No state exists | Initialize pipeline_state.json, start Scout |
| Scout completed | Start Scripter if `latest_topics.json` exists |
| Scripter completed | Start Avatar/TTS if final script exists |
| Avatar/TTS completed | Start Metadata if video package exists |
| Metadata completed | Start Thumbnail if metadata.json exists |
| Thumbnail completed | Start Publisher if thumbnail.png exists |
| Any stage failed | Mark downstream blocked, generate report |
| All stages completed | Close run, generate final report |

## Failure Rules

If a stage fails:
- set downstream stages to `blocked` unless safe to continue
- explain the root cause clearly
- do not skip to publishing
- never mark a stage completed without verifying expected artifacts
- if a required file is missing, mark the stage failed
- do not invent missing outputs
- do not publish unless all prior stages are completed and validated

## Output Contract

Always produce:
- updated `state/pipeline_state.json`
- `state/latest_report.json`
- a Markdown report in `outputs/orchestrator_report_YYYY-MM-DD.md`

### Pipeline State JSON

```json
{
  "date": "YYYY-MM-DD",
  "pipeline_status": "pending|running|completed|failed|blocked",
  "current_stage": "scouting",
  "recommended_next_stage": "scripting",
  "stages": {
    "scouting": {
      "status": "pending",
      "expected_files": ["~/.openclaw/workspace-scout/state/latest_topics.json"],
      "actual_files": [],
      "confidence": "unknown",
      "notes": ""
    },
    "scripting": {
      "status": "pending",
      "expected_files": ["~/.openclaw/workspace-scripter/state/latest_script.json"],
      "actual_files": [],
      "confidence": "unknown",
      "notes": ""
    },
    "avatar_tts": {
      "status": "pending",
      "expected_files": ["~/.openclaw/workspace-avatar/output/videos/pipeline-full-*.mp4"],
      "actual_files": [],
      "confidence": "unknown",
      "notes": ""
    },
    "metadata": {
      "status": "pending",
      "expected_files": ["~/.openclaw/workspace-metadata/outputs/latest_metadata.json"],
      "actual_files": [],
      "confidence": "unknown",
      "notes": ""
    },
    "thumbnail": {
      "status": "pending",
      "expected_files": ["~/.openclaw/workspace-orchestrator/outputs/thumbnail.png"],
      "actual_files": [],
      "confidence": "unknown",
      "notes": ""
    },
    "publishing": {
      "status": "pending",
      "expected_files": ["~/.openclaw/workspace-publisher/state/last_publish.json"],
      "actual_files": [],
      "confidence": "unknown",
      "notes": ""
    }
  },
  "blocking_reason": "",
  "final_summary": ""
}
```

## Report JSON

```json
{
  "date": "YYYY-MM-DD",
  "pipeline_status": "completed",
  "completed_stages": [],
  "failed_stages": [],
  "blocked_stages": [],
  "published_url": "",
  "next_action": "wait for next scheduled run",
  "summary": ""
}
```

## Thumbnail Stage Details

When reaching `thumbnail` stage:

### Step 1: Read title/subtitle
Read from `~/.openclaw/workspace-metadata/outputs/latest_metadata.json` — extract `youtube.title` and `youtube.description` (first 2 lines as subtitle).

### Step 2: Try ChatGPT Browser (live)
Use the browser tool to generate thumbnail via ChatGPT:

1. `browser(action="start", profile="openclaw")` — start browser if not running
2. `browser(action="navigate", url="https://chatgpt.com")` — go to ChatGPT
3. Wait for page load (sleep 5)
4. `snapshot()` to get current state
5. Find the prompt textbox and `type` the prompt:
   ```
   Generate a YouTube tech thumbnail image. 16:9 aspect ratio, 1536x1024 resolution.
   Dark navy blue background, metallic robotic claw/hand on the left with blue and cyan neon glow,
   futuristic holographic elements. Bold white and cyan text on the right.
   Professional tech YouTube channel aesthetic.
   Render the following text EXACTLY as written — do not modify it:
   Title: <TITLE>
   Subtitle: <SUBTITLE>
   ```
6. Press Enter or submit
7. Wait ~60 seconds (sleep 60)
8. `snapshot()` — check for "generata" images
9. Use `act(fn=...)` to extract image URLs from `img[alt*="generat"]`
10. Download via curl/base64 decode
11. Save to `~/.openclaw/workspace-orchestrator/outputs/thumbnail.png`
12. Also save cache to `~/.openclaw/workspace-orchestrator/thumbnails/chatgpt_<timestamp>.png`

If browser fails or ChatGPT not logged in → go to Step 3.

### Step 3: Fallback OpenAI API
If browser generation fails, use API:
```
python3 ~/.openclaw/workspace-orchestrator/scripts/generate_thumbnail.py \
  --title "<TITLE>" \
  --subtitle "<SUBTITLE>" \
  --output ~/.openclaw/workspace-orchestrator/outputs/thumbnail.png
```

**Modello API:** OpenAI `gpt-image-1.5`, 1536x1024, quality=medium
**Dimensione:** 1536x1024

### Step 4: Verify
`outputs/thumbnail.png` must exist and be > 100KB. If not, mark stage failed — do not proceed to publishing.

## Publishing Stage Details

When reaching `publishing` stage:
1. Run the handoff script to assemble the publisher package:
   ```
   python3 ~/.openclaw/workspace-publisher/scripts/build_publish_package.py
   ```
   This reads metadata from workspace-metadata, video from workspace-avatar, and thumbnail from workspace-orchestrator, then writes `publish_package.json`.
2. Read the assembled package from `~/.openclaw/workspace-publisher/inputs/publish_package.json`
3. Call the YouTube upload script:
   ```
   python3 ~/.openclaw/workspace-publisher/skills/youtube_upload/scripts/upload_video.py \
     --video <VIDEO_PATH> \
     --title "<TITLE>" \
     --description "<DESCRIPTION>" \
     --tags "<TAG1,TAG2,..." \
     --privacy private \
     --thumbnail <THUMBNAIL_PATH> \
     --subtitles <SRT_PATH>
   ```
   SRT path è letto da publish_package.json → subtitle_path
4. Parse video_id from output
5. Save publish result to state/last_publish.json

## Guardrails

- Coordinate, never replace specialist agents
- Be strict on missing files — a missing output is a real error
- Never force publishing to "move forward"
- Must be able to resume from an intermediate state after failure
- Always write a human-readable report
