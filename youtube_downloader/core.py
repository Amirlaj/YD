"""Shared yt-dlp discovery and command-building logic."""

import shutil
from pathlib import Path
from urllib.parse import parse_qs, urlparse


PLAYLIST_OUTPUT_TEMPLATE = (
    "%(playlist_title)s/%(playlist_index)03d - %(title)s.%(ext)s"
)


def find_ytdlp():
    """Return the yt-dlp executable path, or None if it is unavailable."""
    preferred_path = Path("/usr/local/bin/yt-dlp")
    if preferred_path.exists():
        return str(preferred_path)
    return shutil.which("yt-dlp")


def default_download_directory():
    """Return the current user's Downloads folder."""
    return Path.home() / "Downloads"


def is_playlist_url(url):
    """Return whether a URL includes YouTube's playlist query parameter."""
    try:
        return "list" in parse_qs(urlparse(url).query)
    except ValueError:
        return False


def build_download_command(
    *,
    ytdlp,
    url,
    destination,
    download_playlist=False,
    use_chrome_cookies=True,
):
    """Build the yt-dlp command used by both application interfaces."""
    command = [ytdlp, "--newline", "-P", str(destination)]

    if use_chrome_cookies:
        command.extend(["--cookies-from-browser", "chrome"])

    if download_playlist and is_playlist_url(url):
        command.extend(
            ["--yes-playlist", "-o", PLAYLIST_OUTPUT_TEMPLATE]
        )
    else:
        command.append("--no-playlist")

    command.append(url)
    return command
