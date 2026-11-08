"""
Firestarter - Hand Drill & Stone Spindle System
Implements Section 3.2:
Longer spindle (40-60 cm) rotated directly between hands or stone socket,
rapid downward hand travel and player stamina expenditure.
"""

import math
from typing import Dict, Any, Optional
from firestarter.config import TEMP_EMBER_FORMATION, CP_DRY_WOOD

class HandDrillSystem:
    def __init__(
        self,
        spindle_length_cm: float = 50.0,
        spindle_diameter_cm: float = 1.8,
        hearthboard_moisture: float = 0.08,
        has_stone_handle: bool = False
    ):
        self.spindle_length_cm = spindle_length_cm
        self.spindle_radius_m = (spindle_diameter_cm / 2.0) / 100.0
        self.hearthboard_moisture = hearthboard_moisture
        self.has_stone_handle = has_stone_handle
        
        self.hand_height_cm = spindle_length_cm * 0.9
        self.socket_temp = 20.0
        self.wood_dust_mass = 0.0
        self.char_fraction = 0.0
        self.has_ember = False
        self.ember_temp = 0.0
        self.stamina_cost_rate = 12.0  # stamina / sec
        
    def drill_step(
        self,
        hand_spin_speed_rad_s: float,
        player_stamina: float,
        dt: float
    ) -> Dict[str, Any]:
        """
        Executes one drill cycle between palms or stone handle.
        Hands travel downward along the spindle.
        """
        if player_stamina <= 0.0:
            return {"success": False, "reason": "Exhausted! Rest to recover stamina."}

        # Downward pressure from hands or stone handle
        downward_force = 45.0 if self.has_stone_handle else 35.0
        omega = max(0.0, min(24.0, hand_spin_speed_rad_s))
        
        # Friction power P = mu * F_N * omega * r
        mu = 0.52
        moisture_mult = max(0.4, 1.0 - self.hearthboard_moisture * 1.5)
        power = mu * downward_force * omega * self.spindle_radius_m * moisture_mult
        
        # Hand travel down the spindle (requires resetting hands to the top)
        travel_speed = 4.0 if not self.has_stone_handle else 1.0 # cm/s
        self.hand_height_cm -= travel_speed * dt
        
        reset_required = False
        if self.hand_height_cm < 8.0:
            self.hand_height_cm = self.spindle_length_cm * 0.9
            reset_required = True
            
        # Socket heating
        contact_mass = 0.0012 # kg
        c_p = CP_DRY_WOOD
        heat_energy = power * dt
        cooling = 3.8 * (self.socket_temp - 20.0) * dt
        net_energy = max(0.0, heat_energy - cooling)
        self.socket_temp += net_energy / (contact_mass * c_p)
        
        # Dust and charring
        self.wood_dust_mass += 0.012 * (omega / 15.0) * dt
        if self.socket_temp >= 200.0:
            self.char_fraction = min(1.0, self.char_fraction + 0.12 * dt)
            
        # Ember formation
        if (
            self.socket_temp >= TEMP_EMBER_FORMATION
            and self.char_fraction >= 0.70
            and self.wood_dust_mass >= 0.07
            and not self.has_ember
        ):
            self.has_ember = True
            self.ember_temp = self.socket_temp

        return {
            "success": True,
            "power_watts": power,
            "socket_temp": self.socket_temp,
            "dust_mass": self.wood_dust_mass,
            "char_fraction": self.char_fraction,
            "has_ember": self.has_ember,
            "hand_height_cm": self.hand_height_cm,
            "reset_required": reset_required,
            "stamina_spent": self.stamina_cost_rate * dt
        }

    def extract_ember(self) -> Optional[float]:
        if not self.has_ember:
            return None
        t = self.ember_temp
        self.has_ember = False
        self.wood_dust_mass = 0.0
        return t
