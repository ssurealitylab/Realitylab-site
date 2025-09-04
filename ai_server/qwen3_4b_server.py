#!/usr/bin/env python3
"""
Reality Lab Qwen3-4B Server
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables
model = None
tokenizer = None

def load_model():
    """Load Qwen3-4B model"""
    global model, tokenizer
    
    try:
        # Use the downloaded model path
        model_path = "/home/i0179/.cache/huggingface/hub/qwen3-4b-git"
        
        logger.info("Loading tokenizer from local path")
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        
        # Set padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("Loading Qwen3-4B model on GPU 2")
        model = AutoModelForCausalLM.from_pretrained(
            model_path,
            torch_dtype=torch.float16,
            device_map="cuda:0",  # CUDA_VISIBLE_DEVICES=2 makes GPU 2 appear as cuda:0
            low_cpu_mem_usage=True
        )
        
        logger.info("✅ Qwen3-4B model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False

def ensure_sentence_completion(text, language='ko'):
    """Ensure the response ends with complete sentences"""
    import re
    
    # Korean sentence endings
    korean_endings = ['다', '요', '니다', '습니다', '어요', '아요', '게요', '죠', '네요', '세요']
    # English sentence endings
    english_endings = ['.', '!', '?']
    
    if language == 'ko':
        # Check if text ends with Korean sentence ending
        for ending in korean_endings:
            if text.endswith(ending):
                return text
        
        # Find the last complete Korean sentence
        sentences = re.split(r'[.!?]|(?<=[다요니습어아게죠네세])\s', text)
        if len(sentences) > 1 and sentences[-2].strip():
            # Return text up to the last complete sentence
            last_complete = sentences[-2].strip()
            # Find position of last complete sentence
            pos = text.rfind(last_complete)
            if pos != -1:
                end_pos = pos + len(last_complete)
                return text[:end_pos].strip()
    else:
        # English text
        for ending in english_endings:
            if text.endswith(ending):
                return text
        
        # Find last complete English sentence
        sentences = re.split(r'[.!?]\s+', text)
        if len(sentences) > 1 and sentences[-2].strip():
            # Return up to last complete sentence
            return '.'.join(sentences[:-1]) + '.'
    
    return text

def generate_response(prompt, language='ko', max_length=800):
    """Generate AI response"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        return "AI model not loaded"
    
    try:
        # Create language-specific system prompt
        if language == 'en':
            system_content = """You are a professional English assistant for Soongsil University Reality Lab. Please provide accurate and detailed answers in English only.

**Reality Lab Core Information:**
- Established: 2023 at Soongsil University, led by Professor Heewon Kim
- Research Goal: Advancing AI technologies that understand and interact with the real world
- Major Research Areas: Robotics, Computer Vision, Machine Learning, Multimodal Language Understanding, AI+X Healthcare
- Location: 105 Sadan-ro, Dongjak-gu, Seoul, Soongsil University
- Contact: +82-2-820-0679

**Key Members:** Led by Professor Heewon Kim with diverse researchers including Sungyong Park, Byungkwan Chae, Youngjae Choi, Sangmin Lee, Minju Ko, Hyunjun Ko, Hyunsuh Ko, Juhyeong Lee, Jiwoo Seo, Hojae Jeong, Seoyoung Kim, Yeri Kim, Suyoung Choi, Jiwon Hwang, Eunwoo Song, Sebin Lee, Dowon Kim, Yeonji Kim, Jaehyun Lee, Yebin Lee, Jungha Lim, and others

**Recent Achievements:** Publications in top-tier conferences and journals including CVPR 2025, BMVC 2025, AAAI 2025, PLOS One, ICT Express, ARNOLD Challenge 1st place winner, Qualcomm internships, etc.

**Courses Offered:** Computer Vision, Machine Learning, Image Processing Lab, Advanced Computer Vision, Media GAN, Data Science

**Important:** Always think and respond in English only. Never use Korean."""
        else:
            system_content = """당신은 숭실대학교 Reality Lab의 전문 한국어 어시스턴트입니다. 항상 한국어로만 생각하고 한국어로만 답변해주세요.

**Reality Lab 핵심 정보:**
- 설립: 2023년 숭실대학교, 김희원 교수님 지도
- 연구목표: 현실을 이해하는 AI 기술 발전
- 주요 연구분야: 로보틱스, 컴퓨터비전, 기계학습, 멀티모달 언어이해, AI+X 헬스케어
- 위치: 서울특별시 동작구 사당로 105, 숭실대학교
- 연락처: +82-2-820-0679

**주요 구성원:** 김희원 교수님을 중심으로 박성용, 채병관, 최영재, 이상민, 고민주, 고현준, 고현서, 이주형, 서지우, 정호재, 김서영, 김예리, 최수영, 황지원, 송은우, 이세빈, 김도원, 김연지, 이재현, 이예빈, 임정하 등 다양한 연구진

**최근 성과:** CVPR 2025, BMVC 2025, AAAI 2025, PLOS One, ICT Express 등 최고 수준 학술대회 및 저널 논문 발표, ARNOLD Challenge 1위 수상, Qualcomm 인턴십 등

**제공 강의:** 컴퓨터비전, 기계학습, 영상처리및실습, 컴퓨터비전특론, 미디어GAN, 데이터사이언스

**중요:** 한국어 질문에는 반드시 한국어로만 생각하고 한국어로만 답변하세요. 절대 영어를 사용하지 마세요."""

        # Create chat template
        messages = [
            {
                "role": "system", 
                "content": system_content
            },
            {"role": "user", "content": prompt}
        ]
        
        # Apply chat template
        formatted_prompt = tokenizer.apply_chat_template(
            messages, 
            tokenize=False, 
            add_generation_prompt=True
        )
        
        # Tokenize input
        inputs = tokenizer(
            formatted_prompt, 
            return_tensors="pt", 
            truncation=True, 
            max_length=512
        ).to("cuda:0")
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                max_new_tokens=max_length,
                temperature=0.7,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                attention_mask=inputs.attention_mask
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract generated text
        if "assistant\n" in response:
            parts = response.split("assistant\n")
            if len(parts) > 1:
                generated_text = parts[-1].replace("<|im_end|>", "").strip()
            else:
                generated_text = response[len(formatted_prompt):].strip()
        else:
            generated_text = response[len(formatted_prompt):].strip()
        
        # Remove thinking tags and content
        import re
        generated_text = re.sub(r'<think>.*?</think>', '', generated_text, flags=re.DOTALL).strip()
        
        # Ensure natural sentence completion
        if generated_text:
            generated_text = ensure_sentence_completion(generated_text, language)
            return generated_text
        else:
            return "죄송합니다. 응답을 생성할 수 없습니다."
            
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "응답 생성 중 오류가 발생했습니다."

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'model_name': 'Qwen3-4B'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint"""
    try:
        start_time = time.time()
        
        print(f"Request content type: {request.content_type}")
        print(f"Request is_json: {request.is_json}")
        
        data = request.get_json(force=True)
        print(f"Parsed JSON: {data}")
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        if 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        user_question = data['question']
        language = data.get('language', 'ko')
        
        # Generate AI response
        ai_response = generate_response(user_question, language=language, max_length=800)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'model': 'Qwen3-4B',
            'response_time': response_time
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Error in chat endpoint: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("Starting Reality Lab Qwen3-4B Server...")
    
    if load_model():
        logger.info("🚀 Qwen3-4B server ready on port 4004!")
        app.run(host='0.0.0.0', port=4004, debug=False, threaded=True)
    else:
        logger.error("❌ Failed to load model. Server not started.")