"""Tkinter desktop interface for the YouTube downloader."""

import os
import queue
import signal
import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from .core import build_download_command, default_download_directory, find_ytdlp


class YouTubeDownloaderApp:
    """Coordinate the desktop interface and its background download."""

    def __init__(self, root):
        self.root = root
        self.root.title("YouTube Downloader")
        self.root.geometry("760x560")
        self.root.minsize(620, 460)

        self.url = tk.StringVar()
        self.destination = tk.StringVar(value=str(default_download_directory()))
        self.download_playlist = tk.BooleanVar(value=False)
        self.use_cookies = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value="Ready")

        self.process = None
        self.running = False
        self.cancel_requested = False
        self.events = queue.Queue()

        self._build_interface()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.after(100, self._process_events)

    def _build_interface(self):
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(5, weight=1)

        ttk.Label(
            container,
            text="YouTube Downloader",
            font=("TkDefaultFont", 20, "bold"),
        ).grid(row=0, column=0, sticky="w", pady=(0, 18))

        ttk.Label(container, text="Video or playlist URL").grid(
            row=1, column=0, sticky="w"
        )
        self.url_entry = ttk.Entry(container, textvariable=self.url)
        self.url_entry.grid(row=2, column=0, sticky="ew", pady=(5, 14))
        self.url_entry.focus_set()

        ttk.Label(container, text="Save to").grid(row=3, column=0, sticky="w")
        destination_row = ttk.Frame(container)
        destination_row.grid(row=4, column=0, sticky="ew", pady=(5, 12))
        destination_row.columnconfigure(0, weight=1)

        self.destination_entry = ttk.Entry(
            destination_row, textvariable=self.destination
        )
        self.destination_entry.grid(row=0, column=0, sticky="ew")
        self.browse_button = ttk.Button(
            destination_row, text="Browse…", command=self.choose_destination
        )
        self.browse_button.grid(row=0, column=1, padx=(8, 0))

        self._build_output_area(container)
        self._build_options(container)
        self._build_footer(container)

        self.root.bind("<Return>", lambda _event: self.start_download())

    def _build_output_area(self, container):
        output_frame = ttk.LabelFrame(container, text="Download output", padding=8)
        output_frame.grid(row=5, column=0, sticky="nsew", pady=(0, 12))
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output = tk.Text(
            output_frame,
            height=12,
            wrap="word",
            state="disabled",
            font=("TkFixedFont", 11),
        )
        self.output.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(
            output_frame, orient="vertical", command=self.output.yview
        )
        scrollbar.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=scrollbar.set)

    def _build_options(self, container):
        options = ttk.Frame(container)
        options.grid(row=6, column=0, sticky="ew", pady=(0, 12))

        self.playlist_check = ttk.Checkbutton(
            options,
            text="Download the full playlist when the URL contains one",
            variable=self.download_playlist,
        )
        self.playlist_check.pack(anchor="w")

        self.cookies_check = ttk.Checkbutton(
            options,
            text="Use cookies from Chrome (for signed-in or restricted videos)",
            variable=self.use_cookies,
        )
        self.cookies_check.pack(anchor="w", pady=(5, 0))

    def _build_footer(self, container):
        footer = ttk.Frame(container)
        footer.grid(row=7, column=0, sticky="ew")
        footer.columnconfigure(0, weight=1)

        status_area = ttk.Frame(footer)
        status_area.grid(row=0, column=0, sticky="ew", padx=(0, 12))
        status_area.columnconfigure(0, weight=1)
        ttk.Label(status_area, textvariable=self.status).grid(
            row=0, column=0, sticky="w"
        )

        self.progress = ttk.Progressbar(status_area, mode="indeterminate")
        self.progress.grid(row=1, column=0, sticky="ew", pady=(5, 0))

        self.cancel_button = ttk.Button(
            footer, text="Cancel", command=self.cancel_download, state="disabled"
        )
        self.cancel_button.grid(row=0, column=1, padx=(0, 8))

        self.download_button = ttk.Button(
            footer, text="Download", command=self.start_download
        )
        self.download_button.grid(row=0, column=2)

    def choose_destination(self):
        chosen_directory = filedialog.askdirectory(
            title="Choose download folder", initialdir=self.destination.get()
        )
        if chosen_directory:
            self.destination.set(chosen_directory)

    def start_download(self):
        if self.running:
            return

        url = self.url.get().strip()
        if not url:
            messagebox.showwarning("Missing URL", "Paste a YouTube URL first.")
            self.url_entry.focus_set()
            return

        ytdlp = find_ytdlp()
        if not ytdlp:
            messagebox.showerror(
                "yt-dlp not found",
                "Install yt-dlp first with:\n\nbrew install yt-dlp",
            )
            return

        destination = self._prepare_destination()
        if destination is None:
            return

        command = build_download_command(
            ytdlp=ytdlp,
            url=url,
            destination=destination,
            download_playlist=self.download_playlist.get(),
            use_chrome_cookies=self.use_cookies.get(),
        )

        self.cancel_requested = False
        self._clear_output()
        self._append_output("Starting download...\n\n")
        self._set_running(True)

        threading.Thread(
            target=self._run_download,
            args=(command, str(destination)),
            daemon=True,
        ).start()

    def _prepare_destination(self):
        destination = Path(self.destination.get()).expanduser()
        try:
            destination.mkdir(parents=True, exist_ok=True)
        except OSError as error:
            messagebox.showerror(
                "Invalid destination",
                f"The download folder cannot be used:\n\n{error}",
            )
            return None
        return destination

    def _run_download(self, command, destination):
        options = {
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
            "text": True,
            "bufsize": 1,
        }
        if os.name == "posix":
            options["start_new_session"] = True

        try:
            self.process = subprocess.Popen(command, **options)
            if self.cancel_requested:
                self._terminate_process(self.process)

            if self.process.stdout:
                for line in self.process.stdout:
                    self.events.put(("output", line))

            return_code = self.process.wait()
            if self.cancel_requested:
                self.events.put(("finished", "Download cancelled."))
            elif return_code == 0:
                self.events.put(
                    ("finished", f"Download complete. Saved to {destination}")
                )
            else:
                self.events.put(
                    ("failed", "Download failed. See the output above for details.")
                )
        except OSError as error:
            self.events.put(("failed", f"Could not start yt-dlp: {error}"))
        finally:
            self.process = None

    def cancel_download(self):
        if not self.running:
            return

        self.cancel_requested = True
        self.status.set("Cancelling…")
        self.cancel_button.configure(state="disabled")

        if self.process is not None and self.process.poll() is None:
            self._terminate_process(self.process)

    @staticmethod
    def _terminate_process(process):
        try:
            if os.name == "posix":
                os.killpg(process.pid, signal.SIGTERM)
            else:
                process.terminate()
        except OSError:
            pass

    def _process_events(self):
        try:
            while True:
                event, message = self.events.get_nowait()
                if event == "output":
                    self._append_output(message)
                elif event == "finished":
                    self._finish_download(message)
                elif event == "failed":
                    self._finish_download(message, failed=True)
        except queue.Empty:
            pass
        self.root.after(100, self._process_events)

    def _finish_download(self, message, failed=False):
        self._append_output(f"\n{message}\n")
        self.status.set("Download failed" if failed else message)
        self._set_running(False)
        if failed:
            messagebox.showerror("Download failed", message)

    def _set_running(self, running):
        self.running = running
        field_state = "disabled" if running else "normal"

        for widget in (
            self.url_entry,
            self.destination_entry,
            self.browse_button,
            self.playlist_check,
            self.cookies_check,
        ):
            widget.configure(state=field_state)

        self.download_button.configure(state="disabled" if running else "normal")
        self.cancel_button.configure(state="normal" if running else "disabled")

        if running:
            self.status.set("Downloading…")
            self.progress.start(10)
        else:
            self.progress.stop()

    def _append_output(self, text):
        self.output.configure(state="normal")
        self.output.insert("end", text)
        self.output.see("end")
        self.output.configure(state="disabled")

    def _clear_output(self):
        self.output.configure(state="normal")
        self.output.delete("1.0", "end")
        self.output.configure(state="disabled")

    def close(self):
        if self.running:
            should_close = messagebox.askyesno(
                "Download in progress",
                "Cancel the current download and close the application?",
            )
            if not should_close:
                return
            self.cancel_download()
        self.root.destroy()


def main():
    root = tk.Tk()
    YouTubeDownloaderApp(root)
    root.mainloop()
