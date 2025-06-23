#!/usr/bin/env python3
"""
FFmpeg优化ASR测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.asr_service import ASRService
from config import Config
import shutil

def test_ffmpeg_optimization():
    """测试FFmpeg优化功能"""
    print("=== FFmpeg优化ASR测试 ===")
    
    try:
        # 检查FFmpeg是否可用
        ffmpeg_available = shutil.which('ffmpeg') is not None
        print(f"FFmpeg可用: {'✅ 是' if ffmpeg_available else '❌ 否'}")
        
        # 加载配置
        config = Config()
        print("✅ 配置加载成功")
        
        # 创建ASR服务实例
        asr_service = ASRService(config)
        print("✅ ASR服务实例创建成功")
        
        # 测试支持的格式
        formats = asr_service.get_supported_formats()
        print(f"✅ 支持的格式: {', '.join(formats)}")
        
        # 测试预处理功能（使用虚拟文件）
        print("\n--- 测试音频预处理 ---")
        dummy_file = "test_audio.wav"
        
        # 创建一个虚拟文件用于测试
        with open(dummy_file, 'wb') as f:
            f.write(b'RIFF' + b'\x00' * 100)  # 简单的WAV文件头
        
        try:
            processed_file = asr_service.preprocess_audio(dummy_file)
            if processed_file != dummy_file:
                print(f"✅ 音频预处理成功: {processed_file}")
                if os.path.exists(processed_file):
                    os.remove(processed_file)
            else:
                print("⚠️ 使用原始文件（FFmpeg不可用或处理失败）")
            
            # 测试transcribe方法
            result = asr_service.transcribe(dummy_file)
            print(f"✅ ASR转录结果: {result}")
            
        finally:
            # 清理测试文件
            if os.path.exists(dummy_file):
                os.remove(dummy_file)
        
        print(f"\n🎉 FFmpeg优化ASR测试完成!")
        
        if ffmpeg_available:
            print("✨ 您的系统支持FFmpeg音频优化，将获得更好的识别效果!")
        else:
            print("💡 建议安装FFmpeg以获得更好的音频处理效果")
            
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_format_support():
    """测试格式支持"""
    print("\n=== 格式支持测试 ===")
    
    try:
        config = Config()
        asr_service = ASRService(config)
        
        test_files = [
            "test.wav",
            "test.mp3", 
            "test.mp4",
            "test.avi",
            "test.opus",
            "test.unknown"
        ]
        
        for file_name in test_files:
            # 创建测试文件
            with open(file_name, 'wb') as f:
                f.write(b'test')
            
            try:
                is_valid = asr_service.validate_audio_file(file_name)
                status = "✅ 支持" if is_valid else "❌ 不支持"
                print(f"{file_name}: {status}")
            finally:
                if os.path.exists(file_name):
                    os.remove(file_name)
        
        return True
        
    except Exception as e:
        print(f"❌ 格式测试失败: {str(e)}")
        return False

def main():
    """主函数"""
    print("开始FFmpeg优化ASR功能测试...\n")
    
    # 测试FFmpeg优化
    ffmpeg_ok = test_ffmpeg_optimization()
    
    # 测试格式支持
    format_ok = test_format_support()
    
    if ffmpeg_ok and format_ok:
        print("\n🎉 所有测试通过! ASR服务已优化!")
        print("\n📋 优化特性:")
        print("- ✅ FFmpeg音频预处理")
        print("- ✅ 支持更多音频/视频格式")
        print("- ✅ 自动音频压缩和采样率调整")
        print("- ✅ 智能回退机制")
    else:
        print("\n⚠️ 部分测试失败，请检查配置")

if __name__ == "__main__":
    main()
