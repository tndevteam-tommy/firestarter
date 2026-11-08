"""
Firestarter - CombustionBody Base Class & Four-Stage State Machine
Implements Sections 2.1, 2.2, and 2.3 of the Technical Design Specification.
"""

from enum import Enum
import math
import numpy as np
from typing import Optional, Tuple, Dict, Any

from firestarter.config import (
    H_VAP_WATER, CP_DRY_WOOD, CP_WATER, CP_CHARCOAL,
    CARBON_COMBUSTION_HEAT, STEFAN_BOLTZMANN,
    TEMP_WATER_BOILING, TEMP_PYROLYSIS_START, TEMP_PYROLYSIS_HEMICELLULOSE,
    TEMP_PYROLYSIS_CELLULOSE, TEMP_PYROLYSIS_LIGNIN, TEMP_FLAMING_MIN,
    TEMP_CHAR_GLOW_MIN, TEMP_CHAR_GLOW_MAX, O2_FLAMING_MIN, O2_CHOKED_MAX
)
from firestarter.thermodynamics.wood_properties import (
    WoodSpeciesType, WoodProperties, get_wood_properties
)
from firestarter.thermodynamics.moisture_diffusion import MoistureDiffusionEngine

class CombustionStage(Enum):
    AMBIENT = "Ambient"
    DEHYDRATION = "Dehydration"
    PYROLYSIS = "Pyrolysis"
    FLAMING = "Flaming Combustion"
    CHAR_OXIDATION = "Char Oxidation (Glowing Coals)"
    INERT_ASH = "Inert Ash"

class CombustionBody:
    """
    Every combustive object in the game world inherits from CombustionBody.
    Models four-stage combustion state machine, moisture gradients (surface vs core),
    volatile gasification, char oxidation, and ash insulation.
    """
    def __init__(
        self,
        species: WoodSpeciesType,
        dry_mass: float,
        initial_m_surface: float = 0.15,
        initial_m_core: float = 0.15,
        initial_temp: float = 20.0,
        geometry_type: str = "log",
        position: Optional[np.ndarray] = None,
        orientation: Optional[np.ndarray] = None,
        dimensions: Optional[np.ndarray] = None,
    ):
        self.species_type = species
        self.props: WoodProperties = get_wood_properties(species)
        
        self.dry_mass = max(0.0001, dry_mass)
        self.m_surface = max(0.0, initial_m_surface)
        self.m_core = max(0.0, initial_m_core)
        
        self.t_surface = initial_temp
        self.t_internal = initial_temp
        
        self.geometry_type = geometry_type
        self.position = position if position is not None else np.array([0.0, 0.0, 0.0], dtype=float)
        self.orientation = orientation if orientation is not None else np.array([0.0, 0.0, 0.0], dtype=float)
        # dimensions: [length, radius] or [lx, ly, lz]
        self.dimensions = dimensions if dimensions is not None else np.array([0.4, 0.05], dtype=float)
        
        # Cellular chemical mass pools
        self.char_yield_max = self.dry_mass * self.props.char_yield_fraction
        self.char_mass = self.char_yield_max
        self.volatile_mass = self.dry_mass * (1.0 - self.props.char_yield_fraction - self.props.ash_fraction)
        self.ash_mass = 0.0
        self.accelerant_mass = 0.0
        self.accelerant_type = "none"
        
        # State machine
        self.stage = CombustionStage.AMBIENT
        self.ash_insulation_depth = 0.0    # mm
        self.heat_flux_output = 0.0        # Watts
        self.flame_height = 0.0            # meters
        self.steam_rate = 0.0              # kg/s
        self.smoke_rate = 0.0              # g/s
        
        # Acoustic / ASMR event flags
        self.resin_pop_event = False
        self.hiss_event = False
        self.crackle_factor = 0.0
        
        # Environmental contact flags
        self.is_on_ground = True
        self.is_tarp_covered = False
        self.is_decayed = (species == WoodSpeciesType.PUNK_WOOD)

    @property
    def total_mass(self) -> float:
        """Total physical mass: dry mass + moisture + accelerant + ash."""
        water_mass = (self.m_surface * 0.3 + self.m_core * 0.7) * self.dry_mass
        return max(0.0001, self.dry_mass + water_mass + self.accelerant_mass + self.ash_mass)

    @property
    def radius(self) -> float:
        if len(self.dimensions) >= 2:
            return float(self.dimensions[1])
        return 0.05

    @property
    def surface_area(self) -> float:
        """Approximate cylinder surface area."""
        l = float(self.dimensions[0])
        r = self.radius
        return 2.0 * math.pi * r * l + 2.0 * math.pi * (r ** 2)

    def add_accelerant(self, mass_kg: float, accelerant_type: str = "lighter_fluid"):
        self.accelerant_mass += max(0.0, mass_kg)
        self.accelerant_type = accelerant_type

    def clear_ash(self):
        """Removes insulating ash blanket when cleared or blown."""
        self.ash_insulation_depth = max(0.0, self.ash_insulation_depth - 5.0)

    def blow(self, intensity: float):
        """Disturbs ash and injects oxygen."""
        self.clear_ash()

    def apply_external_heat(self, watts: float, dt: float):
        """Applies heat directly to surface."""
        if watts <= 0.0:
            return
        energy = watts * dt
        surf_mass = max(0.0001, self.dry_mass * 0.3)
        # Heat surface
        c_eff = CP_DRY_WOOD + self.m_surface * CP_WATER
        self.t_surface += energy / (surf_mass * c_eff)

    def update(
        self,
        dt: float,
        ambient_temp: float = 20.0,
        oxygen_fraction: float = 0.2095,
        draft_velocity: float = 0.5,
        wind_speed: float = 0.5
    ):
        """
        Fixed tick thermodynamic and chemical reaction update.
        """
        self.resin_pop_event = False
        self.hiss_event = False
        self.steam_rate = 0.0
        self.smoke_rate = 0.0
        self.heat_flux_output = 0.0
        self.flame_height = 0.0
        
        # If reduced to inert ash, cool to ambient
        if self.dry_mass <= 0.0005 and self.char_mass <= 0.0005:
            self.stage = CombustionStage.INERT_ASH
            cool_rate = 0.05 * dt
            self.t_surface += (ambient_temp - self.t_surface) * cool_rate
            self.t_internal += (ambient_temp - self.t_internal) * cool_rate
            return

        # 1. Moisture Diffusion between core and surface
        self.m_surface, self.m_core, _ = MoistureDiffusionEngine.calculate_internal_diffusion(
            self.m_surface, self.m_core,
            self.props.moisture_diffusion_coeff,
            self.radius, dt
        )

        # 2. Accelerant burning (Gasoline / Lighter fluid)
        accelerant_heat = 0.0
        if self.accelerant_mass > 0.0 and self.t_surface >= 40.0:
            burn_rate = 0.005 if self.accelerant_type == "lighter_fluid" else 0.02
            burned_kg = min(self.accelerant_mass, burn_rate * dt)
            self.accelerant_mass -= burned_kg
            # Accelerant energy ~ 44 MJ/kg
            accelerant_heat = burned_kg * 44.0e6 / dt
            self.t_surface += 250.0 * dt

        # 3. Moisture Dehydration Phase (Clamped at ~100°C)
        if self.t_surface >= TEMP_WATER_BOILING and self.m_surface > 0.001:
            # Latent heat of vaporization absorbs energy
            surf_dry_mass = self.dry_mass * 0.3
            latent_power = max(100.0, (self.t_surface - 98.0) * 80.0 + accelerant_heat)
            self.m_surface, evap_kg, self.steam_rate, _ = MoistureDiffusionEngine.calculate_evaporation(
                self.t_surface, self.m_surface, latent_power, surf_dry_mass, dt
            )
            # Clamped near 100°C
            self.t_surface = min(118.0, max(99.0, self.t_surface))
            self.hiss_event = True
            self.stage = CombustionStage.DEHYDRATION

        # 4. Pyrolysis Phase (200°C - 450°C)
        volatile_release_rate = 0.0
        if self.t_surface >= TEMP_PYROLYSIS_START and self.volatile_mass > 0.0:
            self.stage = CombustionStage.PYROLYSIS
            # Thermal decomposition rates
            hemi_rate = max(0.0, min(1.0, (self.t_surface - 200.0) / 60.0)) * 0.001
            cell_rate = max(0.0, min(1.0, (self.t_surface - 240.0) / 110.0)) * 0.002
            lign_rate = max(0.0, min(1.0, (self.t_surface - 280.0) / 220.0)) * 0.001
            
            total_pyro_fraction = hemi_rate + cell_rate + lign_rate
            released = min(self.volatile_mass, self.volatile_mass * total_pyro_fraction * dt)
            self.volatile_mass -= released
            volatile_release_rate = released / dt
            self.smoke_rate = volatile_release_rate * 1000.0 # g/s
            
            # Softwoods resin steam popping
            if self.props.resin_content > 0.10 and np.random.random() < (self.props.spark_pop_rate * 0.08):
                self.resin_pop_event = True

        # 5. Flaming Phase (T > 450°C, O2 > 12%)
        # Birch bark betulin can ignite at slightly lower temp (380°C)
        ign_temp = self.props.volatile_ignition_temp
        can_flame = (
            (self.t_surface >= ign_temp or accelerant_heat > 0.0)
            and oxygen_fraction >= O2_FLAMING_MIN
            and (volatile_release_rate > 0.00001 or self.accelerant_mass > 0.0)
        )
        
        # Quench check: if core boils (T_core > 100°C) and core is very wet (M_core > 0.45)
        if self.t_internal >= 100.0 and self.m_core > 0.45:
            steam_quench = (self.t_internal - 100.0) * 0.05 * self.m_core
            if steam_quench > 0.08:
                can_flame = False  # Quenched by boiling internal steam bursts!
                self.steam_rate += steam_quench * 0.01
                self.hiss_event = True

        if can_flame:
            self.stage = CombustionStage.FLAMING
            # Highly exothermic combustion of volatile gases
            # Lower heating value of wood volatiles ~ 16 MJ/kg
            gas_power = volatile_release_rate * 16.0e6 + accelerant_heat
            draft_factor = max(0.5, min(2.5, draft_velocity / 1.0))
            self.heat_flux_output += gas_power * draft_factor
            
            # Radiate heat back into self
            self.t_surface += min(40.0, (gas_power * 0.12 * dt) / (self.dry_mass * 0.3 * CP_DRY_WOOD))
            self.flame_height = max(0.05, 0.4 * math.sqrt(max(0.01, volatile_release_rate * 1000.0)) * draft_factor)
            self.crackle_factor = min(1.0, self.flame_height * 2.0)

        # 6. Char Oxidation / Glowing Coals (500°C - 900°C)
        # Ash insulation decreases effective oxygen diffusion
        effective_o2 = max(0.02, oxygen_fraction * math.exp(-self.ash_insulation_depth / 8.0))
        
        if (self.t_surface >= TEMP_CHAR_GLOW_MIN or self.stage == CombustionStage.FLAMING) and self.char_mass > 0.0:
            if effective_o2 >= 0.05:
                # Solid carbon oxidation: C + O2 -> CO2 + 393.5 kJ/mol (32.79 MJ/kg)
                ox_rate_base = 0.0004 * (effective_o2 / 0.21) * ((self.t_surface - 400.0) / 400.0)
                # Hardwoods burn longer and slower
                density_factor = 400.0 / self.props.bulk_density
                ox_rate = ox_rate_base * density_factor
                
                burned_char = min(self.char_mass, self.char_mass * ox_rate * dt)
                self.char_mass -= burned_char
                self.dry_mass = max(0.0, self.dry_mass - burned_char)
                
                # Ash deposition
                ash_created = burned_char * self.props.ash_fraction
                self.ash_mass += ash_created
                self.ash_insulation_depth += ash_created * 15.0 # mm growth
                
                char_power = (burned_char * CARBON_COMBUSTION_HEAT) / dt
                self.heat_flux_output += char_power
                
                # Maintain glowing coal temperature
                self.t_surface = min(TEMP_CHAR_GLOW_MAX, self.t_surface + (char_power * 0.25 * dt) / (max(0.01, self.char_mass) * CP_CHARCOAL))
                if not can_flame:
                    self.stage = CombustionStage.CHAR_OXIDATION

        # 7. Internal Heat Conduction between surface and core
        k_therm = self.props.thermal_conductivity
        radial_dist = max(0.005, self.radius * 0.5)
        # Heat transfer rate Q = k * A * (T_surf - T_core) / delta_x
        q_internal = (k_therm * self.surface_area * (self.t_surface - self.t_internal)) / radial_dist
        core_c_eff = CP_DRY_WOOD + self.m_core * CP_WATER
        core_mass = max(0.0001, self.dry_mass * 0.7)
        self.t_internal += (q_internal * dt) / (core_mass * core_c_eff)

        # 8. Ambient Heat Loss (Convection + Radiation)
        # Convective cooling to ambient air
        h_amb = 5.0 + 8.0 * math.sqrt(max(0.1, wind_speed))
        q_conv_loss = h_amb * self.surface_area * (self.t_surface - ambient_temp)
        # Radiative cooling (Stefan-Boltzmann)
        t_s_k = self.t_surface + 273.15
        t_amb_k = ambient_temp + 273.15
        q_rad_loss = 0.85 * STEFAN_BOLTZMANN * self.surface_area * (t_s_k**4 - t_amb_k**4)
        
        total_loss = (q_conv_loss + q_rad_loss) * dt
        surf_c_eff = CP_DRY_WOOD + self.m_surface * CP_WATER
        surf_mass = max(0.0001, self.dry_mass * 0.3)
        self.t_surface = max(ambient_temp, self.t_surface - total_loss / (surf_mass * surf_c_eff))
        
        # Check transition to inert ash
        if self.char_mass <= 0.0005 and self.volatile_mass <= 0.0005:
            self.stage = CombustionStage.INERT_ASH

    def get_render_state(self) -> Dict[str, Any]:
        """Provides visual rendering state."""
        return {
            "position": self.position.copy(),
            "orientation": self.orientation.copy(),
            "dimensions": self.dimensions.copy(),
            "species": self.species_type.value,
            "stage": self.stage.value,
            "t_surface": self.t_surface,
            "t_internal": self.t_internal,
            "m_surface": self.m_surface,
            "m_core": self.m_core,
            "flame_height": self.flame_height,
            "steam_rate": self.steam_rate,
            "smoke_rate": self.smoke_rate,
            "char_fraction": max(0.0, min(1.0, 1.0 - (self.char_mass / max(0.0001, self.char_yield_max)))),
            "ash_depth": self.ash_insulation_depth,
            "heat_output": self.heat_flux_output
        }
