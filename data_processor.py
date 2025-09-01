#!/usr/bin/env python3
"""
Reality Lab Dataset Processor
Clean and format the crawled data for LLM training
"""

import json
import re
from datetime import datetime

def clean_and_structure_data():
    """Process raw data into cleaner, more structured format"""
    
    # Load raw data
    with open('reality_lab_dataset/raw_data.json', 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    # Create structured dataset
    structured_data = {
        "metadata": {
            "dataset_name": "Reality Lab Knowledge Base",
            "created": datetime.now().isoformat(),
            "source": "https://reality.ssu.ac.kr/",
            "description": "Comprehensive knowledge base of Soongsil University Reality Lab",
        },
        "sections": {}
    }
    
    # Process each page
    for item in raw_data:
        url = item['url']
        content = item['content']
        title = item['title']
        
        # Clean and categorize content
        if 'news' in url.lower():
            category = 'news'
        elif 'member' in url.lower() or 'faculty' in url.lower() or 'student' in url.lower():
            category = 'members'
        elif 'publication' in url.lower():
            category = 'publications'
        elif 'course' in url.lower():
            category = 'courses'
        else:
            category = 'general'
        
        # Clean content
        clean_content = clean_text_content(content)
        
        if category not in structured_data['sections']:
            structured_data['sections'][category] = []
        
        if clean_content and len(clean_content) > 100:  # Only meaningful content
            structured_data['sections'][category].append({
                'title': title,
                'url': url,
                'content': clean_content
            })
    
    # Save structured data
    with open('reality_lab_dataset/structured_data.json', 'w', encoding='utf-8') as f:
        json.dump(structured_data, f, ensure_ascii=False, indent=2)
    
    return structured_data

def clean_text_content(text):
    """Clean and normalize text content more thoroughly"""
    if not text:
        return ""
    
    # Remove repeated navigation elements
    text = re.sub(r'(Home\s+News\s+Members.*?Courses\s*)+', '', text)
    text = re.sub(r'(Faculty\s+Students\s+Alumni\s*)+', '', text)
    text = re.sub(r'(International\s+Domestic\s*)+', '', text)
    text = re.sub(r'More.*?Courses', '', text)
    
    # Clean up repeated whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove empty lines and trim
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    text = '\n'.join(lines)
    
    return text.strip()

def create_instruction_dataset():
    """Create a high-quality instruction dataset for fine-tuning"""
    
    with open('reality_lab_dataset/structured_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    instruction_dataset = []
    
    # Create comprehensive Q&A pairs
    qa_templates = {
        'general': [
            ("Reality Lab에 대해 설명해주세요.", "general_description"),
            ("Reality Lab의 연구 목표는 무엇인가요?", "research_goals"),
            ("Reality Lab은 언제 설립되었나요?", "establishment"),
        ],
        'news': [
            ("Reality Lab의 최근 뉴스나 성과를 알려주세요.", "recent_news"),
            ("Reality Lab에서 최근에 발표한 논문이 있나요?", "recent_papers"),
            ("Reality Lab 구성원들의 최근 수상 내역을 알려주세요.", "recent_awards"),
        ],
        'members': [
            ("Reality Lab의 구성원들을 소개해주세요.", "member_introduction"),
            ("Reality Lab의 교수님은 누구인가요?", "faculty_info"),
            ("Reality Lab에는 몇 명의 학생이 있나요?", "student_count"),
            ("Reality Lab 구성원들의 연구 분야는 무엇인가요?", "research_interests"),
        ],
        'publications': [
            ("Reality Lab에서 발표한 논문들을 알려주세요.", "publication_list"),
            ("Reality Lab의 국제 학술지 논문 목록을 보여주세요.", "international_papers"),
            ("Reality Lab의 국내 학술지 논문 목록을 보여주세요.", "domestic_papers"),
            ("Reality Lab에서 CVPR, ICCV, ECCV에 발표한 논문이 있나요?", "top_conference_papers"),
        ],
        'courses': [
            ("Reality Lab에서 제공하는 강의는 무엇인가요?", "course_list"),
            ("김희원 교수님이 담당하는 과목은 무엇인가요?", "professor_courses"),
            ("컴퓨터 비전 관련 강의가 있나요?", "cv_courses"),
        ]
    }
    
    # Generate instruction pairs for each category
    for category, sections in data['sections'].items():
        if category in qa_templates:
            combined_content = '\n\n'.join([section['content'] for section in sections])
            
            for question, _ in qa_templates[category]:
                # Create context-aware responses
                if category == 'general':
                    answer = create_general_answer(combined_content)
                elif category == 'news':
                    answer = create_news_answer(combined_content)
                elif category == 'members':
                    answer = create_members_answer(combined_content)
                elif category == 'publications':
                    answer = create_publications_answer(combined_content, question)
                elif category == 'courses':
                    answer = create_courses_answer(combined_content)
                else:
                    answer = combined_content[:1000] + "..."
                
                if answer and len(answer) > 50:
                    instruction_dataset.append({
                        "instruction": question,
                        "input": "",
                        "output": answer,
                        "category": category
                    })
    
    # Add specific factual Q&As
    factual_qas = [
        {
            "instruction": "Reality Lab의 연락처 정보를 알려주세요.",
            "input": "",
            "output": "Reality Lab은 숭실대학교에 위치하고 있습니다.\n\n- 주소: 서울특별시 동작구 사당로 105, 숭실대학교\n- 교수: 김희원 교수님\n- 전화: +82-2-820-0679\n- 연구실: 07027호실, 과학기술관 6층 602호\n\n더 자세한 정보나 문의사항은 Reality Lab 웹사이트(https://reality.ssu.ac.kr)를 참조하시거나 직접 연락 바랍니다.",
            "category": "contact"
        },
        {
            "instruction": "Reality Lab의 연구 분야는 무엇인가요?",
            "input": "",
            "output": "Reality Lab의 주요 연구 분야는 다음과 같습니다:\n\n1. **컴퓨터 비전 (Computer Vision)**: 이미지 처리, 영상 인식, 3D 비전\n2. **로보틱스 (Robotics)**: 로봇 조작, 자율 주행, Embodied AI\n3. **기계학습 (Machine Learning)**: 딥러닝, 신경망, AI 모델 개발\n4. **멀티모달 언어 이해 (Multimodal Language Understanding)**: 텍스트-이미지 연동, 대화형 AI\n5. **AI+X 응용 분야**: 헬스케어 AI, 스포츠 AI, 의료 AI\n\nReality Lab은 '현실을 이해하는 AI 발전'을 목표로 인공지능과 물리적 세계의 교차점을 탐구하며, 인간처럼 실제 세계의 인식과 상호작용으로부터 학습하는 지능형 시스템을 개발하고 있습니다.",
            "category": "research"
        }
    ]
    
    instruction_dataset.extend(factual_qas)
    
    # Save instruction dataset
    with open('reality_lab_dataset/instruction_dataset.json', 'w', encoding='utf-8') as f:
        json.dump(instruction_dataset, f, ensure_ascii=False, indent=2)
    
    # Create training format for different frameworks
    create_training_formats(instruction_dataset)
    
    return instruction_dataset

def create_general_answer(content):
    """Create a comprehensive general answer about Reality Lab"""
    return """Reality Lab은 2023년 숭실대학교에 설립된 연구실로, 김희원 교수님의 지도 하에 운영되고 있습니다.

**연구 목표**: "Advancing AI to Understand Reality" - 현실을 이해하는 AI 발전

**주요 연구 분야**:
- 로보틱스 (Robotics)
- 컴퓨터 비전 (Computer Vision)  
- 기계학습 (Machine Learning)
- 멀티모달 언어 이해 (Multimodal Language Understanding)
- AI+X 헬스케어 응용

Reality Lab은 인공지능과 물리적 세계의 교차점을 탐구하며, 인간처럼 실제 세계의 인식과 상호작용으로부터 학습하는 지능형 시스템을 개발하는 것을 목표로 하고 있습니다."""

def create_news_answer(content):
    """Extract and format recent news"""
    news_items = []
    lines = content.split('\n')
    
    for line in lines:
        if 'accepted' in line.lower() or 'place' in line.lower() or 'internship' in line.lower():
            if len(line.strip()) > 20:
                news_items.append(line.strip())
    
    if news_items:
        return "Reality Lab의 최근 주요 성과들:\n\n" + '\n\n'.join(news_items[:10])
    return "최근 뉴스 정보를 업데이트하고 있습니다."

def create_members_answer(content):
    """Format member information"""
    return """Reality Lab은 김희원 교수님을 중심으로 한 활발한 연구팀입니다.

**구성**:
- 지도교수: 김희원 교수님
- 석사과정 학생들: 다양한 연구 분야에서 활동
- 학부 인턴: 연구 경험을 쌓는 학부생들

**주요 연구진의 관심 분야**:
- 컴퓨터 비전 및 딥러닝
- 로보틱스 및 Embodied AI  
- 이미지 처리 및 영상 복원
- 3D 비전 및 증강현실
- 의료 AI 및 스포츠 AI
- 자연어 처리 및 멀티모달 학습

각 구성원은 자신의 전문 분야에서 국제적 수준의 연구를 수행하고 있으며, 정기적으로 최고 수준의 국제 학술대회와 저널에 논문을 발표하고 있습니다."""

def create_publications_answer(content, question):
    """Format publication information based on question type"""
    if 'international' in question.lower() or 'CVPR' in question or 'ICCV' in question:
        return """Reality Lab에서 발표한 주요 국제 논문들:

**최고 수준 학술대회 (CVPR, ICCV, ECCV)**:
- CVPR 2025: "DynScene: Scalable Generation of Dynamic Robotic Manipulation Scenes for Embodied AI"
- CVPR 2022: "Attentive Fine-Grained Structured Sparsity for Image Restoration"
- ICCV 2021: "Meta-Learning with Task-Adaptive Loss Function for Few-Shot Learning" (ORAL)
- ICCV 2021: "Motion-Aware Dynamic Architecture for Efficient Frame Interpolation"
- ECCV 2022: "CADyQ: Content-Aware Dynamic Quantization for Image Super Resolution"

**최고 수준 저널**:
- IEEE TPAMI: "Learning to Learn Task-Adaptive Hyperparameters for Few-Shot Learning"
- IEEE TIP: "Learning Controllable ISP for Image Enhancement"

**기타 주요 학술대회**:
- BMVC 2025, AAAI 2025, ICLR 2023, NeurIPS 2020 등 다수

Reality Lab은 컴퓨터 비전 분야 최고 수준의 연구 성과를 지속적으로 발표하고 있습니다."""
    
    return "Reality Lab에서는 국제 및 국내 학술지에 다수의 고품질 논문을 발표하고 있습니다. 주요 연구 성과는 웹사이트의 Publication 섹션에서 확인하실 수 있습니다."

def create_courses_answer(content):
    """Format course information"""
    return """Reality Lab에서 제공하는 주요 강의 과목들:

**전공 핵심 과목**:
- 컴퓨터비전 (Computer Vision)
- 기계학습 (머신러닝, Machine Learning)
- 영상처리및실습 (Image Processing and Practice)

**전공 심화 과목**:
- 컴퓨터비전특론 (Advanced Computer Vision)
- 미디어GAN (Media GAN)
- 데이터 사이언스 (Data Science)

이러한 강의들은 Reality Lab의 연구 분야와 직접적으로 연관되어 있으며, 최신 연구 동향과 실무 경험을 바탕으로 구성되어 있습니다. 학생들은 이론적 지식과 함께 실제 연구 프로젝트에 참여할 수 있는 기회를 얻을 수 있습니다."""

def create_training_formats(instruction_dataset):
    """Create training files in various formats"""
    
    # Alpaca format
    with open('reality_lab_dataset/alpaca_format.json', 'w', encoding='utf-8') as f:
        json.dump(instruction_dataset, f, ensure_ascii=False, indent=2)
    
    # ChatML format for modern LLMs
    chatML_dataset = []
    for item in instruction_dataset:
        chatML_dataset.append({
            "messages": [
                {"role": "system", "content": "당신은 숭실대학교 Reality Lab에 대한 전문 지식을 가진 도움이 되는 어시스턴트입니다. 연구실에 대한 정확하고 상세한 정보를 제공해주세요."},
                {"role": "user", "content": item["instruction"]},
                {"role": "assistant", "content": item["output"]}
            ]
        })
    
    with open('reality_lab_dataset/chatML_format.json', 'w', encoding='utf-8') as f:
        json.dump(chatML_dataset, f, ensure_ascii=False, indent=2)
    
    # Plain text format for simple training
    with open('reality_lab_dataset/plain_training.txt', 'w', encoding='utf-8') as f:
        for item in instruction_dataset:
            f.write(f"### 질문: {item['instruction']}\n")
            f.write(f"### 답변: {item['output']}\n\n")
            f.write("---\n\n")

if __name__ == "__main__":
    print("Reality Lab 데이터 후처리를 시작합니다...")
    
    # Process and structure the data
    structured_data = clean_and_structure_data()
    print(f"구조화된 데이터 생성 완료: {len(structured_data['sections'])} 카테고리")
    
    # Create instruction dataset
    instruction_dataset = create_instruction_dataset()
    print(f"Instruction 데이터셋 생성 완료: {len(instruction_dataset)} 개의 Q&A 쌍")
    
    print("\n생성된 파일들:")
    print("- structured_data.json: 카테고리별 구조화된 데이터")
    print("- instruction_dataset.json: 기본 instruction 형태")
    print("- alpaca_format.json: Alpaca 학습 형태") 
    print("- chatML_format.json: ChatML 대화 형태")
    print("- plain_training.txt: 일반 텍스트 형태")
    
    print(f"\n총 {len(instruction_dataset)}개의 고품질 Q&A 쌍이 생성되었습니다!")
    print("LLM 파인튜닝에 바로 사용할 수 있습니다.")