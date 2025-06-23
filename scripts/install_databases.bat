@echo off
echo ================================================
echo   ASR-LLM-TTS 数据库安装脚本
echo ================================================
echo.

echo [1/3] 检查Docker是否可用...
docker --version >nul 2>&1
if %errorlevel%==0 (
    echo ✅ Docker已安装，推荐使用Docker方式安装
    echo.
    echo 正在启动PostgreSQL容器...
    docker run --name postgres-asr -e POSTGRES_PASSWORD=postgres123 -e POSTGRES_DB=asr_llm_tts -p 5432:5432 -d postgres:15
    echo.
    echo 正在启动Redis容器...
    docker run --name redis-asr -p 6379:6379 -d redis:latest
    echo.
    echo ✅ 数据库容器启动完成！
    echo.
    echo 容器管理命令：
    echo   启动: docker start postgres-asr redis-asr
    echo   停止: docker stop postgres-asr redis-asr
    echo   删除: docker rm postgres-asr redis-asr
) else (
    echo ❌ Docker未安装
    echo.
    echo 请手动安装PostgreSQL和Redis：
    echo.
    echo PostgreSQL:
    echo   1. 访问 https://www.postgresql.org/download/windows/
    echo   2. 下载并安装PostgreSQL
    echo   3. 设置密码为: postgres123
    echo   4. 创建数据库: asr_llm_tts
    echo.
    echo Redis:
    echo   1. 访问 https://github.com/tporadowski/redis/releases
    echo   2. 下载并安装Redis for Windows
    echo   3. 使用默认配置
)

echo.
echo [2/3] 安装Python依赖...
pip install psycopg2-binary redis SQLAlchemy

echo.
echo [3/3] 测试数据库连接...
python -c "
import os
os.environ['TESTING'] = '1'
try:
    import psycopg2
    import redis
    print('✅ Python数据库驱动安装成功')
except ImportError as e:
    print(f'❌ 缺少依赖: {e}')
"

echo.
echo ================================================
echo   安装完成！运行以下命令启动应用：
echo   python app.py
echo ================================================
pause
