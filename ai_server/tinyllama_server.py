#!/usr/bin/env python3
"""
Reality Lab TinyLlama Server
Lightweight AI inference server for TinyLlama model
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

# Global variables for model and tokenizer
model = None
tokenizer = None
device = None

def load_model():
    """Load TinyLlama model and tokenizer"""
    global model, tokenizer, device
    
    try:
        # Check if CUDA is available
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU")
        
        # Use TinyLlama model
        model_name = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        logger.info(f"Loading model: {model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            device_map="auto" if device.type == "cuda" else "cpu",
            low_cpu_mem_usage=True
        )
        
        # Set padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("TinyLlama model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def generate_response(prompt, max_length=300, temperature=0.7):
    """Generate AI response using TinyLlama"""
    global model, tokenizer, device
    
    if model is None or tokenizer is None:
        return "AI model is not loaded"
    
    try:
        # Create chat template
        messages = [
            {
                "role": "system", 
                "content": "You are a helpful assistant for the Reality Lab at Soongsil University. Answer questions about the lab's research areas, team members, and activities. Keep responses concise and informative."
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
        ).to(device)
        
        # Generate response
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_new_tokens=max_length,
                do_sample=True,
                temperature=temperature,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                num_return_sequences=1
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part (remove input prompt)
        input_text = tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)
        generated_text = response[len(input_text):].strip()
        
        return generated_text if generated_text else "Sorry, I couldn't generate a response."
        
    except Exception as e:
        logger.error(f"Error generating response: {e}")
        return "An error occurred while generating the response."

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': model is not None,
        'device': str(device) if device else 'unknown',
        'model_name': 'TinyLlama-1.1B-Chat-v1.0'
    })

@app.route('/generate', methods=['POST'])
def generate():
    """Generate AI response endpoint"""
    try:
        start_time = time.time()
        
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'error': 'No prompt provided'}), 400
        
        user_question = data['prompt']
        language = data.get('language', 'en')  # Default to English for TinyLlama
        
        # Generate response
        response = generate_response(user_question, max_length=300, temperature=0.7)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': response,
            'language': language,
            'model': 'TinyLlama-1.1B-Chat-v1.0',
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint compatible with KULLM3-AWQ interface"""
    try:
        start_time = time.time()
        
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        user_question = data['question']
        language = data.get('language', 'en')
        
        # Generate AI response
        ai_response = generate_response(user_question, max_length=300, temperature=0.7)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'model': 'TinyLlama-1.1B-Chat-v1.0',
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Reality Lab TinyLlama Server...")
    
    # Load model on startup
    if load_model():
        logger.info("TinyLlama Server ready!")
        app.run(host='0.0.0.0', port=4005, debug=False)
    else:
        logger.error("Failed to load model. Server not started.")