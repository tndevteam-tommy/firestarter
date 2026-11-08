"""
Firestarter - Bow Drill Friction Physics & Coal Formation
Implements Section 3.1:
P = mu * F_N * omega * r_spindle
V-notch wood dust char accumulation & ember formation at T > 380°C
"""

import math
import numpy as np
from typing import Tuple, Optional, Dict, Any
from firestarter.config import (
    TEMP_EMBER_FORMATION, CP_DRY_WOOD, CP_CHARCOAL,
    BOW_DRILL_FRICTION_MU_RANGE, BOW_DRILL_FORCE_RANGE,
    BOW_DRILL_OMEGA_RANGE, BOW_DRILL_SPINDLE_RADIUS
)

class BowDrillSystem:
    def __init__(
        self,
        hearthboard_dry_mass: float = 0.12,
        hearthboard_moisture: float = 0.08,
        spindle_radius: float = BOW_DRILL_SPINDLE_RADIUS,
        spindle_moisture: float = 0.07,
        has_v_notch: bool = False,
        cordage_condition: float = 1.0 # 0.0 to 1.0
    ):
        # 5 physical components:
        # 1. Bow, 2. Cordage, 3. Spindle, 4. Hearthboard, 5. Bearing Block
        self.spindle_radius = spindle_radius
        self.hearthboard_moisture = hearthboard_moisture
        self.spindle_moisture = spindle_moisture
        self.has_v_notch = has_v_notch
        self.cordage_condition = cordage_condition
        
        # Friction socket state
        self.socket_temp = 20.0             # °C
        self.wood_dust_mass = 0.0           # grams of charred wood dust
        self.dust_char_fraction = 0.0       # 0.0 to 1.0 charring level
        self.has_ember = False
        self.ember_mass = 0.0               # grams
        self.ember_temp = 20.0              # °C
        self.stroke_direction = 1           # 1 = forward, -1 = backward
        self.stroke_distance = 0.0          # meters traveled this stroke
        self.total_strokes = 0
        self.is_smoking = False

    def carve_v_notch(self) -> bool:
        """Player carves a 45-degree wedge into hearthboard edge using pocket knife."""
        self.has_v_notch = True
        return True

    def calculate_friction_power(
        self,
        normal_force_n: float,
        angular_velocity_rad_s: float,
        friction_mu: float = 0.55
    ) -> float:
        """
        P = mu * F_N * omega * r_spindle
        """
        mu = max(BOW_DRILL_FRICTION_MU_RANGE[0], min(BOW_DRILL_FRICTION_MU_RANGE[1], friction_mu))
        f_n = max(0.0, normal_force_n)
        omega = max(0.0, angular_velocity_rad_s)
        
        # Damp wood has lower friction and absorbs heat into steam
        moisture_penalty = max(0.4, 1.0 - (self.hearthboard_moisture + self.spindle_moisture) * 1.5)
        
        return mu * f_n * omega * self.spindle_radius * moisture_penalty

    def stroke(
        self,
        stroke_length_m: float,
        stroke_speed_m_s: float,
        downward_force_n: float,
        dt: float
    ) -> Dict[str, Any]:
        """
        Executes bow drill stroking motion.
        """
        if self.cordage_condition <= 0.05:
            return {"success": False, "reason": "Cordage snapped! Need to twist new bark cordage."}

        # Convert linear bow stroke velocity to spindle angular velocity
        # omega = v_bow / r_spindle
        omega = stroke_speed_m_s / max(0.005, self.spindle_radius)
        omega = min(BOW_DRILL_OMEGA_RANGE[1], max(BOW_DRILL_OMEGA_RANGE[0], omega))
        
        f_n = min(BOW_DRILL_FORCE_RANGE[1], max(BOW_DRILL_FORCE_RANGE[0], downward_force_n))
        power = self.calculate_friction_power(f_n, omega)
        
        # Cordage wear
        cordage_wear = 0.0004 * (f_n / 50.0) * (omega / 15.0) * dt
        self.cordage_condition = max(0.0, self.cordage_condition - cordage_wear)
        
        # Heat socket (localized contact mass ~ 1.5 grams of wood)
        contact_mass = 0.0015 # kg
        c_p = CP_DRY_WOOD
        heat_energy = power * dt
        
        # If damp, clamp near 100°C until dry
        avg_moisture = 0.5 * (self.hearthboard_moisture + self.spindle_moisture)
        if self.socket_temp >= 100.0 and avg_moisture > 0.02:
            # Boil off moisture
            water_loss = (heat_energy / 2.26e6) / contact_mass
            self.hearthboard_moisture = max(0.01, self.hearthboard_moisture - water_loss)
            self.spindle_moisture = max(0.01, self.spindle_moisture - water_loss)
            self.socket_temp = min(110.0, self.socket_temp + 2.0 * dt)
        else:
            # Heat climbs rapidly
            cooling = 4.5 * (self.socket_temp - 20.0) * dt
            net_energy = max(0.0, heat_energy - cooling)
            self.socket_temp += net_energy / (contact_mass * c_p)

        # Generate fine wood dust from abrasive friction
        dust_generated = 0.015 * (f_n / 50.0) * (omega / 15.0) * dt # grams
        if self.has_v_notch:
            self.wood_dust_mass += dust_generated
        
        # Pyrolysis and charring of wood dust at T > 200°C
        self.is_smoking = (self.socket_temp >= 200.0)
        if self.socket_temp >= 220.0:
            char_increase = 0.15 * ((self.socket_temp - 200.0) / 180.0) * dt
            self.dust_char_fraction = min(1.0, self.dust_char_fraction + char_increase)

        # Coal / Ember formation condition (T > 380°C, V-notch present, charred dust accumulated)
        if (
            self.has_v_notch
            and self.socket_temp >= TEMP_EMBER_FORMATION
            and self.dust_char_fraction >= 0.70
            and self.wood_dust_mass >= 0.08
            and not self.has_ember
        ):
            self.has_ember = True
            self.ember_mass = min(0.15, self.wood_dust_mass)
            self.ember_temp = self.socket_temp
            
        if self.has_ember:
            # Ember self-sustains smoldering
            self.ember_temp = max(350.0, self.ember_temp)

        return {
            "success": True,
            "power_watts": power,
            "socket_temp": self.socket_temp,
            "dust_mass_g": self.wood_dust_mass,
            "char_level": self.dust_char_fraction,
            "has_ember": self.has_ember,
            "ember_temp": self.ember_temp if self.has_ember else 0.0,
            "cordage_condition": self.cordage_condition,
            "is_smoking": self.is_smoking
        }

    def extract_ember(self) -> Optional[float]:
        """Transfers glowing coal ember from V-notch into tinder nest."""
        if not self.has_ember:
            return None
        ember_t = self.ember_temp
        self.has_ember = False
        self.wood_dust_mass = 0.0
        self.dust_char_fraction = 0.0
        return ember_t
