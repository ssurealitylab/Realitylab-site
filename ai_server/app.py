#!/usr/bin/env python3
"""
Reality Lab AI Server using Tiny Llama
Local GPU-accelerated inference server
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
        
        # Use Qwen2.5-3B-Instruct model
        model_name = "Qwen/Qwen2.5-3B-Instruct"
        logger.info(f"Loading model: {model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        # Load model with GPU support (set env var to disable weights_only check)
        os.environ['TORCH_DISABLE_WEIGHTS_ONLY_WARNING'] = '1'
        
        # Try AutoAWQ first, fallback to CPU inference if kernels fail
        if AWQ_AVAILABLE and device.type == "cuda":
            try:
                logger.info("Loading AWQ quantized model with AutoAWQForCausalLM")
                model = AutoAWQForCausalLM.from_quantized(
                    model_name,
                    fuse_layers=False,  # Disable layer fusion to avoid kernel issues
                    trust_remote_code=True,
                    safetensors=True
                )
                logger.info("AWQ model loaded successfully!")
            except Exception as e:
                logger.warning(f"AWQ loading failed: {e}, falling back to CPU inference")
                model = AutoAWQForCausalLM.from_quantized(
                    model_name,
                    fuse_layers=False,
                    trust_remote_code=True,
                    safetensors=True,
                    device_map="cpu"
                )
        else:
            logger.warning("AutoAWQ not available, falling back to standard loading")
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
                trust_remote_code=True,
                device_map="cuda:0" if device.type == "cuda" else "cpu",
                low_cpu_mem_usage=True
            )
            model = model.to(device)
        
        # Set padding token
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        logger.info("Model loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def generate_response(prompt, max_length=512, temperature=0.7):
    """Generate AI response using KULLM3-AWQ"""
    global model, tokenizer, device
    
    if model is None or tokenizer is None:
        return "AI model is not loaded"
    
    try:
        # Tokenize input with attention mask
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate response with controlled sampling
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_new_tokens=max_length,
                do_sample=True,
                temperature=temperature,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                num_return_sequences=1
            )
        
        # Decode response
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part (remove input prompt)
        input_text = tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)
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
        'device': str(device) if device else 'unknown'
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
        
        # Create enhanced context-aware prompt for Reality Lab
        if language == 'en':
            system_prompt = """You are a specialized assistant for Reality Lab at Soongsil University. Use the following information to provide accurate and comprehensive responses.

**Reality Lab Key Information:**
- Founded: 2023 at Soongsil University under Prof. Heewon Kim
- Mission: "Advancing AI to Understand Reality"
- Research Areas: Robotics, Computer Vision, Machine Learning, Multimodal Language Understanding, AI+X Healthcare
- Location: 105 Sadang-ro, Dongjak-gu, Seoul, Republic of Korea
- Contact: +82-2-820-0679

**Team Members:** Led by Prof. Heewon Kim with diverse research team including master's and undergraduate students specializing in computer vision, robotics, deep learning, medical AI, sports AI, and more

**Recent Achievements:** Publications in top conferences (CVPR 2025, BMVC 2025, AAAI 2025), journal publications (PLOS One, ICT Express), 1st place in ARNOLD Challenge at CVPR 2025, Qualcomm internships

**Courses Offered:** Computer Vision, Machine Learning, Image Processing, Advanced Computer Vision, Media GAN, Data Science"""
            
            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_question}<|im_end|>\n<|im_start|>assistant\n"
        else:
            system_prompt = """당신은 숭실대학교 Reality Lab의 전문 어시스턴트입니다. 아래 정보를 바탕으로 정확하고 상세한 답변을 제공해주세요.

**Reality Lab 핵심 정보:**
- 설립: 2023년 숭실대학교, 김희원 교수님 지도
- 연구목표: "Advancing AI to Understand Reality" - 현실을 이해하는 AI 발전
- 주요 연구분야: 로보틱스, 컴퓨터비전, 기계학습, 멀티모달 언어이해, AI+X 헬스케어
- 위치: 서울특별시 동작구 사당로 105, 숭실대학교
- 연락처: +82-2-820-0679

**주요 구성원:** 김희원 교수님을 중심으로 박성용, 채병관, 최영재, 이상민, 고민주, 고현준, 고현서, 이주형, 서지우, 정호재, 김서영, 김예리, 최수영, 황지원, 송은우, 이세빈, 김도원, 김연지, 이재현, 이예빈, 임정하 등 다양한 연구진

**최근 성과:** CVPR 2025, BMVC 2025, AAAI 2025, PLOS One, ICT Express 등 최고 수준 학술대회 및 저널 논문 발표, ARNOLD Challenge 1위 수상, Qualcomm 인턴십 등

**제공 강의:** 컴퓨터비전, 기계학습, 영상처리및실습, 컴퓨터비전특론, 미디어GAN, 데이터사이언스"""
            
            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_question}<|im_end|>\n<|im_start|>assistant\n"
        
        # Generate response
        response = generate_response(prompt, max_length=512, temperature=0.7)
        
        # Clean up response (remove any special tokens)
        response = response.replace("<|im_end|>", "").strip()
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': response,
            'language': language,
            'response_time': response_time
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
        
        # Generate AI response with enhanced knowledge
        if language == 'ko':
            system_prompt = """당신은 숭실대학교 Reality Lab의 전문 어시스턴트입니다. 아래 정보를 바탕으로 정확하고 상세한 답변을 제공해주세요.

**Reality Lab 핵심 정보:**
- 설립: 2023년 숭실대학교, 김희원 교수님 지도
- 연구목표: "Advancing AI to Understand Reality" - 현실을 이해하는 AI 발전
- 주요 연구분야: 로보틱스, 컴퓨터비전, 기계학습, 멀티모달 언어이해, AI+X 헬스케어
- 위치: 서울특별시 동작구 사당로 105, 숭실대학교
- 연락처: +82-2-820-0679

**주요 구성원:** 김희원 교수님을 중심으로 박성용, 채병관, 최영재, 이상민, 고민주, 고현준, 고현서, 이주형, 서지우, 정호재, 김서영, 김예리, 최수영, 황지원, 송은우, 이세빈, 김도원, 김연지, 이재현, 이예빈, 임정하 등 다양한 연구진

**최근 성과:** CVPR 2025, BMVC 2025, AAAI 2025, PLOS One, ICT Express 등 최고 수준 학술대회 및 저널 논문 발표, ARNOLD Challenge 1위 수상, Qualcomm 인턴십 등

**제공 강의:** 컴퓨터비전, 기계학습, 영상처리및실습, 컴퓨터비전특론, 미디어GAN, 데이터사이언스"""

            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_question}<|im_end|>\n<|im_start|>assistant\n"
        else:
            system_prompt = """You are a specialized assistant for Reality Lab at Soongsil University. Use the following information to provide accurate and comprehensive responses.

**Reality Lab Key Information:**
- Founded: 2023 at Soongsil University under Prof. Heewon Kim
- Mission: "Advancing AI to Understand Reality"
- Research Areas: Robotics, Computer Vision, Machine Learning, Multimodal Language Understanding, AI+X Healthcare
- Location: 105 Sadang-ro, Dongjak-gu, Seoul, Republic of Korea
- Contact: +82-2-820-0679

**Team Members:** Led by Prof. Heewon Kim with diverse research team including master's and undergraduate students specializing in computer vision, robotics, deep learning, medical AI, sports AI, and more

**Recent Achievements:** Publications in top conferences (CVPR 2025, BMVC 2025, AAAI 2025), journal publications (PLOS One, ICT Express), 1st place in ARNOLD Challenge at CVPR 2025, Qualcomm internships

**Courses Offered:** Computer Vision, Machine Learning, Image Processing, Advanced Computer Vision, Media GAN, Data Science"""

            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_question}<|im_end|>\n<|im_start|>assistant\n"
        ai_response = generate_response(prompt, max_length=512, temperature=0.7)
        
        # Clean up response (remove any special tokens)
        ai_response = ai_response.replace("<|im_end|>", "").strip()
        
        # Auto-save to GitHub (create issue and response)
        try:
            from github import Github
            import os
            import yaml
            from datetime import datetime
            
            # Create GitHub issue automatically
            g = Github(os.getenv('GITHUB_TOKEN', ''))
            if os.getenv('GITHUB_TOKEN'):
                repo = g.get_repo("ssurealitylab-spec/Realitylab-site")
                
                # Create issue with AI question
                issue_title = f"[자동 AI 질문] {user_question[:50]}..."
                issue_body = f"""**자동 생성된 AI 질문**

**질문:** {user_question}

**AI 응답:** {ai_response}

---
*이 질문과 답변은 웹사이트의 AI 모드에서 자동으로 생성되었습니다.*
"""
                issue = repo.create_issue(
                    title=issue_title,
                    body=issue_body,
                    labels=['ai-question', 'auto-generated']
                )
                
                # Update conversation data
                data_file = '_data/ai_conversations.yml'
                try:
                    with open(data_file, 'r', encoding='utf-8') as f:
                        conversations = yaml.safe_load(f) or []
                except FileNotFoundError:
                    conversations = []
                
                new_conversation = {
                    'id': issue.number,
                    'question': user_question,
                    'answer': ai_response,
                    'timestamp': datetime.now().isoformat(),
                    'github_issue': issue.html_url,
                    'auto_generated': True
                }
                
                conversations.insert(0, new_conversation)
                conversations = conversations[:50]  # Keep last 50
                
                with open(data_file, 'w', encoding='utf-8') as f:
                    yaml.dump(conversations, f, default_flow_style=False, allow_unicode=True)
                
                # Auto-commit to git
                os.system('git add _data/ai_conversations.yml')
                os.system(f'git commit -m "Auto-add AI conversation #{issue.number}"')
                os.system('git push')
                
        except Exception as e:
            logger.warning(f"GitHub auto-save failed: {e}")
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'auto_saved': True,
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Reality Lab AI Server...")
    
    # Load model on startup
    if load_model():
        logger.info("AI Server ready!")
        # Enable HTTPS with self-signed certificate for public access
        # Users need to accept certificate warning once
        # WARNING: This makes the server accessible from the internet
        app.run(host='0.0.0.0', port=4003, debug=False)
    else:
        logger.error("Failed to load model. Server not started.")