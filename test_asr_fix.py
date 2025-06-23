#!/usr/bin/env python3
"""
测试修复后的ASR调用
"""

import os
import sys
import logging
import numpy as np
import wave
import tempfile
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_asr_with_wav():
    """测试ASR服务与WAV文件"""
    logger.info("测试ASR服务与WAV音频...")
    
    try:
        from backend.asr_service import ASRService
        
        # 创建配置
        class Config:
            DASHSCOPE_API_KEY = os.getenv('DASHSCOPE_API_KEY')
            ASR_MODEL = os.getenv('ASR_MODEL', 'paraformer-realtime-v2')
        
        config = Config()
        asr_service = ASRService(config)
        
        # 生成测试音频数据（正弦波）
        sample_rate = 16000
        duration = 2.0  # 2秒
        samples = int(sample_rate * duration)
        
        # 生成音频信号
        t = np.linspace(0, duration, samples)
        frequency = 440  # A4音符
        audio_signal = np.sin(2 * np.pi * frequency * t) * 0.5
        
        # 转换为16位PCM
        audio_16bit = (audio_signal * 32767).astype(np.int16)
        audio_bytes = audio_16bit.tobytes()
        
        # 创建WAV文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            temp_path = tmp_file.name
            
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)  # 单声道
                wav_file.setsampwidth(2)  # 16位音频
                wav_file.setframerate(sample_rate)  # 16kHz采样率
                wav_file.writeframes(audio_bytes)
        
        logger.info(f"创建测试WAV文件: {temp_path}")
        
        # 测试ASR调用
        try:
            transcription = asr_service.transcribe(temp_path)
            logger.info(f"ASR转录结果: {transcription}")
            
            if transcription:
                logger.info("✓ ASR调用成功")
            else:
                logger.warning("✗ ASR返回空结果（可能是因为测试音频不包含语音）")
        
        except Exception as e:
            logger.error(f"✗ ASR调用失败: {e}")
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_path):
                os.remove(temp_path)
                logger.info("清理临时文件")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")

def test_wav_creation():
    """测试WAV文件创建"""
    logger.info("测试WAV文件创建...")
    
    try:
        # 生成测试音频数据
        sample_rate = 16000
        duration = 1.0  # 1秒
        samples = int(sample_rate * duration)
        
        # 生成噪音信号（模拟语音）
        audio_data = np.random.randint(-1000, 1000, samples, dtype=np.int16)
        audio_bytes = audio_data.tobytes()
        
        # 创建WAV文件
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
            temp_path = tmp_file.name
            
            with wave.open(temp_path, 'wb') as wav_file:
                wav_file.setnchannels(1)
                wav_file.setsampwidth(2)
                wav_file.setframerate(sample_rate)
                wav_file.writeframes(audio_bytes)
        
        # 验证WAV文件
        with wave.open(temp_path, 'rb') as wav_file:
            frames = wav_file.getnframes()
            sample_rate_read = wav_file.getframerate()
            channels = wav_file.getnchannels()
            sampwidth = wav_file.getsampwidth()
            
            logger.info(f"WAV文件信息:")
            logger.info(f"  - 帧数: {frames}")
            logger.info(f"  - 采样率: {sample_rate_read}Hz")
            logger.info(f"  - 声道数: {channels}")
            logger.info(f"  - 采样宽度: {sampwidth}字节")
            logger.info(f"  - 时长: {frames/sample_rate_read:.2f}秒")
        
        logger.info("✓ WAV文件创建和读取成功")
        
        # 清理
        os.remove(temp_path)
        
    except Exception as e:
        logger.error(f"✗ WAV文件测试失败: {e}")

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("ASR修复验证测试")
    logger.info("=" * 50)
    
    try:
        # 测试WAV创建
        test_wav_creation()
        print()
        
        # 测试ASR调用
        test_asr_with_wav()
        
        logger.info("所有测试完成!")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        sys.exit(1)
