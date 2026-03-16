# 🏗️ YouTube Pipeline Architecture

## Overview

The YouTube Pipeline is a multi-agent system built on [OpenClaw](https://github.com/openclaw/openclaw) that automates the full content creation workflow for YouTube channels. Each stage of the pipeline is handled by a specialized agent with its own workspace, instructions, and skills.

## Pipeline Flow

```
┌─────────┐    ┌──────────┐    ┌─────────────┐    ┌──────────┐    ┌────────────┐    ┌───────────┐
│  Scout  │───▶│ Scripter │───▶│ Avatar/TTS  │───▶│ Metadata │───▶│ Thumbnail  │───▶│ Publisher │
└─────────┘    └──────────┘    └─────────────┘    └──────────┘    └────────────┘    └───────────┘
```
```

Each stage is coordinated by the **Orchestrator** agent, which manages state transitions, error handling, and reporting.

## Agents

### 1. Scout 🔍
**Workspace:** `scout/`
**Purpose:** Research and select trending topics for the channel.

- Uses Perplexity/web search to find trending tech topics
- Filters based on channel niche (AI, tech, gaming, coding)
- Outputs `latest_topics.json` with ranked topic suggestions
- Configurable search depth and topic count

### 2. Scripter ✍️
**Workspace:** `scripter/`
**Purpose:** Write engaging video scripts from selected topics.

- Receives topic from Scout output
- Generates structured scripts with intro, body, and CTA
- Optimized for spoken delivery (conversational tone)
- Includes timing hints for video editing
- Outputs `latest_script.json`

### 3. Avatar/TTS 🎭
**Workspace:** `avatar/`
**Purpose:** Generate talking-head video using HeyGen avatar + voice.

- Uses HeyGen API for avatar lip-sync
- Supports custom avatar and voice IDs
- Produces MP4 video ready for YouTube
- Italian voice support (Savvy Stefano)
- Outputs `latest_video.json`

### 4. Metadata 📋
**Workspace:** `metadata/`
**Purpose:** Create optimized YouTube metadata.

- Generates SEO-optimized titles
- Writes descriptions with timestamps
- Creates relevant tags
- Adds chapter markers
- Optimizes for YouTube algorithm
- Outputs `latest_metadata.json`

### 5. Thumbnail Generator 🎨
**Workspace:** `orchestrator/` (runs as part of Orchestrator)
**Purpose:** Generate eye-catching YouTube thumbnails.

- Uses OpenAI GPT Image API (gpt-image-1.5)
- Tech-focused design template (dark navy, neon glow)
- Customizable title and subtitle text
- 1536x1024 resolution
- Outputs `thumbnail.png`

### 6. Publisher 📤
**Workspace:** `publisher/`
**Purpose:** Upload and publish videos to YouTube.

- OAuth 2.0 authentication with Google
- Resumable upload via curl (handles large files)
- Automatic thumbnail setting
- Privacy status management (private → public)
- Upload logging and state tracking

### 7. Orchestrator 🎯
**Workspace:** `orchestrator/`
**Purpose:** Coordinate the entire pipeline.

- Manages pipeline state machine
- Validates outputs between stages
- Handles failures gracefully
- Generates reports
- Can trigger individual stages or full pipeline

## State Machine

```
                ┌──────────────────────────────┐
                │                              │
                ▼                              │
         ┌─────────────┐                      │
    ┌────│  SCOUTING   │──────┐               │
    │    └─────────────┘      │               │
    │         │ failed        │               │
    │         ▼               ▼               │
    │    ┌─────────┐    ┌───────────┐         │
    │    │ BLOCKED │    │ SCRIPTING │         │
    │    └─────────┘    └─────┬─────┘         │
    │         ▲               │ failed        │
    │         │               ▼               │
    │         │         ┌─────────┐           │
    │         │         │ BLOCKED │           │
    │         │         └─────────┘           │
    │         │               │               │
    │         │               ▼               │
    │         │      ┌──────────────┐         │
    │         │      │  AVATAR/TTS  │         │
    │         │      └──────┬───────┘         │
    │         │             │                 │
    │         │             ▼                 │
    │         │      ┌────────────┐           │
    │         │      │  METADATA  │           │
    │         │      └─────┬──────┘           │
    │         │            │                  │
    │         │            ▼                  │
    │         │      ┌────────────┐           │
    │         │      │ THUMBNAIL  │           │
    │         │      └─────┬──────┘           │
    │         │            │                  │
    │         │            ▼                  │
    │         │      ┌────────────┐           │
    └─────────┴──────│ PUBLISHING │───────────┘
                     └─────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │  COMPLETED  │
                    └─────────────┘
```

## Inter-Agent Communication

Agents communicate through shared files in their `outputs/` directories:

| From | To | File | Content |
|------|----|------|---------|
| Scout | Scripter | `latest_topics.json` | Ranked topics |
| Scripter | Avatar | `latest_script.json` | Video script |
| Avatar | Metadata | `latest_video.json` | Video file info |
| Metadata | Orchestrator | `latest_metadata.json` | YouTube metadata |
| Orchestrator | Publisher | `thumbnail.png` | Generated thumbnail |

The Orchestrator reads state files from all agents and orchestrates the flow.

## Error Handling

Each stage includes validation:

1. **Pre-flight checks** — Verify required input files exist
2. **Execution monitoring** — Track API calls and responses
3. **Output validation** — Confirm expected files are generated
4. **State tracking** — Record status, timing, and errors
5. **Failure isolation** — Failed stages don't corrupt downstream state

If a stage fails:
- Downstream stages are marked `blocked`
- Error details are logged to `state/latest_report.json`
- A markdown report is generated in `outputs/`
- The pipeline can be resumed from the failed stage

## Security Model

All sensitive data is isolated from the git repository:

| Data | Location | Gitignored |
|------|----------|------------|
| API Keys | `.env` | ✅ |
| Google OAuth Secret | `config/client_secret.json` | ✅ |
| OAuth Token | `config/token.pickle` | ✅ |
| Pipeline State | `state/` | ✅ |
| Generated Content | `outputs/` | ✅ |
| Agent Memory | `memory/` | ✅ |

Scripts reference environment variables or local config files — no hardcoded secrets.

## Adding a New Stage

To add a new stage to the pipeline:

1. Create a new workspace directory: `workspace-name/`
2. Add `AGENTS.md` with operating instructions
3. Add `SOUL.md` with agent personality
4. Create output files that the next stage expects
5. Register the stage in `orchestrator/AGENTS.md`
6. Update the state machine in the Orchestrator
7. Add file transfer contract in this document

## Configuration

### OpenClaw Agent Configuration

Each agent is registered in `openclaw.json`:

```json
{
  "agents": {
    "youtube-scout": {
      "workspace": "~/.openclaw/workspace-scout",
      "model": "openrouter/healer-alpha"
    },
    "youtube-scripter": {
      "workspace": "~/.openclaw/workspace-scripter",
      "model": "openrouter/healer-alpha"
    }
    // ... etc
  }
}
```

### Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `OPENAI_API_KEY` | Yes | Thumbnail generation |
| `HEYGEN_API_KEY` | Yes | Avatar video generation |
| `OPENROUTER_API_KEY` | No | Alternative LLM provider |

## Performance

Typical pipeline timing (approximate):

| Stage | Duration |
|-------|----------|
| Scout | 2-5 min |
| Scripter | 3-8 min |
| Avatar/TTS | 5-15 min |
| Metadata | 1-3 min |
| Thumbnail | 1-2 min |
| Publisher | 3-10 min (depends on video size) |
| **Total** | **15-45 min** |

## Troubleshooting

### "Client secret not found"
→ Download OAuth credentials from Google Cloud Console and save as `publisher/config/client_secret.json`

### "OPENAI_API_KEY not set"
→ Add your key to `.env` file: `OPENAI_API_KEY=sk-...`

### "HEYGEN_API_KEY not set"
→ Add your key to `.env` file: `HEYGEN_API_KEY=...`

### Upload fails with HTTP 401
→ Token expired. Delete `config/token.pickle` and re-authenticate by running upload again.
