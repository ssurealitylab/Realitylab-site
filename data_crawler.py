#!/usr/bin/env python3
"""
Reality Lab Website Data Crawler
Extracts all content for LLM training dataset
"""

import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urljoin, urlparse
import re
from datetime import datetime

class RealityLabCrawler:
    def __init__(self):
        self.base_url = "https://reality.ssu.ac.kr"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        self.crawled_urls = set()
        self.dataset = []
        
    def clean_text(self, text):
        """Clean and normalize text content"""
        if not text:
            return ""
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep Korean, English, numbers, basic punctuation
        text = re.sub(r'[^\w\s가-힣.,!?;:()\-\[\]{}\'\"/@#%&*+=<>]', '', text)
        return text.strip()
    
    def extract_page_content(self, url, soup):
        """Extract structured content from a page"""
        content_data = {
            'url': url,
            'title': '',
            'content': '',
            'metadata': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            content_data['title'] = self.clean_text(title_tag.get_text())
        
        # Extract main content areas
        content_sections = []
        
        # Look for main content containers
        main_containers = soup.find_all(['main', 'article', 'div'], 
                                      class_=re.compile(r'content|main|article|post'))
        
        if not main_containers:
            # Fallback to body content
            main_containers = [soup.find('body')]
        
        for container in main_containers:
            if container:
                # Extract text content
                text_content = self.clean_text(container.get_text())
                if text_content and len(text_content) > 50:  # Only meaningful content
                    content_sections.append(text_content)
        
        # Extract specific sections
        sections = {
            'headings': [],
            'paragraphs': [],
            'lists': [],
            'links': []
        }
        
        # Extract headings
        for heading in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
            heading_text = self.clean_text(heading.get_text())
            if heading_text:
                sections['headings'].append(heading_text)
        
        # Extract paragraphs
        for p in soup.find_all('p'):
            p_text = self.clean_text(p.get_text())
            if p_text and len(p_text) > 20:
                sections['paragraphs'].append(p_text)
        
        # Extract lists
        for ul in soup.find_all(['ul', 'ol']):
            list_items = [self.clean_text(li.get_text()) for li in ul.find_all('li')]
            list_items = [item for item in list_items if item]
            if list_items:
                sections['lists'].append(list_items)
        
        # Extract internal links
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('/') or 'reality.ssu.ac.kr' in href:
                full_url = urljoin(self.base_url, href)
                link_text = self.clean_text(link.get_text())
                if link_text:
                    sections['links'].append({'url': full_url, 'text': link_text})
        
        # Combine all content
        all_content = []
        if sections['headings']:
            all_content.extend(sections['headings'])
        if sections['paragraphs']:
            all_content.extend(sections['paragraphs'])
        if sections['lists']:
            for list_items in sections['lists']:
                all_content.extend(list_items)
        
        content_data['content'] = '\n\n'.join(all_content)
        content_data['metadata'] = sections
        
        return content_data
    
    def crawl_page(self, url):
        """Crawl a single page"""
        if url in self.crawled_urls:
            return None
            
        print(f"Crawling: {url}")
        self.crawled_urls.add(url)
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            content_data = self.extract_page_content(url, soup)
            
            # Find additional internal links to crawl
            internal_links = []
            for link in soup.find_all('a', href=True):
                href = link['href']
                if href.startswith('/') or 'reality.ssu.ac.kr' in href:
                    full_url = urljoin(self.base_url, href)
                    if full_url not in self.crawled_urls and self.is_valid_url(full_url):
                        internal_links.append(full_url)
            
            return content_data, internal_links
            
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            return None
    
    def is_valid_url(self, url):
        """Check if URL should be crawled"""
        # Skip external links, files, etc.
        skip_extensions = ['.pdf', '.jpg', '.png', '.gif', '.css', '.js', '.ico']
        skip_patterns = ['mailto:', 'tel:', '#', 'javascript:']
        
        for ext in skip_extensions:
            if url.lower().endswith(ext):
                return False
        
        for pattern in skip_patterns:
            if pattern in url.lower():
                return False
        
        return True
    
    def crawl_all(self):
        """Crawl all pages starting from the main page"""
        # Start with main page and known sections
        urls_to_crawl = [
            f"{self.base_url}/",
            f"{self.base_url}/news",
            f"{self.base_url}/members",
            f"{self.base_url}/publication/international",
            f"{self.base_url}/publication/domestic", 
            f"{self.base_url}/courses"
        ]
        
        while urls_to_crawl:
            url = urls_to_crawl.pop(0)
            result = self.crawl_page(url)
            
            if result:
                if isinstance(result, tuple):
                    content_data, new_links = result
                    self.dataset.append(content_data)
                    # Add new links to crawl
                    for link in new_links:
                        if link not in urls_to_crawl and link not in self.crawled_urls:
                            urls_to_crawl.append(link)
                else:
                    self.dataset.append(result)
            
            # Be polite to the server
            time.sleep(1)
    
    def save_dataset(self):
        """Save the dataset in multiple formats for LLM training"""
        os.makedirs('reality_lab_dataset', exist_ok=True)
        
        # Save as JSON for structured access
        with open('reality_lab_dataset/raw_data.json', 'w', encoding='utf-8') as f:
            json.dump(self.dataset, f, ensure_ascii=False, indent=2)
        
        # Save as plain text for training
        with open('reality_lab_dataset/training_text.txt', 'w', encoding='utf-8') as f:
            for item in self.dataset:
                if item['content']:
                    f.write(f"# {item['title']}\n\n")
                    f.write(f"{item['content']}\n\n")
                    f.write("---\n\n")
        
        # Save as Q&A format for instruction tuning
        qa_dataset = []
        for item in self.dataset:
            if item['content'] and len(item['content']) > 100:
                # Create potential Q&A pairs
                if 'news' in item['url'].lower():
                    qa_dataset.append({
                        "instruction": "Reality Lab의 최근 뉴스를 알려주세요.",
                        "input": "",
                        "output": item['content']
                    })
                elif 'member' in item['url'].lower():
                    qa_dataset.append({
                        "instruction": "Reality Lab의 구성원에 대해 알려주세요.",
                        "input": "",
                        "output": item['content']
                    })
                elif 'publication' in item['url'].lower():
                    qa_dataset.append({
                        "instruction": "Reality Lab의 연구 논문과 출간물을 알려주세요.",
                        "input": "",
                        "output": item['content']
                    })
                elif 'course' in item['url'].lower():
                    qa_dataset.append({
                        "instruction": "Reality Lab에서 제공하는 강의나 교육과정을 알려주세요.",
                        "input": "",
                        "output": item['content']
                    })
                else:
                    qa_dataset.append({
                        "instruction": f"{item['title']}에 대해 설명해주세요.",
                        "input": "",
                        "output": item['content']
                    })
        
        with open('reality_lab_dataset/qa_dataset.json', 'w', encoding='utf-8') as f:
            json.dump(qa_dataset, f, ensure_ascii=False, indent=2)
        
        # Save summary statistics
        stats = {
            'total_pages': len(self.dataset),
            'total_characters': sum(len(item['content']) for item in self.dataset),
            'average_content_length': sum(len(item['content']) for item in self.dataset) / len(self.dataset) if self.dataset else 0,
            'urls_crawled': list(self.crawled_urls),
            'qa_pairs': len(qa_dataset)
        }
        
        with open('reality_lab_dataset/statistics.json', 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"\n데이터셋 저장 완료!")
        print(f"총 페이지 수: {stats['total_pages']}")
        print(f"총 텍스트 길이: {stats['total_characters']:,} 문자")
        print(f"평균 페이지 길이: {stats['average_content_length']:.1f} 문자")
        print(f"Q&A 쌍: {stats['qa_pairs']}개")
        print(f"저장 경로: ./reality_lab_dataset/")

if __name__ == "__main__":
    crawler = RealityLabCrawler()
    print("Reality Lab 웹사이트 데이터 수집을 시작합니다...")
    crawler.crawl_all()
    crawler.save_dataset()