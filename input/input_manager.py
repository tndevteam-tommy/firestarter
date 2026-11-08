"""
Firestarter - InputManager & Tutorial Progression
Implements game controls table and guided early-game tutorial walkthrough.
"""

from typing import Dict, Any, Optional
from firestarter.simulation.world_manager import WorldManager
from firestarter.economy.smartphone import SmartphoneOS
from firestarter.recipes.reference_book import ReferenceBook
from firestarter.input.hand_physics_rig import HandController

class InputManager:
    def __init__(
        self,
        world: WorldManager,
        phone: SmartphoneOS,
        ref_book: ReferenceBook,
        hands: HandController
    ):
        self.world = world
        self.phone = phone
        self.ref_book = ref_book
        self.hands = hands
        
        # Tutorial progression state
        self.tutorial_step = 1
        self.tutorial_hints = {
            1: "Tutorial 1/5: Pick up birch shavings & cedar tinder. Inspect fire hearth with Mouse Look.",
            2: "Tutorial 2/5: Stack kindling twigs into a mini-teepee around the tinder (RMB to place, Scroll to rotate).",
            3: "Tutorial 3/5: Equip Pocket Lighter [1] and click LMB to strike sparks and pilot flame.",
            4: "Tutorial 4/5: Press 'F' to deliver controlled rhythmic breaths of air into ember core (>550°C).",
            5: "Tutorial 5/5: Press 'Tab' to open your Wilderness Smartphone and claim fire mastery credits!"
        }
        self.is_paused = False

    def handle_key_down(self, key_name: str) -> Dict[str, Any]:
        """Processes key press events."""
        key = key_name.lower()
        
        # Menu toggles
        if key == "tab":
            is_open = self.phone.toggle()
            if is_open and self.tutorial_step == 5:
                self.world.notify("Smartphone opened! Browse the Store app ($) or Topo Map.", 4.0)
            return {"action": "toggle_phone", "is_open": is_open}

        elif key == "b":
            is_open = self.ref_book.toggle()
            return {"action": "toggle_book", "is_open": is_open}

        elif key == "t":
            is_open = self.world.time_engine.toggle_menu()
            return {"action": "toggle_time_menu", "is_open": is_open}

        elif key == "escape":
            if self.phone.is_open:
                self.phone.is_open = False
                return {"action": "close_phone"}
            elif self.ref_book.is_open:
                self.ref_book.is_open = False
                return {"action": "close_book"}
            elif self.world.time_engine.is_menu_open:
                self.world.time_engine.is_menu_open = False
                return {"action": "close_time_menu"}
            else:
                self.is_paused = not self.is_paused
                return {"action": "toggle_pause", "paused": self.is_paused}

        # Sub-menu navigation if open
        if self.phone.is_open:
            if key in ("up", "w"):
                return self.phone.handle_input("up")
            elif key in ("down", "s"):
                return self.phone.handle_input("down")
            elif key in ("return", "space", "e"):
                return self.phone.handle_input("select")
            elif key in ("left", "right", "q"):
                return self.phone.handle_input("switch")
            return {"action": "phone_input"}

        if self.ref_book.is_open:
            if key in ("right", "d", "space"):
                self.ref_book.next_page()
            elif key in ("left", "a"):
                self.ref_book.prev_page()
            return {"action": "book_page"}

        if self.world.time_engine.is_menu_open:
            if key in ("down", "s"):
                self.world.time_engine.next_option()
            elif key in ("up", "w"):
                self.world.time_engine.prev_option()
            elif key in ("return", "space", "e"):
                res = self.world.time_engine.execute_selected_skip(self.world.apply_time_skip)
                return {"action": "time_skip", "result": res}
            return {"action": "time_menu_nav"}

        # Game action keys
        if key == "f":
            # Breathe / Blow
            self.hands.blow_phase = 1.0
            res = self.world.blow_breath()
            if self.tutorial_step == 4:
                self.tutorial_step = 5
            return {"action": "blow_breath", "result": res}

        # Quick tool slots [1 - 5]
        tools = {
            "1": "pocket_lighter",
            "2": "pocket_knife",
            "3": "felling_axe",
            "4": "bow_drill_spindle",
            "5": "kindling"
        }
        if key in tools:
            self.world.player.primary_hand = tools[key]
            self.world.notify(f"Equipped: {tools[key].replace('_', ' ').title()}", 2.0)
            if key == "1" and self.tutorial_step == 3:
                self.tutorial_step = 4
            return {"action": "equip_tool", "tool": tools[key]}

        return {"action": "none"}

    def handle_mouse_button_down(self, button: int) -> Dict[str, Any]:
        """
        button 1: LMB (primary hand / strike / carve)
        button 3: RMB (secondary hand / place / hold)
        button 4/5: Scroll up / down (rotate item)
        """
        if button == 1:
            # LMB
            res = self.world.interact_primary()
            if self.tutorial_step == 1:
                self.tutorial_step = 2
            elif self.tutorial_step == 3 and res.get("success"):
                self.tutorial_step = 4
            return {"action": "primary_interact", "result": res}

        elif button == 3:
            # RMB
            res = self.world.interact_secondary()
            if self.tutorial_step == 2:
                self.tutorial_step = 3
            return {"action": "secondary_interact", "result": res}

        elif button == 4: # Scroll Up
            self.world.player.rotate_held_item(15.0)
            return {"action": "rotate_item", "rot": self.world.player.held_item_rotation}

        elif button == 5: # Scroll Down
            self.world.player.rotate_held_item(-15.0)
            return {"action": "rotate_item", "rot": self.world.player.held_item_rotation}

        return {"action": "none"}

    def get_tutorial_hint(self) -> str:
        return self.tutorial_hints.get(self.tutorial_step, "")
