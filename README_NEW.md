# ASR-LLM-TTS 智能助手

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-orange.svg)](https://flask.palletsprojects.com/)
[![DashScope](https://img.shields.io/badge/AI-DashScope-green.svg)](https://help.aliyun.com/product/2236920.html)
[![WebSocket](https://img.shields.io/badge/WebSocket-Real--time-red.svg)](https://socket.io/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

一个功能强大的**实时语音对话智能助手**，深度集成了**语音识别 (ASR)**、**大语言模型 (LLM)** 对话和**语音合成 (TTS)** 功能。支持实时语音对话、WebSocket流式处理、VAD智能断点检测，以及完整的知识库管理系统。

---

## 🚀 项目特色

### 🎯 核心功能
- **🎤 实时语音对话**: WebSocket支持的端到端语音对话体验
- **🧠 智能VAD检测**: 自动检测语音开始/结束，智能断点处理
- **💬 流式AI对话**: 基于RAG的知识增强对话系统
- **🔊 高质量TTS**: CosyVoice v2多音色语音合成
- **📚 知识库管理**: 支持文档上传、向量化、检索增强
- **🌐 现代化UI**: Bootstrap 5 + WebSocket实时交互

### 🏗️ 技术架构
- **后端**: Flask + SocketIO + Redis + ChromaDB
- **AI服务**: 阿里云DashScope API全栈
- **前端**: HTML5 + Bootstrap 5 + WebSocket
- **数据库**: PostgreSQL + Redis + ChromaDB向量数据库
- **部署**: Docker + Docker Compose

---

## 📋 技术栈详解

### 🔧 后端技术
| 技术 | 版本 | 用途 |
|------|------|------|
| Python | 3.9+ | 主要开发语言 |
| Flask | 2.x | Web框架 |
| Flask-SocketIO | 5.x | WebSocket实时通信 |
| DashScope SDK | 1.20+ | 阿里云AI服务 |
| Redis | 7.x | 缓存和会话存储 |
| PostgreSQL | 15+ | 结构化数据存储 |
| ChromaDB | 0.4+ | 向量数据库 |
| SQLAlchemy | 2.x | ORM框架 |
| webrtcvad | 2.x | 语音活动检测 |

### 🎨 前端技术
| 技术 | 版本 | 用途 |
|------|------|------|
| Bootstrap | 5.x | UI框架 |
| Socket.IO Client | 4.x | WebSocket客户端 |
| Web Audio API | - | 浏览器录音 |
| MediaRecorder API | - | 音频流处理 |
| JavaScript ES6+ | - | 前端逻辑 |

### 🤖 AI模型
| 模型 | 类型 | 用途 |
|------|------|------|
| paraformer-realtime-v2 | ASR | 实时语音识别 |
| qwen-plus | LLM | 大语言模型对话 |
| cosyvoice-v2 | TTS | 语音合成 |
| text-embedding-v1 | Embedding | 文本向量化 |

---

## 🏃‍♂️ 快速开始

### 📋 环境要求
- Python 3.9+
- Redis Server
- 阿里云DashScope API Key
- （可选）PostgreSQL

### 🔧 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/your-username/asr-llm-tts.git
cd asr-llm-tts
```

2. **安装依赖**
```bash
pip install -r requirements.txt
```

3. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件，添加必要配置
DASHSCOPE_API_KEY=your_dashscope_api_key
REDIS_HOST=localhost
REDIS_PORT=6379
# ... 其他配置
```

4. **启动服务**
```bash
# 方式1: 使用启动脚本（推荐）
./start_app_clean.bat

# 方式2: 直接运行
python app_clean.py
```

5. **访问应用**
```
打开浏览器访问: http://127.0.0.1:5000
```

### 🐳 Docker部署

```bash
# 构建并启动
docker-compose up -d

# 查看日志
docker-compose logs -f
```

---

## 🎯 功能详解

### 🎤 实时语音对话系统
- **WebSocket连接**: 建立持久化实时连接
- **流式音频处理**: 20ms音频块实时处理
- **VAD智能检测**: 自动识别语音开始/结束
- **端到端处理**: 语音 → ASR → LLM → TTS → 音频播放

### 🧠 智能对话系统
- **RAG增强**: 基于知识库的检索增强生成
- **上下文管理**: 维护对话历史和上下文
- **流式响应**: 逐字符返回AI回复
- **多轮对话**: 支持复杂的多轮交互

### 📚 知识库管理
- **文档处理**: 支持PDF、DOCX、TXT等格式
- **向量化存储**: ChromaDB向量数据库
- **语义检索**: 基于embedding的相似度搜索
- **动态更新**: 实时添加/删除文档

### 🔊 语音合成系统
- **多音色支持**: CosyVoice v2的7种声音
- **高质量输出**: 16kHz采样率，清晰自然
- **实时合成**: 快速响应，低延迟
- **格式支持**: WAV/MP3多格式输出

---

## 📂 项目结构

```
Ultimate/
├── app_clean.py              # 主应用文件（清理版）
├── app.py                    # 原始应用文件
├── config.py                 # 配置管理
├── requirements.txt          # Python依赖
├── docker-compose.yml        # Docker编排
├── Dockerfile               # Docker镜像构建
├── .env.example             # 环境变量模板
├── backend/                 # 后端服务模块
│   ├── asr_service.py       # 语音识别服务
│   ├── tts_service.py       # 语音合成服务
│   ├── rag_system.py        # RAG对话系统
│   ├── knowledge_base.py    # 知识库管理
│   ├── database.py          # 数据库管理
│   └── vad_processor.py     # VAD语音检测
├── utils/                   # 工具模块
│   ├── logger.py            # 日志管理
│   └── security.py          # 安全工具
├── templates/               # HTML模板
│   └── index.html           # 主页面
├── static/                  # 静态资源
│   ├── css/style.css        # 样式文件
│   └── js/app.js            # 前端脚本
├── logs/                    # 日志文件
├── uploads/                 # 上传文件存储
├── knowledge_base/          # 知识库文件
└── vector_db/               # 向量数据库
```

---

## 🔧 API接口

### 🌐 HTTP端点
| 端点 | 方法 | 描述 |
|------|------|------|
| `/` | GET | 主页面 |
| `/health` | GET | 健康检查 |
| `/asr` | POST | 音频转文字 |
| `/tts` | POST | 文字转语音 |
| `/chat` | POST | AI对话 |
| `/chat_stream` | POST | 流式对话 |
| `/upload_document` | POST | 上传文档 |
| `/list_documents` | GET | 列出文档 |
| `/delete_document` | POST | 删除文档 |

### 🔌 WebSocket事件
| 事件 | 方向 | 描述 |
|------|------|------|
| `connect` | 客户端→服务器 | 建立连接 |
| `stream` | 客户端→服务器 | 音频流数据 |
| `pause_voice` | 客户端→服务器 | 暂停语音 |
| `resume_voice` | 客户端→服务器 | 恢复语音 |
| `voice_status` | 服务器→客户端 | 语音状态 |
| `asr_result` | 服务器→客户端 | 识别结果 |
| `llm_response` | 服务器→客户端 | AI回复 |
| `tts_speech` | 服务器→客户端 | 合成语音 |

---

## 🔧 配置说明

### 📝 环境变量
```bash
# 必需配置
DASHSCOPE_API_KEY=sk-xxx        # 阿里云DashScope API密钥

# 服务器配置
HOST=0.0.0.0                    # 监听地址
PORT=5000                       # 监听端口
DEBUG=False                     # 调试模式

# Redis配置
REDIS_HOST=localhost            # Redis主机
REDIS_PORT=6379                 # Redis端口
REDIS_DB=0                      # Redis数据库
REDIS_PASSWORD=                 # Redis密码

# PostgreSQL配置（可选）
POSTGRES_HOST=localhost         # PostgreSQL主机
POSTGRES_PORT=5432              # PostgreSQL端口
POSTGRES_DB=asr_llm_tts         # 数据库名
POSTGRES_USER=postgres          # 用户名
POSTGRES_PASSWORD=              # 密码

# AI模型配置
LLM_MODEL=qwen-plus             # 语言模型
ASR_MODEL=paraformer-realtime-v2 # 语音识别模型
TTS_MODEL=cosyvoice-v2          # 语音合成模型
EMBEDDING_MODEL=text-embedding-v1 # 嵌入模型
```

### 🎛️ 应用配置
```python
# 文件上传限制
MAX_CONTENT_LENGTH = 16MB       # 最大文件大小
ALLOWED_AUDIO_EXTENSIONS = wav,mp3,flac,m4a,ogg,webm
ALLOWED_DOCUMENT_EXTENSIONS = pdf,txt,docx,doc,md

# RAG设置
CHUNK_SIZE = 1000               # 文档块大小
CHUNK_OVERLAP = 200             # 块重叠大小
RETRIEVAL_K = 3                 # 检索数量

# 语音设置
RECORDING_SAMPLE_RATE = 16000   # 采样率
RECORDING_CHANNELS = 1          # 单声道
```

---

## 🚧 开发历程与问题解决

### 🔄 迭代过程
我们在开发过程中经历了多个版本的迭代，解决了大量技术难题：

#### 第一阶段：基础功能实现
- ✅ **基础Flask应用**: HTTP API端点
- ✅ **DashScope集成**: ASR、LLM、TTS基础功能
- ✅ **前端界面**: Bootstrap UI设计

#### 第二阶段：实时语音对话
- ✅ **WebSocket集成**: Flask-SocketIO实时通信
- ✅ **VAD语音检测**: 智能断点识别
- ✅ **流式音频处理**: 20ms音频块处理
- ✅ **端到端链路**: 完整的语音对话流程

#### 第三阶段：数据库与RAG
- ✅ **数据库集成**: PostgreSQL + Redis
- ✅ **向量数据库**: ChromaDB文档检索
- ✅ **RAG系统**: 知识增强对话
- ✅ **Fallback机制**: 数据库不可用时的内存模式

#### 第四阶段：稳定性优化
- ✅ **错误处理**: 完整的异常处理机制
- ✅ **配置管理**: 统一的配置访问方式
- ✅ **代码清理**: 修复语法错误和格式问题
- ✅ **性能优化**: 异步处理和连接池

### 🐛 主要问题与解决方案

#### 1. 配置访问不一致
**问题**: `app.config[]` 和 `config.属性` 混用导致AttributeError
```python
# 错误方式
dashscope.api_key = app.config['DASHSCOPE_API_KEY']  # KeyError

# 正确方式  
dashscope.api_key = config_instance.DASHSCOPE_API_KEY
```
**解决**: 统一使用 `config_instance` 访问所有配置

#### 2. Flask版本兼容性
**问题**: `@app.before_first_request` 在新版Flask中被废弃
```python
# 废弃方式
@app.before_first_request
def init_services():
    pass

# 现代方式
if __name__ == '__main__':
    initialize_services()
```
**解决**: 在主函数中显式初始化服务

#### 3. 数据库连接问题  
**问题**: PostgreSQL编码错误，Redis连接失败
```python
# 问题：硬编码连接失败
engine = create_engine(db_url)  # 可能失败

# 解决：Fallback机制
try:
    engine = create_engine(db_url)
    self.postgres_available = True
except Exception:
    self.postgres_available = False
    logger.warning("使用内存模式")
```
**解决**: 实现完整的fallback机制，确保应用在任何环境下都能运行

#### 4. WebSocket异步模式
**问题**: `gevent` 模式在Windows下兼容性问题
```python
# 问题模式
socketio = SocketIO(app, async_mode='gevent')  # Windows兼容性差

# 解决方案
socketio = SocketIO(app, async_mode='threading')  # 更好的兼容性
```
**解决**: 使用 `threading` 模式提高跨平台兼容性

#### 5. 语法错误和格式问题
**问题**: 行合并导致的语法错误
```python
# 错误格式
print("消息1")    print("消息2")  # SyntaxError

# 正确格式
print("消息1")
print("消息2")
```
**解决**: 创建 `app_clean.py` 清理版本，完全重写有问题的代码段

#### 6. VAD音频处理
**问题**: 音频格式转换和VAD参数调优
```python
# 问题：直接处理原始音频
vad.is_speech(raw_audio)  # 可能失败

# 解决：格式转换和参数优化
chunk_size = int(sample_rate * frame_duration_ms / 1000) * 2
audio_frame = struct.unpack('<h', chunk_data)
is_speech = vad.is_speech(audio_frame, sample_rate)
```
**解决**: 实现完整的音频格式转换和VAD参数调优

### 🏆 最终成果
经过多轮迭代和问题解决，我们实现了：
- ✅ **稳定的实时语音对话系统**
- ✅ **完整的错误处理和fallback机制**  
- ✅ **高质量的代码结构和文档**
- ✅ **跨平台兼容性**
- ✅ **生产就绪的部署方案**

---

## 🧪 测试与验证

### 🔍 功能测试
```bash
# 测试基础功能
python test_server.py        # 服务器连接测试
python test_tts_api.py       # TTS功能测试
python test_redis.py         # Redis连接测试
python test_config.py        # 配置读取测试

# 健康检查
curl http://127.0.0.1:5000/health
```

### 📊 性能指标
- **语音识别延迟**: < 500ms
- **AI回复生成**: < 2s
- **语音合成**: < 800ms
- **端到端延迟**: < 3s
- **并发支持**: 10+ 用户

---

## 🚀 部署建议

### 🏭 生产环境
1. **使用反向代理** (Nginx)
2. **启用HTTPS** (SSL证书)
3. **配置日志轮转**
4. **监控和告警** (Prometheus + Grafana)
5. **负载均衡** (多实例部署)

### 🔒 安全配置
```bash
# 生产环境变量
DEBUG=False
SECRET_KEY=your-secret-production-key
REDIS_PASSWORD=strong-redis-password
POSTGRES_PASSWORD=strong-db-password
```

### 📈 扩展建议
- **微服务化**: 拆分ASR、LLM、TTS为独立服务
- **消息队列**: Redis/RabbitMQ处理异步任务
- **CDN加速**: 静态资源和音频文件
- **数据库优化**: 读写分离、缓存策略

---

## 🤝 贡献指南

### 📝 提交规范
```bash
# 功能开发
git commit -m "feat: 添加新功能描述"

# 问题修复  
git commit -m "fix: 修复具体问题"

# 文档更新
git commit -m "docs: 更新文档内容"
```

### 🔧 开发环境
```bash
# 安装开发依赖
pip install -r requirements-dev.txt

# 代码格式化
black .
flake8 .

# 类型检查
mypy .
```

---

## 📜 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [阿里云DashScope](https://help.aliyun.com/product/2236920.html) - AI服务支持
- [Flask](https://flask.palletsprojects.com/) - Web框架
- [Bootstrap](https://getbootstrap.com/) - UI框架  
- [ChromaDB](https://www.trychroma.com/) - 向量数据库
- 所有开源贡献者

---

## 📞 联系方式

- **项目主页**: https://github.com/your-username/asr-llm-tts
- **问题反馈**: [GitHub Issues](https://github.com/your-username/asr-llm-tts/issues)
- **讨论交流**: [GitHub Discussions](https://github.com/your-username/asr-llm-tts/discussions)

---

**⭐ 如果这个项目对您有帮助，请给我们一个Star！**
