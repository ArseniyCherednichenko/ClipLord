"""
Subtitle generation module using OpenAI Whisper
Handles ASR and subtitle creation
"""

import logging
import tempfile
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
import json

try:
    import whisper
except ImportError:
    raise ImportError("openai-whisper not installed. Run: pip install openai-whisper")

try:
    from moviepy.editor import VideoFileClip
except ImportError:
    raise ImportError("moviepy not installed. Run: pip install moviepy")

from utils import handle_error

class SubtitleGenerator:
    """Handles subtitle generation using OpenAI Whisper"""
    
    def __init__(self, model_name: str = "base"):
        """
        Initialize the subtitle generator
        
        Args:
            model_name: Whisper model to use (tiny, base, small, medium, large)
        """
        self.logger = logging.getLogger(__name__)
        self.model_name = model_name
        self.model = None
        
        # Load Whisper model
        self._load_model()
    
    def _load_model(self):
        """Load the Whisper model"""
        try:
            self.logger.info(f"Loading Whisper model: {self.model_name}")
            self.model = whisper.load_model(self.model_name)
            self.logger.info("Whisper model loaded successfully")
        except Exception as e:
            self.logger.error(f"Failed to load Whisper model: {e}")
            print(f"❌ Failed to load Whisper model: {e}")
            raise
    
    def generate_subtitles(self, video_path: str, language: str = None) -> List[Dict[str, Any]]:
        """
        Generate subtitles from video audio
        
        Args:
            video_path: Path to video file
            language: Language code (auto-detect if None)
            
        Returns:
            List of subtitle segments with start, end, and text
        """
        try:
            # Extract audio from video
            audio_path = self._extract_audio(video_path)
            if not audio_path:
                return []
            
            # Transcribe audio using Whisper
            self.logger.info("Transcribing audio with Whisper...")
            result = self.model.transcribe(
                audio_path,
                language=language,
                word_timestamps=True,
                verbose=False
            )
            
            # Clean up temporary audio file
            try:
                os.remove(audio_path)
            except:
                pass
            
            # Convert Whisper output to subtitle format
            subtitles = self._process_whisper_result(result)
            
            self.logger.info(f"Generated {len(subtitles)} subtitle segments")
            return subtitles
            
        except Exception as e:
            error_msg = handle_error(e, "generating subtitles")
            self.logger.error(f"Subtitle generation error: {e}")
            print(f"❌ Subtitle error: {error_msg}")
            return []
    
    def _extract_audio(self, video_path: str) -> Optional[str]:
        """
        Extract audio from video file
        
        Args:
            video_path: Path to video file
            
        Returns:
            Path to extracted audio file or None if failed
        """
        try:
            with VideoFileClip(video_path) as video:
                if not video.audio:
                    self.logger.warning("Video has no audio track")
                    return None
                
                # Create temporary audio file
                temp_audio = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_audio_path = temp_audio.name
                temp_audio.close()
                
                # Extract audio
                video.audio.write_audiofile(
                    temp_audio_path,
                    verbose=False,
                    logger=None
                )
                
                return temp_audio_path
                
        except Exception as e:
            self.logger.error(f"Error extracting audio: {e}")
            return None
    
    def _process_whisper_result(self, result: Dict) -> List[Dict[str, Any]]:
        """
        Process Whisper transcription result into subtitle format
        
        Args:
            result: Whisper transcription result
            
        Returns:
            List of subtitle segments
        """
        subtitles = []
        
        # Use segments for better timing
        segments = result.get('segments', [])
        
        for segment in segments:
            subtitle = {
                'start': segment.get('start', 0),
                'end': segment.get('end', 0),
                'text': segment.get('text', '').strip()
            }
            
            # Skip empty or very short segments
            if subtitle['text'] and (subtitle['end'] - subtitle['start']) > 0.1:
                subtitles.append(subtitle)
        
        # If no segments, fall back to words with grouping
        if not subtitles and 'words' in result:
            subtitles = self._group_words_into_subtitles(result['words'])
        
        # Final fallback to full text
        if not subtitles and result.get('text'):
            subtitles = [{
                'start': 0,
                'end': 30,  # Default duration
                'text': result['text'].strip()
            }]
        
        return subtitles
    
    def _group_words_into_subtitles(self, words: List[Dict], max_words: int = 8) -> List[Dict[str, Any]]:
        """
        Group words into subtitle segments
        
        Args:
            words: List of word dictionaries from Whisper
            max_words: Maximum words per subtitle
            
        Returns:
            List of subtitle segments
        """
        if not words:
            return []
        
        subtitles = []
        current_words = []
        
        for word in words:
            current_words.append(word)
            
            # Create subtitle if we have enough words or hit punctuation
            word_text = word.get('word', '').strip()
            if (len(current_words) >= max_words or 
                any(punct in word_text for punct in ['.', '!', '?', ','])):
                
                if current_words:
                    subtitle = {
                        'start': current_words[0].get('start', 0),
                        'end': current_words[-1].get('end', 0),
                        'text': ' '.join(w.get('word', '').strip() for w in current_words)
                    }
                    subtitles.append(subtitle)
                    current_words = []
        
        # Add remaining words
        if current_words:
            subtitle = {
                'start': current_words[0].get('start', 0),
                'end': current_words[-1].get('end', 0),
                'text': ' '.join(w.get('word', '').strip() for w in current_words)
            }
            subtitles.append(subtitle)
        
        return subtitles
    
    def export_srt(self, subtitles: List[Dict[str, Any]], output_path: str) -> bool:
        """
        Export subtitles as SRT file
        
        Args:
            subtitles: List of subtitle segments
            output_path: Path for SRT file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                for i, subtitle in enumerate(subtitles, 1):
                    start_time = self._seconds_to_srt_time(subtitle['start'])
                    end_time = self._seconds_to_srt_time(subtitle['end'])
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{subtitle['text']}\n\n")
            
            self.logger.info(f"SRT file exported: {output_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting SRT: {e}")
            return False
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """
        Convert seconds to SRT time format
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Time in SRT format (HH:MM:SS,mmm)
        """
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def detect_language(self, audio_path: str) -> str:
        """
        Detect language from audio file
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            Detected language code
        """
        try:
            # Load audio and pad/trim it to fit 30 seconds
            audio = whisper.load_audio(audio_path)
            audio = whisper.pad_or_trim(audio)
            
            # Make log-Mel spectrogram and move to the same device as the model
            mel = whisper.log_mel_spectrogram(audio).to(self.model.device)
            
            # Detect the spoken language
            _, probs = self.model.detect_language(mel)
            detected_language = max(probs, key=probs.get)
            
            self.logger.info(f"Detected language: {detected_language}")
            return detected_language
            
        except Exception as e:
            self.logger.error(f"Error detecting language: {e}")
            return "en"  # Default to English
