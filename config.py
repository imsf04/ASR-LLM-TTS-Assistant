import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration"""
    
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-change-in-production')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # DashScope API settings
    DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
      # Model configurations
    LLM_MODEL = os.getenv('LLM_MODEL', 'qwen-plus')
    EMBEDDING_MODEL = os.getenv('EMBEDDING_MODEL', 'text-embedding-v1')
    ASR_MODEL = os.getenv('ASR_MODEL', 'paraformer-realtime-v1')
    TTS_MODEL = os.getenv('TTS_MODEL', 'cosyvoice-v2')
    
    # File upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'
    KNOWLEDGE_BASE_FOLDER = 'knowledge_base'
    LOG_FOLDER = 'logs'
    
    # Allowed file extensions
    ALLOWED_AUDIO_EXTENSIONS = {'wav', 'mp3', 'flac', 'm4a', 'ogg', 'webm'}
    ALLOWED_DOCUMENT_EXTENSIONS = {'pdf', 'txt', 'docx', 'doc', 'md'}
    
    # RAG settings
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200
    MAX_CONTEXT_LENGTH = 4000
    RETRIEVAL_K = 3
    
    # Chat settings
    MAX_CHAT_HISTORY = 20
    SYSTEM_PROMPT = """你是一个有用的AI助手，能够基于提供的上下文信息来回答问题。
请根据给定的上下文信息来回答用户的问题。如果上下文中没有相关信息，请诚实地说明你不知道答案。
回答要准确、有用且简洁。"""
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Vector database settings
    VECTOR_DB_PATH = 'vector_db'
    COLLECTION_NAME = 'knowledge_base'
    
    # CosyVoice v2 voice options
    TTS_VOICES = {
        'longxiaochun_v2': '龙小春 - 女声',
        'longxiaoxia_v2': '龙小夏 - 女声', 
        'longwan_v2': '龙万 - 男声',
        'longcheng_v2': '龙城 - 男声',
        'longhua_v2': '龙华 - 男声',
        'longshu_v2': '龙书 - 男声',
        'loongbella_v2': 'Bella - 女声'
    }
    
    # Redis settings
    REDIS_HOST = os.getenv('REDIS_HOST', 'localhost')
    REDIS_PORT = int(os.getenv('REDIS_PORT', 6379))
    REDIS_DB = int(os.getenv('REDIS_DB', 0))
    REDIS_PASSWORD = os.getenv('REDIS_PASSWORD', None)
    
    # PostgreSQL settings  
    POSTGRES_HOST = os.getenv('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = int(os.getenv('POSTGRES_PORT', 5432))
    POSTGRES_DB = os.getenv('POSTGRES_DB', 'asr_llm_tts')
    POSTGRES_USER = os.getenv('POSTGRES_USER', 'postgres')
    POSTGRES_PASSWORD = os.getenv('POSTGRES_PASSWORD', '')
    
    # Audio recording settings
    RECORDING_MAX_DURATION = 300  # 5 minutes max
    RECORDING_SAMPLE_RATE = 16000
    RECORDING_CHANNELS = 1
    
    # Session settings
    SESSION_TIMEOUT = 3600  # 1 hour
    
    @staticmethod
    def validate_config():
        """Validate required configuration"""
        if not Config.DASHSCOPE_API_KEY:
            raise ValueError("DASHSCOPE_API_KEY is required")
        
        return True
