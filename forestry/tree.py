"""
Firestarter - Tree Anatomy & Ecological Growth
Implements Section 4.1 & 7.2:
Bark, sapwood, and heartwood layers; species characteristics, fungal fruitings.
"""

from enum import Enum
import math
import numpy as np
from typing import Optional, List
from firestarter.thermodynamics.wood_properties import WoodSpeciesType

class TreeGrowthStage(Enum):
    SAPLING = "Sapling"
    MATURE = "Mature Living"
    STANDING_DEAD = "Standing Dead"
    FALLEN_DECAYING = "Fallen Decaying"

class Tree:
    def __init__(
        self,
        species: WoodSpeciesType,
        position: np.ndarray,
        height_m: float = 12.0,
        trunk_radius_m: float = 0.22,
        stage: TreeGrowthStage = TreeGrowthStage.MATURE
    ):
        self.species = species
        self.position = position
        self.height_m = height_m
        self.trunk_radius_m = trunk_radius_m
        self.stage = stage
        
        # Anatomy layers (radial fractions of trunk)
        # Bark: outer 8%, Sapwood: middle 40%, Heartwood: inner 52%
        self.bark_thickness_m = trunk_radius_m * 0.08
        self.sapwood_thickness_m = trunk_radius_m * 0.40
        self.heartwood_thickness_m = trunk_radius_m * 0.52
        
        # Moisture based on life stage
        if stage == TreeGrowthStage.MATURE:
            self.living_moisture_surface = 0.80
            self.living_moisture_core = 1.10  # 110% dry-basis sap saturation
        elif stage == TreeGrowthStage.STANDING_DEAD:
            self.living_moisture_surface = 0.35
            self.living_moisture_core = 0.45
        elif stage == TreeGrowthStage.FALLEN_DECAYING:
            self.living_moisture_surface = 0.70
            self.living_moisture_core = 0.90
        else: # SAPLING
            self.living_moisture_surface = 0.85
            self.living_moisture_core = 1.20

        # Felling cut progress
        self.notch_depth_m = 0.0
        self.backcut_depth_m = 0.0
        self.fall_angle = 0.0 # degrees
        self.is_falling = False
        self.is_fallen = (stage == TreeGrowthStage.FALLEN_DECAYING)
        
        # Fungi fruiting on standing dead or fallen timber
        self.has_fungi = (stage in (TreeGrowthStage.STANDING_DEAD, TreeGrowthStage.FALLEN_DECAYING))
        self.fungi_type = "Tinder Fungus" if species != WoodSpeciesType.PAPER_BIRCH else "Birch Polypore"

    @property
    def total_trunk_mass_kg(self) -> float:
        """Approximates cylinder mass based on species density."""
        volume = math.pi * (self.trunk_radius_m ** 2) * self.height_m
        density = 500.0
        return volume * density
