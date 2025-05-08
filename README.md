# YouTube Downloader

A terminal-based YouTube downloader built using `yt-dlp`, designed specifically for Termux on Android. Features video/audio download, interactive search, resolution selection, thumbnail preview, and download logs.

## Features

- Works seamlessly on Android Termux
- Search YouTube and pick videos interactively
- Download video, audio, or both
- Select preferred resolution and quality
- Supports playlists
- View thumbnails in ASCII or with image viewers
- Logs all downloads with size and format
- Optional toast, vibration, and sound notifications (Termux API)

## Prerequisites

Before running, make sure you have the following installed:

### For Termux (Android)

Run this setup script to install all dependencies:

```bash
pkg update && pkg upgrade -y
pkg install -y python ffmpeg wget curl termux-api jp2a
pip install --upgrade pip
pip install yt-dlp colorama pyfiglet Pillow
```

> Make sure `termux-api` and `termux-api` app are installed from F-Droid or GitHub.

### For Windows (CMD)

1. Install [Python](https://www.python.org/downloads/) and check "Add to PATH".
2. Open Command Prompt and run:

```cmd
pip install yt-dlp colorama pyfiglet Pillow
```

3. (Optional) Download and add [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) to your system PATH.

## How to Use

Simply run the script:

```bash
python youtube_dl_script.py
```

You can either:
- Paste a YouTube URL directly
- Type a keyword to search and select from results

Then:
- Choose download mode: Video, Audio, or Both
- Pick the quality/resolution
- Your file will be saved in `~/storage/downloads/YtVideo` or `/sdcard/Download/YtVideo`
