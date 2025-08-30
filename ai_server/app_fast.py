#!/usr/bin/env python3
"""
Reality Lab KULLM3-AWQ Server - Fast Single GPU Version
Optimized for minimal latency and quick responses
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
CORS(app)  # Enable CORS for frontend access

# Global variables
model = None
tokenizer = None
device = None

def load_model():
    """Load KULLM3 model optimized for speed"""
    global model, tokenizer, device
    
    try:
        # Use the best available GPU
        if torch.cuda.is_available():
            device = torch.device("cuda:0")  # Use only GPU 0
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU")
        
        model_name = "/home/i0179/models/KULLM3-awq"
        logger.info("Loading KULLM3 model (standard loading for speed)...")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load model without AWQ for faster loading
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map="cuda:0",
            low_cpu_mem_usage=True,
            trust_remote_code=True
        )
        
        logger.info("✅ KULLM3 model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def generate_response_fast(prompt, max_length=50):
    """Generate AI response optimized for speed"""
    global model, tokenizer, device
    
    if model is None or tokenizer is None:
        return "AI model is not loaded"
    
    try:
        # Tokenize with very short limits for speed
        inputs = tokenizer(
            prompt, 
            return_tensors="pt", 
            padding=True, 
            truncation=True, 
            max_length=200  # Shorter input
        ).to(device)
        
        # Generate with speed-optimized settings
        with torch.no_grad():
            outputs = model.generate(
                inputs.input_ids,
                attention_mask=inputs.attention_mask,
                max_new_tokens=max_length,  # Very short output
                do_sample=False,  # Greedy is fastest
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                use_cache=True,
                early_stopping=True,
                # Additional speed optimizations
                num_beams=1,
                temperature=1.0
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract generated part
        input_text = tokenizer.decode(inputs.input_ids[0], skip_special_tokens=True)
        generated_text = response[len(input_text):].strip()
        
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
        'device': str(device),
        'version': 'fast'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Fast chat endpoint"""
    try:
        start_time = time.time()
        
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        user_question = data['question']
        language = data.get('language', 'ko')
        
        # Generate AI response with very short prompt
        system_prompt = "답변: " if language == 'ko' else "Answer: "
        prompt = user_question + "\n" + system_prompt
        
        ai_response = generate_response_fast(prompt, max_length=30)  # Extremely short
        
        # Clean up response
        if system_prompt in ai_response:
            ai_response = ai_response.split(system_prompt)[-1].strip()
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'model': 'KULLM3-fast',
            'response_time': response_time,
            'version': 'fast'
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Fast Reality Lab KULLM3 Server...")
    
    # Load model
    if load_model():
        logger.info("🚀 Fast KULLM3 server ready!")
        app.run(host='0.0.0.0', port=4003, debug=False, threaded=True)
    else:
        logger.error("❌ Failed to load model. Server not started.")