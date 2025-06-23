#!/usr/bin/env python3
"""
ASR功能测试脚本 - 测试语音识别API
"""

import requests
import os
import sys

def test_asr_api():
    """测试ASR API"""
    print("=== 测试ASR API ===")
    
    # 测试URL
    url = "http://localhost:5000/asr"
    
    try:
        # 准备测试文件
        test_data = {"text": "测试语音识别"}
        
        # 发送POST请求
        response = requests.post(url, json=test_data, timeout=10)
        
        print(f"状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"响应内容: {result}")
            print("✅ ASR API测试成功!")
            return True
        else:
            print(f"❌ ASR API测试失败: {response.text}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器，请确保Flask应用正在运行")
        return False
    except Exception as e:
        print(f"❌ ASR API测试失败: {str(e)}")
        return False

def test_health_check():
    """测试健康检查"""
    print("\n=== 测试健康检查 ===")
    
    try:
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            result = response.json()
            print(f"健康检查响应: {result}")
            print("✅ 健康检查成功!")
            return True
        else:
            print(f"❌ 健康检查失败: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 健康检查失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始测试ASR修复结果...\n")
    
    # 测试健康检查
    health_ok = test_health_check()
    
    if health_ok:
        # 测试ASR
        asr_ok = test_asr_api()
        
        if asr_ok:
            print("\n🎉 所有测试通过! ASR语法错误已修复!")
        else:
            print("\n⚠️ ASR API功能需要进一步检查")
    else:
        print("\n❌ 服务器未运行或存在问题")

if __name__ == "__main__":
    main()
