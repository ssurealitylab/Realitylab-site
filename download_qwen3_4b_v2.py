#!/usr/bin/env python3
"""
Qwen3-4B Download Script - Alternative Method
Using transformers library for more reliable downloading
"""

import os
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

def download_qwen3_4b_transformers():
    print("🚀 Starting Qwen3-4B download using transformers...")
    
    try:
        # Set cache directory
        cache_dir = "/home/i0179/.cache/huggingface/hub"
        
        print("📥 Downloading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(
            "Qwen/Qwen3-4B", 
            cache_dir=cache_dir,
            trust_remote_code=True
        )
        print("✅ Tokenizer downloaded successfully!")
        
        print("📥 Downloading model (this will take time)...")
        model = AutoModelForCausalLM.from_pretrained(
            "Qwen/Qwen3-4B",
            cache_dir=cache_dir,
            trust_remote_code=True,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        print("✅ Model downloaded successfully!")
        
        print("🎉 Qwen3-4B download completed using transformers!")
        return True
        
    except Exception as e:
        print(f"❌ Error downloading Qwen3-4B: {e}")
        return False

if __name__ == "__main__":
    success = download_qwen3_4b_transformers()
    if success:
        print("🎉 Download completed!")
    else:
        print("💥 Download failed!")