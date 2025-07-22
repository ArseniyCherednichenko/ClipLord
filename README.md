# 🎬 ClipLord - TikTok Video Generator

ClipLord is a powerful Python tool that automatically converts YouTube videos into TikTok-ready vertical shorts with styled subtitles. It downloads videos, crops them to 9:16 aspect ratio, generates subtitles using AI, and trims videos at natural speech breaks.

## ✨ Features

- **Automatic Video Download**: Download YouTube videos in high quality using `yt-dlp`
- **Smart Cropping**: Convert any video to TikTok's 9:16 vertical format
- **AI Subtitles**: Generate accurate subtitles using OpenAI Whisper
- **Intelligent Trimming**: Automatically trim videos at natural sentence endings
- **Styled Subtitles**: Add TikTok-style subtitles with proper formatting
- **Batch Processing**: Process multiple videos at once
- **Error Handling**: Robust error handling and progress reporting

## 🚀 Quick Start

### Prerequisites

- Python 3.9 or higher
- FFmpeg installed on your system
- At least 4GB of RAM (8GB recommended)
- Stable internet connection

### Installation

1. **Clone or download the ClipLord files**
   ```bash
   # Create a new directory
   mkdir cliplord
   cd cliplord
   
   # Copy all the Python files to this directory
   ```

2. **Install FFmpeg**
   
   **Windows:**
   - Download from [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)
   - Add to system PATH
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

3. **Set up Python virtual environment** (recommended)
   ```bash
   python -m venv venv
   
   # Activate virtual environment
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

### First Run

```bash
python main.py
```

The script will prompt you to enter YouTube URLs. You can enter multiple URLs separated by commas:

```
🎬 ClipLord - TikTok Video Generator
==================================================
Paste YouTube video URL(s) (comma-separated): https://www.youtube.com/watch?v=example123
```

## 📖 Usage Examples

### Single Video
```bash
python main.py
# Enter: https://www.youtube.com/watch?v=dQw4w9WgXcQ
```

### Multiple Videos
```bash
python main.py
# Enter: https://www.youtube.com/watch?v=video1, https://www.youtube.com/watch?v=video2
```

### Expected Output
```
🎬 ClipLord - TikTok Video Generator
==================================================
Paste YouTube video URL(s) (comma-separated): https://www.youtube.com/watch?v=example

🔄 Processing video 1/1
URL: https://www.youtube.com/watch?v=example
📥 Downloading video...
✅ Downloaded: Example Gym Workout Video
🎤 Generating subtitles...
✅ Generated 45 subtitle segments
✂️ Processing and cropping to 9:16...
✂️ Trimmed video to 32.5 seconds
📝 Added subtitles to video
✅ Video processed successfully!
📁 Output: output/Example_Gym_Workout_Video_tiktok.mp4
⏱️ Duration: 32.5 seconds

🎉 Process Complete!
✅ Successfully processed: 1/1 videos
📁 Output directory: /path/to/cliplord/output
🚀 Your TikTok-ready videos are ready for upload!
```

## 📁 Project Structure

```
cliplord/
├── main.py           # Main orchestration script
├── downloader.py     # YouTube video downloading
├── processor.py      # Video processing and cropping
├── subtitle.py       # Subtitle generation with Whisper
├── utils.py          # Utility functions
├── requirements.txt  # Python dependencies
├── README.md         # This file
└── output/           # Generated videos (created automatically)
```

## ⚙️ Configuration

### Whisper Model Selection

Edit `subtitle.py` to change the Whisper model:

```python
# In subtitle.py, line 24
def __init__(self, model_name: str = "base"):
```

Available models (larger = more accurate but slower):
- `tiny` - Fastest, least accurate
- `base` - Good balance (default)
- `small` - Better accuracy
- `medium` - High accuracy
- `large` - Best accuracy, slowest

### Video Duration Settings

Edit `main.py` to change target duration:

```python
# In main.py, line 89
target_duration_range=(15, 60)  # Min: 15s, Max: 60s
```

### Output Resolution

Edit `processor.py` to change output resolution:

```python
# In processor.py, lines 30-31
self.target_width = 1080
self.target_height = 1920
```

## 🔧 Troubleshooting

### Common Issues

**"FFmpeg not found"**
- Install FFmpeg and ensure it's in your system PATH
- Restart your terminal/command prompt after installation

**"No module named 'whisper'"**
- Ensure you're in the virtual environment: `source venv/bin/activate`
- Reinstall dependencies: `pip install -r requirements.txt`

**"Video unavailable" or "403 error"**
- Video might be private, age-restricted, or geo-blocked
- Try a different video URL

**Out of memory errors**
- Close other applications
- Use a smaller Whisper model (`tiny` or `base`)
- Process one video at a time

**Slow processing**
- Use `tiny` or `base` Whisper model for faster processing
- Ensure you have adequate RAM and CPU

### Performance Optimization

1. **Use smaller Whisper model** for faster processing
2. **Close unnecessary applications** to free up RAM
3. **Use SSD storage** for better I/O performance
4. **Process shorter videos** first to test setup

## 📊 System Requirements

### Minimum Requirements
- Python 3.9+
- 4GB RAM
- 2GB free disk space
- FFmpeg installed

### Recommended Requirements
- Python 3.10+
- 8GB+ RAM
- 5GB+ free disk space
- SSD storage
- Good internet connection

## 🎯 Advanced Usage

### Custom Output Directory

Modify `main.py` to change output directory:

```python
# Line 45 in main.py
output_dir = Path("my_custom_output")
```

### Export SRT Files

Add SRT export in `main.py`:

```python
# After subtitle generation
if subtitles:
    srt_path = output_dir / f"{video_title}.srt"
    subtitle_gen.export_srt(subtitles, srt_path)
```

### Batch Processing from File

Create a text file with URLs (one per line) and modify `main.py`:

```python
# Read URLs from file instead of input
with open('urls.txt', 'r') as f:
    urls = [line.strip() for line in f if line.strip()]
```

## 🐛 Known Limitations

- May not work with private or age-restricted videos
- Processing time depends on video length and system specs
- Some videos might have sync issues with very fast speech
- Subtitle styling is basic (can be enhanced)

## 🆘 Support

If you encounter issues:

1. Check this README for common solutions
2. Verify all dependencies are installed correctly
3. Test with a known working YouTube URL
4. Check system resources (RAM, disk space)

## 📝 License

This project is for educational and personal use. Respect YouTube's Terms of Service and copyright laws when downloading content.

## 🔄 Updates

To update dependencies:
```bash
pip install --upgrade -r requirements.txt
```

---

**Happy video creating! 🎬✨**