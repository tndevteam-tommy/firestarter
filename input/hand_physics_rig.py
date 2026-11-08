"""
Firestarter - Procedural Hand Physics Rig & Inverse Kinematics (IK)
Implements Section 8.1 HandController & HandPhysicsRig:
Two-handed inverse kinematics for reach, grasp, cordage twisting,
and bow drill stroking.
"""

import math
import numpy as np
from typing import Dict, Any, Tuple

class HandJointState:
    def __init__(self, position: np.ndarray, rotation: np.ndarray, flex: float = 0.0):
        self.position = position
        self.rotation = rotation
        self.flex = flex # 0.0 = open hand, 1.0 = clenched fist

class HandController:
    """
    Procedural IK solver for player dual hands.
    Calculates arm joint angles and hand positions relative to camera view.
    """
    def __init__(self):
        # Resting position in camera view coordinates (X: right, Y: down, Z: forward)
        self.rest_left = np.array([-0.28, -0.22, 0.45])
        self.rest_right = np.array([0.28, -0.22, 0.45])
        
        # Current simulated positions
        self.pos_left = self.rest_left.copy()
        self.pos_right = self.rest_right.copy()
        
        # Rotation (pitch, yaw, roll)
        self.rot_left = np.array([0.0, 0.0, 0.0])
        self.rot_right = np.array([0.0, 0.0, 0.0])
        
        # Finger curl
        self.flex_left = 0.2
        self.flex_right = 0.2
        
        # Action animation variables
        self.bow_stroke_phase = 0.0
        self.whittle_phase = 0.0
        self.strike_phase = 0.0
        self.blow_phase = 0.0
        self.cordage_twist_phase = 0.0

    def solve_ik_reach(self, target_pos: np.ndarray, is_right_hand: bool = True):
        """Two-link arm inverse kinematics towards interaction target."""
        upper_arm_len = 0.35
        forearm_len = 0.32
        
        shoulder_pos = np.array([0.22 if is_right_hand else -0.22, -0.15, 0.0])
        to_target = target_pos - shoulder_pos
        dist = np.linalg.norm(to_target)
        dist = max(0.05, min(upper_arm_len + forearm_len - 0.01, dist))
        
        # Law of cosines for elbow angle
        cos_elbow = (upper_arm_len**2 + forearm_len**2 - dist**2) / (2.0 * upper_arm_len * forearm_len)
        elbow_angle = math.acos(max(-1.0, min(1.0, cos_elbow)))
        
        if is_right_hand:
            self.pos_right = target_pos.copy()
        else:
            self.pos_left = target_pos.copy()

    def update(self, dt: float, current_action: str = "idle"):
        """Procedural IK animation loop."""
        # Breathing / idle hand bob
        idle_bob_y = 0.012 * math.sin(self.bow_stroke_phase * 2.0)
        idle_bob_x = 0.006 * math.cos(self.bow_stroke_phase * 1.5)
        
        if current_action == "bow_drilling":
            # Left hand holds bearing stone firmly over spindle top
            self.pos_left = np.array([0.0, -0.05, 0.42])
            self.rot_left = np.array([25.0, 0.0, -10.0])
            self.flex_left = 0.85 # holding stone socket
            
            # Right hand strokes bow back and forth horizontally
            self.bow_stroke_phase += 14.0 * dt
            stroke_offset = 0.18 * math.sin(self.bow_stroke_phase)
            self.pos_right = np.array([0.15 + stroke_offset, -0.08, 0.45])
            self.rot_right = np.array([0.0, stroke_offset * 40.0, 15.0])
            self.flex_right = 0.75

        elif current_action == "whittling":
            # Left hand holds wood stick
            self.pos_left = np.array([-0.12, -0.15, 0.40])
            self.flex_left = 0.8
            # Right hand slices knife downward along stick
            self.whittle_phase = (self.whittle_phase + 5.0 * dt) % 1.0
            slice_y = -0.12 - self.whittle_phase * 0.14
            self.pos_right = np.array([-0.08, slice_y, 0.42])
            self.rot_right = np.array([35.0, -15.0, 20.0])
            self.flex_right = 0.9

        elif current_action == "cordage_twisting":
            # Two hands counter-rotating in reverse wrap
            self.cordage_twist_phase += 12.0 * dt
            roll = math.sin(self.cordage_twist_phase) * 35.0
            self.pos_left = np.array([-0.06, -0.18, 0.38])
            self.pos_right = np.array([0.06, -0.18, 0.38])
            self.rot_left = np.array([0.0, 0.0, -roll])
            self.rot_right = np.array([0.0, 0.0, roll])
            self.flex_left = 0.6
            self.flex_right = 0.6

        elif current_action == "striking_lighter":
            # Right hand flicks spark wheel
            self.strike_phase = min(1.0, self.strike_phase + 8.0 * dt)
            self.pos_right = np.array([0.12, -0.14, 0.38])
            self.rot_right = np.array([15.0, -10.0, -5.0])
            self.flex_right = 0.7

        elif current_action == "blowing":
            # Hands cupped around tinder nest close to face
            self.pos_left = np.array([-0.08, -0.08, 0.28])
            self.pos_right = np.array([0.08, -0.08, 0.28])
            self.rot_left = np.array([20.0, 30.0, -25.0])
            self.rot_right = np.array([20.0, -30.0, 25.0])
            self.flex_left = 0.5
            self.flex_right = 0.5

        else: # Idle
            self.bow_stroke_phase += 2.0 * dt
            # Return smoothly to rest
            self.pos_left += (self.rest_left + np.array([idle_bob_x, idle_bob_y, 0.0]) - self.pos_left) * (8.0 * dt)
            self.pos_right += (self.rest_right + np.array([-idle_bob_x, idle_bob_y, 0.0]) - self.pos_right) * (8.0 * dt)
            self.rot_left += (np.array([0.0, 0.0, 0.0]) - self.rot_left) * (8.0 * dt)
            self.rot_right += (np.array([0.0, 0.0, 0.0]) - self.rot_right) * (8.0 * dt)
            self.flex_left += (0.25 - self.flex_left) * (8.0 * dt)
            self.flex_right += (0.25 - self.flex_right) * (8.0 * dt)
            self.strike_phase = 0.0

    def get_hand_render_matrices(self) -> Dict[str, Any]:
        """Provides hand transforms for rendering meshes."""
        return {
            "left_pos": self.pos_left.copy(),
            "left_rot": self.rot_left.copy(),
            "left_flex": self.flex_left,
            "right_pos": self.pos_right.copy(),
            "right_rot": self.rot_right.copy(),
            "right_flex": self.flex_right
        }
