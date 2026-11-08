"""
Firestarter - Forest Ecosystem & Lifecycle Dynamics
Implements Section 7.2:
Seed dispersal, ash-fertilized sapling growth, and fungal decay stages.
"""

import math
import numpy as np
from typing import List, Dict, Any, Tuple
from firestarter.forestry.tree import Tree, TreeGrowthStage
from firestarter.thermodynamics.wood_properties import WoodSpeciesType

class AshDepositZone:
    def __init__(self, position: np.ndarray, ash_mass_kg: float = 1.0):
        self.position = position
        self.ash_mass_kg = ash_mass_kg
        # Minerals: Potassium carbonate (K2CO3), Calcium carbonate (CaCO3), Phosphate
        self.fertility_boost = min(3.0, 1.0 + ash_mass_kg * 0.5)

class ForestEcosystem:
    def __init__(self, area_size_m: float = 150.0):
        self.area_size_m = area_size_m
        self.trees: List[Tree] = []
        self.ash_zones: List[AshDepositZone] = []
        self.fallen_decay_logs: List[Dict[str, Any]] = []
        
        # Populate initial procedural forest
        self._populate_forest()

    def _populate_forest(self):
        np.random.seed(42)
        species_list = [
            WoodSpeciesType.WHITE_PINE,
            WoodSpeciesType.RED_CEDAR,
            WoodSpeciesType.PAPER_BIRCH,
            WoodSpeciesType.WHITE_OAK
        ]
        
        for _ in range(25):
            sp = np.random.choice(species_list)
            pos = np.array([
                np.random.uniform(-self.area_size_m * 0.4, self.area_size_m * 0.4),
                0.0,
                np.random.uniform(-self.area_size_m * 0.4, self.area_size_m * 0.4)
            ])
            stage = TreeGrowthStage.MATURE
            if np.random.random() < 0.20:
                stage = TreeGrowthStage.STANDING_DEAD
            tree = Tree(species=sp, position=pos, stage=stage)
            self.trees.append(tree)

    def add_campfire_ash(self, position: np.ndarray, ash_kg: float):
        """Deposits potassium/calcium ash from campfire, boosting local fertility."""
        zone = AshDepositZone(position.copy(), ash_kg)
        self.ash_zones.append(zone)

    def step_ecosystem(self, days_passed: float, wind_vector: np.ndarray):
        """
        Seasonal ecosystem step:
        - Seed dispersal
        - Ash-fertilized sapling growth
        - Decay progression to humus
        """
        # 1. Seed dispersal based on wind
        wind_strength = np.linalg.norm(wind_vector)
        if wind_strength > 1.0 and len(self.trees) < 45:
            # Drop pine cones or acorns
            mature_trees = [t for t in self.trees if t.stage == TreeGrowthStage.MATURE]
            if mature_trees and np.random.random() < 0.35:
                parent = mature_trees[np.random.randint(len(mature_trees))]
                seed_pos = parent.position + wind_vector * np.random.uniform(2.0, 15.0)
                
                # Check fertility boost from nearby ash deposits
                fertility = 1.0
                for zone in self.ash_zones:
                    if np.linalg.norm(zone.position - seed_pos) < 5.0:
                        fertility = zone.fertility_boost
                        break
                        
                sapling = Tree(
                    species=parent.species,
                    position=seed_pos,
                    height_m=1.5,
                    trunk_radius_m=0.04,
                    stage=TreeGrowthStage.SAPLING
                )
                self.trees.append(sapling)

        # 2. Sapling growth
        for tree in self.trees:
            if tree.stage == TreeGrowthStage.SAPLING:
                growth = 0.05 * (days_passed / 30.0)
                tree.height_m += growth
                tree.trunk_radius_m += growth * 0.015
                if tree.height_m >= 6.0:
                    tree.stage = TreeGrowthStage.MATURE
