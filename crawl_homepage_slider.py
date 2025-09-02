#!/usr/bin/env python3
"""
Reality Lab Homepage Slider Images Crawler
Crawls slider images from the original Reality Lab website
"""

import requests
from bs4 import BeautifulSoup
import os
import time
from urllib.parse import urljoin, urlparse
import re

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def download_image(url, filepath):
    """Download image from URL to filepath"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(filepath, 'wb') as f:
            f.write(response.content)
        print(f"Downloaded: {os.path.basename(filepath)} ({len(response.content)} bytes)")
        return True
    except Exception as e:
        print(f"Failed to download {url}: {e}")
        return False

def crawl_homepage_slider():
    """Crawl slider images from Reality Lab homepage"""
    base_url = "https://reality.ssu.ac.kr/"
    output_dir = "참고 이미지/homepage_slider_images"
    
    # Create output directory
    create_directory(output_dir)
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"Fetching homepage: {base_url}")
        response = requests.get(base_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Look for slider images - common selectors
        slider_images = []
        
        # Try different slider selectors
        selectors = [
            '.slider img',
            '.carousel img', 
            '.swiper-slide img',
            '.slide img',
            '.banner img',
            '#slider img',
            '#carousel img',
            '[class*="slider"] img',
            '[class*="carousel"] img',
            '[class*="slide"] img',
            '.main-slider img',
            '.hero-slider img'
        ]
        
        for selector in selectors:
            images = soup.select(selector)
            for img in images:
                src = img.get('src') or img.get('data-src') or img.get('data-lazy')
                if src:
                    if not src.startswith('http'):
                        src = urljoin(base_url, src)
                    slider_images.append(src)
        
        # Also look for background images in CSS
        css_images = []
        for element in soup.find_all(attrs={'style': True}):
            style = element.get('style', '')
            bg_matches = re.findall(r'background-image\s*:\s*url\(["\']?([^"\']+)["\']?\)', style)
            for match in bg_matches:
                if not match.startswith('http'):
                    match = urljoin(base_url, match)
                css_images.append(match)
        
        all_images = list(set(slider_images + css_images))
        
        print(f"Found {len(all_images)} potential slider images:")
        for i, img_url in enumerate(all_images, 1):
            print(f"  {i}. {img_url}")
        
        # Download images
        downloaded = 0
        for i, img_url in enumerate(all_images, 1):
            try:
                # Get file extension from URL
                parsed = urlparse(img_url)
                ext = os.path.splitext(parsed.path)[1] or '.jpg'
                filename = f"slider_{i:02d}{ext}"
                filepath = os.path.join(output_dir, filename)
                
                if download_image(img_url, filepath):
                    downloaded += 1
                
                time.sleep(1)  # Be respectful
                
            except Exception as e:
                print(f"Error processing image {i}: {e}")
        
        print(f"\nCompleted! Downloaded {downloaded} slider images to {output_dir}")
        
        # Create summary
        summary_file = os.path.join(output_dir, "slider_summary.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write("Reality Lab Homepage Slider Images\n")
            f.write(f"Crawled on: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Source: {base_url}\n\n")
            f.write(f"Total images found: {len(all_images)}\n")
            f.write(f"Successfully downloaded: {downloaded}\n\n")
            f.write("Image URLs:\n")
            for i, url in enumerate(all_images, 1):
                f.write(f"{i}. {url}\n")
        
        return downloaded
        
    except Exception as e:
        print(f"Error crawling homepage: {e}")
        return 0

if __name__ == "__main__":
    print("Reality Lab Homepage Slider Crawler")
    print("=" * 40)
    crawl_homepage_slider()