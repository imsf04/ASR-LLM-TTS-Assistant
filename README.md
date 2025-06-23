# ASR-LLM-TTS 智能助手

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-2.x-orange.svg)](https://flask.palletsprojects.com/)
[![DashScope](https://img.shields.io/badge/AI-DashScope-green.svg)](https://help.aliyun.com/product/2236920.html)
[![Bootstrap](https://img.shields.io/badge/Frontend-Bootstrap%205-purple.svg)](https://getbootstrap.com/)
[![Docker](https://img.shields.io/badge/Docker-Supported-blue.svg)](https://www.docker.com/)

一个功能强大的Web智能助手，深度集成了**语音识别 (ASR)**、**大语言模型 (LLM)** 对话和**语音合成 (TTS)** 功能。项目基于Flask和阿里云DashScope API构建，拥有现代化的Web界面和可扩展的后端服务。

![TTS Demo Page](https://raw.githubusercontent.com/your-username/your-repo/main/docs/images/screenshot.png)
*(请将此图片链接替换为您的项目截图)*

---

## ✨ 功能特性

- **🎤 实时语音识别 (ASR)**:
  - 基于DashScope Paraformer-realtime-v2模型，支持中英文自动识别。
  - 支持浏览器端实时录音和音频文件上传。
  - 识别结果自动填充输入框，并高亮提示一键发送。

- **💬 智能LLM对话**:
  - 集成DashScope Qwen系列大语言模型，提供流畅、智能的对话体验。
  - 支持Markdown格式渲染，包括代码块、列表和数学公式(MathJax)。

- **🔊 高质量语音合成 (TTS)**:
  - 集成DashScope CosyVoice v2模型，提供多种高质量中文语音。
  - **自动播报**: AI的每一个回复都能自动播放语音。
  - **手动点播**: 每条AI回复都附带“朗读”按钮，可随时播放。
  - **独立演示页面**: 提供`tts_demo.html`用于测试和展示所有可用语音。

- **📚 RAG知识库 (可选)**:
  - 支持上传PDF, DOCX, TXT等格式的文档，构建本地知识库。
  - 利用Embedding模型和ChromaDB向量数据库实现检索增强生成。

- **🌐 现代化Web界面**:
  - 基于Bootstrap 5构建，响应式设计，适配桌面和移动设备。
  - 包含侧边栏、对话区、文件上传、知识库管理等模块。
  - 实时打字效果、录音动画、消息操作（复制/朗读）等交互细节。

- **🔧 可扩展架构**:
  - 清晰的前后端分离。
  - 后端服务模块化（ASR, TTS, RAG等），易于扩展和维护。
  - 支持Redis缓存和PostgreSQL持久化（当前简化版已禁用PostgreSQL）。

- **🐳 Docker化部署**:
  - 提供`Dockerfile`和`docker-compose.yml`，支持一键容器化部署。

---

## 🛠️ 技术栈

- **后端**: Flask, Python
- **AI服务**: 阿里云DashScope (ASR, LLM, TTS, Embedding)
- **数据库**: Redis (缓存), ChromaDB (向量存储), PostgreSQL (结构化数据 - 可选)
- **前端**: HTML5, CSS3, JavaScript (原生), Bootstrap 5
- **核心库**: `dashscope`, `redis`, `flask_cors`, `gunicorn`

---

## 🚀 快速开始

### 1. 环境准备

- Python 3.9+
- FFmpeg (用于音频处理，请确保已安装并添加到系统PATH)
- Redis (用于缓存)

### 2. 克隆与安装依赖

```bash
git clone <your-repository-url>
cd Ultimate
pip install -r requirements.txt
```

### 3. 配置API密钥

1.  在项目根目录创建 `.env` 文件。
2.  在 `.env` 文件中填入您的阿里云DashScope API密钥。

```env
# .env
DASHSCOPE_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

### 4. 启动应用

项目提供了两个启动入口：

- **完整版 (包含数据库)**: `app.py`
- **简化版 (仅核心AI功能)**: `app_simple.py` (推荐用于快速体验)

```bash
# 启动简化版
python app_simple.py
```

应用将在 `http://localhost:5000` 启动。

### 5. Docker部署 (可选)

确保Docker和Docker Compose已安装。

```bash
# 在项目根目录运行
docker-compose up --build
```

---

## 📝 API 端点

- `GET /health`: 健康检查
- `POST /asr`: 语音识别 (上传音频文件)
- `POST /tts`: 语音合成 (输入文本)
- `POST /chat`: LLM对话
- `POST /upload_document`: 上传文档到知识库
- `GET /list_documents`: 列出知识库中的文档
- `POST /delete_document`: 删除知识库中的文档

---

## 📂 项目结构

```
/
├── backend/              # 后端核心服务
│   ├── asr_service.py    # ASR服务
│   ├── tts_service.py    # TTS服务
│   ├── rag_system.py     # RAG系统
│   └── ...
├── static/               # 前端静态资源
│   ├── css/style.css
│   └── js/app.js
├── templates/            # Flask HTML模板
│   └── index.html
├── scripts/              # 测试和工具脚本
├── knowledge_base/       # 知识库文档存储
├── app_simple.py         # 简化版启动入口
├── app.py                # 完整版启动入口
├── requirements.txt      # Python依赖
├── config.py             # 配置文件
├── Dockerfile            # Docker镜像配置
└── docker-compose.yml    # Docker Compose配置
```

---

## 🤝 贡献

欢迎提交Pull Request或Issue来改进项目！

## 📄 许可证

本项目采用 [MIT](LICENSE) 许可证。
