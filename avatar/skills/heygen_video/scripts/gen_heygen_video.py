#!/usr/bin/env python3
"""Generate video using HeyGen API: TTS + avatar lip-sync.

Usage:
    python3 gen_heygen_video.py --text "Hello world" [--output video.mp4]

Requires:
    - HEYGEN_API_KEY environment variable set
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime
from pathlib import Path

HEYGEN_API_KEY = os.getenv("HEYGEN_API_KEY", "")
HEYGEN_BASE = "https://api.heygen.com"

DEFAULT_AVATAR = "7f6390b2e98d45149dc5661ca3aa642d"  # Zihan
DEFAULT_VOICE = "6924376faa724608a539daba27d691b6"  # Savvy Stefano (Italian)


def check_api_key():
    if not HEYGEN_API_KEY:
        print("❌ HEYGEN_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)


def api_post(endpoint, data):
    url = f"{HEYGEN_BASE}{endpoint}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", f"Bearer {HEYGEN_API_KEY}")
    req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"ERRORE API {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)


def api_get(endpoint):
    url = f"{HEYGEN_BASE}{endpoint}"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {HEYGEN_API_KEY}")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode()
        print(f"ERRORE API {e.code}: {err_body}", file=sys.stderr)
        sys.exit(1)


def create_video(text, avatar_id, voice_id=None, output_path=None):
    """Create video via HeyGen v2 API"""
    payload = {
        "video_inputs": [
            {
                "character": {
                    "type": "avatar_id",
                    "avatar_id": avatar_id
                },
                "voice": {
                    "type": "voice_id",
                    "voice_id": voice_id or DEFAULT_VOICE
                },
                "text": {
                    "type": "text",
                    "input_text": text
                }
            }
        ],
        "dimension": {
            "width": 1280,
            "height": 720
        }
    }

    print(f"🎬 Creazione video con avatar {avatar_id}...")
    result = api_post("/v2/video.generate", payload)
    
    video_id = result.get("data", {}).get("video_id")
    if not video_id:
        print(f"❌ Nessun video_id nella risposta: {json.dumps(result, indent=2)}", file=sys.stderr)
        sys.exit(1)
    
    print(f"📋 Video ID: {video_id}")
    
    # Poll for completion
    print("⏳ Attesa generazione video...")
    while True:
        status_result = api_get(f"/v2/video.get/{video_id}")
        status = status_result.get("data", {}).get("status")
        
        if status == "completed":
            video_url = status_result.get("data", {}).get("video_url")
            print(f"✅ Video completato!")
            print(f"🔗 {video_url}")
            
            if output_path and video_url:
                os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
                print(f"⬇️ Download video...")
                urllib.request.urlretrieve(video_url, output_path)
                print(f"💾 Salvato: {output_path}")
            
            return video_url
        elif status == "failed":
            print(f"❌ Generazione fallita: {status_result}", file=sys.stderr)
            sys.exit(1)
        else:
            print(f"   Status: {status}...")
            time.sleep(10)


def main():
    parser = argparse.ArgumentParser(description="Generate video with HeyGen avatar")
    parser.add_argument("--text", required=True, help="Text to speak")
    parser.add_argument("--avatar", default=DEFAULT_AVATAR, help="Avatar ID")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help="Voice ID")
    parser.add_argument("--output", help="Output video path")
    args = parser.parse_args()

    check_api_key()
    create_video(args.text, args.avatar, args.voice, args.output)


if __name__ == "__main__":
    main()
