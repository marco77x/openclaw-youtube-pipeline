#!/usr/bin/env python3
"""Upload video to YouTube using curl for resumable upload.

Usage:
    python3 upload_video.py --video <VIDEO> --title "<TITLE>" --description "<DESC>" --tags "<TAG1,TAG2>" --privacy <private|unlisted|public> --thumbnail <THUMBNAIL>

Requires:
    - Configured Google OAuth credentials in config/client_secret.json
    - Valid token.pickle (generated on first OAuth run)
"""

import argparse
import json
import os
import sys
import pickle
import subprocess
import time

SCOPES = ["https://www.googleapis.com/auth/youtube.upload",
          "https://www.googleapis.com/auth/youtube"]

CLIENT_SECRET_FILE = "config/client_secret.json"
TOKEN_FILE = "config/token.pickle"

WORKSPACE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def get_token():
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request as GoogleRequest
    
    token_path = os.path.join(WORKSPACE_DIR, TOKEN_FILE)
    secret_path = os.path.join(WORKSPACE_DIR, CLIENT_SECRET_FILE)
    
    if not os.path.exists(secret_path):
        print(f"❌ Client secret not found: {secret_path}", file=sys.stderr)
        print("See config/client_secret.json.example for setup instructions", file=sys.stderr)
        sys.exit(1)
    
    creds = None
    if os.path.exists(token_path):
        with open(token_path, "rb") as f:
            creds = pickle.load(f)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(GoogleRequest())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secret_path, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(token_path, "wb") as f:
            pickle.dump(creds, f)
    
    return creds.token


def upload_with_curl(video_path, title, description, tags, privacy, thumbnail_path=None):
    token = get_token()
    
    # Prepare metadata
    metadata = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags.split(",") if tags else [],
            "categoryId": "28"  # Science & Technology
        },
        "status": {
            "privacyStatus": privacy,
            "selfDeclaredMadeForKids": False
        }
    }

    metadata_file = "/tmp/youtube_metadata.json"
    with open(metadata_file, "w") as f:
        json.dump(metadata, f)
    
    # Resumable upload using curl
    print("Step 1: Initiate upload...")
    init_result = subprocess.run([
        "curl", "-s", "-X", "POST",
        "https://www.googleapis.com/upload/youtube/v3/videos?uploadType=resumable&part=snippet,status",
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "-H", "X-Upload-Content-Length: " + str(os.path.getsize(video_path)),
        "-H", "X-Upload-Content-Type: video/mp4",
        "-d", json.dumps(metadata),
        "-D", "/tmp/youtube_headers.txt"
    ], capture_output=True, text=True, timeout=30)
    
    # Extract upload URL (case-insensitive)
    upload_url = None
    with open("/tmp/youtube_headers.txt") as f:
        for line in f:
            if line.lower().startswith("location:"):
                upload_url = line.split(":", 1)[1].strip()
                break
    
    if not upload_url:
        print("❌ Failed to get upload URL", file=sys.stderr)
        print("Headers:", init_result.stdout[:500], file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Upload URL obtained")
    
    # Upload the video file
    print("Step 2: Uploading video...")
    upload_result = subprocess.run([
        "curl", "-s", "-X", "PUT",
        upload_url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: video/mp4",
        "-H", f"Content-Length: {os.path.getsize(video_path)}",
        "--data-binary", f"@{video_path}",
        "-w", "\n%{http_code}"
    ], capture_output=True, text=True, timeout=600)
    
    # Parse response (last line is HTTP status code)
    lines = upload_result.stdout.strip().split("\n")
    http_code = lines[-1].strip()
    response_body = "\n".join(lines[:-1])
    
    if http_code not in ("200", "201"):
        print(f"❌ Upload failed (HTTP {http_code})", file=sys.stderr)
        print(response_body[:500], file=sys.stderr)
        sys.exit(1)
    
    try:
        result = json.loads(response_body)
    except json.JSONDecodeError:
        print(f"❌ Could not parse response: {response_body[:200]}", file=sys.stderr)
        sys.exit(1)
    
    video_id = result.get("id")
    if not video_id:
        print("❌ No video ID in response", file=sys.stderr)
        sys.exit(1)
    
    print(f"✅ Video uploaded! ID: {video_id}")
    print(f"🔗 https://www.youtube.com/watch?v={video_id}")
    
    # Set thumbnail if provided
    if thumbnail_path and os.path.exists(thumbnail_path):
        print("Step 3: Setting thumbnail...")
        thumb_result = subprocess.run([
            "curl", "-s", "-X", "POST",
            "https://www.googleapis.com/upload/youtube/v3/thumbnails?videoId=" + video_id,
            "-H", f"Authorization: Bearer {token}",
            "-H", f"Content-Type: image/png",
            "--data-binary", f"@{thumbnail_path}"
        ], capture_output=True, text=True, timeout=30)
        
        try:
            thumb_resp = json.loads(thumb_result.stdout)
            if "items" in thumb_resp:
                print("✅ Thumbnail impostata!")
            else:
                print(f"⚠️ Thumbnail upload issue: {thumb_result.stdout[:200]}")
        except:
            print(f"⚠️ Could not set thumbnail: {thumb_result.stdout[:200]}")
    
    return video_id


def main():
    parser = argparse.ArgumentParser(description="Upload video to YouTube")
    parser.add_argument("--video", required=True, help="Path to MP4 video")
    parser.add_argument("--title", required=True, help="Video title")
    parser.add_argument("--description", default="", help="Video description")
    parser.add_argument("--tags", default="", help="Comma-separated tags")
    parser.add_argument("--privacy", default="private", choices=["public", "unlisted", "private"])
    parser.add_argument("--thumbnail", help="Path to thumbnail PNG")
    args = parser.parse_args()
    
    if not os.path.exists(args.video):
        print(f"❌ Video file not found: {args.video}", file=sys.stderr)
        sys.exit(1)
    
    video_id = upload_with_curl(
        args.video, args.title, args.description,
        args.tags, args.privacy, args.thumbnail
    )
    
    # Save last upload info
    state_dir = os.path.join(WORKSPACE_DIR, "state")
    os.makedirs(state_dir, exist_ok=True)
    with open(os.path.join(state_dir, "last_publish.json"), "w") as f:
        json.dump({
            "youtube_video_id": video_id,
            "title": args.title,
            "privacy_status": args.privacy,
            "uploaded_at": time.strftime("%Y-%m-%dT%H:%M:%S")
        }, f, indent=2)
    
    print(f"📝 Saved to state/last_publish.json")


if __name__ == "__main__":
    main()
