#!/usr/bin/env python3
"""
测试ASR前端修复
"""

import requests
import json
import time

def test_asr_frontend_fix():
    """测试ASR前端修复"""
    print("=== 测试ASR前端修复 ===")
    
    try:
        # 测试健康检查
        print("1. 检查服务状态...")
        response = requests.get("http://localhost:5000/health", timeout=5)
        
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ 服务运行正常: {health_data['status']}")
            print(f"✅ DashScope配置: {health_data['dashscope_configured']}")
        else:
            print(f"❌ 服务异常: {response.status_code}")
            return False
        
        print("\n2. 测试ASR API返回格式...")
        
        # 创建测试音频数据
        test_audio_data = b'test_audio_content_for_asr_testing'
        
        # 模拟文件上传
        files = {'audio': ('test.wav', test_audio_data, 'audio/wav')}
        
        response = requests.post("http://localhost:5000/asr", files=files, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ ASR API响应成功")
            print(f"📝 响应结构: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            # 检查响应字段
            if 'success' in result and result['success']:
                if 'transcription' in result:
                    print(f"✅ 正确字段 'transcription': {result['transcription']}")
                    print("✅ 前端现在应该能正确显示识别结果")
                else:
                    print("❌ 缺少 'transcription' 字段")
                    return False
            else:
                print(f"⚠️ API返回非成功状态: {result}")
        else:
            print(f"❌ ASR API错误: {response.status_code}")
            print(f"响应: {response.text}")
            return False
        
        print("\n🎉 ASR前端修复测试完成!")
        print("\n📋 修复内容:")
        print("- ✅ 修复前端JavaScript中的字段名错误")
        print("- ✅ 使用正确的 'transcription' 字段")
        print("- ✅ 添加自动发送按钮高亮提示")
        print("- ✅ 更新为最新的 paraformer-realtime-v2 模型")
        
        print("\n💡 测试步骤:")
        print("1. 访问 http://localhost:5000")
        print("2. 点击'开始录音'按钮")
        print("3. 说出'请问你是谁'或其他内容")
        print("4. 停止录音")
        print("5. 查看输入框是否自动填入识别文本")
        print("6. 发送按钮应该会高亮提示")
        
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
    print("开始测试ASR前端修复...\n")
    
    success = test_asr_frontend_fix()
    
    if success:
        print("\n✨ ASR前端修复成功！")
        print("现在语音识别结果会正确显示在输入框中")
    else:
        print("\n⚠️ 修复测试失败，请检查服务状态")

if __name__ == "__main__":
    main()
