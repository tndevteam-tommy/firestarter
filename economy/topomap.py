"""
Firestarter - Smartphone Topographical Map App
Implements Section 5.1 App 2:
GPS topomap with 5m contour lines, microclimate humidity zones,
and waypoint markers (drying racks, fire pits, fungal stands).
"""

import math
import numpy as np
from typing import List, Dict, Tuple, Any

class MapWaypoint:
    def __init__(self, name: str, category: str, position: np.ndarray, symbol: str):
        self.name = name
        self.category = category # 'fire_pit', 'drying_rack', 'fungi_stand', 'player'
        self.position = position
        self.symbol = symbol

class TopographicalMap:
    def __init__(self, map_size_m: float = 200.0, contour_interval_m: float = 5.0):
        self.map_size_m = map_size_m
        self.contour_interval_m = contour_interval_m
        self.waypoints: List[MapWaypoint] = []
        
        # Microclimate zones
        # Creek bed at z ~ -30, high humidity ~ 85%
        # Ridge top at z ~ 45, low humidity ~ 25% (dry, sun-baked)
        self.microclimates = [
            {"name": "Marshy Creek Bed", "center": np.array([0.0, 0.0, -40.0]), "radius": 35.0, "humidity": 0.88, "desc": "Saturated soil, damp mossy timber"},
            {"name": "Sun-Baked Ridge", "center": np.array([20.0, 18.0, 50.0]), "radius": 40.0, "humidity": 0.22, "desc": "Arid, rapid drying, brittle tinder"},
            {"name": "Hardwood Basin", "center": np.array([-40.0, 5.0, 10.0]), "radius": 30.0, "humidity": 0.55, "desc": "Temperate mixed canopy"}
        ]

    def add_waypoint(self, name: str, category: str, position: np.ndarray, symbol: str = "o"):
        wp = MapWaypoint(name, category, position.copy(), symbol)
        self.waypoints.append(wp)

    def get_elevation_at(self, x: float, z: float) -> float:
        """Procedural terrain elevation function."""
        # Rolling hills and valley
        h1 = 12.0 * math.sin(x * 0.03) * math.cos(z * 0.03)
        h2 = 8.0 * math.sin(z * 0.05 + 1.2)
        valley = -6.0 * math.exp(-((z + 40.0) / 25.0) ** 2)
        ridge = 15.0 * math.exp(-((z - 50.0) / 30.0) ** 2)
        return max(0.0, 10.0 + h1 + h2 + valley + ridge)

    def get_microclimate_at(self, x: float, z: float) -> Tuple[str, float]:
        """Returns (zone_name, relative_humidity)."""
        p = np.array([x, 0.0, z])
        for z_info in self.microclimates:
            dist = np.linalg.norm(p - z_info["center"])
            if dist < z_info["radius"]:
                return z_info["name"], z_info["humidity"]
        return "Forest Floor", 0.50

    def generate_contour_slices(self, resolution: int = 24) -> List[Dict[str, Any]]:
        """Generates elevation grid for contour lines rendering."""
        half = self.map_size_m / 2.0
        xs = np.linspace(-half, half, resolution)
        zs = np.linspace(-half, half, resolution)
        elevations = np.zeros((resolution, resolution))
        
        for i, x in enumerate(xs):
            for j, z in enumerate(zs):
                elevations[i, j] = self.get_elevation_at(x, z)
                
        return {
            "xs": xs,
            "zs": zs,
            "elevations": elevations,
            "min_elev": float(np.min(elevations)),
            "max_elev": float(np.max(elevations)),
            "contour_interval": self.contour_interval_m
        }
