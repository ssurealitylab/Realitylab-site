#!/usr/bin/env python3
"""
Simple Gemma2 Server for Reality Lab
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

model = None
tokenizer = None

def load_model():
    """Load Gemma2-9B model"""
    global model, tokenizer
    
    try:
        model_name = "google/gemma-2-9b-it"
        
        logger.info("Loading Gemma2 tokenizer...")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("Loading Gemma2 model...")
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="auto"
        )
        
        logger.info("✅ Gemma2 loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error loading Gemma2: {e}")
        return False

def generate_response(question):
    """Generate response using Gemma2"""
    global model, tokenizer
    
    if model is None or tokenizer is None:
        return "Gemma2 model is not loaded"
    
    try:
        # Simple prompt
        prompt = f"질문: {question}\n답변:"
        
        inputs = tokenizer(prompt, return_tensors="pt").to(model.device)
        
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=200,
                temperature=0.7,
                do_sample=True,
                top_p=0.9,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        answer = response[len(prompt):].strip()
        
        return answer if answer else "죄송합니다. 답변을 생성할 수 없습니다."
            
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "응답 생성 중 오류가 발생했습니다."

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'model_name': 'Gemma2-9B-IT'
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
        
        ai_response = generate_response(user_question)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'model': 'Gemma2-9B-IT',
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

if __name__ == '__main__':
    logger.info("🚀 Starting Gemma2 Simple Server...")
    
    if load_model():
        logger.info("✅ Gemma2 server ready on port 4001!")
        app.run(host='0.0.0.0', port=4001, debug=False, threaded=True)
    else:
        logger.error("❌ Failed to load Gemma2. Server not started.")