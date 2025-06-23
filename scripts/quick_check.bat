@echo off
echo ==========================================
echo   Redis 和 PostgreSQL 快速检查
echo ==========================================

echo.
echo [1] 检查Redis服务状态...
sc query Redis >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Redis服务已安装
    sc query Redis | findstr "STATE"
) else (
    echo ❌ Redis服务未找到
)

echo.
echo [2] 检查PostgreSQL服务状态...
sc query postgresql* >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ PostgreSQL服务已安装
    sc query postgresql* | findstr "STATE"
) else (
    echo ❌ PostgreSQL服务未找到
)

echo.
echo [3] 测试Redis连接...
redis-cli ping >nul 2>&1
if %errorlevel% == 0 (
    echo ✅ Redis可连接
) else (
    echo ❌ Redis连接失败
)

echo.
echo [4] 检查Python依赖...
python -c "import redis; print('✅ Redis库可用')" 2>nul
python -c "import psycopg2; print('✅ PostgreSQL库可用')" 2>nul

echo.
echo ==========================================
echo   如果Redis显示可连接，可以继续安装PostgreSQL
echo   PostgreSQL下载: https://www.postgresql.org/download/windows/
echo ==========================================
pause
