import os
import tempfile
import shutil
from typing import Dict, Optional, Tuple
from pathlib import Path
import yt_dlp
import re
from datetime import datetime
import time
import sys

class YouTubeDownloader:
    def __init__(self, download_dir: str = "temp"):
        """
        Initialize YouTube downloader
        
        Args:
            download_dir: Directory to save downloaded videos
        """
        self.download_dir = download_dir
        
        # Create download directory if it doesn't exist
        os.makedirs(download_dir, exist_ok=True)
        
        print(f"🔧 [INIT] YouTube Downloader initialized:")
        print(f"  - Download directory: {os.path.abspath(download_dir)}")
        print(f"  - Directory exists: {os.path.exists(download_dir)}")
        print(f"  - Directory writable: {os.access(download_dir, os.W_OK)}")
        
        # Check system information
        print(f"🖥️ [SYSTEM] System information:")
        print(f"  - Python version: {sys.version}")
        print(f"  - Platform: {sys.platform}")
        print(f"  - Current working directory: {os.getcwd()}")
        
        # Check yt-dlp version
        try:
            import yt_dlp
            print(f"  - yt-dlp version: {yt_dlp.version.__version__}")
        except Exception as e:
            print(f"  - yt-dlp version check failed: {e}")
        
        # Check disk space
        try:
            import shutil
            total, used, free = shutil.disk_usage(download_dir)
            print(f"💾 [DISK] Disk space:")
            print(f"  - Total: {total / 1024 / 1024 / 1024:.1f}GB")
            print(f"  - Used: {used / 1024 / 1024 / 1024:.1f}GB")
            print(f"  - Free: {free / 1024 / 1024 / 1024:.1f}GB")
        except Exception as e:
            print(f"  - Disk space check failed: {e}")
        
        # Check environment variables
        print(f"🔑 [ENV] Environment variables:")
        proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy']
        for var in proxy_vars:
            if var in os.environ:
                print(f"  - {var}: {os.environ[var]}")
        
        # Check if server environment
        is_server = self._is_server_environment()
        print(f"🌐 [ENV] Server environment: {is_server}")
        
        print(f"✅ [INIT] Initialization complete")
        print("-" * 50)
    
    def _is_server_environment(self) -> bool:
        """Check if running in server environment"""
        server_indicators = [
            'RENDER',
            'HEROKU',
            'RAILWAY',
            'VERCEL',
            'NETLIFY',
            'CLOUD_RUN_SERVICE',
            'AWS_LAMBDA_FUNCTION_NAME',
            'AZURE_FUNCTIONS_WORKER_RUNTIME',
        ]
        
        is_server = any(indicator in os.environ for indicator in server_indicators)
        
        print(f"🌐 [ENV] Server environment detection:")
        print(f"  - Is server: {is_server}")
        
        if is_server:
            detected_envs = [env for env in server_indicators if env in os.environ]
            print(f"  - Detected environments: {detected_envs}")
        
        # Check for common server paths
        server_paths = ['/app', '/tmp', '/var/task']
        current_path = os.getcwd()
        path_indicates_server = any(path in current_path for path in server_paths)
        
        print(f"  - Current path: {current_path}")
        print(f"  - Path indicates server: {path_indicates_server}")
        
        final_result = is_server or path_indicates_server
        print(f"  - Final result: {final_result}")
        
        return final_result
    
    def _get_safe_ydl_opts(self) -> Dict:
        """Get safe yt-dlp options optimized for server environments"""
        
        is_server = self._is_server_environment()
        
        print(f"⚙️ [OPTS] Configuring yt-dlp options:")
        print(f"  - Server environment: {is_server}")
        
        # Base options optimized for server environments
        opts = {
            'format': 'best[ext=mp4]/best',
            'socket_timeout': 15 if is_server else 30,
            'retries': 1 if is_server else 3,
            'fragment_retries': 1 if is_server else 3,
            'writeinfojson': False,
            'writethumbnail': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'extractaudio': False,
            'embedsubs': False,
            'embedthumbnail': False,
            'addmetadata': False,
            'ignoreerrors': False,
            'user_agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
            'referer': 'https://www.youtube.com/',
            'merge_output_format': 'mp4',
            'postprocessors': [],
        }
        
        if is_server:
            # More conservative settings for server environments
            opts.update({
                'max_downloads': 1,
                'max_filesize': 100 * 1024 * 1024,  # 100MB limit
                'concurrent_fragment_downloads': 1,
                'http_chunk_size': 1024 * 1024,  # 1MB chunks
                'buffersize': 1024 * 1024,  # 1MB buffer
                'ratelimit': 1 * 1024 * 1024,  # 1MB/s rate limit
            })
            
            print(f"  - Applied server-specific limits:")
            print(f"    - Max filesize: {opts['max_filesize'] / 1024 / 1024:.0f}MB")
            print(f"    - Rate limit: {opts['ratelimit'] / 1024 / 1024:.0f}MB/s")
        
        print(f"  - Socket timeout: {opts['socket_timeout']}s")
        print(f"  - Retries: {opts['retries']}")
        print(f"  - Fragment retries: {opts['fragment_retries']}")
        print(f"  - User agent: {opts['user_agent'][:50]}...")
        print(f"  - Format: {opts['format']}")
        
        return opts
    
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
            print("🔧 [SIMPLE] Trying simple download approach...")
            
            video_id = self.extract_video_id(url)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{video_id}_{timestamp}_simple"
            
            print(f"🔧 [SIMPLE] Video ID: {video_id}")
            print(f"🔧 [SIMPLE] Filename: {filename}")
            
            # Most basic yt-dlp options
            ydl_opts = {
                'format': 'best[ext=mp4]/best',
                'outtmpl': os.path.join(self.download_dir, f'{filename}.%(ext)s'),
                'quiet': False,  # Enable output for debugging
                'no_warnings': False,
                'verbose': True,
                'writeinfojson': False,
                'writethumbnail': False,
                'user_agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                'socket_timeout': 10,
                'retries': 0,
                'fragment_retries': 0,
            }
            
            print(f"🔧 [SIMPLE] Options: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("🔧 [SIMPLE] Extracting info...")
                info = ydl.extract_info(url, download=False)
                
                print(f"🔧 [SIMPLE] Info extracted successfully:")
                print(f"  - Title: {info.get('title', 'N/A')}")
                print(f"  - Duration: {info.get('duration', 'N/A')}")
                print(f"  - Availability: {info.get('availability', 'N/A')}")
                
                print("🔧 [SIMPLE] Starting download...")
                ydl.download([url])
                
                print("🔧 [SIMPLE] Download completed, looking for files...")
                
                # Find downloaded file
                if os.path.exists(self.download_dir):
                    all_files = os.listdir(self.download_dir)
                    print(f"🔧 [SIMPLE] All files: {all_files}")
                    
                    for file in all_files:
                        if file.startswith(filename):
                            file_path = os.path.join(self.download_dir, file)
                            file_size = os.path.getsize(file_path)
                            
                            print(f"🔧 [SIMPLE] Found file: {file}")
                            print(f"🔧 [SIMPLE] File size: {file_size} bytes")
                            
                            if file_size > 0:
                                result = {
                                    'video_id': video_id,
                                    'title': info.get('title'),
                                    'duration': info.get('duration'),
                                    'file_path': file_path,
                                    'file_size': file_size,
                                    'downloaded_files': [file_path],
                                    'download_time': datetime.now().isoformat(),
                                    'method': 'simple'
                                }
                                
                                print(f"✅ [SIMPLE] Simple download successful!")
                                return result
                            else:
                                print(f"❌ [SIMPLE] File is empty")
                else:
                    print(f"❌ [SIMPLE] Download directory doesn't exist")
            
            print(f"❌ [SIMPLE] No valid file found")
            return None
            
        except Exception as e:
            print(f"❌ [SIMPLE] Simple download failed:")
            print(f"  - Error type: {type(e).__name__}")
            print(f"  - Error message: {str(e)}")
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
        video_id = self.extract_video_id(url)
        print(f"🔍 [DEBUG] Extracting info for video ID: {video_id}")
        print(f"🔍 [DEBUG] Full URL: {url}")
        
        # Try with safe options first
        try:
            print("🔍 [DEBUG] Trying with safe yt-dlp options...")
            ydl_opts = self._get_safe_ydl_opts()
            ydl_opts.update({
                'quiet': False,  # Enable verbose output for debugging
                'no_warnings': False,
                'verbose': True,  # More detailed logging
            })
            
            print(f"🔍 [DEBUG] yt-dlp options: {ydl_opts}")
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print("🔍 [DEBUG] Starting yt-dlp extract_info...")
                info = ydl.extract_info(url, download=False)
                
                print(f"🔍 [DEBUG] Successfully extracted info:")
                print(f"  - Title: {info.get('title', 'N/A')}")
                print(f"  - Uploader: {info.get('uploader', 'N/A')}")
                print(f"  - Duration: {info.get('duration', 'N/A')}")
                print(f"  - View count: {info.get('view_count', 'N/A')}")
                print(f"  - Upload date: {info.get('upload_date', 'N/A')}")
                print(f"  - Availability: {info.get('availability', 'N/A')}")
                print(f"  - Age limit: {info.get('age_limit', 'N/A')}")
                print(f"  - Live status: {info.get('live_status', 'N/A')}")
                
                return {
                    'id': info.get('id'),
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'uploader': info.get('uploader'),
                    'upload_date': info.get('upload_date'),
                    'view_count': info.get('view_count'),
                    'description': info.get('description', '')[:200] + '...',
                    'thumbnail': info.get('thumbnail'),
                    'availability': info.get('availability'),
                    'age_limit': info.get('age_limit'),
                    'live_status': info.get('live_status'),
                }
                
        except Exception as e:
            error_str = str(e)
            print(f"❌ [ERROR] Failed to extract video information with safe options:")
            print(f"  - Error type: {type(e).__name__}")
            print(f"  - Error message: {error_str}")
            print(f"  - Video ID: {video_id}")
            
            # Check for specific error patterns
            if 'video unavailable' in error_str.lower():
                print("❌ [ANALYSIS] Video is marked as unavailable by YouTube")
                
                # Try to get more details about why it's unavailable
                try:
                    print("🔍 [DEBUG] Attempting minimal extraction for error details...")
                    minimal_opts = {
                        'quiet': False,
                        'verbose': True,
                        'ignore_errors': True,
                        'extract_flat': True,
                    }
                    
                    with yt_dlp.YoutubeDL(minimal_opts) as ydl:
                        minimal_info = ydl.extract_info(url, download=False)
                        print(f"🔍 [DEBUG] Minimal info extraction result: {minimal_info}")
                        
                except Exception as e2:
                    print(f"❌ [ERROR] Even minimal extraction failed: {str(e2)}")
            
            elif 'private video' in error_str.lower():
                print("❌ [ANALYSIS] Video is private")
            elif 'sign in to confirm your age' in error_str.lower():
                print("❌ [ANALYSIS] Video is age-restricted")
            elif 'this video is not available' in error_str.lower():
                print("❌ [ANALYSIS] Video not available in this region")
            
            # Fallback: try with minimal options
            try:
                print("🔍 [DEBUG] Trying with minimal options...")
                ydl_opts = {
                    'quiet': False,
                    'no_warnings': False,
                    'verbose': True,
                    'socket_timeout': 10,
                    'retries': 0,
                    'user_agent': 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)',
                    'extract_flat': False,
                }
                
                print(f"🔍 [DEBUG] Minimal options: {ydl_opts}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                    
                    print(f"✅ [SUCCESS] Minimal extraction succeeded:")
                    print(f"  - Title: {info.get('title', 'Unknown')}")
                    
                    return {
                        'id': info.get('id'),
                        'title': info.get('title', 'Unknown'),
                        'duration': info.get('duration', 0),
                        'uploader': info.get('uploader', 'Unknown'),
                        'upload_date': info.get('upload_date', ''),
                        'view_count': info.get('view_count', 0),
                        'description': info.get('description', '')[:200] + '...',
                        'thumbnail': info.get('thumbnail', ''),
                        'availability': info.get('availability', 'unknown'),
                        'method': 'minimal'
                    }
                    
            except Exception as e2:
                print(f"❌ [ERROR] Failed to extract video information with minimal options:")
                print(f"  - Error type: {type(e2).__name__}")
                print(f"  - Error message: {str(e2)}")
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
        video_id = self.extract_video_id(url)
        print(f"🚀 [DOWNLOAD] Starting download for video ID: {video_id}")
        print(f"🚀 [DOWNLOAD] URL: {url}")
        print(f"🚀 [DOWNLOAD] Requested quality: {quality}")
        print(f"🚀 [DOWNLOAD] Server environment: {self._is_server_environment()}")
        
        # Use fewer retries in server environments
        max_retries = 2 if self._is_server_environment() else 3
        print(f"🚀 [DOWNLOAD] Max retries: {max_retries}")
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Simple delay between retries
                    delay = 2 * attempt
                    print(f"⏳ [RETRY] Retrying download in {delay}s... (attempt {attempt + 1}/{max_retries})")
                    time.sleep(delay)
                
                print(f"🔄 [ATTEMPT {attempt + 1}] Starting download attempt...")
                
                # Validate URL
                is_valid, message = self.validate_url(url)
                if not is_valid:
                    print(f"❌ [VALIDATION] URL validation failed: {message}")
                    raise ValueError(message)
                
                print(f"✅ [VALIDATION] URL is valid")
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"{video_id}_{timestamp}"
                print(f"📁 [FILE] Output filename: {filename}")
                
                # Configure yt-dlp options
                format_selector = self._get_format_selector(quality)
                print(f"🎬 [FORMAT] Format selector: {format_selector}")
                
                ydl_opts = self._get_safe_ydl_opts()
                ydl_opts.update({
                    'format': format_selector,
                    'outtmpl': os.path.join(self.download_dir, f'{filename}.%(ext)s'),
                    'writeinfojson': False,
                    'writethumbnail': False,
                    'extractaudio': False,
                    'merge_output_format': 'mp4',
                    'verbose': True,  # Enable verbose logging
                })
                
                print(f"⚙️ [CONFIG] Download directory: {self.download_dir}")
                print(f"⚙️ [CONFIG] yt-dlp options: {ydl_opts}")
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    print(f"🔍 [INFO] Extracting video information...")
                    
                    # Extract video information
                    info = ydl.extract_info(url, download=False)
                    
                    # Check video duration - avoid very long videos on servers
                    duration = info.get('duration', 0)
                    title = info.get('title', 'Unknown')
                    availability = info.get('availability', 'unknown')
                    
                    print(f"📹 [VIDEO INFO] Title: {title}")
                    print(f"📹 [VIDEO INFO] Duration: {duration}s")
                    print(f"📹 [VIDEO INFO] Availability: {availability}")
                    print(f"📹 [VIDEO INFO] Uploader: {info.get('uploader', 'Unknown')}")
                    print(f"📹 [VIDEO INFO] Upload date: {info.get('upload_date', 'Unknown')}")
                    
                    if duration > 600:  # 10 minutes
                        print(f"⚠️ [WARNING] Video is {duration}s long, might cause server timeout")
                    
                    # Check if video is actually available for download
                    if availability and availability not in ['public', 'unlisted']:
                        print(f"❌ [AVAILABILITY] Video availability issue: {availability}")
                    
                    # Check available formats
                    formats = info.get('formats', [])
                    print(f"🎬 [FORMATS] Available formats count: {len(formats)}")
                    
                    if formats:
                        for i, fmt in enumerate(formats[:5]):  # Show first 5 formats
                            print(f"  Format {i+1}: {fmt.get('format_id', 'N/A')} - {fmt.get('format', 'N/A')}")
                    else:
                        print(f"❌ [FORMATS] No formats available!")
                    
                    print(f"⬇️ [DOWNLOAD] Starting actual download...")
                    
                    # Execute actual download
                    ydl.download([url])
                    
                    print(f"✅ [DOWNLOAD] Download command completed, looking for files...")
                    
                    # Find downloaded files
                    downloaded_files = []
                    if os.path.exists(self.download_dir):
                        all_files = os.listdir(self.download_dir)
                        print(f"📁 [FILES] All files in download dir: {all_files}")
                        
                        for file in all_files:
                            if file.startswith(filename):
                                downloaded_files.append(os.path.join(self.download_dir, file))
                                print(f"📄 [MATCH] Found matching file: {file}")
                    else:
                        print(f"❌ [ERROR] Download directory doesn't exist: {self.download_dir}")
                    
                    print(f"📋 [SUMMARY] Downloaded files: {downloaded_files}")
                    
                    # Find video file
                    video_file = None
                    for file in downloaded_files:
                        if file.endswith(('.mp4', '.mkv', '.webm', '.avi')):
                            video_file = file
                            print(f"🎬 [VIDEO] Found video file: {video_file}")
                            break
                    
                    if not video_file:
                        print(f"❌ [ERROR] No video file found in downloaded files")
                        raise Exception("Downloaded video file not found.")
                    
                    # Check file size
                    file_size = os.path.getsize(video_file)
                    print(f"📏 [SIZE] File size: {file_size} bytes ({file_size / 1024 / 1024:.1f}MB)")
                    
                    if file_size == 0:
                        print(f"❌ [ERROR] Downloaded file is empty")
                        raise Exception("Downloaded file is empty.")
                    
                    result = {
                        'video_id': video_id,
                        'title': title,
                        'duration': duration,
                        'file_path': video_file,
                        'file_size': file_size,
                        'downloaded_files': downloaded_files,
                        'download_time': datetime.now().isoformat(),
                        'availability': availability,
                        'attempt': attempt + 1,
                    }
                    
                    print(f"🎉 [SUCCESS] Download complete: {video_file} ({file_size / 1024 / 1024:.1f}MB)")
                    return result
                    
            except Exception as e:
                error_msg = str(e)
                error_type = type(e).__name__
                
                print(f"❌ [ERROR] Download attempt {attempt + 1} failed:")
                print(f"  - Error type: {error_type}")
                print(f"  - Error message: {error_msg}")
                print(f"  - Video ID: {video_id}")
                print(f"  - Quality: {quality}")
                
                # Detailed error analysis
                error_lower = error_msg.lower()
                
                # Check for specific errors that shouldn't be retried
                if any(phrase in error_lower for phrase in [
                    'video unavailable', 'private video', 'sign in to confirm your age',
                    'video has been removed', 'video is not available', 'requested format not available'
                ]):
                    print(f"🛑 [ANALYSIS] Video is unavailable or restricted. Stopping retries.")
                    print(f"  - Specific issue: Video cannot be accessed")
                    break
                
                # Check for server-specific errors
                elif any(phrase in error_lower for phrase in [
                    'connection timeout', 'read timeout', 'network unreachable',
                    'temporary failure', 'service unavailable'
                ]):
                    print(f"🌐 [ANALYSIS] Network/server error detected:")
                    print(f"  - Issue: Network connectivity problem")
                    print(f"  - Action: Will retry with longer delay...")
                    if attempt < max_retries - 1:
                        time.sleep(5)  # Longer delay for network issues
                
                # Check for format-related errors
                elif any(phrase in error_lower for phrase in [
                    'no video formats', 'format not available', 'no suitable format'
                ]):
                    print(f"🎬 [ANALYSIS] Format-related error:")
                    print(f"  - Issue: Requested format not available")
                    print(f"  - Action: Will try different quality")
                
                # Other errors
                else:
                    print(f"❓ [ANALYSIS] Unknown error type")
                    print(f"  - Will retry with standard delay")
                    
                # If it's the last attempt, try with different quality
                if attempt == max_retries - 1 and quality != 'worst':
                    print(f"🔄 [FALLBACK] Trying with lowest quality as final attempt...")
                    return self.download_video(url, 'worst')
                    
        # Final fallback: try the simplest download approach
        print(f"🆘 [FALLBACK] All standard attempts failed. Trying simple download approach...")
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