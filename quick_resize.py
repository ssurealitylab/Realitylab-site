#!/usr/bin/env python3
import os
from PIL import Image
import glob

def resize_all_sidl():
    count = 0
    for image_path in glob.glob("assets/img/sidl/**/*.png", recursive=True):
        if count % 10 == 0:
            print(f"Processed {count} images...")
        
        try:
            with Image.open(image_path) as img:
                # Resize to 50%
                new_width = int(img.width * 0.5)
                new_height = int(img.height * 0.5)
                resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
                resized_img.save(image_path, 'PNG', optimize=True)
                count += 1
        except Exception as e:
            print(f"Error processing {image_path}: {e}")
    
    print(f"Resized {count} images total!")

resize_all_sidl()