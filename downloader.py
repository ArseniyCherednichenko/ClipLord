"""
Video downloader module using yt-dlp
Handles downloading YouTube videos with high quality
"""

import os
import tempfile
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

try:
    import yt_dlp
except ImportError:
    raise ImportError("yt-dlp not installed. Run: pip install yt-dlp")

from utils import handle_error

class VideoDownloader:
    """Handles video downloading from YouTube using yt-dlp"""
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Initialize the video downloader
        
        Args:
            temp_dir: Directory for temporary files
        """
        self.logger = logging.getLogger(__name__)
        self.temp_dir = temp_dir or tempfile.gettempdir()
        
        # yt-dlp options for high quality download
        self.ydl_opts = {
            'format': 'best[height<=1080][ext=mp4]/best[ext=mp4]/best',
            'outtmpl': os.path.join(self.temp_dir, '%(title)s.%(ext)s'),
            'quiet': True,
            'no_warnings': True,
            'extractaudio': False,
            'audioformat': 'mp4',
            'embed_subs': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
        }
    
    def download(self, url: str) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Download video from YouTube URL
        
        Args:
            url: YouTube video URL
            
        Returns:
            Tuple of (video_path, video_info) or (None, {}) if failed
        """
        try:
            with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                # Extract video info first
                self.logger.info(f"Extracting info for: {url}")
                info = ydl.extract_info(url, download=False)
                
                if not info:
                    self.logger.error("Could not extract video info")
                    return None, {}
                
                # Check video duration (avoid extremely long videos)
                duration = info.get('duration', 0)
                if duration > 3600:  # 1 hour limit
                    self.logger.warning(f"Video too long: {duration}s, skipping")
                    print(f"⚠️ Video is too long ({duration//60} minutes), skipping...")
                    return None, {}
                
                # Download the video
                self.logger.info(f"Downloading: {info.get('title', 'Unknown')}")
                ydl.download([url])
                
                # Find the downloaded file
                expected_path = ydl.prepare_filename(info)
                
                # Handle different possible extensions
                possible_paths = [
                    expected_path,
                    expected_path.rsplit('.', 1)[0] + '.mp4',
                    expected_path.rsplit('.', 1)[0] + '.webm',
                    expected_path.rsplit('.', 1)[0] + '.mkv'
                ]
                
                video_path = None
                for path in possible_paths:
                    if os.path.exists(path):
                        video_path = path
                        break
                
                if not video_path:
                    self.logger.error("Downloaded file not found")
                    return None, {}
                
                self.logger.info(f"Successfully downloaded: {video_path}")
                return video_path, info
                
        except yt_dlp.DownloadError as e:
            error_msg = handle_error(e, "downloading video")
            self.logger.error(f"Download error: {e}")
            print(f"❌ Download failed: {error_msg}")
            return None, {}
            
        except Exception as e:
            error_msg = handle_error(e, "downloading video")
            self.logger.error(f"Unexpected error: {e}")
            print(f"❌ Unexpected error: {error_msg}")
            return None, {}
    
    def get_video_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get video information without downloading
        
        Args:
            url: YouTube video URL
            
        Returns:
            Video info dictionary or None if failed
        """
        try:
            with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                info = ydl.extract_info(url, download=False)
                return info
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return None
    
    def cleanup_temp_files(self, patterns: list = None):
        """
        Clean up temporary files
        
        Args:
            patterns: List of file patterns to clean (optional)
        """
        if patterns is None:
            patterns = ['*.mp4', '*.webm', '*.mkv', '*.part']
        
        temp_path = Path(self.temp_dir)
        for pattern in patterns:
            for file in temp_path.glob(pattern):
                try:
                    file.unlink()
                    self.logger.debug(f"Cleaned up: {file}")
                except Exception as e:
                    self.logger.warning(f"Could not clean up {file}: {e}")
