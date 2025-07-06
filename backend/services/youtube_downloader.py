import os
import tempfile
import shutil
from typing import Dict, Optional, Tuple
from pathlib import Path
import yt_dlp
import re
from datetime import datetime

class YouTubeDownloader:
    def __init__(self, temp_dir: str = None):
        """
        Initialize YouTube video downloader
        
        Args:
            temp_dir: Temporary file storage directory (uses system temp dir if None)
        """
        self.temp_dir = temp_dir or tempfile.gettempdir()
        self.download_dir = os.path.join(self.temp_dir, "promptsnap_downloads")
        
        # Create download directory
        os.makedirs(self.download_dir, exist_ok=True)
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """
        Extract video ID from YouTube URL
        
        Args:
            url: YouTube URL
            
        Returns:
            Video ID or None
        """
        patterns = [
            r'(?:youtube\.com\/(?:[^\/]+\/.+\/|(?:v|e(?:mbed)?)\/|.*[?&]v=)|youtu\.be\/)([^"&?\/\s]{11})',
            r'youtube\.com\/shorts\/([^"&?\/\s]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        
        return None
    
    def validate_url(self, url: str) -> Tuple[bool, str]:
        """
        Validate YouTube URL
        
        Args:
            url: URL to validate
            
        Returns:
            (is_valid, message)
        """
        if not url:
            return False, "URL is empty."
        
        video_id = self.extract_video_id(url)
        if not video_id:
            return False, "Invalid YouTube URL."
        
        return True, "Valid URL."
    
    def _get_format_selector(self, quality: str) -> str:
        """
        Get format selector based on quality setting
        
        Args:
            quality: Quality setting
            
        Returns:
            yt-dlp format selector
        """
        # YouTube format ID based selection (automatic video+audio merging)
        quality_formats = {
            'worst': 'worst[ext=mp4]+worst[ext=m4a]/worst',
            'best': 'best[ext=mp4]+best[ext=m4a]/best',
            '144p': '160+139/160+140/best[height<=144]',  # 144p video + audio
            '240p': '133+139/133+140/best[height<=240]',  # 240p video + audio  
            '360p': '134+139/134+140/best[height<=360]',  # 360p video + audio
            '480p': '135+139/135+140/best[height<=480]',  # 480p video + audio
            '720p': '136+139/136+140/best[height<=720]',  # 720p video + audio
            '1080p': '137+139/137+140/best[height<=1080]', # 1080p video + audio
        }
        
        return quality_formats.get(quality, 'best[ext=mp4]+best[ext=m4a]/best')
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video information only (without downloading)
        
        Args:
            url: YouTube URL
            
        Returns:
            Video information dictionary or None
        """
        try:
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description', '')[:200] + '...',  # Description up to 200 chars
                    'thumbnail': info.get('thumbnail'),
                }
                
        except Exception as e:
            print(f"Failed to extract video information: {str(e)}")
            return None
    
    def download_video(self, url: str, quality: str = 'best') -> Optional[Dict]:
        """
        Download YouTube video
        
        Args:
            url: YouTube URL
            quality: Video quality ('best', 'worst', '720p', '480p', etc.)
            
        Returns:
            Download information dictionary or None
        """
        try:
            # Validate URL
            is_valid, message = self.validate_url(url)
            if not is_valid:
                raise ValueError(message)
            
            video_id = self.extract_video_id(url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{video_id}_{timestamp}"
            
            # Configure yt-dlp options
            format_selector = self._get_format_selector(quality)
            ydl_opts = {
                'format': format_selector,
                'outtmpl': os.path.join(self.download_dir, f'{filename}.%(ext)s'),
                'writeinfojson': False,  # Disable JSON file saving (saves space)
                'writethumbnail': False,  # Disable thumbnail saving (saves space)
                'extractaudio': False,
                'audioformat': 'mp3',
                'merge_output_format': 'mp4',  # Unify output format to mp4
                'quiet': False,  # Enable logs for debugging
                'no_warnings': False,
            }
            
            print(f"Starting video download: {url}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                # Extract video information
                info = ydl.extract_info(url, download=False)
                
                # Execute actual download
                ydl.download([url])
                
                # Find downloaded files
                downloaded_files = []
                for file in os.listdir(self.download_dir):
                    if file.startswith(filename):
                        downloaded_files.append(os.path.join(self.download_dir, file))
                
                # Find video file
                video_file = None
                for file in downloaded_files:
                    if file.endswith(('.mp4', '.mkv', '.webm', '.avi')):
                        video_file = file
                        break
                
                if not video_file:
                    raise Exception("Downloaded video file not found.")
                
                result = {
                    'video_id': video_id,
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'file_path': video_file,
                    'file_size': os.path.getsize(video_file),
                    'downloaded_files': downloaded_files,
                    'download_time': datetime.now().isoformat(),
                }
                
                print(f"Download complete: {video_file}")
                return result
                
        except Exception as e:
            print(f"Download failed: {str(e)}")
            return None
    
    def cleanup_file(self, file_path: str) -> bool:
        """
        Delete a single file
        
        Args:
            file_path: Path of file to delete
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                print(f"File deleted: {file_path}")
                return True
            return False
        except Exception as e:
            print(f"File deletion failed: {str(e)}")
            return False
    
    def cleanup_download(self, download_info: Dict) -> bool:
        """
        Clean up downloaded files
        
        Args:
            download_info: Download information dictionary
            
        Returns:
            True if successful, False otherwise
        """
        try:
            success_count = 0
            
            # Delete all downloaded files
            for file_path in download_info.get('downloaded_files', []):
                if self.cleanup_file(file_path):
                    success_count += 1
            
            print(f"Cleanup complete: {success_count} files deleted")
            return success_count > 0
            
        except Exception as e:
            print(f"Cleanup failed: {str(e)}")
            return False
    
    def cleanup_all(self) -> bool:
        """
        Clean up all files in download directory
        
        Returns:
            True if successful, False otherwise
        """
        try:
            if os.path.exists(self.download_dir):
                shutil.rmtree(self.download_dir)
                os.makedirs(self.download_dir, exist_ok=True)
                print(f"All files in download directory cleaned up")
                return True
            return False
        except Exception as e:
            print(f"Complete cleanup failed: {str(e)}")
            return False

# Create global instance
youtube_downloader = YouTubeDownloader()

# Convenience functions
def download_youtube_video(url: str, quality: str = 'best') -> Optional[Dict]:
    return youtube_downloader.download_video(url, quality)

def get_youtube_info(url: str) -> Optional[Dict]:
    return youtube_downloader.get_video_info(url)

def validate_youtube_url(url: str) -> Tuple[bool, str]:
    return youtube_downloader.validate_url(url) 