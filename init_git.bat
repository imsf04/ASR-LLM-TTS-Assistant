@echo off
chcp 65001 >nul

echo ==========================================
echo   ASR-LLM-TTS 项目 Git 部署脚本
echo ==========================================

REM 检查是否已经是Git仓库
if not exist ".git" (
    echo 🔧 初始化Git仓库...
    git init
)

REM 创建.gitignore文件
echo 📝 创建.gitignore文件...
(
echo # Python
echo __pycache__/
echo *.py[cod]
echo *$py.class
echo *.so
echo .Python
echo build/
echo develop-eggs/
echo dist/
echo downloads/
echo eggs/
echo .eggs/
echo lib/
echo lib64/
echo parts/
echo sdist/
echo var/
echo wheels/
echo pip-wheel-metadata/
echo share/python-wheels/
echo *.egg-info/
echo .installed.cfg
echo *.egg
echo MANIFEST
echo.
echo # Environment
echo .env
echo .venv
echo env/
echo venv/
echo ENV/
echo env.bak/
echo venv.bak/
echo.
echo # IDE
echo .vscode/
echo .idea/
echo *.swp
echo *.swo
echo *~
echo.
echo # Logs
echo logs/
echo *.log
echo.
echo # Uploads and temporary files
echo uploads/
echo temp/
echo tmp/
echo.
echo # Database
echo *.db
echo *.sqlite3
echo.
echo # Vector database
echo vector_db/
echo chroma.sqlite3
echo.
echo # Knowledge base files
echo knowledge_base/*.pdf
echo knowledge_base/*.docx
echo knowledge_base/*.txt
echo.
echo # OS
echo .DS_Store
echo .DS_Store?
echo ._*
echo .Spotlight-V100
echo .Trashes
echo ehthumbs.db
echo Thumbs.db
echo.
echo # Docker
echo .dockerignore
echo.
echo # Backup files
echo *.backup
echo *.bak
) > .gitignore

REM 添加所有文件到Git
echo 📦 添加文件到Git...
git add .

REM 检查状态
echo 📊 Git状态:
git status

REM 提交更改
echo 💾 提交更改...
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

echo.
echo ✅ Git仓库初始化完成!
echo.
echo 🚀 推送到GitHub步骤:
echo 1. 在GitHub创建新仓库: asr-llm-tts
echo 2. 执行以下命令:
echo.
echo    git remote add origin https://github.com/your-username/asr-llm-tts.git
echo    git branch -M main
echo    git push -u origin main
echo.
echo 📚 或者使用GitHub CLI:
echo    gh repo create asr-llm-tts --public --source=. --remote=origin --push
echo.
echo ==========================================
echo   Git仓库准备完成!
echo ==========================================

pause
