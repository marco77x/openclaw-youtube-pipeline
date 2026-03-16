#!/usr/bin/env python3
"""
Publish a previously uploaded YouTube video (change privacy from private to public).

Usage:
    python3 publish_video.py [--video-id VIDEO_ID] [--privacy public|unlisted]

If --video-id is not provided, reads from last_publish.json.

Requires:
    - Configured Google OAuth credentials (see config/client_secret.json.example)
    - Valid token.pickle generated during first OAuth flow
"""

import argparse
import json
import os
import pickle
import urllib.request
import sys
from datetime import datetime

WORKSPACE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOKEN_FILE = os.path.join(WORKSPACE, "config/token.pickle")
LAST_PUBLISH = os.path.join(WORKSPACE, "state/last_publish.json")
PUBLISH_LOG = os.path.join(WORKSPACE, "outputs")


def get_token():
    from google.auth.transport.requests import Request as GoogleRequest
    token_path = TOKEN_FILE
    secret_path = os.path.join(WORKSPACE, "config/client_secret.json")
    
    if not os.path.exists(token_path):
        print(f"❌ Token file not found: {token_path}", file=sys.stderr)
        print("Run upload_video.py first to generate OAuth token", file=sys.stderr)
        sys.exit(1)
    
    with open(token_path, "rb") as f:
        creds = pickle.load(f)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            print("❌ Token non valido e nessun refresh token", file=sys.stderr)
            sys.exit(1)
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)
    
    return creds.token


def update_privacy(video_id, new_privacy, token):
    payload = json.dumps({
        "id": video_id,
        "status": {
            "privacyStatus": new_privacy
        }
    }).encode()
    
    req = urllib.request.Request(
        f"https://www.googleapis.com/youtube/v3/videos?part=status",
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        },
        method="PUT"
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            result = json.loads(resp.read())
        return result
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get("error", {}).get("message", body[:200])
        except:
            msg = body[:200]
        print(f"❌ API error ({e.code}): {msg}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Publish YouTube video (change privacy)")
    parser.add_argument("--video-id", help="YouTube video ID (or read from last_publish.json)")
    parser.add_argument("--privacy", default="public", choices=["public", "unlisted", "private"])
    args = parser.parse_args()
    
    # Get video ID
    video_id = args.video_id
    if not video_id and os.path.exists(LAST_PUBLISH):
        with open(LAST_PUBLISH) as f:
            last = json.load(f)
        video_id = last.get("youtube_video_id")
        if not video_id:
            print("❌ Nessun video_id in last_publish.json", file=sys.stderr)
            sys.exit(1)
        print(f"📋 Video ID da last_publish: {video_id}")
    
    if not video_id:
        print("❌ Nessun video_id specificato", file=sys.stderr)
        sys.exit(1)
    
    # Get token
    token = get_token()
    
    # Update privacy
    print(f"🔄 Cambio privacy a '{args.privacy}' per video {video_id}...")
    result = update_privacy(video_id, args.privacy, token)
    
    new_status = result.get("status", {}).get("privacyStatus", args.privacy)
    print(f"✅ Privacy aggiornata a: {new_status}")
    print(f"🔗 https://www.youtube.com/watch?v={video_id}")
    
    # Update last_publish
    if os.path.exists(LAST_PUBLISH):
        with open(LAST_PUBLISH) as f:
            last = json.load(f)
    else:
        last = {}
    
    last["privacy_status"] = new_status
    last["published_at"] = datetime.now().isoformat()
    
    os.makedirs(os.path.dirname(LAST_PUBLISH), exist_ok=True)
    with open(LAST_PUBLISH, "w") as f:
        json.dump(last, f, indent=2, ensure_ascii=False)
    
    # Log
    os.makedirs(PUBLISH_LOG, exist_ok=True)
    log_path = os.path.join(PUBLISH_LOG, f"publish_log_{datetime.now().strftime('%Y-%m-%d')}.json")
    with open(log_path, "w") as f:
        json.dump({
            "video_id": video_id,
            "privacy": new_status,
            "published_at": datetime.now().isoformat(),
            "youtube_url": f"https://www.youtube.com/watch?v={video_id}"
        }, f, indent=2)
    
    print(f"📝 Log: {log_path}")


if __name__ == "__main__":
    main()
