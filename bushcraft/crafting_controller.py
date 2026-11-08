"""
Firestarter - Bushcraft Crafting Controller
Coordinates two-handed bushcraft operations: knife carving, cordage twisting,
lighter strikes, bow drill friction, and ember nesting.
"""

from typing import Dict, Any, Optional, List
from firestarter.bushcraft.bow_drill import BowDrillSystem
from firestarter.bushcraft.hand_drill import HandDrillSystem
from firestarter.bushcraft.tinder_nest import TinderNest
from firestarter.bushcraft.fungi import SmolderingFungus, FungusType

class BushcraftCraftingController:
    def __init__(self):
        # Tools & gear
        self.has_pocket_knife = True
        self.knife_sharpness = 1.0
        self.axe_type = "stone" # "stone" or "steel"
        self.axe_durability = 1.0
        
        # Pocket lighter with limited fluid
        self.lighter_fluid_starts = 4
        self.lighter_is_lit = False
        
        # Cordage inventory
        self.raw_bark_strips = 3
        self.two_ply_cordage_pieces = 1
        
        # Active crafting systems
        self.bow_drill = BowDrillSystem(has_v_notch=False)
        self.hand_drill = HandDrillSystem()
        self.active_tinder_nest: Optional[TinderNest] = TinderNest()
        self.smoldering_fungus: Optional[SmolderingFungus] = None
        
        # Whittled shavings and kindling twigs in hand
        self.fine_shavings_count = 5
        self.dry_kindling_twigs = 8
        
        # Player stamina (0.0 to 100.0)
        self.stamina = 100.0
        self.active_task = "idle" # "idle", "whittling", "twisting_cordage", "bow_drilling", "blowing"
        
        # Audio / ASMR event cue
        self.audio_trigger = None

    def whittle_shavings(self) -> Dict[str, Any]:
        """Player uses pocket knife to whittle crisp shavings ribbons."""
        if not self.has_pocket_knife:
            return {"success": False, "message": "Pocket knife required to whittle shavings."}
            
        self.fine_shavings_count += 3
        self.knife_sharpness = max(0.2, self.knife_sharpness - 0.01)
        self.audio_trigger = "whittle"
        return {
            "success": True,
            "message": "Carved crisp ribbons of dry cedar shavings.",
            "shavings_count": self.fine_shavings_count
        }

    def strip_tree_bark(self) -> Dict[str, Any]:
        """Harvests inner fibrous cambium bark for cordage."""
        self.raw_bark_strips += 2
        self.audio_trigger = "whittle"
        return {
            "success": True,
            "message": "Stripped long fibers of inner basswood/cedar cambium bark.",
            "bark_strips": self.raw_bark_strips
        }

    def twist_two_ply_cordage(self) -> Dict[str, Any]:
        """Two-handed reverse-wrap twisting of cambium fibers into high-tensile cordage."""
        if self.raw_bark_strips < 2:
            return {"success": False, "message": "Need at least 2 strips of inner bark fibers."}
            
        self.raw_bark_strips -= 2
        self.two_ply_cordage_pieces += 1
        self.audio_trigger = "cordage_twist"
        return {
            "success": True,
            "message": "Twisted strong two-ply reverse wrap cordage.",
            "cordage_count": self.two_ply_cordage_pieces
        }

    def carve_hearthboard_notch(self) -> Dict[str, Any]:
        """Carves a 45-degree V-notch collector into the hearthboard."""
        if not self.has_pocket_knife:
            return {"success": False, "message": "Pocket knife required."}
        self.bow_drill.carve_v_notch()
        self.audio_trigger = "whittle"
        return {"success": True, "message": "Carved 45-degree V-notch into hearthboard."}

    def stroke_bow_drill(self, downward_force_n: float = 55.0, stroke_speed_m_s: float = 1.2, dt: float = 0.1) -> Dict[str, Any]:
        """Executes bow drill stroking motion."""
        self.active_task = "bow_drilling"
        res = self.bow_drill.stroke(
            stroke_length_m=0.35,
            stroke_speed_m_s=stroke_speed_m_s,
            downward_force_n=downward_force_n,
            dt=dt
        )
        self.audio_trigger = "friction_squeak"
        self.stamina = max(0.0, self.stamina - 6.0 * dt)
        return res

    def strike_lighter(self) -> Dict[str, Any]:
        """Strikes pocket lighter."""
        if self.lighter_fluid_starts <= 0:
            return {"success": False, "message": "Pocket lighter is out of fluid!"}
            
        self.lighter_fluid_starts -= 1
        self.lighter_is_lit = True
        self.audio_trigger = "spark"
        return {
            "success": True,
            "message": "Lighter struck! Pilot flame active.",
            "starts_remaining": self.lighter_fluid_starts
        }

    def blow_tinder(self, breath_velocity: float = 2.5, dt: float = 0.2) -> Dict[str, Any]:
        """Breathing mechanic ('F' key)."""
        self.audio_trigger = "breath"
        if not self.active_tinder_nest:
            return {"status": "no_tinder", "is_flaming": False}
        return self.active_tinder_nest.blow(breath_velocity, dt)

    def transfer_ember_to_nest(self) -> Dict[str, Any]:
        """Transfers ember from bow drill or fungi into tinder nest."""
        ember_t = self.bow_drill.extract_ember()
        if ember_t is None and self.smoldering_fungus:
            ember_t = self.smoldering_fungus.transfer_ember_to_tinder()
            
        if ember_t is None:
            return {"success": False, "message": "No active ember found to transfer!"}
            
        if not self.active_tinder_nest:
            self.active_tinder_nest = TinderNest()
            
        self.active_tinder_nest.insert_ember(ember_t)
        return {"success": True, "message": "Gently rolled glowing coal into dry tinder nest!"}

    def update(self, dt: float, ambient_temp: float = 20.0):
        # Regenerate stamina when idle
        if self.active_task == "idle":
            self.stamina = min(100.0, self.stamina + 10.0 * dt)
        self.active_task = "idle"
        
        # Step active tinder nest and smoldering fungi
        if self.active_tinder_nest:
            self.active_tinder_nest.update(dt, ambient_temp)
        if self.smoldering_fungus:
            self.smoldering_fungus.update(dt, ambient_temp)
