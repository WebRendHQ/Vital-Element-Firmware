# speaker/init.py
import pygame
from dataclasses import dataclass
from typing import Optional

@dataclass
class SpeakerConfig:
    sample_rate: int = 44100
    channels: int = 2
    buffer: int = 2048
    volume: float = 1.0

class Speaker:
    def __init__(self, config: SpeakerConfig):
        self.config = config
        pygame.mixer.init(
            frequency=config.sample_rate,
            channels=config.channels,
            buffer=config.buffer
        )
        pygame.mixer.music.set_volume(config.volume)
        
    def play_file(self, file_path: str, loops: int = 0):
        """Play audio file"""
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play(loops)
        
    def stop(self):
        """Stop audio playback"""
        pygame.mixer.music.stop()
        
    def set_volume(self, volume: float):
        """Set volume (0.0-1.0)"""
        pygame.mixer.music.set_volume(max(0.0, min(1.0, volume)))
        
    def is_playing(self) -> bool:
        """Check if audio is currently playing"""
        return pygame.mixer.music.get_busy()
        
    def cleanup(self):
        """Cleanup pygame mixer"""
        pygame.mixer.quit()