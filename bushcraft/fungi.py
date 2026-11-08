"""
Firestarter - Smoldering Fungi (Amadou & Chaga)
Implements Section 3.4:
Birch Polypore (Piptoporus betulinus) and Tinder Fungus (Fomes fomentarius / Chaga).
Trama layer smolders at 0.5 - 1.5 cm/hour without flame, serving as ember carrier.
"""

from enum import Enum
from typing import Dict, Any, Optional

class FungusType(Enum):
    BIRCH_POLYPORE = "Birch Polypore (Piptoporus betulinus)"
    TINDER_FUNGUS = "Tinder Fungus (Fomes fomentarius)"
    CHAGA = "Chaga (Inonotus obliquus)"

class SmolderingFungus:
    def __init__(
        self,
        fungus_type: FungusType = FungusType.TINDER_FUNGUS,
        diameter_cm: float = 8.0,
        moisture: float = 0.08,
        is_smoldering: bool = False,
        smolder_temp_c: float = 350.0
    ):
        self.fungus_type = fungus_type
        self.diameter_cm = diameter_cm
        self.initial_diameter_cm = diameter_cm
        self.moisture = moisture
        self.is_smoldering = is_smoldering
        self.core_temp = smolder_temp_c if is_smoldering else 20.0
        
        # Controlled smolder burn rate (0.5 - 1.5 cm/hour -> cm/sec)
        # 1.0 cm/hr = 1.0 / 3600 cm/s ~ 2.77e-4 cm/s
        self.burn_rate_cm_per_sec = 1.0 / 3600.0
        self.smoke_rate = 0.0

    def catch_spark_or_ember(self, contact_temp_c: float) -> bool:
        """When dried, amadou/chaga catches even faint sparks easily."""
        if self.moisture > 0.20:
            return False # Too damp to take a spark
        if contact_temp_c >= 250.0:
            self.is_smoldering = True
            self.core_temp = max(320.0, contact_temp_c)
            return True
        return False

    def update(self, dt: float, ambient_temp: float = 20.0):
        if not self.is_smoldering:
            self.smoke_rate = 0.0
            return

        # Advance smolder boundary through trama layer
        consumed_cm = self.burn_rate_cm_per_sec * dt
        self.diameter_cm -= consumed_cm
        self.smoke_rate = 0.05 # gentle aromatic wisp of smoke
        self.core_temp = max(300.0, min(450.0, self.core_temp))

        # Check if exhausted
        if self.diameter_cm <= 0.2:
            self.is_smoldering = False
            self.diameter_cm = 0.0
            self.core_temp = ambient_temp

    def transfer_ember_to_tinder(self) -> Optional[float]:
        """Touches glowing trama core to tinder nest to ignite it."""
        if self.is_smoldering and self.diameter_cm > 0.5:
            return self.core_temp
        return None

    @property
    def remaining_hours(self) -> float:
        """Hours of smolder life remaining."""
        if self.burn_rate_cm_per_sec <= 0:
            return 0.0
        return (self.diameter_cm / self.burn_rate_cm_per_sec) / 3600.0

    def get_state(self) -> Dict[str, Any]:
        return {
            "type": self.fungus_type.value,
            "diameter_cm": self.diameter_cm,
            "is_smoldering": self.is_smoldering,
            "core_temp": self.core_temp,
            "moisture": self.moisture,
            "remaining_hours": self.remaining_hours
        }
