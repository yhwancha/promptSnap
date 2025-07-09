import os
import tempfile
import shutil
from typing import Dict, Optional, Tuple
from pathlib import Path
import yt_dlp
import re
from datetime import datetime
import time

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
        
        # Check server environment
        self._check_server_environment()
    
    def _check_server_environment(self) -> None:
        """
        Check server environment for potential issues
        """
        try:
            # Check if download directory is writable
            test_file = os.path.join(self.download_dir, "test_write.tmp")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            
            # Check available disk space (at least 100MB)
            import shutil
            free_space = shutil.disk_usage(self.download_dir).free
            if free_space < 100 * 1024 * 1024:  # 100MB
                print(f"Warning: Low disk space ({free_space / 1024 / 1024:.1f}MB available)")
                
        except Exception as e:
            print(f"Warning: Server environment check failed: {str(e)}")
    
    def _is_server_environment(self) -> bool:
        """
        Detect if running in a server environment
        
        Returns:
            True if likely running on a server
        """
        # Check common server environment indicators
        server_indicators = [
            os.getenv('RENDER'),  # Render.com
            os.getenv('HEROKU'),  # Heroku
            os.getenv('VERCEL'),  # Vercel
            os.getenv('NETLIFY'), # Netlify
            os.getenv('AWS_LAMBDA_FUNCTION_NAME'),  # AWS Lambda
            os.getenv('RAILWAY_ENVIRONMENT'),  # Railway
            os.getenv('DYNO'),  # Heroku dyno
        ]
        
        return any(indicator for indicator in server_indicators)
    
    def _get_safe_ydl_opts(self) -> Dict:
        """
        Get safe yt-dlp options for server environments
        
        Returns:
            Safe yt-dlp options dictionary
        """
        return {
            # Basic settings
            'quiet': False,
            'no_warnings': False,
            
            # Simple user agent to avoid bot detection
            'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            
            # Very conservative retry settings for server environments
            'retries': 1,
            'fragment_retries': 1,
            
            # Shorter timeout to avoid hanging
            'socket_timeout': 15,
            
            # Format preferences - prefer simpler formats
            'format_sort': ['res', 'ext:mp4:m4a'],
            
            # Avoid complex features that might be blocked
            'extract_flat': False,
            'ignoreerrors': False,
            
            # YouTube specific - use most basic settings
            'youtube_include_dash_manifest': False,
            'youtube_skip_dash_manifest': True,
            
            # Disable features that might cause issues on servers
            'writeinfojson': False,
            'writethumbnail': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            
            # Server-friendly settings
            'no_color': True,
            'no_call_home': True,
            'prefer_insecure': False,
            
            # Rate limiting to be server-friendly
            'sleep_interval': 1,
            'max_sleep_interval': 5,
        }
    
    def _try_simple_download(self, url: str, quality: str = 'best') -> Optional[Dict]:
        """
        Try the most basic download approach for server environments
        
        Args:
            url: YouTube URL
            quality: Video quality
            
        Returns:
            Download information or None
        """
        try:
            print("Trying simple download approach...")
            
            video_id = self.extract_video_id(url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{video_id}_{timestamp}_simple"
            
            # Most basic yt-dlp options
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': os.path.join(self.download_dir, f'{filename}.%(ext)s'),
                'quiet': True,
                'no_warnings': True,
                'writeinfojson': False,
                'writethumbnail': False,
                'user_agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'socket_timeout': 10,
                'retries': 0,
                'fragment_retries': 0,
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                ydl.download([url])
                
                # Find downloaded file
                for file in os.listdir(self.download_dir):
                    if file.startswith(filename):
                        file_path = os.path.join(self.download_dir, file)
                        return {
                            'video_id': video_id,
                            'title': info.get('title'),
                            'duration': info.get('duration'),
                            'file_path': file_path,
                            'file_size': os.path.getsize(file_path),
                            'downloaded_files': [file_path],
                            'download_time': datetime.now().isoformat(),
                            'method': 'simple'
                        }
            
            return None
            
        except Exception as e:
            print(f"Simple download failed: {str(e)}")
            return None
    
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
        # Simplified format selection for better compatibility
        quality_formats = {
            'worst': 'worst[ext=mp4]',
            'best': 'best[ext=mp4]',
            '144p': 'best[height<=144][ext=mp4]',
            '240p': 'best[height<=240][ext=mp4]',
            '360p': 'best[height<=360][ext=mp4]',
            '480p': 'best[height<=480][ext=mp4]',
            '720p': 'best[height<=720][ext=mp4]',
            '1080p': 'best[height<=1080][ext=mp4]',
        }
        
        return quality_formats.get(quality, 'best[ext=mp4]')
    
    def get_video_info(self, url: str) -> Optional[Dict]:
        """
        Get video information only (without downloading)
        
        Args:
            url: YouTube URL
            
        Returns:
            Video information dictionary or None
        """
        # Try with safe options first
        try:
            ydl_opts = self._get_safe_ydl_opts()
            ydl_opts.update({
                'quiet': True,
                'no_warnings': True,
            })
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description', '')[:200] + '...',
                    'thumbnail': info.get('thumbnail'),
                }
                
        except Exception as e:
            print(f"Failed to extract video information with safe options: {str(e)}")
            
            # Fallback: try with minimal options
            try:
                print("Trying with minimal options...")
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'socket_timeout': 10,
                    'retries': 0,
                    'user_agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    return {
                        'id': info.get('id'),
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Unknown'),
                        'upload_date': info.get('upload_date', ''),
                        'view_count': info.get('view_count', 0),
                        'description': info.get('description', '')[:200] + '...',
                        'thumbnail': info.get('thumbnail', ''),
                    }
                    
            except Exception as e2:
                print(f"Failed to extract video information with minimal options: {str(e2)}")
                return None
    
    def download_video(self, url: str, quality: str = 'best') -> Optional[Dict]:
        """
        Download YouTube video with simple retry logic optimized for server environments
        
        Args:
            url: YouTube URL
            quality: Video quality ('best', 'worst', '720p', '480p', etc.)
            
        Returns:
            Download information dictionary or None
        """
        # Use fewer retries in server environments
        max_retries = 2 if self._is_server_environment() else 3
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Simple delay between retries
                    delay = 2 * attempt
                    print(f"Retrying download in {delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                
                # Validate URL
                is_valid, message = self.validate_url(url)
                if not is_valid:
                    raise ValueError(message)
                
                video_id = self.extract_video_id(url)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{video_id}_{timestamp}"
                
                # Configure yt-dlp options
                format_selector = self._get_format_selector(quality)
                ydl_opts = self._get_safe_ydl_opts()
                ydl_opts.update({
                    'format': format_selector,
                    'outtmpl': os.path.join(self.download_dir, f'{filename}.%(ext)s'),
                    'writeinfojson': False,
                    'writethumbnail': False,
                    'extractaudio': False,
                    'merge_output_format': 'mp4',
                })
                
                print(f"Starting video download: {url}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extract video information
                    info = ydl.extract_info(url, download=False)
                    
                    # Check video duration - avoid very long videos on servers
                    duration = info.get('duration', 0)
                    if duration > 600:  # 10 minutes
                        print(f"Warning: Video is {duration}s long, might cause server timeout")
                    
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
                    
                    # Check file size
                    file_size = os.path.getsize(video_file)
                    if file_size == 0:
                        raise Exception("Downloaded file is empty.")
                    
                    result = {
                        'video_id': video_id,
                        'title': info.get('title'),
                        'duration': duration,
                        'file_path': video_file,
                        'file_size': file_size,
                        'downloaded_files': downloaded_files,
                        'download_time': datetime.now().isoformat(),
                    }
                    
                    print(f"Download complete: {video_file} ({file_size / 1024 / 1024:.1f}MB)")
                    return result
                    
            except Exception as e:
                error_msg = str(e).lower()
                print(f"Download attempt {attempt + 1} failed: {str(e)}")
                
                # Check for specific errors that shouldn't be retried
                if any(phrase in error_msg for phrase in [
                    'video unavailable', 'private video', 'sign in to confirm your age',
                    'video has been removed', 'video is not available', 'requested format not available'
                ]):
                    print("Video is unavailable or restricted. Stopping retries.")
                    break
                
                # Check for server-specific errors
                if any(phrase in error_msg for phrase in [
                    'connection timeout', 'read timeout', 'network unreachable',
                    'temporary failure', 'service unavailable'
                ]):
                    print("Network/server error detected. Will retry with longer delay...")
                    if attempt < max_retries - 1:
                        time.sleep(5)  # Longer delay for network issues
                    
                # If it's the last attempt, try with different quality
                if attempt == max_retries - 1 and quality != 'worst':
                    print("Trying with lowest quality as final attempt...")
                    return self.download_video(url, 'worst')
                    
        # Final fallback: try the simplest download approach
        print("All standard attempts failed. Trying simple download approach...")
        return self._try_simple_download(url, quality)
    
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