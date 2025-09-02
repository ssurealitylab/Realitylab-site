#!/usr/bin/env python3
"""
Qwen3-4B Download Script
Uses huggingface_hub for reliable downloading
"""

import os
from huggingface_hub import snapshot_download
import time

def download_qwen3_4b():
    print("🚀 Starting Qwen3-4B download...")
    
    try:
        # Download complete model with resume capability and progress tracking
        model_path = snapshot_download(
            repo_id="Qwen/Qwen3-4B",
            resume_download=True,  # Resume if interrupted
            local_files_only=False,
            cache_dir=None,  # Use default cache
            force_download=False,  # Don't re-download existing files
            tqdm_class=None  # Show progress
        )
        
        print(f"✅ Qwen3-4B downloaded successfully to: {model_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading Qwen3-4B: {e}")
        return False

if __name__ == "__main__":
    success = download_qwen3_4b()
    if success:
        print("🎉 Qwen3-4B download completed!")
    else:
        print("💥 Qwen3-4B download failed!")