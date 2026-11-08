"""
Firestarter - Forestry Seasoning & Raised Platform Physics
Implements Section 4.2:
Raised platforms eliminate capillary ground water transfer (J_ground = 0),
waterproof tarps shield precipitation (P_rain = 0),
and time dilation cures logs to 12% equilibrium moisture or rots ground logs to punk wood.
"""

import math
import numpy as np
from typing import List, Dict, Any, Optional
from firestarter.thermodynamics.combustion_body import CombustionBody
from firestarter.thermodynamics.wood_properties import WoodSpeciesType

class RaisedDryingRack:
    def __init__(
        self,
        position: np.ndarray,
        has_tarp: bool = False,
        capacity: int = 12
    ):
        self.position = position
        self.has_tarp = has_tarp
        self.capacity = capacity
        self.logs: List[CombustionBody] = []
        
    def add_log(self, log: CombustionBody) -> bool:
        if len(self.logs) >= self.capacity:
            return False
        log.is_on_ground = False
        log.is_tarp_covered = self.has_tarp
        self.logs.append(log)
        return True

    def remove_log(self, log: CombustionBody):
        if log in self.logs:
            self.logs.remove(log)
            log.is_on_ground = True
            log.is_tarp_covered = False

    def equip_tarp(self):
        """Attaches waterproof polyethylene tarp over rack."""
        self.has_tarp = True
        for log in self.logs:
            log.is_tarp_covered = True

    def update_seasoning(
        self,
        days_passed: float,
        season: str = "Summer",
        rain_intensity: float = 0.0,
        ground_humidity: float = 0.6,
        wind_speed: float = 2.0
    ):
        """
        Advances seasoning over days/weeks/seasons.
        """
        # Under tarp on raised platform: J_ground = 0, P_rain = 0
        # Target equilibrium moisture content EMC ~ 12% (0.12) in dry summer
        target_emc = 0.12 if season == "Summer" else 0.16
        
        # Curing rate: ~60 days to reach 12% EMC under tarp in summer
        cure_rate_per_day = 0.015 * (wind_speed / 2.0)
        if season == "Summer":
            cure_rate_per_day *= 1.3
        elif season == "Winter":
            cure_rate_per_day *= 0.4
            
        for log in self.logs:
            # Shielded from rain
            if self.has_tarp:
                # Convective moisture loss toward EMC
                if log.m_surface > target_emc:
                    log.m_surface = max(target_emc, log.m_surface - cure_rate_per_day * days_passed)
                if log.m_core > target_emc:
                    log.m_core = max(target_emc, log.m_core - (cure_rate_per_day * 0.7) * days_passed)
            else:
                # Open rack without tarp: exposed to rain
                if rain_intensity > 0.0:
                    log.m_surface = min(1.2, log.m_surface + rain_intensity * 0.05 * days_passed)
                else:
                    if log.m_surface > target_emc:
                        log.m_surface = max(target_emc, log.m_surface - cure_rate_per_day * days_passed * 0.8)


class GroundSeasoningSimulator:
    """
    Simulates unshielded logs lying directly on forest soil.
    In autumn/winter, ground capillary transfer + rain soaking causes fungal rot,
    decaying hardwood into sponge punk wood (M -> 95%).
    """
    @staticmethod
    def step_ground_log(
        log: CombustionBody,
        days_passed: float,
        season: str,
        rain_intensity: float,
        soil_moisture: float = 0.75
    ):
        if not log.is_on_ground:
            return

        if season in ("Autumn", "Winter"):
            # Ground capillary absorption + rain soaking
            intake = (soil_moisture * 0.02 + rain_intensity * 0.04) * days_passed
            log.m_surface = min(0.95, log.m_surface + intake)
            log.m_core = min(0.95, log.m_core + intake * 0.8)
            
            # Fungal rot colonization over 60+ days
            if log.m_core > 0.75 and not log.is_decayed:
                # Transform to Punk Wood!
                log.species_type = WoodSpeciesType.PUNK_WOOD
                log.is_decayed = True
        else: # Summer
            # Slow surface drying, but damp bottom touching dirt
            if rain_intensity == 0.0:
                log.m_surface = max(0.20, log.m_surface - 0.005 * days_passed)
                # Core stays damp from capillary ground contact
                log.m_core = max(0.50, log.m_core - 0.002 * days_passed)
            else:
                log.m_surface = min(0.90, log.m_surface + rain_intensity * 0.03 * days_passed)
