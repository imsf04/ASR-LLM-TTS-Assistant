#!/usr/bin/env python3
"""
测试Redis连接
"""
import os
import redis
from dotenv import load_dotenv
from config import Config

# 加载环境变量
load_dotenv()

print("=== 测试Redis连接 ===")

# 测试配置读取
config = Config()
print(f"REDIS_HOST: {config.REDIS_HOST}")
print(f"REDIS_PORT: {config.REDIS_PORT}")
print(f"REDIS_DB: {config.REDIS_DB}")
print(f"REDIS_PASSWORD: {config.REDIS_PASSWORD}")

# 测试直接连接
try:
    redis_client = redis.Redis(
        host=config.REDIS_HOST,
        port=config.REDIS_PORT,
        db=config.REDIS_DB,
        password=config.REDIS_PASSWORD if config.REDIS_PASSWORD else None,
        decode_responses=True,
        socket_timeout=5,
        socket_connect_timeout=5,
        retry_on_timeout=True
    )
    
    result = redis_client.ping()
    print(f"✓ Redis连接成功: {result}")
    
    # 测试基本操作
    redis_client.set("test_key", "test_value")
    value = redis_client.get("test_key")
    print(f"✓ Redis读写测试成功: {value}")
    redis_client.delete("test_key")
    
except Exception as e:
    print(f"✗ Redis连接失败: {e}")

# 测试DatabaseManager
try:
    from backend.database import DatabaseManager
    db_manager = DatabaseManager(config)
    health = db_manager.health_check()
    print(f"数据库健康检查: {health}")
except Exception as e:
    print(f"✗ DatabaseManager初始化失败: {e}")
    import traceback
    traceback.print_exc()
