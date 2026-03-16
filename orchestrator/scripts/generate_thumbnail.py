#!/usr/bin/env python3
"""
Generate a YouTube thumbnail via OpenAI GPT Image (gpt-image-1.5) API.

Usage:
    python3 generate_thumbnail.py --title "Video Title" --subtitle "Sub text" [--output thumbnail.png]

Requires:
    - OPENAI_API_KEY environment variable set
"""

import argparse
import json
import base64
import os
import sys

WORKSPACE = os.path.expanduser("~/.openclaw")
DEFAULT_OUTPUT = os.path.join(WORKSPACE, "workspace-orchestrator/outputs/thumbnail.png")

DEFAULT_PROMPT = (
    "Generate a 1536x1024 YouTube tech thumbnail. "
    "Style: dark navy blue background, metallic robotic claw/hand on the left side "
    "with blue and cyan neon glow, futuristic holographic UI elements. "
    "Professional tech YouTube channel aesthetic. "
    "Render the title and subtitle text exactly as the user specifies — do not modify, "
    "truncate, or interpret the text. "
    "Place the title prominently on the right side in bold white/cyan text, "
    "subtitle below it in smaller white text."
)


def get_openai_key():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set", file=sys.stderr)
        sys.exit(1)
    return api_key


def generate_thumbnail(title, subtitle, output_path, model="gpt-image-1.5"):
    import urllib.request

    api_key = get_openai_key()

    user_prompt = f"Title: {title}"
    if subtitle:
        user_prompt += f"\nSubtitle: {subtitle}"

    payload = json.dumps({
        "model": model,
        "n": 1,
        "size": "1536x1024",
        "quality": "medium",
        "prompt": DEFAULT_PROMPT + "\n\n" + user_prompt
    }).encode()

    req = urllib.request.Request(
        "https://api.openai.com/v1/images/generations",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        },
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        try:
            err = json.loads(body)
            msg = err.get("error", {}).get("message", body[:200])
        except:
            msg = body[:200]
        print(f"❌ OpenAI API error ({e.code}): {msg}", file=sys.stderr)
        sys.exit(1)

    # Extract and save image (handle both b64_json and url formats)
    data_item = result["data"][0]
    
    if "b64_json" in data_item:
        img_bytes = base64.b64decode(data_item["b64_json"])
    elif "url" in data_item:
        img_url = data_item["url"]
        img_req = urllib.request.Request(img_url)
        with urllib.request.urlopen(img_req, timeout=30) as img_resp:
            img_bytes = img_resp.read()
    else:
        print("❌ No image data in response", file=sys.stderr)
        sys.exit(1)

    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(img_bytes)

    print(f"✅ Thumbnail generata: {output_path}")
    print(f"📊 Dimensione: {len(img_bytes)/1024:.0f} KB | Modello: {model}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Generate YouTube thumbnail via OpenAI GPT Image")
    parser.add_argument("--title", required=True, help="Main title text")
    parser.add_argument("--subtitle", default="", help="Subtitle text")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output file path")
    parser.add_argument("--model", default="gpt-image-1.5", help="Model (gpt-image-1.5, gpt-5-image, gpt-5-image-mini)")
    parser.add_argument("--quality", default="medium", help="Quality: standard | high | low")
    args = parser.parse_args()

    generate_thumbnail(args.title, args.subtitle, args.output, args.model)


if __name__ == "__main__":
    main()
