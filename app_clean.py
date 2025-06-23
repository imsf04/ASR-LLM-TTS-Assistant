#!/usr/bin/env python3
"""
ASR-LLM-TTS智能助手应用 - 清理版本
"""
import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, Namespace, emit
from werkzeug.utils import secure_filename
import dashscope
import numpy as np
import json
import traceback
from dotenv import load_dotenv
import tempfile
import base64
import time

# Import our custom modules
from backend.rag_system import RAGSystem
from backend.asr_service import ASRService
from backend.tts_service import TTSService
from backend.knowledge_base import KnowledgeBaseManager
from backend.database import DatabaseManager
from backend.vad_processor import VADProcessor
from utils.logger import setup_logger
from utils.security import validate_file
from config import Config

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)
config_instance = Config()
app.config.from_object(config_instance)
CORS(app)

# Initialize SocketIO with threading mode
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Setup logging
logger = setup_logger('app', config_instance.LOG_LEVEL)

# Global services
rag_system = None
asr_service = None
tts_service = None
kb_manager = None
db_manager = None

def initialize_services():
    """Initialize all AI services"""
    global rag_system, asr_service, tts_service, kb_manager, db_manager
    
    try:
        logger.info(f"正在初始化 DashScope API Key: {config_instance.DASHSCOPE_API_KEY[:8]}...")
        dashscope.api_key = config_instance.DASHSCOPE_API_KEY
        
        # Initialize database manager (with fallback)
        try:
            db_manager = DatabaseManager(config_instance)
            logger.info("数据库管理器初始化成功")
        except Exception as db_error:
            logger.warning(f"数据库初始化失败，将使用简化模式: {str(db_error)}")
            db_manager = None
        
        # Initialize AI services
        rag_system = RAGSystem(config_instance)
        asr_service = ASRService(config_instance)
        tts_service = TTSService(config_instance)
        kb_manager = KnowledgeBaseManager(config_instance)
        
        logger.info("All services initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize services: {str(e)}")
        logger.error(traceback.format_exc())
        return False

@app.route('/health')
def health_check():
    """Health check endpoint"""
    if db_manager:
        db_health = db_manager.health_check()
    else:
        db_health = {"postgres": False, "redis": False}
    
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
        'databases': db_health,
        'mode': 'full' if db_manager else 'simplified'
    })

@app.route('/')
def index():
    """Main application page"""
    return render_template('index.html')

@app.route('/asr', methods=['POST'])
def audio_to_text():
    """Convert audio to text using ASR"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有上传音频文件'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': '未选择音频文件'}), 400
        
        if not validate_file(audio_file, config_instance.ALLOWED_AUDIO_EXTENSIONS):
            return jsonify({'error': '不支持的音频格式'}), 400
        
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(config_instance.UPLOAD_FOLDER, filename)
        audio_file.save(temp_path)
        
        try:
            text = asr_service.transcribe(temp_path)
            logger.info(f"ASR transcription completed: {text[:100]}...")
            
            return jsonify({
                'success': True,
                'text': text,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        logger.error(f"ASR error: {str(e)}")
        return jsonify({'error': f'语音识别失败: {str(e)}'}), 500

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
        
        voice = data.get('voice', 'longwan_v2')
        audio_data = tts_service.synthesize(text, voice)
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        logger.info(f"TTS synthesis completed for text: {text[:50]}...")
        
        return jsonify({
            'success': True,
            'audio': audio_base64,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return jsonify({'error': f'语音合成失败: {str(e)}'}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Chat with LLM using RAG"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': '缺少消息参数'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        response = rag_system.chat(user_message)
        logger.info(f"Chat completed for message: {user_message[:50]}...")
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': f'对话生成失败: {str(e)}'}), 500

# WebSocket Voice Chat Namespace
class VoiceChatNamespace(Namespace):
    """WebSocket namespace for real-time voice chat"""
    
    def __init__(self, namespace=None):
        super().__init__(namespace)
        self.AUDIO_RATE = 16000
        self.vad_processor = VADProcessor(
            sample_rate=self.AUDIO_RATE,
            vad_mode=3,
            frame_duration_ms=20,
            speech_threshold=0.3,
            silence_threshold=1.0
        )
        self.vad_processor.set_callbacks(
            on_speech_start=self._on_speech_start,
            on_speech_end=self._on_speech_end,
            on_voice_activity=self._on_voice_activity
        )
        self.audio_buffer = bytearray()
        self.collected_audio = bytearray()
        self.is_speaking = False
        self.is_paused = False
    
    def on_connect(self):
        logger.info(f"客户端连接: {request.sid}")
        self.vad_processor.reset()
        self.audio_buffer = bytearray()
        self.collected_audio = bytearray()
        self.is_speaking = False
        self.is_paused = False
        emit('server_message', {'message': '成功连接到服务器，实时语音对话已就绪!'})

    def on_disconnect(self):
        logger.info(f"客户端断开连接: {request.sid}")
        self.vad_processor.reset()

    def _on_speech_start(self):
        logger.info("检测到语音开始")
        self.is_speaking = True
        self.collected_audio = bytearray()
        emit('voice_status', {'status': 'speaking', 'message': '正在说话...'})

    def _on_speech_end(self, audio_data: bytes):
        logger.info(f"检测到语音结束，音频长度: {len(audio_data)} bytes")
        self.is_speaking = False
        emit('voice_status', {'status': 'processing', 'message': '正在处理语音...'})
        self.handle_transcription(audio_data)
    
    def _on_voice_activity(self, is_active: bool):
        pass
    
    def on_stream(self, data):
        """处理音频流"""
        try:
            if self.is_paused:
                return
            
            if isinstance(data, str):
                audio_bytes = base64.b64decode(data)
            else:
                audio_bytes = bytes(data)
            
            self.audio_buffer.extend(audio_bytes)
            
            chunk_size = int(self.AUDIO_RATE * 0.02) * 2  # 20ms
            while len(self.audio_buffer) >= chunk_size:
                chunk_data = bytes(self.audio_buffer[:chunk_size])
                self.audio_buffer = self.audio_buffer[chunk_size:]
                self.vad_processor.process_audio_chunk(chunk_data)
                self.collected_audio.extend(chunk_data)
                
        except Exception as e:
            logger.error(f"音频流处理错误: {e}")
            emit('server_error', {'message': f'音频处理错误: {str(e)}'})

    def on_pause_voice(self):
        """暂停语音对话"""
        self.is_paused = True
        if len(self.collected_audio) > 0:
            self.handle_transcription(bytes(self.collected_audio))
            self.collected_audio = bytearray()
        self.vad_processor.reset()
        emit('voice_status', {'status': 'paused', 'message': '语音对话已暂停'})

    def on_resume_voice(self):
        """恢复语音对话"""
        self.is_paused = False
        self.vad_processor.reset()
        self.audio_buffer = bytearray()
        self.collected_audio = bytearray()
        emit('voice_status', {'status': 'idle', 'message': '语音对话已恢复'})

    def handle_transcription(self, audio_data):
        """处理转录"""
        try:
            import wave
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_path = tmp_file.name
                
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(16000)
                    wav_file.writeframes(audio_data)
            
            transcription = asr_service.transcribe(temp_path)
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if transcription:
                logger.info(f"ASR 结果: {transcription}")
                emit('asr_result', {'text': transcription})
                self.handle_chat(transcription)
            else:
                emit('server_error', {'message': '语音识别失败'})

        except Exception as e:
            logger.error(f"转录处理失败: {e}")
            emit('server_error', {'message': f'语音识别内部错误: {e}'})

    def handle_chat(self, text):
        """处理聊天并返回TTS"""
        try:
            assistant_response = rag_system.chat(text)
            logger.info(f"LLM回复: {assistant_response}")
            emit('llm_response', {'text': assistant_response})
            
            audio_data = tts_service.synthesize(assistant_response, "longwan_v2")
            if audio_data:
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                emit('tts_speech', {'audio': audio_base64})
                emit('voice_status', {'status': 'idle', 'message': '等待下次语音输入...'})
            else:
                emit('server_error', {'message': 'TTS合成失败'})
                
        except Exception as e:
            logger.error(f"聊天处理失败: {e}")
            emit('server_error', {'message': f'AI对话内部错误: {e}'})

# Register WebSocket namespace
socketio.on_namespace(VoiceChatNamespace('/voice'))

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '页面未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': '服务器内部错误'}), 500

if __name__ == '__main__':
    try:
        # Create directories
        os.makedirs(config_instance.UPLOAD_FOLDER, exist_ok=True)
        os.makedirs(config_instance.KNOWLEDGE_BASE_FOLDER, exist_ok=True)
        os.makedirs(config_instance.LOG_FOLDER, exist_ok=True)
        
        # Initialize services
        if not initialize_services():
            logger.error("Failed to initialize services")
            exit(1)
        
        # Startup info
        logger.info("启动Flask-SocketIO服务器（清理版）...")
        print("=" * 60)
        print("ASR-LLM-TTS智能助手正在启动...")
        print("功能: 语音识别 + AI对话 + 语音合成 + 实时语音对话")
        
        if db_manager:
            print("模式: 完整模式（支持数据库）")
        else:
            print("模式: 简化模式（内存模式）")
            
        print(f"访问地址: http://{config_instance.HOST}:{config_instance.PORT}")
        print("=" * 60)
        
        # Start server
        socketio.run(app,
            host=config_instance.HOST,
            port=config_instance.PORT,
            debug=config_instance.DEBUG,
            allow_unsafe_werkzeug=True
        )
        
    except Exception as e:
        print(f"启动失败: {e}")
        traceback.print_exc()
