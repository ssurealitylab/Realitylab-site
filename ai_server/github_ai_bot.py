#!/usr/bin/env python3
"""
Reality Lab GitHub AI Bot
Automatically responds to GitHub issues with AI-generated answers
"""

import os
import requests
import yaml
from datetime import datetime
from github import Github

def generate_ai_response(question):
    """Generate AI response using local server"""
    try:
        response = requests.post('http://127.0.0.1:5000/generate', 
                               json={
                                   'prompt': question,
                                   'language': 'ko'
                               }, 
                               timeout=30)
        if response.ok:
            return response.json().get('response', 'AI 응답 생성 실패')
        else:
            return 'AI 서버 오류'
    except Exception as e:
        print(f"AI generation error: {e}")
        return 'AI 서버에 연결할 수 없습니다.'

def update_conversations_data(question, answer, issue_number):
    """Update Jekyll data file with new conversation"""
    data_file = '_data/ai_conversations.yml'
    
    # Load existing data or create new
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            conversations = yaml.safe_load(f) or []
    except FileNotFoundError:
        conversations = []
    
    # Add new conversation
    new_conversation = {
        'id': issue_number,
        'question': question,
        'answer': answer,
        'timestamp': datetime.now().isoformat(),
        'github_issue': f"https://github.com/ssurealitylab-spec/Realitylab-site/issues/{issue_number}"
    }
    
    conversations.insert(0, new_conversation)  # Add to top
    
    # Keep only last 50 conversations
    conversations = conversations[:50]
    
    # Save updated data
    with open(data_file, 'w', encoding='utf-8') as f:
        yaml.dump(conversations, f, default_flow_style=False, allow_unicode=True)
    
    print(f"Updated conversations data with {len(conversations)} entries")

def main():
    # Get environment variables
    github_token = os.getenv('GITHUB_TOKEN')
    issue_number = os.getenv('ISSUE_NUMBER')
    issue_title = os.getenv('ISSUE_TITLE')
    issue_body = os.getenv('ISSUE_BODY')
    comment_body = os.getenv('COMMENT_BODY')
    
    if not all([github_token, issue_number]):
        print("Missing required environment variables")
        return
    
    # Initialize GitHub client
    g = Github(github_token)
    repo = g.get_repo("ssurealitylab-spec/Realitylab-site")
    issue = repo.get_issue(int(issue_number))
    
    # Determine question text
    if comment_body and '@ai' in comment_body:
        question = comment_body.replace('@ai', '').strip()
    else:
        question = f"{issue_title}\n\n{issue_body}" if issue_body else issue_title
    
    print(f"Processing question: {question[:100]}...")
    
    # Generate AI response
    ai_answer = generate_ai_response(question)
    print(f"Generated AI response: {ai_answer[:100]}...")
    
    # Update website data
    update_conversations_data(question, ai_answer, issue_number)
    
    # Post response as comment
    response_comment = f"""🤖 **Reality Lab AI 응답:**

{ai_answer}

---
*이 응답은 Reality Lab의 GPU 서버에서 고려대 KULLM 모델로 생성되었습니다.*
*더 자세한 정보가 필요하시면 [웹사이트](https://ssurealitylab-spec.github.io/Realitylab-site/)를 방문해주세요!*
"""
    
    issue.create_comment(response_comment)
    print("Posted AI response to GitHub issue")

if __name__ == '__main__':
    main()