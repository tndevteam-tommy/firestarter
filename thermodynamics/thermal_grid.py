"""
Firestarter - ThermodynamicGrid & ThermalConvectionSolver
Implements Section 2 and Section 8.1:
Finite-difference heat transfer grid, conduction, convection plumes, and radiation.
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Optional

from firestarter.config import THERMAL_DT, STEFAN_BOLTZMANN
from firestarter.thermodynamics.combustion_body import CombustionBody, CombustionStage
from firestarter.thermodynamics.airflow_draft import AirflowDraftSolver

class ThermalConvectionSolver:
    """
    Finite-difference 3D convection currents and draft vector solver.
    Computes heat exchange between adjacent combustion bodies in the fire structure.
    """
    @staticmethod
    def solve_inter_body_heat_transfer(
        bodies: List[CombustionBody],
        dt: float,
        draft_velocity: float
    ):
        """
        Solves conduction, upward convection plumes, and radiation between all bodies.
        """
        n = len(bodies)
        if n < 2:
            return

        for i in range(n):
            b1 = bodies[i]
            p1 = b1.position
            t1 = b1.t_surface
            r1 = b1.radius

            for j in range(i + 1, n):
                b2 = bodies[j]
                p2 = b2.position
                t2 = b2.t_surface
                r2 = b2.radius

                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]  # vertical displacement
                dz = p2[2] - p1[2]
                dist = math.sqrt(dx * dx + dy * dy + dz * dz)
                touching_dist = r1 + r2
                
                # 1. Contact Conduction
                if dist <= (touching_dist + 0.02):
                    # Intersecting or touching logs
                    contact_area = 2.0 * min(r1, r2) * 0.1
                    k_avg = 0.5 * (b1.props.thermal_conductivity + b2.props.thermal_conductivity)
                    q_cond = (k_avg * contact_area * (t1 - t2)) / max(0.01, dist)
                    # Apply conduction
                    b1.apply_external_heat(-q_cond, dt)
                    b2.apply_external_heat(q_cond, dt)

                # 2. Convective Heat Plume
                # If b1 is lower than b2 (dy > 0) and b1 is hot, convective updraft heats b2
                if dy > 0.02 and dist < 0.6:
                    horizontal_dist = math.sqrt(dx * dx + dz * dz)
                    if horizontal_dist < 0.25:
                        # Inside the rising thermal chimney cone
                        cone_factor = max(0.0, 1.0 - (horizontal_dist / 0.25))
                        plume_power = b1.heat_flux_output * 0.25 * cone_factor * min(2.0, draft_velocity)
                        b2.apply_external_heat(plume_power, dt)
                elif dy < -0.02 and dist < 0.6:
                    # b2 is lower than b1
                    horizontal_dist = math.sqrt(dx * dx + dz * dz)
                    if horizontal_dist < 0.25:
                        cone_factor = max(0.0, 1.0 - (horizontal_dist / 0.25))
                        plume_power = b2.heat_flux_output * 0.25 * cone_factor * min(2.0, draft_velocity)
                        b1.apply_external_heat(plume_power, dt)

                # 3. Radiation View Factor Exchange
                if dist < 0.8:
                    view_factor = min(0.4, (r1 * r2) / (dist * dist + 0.01))
                    t1_k = t1 + 273.15
                    t2_k = t2 + 273.15
                    q_rad = view_factor * STEFAN_BOLTZMANN * (t1_k**4 - t2_k**4) * 0.8
                    b1.apply_external_heat(-q_rad, dt)
                    b2.apply_external_heat(q_rad, dt)


class ThermodynamicGrid:
    """
    Manages the 20 Hz thermal simulation grid, fuel bodies, airflow, and heat metrics.
    """
    def __init__(self, bounds_size: float = 2.0, grid_resolution: int = 16):
        self.bounds_size = bounds_size
        self.grid_resolution = grid_resolution
        self.voxel_size = bounds_size / grid_resolution
        
        self.bodies: List[CombustionBody] = []
        self.ambient_temp = 20.0
        self.wind_speed = 0.5
        self.internal_temp = 20.0
        self.core_coal_temp = 20.0
        
        # Structure airflow state
        self.structure_type = "freeform"
        self.c_d = 0.6
        self.draft_velocity = 0.0
        self.oxygen_fraction = 0.2095
        self.base_vacuum = 0.0
        
        # Energy accounting for economic credits
        self.total_energy_produced_joules = 0.0
        self.total_fuel_consumed_kg = 0.0
        self.current_heat_flux = 0.0

    def add_body(self, body: CombustionBody):
        if body not in self.bodies:
            self.bodies.append(body)

    def remove_body(self, body: CombustionBody):
        if body in self.bodies:
            self.bodies.remove(body)

    def update(self, dt: float, ambient_temp: float = 20.0, wind_speed: float = 0.5):
        self.ambient_temp = ambient_temp
        self.wind_speed = wind_speed
        
        # Clean up inert ash bodies if completely gone
        active_bodies = [b for b in self.bodies if not (b.stage == CombustionStage.INERT_ASH and b.t_surface < ambient_temp + 5.0)]
        self.bodies = active_bodies
        
        if not self.bodies:
            self.internal_temp = ambient_temp
            self.core_coal_temp = ambient_temp
            self.draft_velocity = 0.0
            self.oxygen_fraction = 0.2095
            self.current_heat_flux = 0.0
            return

        # 1. Calculate internal core combustion chamber temperature
        hot_temps = [b.t_surface for b in self.bodies if b.stage in (CombustionStage.FLAMING, CombustionStage.CHAR_OXIDATION, CombustionStage.PYROLYSIS)]
        if hot_temps:
            self.internal_temp = float(np.mean(hot_temps))
            self.core_coal_temp = float(max(hot_temps))
        else:
            self.internal_temp = float(np.mean([b.t_surface for b in self.bodies]))
            self.core_coal_temp = float(max([b.t_surface for b in self.bodies]))

        # 2. Evaluate Structure Airflow and Convective Draft
        positions = [tuple(b.position) for b in self.bodies]
        radii = [b.radius for b in self.bodies]
        
        c_d, u_draft, o2, p_base = AirflowDraftSolver.evaluate_structure_airflow(
            positions, radii, self.internal_temp, ambient_temp, self.structure_type
        )
        self.c_d = c_d
        self.draft_velocity = u_draft
        self.oxygen_fraction = o2
        self.base_vacuum = p_base

        # 3. Inter-body Heat Transfer (Conduction, Updraft Plumes, Radiation)
        ThermalConvectionSolver.solve_inter_body_heat_transfer(
            self.bodies, dt, self.draft_velocity
        )

        # 4. Step each CombustionBody
        total_heat = 0.0
        fuel_before = sum(b.dry_mass + b.char_mass for b in self.bodies)
        
        for body in self.bodies:
            body.update(
                dt=dt,
                ambient_temp=ambient_temp,
                oxygen_fraction=self.oxygen_fraction,
                draft_velocity=self.draft_velocity,
                wind_speed=wind_speed
            )
            total_heat += body.heat_flux_output

        fuel_after = sum(b.dry_mass + b.char_mass for b in self.bodies)
        fuel_consumed = max(0.0, fuel_before - fuel_after)
        
        self.current_heat_flux = total_heat
        self.total_energy_produced_joules += total_heat * dt
        self.total_fuel_consumed_kg += fuel_consumed

    def blow_into_fire(self, breath_velocity: float) -> Tuple[float, bool]:
        """Player breathes into the fire structure ('F' key)."""
        power_boost, o2, blown_away = AirflowDraftSolver.calculate_breath_effect(
            breath_velocity, self.core_coal_temp, self.ambient_temp
        )
        # Apply breath to glowing bodies
        for body in self.bodies:
            body.blow(breath_velocity)
            if body.stage in (CombustionStage.CHAR_OXIDATION, CombustionStage.PYROLYSIS, CombustionStage.AMBIENT):
                if not blown_away:
                    body.apply_external_heat(power_boost, THERMAL_DT)
                    body.t_surface = max(self.ambient_temp, body.t_surface)
                else:
                    # Overblown: cools or blows out ember
                    body.apply_external_heat(-200.0, THERMAL_DT)
        return power_boost, blown_away
