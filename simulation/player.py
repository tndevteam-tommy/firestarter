"""
Firestarter - Player Entity & First-Person Inventory
Manages player movement, look orientation, hands, stamina, and tool equipment.
"""

import math
import numpy as np
from typing import Dict, Any, Optional, List

class Player:
    def __init__(self, position: Optional[np.ndarray] = None):
        self.position = position if position is not None else np.array([0.0, 1.7, 2.5], dtype=float)
        self.velocity = np.array([0.0, 0.0, 0.0], dtype=float)
        self.yaw = -90.0    # facing forward toward -Z
        self.pitch = -15.0  # looking slightly downward toward fire pit
        
        # Physical attributes
        self.walk_speed = 3.5
        self.sprint_speed = 6.0
        self.is_sprinting = False
        self.stamina = 100.0
        self.max_stamina = 100.0
        
        # Dual-Hand equipment
        # Primary hand (LMB): tool / action item
        self.primary_hand = "pocket_lighter" # "pocket_lighter", "pocket_knife", "felling_axe", "bow_drill_spindle", "kindling"
        # Secondary hand (RMB): placement / support item
        self.secondary_hand = "tinder_nest"   # "tinder_nest", "bearing_stone", "hearthboard", "log"
        
        # Hand rotation angle for placement
        self.held_item_rotation = 0.0
        
        # Inventory counts
        self.inventory = {
            "white_pine_log": 2,
            "red_cedar_log": 2,
            "white_oak_log": 1,
            "paper_birch_bark": 4,
            "kindling_twigs": 10,
            "dry_cedar_shavings": 6,
            "two_ply_cordage": 2,
            "waterproof_tarp": 0,
            "gasoline_canister": 0,
            "smoldering_fungus": 0
        }

    def move(self, forward: float, strafe: float, dt: float):
        """First-person movement along yaw plane."""
        yaw_rad = math.radians(self.yaw)
        # Forward vector
        dir_x = math.cos(yaw_rad)
        dir_z = math.sin(yaw_rad)
        # Right vector
        right_x = -math.sin(yaw_rad)
        right_z = math.cos(yaw_rad)
        
        speed = self.sprint_speed if self.is_sprinting and self.stamina > 5.0 else self.walk_speed
        if self.is_sprinting and (forward != 0 or strafe != 0):
            self.stamina = max(0.0, self.stamina - 15.0 * dt)
        else:
            self.stamina = min(self.max_stamina, self.stamina + 12.0 * dt)

        move_vec = (np.array([dir_x, 0.0, dir_z]) * forward + np.array([right_x, 0.0, right_z]) * strafe)
        norm = np.linalg.norm(move_vec)
        if norm > 1e-4:
            move_vec = (move_vec / norm) * speed
            
        self.position += move_vec * dt
        # Clamp bounds
        self.position[0] = max(-60.0, min(60.0, self.position[0]))
        self.position[2] = max(-60.0, min(60.0, self.position[2]))

    def rotate_look(self, delta_yaw: float, delta_pitch: float):
        self.yaw += delta_yaw
        self.pitch = max(-85.0, min(85.0, self.pitch + delta_pitch))

    def rotate_held_item(self, delta_degrees: float):
        self.held_item_rotation = (self.held_item_rotation + delta_degrees) % 360.0

    def get_forward_ray(self) -> np.ndarray:
        yaw_rad = math.radians(self.yaw)
        pitch_rad = math.radians(self.pitch)
        x = math.cos(pitch_rad) * math.cos(yaw_rad)
        y = math.sin(pitch_rad)
        z = math.cos(pitch_rad) * math.sin(yaw_rad)
        return np.array([x, y, z])
