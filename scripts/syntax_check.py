#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语法检查和快速修复验证
"""

def test_imports():
    """测试所有导入"""
    try:
        from backend.asr_service import ASRService
        print("✅ ASR服务导入成功")
        
        from backend.tts_service import TTSService
        print("✅ TTS服务导入成功")
        
        import app_simple
        print("✅ 应用主文件导入成功")
        
        return True
    except Exception as e:
        print(f"❌ 导入失败: {e}")
        return False

def test_basic_functionality():
    """测试基础功能"""
    try:
        # 测试配置类
        class Config:
            DASHSCOPE_API_KEY = "test_key"
            ASR_MODEL = "paraformer-realtime-v1"
            TTS_MODEL = "cosyvoice-v2"
        
        config = Config()
        
        # 测试ASR服务创建
        from backend.asr_service import ASRService
        asr_service = ASRService(config)
        print("✅ ASR服务创建成功")
        
        # 测试TTS服务创建
        from backend.tts_service import TTSService
        tts_service = TTSService(config)
        print("✅ TTS服务创建成功")
        
        return True
    except Exception as e:
        print(f"❌ 功能测试失败: {e}")
        return False

def main():
    print("🔧 ASR-LLM-TTS 语法和功能检查")
    print("=" * 40)
    
    # 测试导入
    import_ok = test_imports()
    print()
    
    # 测试基础功能
    if import_ok:
        func_ok = test_basic_functionality()
    else:
        func_ok = False
    
    print("\n" + "=" * 40)
    print("检查结果:")
    print(f"导入测试: {'✅ 通过' if import_ok else '❌ 失败'}")
    print(f"功能测试: {'✅ 通过' if func_ok else '❌ 失败'}")
    
    if import_ok and func_ok:
        print("\n🎉 所有检查通过！ASR语法错误已修复。")
        print("应用现在应该可以正常运行了。")
    else:
        print("\n⚠️  仍有问题需要解决。")

if __name__ == "__main__":
    main()
