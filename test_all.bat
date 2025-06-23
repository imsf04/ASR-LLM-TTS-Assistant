@echo off
echo ==========================================
echo   ASR-LLM-TTS 功能测试
echo ==========================================

echo [1] 检查Flask应用是否运行...
powershell -Command "try { $response = Invoke-WebRequest -Uri 'http://127.0.0.1:5000' -TimeoutSec 3; Write-Host '✅ Flask应用正在运行' } catch { Write-Host '❌ Flask应用未运行，请先启动: python app_simple.py' }"

echo.
echo [2] 运行功能测试...
python scripts\test_app.py

echo.
echo [3] 测试完成
pause
