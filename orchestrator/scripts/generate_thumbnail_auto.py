#!/usr/bin/env python3
"""
Thumbnail generation with automatic fallback.

Flow:
1. Try ChatGPT browser (generates new image if logged in)
2. If browser fails, use OpenAI API

Usage:
    python3 generate_thumbnail_auto.py --title "Title" --subtitle "Sub"
"""

import argparse
import json
import os
import sys
import subprocess
import time

WORKSPACE = os.path.expanduser("~/.openclaw")
OUTPUT_DIR = os.path.join(WORKSPACE, "workspace-orchestrator/outputs")
THUMBNAILS_DIR = os.path.join(WORKSPACE, "workspace-orchestrator/thumbnails")
BROWSER_SCRIPT = os.path.join(WORKSPACE, "workspace-orchestrator/scripts/generate_thumbnail_browser.py")
API_SCRIPT = os.path.join(WORKSPACE, "workspace-orchestrator/scripts/generate_thumbnail.py")


def try_browser(title, subtitle, output_path):
    """Try generating thumbnail via ChatGPT browser."""
    print("   🌐 ChatGPT browser...")
    
    if not os.path.exists(BROWSER_SCRIPT):
        print("   ⚠️  Script browser non trovato")
        return False
    
    result = subprocess.run([
        "python3", BROWSER_SCRIPT,
        "--title", title,
        "--subtitle", subtitle,
        "--output", output_path,
        "--max-wait", "120"
    ], capture_output=True, text=True, timeout=150)
    
    if result.returncode == 0 and os.path.exists(output_path):
        size = os.path.getsize(output_path) / 1024
        print(f"   ✅ ChatGPT browser: {size:.0f} KB")
        return True
    
    error = result.stderr.strip().split('\n')[-1][:80] if result.stderr else "unknown"
    print(f"   ❌ ChatGPT browser fallito: {error}")
    return False


def try_api(title, subtitle, output_path):
    """Try generating thumbnail via OpenAI API."""
    print("   🔑 OpenAI API...")
    
    if not os.path.exists(API_SCRIPT):
        print("   ⚠️  Script API non trovato")
        return False
    
    result = subprocess.run([
        "python3", API_SCRIPT,
        "--title", title,
        "--subtitle", subtitle,
        "--output", output_path
    ], capture_output=True, text=True, timeout=45)
    
    if result.returncode == 0 and os.path.exists(output_path):
        size = os.path.getsize(output_path) / 1024
        print(f"   ✅ OpenAI API: {size:.0f} KB")
        return True
    
    error = result.stderr.strip().split('\n')[-1][:80] if result.stderr else "unknown"
    print(f"   ❌ OpenAI API fallito: {error}")
    return False


def main():
    parser = argparse.ArgumentParser(description="Generate thumbnail with auto fallback")
    parser.add_argument("--title", required=True)
    parser.add_argument("--subtitle", default="")
    parser.add_argument("--output", default=os.path.join(OUTPUT_DIR, "thumbnail.png"))
    args = parser.parse_args()
    
    print(f"🎨 Thumbnail: {args.title[:50]}...")
    
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    
    # Strategy 1: ChatGPT browser
    if try_browser(args.title, args.subtitle, args.output):
        print(f"\n✅ ChatGPT browser OK")
        return 0
    
    # Strategy 2: OpenAI API
    if try_api(args.title, args.subtitle, args.output):
        print(f"\n✅ OpenAI API OK")
        return 0
    
    print(f"\n❌ Tutti i metodi falliti")
    return 1


if __name__ == "__main__":
    sys.exit(main())
