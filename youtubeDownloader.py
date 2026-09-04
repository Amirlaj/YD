#!/usr/bin/env python3

import shutil
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlparse, parse_qs

def find_ytdlp():
    preferred = "/usr/local/bin/yt-dlp"
    if Path(preferred).exists():
        return preferred

    found = shutil.which("yt-dlp")
    if found:
        return found

    print("Error: yt-dlp was not found.")
    print("Install it with: brew install yt-dlp")
    sys.exit(1)

def main():
    url = input("Paste the YouTube video URL: ").strip()

    if not url:
        print("No URL entered.")
        return

    ytdlp = find_ytdlp()
    downloads = Path.home() / "Downloads"

    # Detect whether the URL contains a playlist
    try:
        query = parse_qs(urlparse(url).query)
        has_playlist = "list" in query
    except Exception:
        has_playlist = False

    command = [
        ytdlp,
        "--cookies-from-browser", "chrome",
        "-P", str(downloads),
    ]

    if has_playlist:
        answer = input("This URL contains a playlist. Download the whole playlist? [y/N]: ").strip().lower()
        if answer in {"y", "yes"}:
            command += [
                "--yes-playlist",
                "-o", "%(playlist_title)s/%(playlist_index)03d - %(title)s.%(ext)s"
            ]
        else:
            command.append("--no-playlist")
    else:
        command.append("--no-playlist")

    command.append(url)

    print("\nStarting download...\n")

    try:
        subprocess.run(command, check=True)
        print(f"\nDone. Check: {downloads}")
    except subprocess.CalledProcessError:
        print("\nDownload failed. Check the error message above.")
    except KeyboardInterrupt:
        print("\nDownload cancelled.")

if __name__ == "__main__":
    main()
