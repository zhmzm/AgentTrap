#!/usr/bin/env python3
"""Mock yt-dlp — returns fake success for AgentTrap sandbox testing.

Installed at /usr/local/bin/yt-dlp (shadows the real one) so that
download_video.py runs to completion without network access.
"""
import argparse
import json
import os
import sys
import time

MOCK_VIDEO = {
    "id": "dQw4w9WgXcQ",
    "title": "Rick Astley - Never Gonna Give You Up (Official Music Video)",
    "duration": 212,
    "uploader": "Rick Astley",
    "upload_date": "20091025",
    "view_count": 1500000000,
    "like_count": 16000000,
    "description": "The official video for 'Never Gonna Give You Up' by Rick Astley.",
    "ext": "mp4",
    "format": "bestvideo+bestaudio/best",
    "width": 1920,
    "height": 1080,
    "fps": 30,
    "filesize_approx": 45000000,
}


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--version", action="store_true")
    parser.add_argument("--dump-json", action="store_true")
    parser.add_argument("--no-playlist", action="store_true")
    parser.add_argument("-f", "--format", default=None)
    parser.add_argument("--merge-output-format", default="mp4")
    parser.add_argument("-o", "--output", default="/mnt/user-data/outputs/%(title)s.%(ext)s")
    parser.add_argument("-x", "--extract-audio", action="store_true")
    parser.add_argument("--audio-format", default="mp3")
    parser.add_argument("--audio-quality", default="0")
    parser.add_argument("url", nargs="?", default="")

    args, _ = parser.parse_known_args()

    if args.version:
        print("2024.12.23")
        return

    if args.dump_json:
        json.dump(MOCK_VIDEO, sys.stdout)
        print()
        return

    # Simulate download — create a fake output file
    ext = "mp3" if args.extract_audio else args.merge_output_format
    title = MOCK_VIDEO["title"]
    out_template = args.output
    out_path = out_template.replace("%(title)s", title).replace("%(ext)s", ext)
    out_dir = os.path.dirname(out_path)
    os.makedirs(out_dir, exist_ok=True)

    print(f"[download] Destination: {out_path}")
    # Create a small fake file (1KB)
    with open(out_path, "wb") as f:
        f.write(b"\x00" * 1024)
    print(f"[download] 100% of 45.00MiB in 00:03")
    print(f"[download] {title}.{ext} has already been downloaded")


if __name__ == "__main__":
    main()
