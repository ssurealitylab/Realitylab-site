#!/usr/bin/env python3
import os
from PIL import Image
import glob

def resize_images(input_dir, output_dir, scale=0.5):
    """Resize images to reduce file size"""
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    for image_path in glob.glob(os.path.join(input_dir, "*.png")):
        print(f"Resizing {image_path}...")
        
        # Open image
        with Image.open(image_path) as img:
            # Calculate new size
            new_width = int(img.width * scale)
            new_height = int(img.height * scale)
            
            # Resize image
            resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Save to output directory
            filename = os.path.basename(image_path)
            output_path = os.path.join(output_dir, filename)
            
            # Save with optimization
            resized_img.save(output_path, "PNG", optimize=True)
            
            # Check file size reduction
            original_size = os.path.getsize(image_path)
            new_size = os.path.getsize(output_path)
            reduction = (1 - new_size/original_size) * 100
            print(f"  {filename}: {original_size//1024}KB -> {new_size//1024}KB ({reduction:.1f}% reduction)")

# Process all SIDL image directories
base_dir = "assets/img/sidl"
categories = ["dust", "finger", "mixed", "scratch", "water"]
types = ["input", "target"]

for category in categories:
    for img_type in types:
        input_dir = os.path.join(base_dir, category, img_type)
        if os.path.exists(input_dir):
            print(f"\nProcessing {category}/{img_type}...")
            resize_images(input_dir, input_dir, scale=0.5)

print("\nImage resizing complete!")