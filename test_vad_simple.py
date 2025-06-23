#!/usr/bin/env python3
"""
简单的VAD处理器测试脚本
"""

import os
import sys
import logging
import numpy as np
from backend.vad_processor import VADProcessor

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_vad_processor():
    """测试VAD处理器"""
    logger.info("开始测试VAD处理器...")
    
    # 创建VAD处理器
    vad_processor = VADProcessor(
        sample_rate=16000,
        vad_mode=3,
        frame_duration_ms=20,
        speech_threshold=0.3,
        silence_threshold=1.0
    )
    
    # 测试回调函数
    def on_speech_start():
        logger.info("✓ 语音开始回调被触发")
    
    def on_speech_end(audio_data):
        logger.info(f"✓ 语音结束回调被触发，音频长度: {len(audio_data)} bytes")
    
    def on_voice_activity(is_active):
        logger.info(f"✓ 语音活动回调: {'活跃' if is_active else '静音'}")
    
    # 设置回调
    vad_processor.set_callbacks(
        on_speech_start=on_speech_start,
        on_speech_end=on_speech_end,
        on_voice_activity=on_voice_activity
    )
    
    # 生成测试音频数据
    sample_rate = 16000
    duration = 2.0  # 2秒
    samples = int(sample_rate * duration)
    
    # 生成简单的音频信号（正弦波）
    t = np.linspace(0, duration, samples)
    frequency = 440  # A4音符
    audio_signal = np.sin(2 * np.pi * frequency * t) * 0.5
    
    # 转换为16位PCM
    audio_16bit = (audio_signal * 32767).astype(np.int16)
    audio_bytes = audio_16bit.tobytes()
    
    logger.info(f"测试音频数据: {len(audio_bytes)} bytes, 时长: {duration}秒")
    
    # 分块处理音频
    chunk_size = int(sample_rate * 0.1) * 2  # 100ms chunk
    
    for i in range(0, len(audio_bytes), chunk_size):
        chunk = audio_bytes[i:i+chunk_size]
        if len(chunk) > 0:
            logger.info(f"处理音频块: {len(chunk)} bytes")
            vad_processor.process_audio_chunk(chunk)
    
    # 测试批量检测
    logger.info("测试批量VAD检测...")
    is_speech = vad_processor.check_audio_chunk_activity(audio_bytes)
    logger.info(f"批量VAD检测结果: {'检测到语音' if is_speech else '未检测到语音'}")
    
    # 重置状态
    vad_processor.reset()
    logger.info("VAD处理器状态已重置")
    
    logger.info("VAD处理器测试完成!")

def test_simple_vad():
    """简单的webrtcvad测试"""
    try:
        import webrtcvad
        logger.info("测试webrtcvad基本功能...")
        
        vad = webrtcvad.Vad(3)
        
        # 生成测试音频帧
        sample_rate = 16000
        frame_duration_ms = 20
        frame_size = int(sample_rate * frame_duration_ms / 1000)
        
        # 生成静音帧
        silence_frame = np.zeros(frame_size, dtype=np.int16).tobytes()
        
        # 生成噪音帧
        noise_frame = (np.random.randint(-1000, 1000, frame_size, dtype=np.int16)).tobytes()
        
        # 测试静音
        try:
            is_speech_silence = vad.is_speech(silence_frame, sample_rate)
            logger.info(f"静音检测结果: {'语音' if is_speech_silence else '静音'}")
        except Exception as e:
            logger.error(f"静音检测错误: {e}")
        
        # 测试噪音
        try:
            is_speech_noise = vad.is_speech(noise_frame, sample_rate)
            logger.info(f"噪音检测结果: {'语音' if is_speech_noise else '静音'}")
        except Exception as e:
            logger.error(f"噪音检测错误: {e}")
            
        logger.info("webrtcvad基本功能测试完成!")
        
    except Exception as e:
        logger.error(f"webrtcvad测试失败: {e}")

if __name__ == "__main__":
    logger.info("=" * 50)
    logger.info("VAD处理器测试程序")
    logger.info("=" * 50)
    
    try:
        # 首先测试基本的webrtcvad功能
        test_simple_vad()
        print()
        
        # 然后测试我们的VAD处理器
        test_vad_processor()
        
        logger.info("所有测试完成!")
        
    except Exception as e:
        logger.error(f"测试失败: {e}")
        sys.exit(1)
