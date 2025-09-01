#!/usr/bin/env python3
"""
Enhanced Reality Lab AI Server with Knowledge Base Integration
Uses RAG (Retrieval-Augmented Generation) with Reality Lab dataset
"""

import os
import json
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import time
import re
from datetime import datetime

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global variables
model = None
tokenizer = None
device = None
knowledge_base = None

class RealityLabKnowledgeBase:
    """Reality Lab Knowledge Base for RAG"""
    
    def __init__(self):
        self.knowledge = {}
        self.load_knowledge_base()
    
    def load_knowledge_base(self):
        """Load Reality Lab dataset"""
        try:
            # Load structured data
            with open('reality_lab_dataset/structured_data.json', 'r', encoding='utf-8') as f:
                structured_data = json.load(f)
            
            # Load instruction dataset
            with open('reality_lab_dataset/instruction_dataset.json', 'r', encoding='utf-8') as f:
                instruction_data = json.load(f)
            
            # Create searchable knowledge base
            self.knowledge = {
                'general': [],
                'news': [],
                'members': [],
                'publications': [],
                'courses': [],
                'contact': [],
                'qa_pairs': instruction_data
            }
            
            # Process structured data
            if 'sections' in structured_data:
                for category, items in structured_data['sections'].items():
                    if category in self.knowledge:
                        for item in items:
                            self.knowledge[category].append(item['content'])
            
            logger.info(f"Knowledge base loaded with {len(instruction_data)} Q&A pairs")
            
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self.knowledge = {'qa_pairs': []}
    
    def search_knowledge(self, query, top_k=3):
        """Search relevant knowledge for the query"""
        query_lower = query.lower()
        relevant_info = []
        
        # Search Q&A pairs first
        for qa in self.knowledge['qa_pairs']:
            instruction = qa['instruction'].lower()
            # Simple keyword matching
            if any(keyword in instruction for keyword in query_lower.split()):
                relevant_info.append(qa['output'])
                if len(relevant_info) >= top_k:
                    break
        
        # Search by category keywords
        category_keywords = {
            'news': ['뉴스', '최근', '성과', '논문', '수상', '발표'],
            'members': ['구성원', '팀', '교수', '학생', '연구원', '멤버'],
            'publications': ['논문', '출간', '발표', '연구', 'paper', 'publication'],
            'courses': ['강의', '수업', '교육', '과목', '코스'],
            'contact': ['연락처', '전화', '주소', '위치', '연락']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in query_lower for keyword in keywords):
                if category in self.knowledge:
                    relevant_info.extend(self.knowledge[category][:2])  # Add top 2 from each category
        
        return relevant_info[:top_k]

def load_model():
    """Load Qwen2.5-3B model and tokenizer"""
    global model, tokenizer, device, knowledge_base
    
    try:
        if torch.cuda.is_available():
            device = torch.device("cuda")
            logger.info(f"Using GPU: {torch.cuda.get_device_name(0)}")
        else:
            device = torch.device("cpu")
            logger.info("Using CPU")
        
        model_name = "Qwen/Qwen2.5-3B-Instruct"
        logger.info(f"Loading model: {model_name}")
        
        # Load tokenizer
        tokenizer = AutoTokenizer.from_pretrained(
            model_name,
            trust_remote_code=True
        )
        
        os.environ['TORCH_DISABLE_WEIGHTS_ONLY_WARNING'] = '1'
        
        # Load model
        model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=torch.float16 if device.type == "cuda" else torch.float32,
            trust_remote_code=True,
            device_map="cuda:0" if device.type == "cuda" else "cpu",
            low_cpu_mem_usage=True
        )
        model = model.to(device)
        
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
        
        # Load knowledge base
        knowledge_base = RealityLabKnowledgeBase()
        
        logger.info("Enhanced model with knowledge base loaded successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Error loading model: {e}")
        return False

def generate_enhanced_response(user_question, language='ko', max_length=512):
    """Generate response using RAG approach"""
    global model, tokenizer, device, knowledge_base
    
    if model is None or tokenizer is None:
        return "AI 모델이 로드되지 않았습니다."
    
    try:
        # Search relevant knowledge
        relevant_info = knowledge_base.search_knowledge(user_question, top_k=2)
        
        # Create enhanced system prompt with retrieved knowledge
        if language == 'ko':
            system_prompt = f"""당신은 숭실대학교 Reality Lab의 전문 어시스턴트입니다. 아래 정보를 참고하여 정확하고 도움이 되는 답변을 제공해주세요.

**Reality Lab 정보:**
- 설립: 2023년 숭실대학교
- 지도교수: 김희원 교수님  
- 연구목표: "Advancing AI to Understand Reality" - 현실을 이해하는 AI 발전
- 연구분야: 로보틱스, 컴퓨터비전, 기계학습, 멀티모달 언어이해, AI+X 헬스케어
- 위치: 서울특별시 동작구 사당로 105, 숭실대학교
- 연락처: +82-2-820-0679

**관련 정보:**
{chr(10).join(relevant_info[:2]) if relevant_info else '추가 정보를 검색중입니다.'}"""

            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_question}<|im_end|>\n<|im_start|>assistant\n"
        else:
            system_prompt = f"""You are a specialized assistant for Reality Lab at Soongsil University. Use the following information to provide accurate and helpful responses.

**Reality Lab Information:**
- Founded: 2023 at Soongsil University
- Director: Prof. Heewon Kim
- Mission: "Advancing AI to Understand Reality"  
- Research Areas: Robotics, Computer Vision, Machine Learning, Multimodal Language Understanding, AI+X Healthcare
- Location: 105 Sadang-ro, Dongjak-gu, Seoul, Republic of Korea
- Contact: +82-2-820-0679

**Relevant Information:**
{chr(10).join(relevant_info[:2]) if relevant_info else 'Searching for additional information.'}"""

            prompt = f"<|im_start|>system\n{system_prompt}<|im_end|>\n<|im_start|>user\n{user_question}<|im_end|>\n<|im_start|>assistant\n"
        
        # Generate response
        inputs = tokenizer(prompt, return_tensors="pt", padding=True, truncation=True, max_length=1024)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        with torch.no_grad():
            outputs = model.generate(
                input_ids=inputs["input_ids"],
                attention_mask=inputs.get("attention_mask"),
                max_new_tokens=max_length,
                do_sample=True,
                temperature=0.7,
                top_p=0.9,
                top_k=50,
                repetition_penalty=1.1,
                pad_token_id=tokenizer.eos_token_id,
                eos_token_id=tokenizer.eos_token_id,
                num_return_sequences=1
            )
        
        response = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the generated part
        input_text = tokenizer.decode(inputs["input_ids"][0], skip_special_tokens=True)
        generated_text = response[len(input_text):].strip()
        
        # Clean up response
        generated_text = generated_text.replace("<|im_end|>", "").strip()
        
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
        'knowledge_base_loaded': knowledge_base is not None,
        'device': str(device) if device else 'unknown'
    })

@app.route('/chat', methods=['POST'])
def chat():
    """Enhanced chat endpoint with knowledge base"""
    try:
        start_time = time.time()
        
        data = request.json
        if not data or 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        user_question = data['question']
        language = data.get('language', 'ko')
        
        # Generate enhanced response
        ai_response = generate_enhanced_response(user_question, language, max_length=512)
        
        # Auto-save to GitHub (simplified)
        try:
            from github import Github
            import yaml
            
            g = Github(os.getenv('GITHUB_TOKEN', ''))
            if os.getenv('GITHUB_TOKEN'):
                repo = g.get_repo("ssurealitylab-spec/Realitylab-site")
                
                issue_title = f"[Enhanced AI 질문] {user_question[:50]}..."
                issue_body = f"""**Enhanced AI 질문 및 답변**

**질문:** {user_question}

**AI 답변 (Knowledge Base 활용):** {ai_response}

---
*이 답변은 Reality Lab 지식베이스를 활용한 Enhanced AI에서 생성되었습니다.*
"""
                issue = repo.create_issue(
                    title=issue_title,
                    body=issue_body,
                    labels=['enhanced-ai-question', 'knowledge-base']
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
                    'enhanced': True,
                    'knowledge_base_used': True
                }
                
                conversations.insert(0, new_conversation)
                conversations = conversations[:50]
                
                with open(data_file, 'w', encoding='utf-8') as f:
                    yaml.dump(conversations, f, default_flow_style=False, allow_unicode=True)
                
                os.system('git add _data/ai_conversations.yml')
                os.system(f'git commit -m "Add enhanced AI conversation #{issue.number}"')
                os.system('git push')
                
        except Exception as e:
            logger.warning(f"GitHub auto-save failed: {e}")
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': ai_response,
            'language': language,
            'enhanced': True,
            'knowledge_base_used': True,
            'auto_saved': True,
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/generate', methods=['POST'])
def generate():
    """Enhanced generate endpoint"""
    try:
        start_time = time.time()
        
        data = request.json
        if not data or 'prompt' not in data:
            return jsonify({'error': 'No prompt provided'}), 400
        
        user_question = data['prompt']
        language = data.get('language', 'ko')
        
        response = generate_enhanced_response(user_question, language, max_length=512)
        
        end_time = time.time()
        response_time = round(end_time - start_time, 2)
        
        return jsonify({
            'response': response,
            'language': language,
            'enhanced': True,
            'knowledge_base_used': True,
            'response_time': response_time
        })
        
    except Exception as e:
        logger.error(f"Error in enhanced generate endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    logger.info("Starting Enhanced Reality Lab AI Server...")
    
    if load_model():
        logger.info("Enhanced AI Server with Knowledge Base ready!")
        app.run(host='0.0.0.0', port=4010, debug=False)
    else:
        logger.error("Failed to load model. Server not started.")