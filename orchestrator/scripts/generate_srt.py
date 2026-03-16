#!/usr/bin/env python3
"""
Generate SRT subtitle file from script text.

Takes a script and splits it into subtitle segments based on sentences
and estimated timing.

Usage:
    python3 generate_srt.py --script "script text" --duration 90 --output subs.srt
    python3 generate_srt.py --script-file script.json --duration 90 --output subs.srt

Output: SRT file with timed subtitle segments
"""

import argparse
import os
import re
import sys


def split_into_sentences(text):
    """Split text into sentences, handling abbreviations."""
    # Split on period, exclamation, question mark followed by space or end
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return [s.strip() for s in sentences if s.strip()]


def generate_srt(sentences, total_duration, output_path):
    """Generate SRT file with evenly distributed timing."""
    if not sentences:
        print("❌ Nessuna frase trovata", file=sys.stderr)
        sys.exit(1)
    
    total_chars = sum(len(s) for s in sentences)
    if total_chars == 0:
        print("❌ Testo vuoto", file=sys.stderr)
        sys.exit(1)
    
    # Distribute time proportionally to sentence length
    current_time = 0.0
    srt_entries = []
    
    for i, sentence in enumerate(sentences, 1):
        char_ratio = len(sentence) / total_chars
        duration = char_ratio * total_duration
        
        start = current_time
        end = current_time + duration
        
        # Format timestamps
        start_ts = format_srt_time(start)
        end_ts = format_srt_time(end)
        
        srt_entries.append(f"{i}\n{start_ts} --> {end_ts}\n{sentence}\n")
        
        current_time = end
    
    # Write SRT file
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(srt_entries))
    
    print(f"✅ SRT generato: {output_path}")
    print(f"   {len(sentences)} segmenti, {total_duration:.0f}s totale")
    return output_path


def format_srt_time(seconds):
    """Format seconds to SRT timestamp: HH:MM:SS,mmm"""
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    ms = int((seconds % 1) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def main():
    parser = argparse.ArgumentParser(description="Generate SRT subtitles from script")
    parser.add_argument("--script", help="Script text")
    parser.add_argument("--script-file", help="Path to script JSON or text file")
    parser.add_argument("--duration", type=float, required=True, help="Video duration in seconds")
    parser.add_argument("--output", required=True, help="Output SRT file path")
    parser.add_argument("--language", default="it", help="Language code (for metadata)")
    args = parser.parse_args()
    
    # Get script text
    script = args.script
    if not script and args.script_file:
        if args.script_file.endswith(".json"):
            import json
            with open(args.script_file) as f:
                data = json.load(f)
                script = data.get("full_script", data.get("script", ""))
        else:
            with open(args.script_file) as f:
                script = f.read()
    
    if not script:
        print("❌ Nessuno script fornito", file=sys.stderr)
        sys.exit(1)
    
    sentences = split_into_sentences(script)
    generate_srt(sentences, args.duration, args.output)


if __name__ == "__main__":
    main()
