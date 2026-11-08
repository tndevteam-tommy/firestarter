"""
Firestarter - Architectural Fire Blueprints
Implements Section 6 of the Technical Design Specification:
1. Teepee Fire
2. Log Cabin Fire
3. Lean-To Fire
4. Swedish Torch (Canadian Candle)
5. Star Fire
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Any, Optional

class BlueprintSlot:
    def __init__(
        self,
        slot_id: str,
        expected_type: str, # 'tinder', 'kindling', 'log', 'reflector'
        position: np.ndarray,
        orientation: np.ndarray,
        dimensions: np.ndarray, # [length, radius]
        tolerance_m: float = 0.15
    ):
        self.slot_id = slot_id
        self.expected_type = expected_type
        self.position = position
        self.orientation = orientation
        self.dimensions = dimensions
        self.tolerance_m = tolerance_m
        self.is_filled = False

class FireBlueprint:
    def __init__(
        self,
        name: str,
        key: str,
        description: str,
        ideal_use: str,
        draft_profile: str,
        slots: List[BlueprintSlot]
    ):
        self.name = name
        self.key = key
        self.description = description
        self.ideal_use = ideal_use
        self.draft_profile = draft_profile
        self.slots = slots

    def check_placement(self, log_positions: List[np.ndarray]) -> float:
        """Calculates percentage of blueprint slots matched."""
        if not self.slots:
            return 1.0
        filled = 0
        used = [False] * len(log_positions)
        
        for slot in self.slots:
            slot.is_filled = False
            for idx, p in enumerate(log_positions):
                if not used[idx]:
                    dist = np.linalg.norm(slot.position - p)
                    if dist <= slot.tolerance_m:
                        slot.is_filled = True
                        used[idx] = True
                        filled += 1
                        break
        return filled / len(self.slots)

def create_teepee_blueprint() -> FireBlueprint:
    slots = [
        BlueprintSlot("center_tinder", "tinder", np.array([0.0, 0.05, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.15, 0.04])),
        # 4 cone kindling sticks
        BlueprintSlot("cone_1", "kindling", np.array([0.12, 0.15, 0.0]), np.array([25.0, 0.0, 0.0]), np.array([0.35, 0.02])),
        BlueprintSlot("cone_2", "kindling", np.array([-0.12, 0.15, 0.0]), np.array([-25.0, 0.0, 0.0]), np.array([0.35, 0.02])),
        BlueprintSlot("cone_3", "kindling", np.array([0.0, 0.15, 0.12]), np.array([0.0, 0.0, 25.0]), np.array([0.35, 0.02])),
        BlueprintSlot("cone_4", "kindling", np.array([0.0, 0.15, -0.12]), np.array([0.0, 0.0, -25.0]), np.array([0.35, 0.02])),
        # Outer fuel logs
        BlueprintSlot("log_1", "log", np.array([0.20, 0.25, 0.15]), np.array([35.0, 45.0, 0.0]), np.array([0.55, 0.05])),
        BlueprintSlot("log_2", "log", np.array([-0.20, 0.25, -0.15]), np.array([-35.0, 45.0, 0.0]), np.array([0.55, 0.05])),
    ]
    return FireBlueprint(
        name="Teepee Fire",
        key="teepee",
        description="Conical structure concentrating vertical thermal updraft for quick heat and rapid kindle ignition.",
        ideal_use="Fast initial warmth, lighting damp kindling, emergency flare.",
        draft_profile="Concentrated vertical chimney updraft with strong base vacuum draw.",
        slots=slots
    )

def create_log_cabin_blueprint() -> FireBlueprint:
    slots = [
        # Base tier 1 (North-South)
        BlueprintSlot("base_1", "log", np.array([0.18, 0.06, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.45, 0.06])),
        BlueprintSlot("base_2", "log", np.array([-0.18, 0.06, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.45, 0.06])),
        # Center tinder
        BlueprintSlot("center_tinder", "tinder", np.array([0.0, 0.05, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.15, 0.04])),
        # Tier 2 (East-West cross-hatch)
        BlueprintSlot("tier2_1", "log", np.array([0.0, 0.16, 0.18]), np.array([0.0, 90.0, 0.0]), np.array([0.45, 0.05])),
        BlueprintSlot("tier2_2", "log", np.array([0.0, 0.16, -0.18]), np.array([0.0, 90.0, 0.0]), np.array([0.45, 0.05])),
        # Tier 3 (North-South cross-hatch)
        BlueprintSlot("tier3_1", "log", np.array([0.14, 0.26, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.40, 0.05])),
        BlueprintSlot("tier3_2", "log", np.array([-0.14, 0.26, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.40, 0.05])),
    ]
    return FireBlueprint(
        name="Log Cabin Fire",
        key="log_cabin",
        description="Square cross-hatch chimney providing balanced multi-directional air intake and sustained coal bed.",
        ideal_use="Cooking, long-duration warmth, enduring glowing coal foundation.",
        draft_profile="High-volume, multi-directional lateral intake with stable internal heat trap.",
        slots=slots
    )

def create_lean_to_blueprint() -> FireBlueprint:
    slots = [
        # Heavy windward back-log reflector
        BlueprintSlot("reflector", "log", np.array([0.0, 0.12, -0.25]), np.array([0.0, 90.0, 0.0]), np.array([0.65, 0.10])),
        BlueprintSlot("center_tinder", "tinder", np.array([0.0, 0.05, -0.05]), np.array([0.0, 0.0, 0.0]), np.array([0.15, 0.04])),
        # Sticks leaning against back-log
        BlueprintSlot("lean_1", "kindling", np.array([-0.15, 0.12, -0.10]), np.array([-30.0, 0.0, 0.0]), np.array([0.40, 0.03])),
        BlueprintSlot("lean_2", "kindling", np.array([0.0, 0.12, -0.10]), np.array([0.0, 0.0, 0.0]), np.array([0.40, 0.03])),
        BlueprintSlot("lean_3", "kindling", np.array([0.15, 0.12, -0.10]), np.array([30.0, 0.0, 0.0]), np.array([0.40, 0.03])),
    ]
    return FireBlueprint(
        name="Lean-To Fire",
        key="lean_to",
        description="Wind-deflecting shelter layout utilizing a thick back-log as thermal reflector and shield.",
        ideal_use="High wind conditions, directional heat reflection toward shelter.",
        draft_profile="Windward barrier deflecting gusts; draft pulled in from lee side.",
        slots=slots
    )

def create_swedish_torch_blueprint() -> FireBlueprint:
    slots = [
        # 4 vertical quarters of split log with central bore
        BlueprintSlot("quarter_1", "log", np.array([0.07, 0.25, 0.07]), np.array([90.0, 0.0, 0.0]), np.array([0.50, 0.06])),
        BlueprintSlot("quarter_2", "log", np.array([-0.07, 0.25, 0.07]), np.array([90.0, 0.0, 0.0]), np.array([0.50, 0.06])),
        BlueprintSlot("quarter_3", "log", np.array([0.07, 0.25, -0.07]), np.array([90.0, 0.0, 0.0]), np.array([0.50, 0.06])),
        BlueprintSlot("quarter_4", "log", np.array([-0.07, 0.25, -0.07]), np.array([90.0, 0.0, 0.0]), np.array([0.50, 0.06])),
        # Center bore shavings
        BlueprintSlot("bore_tinder", "tinder", np.array([0.0, 0.35, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.20, 0.03])),
    ]
    return FireBlueprint(
        name="Swedish Torch (Canadian Candle)",
        key="swedish_torch",
        description="Single vertical log split into quarters with central bore packed with shavings. Self-feeding torch.",
        ideal_use="Cooking platform, snow surfaces, efficient fuel conservation.",
        draft_profile="Narrow central bore produces concentrated vertical torch flame with high velocity chimney effect.",
        slots=slots
    )

def create_star_fire_blueprint() -> FireBlueprint:
    slots = [
        BlueprintSlot("center_coals", "tinder", np.array([0.0, 0.05, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.15, 0.05])),
        BlueprintSlot("spoke_1", "log", np.array([0.35, 0.05, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.50, 0.05])),
        BlueprintSlot("spoke_2", "log", np.array([-0.35, 0.05, 0.0]), np.array([0.0, 0.0, 0.0]), np.array([0.50, 0.05])),
        BlueprintSlot("spoke_3", "log", np.array([0.0, 0.05, 0.35]), np.array([0.0, 90.0, 0.0]), np.array([0.50, 0.05])),
        BlueprintSlot("spoke_4", "log", np.array([0.0, 0.05, -0.35]), np.array([0.0, 90.0, 0.0]), np.array([0.50, 0.05])),
    ]
    return FireBlueprint(
        name="Star Fire",
        key="star",
        description="Radial layout of logs pointing toward central ember bed like spokes; pushed inward as tips consume.",
        ideal_use="Overnight burning, low wood consumption, controlled smolder.",
        draft_profile="Lateral spokes channel steady low-velocity draft into center coal bed.",
        slots=slots
    )

ALL_BLUEPRINTS: Dict[str, FireBlueprint] = {
    "teepee": create_teepee_blueprint(),
    "log_cabin": create_log_cabin_blueprint(),
    "lean_to": create_lean_to_blueprint(),
    "swedish_torch": create_swedish_torch_blueprint(),
    "star": create_star_fire_blueprint(),
}
