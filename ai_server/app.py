#!/usr/bin/env python3
"""
Reality Lab AI Server using Tiny Llama
Local GPU-accelerated inference server
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global variables for model and tokenizer
model = None
tokenizer = None
device = None

def load_model():
    """Load Tiny Llama model and tokenizer"""
    global model, tokenizer, device
    
    try:
        # Check if CUDA is available
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU")
        
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        logger.info(f"Loading model: {model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # Load model with GPU support
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            trust_remote_code=True
        )
        
        # Move model to device
        model = model.to(device)
        
        # Set padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("Model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def generate_response(prompt, max_length=150, temperature=0.7):
    """Generate AI response using Tiny Llama"""
    global model, tokenizer, device
    
    if model is None or tokenizer is None:
        return "AI model is not loaded"
    
    try:
        # Tokenize input
        inputs = tokenizer.encode(prompt, return_tensors="pt").to(device)
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                inputs,
                max_length=inputs.shape[1] + max_length,
                temperature=temperature,
                do_sample=True,
                top_p=0.9,
                pad_token_id=tokenizer.eos_token_id,
                num_return_sequences=1
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part (remove input prompt)
        generated_text = response[len(tokenizer.decode(inputs[0], skip_special_tokens=True)):].strip()
        
        return generated_text if generated_text else "죄송합니다. 응답을 생성할 수 없습니다."
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "응답 생성 중 오류가 발생했습니다."

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'device': str(device) if device else 'unknown'
    })

@app.route('/generate', methods=['POST'])
def generate():
    """Generate AI response endpoint"""
    try:
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'error': 'No prompt provided'}), 400
        
        user_question = data['prompt']
        language = data.get('language', 'ko')  # Default to Korean
        
        # Create context-aware prompt for Reality Lab
        if language == 'en':
            system_prompt = """You are a helpful assistant for the Reality Lab at Soongsil University. Answer questions about the lab's research areas, team members, and activities. Keep responses concise and informative.

Question: """
            prompt = system_prompt + user_question + "\nAnswer:"
        else:
            system_prompt = """당신은 숭실대학교 리얼리티 연구실의 도움이 되는 어시스턴트입니다. 연구실의 연구 분야, 팀 구성원, 활동에 대한 질문에 답변해주세요. 간결하고 유익한 답변을 해주세요.

질문: """
            prompt = system_prompt + user_question + "\n답변:"
        
        # Generate response
        response = generate_response(prompt, max_length=100, temperature=0.7)
        
        # Clean up response (remove system prompt remnants)
        if language == 'en':
            if "Answer:" in response:
                response = response.split("Answer:")[-1].strip()
        else:
            if "답변:" in response:
                response = response.split("답변:")[-1].strip()
        
        return jsonify({
            'response': response,
            'language': language
        })
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Reality Lab AI Server...")
    
    # Load model on startup
    if load_model():
        logger.info("AI Server ready!")
        # Enable HTTPS with self-signed certificate for development
        app.run(host='127.0.0.1', port=5000, debug=False, ssl_context='adhoc')
    else:
        logger.error("Failed to load model. Server not started.")