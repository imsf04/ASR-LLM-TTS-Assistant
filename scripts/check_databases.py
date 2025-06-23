#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库状态检查脚本
"""

def check_redis():
    """检查Redis状态"""
    print("=== Redis 状态检查 ===")
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=0, socket_timeout=5)
        result = r.ping()
        print(f"✅ Redis连接成功: PING = {result}")
        
        # 测试读写
        r.set('test_key', 'hello_redis')
        value = r.get('test_key')
        r.delete('test_key')
        print(f"✅ Redis读写测试通过: {value.decode() if value else 'None'}")
        return True
    except Exception as e:
        print(f"❌ Redis连接失败: {e}")
        print("请确认Redis服务是否正在运行")
        return False

def check_postgresql():
    """检查PostgreSQL状态"""
    print("\n=== PostgreSQL 状态检查 ===")
    try:
        import psycopg2
        
        # 连接默认数据库
        conn = psycopg2.connect(
            host='localhost',
            port=5432,
            database='postgres',
            user='postgres',
            password='postgres123',
            connect_timeout=5
        )
        print("✅ PostgreSQL基础连接成功")
        
        # 检查项目数据库
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM pg_database WHERE datname='asr_llm_tts'")
        db_exists = cursor.fetchone()
        
        if db_exists:
            print("✅ 项目数据库 'asr_llm_tts' 已存在")
            conn.close()
            return True
        else:
            print("⚠️  项目数据库 'asr_llm_tts' 不存在，正在创建...")
            conn.autocommit = True
            cursor.execute("CREATE DATABASE asr_llm_tts")
            print("✅ 项目数据库创建成功")
            conn.close()
            return True
            
    except psycopg2.OperationalError as e:
        print(f"❌ PostgreSQL连接失败: {e}")
        if "password authentication failed" in str(e):
            print("   → 密码错误，期望密码: postgres123")
        elif "could not connect to server" in str(e):
            print("   → PostgreSQL服务未运行或未安装")
        else:
            print("   → 请检查PostgreSQL安装和配置")
        return False
    except Exception as e:
        print(f"❌ PostgreSQL其他错误: {e}")
        return False

def main():
    print("🔍 ASR-LLM-TTS 数据库状态检查")
    print("=" * 50)
    
    redis_ok = check_redis()
    pg_ok = check_postgresql()
    
    print("\n" + "=" * 50)
    print("📋 检查结果汇总")
    print("=" * 50)
    print(f"Redis: {'✅ 正常' if redis_ok else '❌ 异常'}")
    print(f"PostgreSQL: {'✅ 正常' if pg_ok else '❌ 异常'}")
    
    if redis_ok and pg_ok:
        print("\n🎉 所有数据库连接正常！")
        print("现在可以运行完整版应用: python app.py")
    else:
        print("\n⚠️  请先解决数据库连接问题")
        if not pg_ok:
            print("PostgreSQL安装指导:")
            print("1. 下载: https://www.postgresql.org/download/windows/")
            print("2. 安装时设置密码: postgres123")
            print("3. 确保服务正在运行")

if __name__ == "__main__":
    main()
