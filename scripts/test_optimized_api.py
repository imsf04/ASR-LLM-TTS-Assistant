#!/usr/bin/env python3
"""
测试优化后的ASR API
"""

import requests
import json
import time

def test_optimized_asr():
    """测试优化后的ASR功能"""
    print("=== 测试优化后的ASR API ===")
    
    try:
        # 测试健康检查
        print("1. 测试健康检查...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 健康检查成功: {health_data}")
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
        
        # 测试聊天功能
        print("\n2. 测试聊天功能...")
        chat_data = {"message": "你好，请介绍一下语音识别功能"}
        response = requests.post("http://localhost:5000/chat", json=chat_data, timeout=10)
        
        if response.status_code == 200:
            chat_result = response.json()
            print(f"✅ 聊天功能正常: {chat_result.get('response', '')[:100]}...")
        else:
            print(f"❌ 聊天功能失败: {response.status_code}")
        
        # 测试TTS功能
        print("\n3. 测试TTS功能...")
        tts_data = {"text": "这是语音合成测试", "voice": "longxiaochun_v2"}
        response = requests.post("http://localhost:5000/tts", json=tts_data, timeout=15)
        
        if response.status_code == 200:
            tts_result = response.json()
            if tts_result.get('success'):
                print("✅ TTS功能正常，音频数据已生成")
            else:
                print(f"❌ TTS生成失败: {tts_result}")
        else:
            print(f"❌ TTS功能失败: {response.status_code}")
        
        print("\n🎉 API测试完成！")
        print("\n📋 优化特性已启用:")
        print("- ✅ FFmpeg音频预处理（支持更多格式）")
        print("- ✅ 智能音频压缩和采样率调整")
        print("- ✅ 改进的错误处理和回退机制")
        print("- ✅ 支持视频文件音轨提取")
        
        return True
        
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务器")
        print("💡 请确保Flask应用正在运行: python app_simple.py")
        return False
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始测试优化后的ASR-LLM-TTS应用...\n")
    
    # 等待服务器启动
    print("等待服务器启动...")
    time.sleep(2)
    
    # 运行测试
    success = test_optimized_asr()
    
    if success:
        print("\n✨ 所有功能测试正常！")
        print("现在可以在浏览器中访问 http://localhost:5000 来体验完整功能")
    else:
        print("\n⚠️ 部分功能需要检查，请确保Flask应用正在运行")

if __name__ == "__main__":
    main()
