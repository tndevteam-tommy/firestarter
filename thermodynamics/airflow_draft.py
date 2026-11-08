"""
Firestarter - Airflow, Convective Chimney & Draft Vacuum
Implements Section 2.4 of the Technical Design Specification:
U_draft = C_d * sqrt(2 * g * H * (T_int - T_amb) / T_int)
P_base = P_amb - 0.5 * rho_air * U_draft^2
"""

import math
from typing import List, Tuple
from firestarter.config import (
    GRAVITY, AIR_DENSITY_STP, STANDARD_PRESSURE,
    O2_AMBIENT_FRACTION, O2_FLAMING_MIN, O2_CHOKED_MAX,
    CHOKE_GAP_METERS, BREATH_O2_FRACTION,
    BREATH_OPTIMAL_VELOCITY, BREATH_MAX_VELOCITY, BREATH_MIN_VELOCITY
)

class AirflowDraftSolver:
    @staticmethod
    def calculate_draft_velocity(
        c_d: float,
        height_meters: float,
        internal_temp_c: float,
        ambient_temp_c: float
    ) -> float:
        """
        Solves thermal updraft velocity via Stack Effect:
        U_draft = C_d * sqrt(2 * g * H * (T_int - T_amb) / T_int)
        Temperatures converted to Kelvin.
        """
        t_int_k = internal_temp_c + 273.15
        t_amb_k = ambient_temp_c + 273.15
        
        if t_int_k <= t_amb_k or height_meters <= 0.0 or c_d <= 0.0:
            return 0.0
            
        delta_t = t_int_k - t_amb_k
        val = 2.0 * GRAVITY * height_meters * (delta_t / t_int_k)
        if val <= 0.0:
            return 0.0
            
        return c_d * math.sqrt(val)

    @staticmethod
    def calculate_base_vacuum(
        ambient_pressure_pa: float,
        draft_velocity: float,
        air_density: float = AIR_DENSITY_STP
    ) -> Tuple[float, float]:
        """
        Calculates low-pressure vacuum zone at base:
        P_base = P_amb - 0.5 * rho_air * U_draft^2
        Returns (P_base, vacuum_draw_pa).
        """
        vacuum_draw = 0.5 * air_density * (draft_velocity ** 2)
        p_base = max(0.0, ambient_pressure_pa - vacuum_draw)
        return p_base, vacuum_draw

    @staticmethod
    def evaluate_structure_airflow(
        log_positions: List[Tuple[float, float, float]],
        log_radii: List[float],
        internal_temp_c: float,
        ambient_temp_c: float,
        structure_type: str = "custom"
    ) -> Tuple[float, float, float, float]:
        """
        Evaluates fire structure clearances and returns:
        (c_d, updraft_velocity, oxygen_fraction, base_vacuum)
        """
        if not log_positions:
            return 0.6, 0.0, O2_AMBIENT_FRACTION, 0.0
            
        ys = [p[1] for p in log_positions]
        height = max(0.05, max(ys) - min(ys) + 0.1)
        
        # Determine minimum clearance between log centers minus radii
        min_clearance = 1.0
        n = len(log_positions)
        if n >= 2:
            for i in range(n):
                for j in range(i + 1, n):
                    dx = log_positions[i][0] - log_positions[j][0]
                    dz = log_positions[i][2] - log_positions[j][2]
                    dist = math.sqrt(dx * dx + dz * dz)
                    clearance = dist - (log_radii[i] + log_radii[j])
                    if clearance < min_clearance:
                        min_clearance = clearance
        else:
            min_clearance = 0.1  # Single log has open clearance

        # Discharge coefficient determined by log clearance
        if min_clearance < CHOKE_GAP_METERS:
            # Choked layout: edge-to-edge < 2 cm -> C_d -> 0, O2 drops < 10%
            ratio = max(0.0, min_clearance / CHOKE_GAP_METERS)
            c_d = 0.05 * ratio
            oxygen_fraction = 0.06 + 0.03 * ratio
        else:
            # Open pathways
            if structure_type == "teepee":
                # High vertical chimney
                c_d = 0.85
                height = max(height, 0.45)
            elif structure_type == "log_cabin":
                # Balanced cross-hatch intake
                c_d = 0.75
            elif structure_type == "lean_to":
                c_d = 0.65
            elif structure_type == "swedish_torch":
                c_d = 0.70
            elif structure_type == "star":
                c_d = 0.60
            else:
                c_d = min(0.8, 0.3 + 0.5 * min(1.0, min_clearance / 0.15))
                
            oxygen_fraction = O2_AMBIENT_FRACTION

        # Stack effect calculation
        u_draft = AirflowDraftSolver.calculate_draft_velocity(
            c_d, height, internal_temp_c, ambient_temp_c
        )
        p_base, vacuum_draw = AirflowDraftSolver.calculate_base_vacuum(
            STANDARD_PRESSURE, u_draft
        )
        
        # Draft vacuum actively draws oxygen into the ember bed
        if oxygen_fraction > O2_CHOKED_MAX:
            oxygen_boost = min(0.02, vacuum_draw * 0.001)
            oxygen_fraction = min(0.22, oxygen_fraction + oxygen_boost)
            
        return c_d, u_draft, oxygen_fraction, vacuum_draw

    @staticmethod
    def calculate_breath_effect(
        breath_velocity: float,
        ember_temp_c: float,
        ambient_temp_c: float = 20.0
    ) -> Tuple[float, float, bool]:
        """
        Blowing dynamics ('F' key):
        Returns (net_thermal_power_watts, oxygen_available, is_blown_away)
        - Weak: dQ/dt < 0 (ambient convective cooling dominates)
        - Too strong (> 6 m/s): blows char dust away
        - Optimal (1.5 - 4.0 m/s): elevates ember temperature > 550°C
        """
        if breath_velocity <= 0.05:
            return 0.0, O2_AMBIENT_FRACTION, False
            
        if breath_velocity > BREATH_MAX_VELOCITY:
            # Overblown: destroys ember core
            return -250.0, BREATH_O2_FRACTION, True
            
        # Convective cooling from breath air (at ~34°C body temp)
        t_breath_c = 34.0
        delta_t = ember_temp_c - t_breath_c
        # Heat transfer coeff: h = 10.45 - v + 10 * sqrt(v)
        h_conv = 10.0 + 15.0 * math.sqrt(breath_velocity)
        # Small ember surface ~ 0.0003 m^2
        area_ember = 0.0003
        q_cool = h_conv * area_ember * delta_t
        
        # Combustion oxidation reaction rate boost from forced oxygen
        # Reaction rate increases with velocity up to optimal
        if breath_velocity < BREATH_MIN_VELOCITY:
            # Weak puff: cooling exceeds combustion gain
            q_combust = 0.6 * q_cool
        elif breath_velocity <= BREATH_OPTIMAL_VELOCITY:
            # Rhythmic optimal breath elevates temperature
            intensity = breath_velocity / BREATH_OPTIMAL_VELOCITY
            q_combust = q_cool * (1.8 + 1.2 * intensity)
        else:
            # Excessive but not blowing away yet: cooling starts catching up
            excess = (breath_velocity - BREATH_OPTIMAL_VELOCITY) / (BREATH_MAX_VELOCITY - BREATH_OPTIMAL_VELOCITY)
            q_combust = q_cool * max(0.8, 2.5 - 1.8 * excess)
            
        net_power = q_combust - q_cool
        return net_power, BREATH_O2_FRACTION, False
