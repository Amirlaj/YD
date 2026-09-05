# YouTube Downloader

A small Python wrapper around `yt-dlp` with both terminal and desktop interfaces.

## Project structure

```text
youtubeDownloader.py       Terminal entry point
youtubeDownloaderGUI.py    Desktop entry point
youtube_downloader/
  __init__.py              Public package exports
  __main__.py              `python -m` entry point
  core.py                  Shared yt-dlp command logic
  gui.py                   Tkinter desktop interface
```

## Run the desktop interface

```bash
python3 youtubeDownloaderGUI.py
```

You can also run it as a module:

```bash
python3 -m youtube_downloader
```

## Run the terminal interface

```bash
python3 youtubeDownloader.py
```

Install the downloader dependency with `brew install yt-dlp` if it is not already
available. Tkinter is included with the Python installation used by this project.
