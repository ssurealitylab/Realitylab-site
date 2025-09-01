#!/usr/bin/env python3
"""
Reality Lab Qwen2.5-3B Server - Simplified Version
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
    """Load Qwen2.5-3B model on GPU 0"""
    global model, tokenizer
    
    try:
        model_name = "Qwen/Qwen2.5-3B-Instruct"
        
        logger.info("Loading tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Set padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("Loading model on GPU 0")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="cuda:0",
            low_cpu_mem_usage=True
        )
        
        logger.info("✅ Model loaded successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        return False

def generate_response(prompt, max_length=400):
    """Generate AI response"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        return "AI model not loaded"
    
    try:
        # Create chat template
        messages = [
            {
                "role": "system", 
                "content": """당신은 숭실대학교 Reality Lab의 전문 어시스턴트입니다. 아래 정보를 바탕으로 정확하고 상세한 답변을 제공해주세요.

**Reality Lab 핵심 정보:**
- 설립: 2023년 숭실대학교, 김희원 교수님 지도
- 연구목표: "Advancing AI to Understand Reality" - 현실을 이해하는 AI 발전
- 주요 연구분야: 로보틱스, 컴퓨터비전, 기계학습, 멀티모달 언어이해, AI+X 헬스케어
- 위치: 서울특별시 동작구 사당로 105, 숭실대학교
- 연락처: +82-2-820-0679

**주요 구성원:** 김희원 교수님을 중심으로 박성용, 채병관, 최영재, 이상민, 고민주, 고현준, 고현서, 이주형, 서지우, 정호재, 김서영, 김예리, 최수영, 황지원, 송은우, 이세빈, 김도원, 김연지, 이재현, 이예빈, 임정하 등 다양한 연구진

**최근 성과:** CVPR 2025, BMVC 2025, AAAI 2025, PLOS One, ICT Express 등 최고 수준 학술대회 및 저널 논문 발표, ARNOLD Challenge 1위 수상, Qualcomm 인턴십 등

**제공 강의:** 컴퓨터비전, 기계학습, 영상처리및실습, 컴퓨터비전특론, 미디어GAN, 데이터사이언스

질문에 관련된 정확한 정보를 제공하세요."""
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
        
        if generated_text:
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
        'model_name': 'Qwen2.5-3B-Instruct'
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
        ai_response = generate_response(user_question, max_length=400)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'model': 'Qwen2.5-3B-Instruct',
            'response_time': response_time
        })
        
    except Exception as e:
        import traceback
        logger.error(f"Error in chat endpoint: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("Starting Reality Lab Qwen2.5-3B Server...")
    
    if load_model():
        logger.info("🚀 Qwen2.5-3B server ready!")
        app.run(host='0.0.0.0', port=4003, debug=False, threaded=True)
    else:
        logger.error("❌ Failed to load model. Server not started.")