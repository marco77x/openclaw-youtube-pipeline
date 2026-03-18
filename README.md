# 🎬 YouTube Pipeline

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/marco77x/openclaw-youtube-pipeline/blob/main/LICENSE)
[![GitHub Stars](https://img.shields.io/github/stars/marco77x/openclaw-youtube-pipeline?style=social)](https://github.com/marco77x/openclaw-youtube-pipeline/stargazers)
[![GitHub Release](https://img.shields.io/github/v/release/marco77x/openclaw-youtube-pipeline)](https://github.com/marco77x/openclaw-youtube-pipeline/releases)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![Built with OpenClaw](https://img.shields.io/badge/built%20with-OpenClaw-purple.svg)](https://github.com/openclaw/openclaw)

A multi-agent automated YouTube content pipeline built with [OpenClaw](https://github.com/openclaw/openclaw). It orchestrates 6 stages — from topic scouting to video publishing — using specialized AI agents.

## Pipeline Stages

```
Scout → Scripter → Avatar/TTS → Metadata → Thumbnail → Publisher
```

| Stage | Agent | Description |
|-------|-------|-------------|
| **Scout** | `scout` | Researches and selects trending topics for the channel |
| **Scripter** | `scripter` | Writes video scripts based on selected topics |
| **Avatar/TTS** | `avatar` | Generates talking-head video with HeyGen avatar + TTS |
| **Metadata** | `metadata` | Creates YouTube titles, descriptions, tags, and chapters |
| **Thumbnail** | `orchestrator` | Generates thumbnail via OpenAI GPT Image API |
| **Publisher** | `publisher` | Uploads video to YouTube and sets thumbnail |

## Architecture

Each stage is an **OpenClaw agent** with its own workspace directory. The **Orchestrator** coordinates the pipeline, managing state transitions and error handling.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## Prerequisites

- Python 3.9+
- [OpenClaw](https://github.com/openclaw/openclaw) installed and configured
- API accounts:
  - **OpenAI** — for thumbnail generation (GPT Image)
  - **HeyGen** — for avatar video generation
  - **Google Cloud** — YouTube Data API v3 + OAuth credentials for upload

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/marco77x/openclaw-youtube-pipeline.git
cd youtube-pipeline
```

### 2. Install dependencies

```bash
pip install google-auth google-auth-oauthlib google-auth-httplib2
```

### 3. Configure environment

```bash
cp .env.example .env
# Edit .env with your API keys
```

### 4. Set up Google OAuth for YouTube upload

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a project (or select existing)
3. Enable **YouTube Data API v3**
4. Create **OAuth 2.0 Client ID** (Desktop app type)
5. Download the JSON and save as `publisher/config/client_secret.json`

### 5. Configure OpenClaw

Add the pipeline agents to your OpenClaw configuration. See the workspace directories for each agent's `AGENTS.md` and `SOUL.md` files as reference.

## Usage

### Run the full pipeline

```bash
# From OpenClaw main session:
"Avvia la pipeline YouTube"
```

The Orchestrator agent will coordinate all stages automatically.

### Run individual stages

Each agent can be triggered independently:

```bash
# Scout: find topics
"Chiedi allo Scout nuovi argomenti"

# Scripter: write script
"Chiedi allo Scripter di scrivere un video su [topic]"

# Publisher: upload video
python publisher/scripts/upload_video.py --video output/video.mp4 --title "My Video"
```

## Project Structure

```
youtube-pipeline/
├── .env.example              # API keys template
├── .gitignore                # Secrets & temp files excluded
├── README.md
├── docs/
│   └── ARCHITECTURE.md       # Detailed architecture docs
├── orchestrator/             # Pipeline coordinator agent
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── scripts/
│       ├── generate_srt.py       # Subtitle generation
│       ├── generate_thumbnail.py # Thumbnail via OpenAI
│       ├── generate_thumbnail_auto.py
│       ├── generate_thumbnail_browser.py
│       └── generate_thumbnail_chatgpt.py
├── scout/                    # Topic research agent
│   ├── AGENTS.md
│   └── SOUL.md
├── scripter/                 # Script writing agent
│   ├── AGENTS.md
│   └── SOUL.md
├── avatar/                   # Avatar video agent
│   ├── AGENTS.md
│   ├── SOUL.md
│   └── skills/heygen_video/
│       ├── SKILL.md
│       └── scripts/gen_heygen_video.py
├── metadata/                 # YouTube metadata agent
│   ├── AGENTS.md
│   └── SOUL.md
└── publisher/                # Upload & publish agent
    ├── AGENTS.md
    ├── SOUL.md
    ├── config/
    │   └── client_secret.json.example  # Google OAuth template
    ├── scripts/
    │   ├── upload_video.py     # Upload to YouTube
    │   ├── publish_video.py    # Change privacy status
    │   └── build_publish_package.py
    └── skills/youtube_upload/
        ├── SKILL.md
        └── scripts/upload_video.py
```

## State Management

Each agent maintains state in its `state/` directory (gitignored). The Orchestrator tracks the overall pipeline state:

```json
{
  "date": "YYYY-MM-DD",
  "pipeline_status": "running",
  "current_stage": "scripting",
  "stages": {
    "scouting": { "status": "completed" },
    "scripting": { "status": "running" },
    "avatar_tts": { "status": "pending" }
  }
}
```

## Security

⚠️ **Never commit API keys, tokens, or credentials.**

- `.env` files are gitignored
- `config/client_secret.json` and `config/token.pickle` are gitignored
- All scripts use environment variables or local config files (not committed)
- Use `.env.example` as a template

## License

MIT — use it, modify it, share it.
