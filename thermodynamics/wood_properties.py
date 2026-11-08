"""
Firestarter - Wood Species & Cellular Property Matrix
Implements Table 2.3 from the Technical Design Specification.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Dict

class WoodSpeciesType(Enum):
    WHITE_PINE = "White Pine"
    RED_CEDAR = "Red Cedar"
    PAPER_BIRCH = "Paper Birch"
    WHITE_OAK = "White Oak"
    PUNK_WOOD = "Punk Wood"

@dataclass(frozen=True)
class WoodProperties:
    species: WoodSpeciesType
    classification: str              # Softwood, Hardwood, Decayed Fibers
    bulk_density: float              # kg/m^3
    resin_content: float             # Fraction (0.0 to 1.0)
    charcoal_caloric_value: float    # J/kg
    moisture_diffusion_coeff: float  # m^2/s (D_m)
    thermal_conductivity: float      # W/(m * K)
    ash_fraction: float              # Fraction of dry mass left as mineral ash
    volatile_ignition_temp: float    # °C
    char_yield_fraction: float       # Fraction of dry mass converted to solid char
    spark_pop_rate: float            # Pop rate modifier for ASMR resin bursts
    is_sponge: bool = False          # High moisture absorption for punk wood
    betulin_content: float = 0.0     # Birch bark betulin resin

WOOD_MATRIX: Dict[WoodSpeciesType, WoodProperties] = {
    WoodSpeciesType.WHITE_PINE: WoodProperties(
        species=WoodSpeciesType.WHITE_PINE,
        classification="Softwood",
        bulk_density=380.0,
        resin_content=0.185,             # 18.5% (Terpenes)
        charcoal_caloric_value=18.2e6,    # 18.2 MJ/kg (Fast burn)
        moisture_diffusion_coeff=1.8e-5,  # 1.8e-5 m^2/s
        thermal_conductivity=0.12,       # W/(m * K)
        ash_fraction=0.015,              # 1.5%
        volatile_ignition_temp=360.0,
        char_yield_fraction=0.22,
        spark_pop_rate=1.8,
        is_sponge=False,
        betulin_content=0.0
    ),
    WoodSpeciesType.RED_CEDAR: WoodProperties(
        species=WoodSpeciesType.RED_CEDAR,
        classification="Softwood",
        bulk_density=360.0,
        resin_content=0.220,             # 22.0% (Resinous oils)
        charcoal_caloric_value=17.8e6,    # 17.8 MJ/kg (Flaring)
        moisture_diffusion_coeff=2.1e-5,  # 2.1e-5 m^2/s
        thermal_conductivity=0.11,
        ash_fraction=0.012,
        volatile_ignition_temp=340.0,
        char_yield_fraction=0.20,
        spark_pop_rate=2.2,
        is_sponge=False,
        betulin_content=0.0
    ),
    WoodSpeciesType.PAPER_BIRCH: WoodProperties(
        species=WoodSpeciesType.PAPER_BIRCH,
        classification="Hardwood",
        bulk_density=650.0,
        resin_content=0.140,             # 14.0% (Betulin in bark)
        charcoal_caloric_value=22.4e6,    # 22.4 MJ/kg (Balanced)
        moisture_diffusion_coeff=1.2e-5,  # 1.2e-5 m^2/s
        thermal_conductivity=0.16,
        ash_fraction=0.020,
        volatile_ignition_temp=380.0,
        char_yield_fraction=0.28,
        spark_pop_rate=0.8,
        is_sponge=False,
        betulin_content=0.25             # High bark betulin
    ),
    WoodSpeciesType.WHITE_OAK: WoodProperties(
        species=WoodSpeciesType.WHITE_OAK,
        classification="Hardwood",
        bulk_density=780.0,
        resin_content=0.042,             # 4.2% (Low volatiles)
        charcoal_caloric_value=28.6e6,    # 28.6 MJ/kg (Enduring)
        moisture_diffusion_coeff=0.6e-5,  # 0.6e-5 m^2/s
        thermal_conductivity=0.19,
        ash_fraction=0.035,
        volatile_ignition_temp=430.0,
        char_yield_fraction=0.35,
        spark_pop_rate=0.3,
        is_sponge=False,
        betulin_content=0.0
    ),
    WoodSpeciesType.PUNK_WOOD: WoodProperties(
        species=WoodSpeciesType.PUNK_WOOD,
        classification="Decayed Fibers",
        bulk_density=120.0,
        resin_content=0.010,             # 1.0% (Lignin-depleted)
        charcoal_caloric_value=12.0e6,    # 12.0 MJ/kg (Smolder only)
        moisture_diffusion_coeff=8.5e-5,  # 8.5e-5 m^2/s (Sponge)
        thermal_conductivity=0.05,
        ash_fraction=0.050,
        volatile_ignition_temp=290.0,
        char_yield_fraction=0.15,
        spark_pop_rate=0.05,
        is_sponge=True,
        betulin_content=0.0
    ),
}

def get_wood_properties(species: WoodSpeciesType) -> WoodProperties:
    return WOOD_MATRIX[species]
