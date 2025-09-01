#!/usr/bin/env python3
"""
Complete Gemma2 Download Script
Uses huggingface_hub for reliable downloading
"""

import os
from huggingface_hub import snapshot_download
import time

def download_gemma2_complete():
    print("🚀 Starting complete Gemma2-9B download...")
    
    try:
        # Download complete model with resume capability and progress tracking
        model_path = snapshot_download(
            repo_id="google/gemma-2-9b-it",
            resume_download=True,  # Resume if interrupted
            local_files_only=False,
            cache_dir=None,  # Use default cache
            force_download=False,  # Don't re-download existing files
            tqdm_class=None  # Show progress
        )
        
        print(f"✅ Complete Gemma2-9B downloaded successfully to: {model_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading Gemma2: {e}")
        return False

if __name__ == "__main__":
    success = download_gemma2_complete()
    if success:
        print("📁 Complete download finished! You can now start the Gemma2 server.")
        print("🎉 All model files downloaded successfully!")
    else:
        print("💥 Download failed. Check your internet connection.")