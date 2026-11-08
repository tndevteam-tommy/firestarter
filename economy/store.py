"""
Firestarter - Smartphone Store App
Implements Section 5.1 Store catalog and purchase transactions.
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Any
from firestarter.economy.credits import CreditSystem

@dataclass
class StoreItem:
    item_id: str
    name: str
    cost: float
    description: str
    category: str

DEFAULT_CATALOG: List[StoreItem] = [
    StoreItem(
        item_id="lighter_refill",
        name="Pocket Lighter Refill Fluid",
        cost=45.0,
        description="Refills your pocket lighter with 4 fresh fire starts.",
        category="Accelerants & Fire"
    ),
    StoreItem(
        item_id="waterproof_tarp",
        name="Waterproof Polyethylene Tarp",
        cost=110.0,
        description="Shields raised drying racks from rain to season timber to 12% EMC.",
        category="Shelter & Seasoning"
    ),
    StoreItem(
        item_id="steel_knife",
        name="High-Carbon Steel Pocket Knife",
        cost=140.0,
        description="Razor-sharp edge for clean wood ribbons and rapid bark strip harvesting.",
        category="Tools"
    ),
    StoreItem(
        item_id="steel_axe",
        name="Drop-Forged Felling Axe",
        cost=240.0,
        description="Heavy-duty steel bit for felling mature hardwoods and splitting logs.",
        category="Tools"
    ),
    StoreItem(
        item_id="gasoline_canister",
        name="Gasoline Canister (1 Gallon)",
        cost=280.0,
        description="High-octane accelerant. Explosive volatility that instantly overcomes wet green timber.",
        category="Accelerants & Fire"
    ),
    StoreItem(
        item_id="reference_book_advanced",
        name="Field Reference Book Editions",
        cost=75.0,
        description="Unlocks Swedish Torch, Lean-To, and Star Fire architectural blueprints.",
        category="Knowledge"
    ),
]

class StoreApp:
    def __init__(self, catalog: Optional[List[StoreItem]] = None):
        self.catalog = catalog if catalog is not None else list(DEFAULT_CATALOG)
        self.selected_index = 0

    def select_next(self):
        self.selected_index = (self.selected_index + 1) % len(self.catalog)

    def select_prev(self):
        self.selected_index = (self.selected_index - 1) % len(self.catalog)

    def purchase_selected(self, credit_system: CreditSystem) -> Dict[str, Any]:
        item = self.catalog[self.selected_index]
        if credit_system.spend(item.cost):
            return {
                "success": True,
                "item_id": item.item_id,
                "name": item.name,
                "message": f"Purchased {item.name} for {item.cost:.1f} credits."
            }
        return {
            "success": False,
            "item_id": item.item_id,
            "name": item.name,
            "message": f"Insufficient credits! Need {item.cost:.1f}, have {credit_system.credits:.1f}."
        }
