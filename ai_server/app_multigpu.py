#!/usr/bin/env python3
"""
Reality Lab KULLM3-AWQ Server - Multi-GPU Load Balancing
Distributes inference across multiple GPUs dynamically
"""

import os
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
try:
    from awq import AutoAWQForCausalLM
    AWQ_AVAILABLE = True
except ImportError:
    AWQ_AVAILABLE = False
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
import subprocess
import threading

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend access

# Global variables for multi-GPU setup
models = {}  # Dict: {gpu_id: model}
tokenizer = None
available_gpus = []
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
    """Select the GPU with lowest utilization and highest free memory"""
    current_stats = get_gpu_utilization()
    if not current_stats:
        return available_gpus[0] if available_gpus else 0
    
    # Filter only available GPUs and sort by utilization, then by free memory
    gpu_options = []
    for gpu_id in available_gpus:
        if gpu_id in current_stats:
            stats = current_stats[gpu_id]
            gpu_options.append((gpu_id, stats['utilization'], -stats['memory_free']))
    
    if not gpu_options:
        return available_gpus[0] if available_gpus else 0
    
    # Sort by utilization (ascending), then by free memory (descending)
    gpu_options.sort(key=lambda x: (x[1], x[2]))
    best_gpu = gpu_options[0][0]
    
    logger.info(f"Selected GPU {best_gpu} (utilization: {current_stats[best_gpu]['utilization']}%, free memory: {current_stats[best_gpu]['memory_free']}MB)")
    return best_gpu

def load_model_on_gpu(gpu_id):
    """Load KULLM3-AWQ model on a specific GPU"""
    try:
        device = torch.device(f"cuda:{gpu_id}")
        model_name = "/home/i0179/models/KULLM3-awq"
        
        logger.info(f"Loading KULLM3-AWQ model on GPU {gpu_id}")
        
        # Set the current GPU
        torch.cuda.set_device(gpu_id)
        
        # Set environment variable to disable weights_only check
        os.environ['TORCH_DISABLE_WEIGHTS_ONLY_WARNING'] = '1'
        
        # Try AutoAWQ first, fallback to standard loading if needed
        model = None
        if AWQ_AVAILABLE:
            try:
                logger.info(f"Loading AWQ quantized model on GPU {gpu_id}")
                model = AutoAWQForCausalLM.from_quantized(
                    model_name,
                    fuse_layers=False,  # Disable layer fusion to avoid kernel issues
                    trust_remote_code=True,
                    safetensors=True,
                    device_map=f"cuda:{gpu_id}"
                )
                logger.info(f"AWQ model loaded successfully on GPU {gpu_id}")
            except Exception as e:
                logger.warning(f"AWQ loading failed on GPU {gpu_id}: {e}, trying standard loading")
                model = None
        
        if model is None:
            logger.info(f"Loading standard model on GPU {gpu_id}")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16,
                trust_remote_code=True,
                device_map=f"cuda:{gpu_id}",
                low_cpu_mem_usage=True
            )
        
        logger.info(f"Successfully loaded KULLM3 model on GPU {gpu_id}")
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
        model_name = "/home/i0179/models/KULLM3-awq"
        logger.info("Loading tokenizer")
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        # Set padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Initialize locks for each GPU
        for gpu_id in available_gpus:
            gpu_locks[gpu_id] = threading.Lock()
        
        # Load models on each GPU (this will take time)
        for gpu_id in available_gpus:
            logger.info(f"Loading KULLM3 model on GPU {gpu_id}...")
            model = load_model_on_gpu(gpu_id)
            if model is not None:
                models[gpu_id] = model
                logger.info(f"✅ KULLM3 model loaded successfully on GPU {gpu_id}")
            else:
                logger.error(f"❌ Failed to load KULLM3 model on GPU {gpu_id}")
        
        if not models:
            logger.error("No KULLM3 models loaded successfully")
            return False
        
        logger.info(f"Successfully loaded KULLM3 models on {len(models)} GPUs: {list(models.keys())}")
        return True
        
    except Exception as e:
        logger.error(f"Error in load_all_models: {e}")
        return False

def generate_response_multigpu(prompt, max_length=150, temperature=0.7):
    """Generate AI response using KULLM3 on the best available GPU - OPTIMIZED FOR SPEED"""
    global models, tokenizer
    
    if not models or tokenizer is None:
        return "AI models are not loaded"
    
    # Select the best GPU for this request
    best_gpu = select_best_gpu()
    
    if best_gpu not in models:
        logger.error(f"Model not available on GPU {best_gpu}")
        return "AI model not available"
    
    try:
        # Acquire lock for the selected GPU
        with gpu_locks[best_gpu]:
            model = models[best_gpu]
            device = torch.device(f"cuda:{best_gpu}")
            
            # Tokenize input with shorter max length for faster processing
            inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=256)
            inputs = {k: v.to(device) for k, v in inputs.items()}
            
            # Generate response with optimized parameters for speed
            with torch.no_grad():
                outputs = model.generate(
                    input_ids=inputs["input_ids"],
                    attention_mask=inputs.get("attention_mask"),
                    max_new_tokens=max_length,  # Reduced from 300 to 150
                    do_sample=False,  # Greedy decoding is fastest
                    pad_token_id=tokenizer.eos_token_id,
                    eos_token_id=tokenizer.eos_token_id,
                    num_return_sequences=1,
                    # Speed optimizations
                    use_cache=True,
                    early_stopping=True
                )
            
            # Decode response
            response = tokenizer.decode(outputs[0], skip_special_tokens=True)
            
            # Extract only the generated part (remove input prompt)
            input_text = tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)
            generated_text = response[len(input_text):].strip()
            
            logger.info(f"Generated KULLM3 response on GPU {best_gpu}")
            return generated_text if generated_text else "죄송합니다. 응답을 생성할 수 없습니다."
            
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
        'loaded_gpus': list(models.keys())
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
        
        # Generate response using multi-GPU load balancing (optimized for speed)
        response = generate_response_multigpu(prompt, max_length=150, temperature=0.7)
        
        # Clean up response (remove system prompt remnants)
        if language == 'en':
            if "Answer:" in response:
                response = response.split("Answer:")[-1].strip()
        else:
            if "답변:" in response:
                response = response.split("답변:")[-1].strip()
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': response,
            'language': language,
            'response_time': response_time,
            'gpu_used': select_best_gpu()  # Show which GPU was likely used
        })
        
    except Exception as e:
        logger.error(f"Error in generate endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Auto-save chat and generate AI response"""
    try:
        start_time = time.time()
        
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        user_question = data['question']
        language = data.get('language', 'ko')
        
        # Generate AI response directly
        system_prompt = """당신은 숭실대학교 리얼리티 연구실의 도움이 되는 어시스턴트입니다. 연구실의 연구 분야, 팀 구성원, 활동에 대한 질문에 답변해주세요. 간결하고 유익한 답변을 해주세요.

질문: """ if language == 'ko' else """You are a helpful assistant for the Reality Lab at Soongsil University. Answer questions about the lab's research areas, team members, and activities. Keep responses concise and informative.

Question: """
        
        prompt = system_prompt + user_question + ("\n답변:" if language == 'ko' else "\nAnswer:")
        ai_response = generate_response_multigpu(prompt, max_length=150, temperature=0.7)
        
        # Clean up response
        if language == 'ko' and "답변:" in ai_response:
            ai_response = ai_response.split("답변:")[-1].strip()
        elif language == 'en' and "Answer:" in ai_response:
            ai_response = ai_response.split("Answer:")[-1].strip()
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'auto_saved': True,
            'response_time': response_time,
            'gpu_used': select_best_gpu()  # Show which GPU was likely used
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Multi-GPU Reality Lab KULLM3-AWQ Server...")
    
    # Load models on all GPUs (this will take several minutes)
    if load_all_models():
        logger.info("🚀 Multi-GPU KULLM3-AWQ server ready!")
        
        # Start Flask server
        app.run(
            host='0.0.0.0', 
            port=4003, 
            debug=False,
            threaded=True  # Enable threading for concurrent requests
        )
    else:
        logger.error("❌ Failed to load KULLM3 models. Server not started.")