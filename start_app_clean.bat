@echo off
echo ==========================================
echo   启动 ASR-LLM-TTS 清理版应用
echo ==========================================

echo [1] 检查环境...
python -c "import flask, dashscope; print('✅ 核心依赖检查通过')" 2>nul
if %errorlevel% neq 0 (
    echo ❌ 依赖包缺失，请先安装
    pause
    exit /b 1
)

echo [2] 检查端口 5000...
netstat -ano | findstr :5000 >nul
if %errorlevel% == 0 (
    echo ⚠️  端口 5000 已被占用，正在清理...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5000') do taskkill /pid %%a /f >nul 2>&1
    timeout /t 2 /nobreak >nul
)

echo [3] 启动清理版应用...
echo 启动地址: http://127.0.0.1:5000
echo 按 Ctrl+C 停止应用
echo.
python app_clean.py

pause
