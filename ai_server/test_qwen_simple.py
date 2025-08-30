#!/usr/bin/env python3
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        print(f"Request content type: {request.content_type}")
        print(f"Request data: {request.data}")
        print(f"Request is_json: {request.is_json}")
        
        data = request.get_json(force=True)
        print(f"Parsed JSON: {data}")
        
        if not data:
            return jsonify({'error': 'No JSON data provided'}), 400
        
        if 'question' not in data:
            return jsonify({'error': 'No question provided'}), 400
        
        question = data['question']
        return jsonify({
            'response': f'테스트 응답: {question}',
            'model': 'Test-Server'
        })
        
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4008, debug=True)