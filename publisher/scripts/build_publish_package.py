#!/usr/bin/env python3
"""
Handoff script: Metadata → Publisher
Reads outputs from upstream agents and assembles the publish_package.json
for the publisher to consume.

Usage:
    python3 build_publish_package.py [--dry-run]

Exit codes:
    0 = success, package written
    1 = missing input file
    2 = incomplete/invalid data
"""

import argparse
import json
import os
import sys
import subprocess
from datetime import datetime

WORKSPACE = os.path.expanduser("~/.openclaw")

# Paths — workspaces are siblings under ~/.openclaw/
METADATA_PATH = os.path.join(WORKSPACE, "workspace-metadata/outputs/latest_metadata.json")
ORCH_THUMBNAIL = os.path.join(WORKSPACE, "workspace-orchestrator/outputs/thumbnail.png")
AVATAR_OUTPUT_DIR = os.path.join(WORKSPACE, "workspace-avatar/output/videos/")
PUBLISHER_INPUTS = os.path.join(WORKSPACE, "workspace-publisher/inputs")
PUBLISHER_PACKAGE = os.path.join(PUBLISHER_INPUTS, "publish_package.json")
SRT_GENERATOR = os.path.join(WORKSPACE, "workspace-orchestrator/scripts/generate_srt.py")


def load_json(path):
    if not os.path.exists(path):
        return None, f"File not found: {path}"
    with open(path) as f:
        try:
            return json.load(f), None
        except json.JSONDecodeError as e:
            return None, f"Invalid JSON in {path}: {e}"


def find_latest_video():
    """Find the most recent .mp4 video in the avatar output/videos directory."""
    if not os.path.isdir(AVATAR_OUTPUT_DIR):
        return None
    mp4s = [f for f in os.listdir(AVATAR_OUTPUT_DIR) if f.endswith(".mp4")]
    if not mp4s:
        return None
    # Prefer the pipeline-full one, otherwise take the largest
    for f in mp4s:
        if f.startswith("pipeline-full"):
            return os.path.join(AVATAR_OUTPUT_DIR, f)
    # Fallback: newest by mtime
    mp4s.sort(key=lambda f: os.path.getmtime(os.path.join(AVATAR_OUTPUT_DIR, f)), reverse=True)
    return os.path.join(AVATAR_OUTPUT_DIR, mp4s[0])


def build_tags_string(metadata):
    """Extract tags as comma-separated string from various metadata formats."""
    tags = metadata.get("youtube", {}).get("tags", metadata.get("tags", []))
    if isinstance(tags, list):
        return ",".join(tags)
    return str(tags)


def build_description(metadata):
    """Extract description from metadata."""
    return metadata.get("youtube", {}).get("description", metadata.get("description", ""))


def build_title(metadata):
    """Extract title from metadata."""
    return metadata.get("youtube", {}).get("title", metadata.get("primary_title", ""))


def main():
    parser = argparse.ArgumentParser(description="Build publisher handoff package")
    parser.add_argument("--dry-run", action="store_true", help="Validate without writing")
    args = parser.parse_args()

    errors = []
    warnings = []

    # 1. Load metadata
    meta, err = load_json(METADATA_PATH)
    if err:
        errors.append(err)
        print(f"❌ {err}")
    else:
        print(f"✅ Metadata loaded: {meta.get('date', 'no date')}")

    # 2. Find video file
    video_path = find_latest_video()
    if video_path and os.path.exists(video_path):
        size_mb = os.path.getsize(video_path) / (1024 * 1024)
        print(f"✅ Video found: {os.path.basename(video_path)} ({size_mb:.1f} MB)")
    else:
        errors.append(f"Video file not found: {video_path}")
        print(f"❌ Video file not found: {video_path}")

    # 3. Check thumbnail
    thumbnail_path = ORCH_THUMBNAIL
    if os.path.exists(thumbnail_path):
        size_kb = os.path.getsize(thumbnail_path) / 1024
        print(f"✅ Thumbnail found: {size_kb:.0f} KB")
    else:
        warnings.append(f"Thumbnail not found: {thumbnail_path}")
        print(f"⚠️  Thumbnail not found (will publish without)")

    # 4. Generate SRT subtitles from script
    srt_path = None
    if meta and video_path:
        script_text = meta.get("youtube", {}).get("description", "") or ""
        # Try to get full script from scripter state
        script_state = os.path.join(WORKSPACE, "workspace-scripter/state/latest_script.json")
        if os.path.exists(script_state):
            with open(script_state) as f:
                script_data = json.load(f)
                script_text = script_data.get("full_script", script_text)
        
        if script_text:
            duration = meta.get("youtube", {}).get("duration_seconds", 90)
            date_str = meta.get("date", datetime.now().strftime("%Y-%m-%d"))
            srt_path = os.path.join(AVATAR_OUTPUT_DIR, f"subs_{date_str}.srt")
            try:
                subprocess.run([
                    "python3", SRT_GENERATOR,
                    "--script", script_text,
                    "--duration", str(duration),
                    "--output", srt_path
                ], check=True, capture_output=True, text=True)
                if os.path.exists(srt_path):
                    print(f"✅ SRT subtitles generated: {srt_path}")
                else:
                    warnings.append("SRT generation failed")
            except subprocess.CalledProcessError as e:
                warnings.append(f"SRT generation error: {e.stderr[:100]}")
                print(f"⚠️  SRT generation failed")

    if errors:
        print(f"\n❌ {len(errors)} errori, impossibile creare il pacchetto.")
        sys.exit(1)

    # 4. Build package
    title = build_title(meta)
    description = build_description(meta)
    tags = build_tags_string(meta)

    if not title:
        errors.append("Title is empty in metadata")
    if not description:
        warnings.append("Description is empty in metadata")

    package = {
        "date": meta.get("date", datetime.now().strftime("%Y-%m-%d")),
        "video_path": video_path,
        "title": title,
        "description": description,
        "tags": tags,
        "privacy_status": "private",  # default to private for safety
        "thumbnail_path": thumbnail_path if os.path.exists(thumbnail_path) else None,
        "subtitle_path": srt_path if srt_path and os.path.exists(srt_path) else None,
        "scheduled_publish_at": None,
        "playlist_name": None,
        "language": meta.get("youtube", {}).get("language", "it"),
        "category_id": "28",  # Science & Technology
        "made_for_kids": False,
        "notify_subscribers": True,
        "source_metadata": METADATA_PATH,
        "built_at": datetime.now().isoformat()
    }

    # 5. Write or dry-run
    if args.dry_run:
        print("\n📋 DRY RUN — package preview:")
        print(json.dumps(package, indent=2, ensure_ascii=False))
        if warnings:
            print(f"\n⚠️  {len(warnings)} avvisi:")
            for w in warnings:
                print(f"   - {w}")
    else:
        os.makedirs(PUBLISHER_INPUTS, exist_ok=True)
        with open(PUBLISHER_PACKAGE, "w") as f:
            json.dump(package, f, indent=2, ensure_ascii=False)
        print(f"\n✅ Pacchetto scritto: {PUBLISHER_PACKAGE}")

        if warnings:
            print(f"⚠️  {len(warnings)} avvisi:")
            for w in warnings:
                print(f"   - {w}")

    print(f"\n🎯 Publisher pronto: python3 upload_video.py --video <path> --title \"...\" ...")
    sys.exit(0)


if __name__ == "__main__":
    main()
