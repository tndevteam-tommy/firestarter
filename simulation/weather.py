"""
Firestarter - Weather, Seasons & Environmental Parameters
Implements Section 7.1:
Seasonal parameters, solar radiation, winter wood freezing enthalpy of fusion (334 kJ/kg),
precipitation, and day-night cycle.
"""

from enum import Enum
import math
import numpy as np
from typing import Dict, Any
from firestarter.config import H_FUS_ICE

class Season(Enum):
    SUMMER = "Summer"
    AUTUMN = "Autumn"
    WINTER = "Winter"
    SPRING = "Spring"

class WeatherSystem:
    def __init__(self):
        self.current_season = Season.SUMMER
        self.day_of_season = 1.0
        self.time_of_day_hours = 12.0 # 0.0 to 24.0 (12.0 = noon)
        
        # Environmental state
        self.ambient_temp_c = 28.0
        self.solar_radiation_w_m2 = 920.0
        self.rain_intensity = 0.0 # 0.0 to 1.0
        self.snow_accumulation_m = 0.0
        self.relative_humidity = 0.45
        self.wind_speed_m_s = 2.2
        self.wind_direction_rad = 0.45
        self.wind_vector = np.array([math.cos(0.45), 0.0, math.sin(0.45)]) * 2.2

    def advance_time(self, hours: float):
        """Advances time of day, seasons, and updates weather."""
        self.time_of_day_hours += hours
        days_passed = self.time_of_day_hours // 24.0
        self.time_of_day_hours %= 24.0
        
        self.day_of_season += days_passed
        if self.day_of_season > 90.0:
            # Advance season
            seasons = list(Season)
            idx = (seasons.index(self.current_season) + 1) % len(seasons)
            self.current_season = seasons[idx]
            self.day_of_season = 1.0

        self._update_parameters()

    def _update_parameters(self):
        # Diurnal temperature cycle: peaks at 14:00, lowest at 04:00
        diurnal_factor = math.sin((self.time_of_day_hours - 8.0) * (2.0 * math.pi / 24.0))
        
        if self.current_season == Season.SUMMER:
            base_temp = 30.0
            temp_var = 6.0
            self.solar_radiation_w_m2 = max(0.0, 950.0 * max(0.0, diurnal_factor))
            self.rain_intensity = 0.0 if np.random.random() > 0.15 else 0.4
            self.snow_accumulation_m = 0.0
            self.relative_humidity = 0.38
            
        elif self.current_season == Season.AUTUMN:
            base_temp = 12.0
            temp_var = 5.0
            self.solar_radiation_w_m2 = max(0.0, 500.0 * max(0.0, diurnal_factor))
            # Frequent rain showers
            self.rain_intensity = 0.55 if np.random.random() > 0.4 else 0.0
            self.snow_accumulation_m = 0.0
            self.relative_humidity = 0.78
            
        elif self.current_season == Season.WINTER:
            # Freezing temperatures (-15°C to -2°C)
            base_temp = -8.0
            temp_var = 6.0
            self.solar_radiation_w_m2 = max(0.0, 320.0 * max(0.0, diurnal_factor))
            self.rain_intensity = 0.0
            # Snow accumulation
            self.snow_accumulation_m = min(1.2, self.snow_accumulation_m + 0.02)
            self.relative_humidity = 0.85
            
        else: # SPRING
            base_temp = 15.0
            temp_var = 5.0
            self.solar_radiation_w_m2 = max(0.0, 700.0 * max(0.0, diurnal_factor))
            # Snowmelt saturation
            self.snow_accumulation_m = max(0.0, self.snow_accumulation_m - 0.08)
            self.rain_intensity = 0.3 if np.random.random() > 0.5 else 0.0
            self.relative_humidity = 0.82

        self.ambient_temp_c = base_temp + diurnal_factor * temp_var
        self.wind_speed_m_s = max(0.2, min(8.0, self.wind_speed_m_s + np.random.uniform(-0.3, 0.3)))
        self.wind_vector = np.array([math.cos(self.wind_direction_rad), 0.0, math.sin(self.wind_direction_rad)]) * self.wind_speed_m_s

    def is_freezing(self) -> bool:
        return self.ambient_temp_c < 0.0

    def get_sun_direction(self) -> np.ndarray:
        """3D sun vector for shaders and lighting."""
        angle = (self.time_of_day_hours / 24.0) * 2.0 * math.pi
        sun_y = math.sin(angle)
        sun_x = math.cos(angle)
        sun_z = 0.3
        vec = np.array([sun_x, sun_y, sun_z])
        norm = np.linalg.norm(vec)
        return vec / max(1e-5, norm)
