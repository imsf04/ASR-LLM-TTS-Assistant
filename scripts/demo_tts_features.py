#!/usr/bin/env python3
"""
TTS功能演示脚本
展示ASR-LLM-TTS智能助手的语音播报功能
"""

import requests
import json
import base64
import os
import sys
from pathlib import Path

# 设置API基础URL
BASE_URL = "http://localhost:5000"

def test_tts_api():
    """测试TTS API端点"""
    print("🎵 测试TTS语音合成功能...")
    
    # 测试文本
    test_text = "你好，欢迎使用ASR-LLM-TTS智能助手的语音播报功能！"
    
    # 构建请求
    url = f"{BASE_URL}/tts"
    payload = {
        "text": test_text,
        "voice": "longxiaochun_v2"
    }
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                print("✅ TTS API调用成功")
                print(f"📝 合成文本: {test_text}")
                print(f"🎙️ 使用语音: {payload['voice']}")
                
                # 保存音频文件
                audio_data = base64.b64decode(data['audio'])
                output_file = "tts_demo_output.mp3"
                
                with open(output_file, 'wb') as f:
                    f.write(audio_data)
                
                print(f"💾 音频已保存到: {output_file}")
                print(f"📊 音频大小: {len(audio_data)} bytes")
                
                # 尝试播放音频（如果系统支持）
                try_play_audio(output_file)
                
            else:
                print(f"❌ TTS API返回错误: {data.get('error', '未知错误')}")
        else:
            print(f"❌ HTTP请求失败: {response.status_code}")
            print(f"响应内容: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ 连接失败：请确保Flask应用程序正在运行")
        print("💡 提示：运行 'python app_simple.py' 启动服务器")
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")

def try_play_audio(audio_file):
    """尝试播放音频文件"""
    try:
        import pygame
        pygame.mixer.init()
        pygame.mixer.music.load(audio_file)
        pygame.mixer.music.play()
        
        print("🔊 正在播放音频...")
        input("按回车键继续...")
        
    except ImportError:
        print("💡 如需播放音频，请安装pygame: pip install pygame")
    except Exception as e:
        print(f"🔊 无法播放音频: {str(e)}")
        print("💡 可以手动播放生成的音频文件")

def test_chat_with_tts():
    """测试聊天+TTS功能"""
    print("\n💬 测试聊天+TTS功能...")
    
    # 测试问题
    test_message = "你能为我介绍一下TTS语音合成技术吗？"
    
    url = f"{BASE_URL}/chat"
    payload = {"message": test_message}
    
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                ai_response = data['response']
                print("✅ 聊天API调用成功")
                print(f"👤 用户: {test_message}")
                print(f"🤖 AI: {ai_response[:100]}...")
                
                # 对AI回复进行TTS
                print("\n🎵 正在为AI回复生成语音...")
                tts_payload = {
                    "text": ai_response,
                    "voice": "longxiaochun_v2"
                }
                
                tts_response = requests.post(f"{BASE_URL}/tts", json=tts_payload, timeout=30)
                
                if tts_response.status_code == 200:
                    tts_data = tts_response.json()
                    if tts_data.get('success'):
                        audio_data = base64.b64decode(tts_data['audio'])
                        output_file = "chat_response_tts.mp3"
                        
                        with open(output_file, 'wb') as f:
                            f.write(audio_data)
                        
                        print(f"💾 AI回复语音已保存到: {output_file}")
                        try_play_audio(output_file)
                    else:
                        print(f"❌ TTS失败: {tts_data.get('error')}")
                else:
                    print(f"❌ TTS请求失败: {tts_response.status_code}")
            else:
                print(f"❌ 聊天API返回错误: {data.get('error')}")
        else:
            print(f"❌ 聊天请求失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 聊天+TTS测试失败: {str(e)}")

def show_tts_features():
    """展示TTS功能特性"""
    print("🎯 ASR-LLM-TTS智能助手 - TTS功能特性")
    print("=" * 50)
    print("📱 前端功能:")
    print("  • 自动语音播报开关 (左侧边栏)")
    print("  • 手动朗读按钮 (每条AI回复下方)")
    print("  • 语音识别结果自动填入输入框")
    print("  • 一键发送识别内容")
    print()
    print("🔧 技术特性:")
    print("  • 基于阿里云DashScope CosyVoice v2")
    print("  • 支持多种中文语音 (男声/女声)")
    print("  • 高质量音频合成 (MP3格式)")
    print("  • 自动文本清理和优化")
    print()
    print("🎙️ 支持的语音:")
    voices = {
        'longxiaochun_v2': '龙小春 - 女声 (默认)',
        'longxiaoxia_v2': '龙小夏 - 女声',
        'longwan_v2': '龙万 - 男声',
        'longcheng_v2': '龙城 - 男声',
        'longhua_v2': '龙华 - 男声',
        'longshu_v2': '龙书 - 男声',
        'loongbella_v2': 'Bella - 女声'
    }
    
    for voice, desc in voices.items():
        print(f"  • {voice}: {desc}")
    print()

def main():
    """主函数"""
    print("🚀 ASR-LLM-TTS智能助手 - TTS功能演示")
    print("=" * 60)
    
    # 显示功能特性
    show_tts_features()
    
    # 检查服务器状态
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ 服务器运行正常")
        else:
            print("⚠️ 服务器状态异常")
    except:
        print("❌ 无法连接到服务器")
        print("💡 请先启动Flask应用: python app_simple.py")
        return
    
    # 运行测试
    print("\n" + "=" * 60)
    test_tts_api()
    
    print("\n" + "=" * 60)
    test_chat_with_tts()
    
    print("\n" + "=" * 60)
    print("✨ 演示完成！")
    print("💻 访问 http://localhost:5000 体验完整的Web界面")
    print("📚 查看 'TTS功能使用说明.md' 了解详细使用方法")

if __name__ == "__main__":
    main()
