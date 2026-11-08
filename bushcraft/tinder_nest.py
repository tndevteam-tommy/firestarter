"""
Firestarter - Tinder Nest & Breathing Dynamics
Implements Section 3.3:
Breathing mechanic ('F' key), rhythmic oxygen pulses, and flame ignition at T > 550°C.
"""

import math
from typing import Dict, Any, Optional
from firestarter.config import (
    TEMP_TINDER_IGNITION, BREATH_O2_FRACTION,
    BREATH_OPTIMAL_VELOCITY, BREATH_MAX_VELOCITY, BREATH_MIN_VELOCITY
)

class TinderNest:
    def __init__(
        self,
        material: str = "cedar_shavings",
        dry_mass_g: float = 25.0,
        moisture: float = 0.08,
        has_ember: bool = False,
        ember_temp_c: float = 0.0
    ):
        self.material = material
        self.dry_mass_g = dry_mass_g
        self.moisture = moisture
        self.has_ember = has_ember
        self.core_temp = ember_temp_c if has_ember else 20.0
        
        self.is_flaming = False
        self.is_destroyed = False
        self.flame_height = 0.0
        self.smoke_density = 0.0
        self.glow_intensity = 0.0
        self.breath_cooldown = 0.0

    def insert_ember(self, ember_temp: float):
        """Transfers ember into center of tinder nest."""
        self.has_ember = True
        self.core_temp = max(380.0, ember_temp)
        self.glow_intensity = 0.4

    def update(self, dt: float, ambient_temp: float = 20.0):
        if not self.has_ember or self.is_destroyed:
            self.glow_intensity = 0.0
            return

        if self.is_flaming:
            self.flame_height = min(0.35, self.flame_height + 0.1 * dt)
            self.core_temp = min(800.0, self.core_temp + 50.0 * dt)
            self.dry_mass_g = max(0.0, self.dry_mass_g - 2.5 * dt)
            if self.dry_mass_g <= 1.0:
                self.is_flaming = False
                self.has_ember = False
                self.is_destroyed = True
            return

        # Without breath, ember slowly smolders or dissipates
        # Ambient natural convective heat loss
        cool_rate = 15.0 * dt
        # Natural oxygen draw keeps slow smolder
        smolder_gain = 8.0 * (1.0 - self.moisture) * dt
        
        self.core_temp = max(ambient_temp, self.core_temp - cool_rate + smolder_gain)
        
        # Ember dying out
        if self.core_temp < 150.0:
            self.has_ember = False
            self.glow_intensity = 0.0

        self.glow_intensity = max(0.1, min(1.0, (self.core_temp - 200.0) / 400.0))
        self.smoke_density = max(0.1, min(1.0, (self.core_temp - 180.0) / 300.0))

    def blow(self, breath_velocity: float, dt: float) -> Dict[str, Any]:
        """
        Player presses 'F' key to deliver a breath puff.
        - Too weak: dQ/dt < 0
        - Too strong: blows ember dust away!
        - Optimal rhythm: elevates temperature > 550°C -> FLAME!
        """
        if not self.has_ember or self.is_destroyed:
            return {"status": "no_ember", "is_flaming": False}

        if breath_velocity > BREATH_MAX_VELOCITY:
            # Overblown!
            self.has_ember = False
            self.is_destroyed = True
            self.glow_intensity = 0.0
            return {"status": "blown_out", "reason": "Breath too strong! Ember scattered into the wind.", "is_flaming": False}

        if breath_velocity < BREATH_MIN_VELOCITY:
            # Weak puff: ambient cooling dominates
            cooling = 25.0 * dt
            self.core_temp = max(20.0, self.core_temp - cooling)
            status = "too_weak"
        elif breath_velocity <= BREATH_OPTIMAL_VELOCITY + 0.8:
            # Optimal deep rhythmic puff!
            # Oxygen rushes in: combustion rate jumps
            heat_gain = (120.0 + 80.0 * (breath_velocity / BREATH_OPTIMAL_VELOCITY)) * (1.0 - self.moisture) * dt
            self.core_temp += heat_gain
            self.glow_intensity = min(1.0, self.glow_intensity + 0.3)
            status = "optimal"
        else:
            # Harsh puff: cooling begins to catch up
            heat_gain = 40.0 * dt
            cooling = 35.0 * dt
            self.core_temp += (heat_gain - cooling)
            status = "too_strong"

        # Ignition into open flame threshold: T > 550°C
        if self.core_temp >= TEMP_TINDER_IGNITION and not self.is_flaming:
            self.is_flaming = True
            self.flame_height = 0.15
            status = "ignited"

        return {
            "status": status,
            "core_temp": self.core_temp,
            "glow_intensity": self.glow_intensity,
            "is_flaming": self.is_flaming,
            "smoke_density": self.smoke_density
        }
