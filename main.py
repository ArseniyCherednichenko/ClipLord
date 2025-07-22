#!/usr/bin/env python3
"""
ClipLord - TikTok Video Generator
Main script that orchestrates the entire pipeline
"""

import os
import sys
import argparse
from pathlib import Path
import logging
from typing import List, Optional

from downloader import VideoDownloader
from processor import VideoProcessor
from subtitle import SubtitleGenerator
from utils import setup_logging, validate_url, clean_filename, handle_error

def main():
    """Main function to orchestrate the video processing pipeline"""
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    print("🎬 ClipLord - TikTok Video Generator")
    print("=" * 50)
    
    # Get YouTube URLs from user
    urls_input = input("Paste YouTube video URL(s) (comma-separated): ").strip()
    if not urls_input:
        print("❌ No URLs provided. Exiting...")
        return
    
    # Parse and validate URLs
    urls = [url.strip() for url in urls_input.split(',')]
    valid_urls = []
    
    for url in urls:
        if validate_url(url):
            valid_urls.append(url)
        else:
            print(f"❌ Invalid URL: {url}")
    
    if not valid_urls:
        print("❌ No valid URLs provided. Exiting...")
        return
    
    # Create output directory
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    
    # Initialize components
    downloader = VideoDownloader()
    processor = VideoProcessor()
    subtitle_gen = SubtitleGenerator()
    
    successful_processes = 0
    
    # Process each URL
    for i, url in enumerate(valid_urls, 1):
        print(f"\n🔄 Processing video {i}/{len(valid_urls)}")
        print(f"URL: {url}")
        
        try:
            # Step 1: Download video
            print("📥 Downloading video...")
            video_path, video_info = downloader.download(url)
            if not video_path:
                print("❌ Failed to download video")
                continue
            
            video_title = clean_filename(video_info.get('title', 'unknown'))
            print(f"✅ Downloaded: {video_title}")
            
            # Step 2: Generate subtitles
            print("🎤 Generating subtitles...")
            subtitles = subtitle_gen.generate_subtitles(video_path)
            if not subtitles:
                print("⚠️ No subtitles generated, continuing without subtitles...")
            else:
                print(f"✅ Generated {len(subtitles)} subtitle segments")
            
            # Step 3: Process video (crop, trim, add subtitles)
            print("✂️ Processing and cropping to 9:16...")
            output_filename = f"{video_title}_tiktok.mp4"
            output_path = output_dir / output_filename
            
            processed_path = processor.process_video(
                video_path=video_path,
                subtitles=subtitles,
                output_path=output_path,
                target_duration_range=(15, 60)
            )
            
            if processed_path:
                duration = processor.get_video_duration(processed_path)
                print(f"✅ Video processed successfully!")
                print(f"📁 Output: {processed_path}")
                print(f"⏱️ Duration: {duration:.1f} seconds")
                successful_processes += 1
            else:
                print("❌ Failed to process video")
            
            # Cleanup temporary files
            try:
                os.remove(video_path)
            except:
                pass
                
        except Exception as e:
            error_msg = handle_error(e, f"processing video from {url}")
            print(f"❌ {error_msg}")
            logger.error(f"Error processing {url}: {e}")
            continue
    
    # Summary
    print(f"\n🎉 Process Complete!")
    print(f"✅ Successfully processed: {successful_processes}/{len(valid_urls)} videos")
    print(f"📁 Output directory: {output_dir.absolute()}")
    
    if successful_processes > 0:
        print("\n🚀 Your TikTok-ready videos are ready for upload!")

if __name__ == "__main__":
    main()