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

### For Termux (Android)

Make sure you have Termux and Termux:API installed (from F-Droid or GitHub). Then run this setup script to install all dependencies:

```bash
pkg update && pkg upgrade -y
pkg install -y python ffmpeg wget curl termux-api jp2a git
pip install --upgrade pip
pip install yt-dlp colorama pyfiglet Pillow
```

### For Windows (CMD)

1. Install [Python](https://www.python.org/downloads/) and check "Add to PATH".
2. Open Command Prompt and run:

```cmd
pip install yt-dlp colorama pyfiglet Pillow
```

3. (Optional) Download and add [FFmpeg](https://www.gyan.dev/ffmpeg/builds/) to your system PATH.

## How to Use

### Clone the Repository

In Termux:

```bash
git clone https://github.com/Leshoraa/python-youtube-downloader.git
cd python-youtube-downloader
python yt_downloader.py
```

Or in CMD (Windows):

```bash
git clone https://github.com/Leshoraa/python-youtube-downloader.git
cd python-youtube-downloader
python yt_downloader.py
```

### Usage Flow

1. Paste a YouTube URL or search with keywords
2. Choose:
   - Download mode: Video, Audio, or Both
   - Preferred quality/resolution
3. The file will be saved to:
   - `~/storage/downloads/YtVideo` (Android Termux)
   - or `/sdcard/Download/YtVideo` (Termux without storage binding)
   - `C:\Users\YourName\Downloads\YtVideo` (PC)
