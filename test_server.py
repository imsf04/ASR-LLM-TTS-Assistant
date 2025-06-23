#!/usr/bin/env python3
"""
简单的服务器测试脚本
"""
import requests
import time
import socket

def check_port(host, port):
    """检查端口是否开放"""
    try:
        socket.create_connection((host, port), timeout=3)
        return True
    except OSError:
        return False

def test_server():
    """测试服务器连接"""
    host = "127.0.0.1"
    port = 5000
    
    print("=== 服务器连接测试 ===")
    
    # 检查端口
    if check_port(host, port):
        print(f"✓ 端口 {port} 可访问")
    else:
        print(f"✗ 端口 {port} 无法访问")
        return False
    
    # 测试HTTP连接
    try:
        response = requests.get(f"http://{host}:{port}/health", timeout=10)
        print(f"✓ 健康检查成功: {response.status_code}")
        print(f"响应: {response.json()}")
        return True
    except requests.exceptions.ConnectionError:
        print("✗ 连接被拒绝")
        return False
    except requests.exceptions.Timeout:
        print("✗ 连接超时")
        return False
    except Exception as e:
        print(f"✗ 其他错误: {e}")
        return False

if __name__ == "__main__":
    test_server()
