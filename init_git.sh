#!/bin/bash

# ASR-LLM-TTS 项目 Git 初始化和推送脚本

echo "=========================================="
echo "  ASR-LLM-TTS 项目 Git 部署脚本"
echo "=========================================="

# 检查是否已经是Git仓库
if [ ! -d ".git" ]; then
    echo "🔧 初始化Git仓库..."
    git init
fi

# 创建.gitignore文件
echo "📝 创建.gitignore文件..."
cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
pip-wheel-metadata/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Environment
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# Logs
logs/
*.log

# Uploads and temporary files
uploads/
temp/
tmp/

# Database
*.db
*.sqlite3

# Vector database
vector_db/
chroma.sqlite3

# Knowledge base files
knowledge_base/*.pdf
knowledge_base/*.docx
knowledge_base/*.txt

# OS
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# Docker
.dockerignore

# Backup files
*.backup
*.bak
EOF

# 添加所有文件到Git
echo "📦 添加文件到Git..."
git add .

# 检查状态
echo "📊 Git状态:"
git status

# 提交更改
echo "💾 提交更改..."
git commit -m "feat: 完整的ASR-LLM-TTS智能助手项目

🚀 项目特性:
- 实时语音对话 (WebSocket + VAD)
- 语音识别 (DashScope ASR)
- AI对话 (RAG + LLM)
- 语音合成 (CosyVoice v2)
- 知识库管理 (ChromaDB)
- 数据库支持 (PostgreSQL + Redis)
- 现代化UI (Bootstrap 5)
- Docker化部署

🐛 解决的问题:
- 配置访问统一化
- Flask版本兼容性
- 数据库fallback机制
- WebSocket异步模式优化
- 语法错误和格式问题
- VAD音频处理优化

📝 技术栈:
- Backend: Flask + SocketIO + Redis + ChromaDB
- Frontend: Bootstrap 5 + WebSocket
- AI: DashScope全栈 (ASR/LLM/TTS/Embedding)
- Database: PostgreSQL + Redis + ChromaDB"

echo ""
echo "✅ Git仓库初始化完成!"
echo ""
echo "🚀 推送到GitHub步骤:"
echo "1. 在GitHub创建新仓库: asr-llm-tts"
echo "2. 执行以下命令:"
echo ""
echo "   git remote add origin https://github.com/your-username/asr-llm-tts.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "📚 或者使用GitHub CLI:"
echo "   gh repo create asr-llm-tts --public --source=. --remote=origin --push"
echo ""
echo "=========================================="
echo "  Git仓库准备完成!"
echo "=========================================="
