#!/usr/bin/env python3
"""
GPU Manager Server - Dynamic GPU allocation for Reality Lab AI servers
"""

import os
import subprocess
import time
import threading
import uuid
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
import psutil
import signal
import requests

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Global state
gpu_sessions = {}  # session_id -> {'gpu_id': int, 'process': subprocess.Popen, 'port': int}
available_gpus = [0, 1, 2, 3]  # GPU indices
base_port = 5000

class GPUManager:
    def __init__(self):
        self.lock = threading.Lock()
    
    def get_gpu_memory_usage(self, gpu_id):
        """Get GPU memory usage in MB"""
        try:
            result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits', f'--id={gpu_id}'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                return int(result.stdout.strip())
            return 0
        except Exception as e:
            logger.error(f"Failed to get GPU {gpu_id} memory usage: {e}")
            return 0
    
    def find_available_gpu(self):
        """Find the first GPU with low memory usage"""
        for gpu_id in available_gpus:
            memory_usage = self.get_gpu_memory_usage(gpu_id)
            if memory_usage < 500:  # Less than 500MB in use
                return gpu_id
        return None
    
    def allocate_gpu(self, session_id):
        """Allocate a GPU for a session"""
        with self.lock:
            # Check if session already has a GPU
            if session_id in gpu_sessions:
                session = gpu_sessions[session_id]
                # Check if process is still running
                if session['process'].poll() is None:
                    return session
                else:
                    # Clean up dead session
                    del gpu_sessions[session_id]
            
            # Find available GPU
            gpu_id = self.find_available_gpu()
            if gpu_id is None:
                return None
            
            # Allocate port
            port = base_port + gpu_id
            
            # Start AI server on this GPU
            try:
                env = os.environ.copy()
                env['CUDA_VISIBLE_DEVICES'] = str(gpu_id)
                env['GITHUB_TOKEN'] = os.environ.get('GITHUB_TOKEN', '')
                
                process = subprocess.Popen([
                    'python3', 'ai_server/qwen3_4b_server.py', '--port', str(port)
                ], env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                
                # Wait for AI server to fully load and start listening
                logger.info(f"🔄 Starting AI server on GPU {gpu_id}, port {port}...")
                
                # Wait up to 30 seconds for server to start
                for attempt in range(30):
                    time.sleep(1)
                    
                    # Check if process is still running
                    if process.poll() is not None:
                        logger.error(f"❌ AI server process died during startup on GPU {gpu_id}")
                        return None
                    
                    # Check if port is listening
                    try:
                        import socket
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(1)
                        result = sock.connect_ex(('localhost', port))
                        sock.close()
                        
                        if result == 0:
                            # Port is open, server is ready
                            session = {
                                'session_id': session_id,
                                'gpu_id': gpu_id,
                                'process': process,
                                'port': port,
                                'started_at': time.time()
                            }
                            gpu_sessions[session_id] = session
                            logger.info(f"✅ Allocated GPU {gpu_id} on port {port} for session {session_id} (took {attempt+1}s)")
                            return session
                    except Exception as e:
                        pass  # Port not ready yet, continue waiting
                
                # Timeout - kill the process and return None
                logger.error(f"❌ Timeout waiting for AI server on GPU {gpu_id} port {port}")
                try:
                    process.terminate()
                    process.wait(timeout=5)
                except:
                    process.kill()
                return None
                    
            except Exception as e:
                logger.error(f"Error starting AI server on GPU {gpu_id}: {e}")
                return None
    
    def release_gpu(self, session_id):
        """Release GPU for a session"""
        with self.lock:
            if session_id in gpu_sessions:
                session = gpu_sessions[session_id]
                try:
                    # Terminate the process
                    session['process'].terminate()
                    session['process'].wait(timeout=5)
                except subprocess.TimeoutExpired:
                    session['process'].kill()
                except Exception as e:
                    logger.error(f"Error terminating process for session {session_id}: {e}")
                
                gpu_id = session['gpu_id']
                del gpu_sessions[session_id]
                logger.info(f"🔄 Released GPU {gpu_id} for session {session_id}")
                return True
            return False
    
    def cleanup_dead_sessions(self):
        """Clean up sessions with dead processes"""
        with self.lock:
            dead_sessions = []
            for session_id, session in gpu_sessions.items():
                if session['process'].poll() is not None:
                    dead_sessions.append(session_id)
            
            for session_id in dead_sessions:
                logger.warning(f"Cleaning up dead session {session_id}")
                gpu_id = gpu_sessions[session_id]['gpu_id']
                del gpu_sessions[session_id]
                logger.info(f"🧹 Cleaned up GPU {gpu_id} from dead session {session_id}")

# Global GPU manager
gpu_manager = GPUManager()

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'active_sessions': len(gpu_sessions)})

@app.route('/allocate', methods=['POST'])
def allocate_gpu():
    """Allocate a GPU for a new session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id') or str(uuid.uuid4())
        
        session = gpu_manager.allocate_gpu(session_id)
        if session:
            return jsonify({
                'success': True,
                'session_id': session['session_id'],
                'gpu_id': session['gpu_id'],
                'port': session['port'],
                'endpoint': 'https://serum-solid-woods-saying.trycloudflare.com'
            })
        else:
            return jsonify({
                'success': False,
                'error': '모든 GPU가 사용 중입니다. 잠시 후 다시 시도해주세요.'
            }), 503
    except Exception as e:
        logger.error(f"Error in allocate_gpu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/release', methods=['POST'])
def release_gpu():
    """Release a GPU session"""
    try:
        data = request.get_json() or {}
        session_id = data.get('session_id')
        
        if not session_id:
            return jsonify({'success': False, 'error': 'session_id required'}), 400
        
        success = gpu_manager.release_gpu(session_id)
        return jsonify({'success': success})
    except Exception as e:
        logger.error(f"Error in release_gpu: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/status', methods=['GET'])
def get_status():
    """Get current GPU allocation status"""
    gpu_manager.cleanup_dead_sessions()
    
    status = {
        'total_gpus': len(available_gpus),
        'active_sessions': len(gpu_sessions),
        'sessions': {}
    }
    
    for session_id, session in gpu_sessions.items():
        status['sessions'][session_id] = {
            'gpu_id': session['gpu_id'],
            'port': session['port'],
            'uptime': time.time() - session['started_at']
        }
    
    return jsonify(status)

@app.route('/chat', methods=['POST', 'OPTIONS'])
def proxy_chat():
    """Proxy chat requests to appropriate AI server"""
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Get session_id from headers or body
        data = request.get_json() or {}
        session_id = request.headers.get('X-Session-ID') or data.get('session_id')
        
        logger.info(f"🔍 Chat request - Session ID: {session_id}, Active sessions: {list(gpu_sessions.keys())}")
        
        if not session_id:
            logger.error("❌ No session_id provided in headers or body")
            return jsonify({'error': 'Session ID required'}), 400
        
        if session_id not in gpu_sessions:
            logger.error(f"❌ Session {session_id} not found in active sessions")
            return jsonify({'error': 'GPU session not found. Please reload the page.'}), 400
        
        session = gpu_sessions[session_id]
        port = session['port']
        
        logger.info(f"📡 Forwarding request to localhost:{port}")
        
        # Forward request to AI server
        import requests
        response = requests.post(
            f'http://localhost:{port}/chat',
            json=data,
            timeout=60  # Increased timeout to 60 seconds
        )
        
        if response.status_code == 200:
            logger.info(f"✅ Successfully got response from port {port}")
            return response.json()
        else:
            logger.error(f"❌ AI server returned status {response.status_code}")
            return jsonify({'error': f'AI server error: {response.status_code}'}), 502
            
    except requests.exceptions.ConnectionError as e:
        logger.error(f"❌ Connection error to AI server: {e}")
        return jsonify({'error': 'AI server connection failed. Please try again.'}), 503
    except Exception as e:
        logger.error(f"❌ Error in proxy_chat: {e}")
        return jsonify({'error': str(e)}), 500

def cleanup_on_exit():
    """Clean up all GPU sessions on exit"""
    logger.info("🛑 Cleaning up all GPU sessions...")
    for session_id in list(gpu_sessions.keys()):
        gpu_manager.release_gpu(session_id)

def signal_handler(sig, frame):
    cleanup_on_exit()
    exit(0)

if __name__ == '__main__':
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("🚀 Starting GPU Manager Server on port 3999")
    try:
        app.run(host='0.0.0.0', port=3999, debug=False)
    except KeyboardInterrupt:
        cleanup_on_exit()