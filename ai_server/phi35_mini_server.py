#!/usr/bin/env python3
"""
Reality Lab Phi-3.5-mini Server - Multi-GPU Load Balancing
Distributes inference across multiple GPUs dynamically
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
import subprocess
import threading
from queue import Queue, Empty
import gc

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global variables for multi-GPU setup
models = {}  # Dict: {gpu_id: model}
tokenizer = None
available_gpus = []
gpu_stats = {}
gpu_locks = {}

def get_gpu_utilization():
    """Get current GPU utilization for all GPUs"""
    try:
        result = subprocess.run([
            'nvidia-smi', '--query-gpu=index,utilization.gpu,memory.used,memory.total',
            '--format=csv,noheader,nounits'
        ], capture_output=True, text=True, check=True)
        
        gpu_info = {}
        for line in result.stdout.strip().split('\n'):
            parts = [x.strip() for x in line.split(',')]
            if len(parts) == 4:
                gpu_id = int(parts[0])
                utilization = int(parts[1])
                mem_used = int(parts[2])
                mem_total = int(parts[3])
                mem_free = mem_total - mem_used
                gpu_info[gpu_id] = {
                    'utilization': utilization,
                    'memory_free': mem_free,
                    'memory_used': mem_used
                }
        return gpu_info
    except Exception as e:
        logger.error(f"Error getting GPU utilization: {e}")
        return {}

def select_best_gpu():
    """Select the GPU with lowest utilization and highest free memory from loaded models"""
    # Only consider GPUs that actually have models loaded
    loaded_gpus = list(models.keys())
    
    if not loaded_gpus:
        logger.error("No models are loaded on any GPU")
        return None
    
    current_stats = get_gpu_utilization()
    if not current_stats:
        return loaded_gpus[0]
    
    # Filter only loaded GPUs and sort by utilization, then by free memory
    gpu_options = []
    for gpu_id in loaded_gpus:
        if gpu_id in current_stats:
            stats = current_stats[gpu_id]
            gpu_options.append((gpu_id, stats['utilization'], -stats['memory_free']))
    
    if not gpu_options:
        return loaded_gpus[0]
    
    # Sort by utilization (ascending), then by free memory (descending)
    gpu_options.sort(key=lambda x: (x[1], x[2]))
    best_gpu = gpu_options[0][0]
    
    logger.info(f"Selected GPU {best_gpu} (utilization: {current_stats[best_gpu]['utilization']}%, free memory: {current_stats[best_gpu]['memory_free']}MB)")
    return best_gpu

def load_model_on_gpu(gpu_id):
    """Load Phi-3.5-mini model on a specific GPU"""
    try:
        device = torch.device(f"cuda:{gpu_id}")
        model_name = "microsoft/Phi-3.5-mini-instruct"
        
        logger.info(f"Loading Phi-3.5-mini model on GPU {gpu_id}")
        
        # Set the current GPU
        torch.cuda.set_device(gpu_id)
        
        # Load model with proper attn_implementation
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16,
            device_map=f"cuda:{gpu_id}",
            low_cpu_mem_usage=True,
            trust_remote_code=True,
            attn_implementation="eager"
        )
        
        logger.info(f"Successfully loaded model on GPU {gpu_id}")
        return model
        
    except Exception as e:
        logger.error(f"Failed to load model on GPU {gpu_id}: {e}")
        return None

def load_all_models():
    """Load models on all available GPUs"""
    global models, tokenizer, available_gpus, gpu_locks
    
    try:
        # Check available GPUs
        if not torch.cuda.is_available():
            logger.error("CUDA not available")
            return False
        
        gpu_count = torch.cuda.device_count()
        logger.info(f"Found {gpu_count} GPUs")
        
        # Use all available GPUs
        available_gpus = list(range(gpu_count))
        
        # Load tokenizer once
        model_name = "microsoft/Phi-3.5-mini-instruct"
        logger.info("Loading tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
        
        # Set padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Initialize locks for each GPU
        for gpu_id in available_gpus:
            gpu_locks[gpu_id] = threading.Lock()
        
        # Load models on each GPU
        for gpu_id in available_gpus:
            logger.info(f"Loading model on GPU {gpu_id}...")
            model = load_model_on_gpu(gpu_id)
            if model is not None:
                models[gpu_id] = model
                logger.info(f"✅ Model loaded successfully on GPU {gpu_id}")
            else:
                logger.error(f"❌ Failed to load model on GPU {gpu_id}")
        
        if not models:
            logger.error("No models loaded successfully")
            return False
        
        logger.info(f"Successfully loaded models on {len(models)} GPUs: {list(models.keys())}")
        return True
        
    except Exception as e:
        logger.error(f"Error in load_all_models: {e}")
        return False

def generate_response_multigpu(prompt, max_length=400, temperature=0.7):
    """Generate AI response using the best available GPU"""
    global models, tokenizer
    
    if not models or tokenizer is None:
        return "AI models are not loaded"
    
    # Select the best GPU for this request
    best_gpu = select_best_gpu()
    
    if best_gpu is None:
        logger.error("No GPU available for inference")
        return "AI model not available"
    
    if best_gpu not in models:
        logger.error(f"Model not available on GPU {best_gpu}")
        return "AI model not available"
    
    try:
        # Acquire lock for the selected GPU
        with gpu_locks[best_gpu]:
            model = models[best_gpu]
            device = torch.device(f"cuda:{best_gpu}")
            
            # Create chat template with detailed Reality Lab information
            messages = [
                {
                    "role": "system", 
                    "content": """당신은 숭실대학교 Reality Lab의 전문 어시스턴트입니다. 연구실에 대한 질문에 정확하고 간결하게 답변하세요.

Reality Lab 정보:
- 설립: 2023년 숭실대학교
- 지도교수: 김희원 교수 (heewon@ssu.ac.kr, +82-2-820-0679)
- 연구분야: 로보틱스, 컴퓨터 비전, 기계학습, AI 응용
- 팀구성: 김희원 교수, 최영재(박사), 고현서(석사), 정호재(석사), 채병관(연구조교), 김도원(연구조교)
- 위치: 서울, 대한민국

질문에 직접적으로 답변하고 불필요한 추가 정보는 제공하지 마세요."""
                },
                {"role": "user", "content": prompt}
            ]
            
            # Apply chat template
            formatted_prompt = tokenizer.apply_chat_template(
                messages, 
                tokenize=False, 
                add_generation_prompt=True
            )
            
            # Tokenize input and move to the selected GPU
            inputs = tokenizer(
                formatted_prompt, 
                return_tensors="pt", 
                truncation=True, 
                max_length=512
            ).to(device)
            
            # Generate response
            with torch.no_grad():
                outputs = model.generate(
                    inputs.input_ids,
                    max_new_tokens=max_length,
                    temperature=temperature,
                    do_sample=True,
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    attention_mask=inputs.attention_mask
                )
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract generated text (remove input prompt)
            generated_text = response[len(formatted_prompt):].strip()
            
            logger.info(f"Generated response on GPU {best_gpu}")
            
            if generated_text:
                return generated_text
            else:
                logger.warning("Generated text is empty, falling back to default message")
                return "죄송합니다. 응답을 생성할 수 없습니다."
            
    except Exception as e:
        logger.error(f"Error generating response on GPU {best_gpu}: {e}")
        return "응답 생성 중 오류가 발생했습니다."

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'model_loaded': len(models) > 0,
        'available_gpus': available_gpus,
        'loaded_gpus': list(models.keys()),
        'model_name': 'Phi-3.5-mini-instruct'
    })

@app.route('/gpu_status', methods=['GET'])
def gpu_status():
    """Get current GPU utilization status"""
    gpu_info = get_gpu_utilization()
    return jsonify({
        'gpu_utilization': gpu_info,
        'available_gpus': available_gpus,
        'loaded_gpus': list(models.keys())
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
        language = data.get('language', 'ko')
        
        # Generate response using multi-GPU load balancing
        response = generate_response_multigpu(user_question, max_length=400, temperature=0.7)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': response,
            'language': language,
            'model': 'Phi-3.5-mini-instruct',
            'response_time': response_time,
            'gpu_used': select_best_gpu()
        })
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint compatible with frontend interface"""
    try:
        start_time = time.time()
        
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        user_question = data['question']
        language = data.get('language', 'ko')
        
        # Generate AI response using multi-GPU load balancing
        ai_response = generate_response_multigpu(user_question, max_length=400, temperature=0.7)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'model': 'Phi-3.5-mini-instruct',
            'response_time': response_time,
            'gpu_used': select_best_gpu()
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Multi-GPU Reality Lab Phi-3.5-mini Server...")
    
    # Load models on all GPUs
    if load_all_models():
        logger.info("🚀 Multi-GPU Phi-3.5-mini server ready!")
        
        # Start Flask server
        app.run(
            host='0.0.0.0', 
            port=4008, 
            debug=False,
            threaded=True
        )
    else:
        logger.error("❌ Failed to load models. Server not started.")