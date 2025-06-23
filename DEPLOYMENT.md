# ASR-LLM-TTS 智能助手 - 部署指南

## 📋 项目概述

本项目是一个功能完整的**实时语音对话智能助手**，包含以下核心功能：

- 🎤 **实时语音识别** (ASR) - DashScope Paraformer
- 🧠 **智能AI对话** (LLM) - DashScope Qwen  
- 🔊 **高质量语音合成** (TTS) - DashScope CosyVoice v2
- 📚 **知识库管理** - ChromaDB向量数据库
- 🌐 **实时语音对话** - WebSocket + VAD智能断点

## 🚀 快速部署

### 方法1: 标准部署

1. **克隆项目**
```bash
git clone https://github.com/your-username/asr-llm-tts.git
cd asr-llm-tts
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境**
```bash
# 复制配置模板
cp .env.example .env

# 编辑.env文件，设置DashScope API Key
DASHSCOPE_API_KEY=sk-your-api-key-here
```

4. **启动应用**
```bash
# Windows
start_app_clean.bat

# Linux/macOS
python app_clean.py
```

### 方法2: Docker部署

1. **使用Docker Compose**
```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

## 🔧 环境要求

### 必需组件
- **Python 3.9+**
- **Redis Server** (推荐7.x)
- **DashScope API Key** (阿里云)

### 可选组件
- **PostgreSQL 15+** (推荐，用于数据持久化)
- **Docker & Docker Compose** (容器化部署)

## 📝 配置详解

### 核心配置 (.env文件)
```bash
# 必需配置
DASHSCOPE_API_KEY=sk-your-dashscope-api-key-here

# 服务器配置
HOST=0.0.0.0
PORT=5000
DEBUG=False

# Redis配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

### 高级配置
```bash
# AI模型配置
LLM_MODEL=qwen-plus                    # 大语言模型
ASR_MODEL=paraformer-realtime-v2       # 语音识别模型  
TTS_MODEL=cosyvoice-v2                 # 语音合成模型
EMBEDDING_MODEL=text-embedding-v1      # 嵌入模型

# 性能配置
MAX_CONTENT_LENGTH=16777216            # 最大文件16MB
CHUNK_SIZE=1000                        # 文档块大小
RETRIEVAL_K=3                          # 检索结果数量
```

## 🏗️ 架构说明

### 后端架构
```
Flask Application
├── WebSocket Server (SocketIO)
├── HTTP API Endpoints
├── AI Services
│   ├── ASR Service (DashScope)
│   ├── LLM Service (DashScope)
│   ├── TTS Service (DashScope)
│   └── RAG System (ChromaDB)
├── Database Layer
│   ├── PostgreSQL (结构化数据)
│   ├── Redis (缓存/会话)
│   └── ChromaDB (向量数据)
└── Utils & Security
```

### 前端架构
```
Web Frontend
├── Bootstrap 5 UI Framework
├── WebSocket Client (Socket.IO)
├── Web Audio API (录音)
├── MediaRecorder API (音频流)
└── Real-time Interaction
```

## 🔌 API文档

### HTTP端点
| 端点 | 方法 | 描述 | 参数 |
|------|------|------|------|
| `/` | GET | 主页面 | - |
| `/health` | GET | 健康检查 | - |
| `/asr` | POST | 语音识别 | audio文件 |
| `/tts` | POST | 语音合成 | text, voice |
| `/chat` | POST | AI对话 | message |
| `/upload_document` | POST | 上传文档 | file |
| `/list_documents` | GET | 文档列表 | - |

### WebSocket事件
| 事件 | 方向 | 描述 |
|------|------|------|
| `connect` | C→S | 建立连接 |
| `stream` | C→S | 音频流数据 |
| `pause_voice` | C→S | 暂停语音 |
| `voice_status` | S→C | 语音状态 |
| `asr_result` | S→C | 识别结果 |
| `llm_response` | S→C | AI回复 |
| `tts_speech` | S→C | 合成语音 |

## 🐳 Docker部署详解

### Dockerfile构建
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "app_clean.py"]
```

### docker-compose.yml
```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "5000:5000"
    environment:
      - DASHSCOPE_API_KEY=${DASHSCOPE_API_KEY}
      - REDIS_HOST=redis
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
```

## 🔍 故障排除

### 常见问题

#### 1. DashScope API错误
```bash
# 检查API Key
python -c "import os; print(os.getenv('DASHSCOPE_API_KEY'))"

# 测试API连接
python test_config.py
```

#### 2. Redis连接失败
```bash
# 检查Redis服务
redis-cli ping

# 测试Redis连接
python test_redis.py
```

#### 3. 语音识别问题
```bash
# 检查音频格式支持
ffmpeg -version

# 测试ASR服务
python -c "from backend.asr_service import ASRService; print('ASR OK')"
```

#### 4. 端口占用
```bash
# Windows
netstat -ano | findstr :5000

# Linux/macOS
lsof -i :5000
```

### 日志查看
```bash
# 应用日志
tail -f logs/app_*.log

# Docker日志
docker-compose logs -f app
```

## 🔒 安全配置

### 生产环境设置
```bash
# .env生产环境配置
DEBUG=False
SECRET_KEY=your-strong-secret-key
REDIS_PASSWORD=strong-redis-password
POSTGRES_PASSWORD=strong-db-password
```

### 网络安全
```bash
# 防火墙配置 (Ubuntu)
sudo ufw allow 5000/tcp
sudo ufw allow 6379/tcp  # Redis

# Nginx反向代理
server {
    listen 80;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 📊 性能优化

### 硬件建议
- **CPU**: 4核心以上 (AI推理)
- **内存**: 8GB以上 (向量数据库)
- **存储**: SSD推荐 (数据库性能)
- **网络**: 稳定互联网连接 (DashScope API)

### 软件优化
```python
# config.py 性能配置
CHUNK_SIZE = 1000              # 文档处理块大小
MAX_CHAT_HISTORY = 20          # 对话历史数量
SESSION_TIMEOUT = 3600         # 会话超时时间
RECORDING_MAX_DURATION = 300   # 最大录音时长
```

## 🔄 更新升级

### 代码更新
```bash
# 拉取最新代码
git pull origin main

# 更新依赖
pip install -r requirements.txt --upgrade

# 重启服务
systemctl restart asr-llm-tts  # 如果使用systemd
```

### 数据迁移
```bash
# 备份数据库
pg_dump asr_llm_tts > backup.sql

# 备份向量数据库
cp -r vector_db vector_db_backup

# 备份知识库
cp -r knowledge_base knowledge_base_backup
```

## 📞 技术支持

### 获取帮助
- **GitHub Issues**: 提交Bug报告和功能请求
- **GitHub Discussions**: 技术讨论和使用问题
- **文档Wiki**: 详细的技术文档

### 监控和告警
```bash
# 健康检查脚本
curl -f http://localhost:5000/health || exit 1

# 服务状态监控
systemctl status asr-llm-tts
```

---

## 🎉 部署完成

部署成功后，访问 http://your-server:5000 即可使用ASR-LLM-TTS智能助手！

🚀 **享受您的AI语音对话体验吧！**
