"""
简化版的ASR-LLM-TTS应用，用于快速测试
"""

import os
import logging
from datetime import datetime
from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import dashscope
from dotenv import load_dotenv
import base64
import tempfile

# 加载环境变量
load_dotenv()

# 创建Flask应用
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'test-key')
CORS(app)

# 设置DashScope API密钥
dashscope.api_key = os.getenv('DASHSCOPE_API_KEY')

# 简单的日志配置
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 内存中存储聊天历史（简化版）
chat_history = []

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
        voice = data.get('voice', 'longxiaochun_v2')
        
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
    
    # 运行应用
    app.run(
        host=os.getenv('HOST', '127.0.0.1'),
        port=int(os.getenv('PORT', 5000)),
        debug=os.getenv('DEBUG', 'True').lower() == 'true'
    )
