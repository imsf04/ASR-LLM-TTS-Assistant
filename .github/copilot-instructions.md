<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# ASR-LLM-TTS 智能助手项目

这是一个基于Flask的ASR-LLM-TTS智能助手项目，整合了语音识别、大语言模型对话和语音合成功能。

## 项目架构

- **Frontend**: HTML5 + Bootstrap 5 + JavaScript (原生JS，支持录音、TTS、文件上传)
- **Backend**: Flask + SQLAlchemy + Redis + ChromaDB
- **AI Services**: 阿里云DashScope API (ASR、LLM、TTS、Embedding)
- **Database**: PostgreSQL (结构化数据) + Redis (缓存) + ChromaDB (向量数据库)

## 主要功能

1. **ASR (语音识别)**: 使用DashScope paraformer模型
2. **LLM对话**: 使用Qwen-Plus模型，支持RAG检索增强
3. **TTS (语音合成)**: 使用CosyVoice v2模型
4. **知识库管理**: 支持PDF、DOCX、TXT文档上传和向量化
5. **实时通信**: WebSocket支持流式对话
6. **数据管理**: Redis缓存 + PostgreSQL持久化

## 代码风格指南

- Python: 遵循PEP 8规范，使用类型提示
- JavaScript: 使用ES6+语法，模块化组织
- 错误处理: 完整的try-catch和日志记录
- 安全性: 输入验证、文件类型检查、API密钥环境变量

## API端点

- `/health` - 健康检查
- `/asr` - 语音识别
- `/tts` - 语音合成  
- `/chat` - LLM对话
- `/chat_stream` - 流式对话
- `/upload_document` - 文档上传
- `/list_documents` - 文档列表
- `/delete_document` - 删除文档

## 开发注意事项

- 使用DashScope SDK 1.20.0+
- 支持CosyVoice v2语音合成
- 实现完整的错误处理和日志记录
- 前端支持响应式设计
- 后端支持异步处理和数据库连接池
