"""
Firestarter - Moisture Gradient & Diffusion Engine
Implements Section 2.2:
dM/dt = D_m * (Nabla^2 M) - R_evap(T)
"""

import math
from typing import Tuple
from firestarter.config import H_VAP_WATER, CP_WATER, TEMP_WATER_BOILING

class MoistureDiffusionEngine:
    @staticmethod
    def calculate_internal_diffusion(
        m_surface: float,
        m_core: float,
        d_m: float,
        radius: float,
        dt: float
    ) -> Tuple[float, float, float]:
        """
        Solves radial diffusion between core and surface:
        J = D_m * (M_core - M_surface) / (0.5 * radius)^2
        Returns (new_m_surface, new_m_core, diffusion_flux).
        """
        effective_dist = max(0.005, radius * 0.5)
        # Diffusion rate constant
        k_diff = d_m / (effective_dist ** 2)
        
        # Stability clamp on explicit Euler
        max_rate = 0.45 / max(1e-4, dt)
        k_diff = min(k_diff, max_rate)
        
        flux = k_diff * (m_core - m_surface) * dt
        
        new_surf = max(0.0, m_surface + flux)
        new_core = max(0.0, m_core - flux)
        
        return new_surf, new_core, flux

    @staticmethod
    def calculate_evaporation(
        temperature: float,
        moisture: float,
        available_heat_watts: float,
        layer_dry_mass: float,
        dt: float
    ) -> Tuple[float, float, float, float]:
        """
        Calculates moisture evaporation:
        - Absorbs 2260 kJ/kg (H_VAP_WATER).
        - Clamps temperature near 100°C until dry.
        Returns: (new_moisture, evaporated_water_kg, steam_rate_kg_s, remaining_heat_watts)
        """
        if moisture <= 0.0 or layer_dry_mass <= 0.0:
            return 0.0, 0.0, 0.0, available_heat_watts

        water_mass = moisture * layer_dry_mass
        
        if temperature < 60.0:
            # Low-temp ambient evaporation
            evap_rate = 1e-6 * max(0.0, temperature - 10.0) * water_mass
            evap_kg = min(water_mass, evap_rate * dt)
            new_m = max(0.0, (water_mass - evap_kg) / layer_dry_mass)
            return new_m, evap_kg, evap_kg / max(1e-6, dt), available_heat_watts

        # High-temp boiling evaporation (T >= 100°C)
        energy_available = max(0.0, available_heat_watts * dt)
        evap_capacity_kg = energy_available / H_VAP_WATER
        
        evap_kg = min(water_mass, evap_capacity_kg)
        energy_spent = evap_kg * H_VAP_WATER
        remaining_energy = max(0.0, energy_available - energy_spent)
        remaining_watts = remaining_energy / max(1e-6, dt)
        
        new_water_mass = max(0.0, water_mass - evap_kg)
        new_m = new_water_mass / layer_dry_mass
        steam_rate = evap_kg / max(1e-6, dt)
        
        return new_m, evap_kg, steam_rate, remaining_watts

    @staticmethod
    def calculate_environmental_uptake(
        m_surface: float,
        m_core: float,
        is_on_ground: bool,
        is_tarp_covered: bool,
        rain_intensity: float,
        ground_humidity: float,
        ambient_humidity: float,
        is_sponge: bool,
        dt: float
    ) -> Tuple[float, float]:
        """
        Calculates moisture intake from environmental exposure:
        - Capillary ground absorption if touching dirt (J_ground)
        - Rain wetting if not covered by tarp (P_rain)
        - Punk wood acts as a sponge with high absorption
        """
        surf_gain = 0.0
        core_gain = 0.0
        
        sponge_mult = 3.5 if is_sponge else 1.0
        
        # Rain precipitation
        if not is_tarp_covered and rain_intensity > 0.0:
            rain_rate = rain_intensity * 0.001 * sponge_mult
            surf_gain += rain_rate * dt
        
        # Ground capillary transfer
        if is_on_ground:
            ground_rate = 0.0002 * ground_humidity * sponge_mult
            surf_gain += ground_rate * dt
            core_gain += (ground_rate * 0.4) * dt
            
        # Ambient humidity equilibrium
        target_m = ambient_humidity * 0.25
        if ambient_humidity > 0.8:
            surf_gain += 1e-5 * (target_m - m_surface) * dt
            
        new_surf = min(1.5, max(0.0, m_surface + surf_gain))
        new_core = min(1.5, max(0.0, m_core + core_gain))
        
        return new_surf, new_core
