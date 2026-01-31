import os
import sys
from pathlib import Path
import yt_dlp
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TDRC, TPE2

class UniversalDownloader:
    def __init__(self, output_dir="downloads"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        # FFmpeg !!!!
        self.ffmpeg_path = r"C:\ffmpeg\bin"
        self.check_ffmpeg()
        
    def check_ffmpeg(self):
        exe_path = os.path.join(self.ffmpeg_path, "ffmpeg.exe")
        if os.path.exists(exe_path):
            print(f"✅ FFmpeg doğrulandı: {exe_path}")
        else:
            print("FFmpeg bulunamadı!")
            print(f"Lütfen 'ffmpeg.exe' dosyasının şu klasörde olduğundan emin olun: {self.ffmpeg_path}")
            print("FFmpeg olmazsa videolar SESSİZ iner.")
        
    def get_common_opts(self):
        opts = {
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'en-us,en;q=0.5',
            },
            'nocheckcertificate': True,
            'ignoreerrors': True,
            'no_warnings': True,
            'ffmpeg_location': self.ffmpeg_path
        }
        return opts

    def download_video(self, url, quality="1080", is_playlist=False):
        outtmpl = str(self.output_dir / '%(title)s [%(id)s].%(ext)s')
        if is_playlist:
            outtmpl = str(self.output_dir / '%(playlist)s' / '%(playlist_index)s - %(title)s [%(id)s].%(ext)s')
            
        ydl_opts = self.get_common_opts()
        
        ydl_opts.update({
            'format': f'bestvideo[height<={quality}]+bestaudio/best[height<={quality}]/best',
            'outtmpl': outtmpl,
            'writeinfojson': False,
            'writesubtitles': False,
            'geo_bypass': True,
        })
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"\nİndiriliyor (Max {quality}p)...")
                ydl.download([url])
                return True
        except Exception as e:
            print(f"Hata: {str(e)}")
            return False
            
    def download_mp3(self, url, quality="192", is_playlist=False):
        outtmpl = str(self.output_dir / '%(title)s.%(ext)s')
        if is_playlist:
            outtmpl = str(self.output_dir / '%(playlist)s' / '%(playlist_index)s - %(title)s.%(ext)s')
            
        ydl_opts = self.get_common_opts()
        ydl_opts.update({
            'format': 'bestaudio/best',
            'outtmpl': outtmpl,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': quality,
            }],
            'writethumbnail': True,
        })
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if 'entries' in info:
                    for entry in info['entries']:
                        if entry:
                            self.add_metadata_to_mp3(entry, is_playlist, info.get('title'))
                else:
                    self.add_metadata_to_mp3(info, is_playlist)
                return True
        except Exception as e:
            print(f"Hata: {str(e)}")
            return False
    
    def add_metadata_to_mp3(self, video_info, is_playlist=False, playlist_title=None):
        try:
            safe_title = self.safe_filename(video_info.get('title', 'Unknown'))
            if is_playlist and playlist_title:
                safe_playlist = self.safe_filename(playlist_title)
                base_path = self.output_dir / safe_playlist
                mp3_filename = f"{video_info.get('playlist_index', 1):02d} - {safe_title}.mp3"
                thumb_base = f"{video_info.get('playlist_index', 1):02d} - {safe_title}"
            else:
                base_path = self.output_dir
                mp3_filename = f"{safe_title}.mp3"
                thumb_base = safe_title

            mp3_path = base_path / mp3_filename
            
            actual_thumbnail = None
            for ext in ['.webp', '.jpg', '.png', '.jpeg']:
                check_path = base_path / (thumb_base + ext)
                if check_path.exists():
                    actual_thumbnail = check_path
                    break
            
            if not mp3_path.exists(): return
            
            audio = MP3(str(mp3_path), ID3=ID3)
            try: audio.add_tags()
            except: pass
            
            audio.tags.add(TIT2(encoding=3, text=video_info.get('title', 'Unknown')))
            audio.tags.add(TPE1(encoding=3, text=video_info.get('uploader', 'Unknown')))
            
            if actual_thumbnail:
                with open(actual_thumbnail, 'rb') as img:
                    mime = 'image/jpeg' if actual_thumbnail.suffix in ['.jpg', '.jpeg'] else 'image/png'
                    audio.tags.add(APIC(encoding=3, mime=mime, type=3, desc='Cover', data=img.read()))
                try: actual_thumbnail.unlink()
                except: pass
            audio.save()
        except Exception:
            pass
    
    def safe_filename(self, filename):
        return "".join([c if c.isalnum() or c in " .-_" else "-" for c in filename]).strip()[:100]

    def get_info_quiet(self, url):
        try:
            with yt_dlp.YoutubeDL({'quiet': True, 'extract_flat': True, **self.get_common_opts()}) as ydl:
                return ydl.extract_info(url, download=False)
        except:
            return None

def get_video_quality():
    while True:
        print("\nVideo Kalitesi Seçin:")
        print("1. 1080p (Full HD)")
        print("2. 720p (HD)")
        print("3. 480p (SD)")
        print("4. En Yüksek (Ne varsa)")
        choice = input("Seçiminiz (1-4): ").strip()
        if choice == '1': return '1080'
        elif choice == '2': return '720'
        elif choice == '3': return '480'
        elif choice == '4': return '2160'
        print("Geçersiz seçim.")

def get_audio_quality():
    while True:
        print("\nSes Kalitesi Seçin:")
        print("1. 320 kbps (Yüksek)")
        print("2. 192 kbps (Standart)")
        print("3. 128 kbps (Düşük)")
        choice = input("Seçiminiz (1-3): ").strip()
        if choice == '1': return '320'
        elif choice == '2': return '192'
        elif choice == '3': return '128'
        print("Geçersiz seçim.")

def main():
    downloader = UniversalDownloader()
    print("=" * 60)
    print("   X, İnsta, Youtube Video ve Ses İndirici")
    print("=" * 60)
    
    while True:
        url = input("\nURL yapıştır (Çıkış için 'q'): ").strip()
        if url.lower() == 'q': break
        if not url: continue
            
        print("Bilgi alınıyor...")
        info = downloader.get_info_quiet(url)
        title = info.get('title', 'Bilinmeyen Başlık') if info else "Video"
        print(f"\nBulunan: {title}")
        
        print("\nNe indirmek istersiniz?")
        print("1. Video (MP4)")
        print("2. Ses (MP3)")
        format_choice = input("Seçim (1 veya 2): ").strip()
        
        if format_choice == '2':
            quality = get_audio_quality()
            print(f"MP3 olarak indiriliyor ({quality} kbps)...")
            downloader.download_mp3(url, quality)
        else:
            quality = get_video_quality()
            print(f"Video olarak indiriliyor (Max {quality}p)...")
            downloader.download_video(url, quality)
            
        print("İşlem tamamlandı.")

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass
    except Exception as e: print(f"Hata: {e}")