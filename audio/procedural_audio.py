"""
Firestarter - Procedural Audio & ASMR Sensory Design Engine
Implements Section 9 of the Technical Design Specification:
Procedural synthesis of combustion roar, pine resin bursts, steam hisses,
crisp whittling foley, bow drill squeaks, breathy blowing, wind, and rain on tarp.
"""

import math
import numpy as np
import wave
import io
import os
from typing import Dict, Optional

class ProceduralAudioEngine:
    @staticmethod
    def synth_resin_pop(duration: float = 0.08, sample_rate: int = 22050) -> bytes:
        """High-frequency pine resin pocket popping from steam bursts inside cells."""
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        freq = float(np.random.uniform(1900.0, 3200.0))
        # Resonant pop ping
        tone = np.sin(2 * np.pi * freq * t) * np.exp(-t * 90.0)
        # Crackle noise burst
        noise = np.random.uniform(-0.6, 0.6, n_samples) * np.exp(-t * 140.0)
        signal = np.clip((tone * 0.7 + noise * 0.5) * 0.8, -1.0, 1.0)
        return ProceduralAudioEngine._to_wav_bytes(signal, sample_rate)

    @staticmethod
    def synth_steam_hiss(duration: float = 1.2, sample_rate: int = 22050) -> bytes:
        """Continuous fine hiss of boiling moisture escaping wood pore channels."""
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        white_noise = np.random.uniform(-1.0, 1.0, n_samples)
        # High-pass filter
        hiss = white_noise - np.convolve(white_noise, np.ones(6)/6.0, mode='same')
        # Gentle bubbling modulation
        mod = 0.6 + 0.3 * np.sin(2 * np.pi * 4.5 * t) + 0.1 * np.sin(2 * np.pi * 11.0 * t)
        signal = np.clip(hiss * mod * 0.35, -1.0, 1.0)
        return ProceduralAudioEngine._to_wav_bytes(signal, sample_rate)

    @staticmethod
    def synth_combustion_roar(duration: float = 2.0, sample_rate: int = 22050) -> bytes:
        """Low-frequency thermal updraft roar and air vacuum draw."""
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, n_samples)
        # Low-pass filter emulation
        smooth = np.convolve(noise, np.ones(30)/30.0, mode='same')
        # Deep sub-bass rumbles (55 Hz, 82 Hz, 110 Hz)
        rumble = 0.5 * np.sin(2 * np.pi * 55.0 * t) + 0.3 * np.sin(2 * np.pi * 82.0 * t) + 0.2 * np.sin(2 * np.pi * 110.0 * t)
        signal = np.clip((smooth * 2.2 + rumble * 0.4) * 0.45, -1.0, 1.0)
        return ProceduralAudioEngine._to_wav_bytes(signal, sample_rate)

    @staticmethod
    def synth_whittling(duration: float = 0.28, sample_rate: int = 22050) -> bytes:
        """Crisp slicing and curling of dry cedar shavings ribbon."""
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        noise = np.random.uniform(-0.9, 0.9, n_samples)
        scrape = noise - np.convolve(noise, np.ones(10)/10.0, mode='same')
        env = (np.sin(np.pi * t / duration) ** 2.2)
        signal = np.clip(scrape * env * 0.55, -1.0, 1.0)
        return ProceduralAudioEngine._to_wav_bytes(signal, sample_rate)

    @staticmethod
    def synth_friction_squeak(duration: float = 0.35, sample_rate: int = 22050) -> bytes:
        """Rhythmic friction squeak and groan of hardwood dowel under heavy load."""
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        freq = 520.0 + 280.0 * np.sin(2 * np.pi * 9.0 * t)
        tone = np.sin(2 * np.pi * freq * t) + 0.4 * np.sin(2 * np.pi * freq * 2.0 * t)
        groan = np.random.uniform(-0.25, 0.25, n_samples)
        env = np.sin(np.pi * t / duration) ** 1.4
        signal = np.clip((tone + groan) * env * 0.45, -1.0, 1.0)
        return ProceduralAudioEngine._to_wav_bytes(signal, sample_rate)

    @staticmethod
    def synth_breath_blowing(duration: float = 0.75, intensity: float = 1.0, sample_rate: int = 22050) -> bytes:
        """Breathy blowing audio with dynamic pitch response to velocity."""
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, n_samples)
        # Bandpass filter
        bp = np.convolve(noise, np.ones(12)/12.0, mode='same') - np.convolve(noise, np.ones(40)/40.0, mode='same')
        env = np.sin(np.pi * t / duration) ** 1.8
        signal = np.clip(bp * env * min(1.2, intensity) * 0.6, -1.0, 1.0)
        return ProceduralAudioEngine._to_wav_bytes(signal, sample_rate)

    @staticmethod
    def synth_wind_ambient(duration: float = 2.5, sample_rate: int = 22050) -> bytes:
        """Mountain pass wind whistling."""
        n_samples = int(duration * sample_rate)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        noise = np.random.uniform(-1.0, 1.0, n_samples)
        smooth = np.convolve(noise, np.ones(25)/25.0, mode='same')
        whistle = 0.25 * np.sin(2 * np.pi * (220.0 + 40.0 * np.sin(2 * np.pi * 0.4 * t)) * t)
        signal = np.clip((smooth * 1.5 + whistle) * 0.35, -1.0, 1.0)
        return ProceduralAudioEngine._to_wav_bytes(signal, sample_rate)

    @staticmethod
    def synth_rain_on_tarp(duration: float = 2.0, sample_rate: int = 22050) -> bytes:
        """Patter of raindrops drummed across stretched polyethylene tarp canvas."""
        n_samples = int(duration * sample_rate)
        signal = np.zeros(n_samples, dtype=float)
        # Drop impacts
        num_drops = int(35 * duration)
        for _ in range(num_drops):
            idx = np.random.randint(0, n_samples - 400)
            drop_len = 350
            t_drop = np.linspace(0, 0.015, drop_len)
            freq = np.random.uniform(300.0, 650.0)
            signal[idx:idx+drop_len] += np.sin(2 * np.pi * freq * t_drop) * np.exp(-t_drop * 350.0) * np.random.uniform(0.3, 0.7)
            
        signal = np.clip(signal * 0.5, -1.0, 1.0)
        return ProceduralAudioEngine._to_wav_bytes(signal, sample_rate)

    @staticmethod
    def _to_wav_bytes(signal: np.ndarray, sample_rate: int) -> bytes:
        int_signal = (signal * 32767.0).astype(np.int16)
        buf = io.BytesIO()
        with wave.open(buf, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(int_signal.tobytes())
        return buf.getvalue()

    @staticmethod
    def generate_and_save_all_assets(output_dir: str):
        """Generates and writes all audio WAV assets to disk."""
        os.makedirs(output_dir, exist_ok=True)
        generators = {
            "resin_pop.wav": ProceduralAudioEngine.synth_resin_pop,
            "steam_hiss.wav": ProceduralAudioEngine.synth_steam_hiss,
            "combustion_roar.wav": ProceduralAudioEngine.synth_combustion_roar,
            "whittle.wav": ProceduralAudioEngine.synth_whittling,
            "friction_squeak.wav": ProceduralAudioEngine.synth_friction_squeak,
            "breath.wav": ProceduralAudioEngine.synth_breath_blowing,
            "wind.wav": ProceduralAudioEngine.synth_wind_ambient,
            "rain_tarp.wav": ProceduralAudioEngine.synth_rain_on_tarp,
        }
        for filename, gen_fn in generators.items():
            filepath = os.path.join(output_dir, filename)
            data = gen_fn()
            with open(filepath, "wb") as f:
                f.write(data)
            print(f"Generated asset: {filename} ({len(data)} bytes)")
