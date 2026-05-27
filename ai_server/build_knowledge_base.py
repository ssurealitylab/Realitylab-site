#!/usr/bin/env python3
"""
Reality Lab Knowledge Base Builder
Extracts information from website data files and creates a knowledge base for RAG
"""

import yaml
import json
import re
from pathlib import Path
from typing import List, Dict, Any

class KnowledgeBaseBuilder:
    def __init__(self, site_root: str):
        self.site_root = Path(site_root)
        self.data_dir = self.site_root / "_data"
        self.documents = []

    def load_yaml(self, filename: str) -> Dict:
        """Load YAML file"""
        with open(self.data_dir / filename, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)

    def add_document(self, content: str, metadata: Dict[str, Any]):
        """Add a document to the knowledge base"""
        self.documents.append({
            "content": content,
            "metadata": metadata
        })

    def build_lab_info_docs(self):
        """Build documents from basic lab info"""
        kb = self.load_yaml("chatbot_knowledge.yml")

        # Korean lab info
        lab_ko = kb['lab_info']['ko']
        content_ko = f"""연구실 정보:
이름: {lab_ko['full_name']}
설립: {lab_ko['established']}년
위치: {lab_ko['location']}
책임교수: {lab_ko['director']}
이메일: {lab_ko['email']}
전화: {lab_ko['phone']}
미션: {lab_ko['mission']}
비전: {lab_ko['vision']}"""

        self.add_document(content_ko, {
            "type": "lab_info",
            "language": "ko",
            "category": "basic_info"
        })

        # English lab info
        lab_en = kb['lab_info']['en']
        content_en = f"""Lab Information:
Name: {lab_en['full_name']}
Established: {lab_en['established']}
Location: {lab_en['location']}
Director: {lab_en['director']}
Email: {lab_en['email']}
Phone: {lab_en['phone']}
Mission: {lab_en['mission']}
Vision: {lab_en['vision']}"""

        self.add_document(content_en, {
            "type": "lab_info",
            "language": "en",
            "category": "basic_info"
        })

    def build_research_area_docs(self):
        """Build documents from research areas"""
        kb = self.load_yaml("chatbot_knowledge.yml")

        for area in kb['research_areas']:
            # Korean
            area_ko = area['ko']
            content_ko = f"""연구 분야: {area_ko['name']}
설명: {area_ko['description']}
키워드: {', '.join(area_ko['keywords'])}"""

            self.add_document(content_ko, {
                "type": "research_area",
                "language": "ko",
                "category": "research",
                "area_name": area_ko['name']
            })

            # English
            area_en = area['en']
            content_en = f"""Research Area: {area_en['name']}
Description: {area_en['description']}
Keywords: {', '.join(area_en['keywords'])}"""

            self.add_document(content_en, {
                "type": "research_area",
                "language": "en",
                "category": "research",
                "area_name": area_en['name']
            })

    def build_member_docs(self):
        """Build documents from member information"""
        members = self.load_yaml("members.yml")

        # Faculty
        for faculty in members.get('faculty', []):
            content_ko = f"""교수진: {faculty['name_ko']} ({faculty['name']})
직책: {faculty['position']}
소속: {faculty['affiliation']}
이메일: {faculty['email']}"""

            self.add_document(content_ko, {
                "type": "member",
                "language": "ko",
                "category": "faculty",
                "name": faculty['name'],
                "name_ko": faculty['name_ko'],
                "email": faculty['email']
            })

        # PhD Students (was missing — chatbot didn't know about 박성용 / Sungyong Park)
        for student in members.get('students', {}).get('phd_students', []):
            achievements_str = f"\n주요 성과: {', '.join(student['achievements'])}" if student.get('achievements') else ""
            content_ko = f"""박사과정 학생: {student['name_ko']} ({student['name']})
연구 분야: {student['research']}{achievements_str}"""

            github = f"\nGitHub: {student['github']}" if student.get('github') else ""
            linkedin = f"\nLinkedIn: {student['linkedin']}" if student.get('linkedin') else ""

            self.add_document(content_ko + github + linkedin, {
                "type": "member",
                "language": "ko",
                "category": "phd_student",
                "name": student['name'],
                "name_ko": student['name_ko'],
                "research": student['research']
            })

        # MS Students
        for student in members.get('students', {}).get('ms_students', []):
            achievements_str = f"\n주요 성과: {', '.join(student['achievements'])}" if student.get('achievements') else ""
            content_ko = f"""석사과정 학생: {student['name_ko']} ({student['name']})
연구 분야: {student['research']}{achievements_str}"""

            github = f"\nGitHub: {student['github']}" if student.get('github') else ""
            linkedin = f"\nLinkedIn: {student['linkedin']}" if student.get('linkedin') else ""

            self.add_document(content_ko + github + linkedin, {
                "type": "member",
                "language": "ko",
                "category": "ms_student",
                "name": student['name'],
                "name_ko": student['name_ko'],
                "research": student['research']
            })

        # Interns
        for intern in members.get('students', {}).get('interns', []):
            content_ko = f"""인턴: {intern['name_ko']} ({intern['name']})
연구 분야: {intern['research']}"""

            github = f"\nGitHub: {intern['github']}" if intern.get('github') else ""
            linkedin = f"\nLinkedIn: {intern['linkedin']}" if intern.get('linkedin') else ""

            self.add_document(content_ko + github + linkedin, {
                "type": "member",
                "language": "ko",
                "category": "intern",
                "name": intern['name'],
                "name_ko": intern['name_ko'],
                "research": intern['research']
            })

    def build_news_docs(self):
        """Build documents from news.yml"""
        news_data = self.load_yaml("news.yml")
        news_list = news_data.get('news', [])
        for item in news_list:
            title = item.get('title', '')
            date = item.get('date', '')
            category = item.get('category', '')
            participants = item.get('participants', [])
            description = item.get('description', '')
            participants_str = ', '.join(participants) if participants else ''

            content_ko = f"""뉴스: {title}
날짜: {date}
카테고리: {category}
참여자: {participants_str}
내용: {description}"""

            content_en = f"""News: {title}
Date: {date}
Category: {category}
Participants: {participants_str}
Description: {description}"""

            self.add_document(content_ko, {
                "type": "news",
                "language": "ko",
                "category": category.lower(),
                "title": title,
                "date": date,
                "participants": participants
            })

            self.add_document(content_en, {
                "type": "news",
                "language": "en",
                "category": category.lower(),
                "title": title,
                "date": date,
                "participants": participants
            })

    def extract_publications_from_yml(self):
        """Extract publication information from publications.yml"""
        pub_data = self.load_yaml("publications.yml")
        pub_list = pub_data.get('publications', [])
        total = len(pub_list)

        for idx, pub in enumerate(pub_list):
            title = pub.get('title', '')
            authors = pub.get('authors', '')
            year = pub.get('year', 2025)
            venue = pub.get('venue', '')
            venue_short = pub.get('venue_short', '')
            pub_type = pub.get('type', 'conference')
            status = pub.get('status', '')
            abstract = pub.get('abstract', '')

            # idx 0 = most recent (listed first in YAML)
            recency = f"최신순 {idx+1}/{total}위" if idx < 5 else ""
            recency_en = f"Recency rank: {idx+1}/{total}" if idx < 5 else ""

            content_text = f"""논문: {title}
저자: {authors}
연도: {year}
학회: {venue} ({venue_short})
{f'최신 논문 순위: {recency}' if recency else ''}
{f'초록: {abstract}' if abstract else ''}

Publication: {title}
Authors: {authors}
Year: {year}
Venue: {venue} ({venue_short})
{f'Recency: {recency_en}' if recency_en else ''}
{f'Abstract: {abstract}' if abstract else ''}"""

            self.add_document(content_text, {
                "type": "publication",
                "language": "both",
                "category": "paper",
                "title": title,
                "authors": authors,
                "year": str(year),
                "venue": venue_short,
                "recency_rank": idx + 1
            })

    def build_qa_docs(self):
        """Build documents from custom Q&A pairs"""
        kb = self.load_yaml("chatbot_knowledge.yml")

        # Korean Q&A
        for qa in kb['custom_qa']['ko']:
            content_ko = f"""질문: {qa['question']}
답변: {qa['answer']}
키워드: {', '.join(qa['keywords'])}"""

            self.add_document(content_ko, {
                "type": "qa",
                "language": "ko",
                "category": "faq",
                "question": qa['question']
            })

        # English Q&A
        for qa in kb['custom_qa']['en']:
            content_en = f"""Question: {qa['question']}
Answer: {qa['answer']}
Keywords: {', '.join(qa['keywords'])}"""

            self.add_document(content_en, {
                "type": "qa",
                "language": "en",
                "category": "faq",
                "question": qa['question']
            })

    def build(self):
        """Build the complete knowledge base"""
        print("Building knowledge base...")

        print("- Extracting lab info...")
        self.build_lab_info_docs()

        print("- Extracting research areas...")
        self.build_research_area_docs()

        print("- Extracting member information...")
        self.build_member_docs()

        print("- Extracting news...")
        self.build_news_docs()

        print("- Extracting publications...")
        self.extract_publications_from_yml()

        print("- Extracting Q&A pairs...")
        self.build_qa_docs()

        print(f"\nTotal documents created: {len(self.documents)}")
        return self.documents

    def save_to_json(self, output_file: str):
        """Save knowledge base to JSON file"""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(self.documents, f, ensure_ascii=False, indent=2)

        print(f"\nKnowledge base saved to: {output_path}")
        print(f"Total size: {output_path.stat().st_size / 1024:.2f} KB")


def main():
    # Build knowledge base
    site_root = "/home/i0179/Realitylab-site"
    builder = KnowledgeBaseBuilder(site_root)

    documents = builder.build()

    # Save to JSON
    output_file = "/home/i0179/Realitylab-site/ai_server/knowledge_base.json"
    builder.save_to_json(output_file)

    # Print statistics
    print("\n=== Knowledge Base Statistics ===")
    types = {}
    for doc in documents:
        doc_type = doc['metadata']['type']
        types[doc_type] = types.get(doc_type, 0) + 1

    for doc_type, count in types.items():
        print(f"  {doc_type}: {count} documents")


if __name__ == "__main__":
    main()
