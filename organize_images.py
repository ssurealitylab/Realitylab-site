#!/usr/bin/env python3
import os
import shutil
from datetime import datetime

def organize_images():
    base_path = "/home/i0179/Realitylab-site/참고 이미지/original_website"
    
    # Create organized directory structure
    organized_path = "/home/i0179/Realitylab-site/참고 이미지/organized_original_images"
    if not os.path.exists(organized_path):
        os.makedirs(organized_path)
    
    # Create subdirectories
    subdirs = ['homepage_main', 'member_photos', 'news_images', 'course_images', 'misc']
    for subdir in subdirs:
        subdir_path = os.path.join(organized_path, subdir)
        if not os.path.exists(subdir_path):
            os.makedirs(subdir_path)
    
    # Move and rename images
    counter = 1
    
    # Process main homepage images
    main_images = [f for f in os.listdir(base_path) if f.endswith('.jpg')]
    for img in main_images:
        src = os.path.join(base_path, img)
        dst = os.path.join(organized_path, 'homepage_main', f'homepage_{counter:02d}.jpg')
        shutil.copy2(src, dst)
        print(f"Moved {img} -> homepage_main/homepage_{counter:02d}.jpg")
        counter += 1
    
    # Process member photos
    members_path = os.path.join(base_path, 'members')
    if os.path.exists(members_path):
        counter = 1
        member_images = [f for f in os.listdir(members_path) if f.endswith('.jpg')]
        for img in member_images:
            src = os.path.join(members_path, img)
            dst = os.path.join(organized_path, 'member_photos', f'member_{counter:02d}.jpg')
            shutil.copy2(src, dst)
            print(f"Moved {img} -> member_photos/member_{counter:02d}.jpg")
            counter += 1
    
    # Process news images
    news_path = os.path.join(base_path, 'news')
    if os.path.exists(news_path):
        counter = 1
        news_images = [f for f in os.listdir(news_path) if f.endswith('.jpg')]
        for img in news_images:
            src = os.path.join(news_path, img)
            dst = os.path.join(organized_path, 'news_images', f'news_{counter:02d}.jpg')
            shutil.copy2(src, dst)
            print(f"Moved {img} -> news_images/news_{counter:02d}.jpg")
            counter += 1
    
    # Process course images
    courses_path = os.path.join(base_path, 'courses')
    if os.path.exists(courses_path):
        counter = 1
        course_images = [f for f in os.listdir(courses_path) if f.endswith('.jpg')]
        for img in course_images:
            src = os.path.join(courses_path, img)
            dst = os.path.join(organized_path, 'course_images', f'course_{counter:02d}.jpg')
            shutil.copy2(src, dst)
            print(f"Moved {img} -> course_images/course_{counter:02d}.jpg")
            counter += 1
    
    print(f"\nAll images organized in: {organized_path}")
    
    # Create summary
    summary_file = os.path.join(organized_path, 'image_summary.txt')
    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write(f"Reality Lab Original Website Images\n")
        f.write(f"Crawled on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Source: https://reality.ssu.ac.kr/\n\n")
        
        for subdir in subdirs:
            subdir_path = os.path.join(organized_path, subdir)
            if os.path.exists(subdir_path):
                count = len([f for f in os.listdir(subdir_path) if f.endswith('.jpg')])
                f.write(f"{subdir}: {count} images\n")
        
        f.write(f"\nTotal: {sum([len([f for f in os.listdir(os.path.join(organized_path, subdir)) if f.endswith('.jpg')]) for subdir in subdirs if os.path.exists(os.path.join(organized_path, subdir))])} images\n")
    
    print(f"Summary created: {summary_file}")

if __name__ == "__main__":
    organize_images()