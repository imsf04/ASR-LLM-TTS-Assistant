import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_template
from flask_cors import CORS
from flask_socketio import SocketIO, Namespace, emit
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
# 创建配置实例并设置Flask配置
config_instance = Config()
app.config.from_object(config_instance)
CORS(app)

# Initialize SocketIO with threading mode for real-time voice chat
socketio = SocketIO(app, async_mode='threading', cors_allowed_origins="*")

# Setup logging
logger = setup_logger('app', config_instance.LOG_LEVEL)

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
        # Initialize DashScope API using config instance
        logger.info(f"正在初始化 DashScope API Key: {config_instance.DASHSCOPE_API_KEY[:8]}...")
        dashscope.api_key = config_instance.DASHSCOPE_API_KEY
        
        # Try to initialize database manager (with fallback)
        try:
            db_manager = DatabaseManager(config_instance)
            logger.info("数据库管理器初始化成功")
        except Exception as db_error:
            logger.warning(f"数据库初始化失败，将使用简化模式: {str(db_error)}")
            db_manager = None
        
        # Initialize services
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

# Initialize services at startup instead of using before_first_request
# @app.before_first_request  # This decorator is deprecated in newer Flask versions
# def before_first_request():
#     """Initialize services before handling first request"""
#     if not initialize_services():
#         logger.error("Failed to initialize services")

@app.route('/health')
def health_check():
    """Health check endpoint"""
    # Check database health if available
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
        if not validate_file(audio_file, config_instance.ALLOWED_AUDIO_EXTENSIONS):
            return jsonify({'error': '不支持的音频格式'}), 400
        
        # Save uploaded file temporarily
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(config_instance.UPLOAD_FOLDER, filename)
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
        if not validate_file(file, config_instance.ALLOWED_DOCUMENT_EXTENSIONS):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # Save uploaded file
        filename = secure_filename(file.filename)
        file_path = os.path.join(config_instance.KNOWLEDGE_BASE_FOLDER, filename)
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

# WebSocket实时语音对话命名空间
class VoiceChatNamespace(Namespace):
    """处理实时语音对话的Socket.IO命名空间"""
    def __init__(self, namespace=None):
        super().__init__(namespace)
        # 音频参数配置
        self.AUDIO_RATE = 16000
        self.CHUNK_SIZE = int(self.AUDIO_RATE * 0.1)  # 100ms块
        self.SILENCE_THRESHOLD = 1.0  # 静音阈值（秒）
        
        # 音频缓冲区
        self.audio_buffer = bytearray()
        self.collected_audio = bytearray()
        # VAD状态
        self.is_speaking = False
        self.last_activity_time = time.time()
        self.is_paused = False  # 暂停状态
        
        # 初始化VAD处理器
        self.vad_processor = VADProcessor(
            sample_rate=self.AUDIO_RATE,
            vad_mode=3,  # 最敏感模式
            frame_duration_ms=20,
            speech_threshold=0.3,
            silence_threshold=self.SILENCE_THRESHOLD
        )
        
        # 设置VAD回调
        self.vad_processor.set_callbacks(
            on_speech_start=self._on_speech_start,
            on_speech_end=self._on_speech_end,
            on_voice_activity=self._on_voice_activity
        )
    
    def on_connect(self):
        logger.info(f"客户端连接: {request.sid}")
        # 重置VAD状态
        self.vad_processor.reset()
        self.audio_buffer = bytearray()
        self.collected_audio = bytearray()
        self.is_speaking = False
        self.last_activity_time = time.time()
        self.is_paused = False
        emit('server_message', {'message': '成功连接到服务器，实时语音对话已就绪!'})

    def on_disconnect(self):
        logger.info(f"客户端断开连接: {request.sid}")
        # 清理状态
        self.vad_processor.reset()
        self.audio_buffer = bytearray()
        self.collected_audio = bytearray()

    def _on_speech_start(self):
        """语音开始回调"""
        logger.info("检测到语音开始")
        self.is_speaking = True
        self.collected_audio = bytearray()
        emit('voice_status', {'status': 'speaking', 'message': '正在说话...'})

    def _on_speech_end(self, audio_data: bytes):
        """语音结束回调"""
        logger.info(f"检测到语音结束，音频长度: {len(audio_data)} bytes")
        self.is_speaking = False
        emit('voice_status', {'status': 'processing', 'message': '正在处理语音...'})
        
        # 处理完整的语音数据
        self.handle_transcription(audio_data)
    
    def _on_voice_activity(self, is_active: bool):
        """语音活动状态回调"""
        pass
    
    def on_stream(self, data):
        """接收音频流并使用智能VAD处理"""
        try:
            # 检查是否暂停
            if self.is_paused:
                return
            
            # 转换数据格式
            if isinstance(data, (list, tuple)):
                audio_bytes = bytes(data)
            elif isinstance(data, str):
                try:
                    audio_bytes = base64.b64decode(data)
                except:
                    logger.error("无法解码base64音频数据")
                    return
            elif hasattr(data, 'tobytes'):
                audio_bytes = data.tobytes()
            else:
                audio_bytes = bytes(data)
            
            # 添加到缓冲区
            self.audio_buffer.extend(audio_bytes)
            
            # VAD处理
            step = int(self.AUDIO_RATE * 0.02)  # 20ms步长
            chunk_size = step * 2  # 每个chunk的字节数
            
            # 当缓冲区有足够数据时进行处理
            while len(self.audio_buffer) >= chunk_size:
                chunk_data = bytes(self.audio_buffer[:chunk_size])
                self.audio_buffer = self.audio_buffer[chunk_size:]
                
                # 使用VAD处理器处理音频块
                self.vad_processor.process_audio_chunk(chunk_data)
                
                # 收集所有音频
                self.collected_audio.extend(chunk_data)
                
                # 更新活动时间
                self.last_activity_time = time.time()
                
            # 检查是否需要强制结束
            current_time = time.time()
            if (current_time - self.last_activity_time) > 5.0 and len(self.collected_audio) > 0:
                logger.info("检测到长时间无活动，强制处理音频")
                if len(self.collected_audio) > 0:
                    self.handle_transcription(bytes(self.collected_audio))
                    self.collected_audio = bytearray()
                    
        except Exception as e:
            logger.error(f"音频流处理错误: {e}")
            self.vad_processor.reset()
            self.audio_buffer = bytearray()
            self.collected_audio = bytearray()
            emit('server_error', {'message': f'音频处理错误: {str(e)}'})

    def on_pause_voice(self):
        """暂停语音对话"""
        try:
            self.is_paused = True
            logger.info("语音对话已暂停")
            
            if len(self.collected_audio) > 0:
                self.handle_transcription(bytes(self.collected_audio))
                self.collected_audio = bytearray()
            
            self.vad_processor.reset()
            self.audio_buffer = bytearray()
            self.is_speaking = False
            
            emit('voice_status', {'status': 'paused', 'message': '语音对话已暂停'})
            
        except Exception as e:
            logger.error(f"暂停处理错误: {e}")
            emit('server_error', {'message': f'暂停处理错误: {str(e)}'})

    def on_resume_voice(self):
        """恢复语音对话"""
        try:
            self.is_paused = False
            logger.info("语音对话已恢复")
            
            self.vad_processor.reset()
            self.audio_buffer = bytearray()
            self.collected_audio = bytearray()
            self.is_speaking = False
            self.last_activity_time = time.time()
            
            emit('voice_status', {'status': 'idle', 'message': '语音对话已恢复，等待语音输入...'})
            
        except Exception as e:
            logger.error(f"恢复处理错误: {e}")
            emit('server_error', {'message': f'恢复处理错误: {str(e)}'})

    def on_force_stop(self):
        """强制停止音频收集并处理"""
        try:
            if len(self.collected_audio) > 0:
                logger.info("强制停止，处理已收集的音频")
                self.handle_transcription(bytes(self.collected_audio))
                self.collected_audio = bytearray()
            
            self.vad_processor.reset()
            self.audio_buffer = bytearray()
            self.is_speaking = False
            
            emit('voice_status', {'status': 'idle', 'message': '已停止录音'})
            
        except Exception as e:
            logger.error(f"强制停止处理错误: {e}")
            emit('server_error', {'message': f'停止处理错误: {str(e)}'})
    
    def handle_transcription(self, audio_data):
        """处理转录逻辑"""
        logger.info(f"处理转录，音频长度: {len(audio_data)} bytes")
        try:
            # 将原始PCM数据转换为WAV格式
            import wave
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_path = tmp_file.name
                
                # 创建WAV文件
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # 单声道
                    wav_file.setsampwidth(2)  # 16位音频
                    wav_file.setframerate(16000)  # 16kHz采样率
                    wav_file.writeframes(audio_data)
            
            # 调用ASR服务
            transcription = asr_service.transcribe(temp_path)
              
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if transcription:
                logger.info(f"ASR 结果: {transcription}")
                emit('asr_result', {'text': transcription})
                # 继续调用LLM和TTS
                self.handle_chat(transcription)
            else:
                logger.warning("ASR未能返回结果")
                emit('server_error', {'message': '语音识别失败'})

        except Exception as e:
            logger.error(f"转录处理失败: {e}")
            emit('server_error', {'message': f'语音识别内部错误: {e}'})

    def handle_chat(self, text):
        """处理聊天逻辑并返回TTS"""
        logger.info(f"用户语音输入: {text}")
        try:
            # 使用RAG系统进行对话
            assistant_response = rag_system.chat(text)
            logger.info(f"LLM回复: {assistant_response}")
            
            # 发送LLM回复文本到前端
            emit('llm_response', {'text': assistant_response})
            
            # 生成TTS语音
            audio_data = tts_service.synthesize(assistant_response, "longwan_v2")

            if audio_data:
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                emit('tts_speech', {'audio': audio_base64})
                logger.info("AI回复语音已发送到客户端")
                
                # 更新状态为空闲
                emit('voice_status', {'status': 'idle', 'message': '等待下次语音输入...'})
            else:
                emit('server_error', {'message': 'TTS合成失败'})
                
        except Exception as e:
            logger.error(f"聊天处理失败: {e}")
            emit('server_error', {'message': f'AI对话内部错误: {e}'})

# 注册WebSocket命名空间
socketio.on_namespace(VoiceChatNamespace('/voice'))

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
    os.makedirs(config_instance.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config_instance.KNOWLEDGE_BASE_FOLDER, exist_ok=True)
    os.makedirs(config_instance.LOG_FOLDER, exist_ok=True)
    
    # Initialize services
    if not initialize_services():
        logger.error("Failed to initialize services, exiting...")
        exit(1)
      # Log startup information
    logger.info("启动Flask-SocketIO服务器（完整版）...")
    print("=" * 60)
    print("完整版服务器正在启动...")
    print("功能: ASR-LLM-TTS + 实时语音对话 + 完整RAG + 知识库管理")
    
    if db_manager:
        print("模式: 完整模式（支持PostgreSQL和Redis）")
    else:
        print("模式: 简化模式（数据库不可用，使用内存存储）")
    
    print(f"请访问: http://{config_instance.HOST}:{config_instance.PORT}")
    print("=" * 60)
    
    # Use socketio.run() to support WebSocket functionality
    try:
        logger.info("正在启动SocketIO服务器...")
        socketio.run(app,
            host=config_instance.HOST,
            port=config_instance.PORT,
            debug=config_instance.DEBUG,
            allow_unsafe_werkzeug=True,
            log_output=True
        )
    except Exception as e:
        logger.error(f"启动服务器失败: {e}")
        print(f"服务器启动错误: {e}")
        traceback.print_exc()
        # 回退到标准Flask启动
        logger.info("回退到标准Flask启动模式...")
        app.run(
            host=config_instance.HOST,
            port=config_instance.PORT,
            debug=config_instance.DEBUG
        )
