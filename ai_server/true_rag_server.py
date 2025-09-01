#!/usr/bin/env python3
"""
True RAG Server for Reality Lab
Real retrieval-augmented generation that produces varied responses
"""

import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
import random

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

model = None
tokenizer = None

# Reality Lab Knowledge Base - Raw facts for retrieval
REALITY_LAB_KNOWLEDGE = {
    "basic_info": {
        "name": "Reality Lab",
        "establishment": "2023년 숭실대학교에서 설립",
        "director": "김희원 교수님이 지도",
        "mission": "Advancing AI to Understand Reality - 현실을 이해하는 AI 발전",
        "contact": "+82-2-820-0679",
        "address": "서울특별시 동작구 사당로 105, 숭실대학교"
    },
    "research_areas": [
        "로보틱스 (Robotics) - 로봇 기술 연구",
        "컴퓨터비전 (Computer Vision) - 영상 인식 및 처리",
        "기계학습 (Machine Learning) - 머신러닝 알고리즘 연구", 
        "멀티모달 언어이해 (Multimodal Language Understanding) - 다중 모달 AI",
        "AI+X 헬스케어 - 의료 분야 AI 응용"
    ],
    "members": [
        "김희원 교수님 (지도교수)",
        "박성용", "채병관", "최영재", "이상민", "고민주",
        "고현준", "고현서", "이주형", "서지우", "정호재", 
        "김서영", "김예리", "최수영", "황지원", "송은우",
        "이세빈", "김도원", "김연지", "이재현", "이예빈", "임정하"
    ],
    "achievements": [
        "CVPR 2025 논문 발표",
        "BMVC 2025 논문 발표",
        "AAAI 2025 논문 발표", 
        "PLOS One 저널 논문 게재",
        "ICT Express 저널 논문 게재",
        "ARNOLD Challenge 1위 수상",
        "Qualcomm 인턴십 프로그램 참여"
    ],
    "courses": [
        "컴퓨터비전 - 영상 처리 기초",
        "기계학습 - 머신러닝 이론과 실습",
        "영상처리및실습 - 디지털 영상 처리",
        "컴퓨터비전특론 - 고급 컴퓨터 비전",
        "미디어GAN - 생성형 AI",
        "데이터사이언스 - 데이터 분석 및 활용"
    ]
}

def retrieve_relevant_knowledge(question):
    """Retrieve relevant knowledge pieces based on question"""
    question_lower = question.lower()
    retrieved_facts = []
    
    # Basic info retrieval
    if any(word in question_lower for word in ['연락', 'contact', '전화', '번호']):
        retrieved_facts.append(f"연락처: {REALITY_LAB_KNOWLEDGE['basic_info']['contact']}")
        retrieved_facts.append(f"주소: {REALITY_LAB_KNOWLEDGE['basic_info']['address']}")
    
    if any(word in question_lower for word in ['설립', '언제', 'established', '교수']):
        retrieved_facts.append(f"설립: {REALITY_LAB_KNOWLEDGE['basic_info']['establishment']}")
        retrieved_facts.append(f"지도교수: {REALITY_LAB_KNOWLEDGE['basic_info']['director']}")
    
    if any(word in question_lower for word in ['연구', '분야', 'research']):
        retrieved_facts.extend(REALITY_LAB_KNOWLEDGE['research_areas'])
        retrieved_facts.append(f"연구 목표: {REALITY_LAB_KNOWLEDGE['basic_info']['mission']}")
    
    if any(word in question_lower for word in ['구성원', '멤버', 'member', '팀', 'team']):
        retrieved_facts.extend(REALITY_LAB_KNOWLEDGE['members'])
    
    if any(word in question_lower for word in ['성과', 'achievement', '논문', 'paper']):
        retrieved_facts.extend(REALITY_LAB_KNOWLEDGE['achievements'])
    
    if any(word in question_lower for word in ['강의', 'course', '수업']):
        retrieved_facts.extend(REALITY_LAB_KNOWLEDGE['courses'])
    
    # Default retrieval if no specific match
    if not retrieved_facts:
        retrieved_facts.extend([
            REALITY_LAB_KNOWLEDGE['basic_info']['establishment'],
            REALITY_LAB_KNOWLEDGE['basic_info']['director'],
            REALITY_LAB_KNOWLEDGE['basic_info']['mission']
        ])
    
    return retrieved_facts

def load_model():
    """Load Qwen2.5-3B model"""
    global model, tokenizer
    
    try:
        model_name = "Qwen/Qwen2.5-3B-Instruct"
        
        logger.info("Loading tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("Loading model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        logger.info("✅ Model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading model: {e}")
        return False

def generate_rag_response(question):
    """True RAG: Retrieve knowledge and generate varied responses"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        return "모델이 로드되지 않았습니다."
    
    try:
        # Step 1: Check if question is Reality Lab related
        question_lower = question.lower()
        reality_lab_keywords = ['연구', 'research', '분야', '구성원', '멤버', 'member', '팀', 'team', 
                               '연락', 'contact', '전화', '번호', '주소', 'address', '위치', 'location',
                               '설립', 'established', '교수', 'professor', '성과', 'achievement', 
                               '논문', 'paper', '강의', 'course', '수업', 'class', 'reality lab',
                               '리얼리티랩', '숭실', '숭실대', 'ssu']
        
        is_relevant = any(keyword in question_lower for keyword in reality_lab_keywords)
        
        if not is_relevant:
            return "죄송합니다. Reality Lab 챗봇은 연구실 관련 질문에만 답변할 수 있습니다. Reality Lab의 연구 분야, 구성원, 연락처, 성과 등에 대해 궁금한 점이 있으시면 언제든 물어보세요!"
        
        # Step 2: Retrieve relevant knowledge
        retrieved_facts = retrieve_relevant_knowledge(question)
        
        # Step 3: Create context from retrieved facts
        context = "\n".join(retrieved_facts)
        
        # Step 3: Generate varied prompt with strict Korean language instruction
        system_instruction = "당신은 Reality Lab 전문 한국어 어시스턴트입니다. 반드시 표준 한국어로만 답변하세요. 외국어나 특수문자를 사용하지 마세요."
        
        prompt_variations = [
            f"{system_instruction}\n\n질문: {question}\n\n참고 자료:\n{context}\n\n위 자료를 바탕으로 정확한 한국어로 자연스럽게 답변해주세요:",
            f"{system_instruction}\n\n사용자 질문: {question}\n\n관련 정보:\n{context}\n\n이 정보들을 활용해서 깔끔한 한국어로 친근하게 답변해주세요:",
            f"{system_instruction}\n\n질문 내용: {question}\n\n참고할 수 있는 정보:\n{context}\n\n위 정보를 바탕으로 표준 한국어로 도움이 되는 답변을 작성해주세요:"
        ]
        
        prompt = random.choice(prompt_variations)
        
        # Step 4: Tokenize with random length variation
        max_length = random.randint(512, 800)
        inputs = tokenizer(prompt, return_tensors="pt", truncation=True, max_length=max_length)
        inputs = {k: v.to(model.device) for k, v in inputs.items()}
        
        # Step 5: Generate with varied parameters for different responses
        temperature = random.uniform(0.4, 0.7)
        top_p = random.uniform(0.8, 0.95)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=random.randint(100, 250),
                temperature=temperature,
                do_sample=True,
                top_p=top_p,
                repetition_penalty=random.uniform(1.1, 1.3),
                no_repeat_ngram_size=3,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id
            )
        
        # Step 6: Decode response
        full_response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract generated part
        generated_text = full_response[len(prompt):].strip()
        
        return generated_text if generated_text else "죄송합니다. 답변을 생성할 수 없습니다."
            
    except Exception as e:
        logger.error(f"Error generating RAG response: {e}")
        return "응답 생성 중 오류가 발생했습니다."

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'model_name': 'Qwen2.5-3B True RAG',
        'method': 'True Retrieval-Augmented Generation'
    })

@app.route('/chat', methods=['POST'])
def chat():
    try:
        start_time = time.time()
        
        data = request.get_json(force=True)
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        user_question = data['question']
        language = data.get('language', 'ko')
        
        # Generate RAG response
        ai_response = generate_rag_response(user_question)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'model': 'Qwen2.5-3B True RAG',
            'method': 'Retrieval-Augmented Generation',
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/generate', methods=['POST'])
def generate():
    try:
        start_time = time.time()
        
        data = request.get_json(force=True)
        if not data or 'prompt' not in data:
            return jsonify({'error': 'No prompt provided'}), 400
        
        user_prompt = data['prompt']
        language = data.get('language', 'ko')
        
        response = generate_rag_response(user_prompt)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': response,
            'language': language,
            'model': 'Qwen2.5-3B True RAG',
            'method': 'True RAG',
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting True RAG Server...")
    
    if load_model():
        logger.info("✅ True RAG server ready on port 4003!")
        app.run(host='0.0.0.0', port=4003, debug=False, threaded=True)
    else:
        logger.error("❌ Failed to load model. Server not started.")