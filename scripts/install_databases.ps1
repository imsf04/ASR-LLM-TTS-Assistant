# ASR-LLM-TTS 数据库安装脚本
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  ASR-LLM-TTS 数据库安装脚本" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan

# 检查是否有管理员权限
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "❌ 需要管理员权限运行此脚本" -ForegroundColor Red
    Write-Host "请以管理员身份运行PowerShell" -ForegroundColor Yellow
    Read-Host "按回车键退出"
    exit 1
}

Write-Host "`n[1/4] 检查现有服务..." -ForegroundColor Yellow

# 检查PostgreSQL是否已安装
$pgService = Get-Service -Name "*PostgreSQL*" -ErrorAction SilentlyContinue
if ($pgService) {
    Write-Host "✅ PostgreSQL 服务已存在: $($pgService.Name)" -ForegroundColor Green
}
else {
    Write-Host "❌ PostgreSQL 未安装" -ForegroundColor Red
    Write-Host "请手动安装PostgreSQL:" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://www.postgresql.org/download/windows/" -ForegroundColor White
    Write-Host "  2. 下载并安装PostgreSQL" -ForegroundColor White
    Write-Host "  3. 设置密码为: postgres123" -ForegroundColor White
    Write-Host "  4. 创建数据库: asr_llm_tts" -ForegroundColor White
}

# 检查Redis是否已安装
$redisService = Get-Service -Name "*Redis*" -ErrorAction SilentlyContinue
if ($redisService) {
    Write-Host "✅ Redis 服务已存在: $($redisService.Name)" -ForegroundColor Green
}
else {
    Write-Host "❌ Redis 未安装" -ForegroundColor Red
    Write-Host "请手动安装Redis:" -ForegroundColor Yellow
    Write-Host "  1. 访问 https://github.com/tporadowski/redis/releases" -ForegroundColor White
    Write-Host "  2. 下载 Redis-x64-xxx.msi" -ForegroundColor White
    Write-Host "  3. 安装时选择'作为服务运行'" -ForegroundColor White
}

Write-Host "`n[2/4] 检查Python依赖..." -ForegroundColor Yellow
try {
    python -c "import psycopg2; print('✅ psycopg2 可用')"
    python -c "import redis; print('✅ redis 可用')"
    python -c "import sqlalchemy; print('✅ SQLAlchemy 可用')"
}
catch {
    Write-Host "❌ 安装Python依赖失败" -ForegroundColor Red
    pip install psycopg2-binary redis SQLAlchemy
}

Write-Host "`n[3/4] 启动数据库服务..." -ForegroundColor Yellow

# 启动PostgreSQL服务
if ($pgService) {
    try {
        Start-Service $pgService.Name -ErrorAction Stop
        Write-Host "✅ PostgreSQL 服务已启动" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ 启动 PostgreSQL 失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

# 启动Redis服务
if ($redisService) {
    try {
        Start-Service $redisService.Name -ErrorAction Stop
        Write-Host "✅ Redis 服务已启动" -ForegroundColor Green
    }
    catch {
        Write-Host "❌ 启动 Redis 失败: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n[4/4] 测试数据库连接..." -ForegroundColor Yellow

# 测试PostgreSQL连接
python -c "
import os
os.environ['TESTING'] = '1'
try:
    import psycopg2
    conn = psycopg2.connect(
        host='localhost',
        port=5432,
        database='postgres',
        user='postgres',
        password='postgres123'
    )
    conn.close()
    print('✅ PostgreSQL 连接成功')
except Exception as e:
    print(f'❌ PostgreSQL 连接失败: {e}')
"

# 测试Redis连接
python -c "
try:
    import redis
    r = redis.Redis(host='localhost', port=6379, db=0)
    r.ping()
    print('✅ Redis 连接成功')
except Exception as e:
    print(f'❌ Redis 连接失败: {e}')
"

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  安装完成！运行以下命令启动应用：" -ForegroundColor Cyan
Write-Host "  python app.py" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Cyan

Read-Host "`n按回车键退出"
