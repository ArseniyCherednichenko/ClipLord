"""
Utility functions for ClipLord
Handles logging, validation, error handling, and helper functions
"""

import logging
import re
import os
import sys
from pathlib import Path
from typing import Optional, Union
from urllib.parse import urlparse

def setup_logging(level: int = logging.INFO, log_file: Optional[str] = None):
    """
    Setup logging configuration
    
    Args:
        level: Logging level
        log_file: Optional log file path
    """
    # Create logs directory if logging to file
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file) if log_file else logging.NullHandler()
        ]
    )

def validate_url(url: str) -> bool:
    """
    Validate if URL is a valid YouTube URL
    
    Args:
        url: URL to validate
        
    Returns:
        True if valid YouTube URL, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    # YouTube URL patterns
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/v/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?youtu\.be/([a-zA-Z0-9_-]+)',
        r'(?:https?://)?(?:www\.)?youtube\.com/shorts/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in youtube_patterns:
        if re.match(pattern, url.strip()):
            return True
    
    return False

def clean_filename(filename: str, max_length: int = 100) -> str:
    """
    Clean filename for safe file system usage
    
    Args:
        filename: Original filename
        max_length: Maximum length for filename
        
    Returns:
        Cleaned filename
    """
    if not filename:
        return "unknown_video"
    
    # Remove/replace invalid characters
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove extra whitespace and replace with underscores
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    
    # Remove consecutive underscores
    cleaned = re.sub(r'_+', '_', cleaned)
    
    # Remove leading/trailing underscores
    cleaned = cleaned.strip('_')
    
    # Limit length
    if len(cleaned) > max_length:
        cleaned = cleaned[:max_length].rsplit('_', 1)[0]
    
    # Ensure not empty
    if not cleaned:
        cleaned = "video"
    
    return cleaned

def handle_error(error: Exception, context: str = "") -> str:
    """
    Handle and format error messages
    
    Args:
        error: Exception object
        context: Context where error occurred
        
    Returns:
        Formatted error message
    """
    error_type = type(error).__name__
    error_msg = str(error)
    
    # Clean up common error messages
    if "HTTP Error 403" in error_msg:
        return "Video unavailable (private/restricted)"
    elif "HTTP Error 404" in error_msg:
        return "Video not found"
    elif "No video formats found" in error_msg:
        return "No downloadable video found"
    elif "network" in error_msg.lower() or "connection" in error_msg.lower():
        return "Network connection error"
    elif len(error_msg) > 100:
        return f"{error_type}: {error_msg[:97]}..."
    
    if context:
        return f"Error {context}: {error_msg}"
    
    return f"{error_type}: {error_msg}"

def format_duration(seconds: float) -> str:
    """
    Format duration in seconds to human readable format
    
    Args:
        seconds: Duration in seconds
        
    Returns:
        Formatted duration string
    """
    if seconds < 60:
        return f"{seconds:.1f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        remaining_seconds = int(seconds % 60)
        return f"{minutes}m {remaining_seconds}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        return f"{hours}h {minutes}m"

def ensure_directory(path: Union[str, Path]) -> Path:
    """
    Ensure directory exists, create if it doesn't
    
    Args:
        path: Directory path
        
    Returns:
        Path object
    """
    path_obj = Path(path)
    path_obj.mkdir(parents=True, exist_ok=True)
    return path_obj

def get_file_size(file_path: Union[str, Path]) -> int:
    """
    Get file size in bytes
    
    Args:
        file_path: Path to file
        
    Returns:
        File size in bytes, 0 if file doesn't exist
    """
    try:
        return Path(file_path).stat().st_size
    except (OSError, FileNotFoundError):
        return 0

def format_file_size(size_bytes: int) -> str:
    """
    Format file size in bytes to human readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while size_bytes >= 1024 and i < len(size_names) - 1:
        size_bytes /= 1024.0
        i += 1
    
    return f"{size_bytes:.1f}{size_names[i]}"

def validate_video_file(file_path: Union[str, Path]) -> bool:
    """
    Validate if file is a valid video file
    
    Args:
        file_path: Path to video file
        
    Returns:
        True if valid video file, False otherwise
    """
    if not Path(file_path).exists():
        return False
    
    # Check file extension
    valid_extensions = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm'}
    if Path(file_path).suffix.lower() not in valid_extensions:
        return False
    
    # Check file size (should be > 0)
    if get_file_size(file_path) == 0:
        return False
    
    return True

def extract_video_id(url: str) -> Optional[str]:
    """
    Extract video ID from YouTube URL
    
    Args:
        url: YouTube URL
        
    Returns:
        Video ID or None if not found
    """
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:youtu\.be\/)([0-9A-Za-z_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None

def create_progress_bar(current: int, total: int, width: int = 50) -> str:
    """
    Create a simple progress bar string
    
    Args:
        current: Current progress
        total: Total items
        width: Width of progress bar
        
    Returns:
        Progress bar string
    """
    if total == 0:
        return "[" + "=" * width + "]"
    
    progress = current / total
    filled = int(width * progress)
    bar = "=" * filled + "-" * (width - filled)
    percentage = progress * 100
    
    return f"[{bar}] {percentage:.1f}%"

def sanitize_text(text: str) -> str:
    """
    Sanitize text for subtitle display
    
    Args:
        text: Input text
        
    Returns:
        Sanitized text
    """
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text.strip())
    
    # Remove special characters that might cause issues
    text = re.sub(r'[^\w\s\.,!?\-\'"()]', '', text)
    
    # Limit length for subtitles
    max_length = 100
    if len(text) > max_length:
        # Try to break at word boundary
        truncated = text[:max_length]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.8:  # If we can break reasonably close to the end
            text = truncated[:last_space] + "..."
        else:
            text = truncated + "..."
    
    return text

def check_dependencies():
    """
    Check if all required dependencies are available
    
    Returns:
        True if all dependencies available, False otherwise
    """
    required_packages = {
        'yt_dlp': 'yt-dlp',
        'moviepy': 'moviepy',
        'whisper': 'openai-whisper'
    }
    
    missing = []
    for module, package in required_packages.items():
        try:
            __import__(module)
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing required packages: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    
    return True

def get_system_info() -> dict:
    """
    Get basic system information
    
    Returns:
        Dictionary with system info
    """
    import platform
    import psutil
    
    return {
        'platform': platform.platform(),
        'python_version': platform.python_version(),
        'cpu_count': os.cpu_count(),
        'memory_gb': round(psutil.virtual_memory().total / (1024**3), 1),
        'disk_free_gb': round(psutil.disk_usage('.').free / (1024**3), 1)
    }
