#!/usr/bin/env python3
"""
Generate YouTube thumbnail via ChatGPT browser (Chrome Live).

Workflow:
1. Open ChatGPT in browser
2. Type prompt with title and subtitle
3. Wait for image generation
4. Download both generated images
5. Pick the best one (first is usually better)
6. Copy to pipeline output

Usage:
    python3 generate_thumbnail_chatgpt.py --title "Title" --subtitle "Sub"

Requires:
    - OpenClaw browser (Chrome Live) with ChatGPT logged in
    - User must be logged in to chatgpt.com

If ChatGPT is not available, exits with code 1 for API fallback.
"""

import argparse
import json
import os
import sys
import base64
import urllib.request
import time
import subprocess

WORKSPACE = os.path.expanduser("~/.openclaw")
DEFAULT_OUTPUT = os.path.join(WORKSPACE, "workspace-orchestrator/outputs/thumbnail.png")

CHATGPT_PROMPT = (
    "Generate a YouTube tech thumbnail image. "
    "16:9 aspect ratio, 1536x1024 resolution. "
    "Dark navy blue background, metallic robotic claw/hand on the left "
    "with blue and cyan neon glow, futuristic holographic elements. "
    "Bold white and cyan text on the right. "
    "Professional tech YouTube channel aesthetic. "
    "Render the following text EXACTLY as written:"
)


def check_browser_running():
    """Check if OpenClaw browser is running."""
    try:
        result = subprocess.run(
            ["curl", "-s", "http://127.0.0.1:18800/json/list"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            tabs = json.loads(result.stdout)
            for tab in tabs:
                if "chatgpt" in tab.get("url", "").lower():
                    return tab.get("webSocketDebuggerUrl"), tab.get("url")
        return None, None
    except:
        return None, None


def generate_via_chatgpt(title, subtitle, output_path):
    """
    Generate thumbnail via ChatGPT browser.
    Returns True on success, False on failure.
    
    NOTE: This is a manual-assist process. The browser automation
    via Chrome Live is unreliable for ChatGPT's React UI.
    
    The recommended workflow is:
    1. Use OpenClaw browser to navigate to chatgpt.com
    2. Type the prompt and wait for generation
    3. Extract images via JS evaluate (message.images[0])
    4. Save to output
    
    For now, this script serves as a wrapper that can be called
    by the orchestrator's browser automation flow.
    """
    
    prompt = f"{CHATGPT_PROMPT}\n\nTitle: {title}\nSubtitle: {subtitle}"
    
    print(f"📝 Prompt generato ({len(prompt)} chars)")
    print(f"   Title: {title}")
    print(f"   Subtitle: {subtitle}")
    print(f"   Output: {output_path}")
    print()
    print("⚠️  Richiesto: browser openclaw con ChatGPT loggato")
    print("   Questo script deve essere chiamato dall'orchestratore")
    print("   che ha accesso al browser via Chrome Live.")
    print()
    print("   Flux manuale:")
    print("   1. Apri browser openclaw (arancione)")
    print("   2. Vai su chatgpt.com")
    print("   3. Incolla il prompt nel chat")
    print("   4. Attendi generazione (~2 min)")
    print("   5. Estrai immagini via JS (message.images[0].image_url.url)")
    print("   6. Salva la prima (migliore) come output")
    
    # Return the prompt for the orchestrator to use
    return prompt


def main():
    parser = argparse.ArgumentParser(description="Generate thumbnail via ChatGPT browser")
    parser.add_argument("--title", required=True, help="Main title text")
    parser.add_argument("--subtitle", default="", help="Subtitle text")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="Output file path")
    args = parser.parse_args()
    
    prompt = generate_via_chatgpt(args.title, args.subtitle, args.output)
    
    # Write prompt to a file for the orchestrator to pick up
    prompt_file = os.path.join(WORKSPACE, "workspace-orchestrator/outputs/chatgpt_prompt.txt")
    os.makedirs(os.path.dirname(prompt_file), exist_ok=True)
    with open(prompt_file, "w") as f:
        f.write(prompt)
    
    print(f"\n📄 Prompt salvato: {prompt_file}")
    print("   Usa questo prompt nel browser ChatGPT per generare il thumbnail.")


if __name__ == "__main__":
    main()
