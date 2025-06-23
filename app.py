import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_template
from flask_cors import CORS
from werkzeug.utils import secure_filename
import dashscope
from dashscope import Generation, TextEmbedding
import numpy as np
from typing import List, Dict, Any, Optional
import json
import traceback
from dotenv import load_dotenv
import tempfile
import base64

# Import our custom modules
from backend.rag_system import RAGSystem
from backend.asr_service import ASRService
from backend.tts_service import TTSService
from backend.knowledge_base import KnowledgeBaseManager
from backend.database import DatabaseManager
from utils.logger import setup_logger
from utils.security import validate_file
from config import Config

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
app.config.from_object(Config)
CORS(app)

# Setup logging
logger = setup_logger('app', app.config['LOG_LEVEL'])

# Global variables for services
rag_system = None
asr_service = None
tts_service = None
kb_manager = None
db_manager = None

def initialize_services():
    """Initialize all AI services"""
    global rag_system, asr_service, tts_service, kb_manager, db_manager
    
    try:
        # Initialize DashScope API
        dashscope.api_key = app.config['DASHSCOPE_API_KEY']
        
        # Initialize database manager first
        db_manager = DatabaseManager(app.config)
        
        # Initialize services
        rag_system = RAGSystem(app.config)
        asr_service = ASRService(app.config)
        tts_service = TTSService(app.config)
        kb_manager = KnowledgeBaseManager(app.config)
        
        logger.info("All services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@app.before_first_request
def before_first_request():
    """Initialize services before handling first request"""
    if not initialize_services():
        logger.error("Failed to initialize services")

# Health check endpoint
@app.route('/health')
def health_check():
    """Health check endpoint"""
    db_health = db_manager.health_check() if db_manager else {"postgres": False, "redis": False}
    
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'rag_system': rag_system is not None,
            'asr_service': asr_service is not None,
            'tts_service': tts_service is not None,
            'kb_manager': kb_manager is not None,
            'db_manager': db_manager is not None
        },
        'databases': db_health
    })

# Main page
@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

# ASR endpoint
@app.route('/asr', methods=['POST'])
def audio_to_text():
    """Convert audio to text using ASR"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有上传音频文件'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': '未选择音频文件'}), 400
        
        # Validate file
        if not validate_file(audio_file, app.config['ALLOWED_AUDIO_EXTENSIONS']):
            return jsonify({'error': '不支持的音频格式'}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        audio_file.save(temp_path)
        
        try:
            # Convert audio to text
            text = asr_service.transcribe(temp_path)
            
            logger.info(f"ASR transcription completed: {text[:100]}...")
            
            return jsonify({
                'success': True,
                'text': text,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        logger.error(f"ASR error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'语音识别失败: {str(e)}'}), 500

# TTS endpoint
@app.route('/tts', methods=['POST'])
def text_to_speech():
    """Convert text to speech using TTS"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': '缺少文本参数'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': '文本不能为空'}), 400
        
        voice = data.get('voice', 'xiaoyun')  # Default voice
        
        # Generate audio
        audio_data = tts_service.synthesize(text, voice)
        
        # Convert to base64 for JSON response
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        logger.info(f"TTS synthesis completed for text: {text[:50]}...")
        
        return jsonify({
            'success': True,
            'audio': audio_base64,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'语音合成失败: {str(e)}'}), 500

# Chat endpoint (streaming)
@app.route('/chat_stream', methods=['POST'])
def chat_stream():
    """Streaming chat with LLM using RAG"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': '缺少消息参数'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        def generate():
            try:
                # Get response from RAG system
                for chunk in rag_system.chat_stream(user_message):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
                # Send completion signal
                yield f"data: {json.dumps({'finished': True})}\n\n"
                
            except Exception as e:
                logger.error(f"Chat streaming error: {str(e)}")
                error_msg = {'error': f'对话生成失败: {str(e)}'}
                yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
        
        return Response(generate(), mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"Chat endpoint error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'对话请求失败: {str(e)}'}), 500

# Non-streaming chat endpoint
@app.route('/chat', methods=['POST'])
def chat():
    """Non-streaming chat with LLM using RAG"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': '缺少消息参数'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # Get response from RAG system
        response = rag_system.chat(user_message)
        
        logger.info(f"Chat completed for message: {user_message[:50]}...")
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'对话生成失败: {str(e)}'}), 500

# Knowledge base management endpoints
@app.route('/upload_document', methods=['POST'])
def upload_document():
    """Upload document to knowledge base"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        # Validate file
        if not validate_file(file, app.config['ALLOWED_DOCUMENT_EXTENSIONS']):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['KNOWLEDGE_BASE_FOLDER'], filename)
        file.save(file_path)
        
        # Process document and add to knowledge base
        result = kb_manager.add_document(file_path)
        
        logger.info(f"Document uploaded and processed: {filename}")
        
        return jsonify({
            'success': True,
            'message': '文档上传成功',
            'filename': filename,
            'chunks_added': result.get('chunks_added', 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Document upload error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'文档上传失败: {str(e)}'}), 500

@app.route('/list_documents', methods=['GET'])
def list_documents():
    """List all documents in knowledge base"""
    try:
        documents = kb_manager.list_documents()
        
        return jsonify({
            'success': True,
            'documents': documents,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"List documents error: {str(e)}")
        return jsonify({'error': f'获取文档列表失败: {str(e)}'}), 500

@app.route('/delete_document', methods=['POST'])
def delete_document():
    """Delete document from knowledge base"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'error': '缺少文件名参数'}), 400
        
        filename = data['filename']
        result = kb_manager.delete_document(filename)
        
        logger.info(f"Document deleted: {filename}")
        
        return jsonify({
            'success': True,
            'message': '文档删除成功',
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Delete document error: {str(e)}")
        return jsonify({'error': f'文档删除失败: {str(e)}'}), 500

@app.route('/clear_history', methods=['POST'])
def clear_chat_history():
    """Clear chat history"""
    try:
        rag_system.clear_history()
        
        return jsonify({
            'success': True,
            'message': '对话历史已清空',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Clear history error: {str(e)}")
        return jsonify({'error': f'清空历史失败: {str(e)}'}), 500

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '页面未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': '文件太大'}), 413

if __name__ == '__main__':
    # Ensure upload directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(app.config['KNOWLEDGE_BASE_FOLDER'], exist_ok=True)
    os.makedirs(app.config['LOG_FOLDER'], exist_ok=True)
    
    # Initialize services
    if not initialize_services():
        logger.error("Failed to initialize services, exiting...")
        exit(1)
    
    # Run the app
    app.run(
        host=app.config['HOST'],
        port=app.config['PORT'],
        debug=app.config['DEBUG']
    )
