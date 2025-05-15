import yt_dlp, os, re, sys, time, shutil, difflib, urllib.request
from colorama import Fore, Style
try:
    from pyfiglet import Figlet
    has_figlet = True
except ImportError:
    has_figlet = False

def sanitize_filename(filename):
    return re.sub(r'[<>:"/\\|?*\0-\x1f]', "", filename).strip().lstrip(".")

def get_download_dir():
    if sys.platform.startswith("linux"):
        if "com.termux" in os.environ.get('PREFIX', ''):
            base_dir = "/data/data/com.termux/files/home/storage/downloads"
            return os.path.join(base_dir, "YtVideo")
        elif os.path.exists("/sdcard/Download"):
            return os.path.join("/sdcard/Download", "YtVideo")
    elif sys.platform.startswith("win"):
        return os.path.join(os.path.expanduser("~"), "Downloads", "YtVideo")
    return os.path.join(os.getcwd(), "YtVideo")

def download_speed(bps):
    return f"{bps/1024/1024:.2f}MB/s" if bps >= 1024*1024 else f"{bps/1024:.1f}KB/s"

def print_colored_progress_bar(percent, info, width=20):
    filled = int(width * percent // 100)
    color = "\033[91m" if percent < 30 else "\033[93m" if percent < 70 else "\033[92m"
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r{color}[{bar}] {percent:5.1f}% | {info}\033[0m")
    sys.stdout.flush()

def log_download(title, format_label, size_mb, output_file):
    path = os.path.join(get_download_dir(), "download_history.log")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {title} - {format_label} - {size_mb:.2f} MB - {output_file}\n")

def notify_done():
    try:
        if sys.platform.startswith("linux"):
            if shutil.which("termux-toast"):
                os.system('termux-toast -g bottom -b green "✅ Download Complete!"')
            if shutil.which("termux-vibrate"):
                os.system('termux-vibrate -d 100')
            if shutil.which("termux-media-player"):
                os.system('termux-media-player play /system/media/audio/ui/Effect_Tick.ogg')
            else:
                print('\a', end='')
        elif sys.platform.startswith("win"):
            try:
                import winsound
                winsound.Beep(1000, 300)
            except:
                try:
                    from playsound import playsound
                    playsound("C:\\Windows\\Media\\notify.wav")
                except:
                    print('\a', end='')
        else:
            print('\a', end='')
    except:
        print('\a', end='')

def display_ascii_thumbnail(url):
    temp = os.path.join(os.path.expanduser("~"), ".cache", "yt_thumb.jpg")
    try:
        os.makedirs(os.path.dirname(temp), exist_ok=True)
        urllib.request.urlretrieve(url, temp)
        if sys.platform.startswith("linux") and shutil.which("jp2a"):
            os.system(f"jp2a --width=40 --colors --fill {temp}")
        else:
            try:
                from PIL import Image
                img = Image.open(temp).resize((40, 20)).convert("L")
                pixels = img.getdata()
                chars = [" ", "░", "▒", "▓", "█"]
                ascii_img = ""
                for i in range(0, len(pixels), img.width):
                    ascii_img += "".join([chars[min(p//51, 4)] for p in pixels[i:i+img.width]]) + "\n"
                print(ascii_img)
            except:
                print("🖼️ Thumbnail downloaded (no display support)")
    except:
        print("🖼️ Thumbnail available (install jp2a or pillow for preview)")

def download(url, format_id, path, is_audio, download_type=""):
    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            percent = d.get('downloaded_bytes', 0) * 100 / total
            speed = download_speed(d.get('speed', 0))
            eta = d.get('eta', 0)
            eta_str = f"{eta//60:02}:{eta%60:02}" if eta else "--:--"
            print_colored_progress_bar(percent, f"{speed} | ETA {eta_str}")
        elif d['status'] == 'finished':
            print_colored_progress_bar(100, "Done ✓")
            print(f"\n✅ {'Merged video & audio' if download_type=='merge' else 'Audio download' if download_type=='audio' else 'Video downloaded — merging with audio' if download_type=='video' else 'Download'} complete!")
            notify_done()

    opts = {
        'format': format_id,
        'outtmpl': path,
        'progress_hooks': [hook],
        'no_warnings': True,
        'logger': type('Logger', (), {'debug': lambda *_: None, 'warning': lambda *_: None, 'info': print, 'error': print})()
    }

    if is_audio:
        opts.update({'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}], 'extractaudio': True, 'keepvideo': False})
    else:
        opts['postprocessors'] = [{'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'}]

    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])

def truncate(text, max_len=50):
    return text if len(text) <= max_len else text[:max_len - 3] + "..."

def search_video(query):
    ydl = yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True})
    offset, per_page, page, last_lines = 0, 10, 1, 0
    all_results = []

    while True:
        if offset == 0:
            info = ydl.extract_info(f"ytsearch{per_page * 5}:{query}", download=False)
            all_results = info.get("entries", [])
            if not all_results:
                print("\n❌ No results found!")
                return None
            for e in all_results:
                ts = difflib.SequenceMatcher(None, query.lower(), e.get("title", "").lower()).ratio() * 100
                vs = 100 if e.get("view_count", 0) >= 1_000_000 else 75 if e.get("view_count", 0) >= 100_000 else 50 if e.get("view_count", 0) >= 10_000 else 25
                ds = 100 if e.get("duration", 0) >= 600 else 75 if e.get("duration", 0) >= 180 else 50 if e.get("duration", 0) >= 60 else 25
                e["relevance_score"] = 0.6 * ts + 0.3 * vs + 0.1 * ds
            all_results.sort(key=lambda x: -x.get("view_count", 0))

        results = all_results[offset:offset + per_page]

        if last_lines > 0:
            os.system('cls' if sys.platform.startswith("win") else 'clear')

        print(f"\n{Fore.CYAN}📄 Page {page}{Style.RESET_ALL} — Results for: '{query}'\n")
        for i, e in enumerate(results):
            n = offset + i + 1
            title = (e.get("title", "")[:50] + "...") if len(e.get("title", "")) > 50 else e.get("title", "")
            channel = e.get("channel", "Unknown")
            duration = time.strftime('%M:%S', time.gmtime(e.get("duration", 0)))
            vc = e.get("view_count", 0)
            views = f"{vc/1_000_000_000:.1f}B" if vc >= 1_000_000_000 else f"{vc/1_000_000:.1f}M" if vc >= 1_000_000 else f"{vc/1_000:.1f}K" if vc >= 1_000 else str(vc)
            print(f"""{Fore.GREEN}┌─{Fore.WHITE} {n}. {title}
{Fore.GREEN}│   {Fore.YELLOW}• {channel}{Style.RESET_ALL}  |  {Fore.MAGENTA}{duration}{Style.RESET_ALL}  |  {Fore.CYAN}{views}{Style.RESET_ALL}
{Fore.GREEN}└────────────────────────────{Style.RESET_ALL}""")

        sel = input("\n🔢 Choose a number" + (", 'p' for previous" if offset >= per_page else "") + (", 'n' for next" if offset + per_page < len(all_results) else "") + ": ").strip().lower()
        last_lines = len(results) * 3 + 3

        if sel == 'n' and offset + per_page < len(all_results):
            offset += per_page; page += 1; continue
        elif sel == 'p' and offset >= per_page:
            offset -= per_page; page -= 1; continue
        try:
            sel_int = int(sel)
            if offset < sel_int <= offset + len(results):
                return results[sel_int - offset - 1].get("url")
        except:
            pass

def list_resolutions(url, is_audio):
    ydl = yt_dlp.YoutubeDL({"quiet": True})
    info = ydl.extract_info(url, download=False)

    entries = info.get("entries")
    if entries:
        print("\n📺 Playlist detected!")
        for i, e in enumerate(entries):
            print(f"{i+1}. {e.get('title', 'Unknown')}")
        try:
            info = entries[int(input("\n🔢 Select video number from playlist: ").strip()) - 1]
        except:
            print("❌ Invalid selection!")
            return None, []

    formats, listed = info.get('formats', []), []

    if is_audio:
        af = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and f.get('filesize')]
        print("\n🎵 Available Audio Qualities:\n")
        printed = set()
        for i, f in enumerate(sorted(af, key=lambda x: (x.get('abr', 0), x.get('filesize', 0)), reverse=True), 1):
            k = (f.get('abr', 0), round(f.get('filesize', 0) / 1024 / 1024, 1))
            if k in printed: continue
            printed.add(k)
            label = f"{k[0]:.0f}kbps - {k[1]} MB"
            print(f"{i}. {label}")
            listed.append((f['format_id'], label, k[1]))
    else:
        vf = [f for f in formats if f.get('vcodec') != 'none' and f.get('filesize')]
        print("\n📐 Available Video Resolutions:\n")
        printed = set()
        for i, f in enumerate(sorted(vf, key=lambda x: x.get('height', 0), reverse=True), 1):
            h = f.get('height', 0)
            if h in printed: continue
            printed.add(h)
            size = f.get('filesize', 0)
            label = f"{h}p - {round(size / 1024 / 1024, 1)} MB"
            print(f"{i}. {label}")
            listed.append((f"{f.get('format_id')}+bestaudio", label, size / 1024 / 1024))

    return info.get('title', 'video'), listed

if __name__ == "__main__":
    while True:
        print("\n\033[95m" + "=" * 34)
        print("       📹 YouTube Downloader       ")
        print("=" * 34 + "\033[0m")
    
        raw = input("\n📋 Paste URL or search video: ").strip()
        if not raw:
            continue
        if not re.match(r'^https?://', raw):
            raw = search_video(raw)
            if not raw:
                continue
    
        ydl = yt_dlp.YoutubeDL({"quiet": True})
        info = ydl.extract_info(raw, download=False)
        thumbnail_url = info.get("thumbnail")
        if thumbnail_url:
            print()
            display_ascii_thumbnail(thumbnail_url)
        print(f"\n🎬 Title: \033[96m{info.get('title', 'Unknown')}\033[0m\n")
    
        mode = input(
            "🎵 Choose mode:\n\n"
            "1. Video 🎞️\n"
            "2. Audio 🎧\n"
            "3. Video & Audio 🔄\n"
            "4. Cancel ❌\n\n"
            "➤ Choice (1/2/3/4): "
        ).strip()
    
        if mode == '4':
            continue
    
        if mode not in ['1', '2', '3']:
            print("❌ Invalid choice!")
            continue
    
        is_audio = mode == '2'
        result = list_resolutions(raw, is_audio if mode != '3' else False)
        if not result:
            continue
        title, formats = result
        if not formats:
            continue
    
        choice = input("\n🎯 Select video number: ").strip()
        try:
            idx = int(choice) - 1
            selected_format_id, label, size_mb = formats[idx]
        except:
            print("❌ Invalid video selection!")
            continue
    
        download_dir = get_download_dir()
        os.makedirs(download_dir, exist_ok=True)
        safe_title = sanitize_filename(title)
    
        if mode == '3':
            print("\n🔎 Fetching audio quality list...")
            audio_formats = [f for f in info['formats'] if f.get('vcodec') == 'none' and f.get('acodec') != 'none']
            if not audio_formats:
                print("❌ No audio formats available!")
                continue

            # Sort berdasarkan bitrate
            sorted_audio = sorted(audio_formats, key=lambda x: (
                x.get('abr') or 0,
                x.get('filesize') or 0
            ), reverse=True)
            
            # Print list
            audio_list = []
            printed = set()
            print("\n🎵 Available Audio Qualities:\n")
            for idx, fmt in enumerate(sorted_audio, 1):
                if not fmt.get("format_id") or not fmt.get("abr"):
                    continue
                abr = fmt.get("abr")
                size = fmt.get("filesize", 0) or 0
                key = (abr, round(size / 1024 / 1024, 1)) if size else (abr, "Unknown")
                if key in printed:
                    continue
                printed.add(key)
                label = f"{abr:.0f}kbps - {key[1]} MB" if isinstance(key[1], (int, float)) else f"{abr:.0f}kbps - size unknown"
                print(f"{idx}. {label}")
                audio_list.append((fmt["format_id"], label, key[1] if isinstance(key[1], (int, float)) else 0))

            # Pilih audio
            audio_choice = input("\n🎯 Select audio number: ").strip()
            try:
                audio_idx = int(audio_choice) - 1
                audio_format_id, audio_label, audio_size = audio_list[audio_idx]
            except:
                print("❌ Invalid audio selection!")
                continue

            # Path file
            video_file = os.path.join(download_dir, safe_title + "_video.mp4")
            audio_file = os.path.join(download_dir, safe_title + "_audio.mp3")

            # Download
            print(f"\n🚀 Downloading video to: \033[92m{video_file}\033[0m")
            download(raw, selected_format_id, video_file, False, download_type="video")
            log_download(title, label + " (video)", size_mb, video_file)

            print(f"\n🎧 Downloading audio to: \033[92m{audio_file}\033[0m")
            download(raw, audio_format_id, audio_file, True, download_type="merge")
            log_download(title, audio_label + " (audio)", audio_size, audio_file)

        elif mode == '1':
            output_file = os.path.join(download_dir, safe_title + ".mp4")
            print(f"\n🚀 Saving to: \033[92m{output_file}\033[0m")
            download(raw, selected_format_id, output_file, False, download_type="video")
            log_download(title, label, size_mb, output_file)
    
        elif mode == '2':
            output_file = os.path.join(download_dir, safe_title + ".mp3")
            print(f"\n🚀 Saving to: \033[92m{output_file}\033[0m")
            download(raw, selected_format_id, output_file, True, download_type="audio")
            log_download(title, label, size_mb, output_file)
    
        again = input("\n🔁 Download again? (y/n): ").lower().strip()
        if again != 'y':
            print("\n👋 Goodbye!")
            break
