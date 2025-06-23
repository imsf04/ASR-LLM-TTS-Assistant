"""
简化版的ASR-LLM-TTS应用，用于快速测试
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, Namespace, emit
import dashscope
from dotenv import load_dotenv
import base64
import tempfile
from collections import deque
import time
import numpy as np
import wave

# 导入VAD处理器
from backend.vad_processor import VADProcessor

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'test-key')
CORS(app)
# 使用gevent模式
socketio = SocketIO(app, async_mode='gevent', cors_allowed_origins="*")


# 设置DashScope API密钥
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

# 简单的日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 内存中存储聊天历史（简化版）
chat_history = []

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
        self.is_paused = False  # 新增：暂停状态
        
        # 初始化VAD处理器
        self.vad_processor = VADProcessor(
            sample_rate=self.AUDIO_RATE,
            vad_mode=3,  # 最敏感模式
            frame_duration_ms=20,
            speech_threshold=0.3,  # 降低语音检测阈值
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
        self.is_paused = False  # 重置暂停状态
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
        # 可以用于实时显示语音活动状态
        pass
    
    def on_stream(self, data):
        """接收音频流并使用智能VAD处理"""
        try:
            # 检查是否暂停
            if self.is_paused:
                return  # 暂停时忽略音频数据
            
            # 转换数据格式
            if isinstance(data, (list, tuple)):
                audio_bytes = bytes(data)
            elif isinstance(data, str):
                # 如果是base64编码的字符串
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
            
            # 参考示例代码：检查是否有足够数据进行VAD检测
            step = int(self.AUDIO_RATE * 0.02)  # 20ms步长
            chunk_size = step * 2  # 每个chunk的字节数 (16位音频)
            
            # 当缓冲区有足够数据时进行处理
            while len(self.audio_buffer) >= chunk_size:
                # 取出一个chunk进行VAD检测
                chunk_data = bytes(self.audio_buffer[:chunk_size])
                self.audio_buffer = self.audio_buffer[chunk_size:]
                
                # 使用VAD处理器处理音频块
                self.vad_processor.process_audio_chunk(chunk_data)
                
                # 同时收集所有音频用于后续处理
                self.collected_audio.extend(chunk_data)
                
                # 更新活动时间
                self.last_activity_time = time.time()
                
            # 检查是否需要强制结束（防止卡住）
            current_time = time.time()
            if (current_time - self.last_activity_time) > 5.0 and len(self.collected_audio) > 0:
                logger.info("检测到长时间无活动，强制处理音频")
                if len(self.collected_audio) > 0:
                    self.handle_transcription(bytes(self.collected_audio))
                    self.collected_audio = bytearray()
                    
        except Exception as e:
            logger.error(f"音频流处理错误: {e}")
            # 重置状态
            self.vad_processor.reset()
            self.audio_buffer = bytearray()
            self.collected_audio = bytearray()
            emit('server_error', {'message': f'音频处理错误: {str(e)}'})

    def on_pause_voice(self):
        """暂停语音对话"""
        try:
            self.is_paused = True
            logger.info("语音对话已暂停")
            
            # 处理当前收集的音频（如果有）
            if len(self.collected_audio) > 0:
                self.handle_transcription(bytes(self.collected_audio))
                self.collected_audio = bytearray()
            
            # 重置VAD状态
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
            
            # 重置状态
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
            
            # 重置状态
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
            # 使用ASR服务
            from backend.asr_service import ASRService
            class Config:
                DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
                ASR_MODEL = os.getenv('ASR_MODEL', 'paraformer-realtime-v2')
            config = Config()
            asr_service = ASRService(config)

            # 将原始PCM数据转换为WAV格式，以便ASR服务正确处理
            import wave
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                temp_path = tmp_file.name
                
                # 创建WAV文件
                with wave.open(temp_path, 'wb') as wav_file:
                    wav_file.setnchannels(1)  # 单声道
                    wav_file.setsampwidth(2)  # 16位音频
                    wav_file.setframerate(16000)  # 16kHz采样率
                    wav_file.writeframes(audio_data)
            
            # 调用ASR服务（不使用format参数）
            transcription = asr_service.transcribe(temp_path)
              # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)

            if transcription:
                logger.info(f"ASR 结果: {transcription}")
                emit('asr_result', {'text': transcription})
                # 在这里可以继续调用LLM和TTS
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
            # 使用DashScope生成LLM回复
            from dashscope import Generation
            
            # 调用大语言模型
            response = Generation.call(
                model='qwen-plus',
                messages=[
                    {'role': 'system', 'content': '你是一个有用的AI助手，请用简洁友好的语言回复用户。回复内容控制在50字以内，适合语音播放。'},
                    {'role': 'user', 'content': text}
                ],
                result_format='message'
            )
            
            if response.status_code == 200:
                assistant_response = response.output.choices[0].message.content
                logger.info(f"LLM回复: {assistant_response}")
                
                # 保存到聊天历史
                chat_history.append({
                    'user': text,
                    'assistant': assistant_response,
                    'timestamp': datetime.now().isoformat()
                })
                
                # 发送LLM回复文本到前端
                emit('llm_response', {'text': assistant_response})
                
                # 生成TTS语音
                from backend.tts_service import TTSService
                class Config:
                    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
                    TTS_MODEL = os.getenv('TTS_MODEL', 'cosyvoice-v2')
                config = Config()
                tts_service = TTSService(config)
                
                # 使用助手回复生成语音
                audio_data = tts_service.synthesize(assistant_response, "longwan_v2")

                if audio_data:
                    audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    emit('tts_speech', {'audio': audio_base64})
                    logger.info("AI回复语音已发送到客户端")
                    
                    # 更新状态为空闲
                    emit('voice_status', {'status': 'idle', 'message': '等待下次语音输入...'})
                else:
                    emit('server_error', {'message': 'TTS合成失败'})
                    
            else:
                logger.error(f"LLM调用失败: {response.message}")
                emit('server_error', {'message': f'AI对话失败: {response.message}'})
                
        except Exception as e:
            logger.error(f"聊天处理失败: {e}")
            emit('server_error', {'message': f'AI对话内部错误: {e}'})


# 注册命名空间
socketio.on_namespace(VoiceChatNamespace('/voice'))


@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/health')
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'dashscope_configured': bool(os.getenv('DASHSCOPE_API_KEY'))
    })

@app.route('/chat', methods=['POST'])
def chat():
    """简化的聊天功能"""
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return jsonify({'error': '消息不能为空'}), 400
        
        # 使用DashScope生成回复
        from dashscope import Generation
        
        response = Generation.call(
            model='qwen-plus',
            messages=[
                {'role': 'system', 'content': '你是一个有用的AI助手。'},
                {'role': 'user', 'content': user_message}
            ],
            result_format='message'
        )
        
        if response.status_code == 200:
            assistant_response = response.output.choices[0].message.content
            
            # 保存到内存历史
            chat_history.append({
                'user': user_message,
                'assistant': assistant_response,
                'timestamp': datetime.now().isoformat()
            })
            
            return jsonify({
                'success': True,
                'response': assistant_response,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': f'API调用失败: {response.message}'}), 500
            
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        return jsonify({'error': f'对话失败: {str(e)}'}), 500

@app.route('/tts', methods=['POST'])
def text_to_speech():
    """简化的TTS功能"""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        voice = data.get('voice', 'longwan_v2')
        
        if not text:
            return jsonify({'error': '文本不能为空'}), 400
        
        # 使用修复的TTS服务
        from backend.tts_service import TTSService
        
        # 创建配置对象
        class Config:
            DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
            TTS_MODEL = os.getenv('TTS_MODEL', 'cosyvoice-v2')
        
        config = Config()
        tts_service = TTSService(config)
        
        # 调用TTS服务
        audio_data = tts_service.synthesize(text, voice)
        
        if audio_data:
            # 转换为base64
            audio_base64 = base64.b64encode(audio_data).decode('utf-8')
            
            return jsonify({
                'success': True,
                'audio': audio_base64,
                'timestamp': datetime.now().isoformat()
            })
        else:
            return jsonify({'error': 'TTS合成失败'}), 500
            
    except Exception as e:
        logger.error(f"TTS error: {str(e)}")
        return jsonify({'error': f'语音合成失败: {str(e)}'}), 500

@app.route('/asr', methods=['POST'])
def audio_to_text():
    """简化的ASR功能"""
    try:
        if 'audio' not in request.files:
            return jsonify({'error': '没有音频文件'}), 400
        
        audio_file = request.files['audio']
        if audio_file.filename == '':
            return jsonify({'error': '未选择文件'}), 400
        
        # 保存临时文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            audio_file.save(tmp_file.name)
            temp_path = tmp_file.name
        
        try:
            # 使用修复的ASR服务
            from backend.asr_service import ASRService
              # 创建配置对象
            class Config:
                DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
                ASR_MODEL = os.getenv('ASR_MODEL', 'paraformer-realtime-v2')  # 使用最新v2模型
            
            config = Config()
            asr_service = ASRService(config)
            
            # 调用ASR服务
            transcription = asr_service.transcribe(temp_path)
            
            return jsonify({
                'success': True,
                'transcription': transcription,
                'timestamp': datetime.now().isoformat()
            })
                
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
            
    except Exception as e:
        logger.error(f"ASR error: {str(e)}")
        return jsonify({'error': f'语音识别失败: {str(e)}'}), 500

@app.route('/clear_history', methods=['POST'])
def clear_history():
    """清空聊天历史"""
    global chat_history
    chat_history = []
    return jsonify({
        'success': True,
        'message': '聊天历史已清空'
    })

if __name__ == '__main__':
    # 确保上传目录存在
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('logs', exist_ok=True)
      # 使用socketio.run()来启动应用
    logger.info("启动Flask-SocketIO服务器...")
    print("=" * 50)
    print("服务器正在启动...")
    print("请访问: http://127.0.0.1:5001")
    print("=" * 50)
    
    # 使用5001端口避免冲突
    socketio.run(app,
        host='127.0.0.1',
        port=5001,
        debug=False,
        allow_unsafe_werkzeug=True
    )
