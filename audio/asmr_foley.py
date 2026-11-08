"""
Firestarter - ASMR Foley Manager
Coordinates dynamic multilayered procedural audio with real-time simulation events.
"""

import os
from typing import Dict, Any, Optional

class ASMRFoleyManager:
    def __init__(self, asset_dir: str = "firestarter/assets/audio"):
        self.asset_dir = asset_dir
        self.sounds: Dict[str, Any] = {}
        self.is_pygame_audio_available = False
        
        self._init_audio()

    def _init_audio(self):
        try:
            import pygame
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.is_pygame_audio_available = True
            
            # Load sounds
            for fname in os.listdir(self.asset_dir):
                if fname.endswith(".wav"):
                    name = fname[:-4]
                    path = os.path.join(self.asset_dir, fname)
                    self.sounds[name] = pygame.mixer.Sound(path)
        except Exception:
            # Running in headless or non-audio environment
            self.is_pygame_audio_available = False

    def play(self, sound_name: str, volume: float = 1.0):
        if not self.is_pygame_audio_available or sound_name not in self.sounds:
            return
        snd = self.sounds[sound_name]
        snd.set_volume(max(0.0, min(1.0, volume)))
        snd.play()

    def update_continuous_ambience(
        self,
        core_temp_c: float,
        draft_velocity: float,
        steam_rate_kg_s: float,
        rain_intensity: float,
        wind_speed: float
    ):
        """Dynamic volume adjustments for continuous roar, hiss, and weather."""
        if not self.is_pygame_audio_available:
            return
            
        # Fire roar
        if core_temp_c > 150.0 and "combustion_roar" in self.sounds:
            roar_vol = min(1.0, (core_temp_c - 150.0) / 600.0 * (draft_velocity / 2.0))
            # Handled via channel volume in active mixer
