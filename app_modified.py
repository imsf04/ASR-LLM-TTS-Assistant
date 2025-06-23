"""
修改版的ASR-LLM-TTS应用，基于app.py但去除PostgreSQL依赖
保留完整功能但使用内存存储和简化的RAG系统
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response
from flask_cors import CORS
from flask_socketio import SocketIO, Namespace, emit
from werkzeug.utils import secure_filename
import dashscope
from dashscope import Generation
import numpy as np
from typing import List, Dict, Any, Optional
import json
import traceback
from dotenv import load_dotenv
import tempfile
import base64
import time

# 导入简化的后端服务
from backend.asr_service import ASRService
from backend.tts_service import TTSService
from backend.vad_processor import VADProcessor
from config import Config

# 简化的日志和安全函数
def setup_logger(name: str, level: str = 'INFO'):
    """简化的日志设置"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(name)

def validate_file(file, allowed_extensions):
    """简化的文件验证"""
    if not file or not file.filename:
        return False
    
    if '.' not in file.filename:
        return False
    
    extension = file.filename.rsplit('.', 1)[1].lower()
    return extension in allowed_extensions

# 加载环境变量
load_dotenv()

# 初始化Flask应用
app = Flask(__name__)
# 创建配置实例
config_instance = Config()
# 设置Flask配置
app.config['SECRET_KEY'] = config_instance.SECRET_KEY
app.config['MAX_CONTENT_LENGTH'] = config_instance.MAX_CONTENT_LENGTH
app.config['UPLOAD_FOLDER'] = config_instance.UPLOAD_FOLDER
app.config['KNOWLEDGE_BASE_FOLDER'] = config_instance.KNOWLEDGE_BASE_FOLDER
app.config['LOG_FOLDER'] = config_instance.LOG_FOLDER
app.config['ALLOWED_AUDIO_EXTENSIONS'] = config_instance.ALLOWED_AUDIO_EXTENSIONS
app.config['ALLOWED_DOCUMENT_EXTENSIONS'] = config_instance.ALLOWED_DOCUMENT_EXTENSIONS
CORS(app)

# 使用gevent模式的SocketIO
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")

# 设置日志
logger = setup_logger('app', config_instance.LOG_LEVEL)

# 全局变量 - 使用内存存储替代数据库
asr_service = None
tts_service = None
chat_history = []  # 内存中的聊天历史
documents_metadata = []  # 内存中的文档元数据

# 简化的RAG系统 - 不依赖PostgreSQL
class SimpleRAGSystem:
    """简化的RAG系统，使用内存存储"""
    
    def __init__(self, config):
        self.config = config
        self.chat_history = []
        self.logger = logging.getLogger(__name__)
        # 直接从环境变量初始化DashScope
        dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
        
    def chat_stream(self, user_message: str):
        """流式聊天响应"""
        try:
            # 构建简化的上下文
            context = self._build_simple_context(user_message)
            
            # 调用DashScope Generation API - 流式
            response = Generation.call(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.config.SYSTEM_PROMPT},
                    {"role": "user", "content": context}
                ],
                result_format='message',
                stream=True
            )
            
            full_response = ""
            for chunk in response:
                if chunk.status_code == 200:
                    if hasattr(chunk.output, 'choices') and chunk.output.choices:
                        delta = chunk.output.choices[0].message.content
                        if delta:
                            full_response += delta
                            yield {"content": delta, "finished": False}
                else:
                    yield {"error": f"API调用失败: {chunk.message}", "finished": True}
                    return
            
            # 保存到历史
            self.chat_history.append({
                "user": user_message,
                "assistant": full_response,
                "timestamp": datetime.now().isoformat()
            })
            
            yield {"finished": True}
            
        except Exception as e:
            self.logger.error(f"Chat streaming error: {str(e)}")
            yield {"error": f"对话生成失败: {str(e)}", "finished": True}
    
    def chat(self, user_message: str) -> str:
        """非流式聊天响应"""
        try:
            context = self._build_simple_context(user_message)
            
            response = Generation.call(
                model=self.config.LLM_MODEL,
                messages=[
                    {"role": "system", "content": self.config.SYSTEM_PROMPT},
                    {"role": "user", "content": context}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                assistant_response = response.output.choices[0].message.content
                
                # 保存到历史
                self.chat_history.append({
                    "user": user_message,
                    "assistant": assistant_response,
                    "timestamp": datetime.now().isoformat()
                })
                
                return assistant_response
            else:
                raise Exception(f"API调用失败: {response.message}")
                
        except Exception as e:
            self.logger.error(f"Chat error: {str(e)}")
            raise e
    
    def _build_simple_context(self, user_message: str) -> str:
        """构建简化的上下文"""
        context_parts = []
        
        # 添加聊天历史
        if self.chat_history:
            context_parts.append("对话历史：")
            for msg in self.chat_history[-5:]:  # 最近5条消息
                context_parts.append(f"用户: {msg['user']}")
                context_parts.append(f"助手: {msg['assistant']}")
            context_parts.append("")
        
        # 添加当前问题
        context_parts.append(f"当前问题: {user_message}")
        
        return "\n".join(context_parts)
    
    def clear_history(self):
        """清空历史"""
        self.chat_history = []

# 简化的知识库管理器
class SimpleKnowledgeBaseManager:
    """简化的知识库管理器，使用内存存储"""
    
    def __init__(self, config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
    def add_document(self, file_path: str) -> Dict[str, Any]:
        """添加文档到知识库"""
        try:
            filename = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            
            # 简单的文档处理 - 只读取文本
            content = ""
            if filename.endswith('.txt'):
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            # 保存元数据到内存
            document_info = {
                "filename": filename,
                "file_path": file_path,
                "file_size": file_size,
                "upload_time": datetime.now().isoformat(),
                "content_preview": content[:200] if content else "无法预览此文件类型"
            }
            
            documents_metadata.append(document_info)
            
            return {"chunks_added": 1, "filename": filename}
            
        except Exception as e:
            self.logger.error(f"Document processing error: {str(e)}")
            raise e
    
    def list_documents(self) -> List[Dict[str, Any]]:
        """列出所有文档"""
        return documents_metadata
    
    def delete_document(self, filename: str) -> bool:
        """删除文档"""
        global documents_metadata
        original_count = len(documents_metadata)
        documents_metadata = [doc for doc in documents_metadata if doc['filename'] != filename]
        return len(documents_metadata) < original_count

# 实时语音对话命名空间（从app_simple.py复制）
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
            # 使用简化的RAG系统
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


def initialize_services():
    """初始化所有AI服务"""
    global rag_system, asr_service, tts_service, kb_manager
    
    try:
        # 创建配置对象实例
        config = Config()
        
        # 直接从环境变量初始化DashScope API
        dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')
        
        # 初始化简化的服务
        rag_system = SimpleRAGSystem(config)
        asr_service = ASRService(config)
        tts_service = TTSService(config)
        kb_manager = SimpleKnowledgeBaseManager(config)
        
        logger.info("所有服务初始化成功")
        return True
        
    except Exception as e:
        logger.error(f"服务初始化失败: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# 注册Socket.IO命名空间
socketio.on_namespace(VoiceChatNamespace('/voice'))

# 健康检查端点
@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'services': {
            'rag_system': rag_system is not None,
            'asr_service': asr_service is not None,
            'tts_service': tts_service is not None,
            'kb_manager': kb_manager is not None
        },
        'databases': {
            'postgres': False,  # 已禁用
            'redis': False      # 已禁用
        },
        'mode': 'simplified'  # 标识这是简化模式
    })

# 主页
@app.route('/')
def index():
    """主应用页面"""
    return render_template('index.html')

# ASR端点
@app.route('/asr', methods=['POST'])
def audio_to_text():
    """使用ASR将音频转换为文本"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有上传音频文件'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': '未选择音频文件'}), 400
          # 验证文件
        if not validate_file(audio_file, config_instance.ALLOWED_AUDIO_EXTENSIONS):
            return jsonify({'error': '不支持的音频格式'}), 400
        
        # 保存上传的文件到临时位置
        filename = secure_filename(audio_file.filename)
        temp_path = os.path.join(config_instance.UPLOAD_FOLDER, filename)
        audio_file.save(temp_path)
        
        try:
            # 转换音频为文本
            text = asr_service.transcribe(temp_path)
            
            logger.info(f"ASR转录完成: {text[:100]}...")
            
            return jsonify({
                'success': True,
                'text': text,
                'timestamp': datetime.now().isoformat()
            })
            
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
        
    except Exception as e:
        logger.error(f"ASR错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'语音识别失败: {str(e)}'}), 500

# TTS端点
@app.route('/tts', methods=['POST'])
def text_to_speech():
    """使用TTS将文本转换为语音"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': '缺少文本参数'}), 400
        
        text = data['text'].strip()
        if not text:
            return jsonify({'error': '文本不能为空'}), 400
        
        voice = data.get('voice', 'longwan_v2')  # 默认语音
        
        # 生成音频
        audio_data = tts_service.synthesize(text, voice)
        
        # 转换为base64以便JSON响应
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        logger.info(f"TTS合成完成，文本: {text[:50]}...")
        
        return jsonify({
            'success': True,
            'audio': audio_base64,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"TTS错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'语音合成失败: {str(e)}'}), 500

# 聊天端点（流式）
@app.route('/chat_stream', methods=['POST'])
def chat_stream():
    """使用RAG的流式LLM聊天"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': '缺少消息参数'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        def generate():
            try:
                # 从RAG系统获取响应
                for chunk in rag_system.chat_stream(user_message):
                    yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"
                
                # 发送完成信号
                yield f"data: {json.dumps({'finished': True})}\n\n"
                
            except Exception as e:
                logger.error(f"聊天流式错误: {str(e)}")
                error_msg = {'error': f'对话生成失败: {str(e)}'}
                yield f"data: {json.dumps(error_msg, ensure_ascii=False)}\n\n"
        
        return Response(generate(), mimetype='text/plain')
        
    except Exception as e:
        logger.error(f"聊天端点错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'对话请求失败: {str(e)}'}), 500

# 非流式聊天端点
@app.route('/chat', methods=['POST'])
def chat():
    """使用RAG的非流式LLM聊天"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': '缺少消息参数'}), 400
        
        user_message = data['message'].strip()
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 从RAG系统获取响应
        response = rag_system.chat(user_message)
        
        logger.info(f"聊天完成，消息: {user_message[:50]}...")
        
        return jsonify({
            'success': True,
            'response': response,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"聊天错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'对话生成失败: {str(e)}'}), 500

# 知识库管理端点
@app.route('/upload_document', methods=['POST'])
def upload_document():
    """上传文档到知识库"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '没有上传文件'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
          # 验证文件
        if not validate_file(file, config_instance.ALLOWED_DOCUMENT_EXTENSIONS):
            return jsonify({'error': '不支持的文件格式'}), 400
        
        # 保存上传的文件
        filename = secure_filename(file.filename)
        file_path = os.path.join(config_instance.KNOWLEDGE_BASE_FOLDER, filename)
        file.save(file_path)
        
        # 处理文档并添加到知识库
        result = kb_manager.add_document(file_path)
        
        logger.info(f"文档上传并处理: {filename}")
        
        return jsonify({
            'success': True,
            'message': '文档上传成功',
            'filename': filename,
            'chunks_added': result.get('chunks_added', 0),
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"文档上传错误: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'文档上传失败: {str(e)}'}), 500

@app.route('/list_documents', methods=['GET'])
def list_documents():
    """列出知识库中的所有文档"""
    try:
        documents = kb_manager.list_documents()
        
        return jsonify({
            'success': True,
            'documents': documents,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"列出文档错误: {str(e)}")
        return jsonify({'error': f'获取文档列表失败: {str(e)}'}), 500

@app.route('/delete_document', methods=['POST'])
def delete_document():
    """从知识库删除文档"""
    try:
        data = request.get_json()
        if not data or 'filename' not in data:
            return jsonify({'error': '缺少文件名参数'}), 400
        
        filename = data['filename']
        result = kb_manager.delete_document(filename)
        
        logger.info(f"文档已删除: {filename}")
        
        return jsonify({
            'success': True,
            'message': '文档删除成功',
            'filename': filename,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"删除文档错误: {str(e)}")
        return jsonify({'error': f'文档删除失败: {str(e)}'}), 500

@app.route('/clear_history', methods=['POST'])
def clear_chat_history():
    """清空聊天历史"""
    try:
        rag_system.clear_history()
        global chat_history
        chat_history = []
        
        return jsonify({
            'success': True,
            'message': '对话历史已清空',
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"清空历史错误: {str(e)}")
        return jsonify({'error': f'清空历史失败: {str(e)}'}), 500

# 错误处理器
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': '页面未找到'}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"内部服务器错误: {str(error)}")
    return jsonify({'error': '服务器内部错误'}), 500

@app.errorhandler(413)
def file_too_large(error):
    return jsonify({'error': '文件太大'}), 413

if __name__ == '__main__':    # 确保上传目录存在
    os.makedirs(config_instance.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(config_instance.KNOWLEDGE_BASE_FOLDER, exist_ok=True)
    os.makedirs(config_instance.LOG_FOLDER, exist_ok=True)
    
    # 初始化服务
    if not initialize_services():
        logger.error("服务初始化失败，退出...")
        exit(1)
    
    # 使用socketio.run()启动应用
    logger.info("启动Flask-SocketIO服务器（修改版）...")
    print("=" * 60)
    print("修改版服务器正在启动...")
    print("功能: ASR-LLM-TTS + 实时语音对话 + 简化RAG")
    print("模式: 简化版（无PostgreSQL依赖）")
    print("请访问: http://127.0.0.1:5002")
    print("=" * 60)
    
    # 使用5002端口避免与app_simple.py冲突
    socketio.run(app,
        host='127.0.0.1',
        port=5002,
        debug=False,
        allow_unsafe_werkzeug=True
    )
