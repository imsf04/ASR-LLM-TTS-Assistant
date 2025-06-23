"""
智能VAD音频处理器
基于WebRTC VAD实现语音活动检测和断点判断
"""

import webrtcvad
import logging
import time
from collections import deque
from typing import Optional, Callable

logger = logging.getLogger(__name__)

class VADProcessor:
    """智能VAD音频处理器"""
    
    def __init__(self, 
                 sample_rate: int = 16000,
                 vad_mode: int = 3,
                 frame_duration_ms: int = 20,
                 speech_threshold: float = 0.5,
                 silence_threshold: float = 1.0):
        """
        初始化VAD处理器
        
        Args:
            sample_rate: 音频采样率
            vad_mode: VAD敏感度模式 (0-3, 数字越大越敏感)
            frame_duration_ms: VAD检测帧长度（毫秒）
            speech_threshold: 判断为语音的阈值（语音帧占比）
            silence_threshold: 判断语音结束的静音时间（秒）
        """
        self.sample_rate = sample_rate
        self.vad_mode = vad_mode
        self.frame_duration_ms = frame_duration_ms
        self.speech_threshold = speech_threshold
        self.silence_threshold = silence_threshold
        
        # 计算帧大小
        self.frame_size = int(sample_rate * frame_duration_ms / 1000)
        self.frame_bytes = self.frame_size * 2  # 16位音频，每样本2字节
        
        # 初始化VAD
        self.vad = webrtcvad.Vad(vad_mode)
        
        # 状态变量
        self.is_speaking = False
        self.speech_frames = []
        self.audio_buffer = bytearray()
        self.last_speech_time = 0
        self.last_silence_time = 0
        
        # 回调函数
        self.on_speech_start: Optional[Callable] = None
        self.on_speech_end: Optional[Callable[[bytes], None]] = None
        self.on_voice_activity: Optional[Callable[[bool], None]] = None
        
        logger.info(f"VAD处理器初始化: 采样率={sample_rate}Hz, 模式={vad_mode}, 帧长={frame_duration_ms}ms")
    
    def process_audio_chunk(self, audio_data: bytes) -> None:
        """
        处理音频数据块
        
        Args:
            audio_data: 音频数据（16位PCM格式）
        """
        try:
            # 添加到缓冲区
            self.audio_buffer.extend(audio_data)
            
            # 处理完整的VAD帧
            while len(self.audio_buffer) >= self.frame_bytes:
                frame = bytes(self.audio_buffer[:self.frame_bytes])
                self.audio_buffer = self.audio_buffer[self.frame_bytes:]
                
                self._process_vad_frame(frame)
                
        except Exception as e:
            logger.error(f"音频处理错误: {e}")
    
    def _process_vad_frame(self, frame: bytes) -> None:
        """处理单个VAD帧"""
        try:
            current_time = time.time()
            
            # VAD检测
            is_speech = self.vad.is_speech(frame, self.sample_rate)
            
            # 通知语音活动状态
            if self.on_voice_activity:
                self.on_voice_activity(is_speech)
            
            if is_speech:
                self.last_speech_time = current_time
                
                if not self.is_speaking:
                    # 语音开始
                    logger.info("检测到语音开始")
                    self.is_speaking = True
                    self.speech_frames = []
                    
                    if self.on_speech_start:
                        self.on_speech_start()
                
                # 收集语音帧
                self.speech_frames.append(frame)
                
            else:
                # 静音帧
                if self.is_speaking:
                    # 检查是否应该结束语音
                    silence_duration = current_time - self.last_speech_time
                    
                    if silence_duration >= self.silence_threshold:
                        # 语音结束
                        logger.info(f"检测到语音结束，静音时长: {silence_duration:.2f}秒")
                        self.is_speaking = False
                        
                        if self.speech_frames and self.on_speech_end:
                            # 合并所有语音帧
                            full_audio = b''.join(self.speech_frames)
                            self.on_speech_end(full_audio)
                        
                        self.speech_frames = []
                
        except Exception as e:
            logger.error(f"VAD帧处理错误: {e}")
    
    def check_audio_chunk_activity(self, audio_data: bytes) -> bool:
        """
        检查音频块的语音活动（批量检测）
        参考示例代码的实现方式
        
        Args:
            audio_data: 音频数据
            
        Returns:
            是否检测到语音活动
        """
        try:
            speech_frame_count = 0
            total_frames = 0
            
            # 分成20ms帧进行检测
            frame_bytes = int(self.sample_rate * 0.02) * 2  # 20ms帧大小
            
            for i in range(0, len(audio_data), frame_bytes):
                frame = audio_data[i:i + frame_bytes]
                
                if len(frame) == frame_bytes:
                    total_frames += 1
                    
                    if self.vad.is_speech(frame, self.sample_rate):
                        speech_frame_count += 1
            
            if total_frames == 0:
                return False
            
            # 计算语音帧占比
            speech_ratio = speech_frame_count / total_frames
            
            return speech_ratio > self.speech_threshold
            
        except Exception as e:
            logger.error(f"批量VAD检测错误: {e}")
            return False
    
    def reset(self):
        """重置处理器状态"""
        self.is_speaking = False
        self.speech_frames = []
        self.audio_buffer = bytearray()
        self.last_speech_time = 0
        self.last_silence_time = 0
        logger.info("VAD处理器状态已重置")
    
    def set_callbacks(self, 
                     on_speech_start: Optional[Callable] = None,
                     on_speech_end: Optional[Callable[[bytes], None]] = None,
                     on_voice_activity: Optional[Callable[[bool], None]] = None):
        """设置回调函数"""
        self.on_speech_start = on_speech_start
        self.on_speech_end = on_speech_end
        self.on_voice_activity = on_voice_activity
