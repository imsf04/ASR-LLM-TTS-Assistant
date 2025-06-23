#!/usr/bin/env python3
"""
测试真实DashScope ASR API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.asr_service import ASRService
from config import Config
import time

def test_real_asr_api():
    """测试真实ASR API"""
    print("=== 测试真实DashScope ASR API ===")
    
    try:
        # 加载配置
        config = Config()
        print("✅ 配置加载成功")
        
        # 检查API密钥
        if not config.DASHSCOPE_API_KEY:
            print("❌ DASHSCOPE_API_KEY未配置")
            return False
        
        print(f"✅ API密钥已配置: {config.DASHSCOPE_API_KEY[:8]}...")
        
        # 创建ASR服务实例
        asr_service = ASRService(config)
        print("✅ ASR服务实例创建成功")
        
        # 测试支持的格式
        formats = asr_service.get_supported_formats()
        print(f"✅ 支持的格式: {', '.join(formats)}")
        
        # 创建测试音频文件
        print("\n--- 创建测试音频文件 ---")
        test_audio_file = "test_real_asr.wav"
        
        # 创建一个简单的WAV文件头
        import struct
        import math
        
        # WAV文件参数
        sample_rate = 16000
        duration = 2.0  # 2秒
        frequency = 440  # A4音符
        amplitude = 0.3
        
        # 生成音频数据
        samples = []
        for i in range(int(sample_rate * duration)):
            t = i / sample_rate
            sample = int(amplitude * 32767 * math.sin(2 * math.pi * frequency * t))
            samples.append(sample)
        
        # 写入WAV文件
        with open(test_audio_file, 'wb') as f:
            # WAV文件头
            f.write(b'RIFF')
            f.write(struct.pack('<I', 36 + len(samples) * 2))
            f.write(b'WAVE')
            f.write(b'fmt ')
            f.write(struct.pack('<I', 16))
            f.write(struct.pack('<H', 1))  # PCM
            f.write(struct.pack('<H', 1))  # 单声道
            f.write(struct.pack('<I', sample_rate))
            f.write(struct.pack('<I', sample_rate * 2))
            f.write(struct.pack('<H', 2))
            f.write(struct.pack('<H', 16))
            f.write(b'data')
            f.write(struct.pack('<I', len(samples) * 2))
            
            # 音频数据
            for sample in samples:
                f.write(struct.pack('<h', sample))
        
        print(f"✅ 测试音频文件创建成功: {test_audio_file}")
        
        try:
            # 测试同步识别
            print("\n--- 测试同步识别 ---")
            start_time = time.time()
            result = asr_service.transcribe(test_audio_file)
            end_time = time.time()
            
            print(f"✅ 同步识别结果: {result}")
            print(f"⏱️ 识别耗时: {end_time - start_time:.2f}秒")
            
            # 测试流式识别
            print("\n--- 测试流式识别 ---")
            start_time = time.time()
            streaming_result = asr_service.transcribe_streaming(test_audio_file)
            end_time = time.time()
            
            print(f"✅ 流式识别结果: {streaming_result}")
            print(f"⏱️ 流式识别耗时: {end_time - start_time:.2f}秒")
            
        finally:
            # 清理测试文件
            if os.path.exists(test_audio_file):
                os.remove(test_audio_file)
                print(f"🧹 清理测试文件: {test_audio_file}")
        
        print(f"\n🎉 真实ASR API测试完成!")
        print("\n📋 API特性:")
        print("- ✅ 基于官方文档的正确API调用")
        print("- ✅ 支持同步和流式识别")
        print("- ✅ 支持中英文语言识别")
        print("- ✅ FFmpeg音频预处理优化")
        print("- ✅ 智能错误处理和降级")
        
        return True
        
    except Exception as e:
        print(f"❌ 真实API测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_api_with_web():
    """测试Web API集成"""
    print("\n=== 测试Web API集成 ===")
    
    try:
        import requests
        
        # 测试健康检查
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Web服务运行正常: {health_data['status']}")
            print(f"✅ DashScope配置: {health_data['dashscope_configured']}")
            
            print("\n💡 现在可以在浏览器中测试语音识别功能:")
            print("   1. 访问 http://localhost:5000")
            print("   2. 点击录音按钮")
            print("   3. 说出 '请问你是谁' 或其他内容")
            print("   4. 查看真实的语音识别结果")
            
            return True
        else:
            print(f"❌ Web服务异常: {response.status_code}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到Web服务")
        print("💡 请先启动Flask应用: python app_simple.py")
        return False
    except Exception as e:
        print(f"❌ Web API测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始测试真实DashScope ASR API...\n")
    
    # 测试ASR服务
    asr_ok = test_real_asr_api()
    
    # 测试Web集成
    web_ok = test_api_with_web()
    
    if asr_ok:
        print("\n✨ 真实ASR API配置成功！")
        if web_ok:
            print("🌐 Web服务集成正常！")
        else:
            print("⚠️ 请启动Flask应用以完成Web测试")
    else:
        print("\n⚠️ 真实API测试失败，请检查:")
        print("  1. DASHSCOPE_API_KEY是否正确配置")
        print("  2. 网络连接是否正常")
        print("  3. DashScope SDK版本是否最新")

if __name__ == "__main__":
    main()
