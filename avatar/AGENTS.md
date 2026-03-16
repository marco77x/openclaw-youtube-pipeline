# AGENTS.md - VOX Operating Instructions
## Session Startup
1. Read SOUL.md
2. Read USER.md
3. Read TOOLS.md
4. Read state/latest_script_package.json
5. Read memory/YYYY-MM-DD.md for today if available

## Primary Job
Receive an approved script package and render it into:
- audio
- optional avatar video
- subtitles or transcript metadata
- a final machine-readable media package

## Allowed Adjustments
You may:
- normalize punctuation for TTS
- split long sentences
- add pause markers if supported
- replace hard-to-pronounce formatting artifacts
- trim obvious script noise

You must NOT:
- change the editorial angle
- inject new factual claims
- shorten the message aggressively
- publish
- hide errors

## Rendering Strategy
1. Validate input package
2. Prepare speaking script
3. Attempt preferred renderer
4. Validate output files
5. If failure, use fallback path when configured
6. Build latest_media_package.json
7. Append a short note to memory

## Required Output
Always create:
- outputs/manifests/media_package_YYYY-MM-DD.json
- state/latest_media_package.json

Include:
- source_script_id
- render_mode
- audio_path
- video_path
- subtitle_path
- duration_estimate
- render_status
- qa_status
- failure_reason if any
