"""
Firestarter - Smartphone OS & Application State Machine
Implements Section 5.1 & Section 8.1 SmartphoneOS architecture.
"""

from enum import Enum
import numpy as np
from typing import Dict, Any, Optional
from firestarter.economy.credits import CreditSystem
from firestarter.economy.store import StoreApp
from firestarter.economy.topomap import TopographicalMap

class PhoneAppType(Enum):
    STORE = "Store ($)"
    TOPO_MAP = "Topographical Map"

class SmartphoneOS:
    def __init__(self, credit_system: Optional[CreditSystem] = None):
        self.credits = credit_system if credit_system is not None else CreditSystem()
        self.store = StoreApp()
        self.topo_map = TopographicalMap()
        
        self.is_open = False
        self.active_app = PhoneAppType.STORE
        self.battery_percent = 94.0
        
        # Phone screen visual dimensions
        self.screen_width = 360
        self.screen_height = 640
        self.status_message = "Ready"

    def toggle(self) -> bool:
        self.is_open = not self.is_open
        return self.is_open

    def switch_app(self, app_type: PhoneAppType):
        self.active_app = app_type
        self.status_message = f"Opened {app_type.value}"

    def next_app(self):
        apps = list(PhoneAppType)
        idx = (apps.index(self.active_app) + 1) % len(apps)
        self.switch_app(apps[idx])

    def prev_app(self):
        apps = list(PhoneAppType)
        idx = (apps.index(self.active_app) - 1) % len(apps)
        self.switch_app(apps[idx])

    def handle_input(self, action: str) -> Dict[str, Any]:
        """
        Processes phone interaction: 'up', 'down', 'select', 'switch'.
        """
        if not self.is_open:
            return {"handled": False}

        if action == "switch":
            self.next_app()
            return {"handled": True, "app": self.active_app.value}

        if self.active_app == PhoneAppType.STORE:
            if action == "down":
                self.store.select_next()
                return {"handled": True, "selected": self.store.selected_index}
            elif action == "up":
                self.store.select_prev()
                return {"handled": True, "selected": self.store.selected_index}
            elif action == "select":
                res = self.store.purchase_selected(self.credits)
                self.status_message = res["message"]
                return {"handled": True, "purchase": res}

        elif self.active_app == PhoneAppType.TOPO_MAP:
            # Map navigation / panning
            return {"handled": True, "app": "map"}

        return {"handled": False}

    def get_display_state(self, player_pos: np.ndarray, ambient_temp: float) -> Dict[str, Any]:
        """Returns complete state for UI overlay renderer."""
        zone_name, humidity = self.topo_map.get_microclimate_at(player_pos[0], player_pos[2])
        return {
            "is_open": self.is_open,
            "active_app": self.active_app.value,
            "credits": self.credits.credits,
            "battery": self.battery_percent,
            "status": self.status_message,
            "gps_coords": (round(player_pos[0], 1), round(player_pos[2], 1)),
            "ambient_temp": round(ambient_temp, 1),
            "zone_name": zone_name,
            "humidity": round(humidity * 100.0, 0),
            "store_catalog": [
                {
                    "name": it.name,
                    "cost": it.cost,
                    "desc": it.description,
                    "cat": it.category,
                    "is_selected": (i == self.store.selected_index)
                }
                for i, it in enumerate(self.store.catalog)
            ],
            "map_waypoints": [
                {"name": wp.name, "pos": wp.position, "symbol": wp.symbol}
                for wp in self.topo_map.waypoints
            ]
        }
