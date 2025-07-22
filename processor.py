"""
Video processing module for cropping, trimming, and adding subtitles
Uses moviepy for video editing operations
"""

import logging
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any
import re

try:
    from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
    from moviepy.config import check_dependencies
except ImportError:
    raise ImportError("moviepy not installed. Run: pip install moviepy")

from utils import handle_error

class VideoProcessor:
    """Handles video processing operations"""
    
    def __init__(self):
        """Initialize the video processor"""
        self.logger = logging.getLogger(__name__)
        
        # TikTok aspect ratio (9:16)
        self.target_aspect_ratio = 9 / 16
        self.target_width = 1080
        self.target_height = 1920
    
    def process_video(self, video_path: str, subtitles: List[Dict], 
                     output_path: Path, target_duration_range: Tuple[int, int] = (15, 60)) -> Optional[str]:
        """
        Main processing function: crop to 9:16, trim, and add subtitles
        
        Args:
            video_path: Path to input video
            subtitles: List of subtitle segments
            output_path: Path for output video
            target_duration_range: Min and max duration in seconds
            
        Returns:
            Path to processed video or None if failed
        """
        try:
            # Load video
            self.logger.info(f"Loading video: {video_path}")
            video = VideoFileClip(video_path)
            
            if video.duration is None or video.duration <= 0:
                self.logger.error("Invalid video duration")
                return None
            
            # Crop to 9:16 aspect ratio
            cropped_video = self._crop_to_vertical(video)
            
            # Find optimal trim duration based on subtitles and target range
            trim_duration = self._find_optimal_duration(
                video_duration=video.duration,
                subtitles=subtitles,
                target_range=target_duration_range
            )
            
            # Trim video
            if trim_duration < video.duration:
                trimmed_video = cropped_video.subclip(0, trim_duration)
                print(f"✂️ Trimmed video to {trim_duration:.1f} seconds")
            else:
                trimmed_video = cropped_video
            
            # Add subtitles if available
            final_video = trimmed_video
            if subtitles:
                final_video = self._add_subtitles(trimmed_video, subtitles)
                print("📝 Added subtitles to video")
            
            # Export final video
            self.logger.info(f"Exporting to: {output_path}")
            final_video.write_videofile(
                str(output_path),
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                verbose=False,
                logger=None
            )
            
            # Cleanup
            video.close()
            cropped_video.close()
            trimmed_video.close()
            if final_video != trimmed_video:
                final_video.close()
            
            return str(output_path)
            
        except Exception as e:
            error_msg = handle_error(e, "processing video")
            self.logger.error(f"Video processing error: {e}")
            print(f"❌ Processing error: {error_msg}")
            return None
    
    def _crop_to_vertical(self, video: VideoFileClip) -> VideoFileClip:
        """
        Crop video to 9:16 vertical aspect ratio
        
        Args:
            video: Input video clip
            
        Returns:
            Cropped video clip
        """
        # Get video dimensions
        w, h = video.size
        current_ratio = w / h
        
        if abs(current_ratio - self.target_aspect_ratio) < 0.01:
            # Already correct aspect ratio
            return video.resize((self.target_width, self.target_height))
        
        if current_ratio > self.target_aspect_ratio:
            # Video is too wide, crop horizontally
            new_width = int(h * self.target_aspect_ratio)
            x_center = w // 2
            x1 = x_center - new_width // 2
            x2 = x_center + new_width // 2
            
            cropped = video.crop(x1=x1, x2=x2)
        else:
            # Video is too tall, crop vertically
            new_height = int(w / self.target_aspect_ratio)
            y_center = h // 2
            y1 = y_center - new_height // 2
            y2 = y_center + new_height // 2
            
            cropped = video.crop(y1=y1, y2=y2)
        
        # Resize to target dimensions
        return cropped.resize((self.target_width, self.target_height))
    
    def _find_optimal_duration(self, video_duration: float, subtitles: List[Dict], 
                              target_range: Tuple[int, int]) -> float:
        """
        Find optimal duration to trim video at natural speech breaks
        
        Args:
            video_duration: Total video duration
            subtitles: List of subtitle segments
            target_range: Min and max target duration
            
        Returns:
            Optimal duration in seconds
        """
        min_duration, max_duration = target_range
        
        if not subtitles:
            # No subtitles, use middle of target range or video duration
            return min(max_duration, video_duration)
        
        # Find subtitle segments that end with sentence-ending punctuation
        sentence_endings = []
        for subtitle in subtitles:
            end_time = subtitle.get('end', 0)
            text = subtitle.get('text', '').strip()
            
            # Check if text ends with sentence-ending punctuation
            if re.search(r'[.!?]$', text) and min_duration <= end_time <= max_duration:
                sentence_endings.append(end_time)
        
        if sentence_endings:
            # Prefer durations closer to the middle of target range
            target_middle = (min_duration + max_duration) / 2
            best_duration = min(sentence_endings, key=lambda x: abs(x - target_middle))
            self.logger.info(f"Found natural break at {best_duration:.1f}s")
            return best_duration
        
        # No good sentence endings found, look for any subtitle end in range
        valid_ends = [s.get('end', 0) for s in subtitles 
                     if min_duration <= s.get('end', 0) <= max_duration]
        
        if valid_ends:
            target_middle = (min_duration + max_duration) / 2
            return min(valid_ends, key=lambda x: abs(x - target_middle))
        
        # Fall back to max duration or video duration
        return min(max_duration, video_duration)
    
    def _add_subtitles(self, video: VideoFileClip, subtitles: List[Dict]) -> CompositeVideoClip:
        """
        Add styled subtitles to video
        
        Args:
            video: Input video clip
            subtitles: List of subtitle segments
            
        Returns:
            Video with subtitles
        """
        subtitle_clips = []
        
        for subtitle in subtitles:
            start_time = subtitle.get('start', 0)
            end_time = subtitle.get('end', 0)
            text = subtitle.get('text', '').strip()
            
            if not text or start_time >= video.duration:
                continue
            
            # Ensure subtitle doesn't extend beyond video duration
            end_time = min(end_time, video.duration)
            duration = end_time - start_time
            
            if duration <= 0:
                continue
            
            # Create styled text clip
            try:
                txt_clip = TextClip(
                    text,
                    fontsize=60,
                    font='Arial-Bold',
                    color='white',
                    stroke_color='black',
                    stroke_width=3,
                    method='caption',
                    size=(video.w * 0.8, None)  # 80% of video width
                ).set_start(start_time).set_duration(duration)
                
                # Position subtitle at bottom of screen
                txt_clip = txt_clip.set_position(('center', video.h * 0.75))
                subtitle_clips.append(txt_clip)
                
            except Exception as e:
                self.logger.warning(f"Could not create subtitle clip: {e}")
                continue
        
        if subtitle_clips:
            return CompositeVideoClip([video] + subtitle_clips)
        else:
            return video
    
    def get_video_duration(self, video_path: str) -> float:
        """
        Get duration of video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Duration in seconds
        """
        try:
            with VideoFileClip(video_path) as video:
                return video.duration or 0.0
        except Exception as e:
            self.logger.error(f"Error getting video duration: {e}")
            return 0.0
    
    def get_video_info(self, video_path: str) -> Dict[str, Any]:
        """
        Get video information
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video info
        """
        try:
            with VideoFileClip(video_path) as video:
                return {
                    'duration': video.duration,
                    'size': video.size,
                    'fps': video.fps,
                    'audio': video.audio is not None
                }
        except Exception as e:
            self.logger.error(f"Error getting video info: {e}")
            return {}
