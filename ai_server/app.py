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
        
        # Use local KULLM3-AWQ files
        model_name = "/home/i0179/models/KULLM3-awq"
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

def generate_response(prompt, max_length=300, temperature=0.7):
    """Generate AI response using KULLM3-AWQ"""
    global model, tokenizer, device
    
    if model is None or tokenizer is None:
        return "AI model is not loaded"
    
    try:
        # Tokenize input with attention mask
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=512)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate response with greedy decoding to avoid sampling issues
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_new_tokens=max_length,
                do_sample=False,  # Use greedy decoding
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
        response = generate_response(prompt, max_length=300, temperature=0.7)
        
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
        
        # Generate AI response directly
        system_prompt = """당신은 숭실대학교 리얼리티 연구실의 도움이 되는 어시스턴트입니다. 연구실의 연구 분야, 팀 구성원, 활동에 대한 질문에 답변해주세요. 간결하고 유익한 답변을 해주세요.

질문: """ if language == 'ko' else """You are a helpful assistant for the Reality Lab at Soongsil University. Answer questions about the lab's research areas, team members, and activities. Keep responses concise and informative.

Question: """
        
        prompt = system_prompt + user_question + ("\n답변:" if language == 'ko' else "\nAnswer:")
        ai_response = generate_response(prompt, max_length=300, temperature=0.7)
        
        # Clean up response
        if language == 'en' and "Answer:" in ai_response:
            ai_response = ai_response.split("Answer:")[-1].strip()
        elif language == 'ko' and "답변:" in ai_response:
            ai_response = ai_response.split("답변:")[-1].strip()
        
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