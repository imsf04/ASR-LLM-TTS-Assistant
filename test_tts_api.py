#!/usr/bin/env python3
"""
快速测试TTS功能
"""
import requests
import json
import base64

def test_tts():
    """测试TTS API"""
    url = "http://127.0.0.1:5000/tts"
    
    data = {
        "text": "你好，我是AI语音助手，TTS功能测试正常！",
        "voice": "longwan_v2"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            if result.get('success'):
                print("✓ TTS测试成功")
                print(f"音频数据长度: {len(result.get('audio', ''))}")
                
                # 可选：保存音频到文件
                if 'audio' in result:
                    audio_data = base64.b64decode(result['audio'])
                    with open('test_tts_output.wav', 'wb') as f:
                        f.write(audio_data)
                    print("✓ 音频已保存到 test_tts_output.wav")
                return True
            else:
                print(f"✗ TTS API返回错误: {result}")
                return False
        else:
            print(f"✗ HTTP错误: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"✗ TTS测试失败: {e}")
        return False

if __name__ == "__main__":
    print("=== TTS功能测试 ===")
    success = test_tts()
    print(f"测试结果: {'成功' if success else '失败'}")
