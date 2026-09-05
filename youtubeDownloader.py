#!/usr/bin/env python3

"""Command-line entry point for the YouTube downloader."""

import subprocess

from youtube_downloader.core import (
    build_download_command,
    default_download_directory,
    find_ytdlp,
    is_playlist_url,
)


def main():
    url = input("Paste the YouTube video URL: ").strip()
    if not url:
        print("No URL entered.")
        return

    ytdlp = find_ytdlp()
    if not ytdlp:
        print("Error: yt-dlp was not found.")
        print("Install it with: brew install yt-dlp")
        return

    download_playlist = False
    if is_playlist_url(url):
        answer = input(
            "This URL contains a playlist. Download the whole playlist? [y/N]: "
        ).strip().lower()
        download_playlist = answer in {"y", "yes"}

    destination = default_download_directory()
    command = build_download_command(
        ytdlp=ytdlp,
        url=url,
        destination=destination,
        download_playlist=download_playlist,
        use_chrome_cookies=True,
    )

    print("\nStarting download...\n")
    try:
        subprocess.run(command, check=True)
        print(f"\nDone. Check: {destination}")
    except subprocess.CalledProcessError:
        print("\nDownload failed. Check the error message above.")
    except KeyboardInterrupt:
        print("\nDownload cancelled.")


if __name__ == "__main__":
    main()
