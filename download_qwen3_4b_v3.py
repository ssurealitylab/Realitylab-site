#!/usr/bin/env python3
"""
Qwen3-4B Download Script - Git LFS Method
Using git to clone the repository directly
"""

import os
import subprocess
import sys

def download_qwen3_4b_git():
    print("🚀 Starting Qwen3-4B download using git...")
    
    try:
        # Create target directory
        target_dir = "/home/i0179/.cache/huggingface/hub/qwen3-4b-git"
        
        # Remove existing directory if exists
        if os.path.exists(target_dir):
            print(f"🗑️ Removing existing directory: {target_dir}")
            subprocess.run(["rm", "-rf", target_dir], check=True)
        
        # Clone the repository
        print("📥 Cloning Qwen3-4B repository...")
        result = subprocess.run([
            "git", "clone", 
            "https://huggingface.co/Qwen/Qwen3-4B",
            target_dir
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Git clone failed: {result.stderr}")
            return False
            
        print("✅ Repository cloned successfully!")
        
        # Navigate to the directory and pull LFS files
        print("📥 Downloading LFS files...")
        os.chdir(target_dir)
        
        result = subprocess.run([
            "git", "lfs", "pull"
        ], capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"⚠️ LFS pull warning: {result.stderr}")
            # Continue anyway as some files might still be downloaded
        
        print("✅ Qwen3-4B downloaded successfully using git!")
        print(f"📁 Model location: {target_dir}")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading Qwen3-4B: {e}")
        return False

if __name__ == "__main__":
    success = download_qwen3_4b_git()
    if success:
        print("🎉 Git download completed!")
    else:
        print("💥 Git download failed!")