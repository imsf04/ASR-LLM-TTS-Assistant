#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统状态检查和修复脚本
"""

import subprocess
import sys
import time
import requests
from pathlib import Path

def check_flask_app():
    """检查Flask应用状态"""
    print("=== Flask应用状态检查 ===")
    try:
        response = requests.get("http://127.0.0.1:5000/health", timeout=3)
        print("✅ Flask应用正在运行")
        return True
    except requests.exceptions.ConnectionError:
        print("❌ Flask应用未运行")
        return False
    except Exception as e:
        print(f"❌ Flask检查失败: {e}")
        return False

def check_processes():
    """检查相关进程"""
    print("\n=== 进程状态检查 ===")
    try:
        # 检查Python进程
        result = subprocess.run(['tasklist', '/FI', 'IMAGENAME eq python.exe'], 
                              capture_output=True, text=True, encoding='gbk')
        if 'python.exe' in result.stdout:
            print("✅ 检测到Python进程运行中")
            lines = result.stdout.split('\n')
            for line in lines:
                if 'python.exe' in line:
                    print(f"   {line.strip()}")
        else:
            print("❌ 未检测到Python进程")
    except Exception as e:
        print(f"❌ 进程检查失败: {e}")

def start_simple_app():
    """启动简化版应用"""
    print("\n=== 启动简化版应用 ===")
    try:
        import os
        os.chdir(Path(__file__).parent.parent)
        print("正在启动 app_simple.py...")
        print("请在另一个终端运行: python app_simple.py")
        print("然后重新运行测试: python scripts/test_app.py")
        return True
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        return False

def check_postgresql_install():
    """检查PostgreSQL安装状态"""
    print("\n=== PostgreSQL安装检查 ===")
    try:
        # 检查PostgreSQL服务
        result = subprocess.run(['sc', 'query', 'postgresql*'], 
                              capture_output=True, text=True, encoding='gbk')
        if 'postgresql' in result.stdout.lower():
            print("✅ PostgreSQL服务已安装")
            return True
        else:
            print("❌ PostgreSQL服务未安装")
            print("请按以下步骤安装PostgreSQL:")
            print("1. 访问: https://www.postgresql.org/download/windows/")
            print("2. 下载PostgreSQL 15.x")
            print("3. 安装时设置密码: postgres123")
            print("4. 跳过Stack Builder")
            return False
    except Exception as e:
        print(f"❌ PostgreSQL检查失败: {e}")
        return False

def main():
    print("🔧 ASR-LLM-TTS 系统修复工具")
    print("=" * 50)
    
    # 检查各组件状态
    flask_ok = check_flask_app()
    check_processes()
    pg_ok = check_postgresql_install()
    
    print("\n" + "=" * 50)
    print("📋 修复建议")
    print("=" * 50)
    
    if not flask_ok:
        print("🔥 [紧急] Flask应用未运行")
        print("   解决方案:")
        print("   1. 打开新的PowerShell终端")
        print("   2. cd \"d:\\Desktop\\py\\6.16-6.20\\Ultimate\"")
        print("   3. python app_simple.py")
        print("   4. 保持运行，然后重新测试")
        print()
    
    if not pg_ok:
        print("📥 [可选] PostgreSQL未安装")
        print("   当前可以:")
        print("   - 使用简化版应用 (app_simple.py)")
        print("   - 体验ASR、LLM、TTS功能")
        print("   - Redis缓存已可用")
        print()
        print("   如需完整功能，请安装PostgreSQL:")
        print("   1. https://www.postgresql.org/download/windows/")
        print("   2. 密码设置为: postgres123")
        print("   3. 跳过Stack Builder")
        print()
    
    # 提供快速启动命令
    print("🚀 快速启动命令:")
    print("   # 启动简化版应用")
    print("   python app_simple.py")
    print()
    print("   # 在另一个终端测试")
    print("   python scripts/test_app.py")
    print()
    print("   # 浏览器访问")
    print("   http://127.0.0.1:5000")

if __name__ == "__main__":
    main()
