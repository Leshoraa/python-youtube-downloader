import yt_dlp
import os
import re
import sys
import time
import shutil
import difflib
import urllib.request
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
        # Deteksi jika di Termux (PREFIX khas Termux)
        if "com.termux" in os.environ.get('PREFIX', ''):
            base_dir = "/data/data/com.termux/files/home/storage/downloads"
            target_dir = os.path.join(base_dir, "YtVideo")
        elif os.path.exists("/sdcard/Download"):
            target_dir = os.path.join("/sdcard/Download", "YtVideo")
        else:
            target_dir = os.path.join(os.getcwd(), "YtVideo")
    elif sys.platform.startswith("win"):
        target_dir = os.path.join(os.path.expanduser("~"), "Downloads", "YtVideo")
    else:
        target_dir = os.path.join(os.getcwd(), "YtVideo")
    return target_dir

def download_speed(bytes_per_sec):
    if not bytes_per_sec:
        return ""
    mb = bytes_per_sec / 1024 / 1024
    return f"{mb:.2f}MB/s" if mb >= 1 else f"{bytes_per_sec/1024:.1f}KB/s"

def print_colored_progress_bar(percent, info_str, width=20):
    filled = int(width * percent // 100)
    empty = width - filled
    color = "\033[91m" if percent < 30 else "\033[93m" if percent < 70 else "\033[92m"
    bar = "█" * filled + "░" * empty
    sys.stdout.write(f"\r{color}[{bar}] {percent:5.1f}% | {info_str}\033[0m")
    sys.stdout.flush()

def log_download(title, format_label, size_mb, output_file):
    log_path = os.path.join(get_download_dir(), "download_history.log")
    with open(log_path, "a", encoding="utf-8") as f:
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] {title} - {format_label} - {size_mb:.2f} MB - {output_file}\n")

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
                print('\a', end='')  # Fallback beep
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

def display_ascii_thumbnail(thumbnail_url):
    temp_image = os.path.join(os.path.expanduser("~"), ".cache", "yt_thumb.jpg")
    try:
        os.makedirs(os.path.dirname(temp_image), exist_ok=True)
        urllib.request.urlretrieve(thumbnail_url, temp_image)
        if sys.platform.startswith("linux") and shutil.which("jp2a"):
            os.system(f"jp2a --width=40 --colors --fill {temp_image}")
        else:
            try:
                from PIL import Image
                img = Image.open(temp_image)
                img = img.resize((40, 20))
                img = img.convert("L")
                pixels = img.getdata()
                chars = [" ", "░", "▒", "▓", "█"]
                ascii_img = ""
                for i in range(0, len(pixels), img.width):
                    line = pixels[i:i+img.width]
                    ascii_img += "".join([chars[min(p//51, 4)] for p in line]) + "\n"
                print(ascii_img)
            except:
                print("🖼️ Thumbnail downloaded (no display support)")
    except:
        print("🖼️ Thumbnail available (install jp2a or pillow for preview)")

def download(url, format_id, output_path, is_audio):
    def hook(d):
        if d['status'] == 'downloading':
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            percent = downloaded * 100 / total
            speed_str = download_speed(speed)
            eta_str = f"{eta//60:02}:{eta%60:02}" if eta else "--:--"
            print_colored_progress_bar(percent, f"{speed_str} | ETA {eta_str}")
        elif d['status'] == 'finished':
            print_colored_progress_bar(100, "Done ✓")
            print("\n✅ Download complete!")
            notify_done()

    ydl_opts = {
        'format': format_id,
        'outtmpl': output_path,
        'progress_hooks': [hook],
        'quiet': True,
        'no_warnings': True,
    }

    if not is_audio:
        ydl_opts['merge_output_format'] = 'mp4'

    class QuietLogger:
        def debug(self, msg): pass
        def warning(self, msg): pass
        def error(self, msg): print(msg)

    ydl_opts['logger'] = QuietLogger()

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

def truncate(text, max_length=50):
    return text if len(text) <= max_length else text[:max_length - 3] + "..."

def search_video(query):
    ydl_opts = {"quiet": True, "extract_flat": True}
    ydl = yt_dlp.YoutubeDL(ydl_opts)
    offset = 0
    per_page = 10
    page = 1
    last_lines = 0
    all_results = []

    while True:
        if offset == 0:
            info = ydl.extract_info(f"ytsearch{per_page * 5}:{query}", download=False)
            all_results = info.get("entries", [])
            if not all_results:
                print("\n❌ No results found!")
                return None

            for entry in all_results:
                title = entry.get("title", "").lower()
                query_lower = query.lower()
                title_similarity = difflib.SequenceMatcher(None, query_lower, title).ratio() * 100
                view_count = entry.get("view_count", 0)
                view_score = 100 if view_count >= 1_000_000 else 75 if view_count >= 100_000 else 50 if view_count >= 10_000 else 25
                duration = entry.get("duration", 0)
                duration_score = 100 if duration >= 600 else 75 if duration >= 180 else 50 if duration >= 60 else 25
                entry["relevance_score"] = (0.6 * title_similarity) + (0.3 * view_score) + (0.1 * duration_score)

            all_results = sorted(
                all_results,
                key=lambda x: (-x.get("view_count", 0))
            )

        results = all_results[offset:offset + per_page]

        if last_lines > 0:
            if sys.platform.startswith("win"):
                os.system('cls')
            else:
                os.system('clear')

        header = f"\n{Fore.CYAN}📄 Page {page}{Style.RESET_ALL} — Results for: '{query}'\n"
        print(header)
        total_lines = header.count('\n') + 1

        for i, entry in enumerate(results):
            num = offset + i + 1
            title = (entry.get("title", "Unknown"))[:50] + "..." if len(entry.get("title", "")) > 50 else entry.get("title", "Unknown")
            channel = entry.get("channel", "Unknown")
            duration = time.strftime('%M:%S', time.gmtime(entry.get("duration", 0)))
            view_count = entry.get("view_count", 0)
            relevance_score = entry.get("relevance_score", 0)

            def shorten_views(count):
                if count >= 1_000_000_000:
                    return f"{count/1_000_000_000:.1f}B"
                elif count >= 1_000_000:
                    return f"{count/1_000_000:.1f}M"
                elif count >= 1_000:
                    return f"{count/1_000:.1f}K"
                else:
                    return str(count)

            views_str = shorten_views(view_count)

            print(f"""{Fore.GREEN}┌─{Fore.WHITE} {num}. {title}
{Fore.GREEN}│   {Fore.YELLOW}• {channel}{Style.RESET_ALL}  |  {Fore.MAGENTA}{duration}{Style.RESET_ALL}  |  {Fore.CYAN}{views_str}{Style.RESET_ALL}
{Fore.GREEN}└────────────────────────────{Style.RESET_ALL}""")
            total_lines += 3

        prompt = "🔢 Choose a number"
        if offset >= per_page:
            prompt += ", 'p' for previous"
        if offset + per_page < len(all_results):
            prompt += ", 'n' for next"
        prompt += ": "

        print()
        sel = input(prompt).strip().lower()
        last_lines = total_lines + 2

        if sel == 'n' and offset + per_page < len(all_results):
            offset += per_page
            page += 1
            continue
        elif sel == 'p' and offset >= per_page:
            offset -= per_page
            page -= 1
            continue
        try:
            sel_int = int(sel)
            if offset < sel_int <= offset + len(results):
                return results[sel_int - offset - 1].get("url")
        except ValueError:
            pass

def list_resolutions(url, is_audio):
    ydl = yt_dlp.YoutubeDL({"quiet": True})
    info = ydl.extract_info(url, download=False)

    entries = info.get("entries")
    if entries:
        print("\n📺 Playlist detected!")
        for i, entry in enumerate(entries):
            print(f"{i+1}. {entry.get('title', 'Unknown')}")
        sel = input("\n🔢 Select video number from playlist: ").strip()
        try:
            sel = int(sel) - 1
            info = entries[sel]
        except:
            print("❌ Invalid selection!")
            return None, []

    formats = info.get('formats', [])
    listed = []

    if is_audio:
        audio_formats = [f for f in formats if f.get('vcodec') == 'none' and f.get('acodec') != 'none' and f.get('filesize')]
        printed = set()
        sorted_audio_formats = sorted(audio_formats, key=lambda x: (x.get('abr', 0), x.get('filesize', 0)), reverse=True)
        print("\n🎵 Available Audio Qualities:\n")
        index = 1
        for fmt in sorted_audio_formats:
            abr = fmt.get('abr', 0)
            size = fmt.get('filesize', 0)
            key = (abr, round(size / 1024 / 1024, 1))
            if key in printed:
                continue
            printed.add(key)
            label = f"{abr:.0f}kbps - {key[1]} MB"
            print(f"{index}. {label}")
            listed.append((fmt['format_id'], label, key[1]))
            index += 1
    else:
        video_formats = [
            f for f in formats 
            if f.get('vcodec') != 'none' and f.get('filesize')
        ]


        printed_res = set()
        sorted_video_formats = sorted(video_formats, key=lambda x: x.get('height', 0), reverse=True)
        print("\n📐 Available Video Resolutions:\n")
        index = 1
        for fmt in sorted_video_formats:
            height = fmt.get('height', 0)
            if height in printed_res:
                continue
            printed_res.add(height)
            size = fmt.get('filesize', 0)
            fmt_id = fmt.get('format_id')
            label = f"{height}p - {round(size / 1024 / 1024, 1)} MB"
            print(f"{index}. {label}")
            listed.append((f"{fmt_id}+bestaudio", label, size / 1024 / 1024))
            index += 1

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
            _, audio_formats = list_resolutions(raw, True)
            if not audio_formats:
                print("❌ No audio formats available!")
                continue
            audio_choice = input("\n🎯 Select audio number: ").strip()
            try:
                audio_idx = int(audio_choice) - 1
                audio_format_id, audio_label, audio_size = audio_formats[audio_idx]
            except:
                print("❌ Invalid audio selection!")
                continue
    
            video_file = os.path.join(download_dir, safe_title + "_video.mp4")
            audio_file = os.path.join(download_dir, safe_title + "_audio.mp3")
    
            print(f"\n🚀 Downloading video to: \033[92m{video_file}\033[0m")
            download(raw, selected_format_id, video_file, False)
            log_download(title, label + " (video)", size_mb, video_file)
    
            print(f"\n🎧 Downloading audio to: \033[92m{audio_file}\033[0m")
            download(raw, audio_format_id, audio_file, True)
            log_download(title, audio_label + " (audio)", audio_size, audio_file)
    
        elif mode == '1':
            output_file = os.path.join(download_dir, safe_title + ".mp4")
            print(f"\n🚀 Saving to: \033[92m{output_file}\033[0m")
            download(raw, selected_format_id, output_file, False)
            log_download(title, label, size_mb, output_file)
    
        elif mode == '2':
            output_file = os.path.join(download_dir, safe_title + ".mp3")
            print(f"\n🚀 Saving to: \033[92m{output_file}\033[0m")
            download(raw, selected_format_id, output_file, True)
            log_download(title, label, size_mb, output_file)
    
        again = input("\n🔁 Download again? (y/n): ").lower().strip()
        if again != 'y':
            print("\n👋 Goodbye!")
            break
