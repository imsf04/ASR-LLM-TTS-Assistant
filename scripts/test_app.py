#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速功能测试脚本
测试ASR-LLM-TTS应用的核心功能
"""

import requests
import json
import time
import redis
import psycopg2
import os
from dotenv import load_dotenv
from typing import Dict, Any

# 加载环境变量
load_dotenv()

# 应用配置
BASE_URL = "http://127.0.0.1:5000"

def test_health() -> bool:
    """测试健康检查端点"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查通过: {data}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def test_llm_chat() -> bool:
    """测试LLM对话功能"""
    try:
        payload = {
            "message": "你好，你是谁？",
            "use_rag": False
        }
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ LLM对话成功: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ LLM对话失败: {response.status_code} - {response.text}")
            return False
    except Exception as e:
        print(f"❌ LLM对话异常: {e}")
        return False

def test_tts() -> bool:
    """测试TTS功能"""
    try:
        payload = {
            "text": "这是一个测试",
            "voice": "longyuan"
        }
        response = requests.post(f"{BASE_URL}/tts", json=payload, timeout=30)
        if response.status_code == 200 and response.headers.get('content-type') == 'audio/wav':
            print(f"✅ TTS合成成功: 音频大小 {len(response.content)} 字节")
            return True
        else:
            print(f"❌ TTS合成失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ TTS合成异常: {e}")
        return False

def test_redis_connection() -> bool:
    """测试Redis连接"""
    try:
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
        r.ping()
        # 测试基本操作
        r.set('test_key', 'test_value')
        value = r.get('test_key')
        r.delete('test_key')
        print(f"✅ Redis连接成功: PING响应正常，读写测试通过")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        return False

def test_postgresql_connection() -> bool:
    """测试PostgreSQL连接"""
    try:
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',  # 先连接默认数据库
            user='postgres',
            password='postgres123',
            connect_timeout=5
        )
        conn.close()
        
        # 检查项目数据库是否存在
        try:
            conn = psycopg2.connect(
                host='localhost',
                port=5432,
                database='asr_llm_tts',
                user='postgres',
                password='postgres123',
                connect_timeout=5
            )
            conn.close()
            print(f"✅ PostgreSQL连接成功: 项目数据库 'asr_llm_tts' 可访问")
            return True
        except psycopg2.OperationalError:
            print(f"⚠️  PostgreSQL连接成功，但项目数据库 'asr_llm_tts' 不存在")
            print(f"   请创建数据库: createdb -U postgres asr_llm_tts")
            return False
            
    except psycopg2.OperationalError as e:
        error_msg = str(e)
        if "could not connect to server" in error_msg:
            print(f"❌ PostgreSQL服务未运行")
            print(f"   PostgreSQL可能未安装，请访问:")
            print(f"   https://www.postgresql.org/download/windows/")
        elif "password authentication failed" in error_msg:
            print(f"❌ PostgreSQL密码错误")
            print(f"   期望密码: postgres123")
        else:
            print(f"❌ PostgreSQL连接失败: 服务未安装或未运行")
            print(f"   请安装PostgreSQL并设置密码为: postgres123")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        print(f"   请确认PostgreSQL已安装并使用密码 'postgres123'")
        return False

def test_simple_connection():
    """简单的数据库连接测试（安装验证用）"""
    print("\n=== 简单连接测试 ===")
    
    # 测试Redis
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=3)
        r.ping()
        print("✅ Redis: 连接正常")
        redis_ok = True
    except Exception as e:
        print(f"❌ Redis: {e}")
        redis_ok = False
    
    # 测试PostgreSQL
    try:
        import psycopg2
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='postgres123',
            connect_timeout=3
        )
        conn.close()
        print("✅ PostgreSQL: 连接正常")
        pg_ok = True
    except Exception as e:
        print(f"❌ PostgreSQL: {e}")
        pg_ok = False
    
    return redis_ok and pg_ok

def main():
    """主测试函数"""
    print("=" * 50)
    print("  ASR-LLM-TTS 功能测试")
    print("=" * 50)
    print(f"测试目标: {BASE_URL}")
    print()
    
    # 等待服务启动
    print("等待服务启动...")
    time.sleep(2)
      # 执行测试
    tests = [
        ("健康检查", test_health),
        ("LLM对话", test_llm_chat),
        ("TTS语音合成", test_tts),
        ("Redis连接", test_redis_connection),
    ]
    
    # 只在PostgreSQL启用时测试
    import os
    if os.getenv('POSTGRES_ENABLED', 'False').lower() == 'true':
        tests.append(("PostgreSQL连接", test_postgresql_connection))
    
    results = {}
    for test_name, test_func in tests:
        print(f"\n[测试] {test_name}...")
        results[test_name] = test_func()
    
    # 显示结果
    print("\n" + "=" * 50)
    print("  测试结果汇总")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{len(tests)} ({passed/len(tests)*100:.1f}%)")
    
    if passed == len(tests):
        print("\n🎉 所有测试通过！应用运行正常。")
        print("你可以在浏览器中访问 http://127.0.0.1:5000 体验完整功能。")
    else:
        print("\n⚠️  部分测试失败，请检查应用状态和配置。")

if __name__ == "__main__":
    # 如果直接运行，进行简单的数据库测试
    print("🔧 简单数据库连接测试")
    result = test_simple_connection()
    if result:
        print("✅ 数据库连接正常，可以运行完整应用")
    else:
        print("⚠️  数据库连接有问题，建议使用简化版应用")
    
    # 运行主要测试
    main()
