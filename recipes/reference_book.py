"""
Firestarter - Reference Book UI & Knowledge Base
Implements Section 6 Reference Book ('B' key) interface.
"""

from typing import List, Dict, Any, Optional
from firestarter.recipes.blueprints import ALL_BLUEPRINTS, FireBlueprint

class ReferenceBook:
    def __init__(self):
        self.is_open = False
        self.current_page = 0
        self.total_pages = 10
        self.selected_blueprint_key: Optional[str] = "teepee"

    def toggle(self) -> bool:
        self.is_open = not self.is_open
        return self.is_open

    def next_page(self):
        self.current_page = (self.current_page + 1) % self.total_pages

    def prev_page(self):
        self.current_page = (self.current_page - 1) % self.total_pages

    def select_blueprint_for_overlay(self, key: str):
        if key in ALL_BLUEPRINTS:
            self.selected_blueprint_key = key

    def get_current_page_data(self) -> Dict[str, Any]:
        """Provides page text, equations, and diagrams for rendering."""
        pages = [
            {
                "title": "I. The Four-Stage Combustion State Machine",
                "subtitle": "Thermodynamics & Organic Chemistry",
                "content": (
                    "1. Dehydration (100°C - 120°C): Endothermic water boil-off (absorbs 2,260 kJ/kg). Temp clamped near 100°C.\n"
                    "2. Pyrolysis (200°C - 450°C): Thermal breakdown of hemicellulose, cellulose, and lignin. Emits volatile smoke.\n"
                    "3. Flaming Combustion (>450°C, O2 > 12%): Exothermic gas-phase flame. Radiates thermal energy into fuel bed.\n"
                    "4. Char Oxidation (500°C - 900°C): Solid carbon oxidation: C + O2 -> CO2 + 393.5 kJ/mol. Long-wave IR.\n"
                    "5. Mineral Ash: Insulating mineral blanket; reduces O2 diffusion unless cleared or blown upon."
                )
            },
            {
                "title": "II. Wood Species Cellular Matrix",
                "subtitle": "Fuel Chemistry & Density",
                "content": (
                    "• White Pine: Softwood (380 kg/m³), 18.5% terpenes resin, 18.2 MJ/kg charcoal. Fast ignition.\n"
                    "• Red Cedar: Softwood (360 kg/m³), 22.0% resin oils, 17.8 MJ/kg charcoal. Flaring ribbons.\n"
                    "• Paper Birch: Hardwood (650 kg/m³), 14.0% bark betulin, 22.4 MJ/kg. Burns even when damp.\n"
                    "• White Oak: Hardwood (780 kg/m³), 4.2% volatiles, 28.6 MJ/kg charcoal. Enduring coal beds.\n"
                    "• Punk Wood: Decayed fibers (120 kg/m³), 1.0% resin, 12.0 MJ/kg. Sponge; bone-dry smolders easily."
                )
            },
            {
                "title": "III. Airflow & The Convective Chimney",
                "subtitle": "The Stack Effect & Base Vacuum",
                "content": (
                    "Updraft Velocity: U_draft = C_d * sqrt(2 * g * H * (T_int - T_amb) / T_int)\n"
                    "Base Vacuum Draw: P_base = P_amb - 0.5 * rho_air * U_draft^2\n"
                    "A tall structure (high H) accelerates draft velocity, pulling ambient oxygen into the ember bed.\n"
                    "WARNING: If log gap spacing is under 2 cm, C_d -> 0 and oxygen saturation drops below 10%, "
                    "smothering flames into noxious carbon monoxide smoke."
                )
            },
            {
                "title": "IV. Architecture: Teepee Fire",
                "subtitle": "Rapid Ignition & High Draft",
                "content": (
                    "Structure: Conical kindling arrangement surrounding center tinder nest.\n"
                    "Thermodynamics: Maximizes vertical chimney height H, yielding strong updraft velocity.\n"
                    "Best For: Quickly generating flame from a spark, boiling water, emergency signalling."
                )
            },
            {
                "title": "V. Architecture: Log Cabin Fire",
                "subtitle": "Balanced Multi-Directional Intake",
                "content": (
                    "Structure: Alternating orthogonal log tiers forming a square cross-hatch chimney.\n"
                    "Thermodynamics: Large intake pathways feed stable oxygen to a massive central coal bed.\n"
                    "Best For: Camp cooking, enduring coals, all-night warmth without collapsing."
                )
            },
            {
                "title": "VI. Architecture: Lean-To Fire",
                "subtitle": "Wind Reflector & Deflector",
                "content": (
                    "Structure: Heavy windward back-log acts as barrier, with kindling leaning against its lee side.\n"
                    "Thermodynamics: Deflects harsh gusts while radiating reflective infrared heat toward shelter.\n"
                    "Best For: High wind, blizzards, cold mountain ridges."
                )
            },
            {
                "title": "VII. Architecture: Swedish Torch",
                "subtitle": "Canadian Candle Single-Log Burner",
                "content": (
                    "Structure: Single vertical standing log quartered with axe cuts, center bore filled with shavings.\n"
                    "Thermodynamics: Narrow internal bore creates extreme stack velocity torch flame.\n"
                    "Best For: Flat cooking stove surface on top, burns directly on top of snow or mud."
                )
            },
            {
                "title": "VIII. Architecture: Star Fire",
                "subtitle": "Radial Low-Fuel Smolder",
                "content": (
                    "Structure: Logs placed horizontally pointing inward toward center coals like spokes of a wheel.\n"
                    "Thermodynamics: Only log tips combust in the core; pushed inward as wood is consumed.\n"
                    "Best For: Extreme fuel conservation, long night sleep without constant stoking."
                )
            },
            {
                "title": "IX. Bushcraft Friction & Bow Drill",
                "subtitle": "Mechanical Power Dissipation",
                "content": (
                    "Power: P = mu * F_N * omega * r_spindle\n"
                    "Carve a 45-degree V-notch in the hearthboard touching the socket.\n"
                    "Abraded wood dust collects in the notch. When friction elevates temperature above 380°C, "
                    "the dust ignites into a microscopic self-sustaining coal. Nest into dry tinder and blow rhythmically."
                )
            },
            {
                "title": "X. Seasoning, Tarps & Platforms",
                "subtitle": "Equilibrium Moisture Content (EMC)",
                "content": (
                    "Living sapwood moisture exceeds 80%. Green wood will hiss and sputter out.\n"
                    "Build Raised Platforms to eliminate ground capillary water transfer (J_ground = 0).\n"
                    "Add Waterproof Tarp to stop rain (P_rain = 0) while allowing lateral drying breeze.\n"
                    "In 60 in-game days under summer tarp, timber reaches optimal 12% equilibrium moisture."
                )
            }
        ]
        return {
            "page_number": self.current_page + 1,
            "total_pages": self.total_pages,
            **pages[self.current_page],
            "blueprint": ALL_BLUEPRINTS.get(self.selected_blueprint_key)
        }
