"""
Firestarter - WorldManager Subsystem
Implements Section 8 Architecture:
Coordinates Terrain, Weather, Ecosystem, ThermodynamicGrid, BushcraftCrafting,
Player, and Seasoning Racks on fixed 60Hz physics & 20Hz thermal tick rates.
"""

import math
import numpy as np
from typing import List, Dict, Any, Optional, Tuple

from firestarter.config import PHYSICS_DT, THERMAL_DT
from firestarter.thermodynamics.combustion_body import CombustionBody, CombustionStage
from firestarter.thermodynamics.wood_properties import WoodSpeciesType
from firestarter.thermodynamics.thermal_grid import ThermodynamicGrid
from firestarter.bushcraft.crafting_controller import BushcraftCraftingController
from firestarter.forestry.tree import Tree, TreeGrowthStage
from firestarter.forestry.felling import TreeFellingSystem
from firestarter.forestry.seasoning import RaisedDryingRack, GroundSeasoningSimulator
from firestarter.forestry.ecosystem import ForestEcosystem
from firestarter.simulation.weather import WeatherSystem
from firestarter.simulation.time_engine import TimeEngine
from firestarter.simulation.player import Player
from firestarter.recipes.blueprints import ALL_BLUEPRINTS

class WorldManager:
    def __init__(self):
        # Subsystems
        self.weather = WeatherSystem()
        self.time_engine = TimeEngine()
        self.ecosystem = ForestEcosystem()
        self.thermal_grid = ThermodynamicGrid()
        self.crafting = BushcraftCraftingController()
        self.player = Player()
        
        # Primary Campfire Pit location
        self.fire_pit_pos = np.array([0.0, 0.05, 0.0])
        
        # Raised drying rack near camp
        self.drying_rack = RaisedDryingRack(
            position=np.array([3.5, 0.4, 1.5]),
            has_tarp=False
        )
        
        # Ground unshielded seasoning logs
        self.ground_logs: List[CombustionBody] = []
        
        # Accumulated fixed tick accumulators
        self.physics_accumulator = 0.0
        self.thermal_accumulator = 0.0
        
        # Message notification banner
        self.notification = "Welcome to Firestarter. Inspect your surroundings and build your first fire."
        self.notification_timer = 8.0
        
        # Initial tutorial setup: place initial tinder nest and dry shavings in pit
        self._setup_initial_camp()

    def _setup_initial_camp(self):
        # 1. Base dry tinder nest in center
        tinder = CombustionBody(
            species=WoodSpeciesType.RED_CEDAR,
            dry_mass=0.03,
            initial_m_surface=0.08,
            initial_m_core=0.08,
            geometry_type="tinder",
            position=np.array([0.0, 0.05, 0.0]),
            dimensions=np.array([0.15, 0.04])
        )
        self.thermal_grid.add_body(tinder)

        # 2. Dry kindling sticks leaning around tinder
        for i in range(4):
            angle = i * (math.pi / 2.0)
            k_pos = np.array([math.cos(angle) * 0.12, 0.12, math.sin(angle) * 0.12])
            kindling = CombustionBody(
                species=WoodSpeciesType.WHITE_PINE,
                dry_mass=0.15,
                initial_m_surface=0.10,
                initial_m_core=0.12,
                geometry_type="kindling",
                position=k_pos,
                dimensions=np.array([0.30, 0.015])
            )
            self.thermal_grid.add_body(kindling)

        # 3. Add green log on ground to demonstrate rotting & seasoning difference
        green_log = CombustionBody(
            species=WoodSpeciesType.WHITE_OAK,
            dry_mass=6.0,
            initial_m_surface=0.80,
            initial_m_core=1.10,
            geometry_type="log",
            position=np.array([-4.0, 0.1, 2.0]),
            dimensions=np.array([0.7, 0.09])
        )
        green_log.is_on_ground = True
        self.ground_logs.append(green_log)

    def notify(self, msg: str, duration: float = 4.0):
        self.notification = msg
        self.notification_timer = duration

    def update(self, frame_dt: float):
        """Advances physics (60Hz) and thermal grid (20Hz) with fixed time steps."""
        # Notification decay
        if self.notification_timer > 0.0:
            self.notification_timer = max(0.0, self.notification_timer - frame_dt)
            if self.notification_timer <= 0.0:
                self.notification = ""

        # Physics tick (60 Hz)
        self.physics_accumulator += min(0.1, frame_dt)
        while self.physics_accumulator >= PHYSICS_DT:
            self._update_physics(PHYSICS_DT)
            self.physics_accumulator -= PHYSICS_DT

        # Thermal tick (20 Hz)
        self.thermal_accumulator += min(0.1, frame_dt)
        while self.thermal_accumulator >= THERMAL_DT:
            self._update_thermodynamics(THERMAL_DT)
            self.thermal_accumulator -= THERMAL_DT

    def _update_physics(self, dt: float):
        # Update falling trees
        for tree in self.ecosystem.trees:
            if tree.is_falling:
                hit_ground, spawned = TreeFellingSystem.update_falling_tree(tree, dt)
                if hit_ground:
                    self.notify(f"{tree.species.value} crashed onto ground! Branches broken into kindling.", 5.0)
                    for b in spawned:
                        self.ground_logs.append(b)

        # Step bushcraft crafting controllers
        self.crafting.update(dt, self.weather.ambient_temp_c)

    def _update_thermodynamics(self, dt: float):
        # Step thermal grid with active combustion bodies
        self.thermal_grid.update(
            dt=dt,
            ambient_temp=self.weather.ambient_temp_c,
            wind_speed=self.weather.wind_speed_m_s
        )

        # Deposit ash when coals burn down completely
        for b in list(self.thermal_grid.bodies):
            if b.stage == CombustionStage.INERT_ASH and b.ash_mass > 0.1:
                self.ecosystem.add_campfire_ash(b.position, b.ash_mass)
                b.ash_mass = 0.0

    def apply_time_skip(self, hours: float):
        """Called by TimeEngine ('T' key) to fast-forward hours or months."""
        days = hours / 24.0
        self.weather.advance_time(hours)
        
        # Advance seasoning racks
        self.drying_rack.update_seasoning(
            days_passed=days,
            season=self.weather.current_season.value,
            rain_intensity=self.weather.rain_intensity,
            ground_humidity=self.weather.relative_humidity,
            wind_speed=self.weather.wind_speed_m_s
        )

        # Advance ground logs (capillary wetting & fungal decay)
        for log in self.ground_logs:
            GroundSeasoningSimulator.step_ground_log(
                log, days, self.weather.current_season.value,
                self.weather.rain_intensity
            )

        # Advance ecosystem lifecycle
        self.ecosystem.step_ecosystem(days, self.weather.wind_vector)

        # Coals settle or extinguish
        for b in self.thermal_grid.bodies:
            b.t_surface = self.weather.ambient_temp_c
            b.t_internal = self.weather.ambient_temp_c
            if b.stage in (CombustionStage.FLAMING, CombustionStage.CHAR_OXIDATION):
                b.stage = CombustionStage.INERT_ASH

        self.notify(f"Time advanced by {hours:.1f} hours ({self.weather.current_season.value}).", 4.0)

    def interact_primary(self) -> Dict[str, Any]:
        """Player LMB action based on held primary item."""
        item = self.player.primary_hand
        
        if item == "pocket_lighter":
            res = self.crafting.strike_lighter()
            if res["success"]:
                # Ignite nearby tinder
                ignited = 0
                for b in self.thermal_grid.bodies:
                    if b.stage in (CombustionStage.AMBIENT, CombustionStage.DEHYDRATION):
                        dist = np.linalg.norm(b.position - self.fire_pit_pos)
                        if dist < 0.4:
                            b.apply_external_heat(3500.0, 0.4) # intense pilot flame
                            b.t_surface += 220.0
                            ignited += 1
                self.notify(f"Lighter struck! Pilot flame ignited {ignited} fuel pieces.", 3.5)
            else:
                self.notify(res["message"], 3.0)
            return res

        elif item == "pocket_knife":
            # Whittle shavings
            res = self.crafting.whittle_shavings()
            self.notify(res["message"], 3.0)
            return res

        elif item == "felling_axe":
            # Find closest tree to chop
            closest_tree: Optional[Tree] = None
            min_dist = 4.0
            for tree in self.ecosystem.trees:
                dist = np.linalg.norm(tree.position - self.player.position)
                if dist < min_dist:
                    min_dist = dist
                    closest_tree = tree

            if closest_tree:
                if closest_tree.notch_depth_m < (closest_tree.trunk_radius_m * 0.7):
                    res = TreeFellingSystem.chop_notch(closest_tree, self.crafting.axe_type)
                else:
                    res = TreeFellingSystem.chop_backcut(closest_tree, self.crafting.axe_type)
                self.notify(res["message"], 3.0)
                return res
            else:
                self.notify("No tree within chopping reach.", 2.5)
                return {"success": False}

        elif item == "bow_drill_spindle":
            # Bow drill stroke
            res = self.crafting.stroke_bow_drill()
            if res.get("has_ember"):
                self.notify("A glowing coal ember formed in the V-notch!", 5.0)
            else:
                self.notify(f"Bow drill stroking... Temp: {res.get('socket_temp', 0):.1f}°C", 2.0)
            return res

        elif item == "kindling":
            # Add kindling to pit
            k = CombustionBody(
                species=WoodSpeciesType.WHITE_PINE,
                dry_mass=0.20,
                initial_m_surface=0.10,
                initial_m_core=0.12,
                geometry_type="kindling",
                position=self.fire_pit_pos + np.array([np.random.uniform(-0.1, 0.1), 0.1, np.random.uniform(-0.1, 0.1)]),
                dimensions=np.array([0.30, 0.018])
            )
            self.thermal_grid.add_body(k)
            self.notify("Placed dry kindling stick into fire structure.", 2.5)
            return {"success": True}

        return {"success": False}

    def interact_secondary(self) -> Dict[str, Any]:
        """Player RMB action based on held secondary item."""
        item = self.player.secondary_hand
        
        if item == "tinder_nest":
            # Transfer ember from bow drill or place tinder
            if self.crafting.bow_drill.has_ember:
                res = self.crafting.transfer_ember_to_nest()
                self.notify(res["message"], 4.0)
                return res
            else:
                # Add tinder shavings to fire pit
                t = CombustionBody(
                    species=WoodSpeciesType.RED_CEDAR,
                    dry_mass=0.04,
                    initial_m_surface=0.08,
                    initial_m_core=0.08,
                    geometry_type="tinder",
                    position=self.fire_pit_pos + np.array([0.0, 0.05, 0.0]),
                    dimensions=np.array([0.15, 0.04])
                )
                self.thermal_grid.add_body(t)
                self.notify("Nested fresh dry cedar shavings into hearth.", 3.0)
                return {"success": True}

        elif item == "log":
            # Place log into pit with rotation
            rot_rad = math.radians(self.player.held_item_rotation)
            log = CombustionBody(
                species=WoodSpeciesType.WHITE_OAK,
                dry_mass=3.5,
                initial_m_surface=0.15,
                initial_m_core=0.18,
                geometry_type="log",
                position=self.fire_pit_pos + np.array([math.cos(rot_rad)*0.15, 0.18, math.sin(rot_rad)*0.15]),
                orientation=np.array([0.0, self.player.held_item_rotation, 0.0]),
                dimensions=np.array([0.45, 0.06])
            )
            self.thermal_grid.add_body(log)
            self.notify("Positioned fuel log in fire structure.", 2.5)
            return {"success": True}

        return {"success": False}

    def blow_breath(self) -> Dict[str, Any]:
        """Player presses 'F' key to deliver a pulsed breath of air."""
        # 1. Blow into tinder nest if holding one with an ember
        if self.crafting.active_tinder_nest and self.crafting.active_tinder_nest.has_ember:
            res = self.crafting.blow_tinder(breath_velocity=2.5)
            if res.get("is_flaming"):
                self.notify("FLAME! The tinder nest caught fire! Transferring to kindling...", 5.0)
                # Transfer flame to fire pit
                flame_body = CombustionBody(
                    species=WoodSpeciesType.RED_CEDAR,
                    dry_mass=0.05,
                    initial_m_surface=0.05,
                    initial_m_core=0.05,
                    initial_temp=580.0,
                    geometry_type="tinder",
                    position=self.fire_pit_pos + np.array([0.0, 0.08, 0.0]),
                    dimensions=np.array([0.15, 0.04])
                )
                flame_body.stage = CombustionStage.FLAMING
                self.thermal_grid.add_body(flame_body)
            elif res.get("status") == "blown_out":
                self.notify("Breath was too strong! Ember blew out.", 3.0)
            else:
                self.notify(f"Blowing gently... Core Temp: {res.get('core_temp', 0):.0f}°C", 2.0)
            return res

        # 2. Or blow directly into hearth coal bed
        power_boost, blown_away = self.thermal_grid.blow_into_fire(breath_velocity=2.5)
        if blown_away:
            self.notify("Overblown! Coals cooled and ash scattered.", 2.5)
        else:
            self.notify(f"Blew breath into coals! Core Temp: {self.thermal_grid.core_coal_temp:.0f}°C", 2.0)
        return {"power_boost": power_boost, "blown_away": blown_away}
