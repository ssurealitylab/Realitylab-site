#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
import os
import urllib.parse
from urllib.request import urlretrieve
import time

def create_directory(path):
    """Create directory if it doesn't exist"""
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Created directory: {path}")

def get_filename_from_url(url):
    """Extract filename from URL"""
    parsed = urllib.parse.urlparse(url)
    filename = os.path.basename(parsed.path)
    if not filename or '.' not in filename:
        # Generate filename from URL hash if no proper filename
        filename = f"image_{hash(url) % 10000}.jpg"
    return filename

def download_image(img_url, save_path, base_url):
    """Download a single image"""
    try:
        # Handle relative URLs
        if not img_url.startswith(('http://', 'https://')):
            img_url = urllib.parse.urljoin(base_url, img_url)
        
        filename = get_filename_from_url(img_url)
        filepath = os.path.join(save_path, filename)
        
        # Skip if file already exists
        if os.path.exists(filepath):
            print(f"Skipping existing file: {filename}")
            return False
            
        print(f"Downloading: {img_url}")
        urlretrieve(img_url, filepath)
        print(f"Saved: {filename}")
        return True
        
    except Exception as e:
        print(f"Error downloading {img_url}: {e}")
        return False

def crawl_images_from_website(url, output_dir):
    """Crawl images from a website"""
    try:
        print(f"Crawling images from: {url}")
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Find all img tags
        img_tags = soup.find_all('img')
        print(f"Found {len(img_tags)} images")
        
        downloaded_count = 0
        for img in img_tags:
            img_url = img.get('src') or img.get('data-src') or img.get('data-original')
            if img_url:
                if download_image(img_url, output_dir, url):
                    downloaded_count += 1
                time.sleep(0.5)  # Be polite to the server
        
        print(f"Downloaded {downloaded_count} new images")
        
    except Exception as e:
        print(f"Error crawling website: {e}")

def main():
    base_url = "https://reality.ssu.ac.kr/"
    output_base = "/home/i0179/Realitylab-site/참고 이미지"
    
    # Create main output directory
    create_directory(output_base)
    
    # Create subdirectory for original website images
    original_images_dir = os.path.join(output_base, "original_website")
    create_directory(original_images_dir)
    
    print("Starting image crawling from Reality Lab website...")
    crawl_images_from_website(base_url, original_images_dir)
    
    # Also try to crawl from common subpages
    subpages = [
        "members/",
        "research/",
        "publications/", 
        "courses/",
        "news/"
    ]
    
    for subpage in subpages:
        subpage_url = urllib.parse.urljoin(base_url, subpage)
        subpage_dir = os.path.join(original_images_dir, subpage.rstrip('/'))
        create_directory(subpage_dir)
        
        print(f"\nCrawling subpage: {subpage_url}")
        crawl_images_from_website(subpage_url, subpage_dir)
        time.sleep(1)  # Be extra polite
    
    print("\nImage crawling completed!")
    print(f"All images saved to: {original_images_dir}")

if __name__ == "__main__":
    main()