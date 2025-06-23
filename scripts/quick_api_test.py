#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
快速API测试脚本
"""

import requests
import json

BASE_URL = "http://127.0.0.1:5000"

def test_tts_api():
    """测试TTS API"""
    print("测试TTS API...")
    try:
        payload = {
            "text": "你好，这是一个语音合成测试",
            "voice": "longxiaochun_v2"
        }
        response = requests.post(f"{BASE_URL}/tts", json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        print(f"Content-Type: {response.headers.get('content-type', 'N/A')}")
        if response.status_code == 200:
            print(f"✅ TTS成功: 音频大小 {len(response.content)} 字节")
            return True
        else:
            print(f"❌ TTS失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ TTS异常: {e}")
        return False

def test_chat_api():
    """测试聊天API"""
    print("\n测试聊天API...")
    try:
        payload = {
            "message": "你好，请介绍一下你自己",
            "use_rag": False
        }
        response = requests.post(f"{BASE_URL}/chat", json=payload, timeout=30)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 聊天成功: {data.get('response', '')[:100]}...")
            return True
        else:
            print(f"❌ 聊天失败: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 聊天异常: {e}")
        return False

def test_health_api():
    """测试健康检查API"""
    print("\n测试健康检查API...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        print(f"状态码: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 健康检查成功: {data}")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 健康检查异常: {e}")
        return False

def main():
    print("🧪 ASR-LLM-TTS API快速测试")
    print("=" * 40)
    
    tests = [
        ("健康检查", test_health_api),
        ("聊天功能", test_chat_api),
        ("TTS合成", test_tts_api),
    ]
    
    results = []
    for name, test_func in tests:
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 40)
    print("测试结果汇总:")
    passed = 0
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
        if result:
            passed += 1
    
    print(f"\n通过率: {passed}/{len(results)} ({passed/len(results)*100:.1f}%)")
    
    if passed == len(results):
        print("\n🎉 所有API测试通过！可以在浏览器中正常使用。")
    else:
        print("\n⚠️  部分API存在问题，请检查应用日志。")

if __name__ == "__main__":
    main()
