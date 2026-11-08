"""
Firestarter - Tree Felling & Dynamic Collapse
Implements Section 4.1:
Directional face notch, back-cut, rigid-body fall, branch break-off upon impact.
"""

import math
import numpy as np
from typing import Dict, Any, List, Tuple
from firestarter.forestry.tree import Tree, TreeGrowthStage
from firestarter.thermodynamics.combustion_body import CombustionBody
from firestarter.thermodynamics.wood_properties import WoodSpeciesType

class TreeFellingSystem:
    @staticmethod
    def chop_notch(tree: Tree, axe_type: str = "steel", swing_power: float = 1.0) -> Dict[str, Any]:
        """Directional undercut face notch."""
        if tree.is_fallen or tree.is_falling:
            return {"success": False, "message": "Tree has already fallen."}

        cut_efficiency = 0.025 if axe_type == "steel" else 0.012
        cut_amount = cut_efficiency * swing_power
        target_notch = tree.trunk_radius_m * 0.7  # 70% of radius
        
        tree.notch_depth_m = min(target_notch, tree.notch_depth_m + cut_amount)
        percent = (tree.notch_depth_m / target_notch) * 100.0
        
        return {
            "success": True,
            "message": f"Chopped directional face notch ({percent:.0f}% complete).",
            "notch_percent": percent,
            "is_complete": tree.notch_depth_m >= target_notch
        }

    @staticmethod
    def chop_backcut(tree: Tree, axe_type: str = "steel", swing_power: float = 1.0) -> Dict[str, Any]:
        """Back-cut on opposite side of trunk to trigger hinge release and collapse."""
        if tree.notch_depth_m < (tree.trunk_radius_m * 0.4):
            return {"success": False, "message": "Face notch must be carved first before back-cut!"}
            
        cut_efficiency = 0.028 if axe_type == "steel" else 0.014
        cut_amount = cut_efficiency * swing_power
        target_backcut = tree.trunk_radius_m * 0.5
        
        tree.backcut_depth_m = min(target_backcut, tree.backcut_depth_m + cut_amount)
        
        # Check hinge release
        hinge_remaining = (tree.trunk_radius_m * 2.0) - (tree.notch_depth_m + tree.backcut_depth_m)
        if hinge_remaining <= 0.04 and not tree.is_falling:
            tree.is_falling = True
            return {
                "success": True,
                "message": "TIMBER! Tree hinge snaps and begins to fall!",
                "tree_falling": True
            }

        return {
            "success": True,
            "message": f"Chopped back-cut. Hinge thickness: {hinge_remaining*100:.1f} cm.",
            "tree_falling": False
        }

    @staticmethod
    def update_falling_tree(tree: Tree, dt: float) -> Tuple[bool, List[CombustionBody]]:
        """
        Simulates gravity fall arc and calculates branch impact shattering.
        Returns (has_hit_ground, spawned_fuel_pieces).
        """
        if not tree.is_falling or tree.is_fallen:
            return False, []

        # Angular acceleration of falling inverted pendulum
        # theta_ddot = (3*g / (2*L)) * sin(theta)
        g = 9.81
        theta_rad = math.radians(max(2.0, tree.fall_angle))
        omega = math.sqrt(max(0.1, (3.0 * g / tree.height_m) * (1.0 - math.cos(theta_rad))))
        tree.fall_angle += math.degrees(omega * dt)

        if tree.fall_angle >= 90.0:
            # Impact with ground!
            tree.fall_angle = 90.0
            tree.is_falling = False
            tree.is_fallen = True
            tree.stage = TreeGrowthStage.FALLEN_DECAYING
            
            # Shatter canopy into kindling twigs and trunk into usable fuel logs
            spawned_bodies: List[CombustionBody] = []
            
            # 1. Main trunk logs (3 logs)
            for i in range(3):
                log_pos = tree.position.copy()
                log_pos[0] += (i + 1) * 1.5
                log = CombustionBody(
                    species=tree.species,
                    dry_mass=8.0,
                    initial_m_surface=tree.living_moisture_surface,
                    initial_m_core=tree.living_moisture_core,
                    geometry_type="log",
                    position=log_pos,
                    dimensions=np.array([0.7, 0.08])
                )
                spawned_bodies.append(log)

            # 2. Kindling branches and twigs (5 pieces)
            for j in range(5):
                twig_pos = tree.position.copy()
                twig_pos[0] += 3.5 + (j * 0.4)
                twig_pos[2] += np.random.uniform(-0.5, 0.5)
                twig = CombustionBody(
                    species=tree.species,
                    dry_mass=0.35,
                    initial_m_surface=max(0.15, tree.living_moisture_surface * 0.6),
                    initial_m_core=max(0.20, tree.living_moisture_core * 0.6),
                    geometry_type="kindling",
                    position=twig_pos,
                    dimensions=np.array([0.25, 0.015])
                )
                spawned_bodies.append(twig)

            return True, spawned_bodies

        return False, []
