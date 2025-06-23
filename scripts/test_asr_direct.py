#!/usr/bin/env python3
"""
直接测试ASR服务类
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.asr_service import ASRService
from config import Config

def test_asr_service():
    """测试ASR服务类"""
    print("=== 测试ASR服务类 ===")
    
    try:
        # 加载配置
        config = Config()
        print("✅ 配置加载成功")
        
        # 创建ASR服务实例
        asr_service = ASRService(config)
        print("✅ ASR服务实例创建成功")
        
        # 测试transcribe方法（使用占位符）
        result = asr_service.transcribe("test.wav")
        print(f"✅ ASR转录结果: {result}")
        
        # 测试支持的格式
        formats = asr_service.get_supported_formats()
        print(f"✅ 支持的格式: {formats}")
        
        print("\n🎉 ASR服务类测试成功!")
        return True
        
    except Exception as e:
        print(f"❌ ASR服务类测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_asr_service()
