import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer, AudioFormat
import logging
from typing import Optional, Dict, Any
import tempfile
import os

class TTSService:
    """Text-to-Speech service using DashScope CosyVoice"""
    
    def __init__(self, config):
        """
        Initialize TTS service
        
        Args:
            config: Application configuration object
        """
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize DashScope
        dashscope.api_key = config.DASHSCOPE_API_KEY
    
    def synthesize(self, text: str, voice: str = 'longxiaochun_v2') -> bytes:
        """
        Synthesize speech from text
        
        Args:
            text: Text to synthesize
            voice: Voice to use for synthesis
            
        Returns:
            Audio data as bytes
            
        Raises:
            Exception: If synthesis fails
        """
        try:
            self.logger.info(f"Starting TTS synthesis for text: {text[:50]}...")
            
            # Validate text
            if not text or not text.strip():
                raise ValueError("Text cannot be empty")
            
            # Clean text for TTS
            cleaned_text = self._clean_text_for_tts(text)
            
            # Use CosyVoice v2 model and voice
            model = "cosyvoice-v2"
              # Create synthesizer instance with correct format
            try:
                # Try different audio format options
                audio_format = None
                if hasattr(AudioFormat, 'MP3_22050HZ_MONO_16BIT'):
                    audio_format = AudioFormat.MP3_22050HZ_MONO_16BIT
                elif hasattr(AudioFormat, 'MP3_22050_MONO'):
                    audio_format = AudioFormat.MP3_22050_MONO
                elif hasattr(AudioFormat, 'WAV_16000HZ_MONO_16BIT'):
                    audio_format = AudioFormat.WAV_16000HZ_MONO_16BIT
                else:
                    # Use default format
                    audio_format = AudioFormat.MP3_44100HZ_MONO_16BIT if hasattr(AudioFormat, 'MP3_44100HZ_MONO_16BIT') else None
                
                synthesizer = SpeechSynthesizer(
                    model=model,
                    voice=voice,
                    format=audio_format
                )
            except Exception as format_error:
                self.logger.warning(f"Audio format issue, trying without format parameter: {format_error}")
                synthesizer = SpeechSynthesizer(
                    model=model,
                    voice=voice
                )
            
            # Call TTS API
            audio_data = synthesizer.call(cleaned_text)
            
            if audio_data:
                self.logger.info(f"TTS synthesis successful, audio size: {len(audio_data)} bytes")
                return audio_data
            else:
                raise Exception("No audio data received from TTS API")
                
        except Exception as e:
            self.logger.error(f"TTS synthesis failed: {str(e)}")
            raise Exception(f"语音合成失败: {str(e)}")
    
    def synthesize_to_file(self, text: str, output_path: str, voice: str = 'longxiaochun_v2') -> str:
        """
        Synthesize speech and save to file
        
        Args:
            text: Text to synthesize
            output_path: Path to save audio file
            voice: Voice to use for synthesis
            
        Returns:
            Path to saved audio file
        """
        try:
            # Get audio data
            audio_data = self.synthesize(text, voice)
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(audio_data)
            
            self.logger.info(f"Audio saved to: {output_path}")
            return output_path
            
        except Exception as e:
            self.logger.error(f"Failed to save TTS audio: {str(e)}")
            raise
    
    def _clean_text_for_tts(self, text: str) -> str:
        """
        Clean text for TTS processing
        
        Args:
            text: Raw text
            
        Returns:
            Cleaned text suitable for TTS
        """
        import re
        
        # Remove markdown formatting
        text = re.sub(r'[#*`_\[\](){}]', '', text)
        
        # Remove mathematical expressions
        text = re.sub(r'\$.*?\$', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove excessive punctuation
        text = re.sub(r'[!]{2,}', '!', text)
        text = re.sub(r'[?]{2,}', '?', text)
        text = re.sub(r'[.]{3,}', '...', text)
        
        # Trim whitespace
        text = text.strip()
        
        return text
    def get_available_voices(self) -> Dict[str, str]:
        """
        Get available voices for CosyVoice v2
        
        Returns:
            Dictionary mapping voice names to descriptions
        """
        return {
            'longxiaochun_v2': '龙小春 - 女声',
            'longxiaoxia_v2': '龙小夏 - 女声',
            'longwan_v2': '龙万 - 男声',
            'longcheng_v2': '龙城 - 男声',
            'longhua_v2': '龙华 - 男声',
            'longshu_v2': '龙书 - 男声',
            'loongbella_v2': 'Bella - 女声'
        }
    def validate_voice(self, voice: str) -> bool:
        """
        Validate if voice is available
        
        Args:
            voice: Voice name to validate
            
        Returns:
            True if voice is available
        """
        return voice in self.get_available_voices()
    
    def get_voice_info(self, voice: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific voice
        
        Args:
            voice: Voice name
            
        Returns:
            Voice information dictionary
        """
        if not self.validate_voice(voice):
            return None
        
        voice_info = {
            'name': voice,
            'model': self.config.TTS_VOICES[voice],
            'language': 'zh-CN',  # Chinese by default
            'gender': self._get_voice_gender(voice)
        }
        
        return voice_info
    
    def _get_voice_gender(self, voice: str) -> str:
        """
        Get voice gender based on voice name
        
        Args:
            voice: Voice name
            
        Returns:
            Gender string
        """
        # Simple heuristic based on common Chinese voice names
        if 'xiao' in voice.lower():
            if any(char in voice.lower() for char in ['yun', 'meng', 'mei']):
                return 'female'
            elif any(char in voice.lower() for char in ['gang', 'ming', 'bin']):
                return 'male'
        
        return 'unknown'
