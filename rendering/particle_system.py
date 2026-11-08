"""
Firestarter - Particle System
Handles flame tongues, white steam hissing puffs, yellow-grey pyrolysis smoke,
pine resin pop sparks, and dynamic weather (rain / snow).
"""

import math
import numpy as np
from typing import List, Tuple, Optional

class Particle:
    __slots__ = ('pos', 'vel', 'color', 'size', 'lifetime', 'max_lifetime', 'gravity', 'growth_rate')
    def __init__(
        self,
        pos: np.ndarray,
        vel: np.ndarray,
        color: List[float],
        size: float,
        lifetime: float,
        gravity: float = 0.0,
        growth_rate: float = 0.0
    ):
        self.pos = np.array(pos, dtype=float)
        self.vel = np.array(vel, dtype=float)
        self.color = np.array(color, dtype=float)
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.growth_rate = growth_rate

class ParticleSystem:
    def __init__(self, max_particles: int = 1800):
        self.max_particles = max_particles
        self.particles: List[Particle] = []

    def spawn_flame(self, pos: np.ndarray, count: int = 2, height: float = 0.35, draft_vel: float = 0.5):
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            ox = np.random.uniform(-0.05, 0.05)
            oz = np.random.uniform(-0.05, 0.05)
            p_pos = pos + np.array([ox, 0.02, oz])
            vy = (0.75 + 0.55 * draft_vel) * (height / 0.35) * np.random.uniform(0.8, 1.25)
            vel = np.array([np.random.uniform(-0.04, 0.04), vy, np.random.uniform(-0.04, 0.04)])
            col = [1.0, np.random.uniform(0.40, 0.75), 0.12, 0.85]
            size = np.random.uniform(0.08, 0.16)
            self.particles.append(Particle(p_pos, vel, col, size, np.random.uniform(0.25, 0.50), gravity=0.15, growth_rate=0.12))

    def spawn_steam(self, pos: np.ndarray, rate_kg_s: float = 0.01, wind_vec: Optional[np.ndarray] = None):
        count = min(4, max(1, int(rate_kg_s * 150)))
        wind = wind_vec if wind_vec is not None else np.zeros(3)
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            ox = np.random.uniform(-0.08, 0.08)
            oz = np.random.uniform(-0.08, 0.08)
            p_pos = pos + np.array([ox, 0.04, oz])
            vel = np.array([np.random.uniform(-0.02, 0.02), np.random.uniform(0.4, 0.75), np.random.uniform(-0.02, 0.02)]) + wind * 0.15
            col = [0.94, 0.96, 0.98, 0.45]
            size = np.random.uniform(0.09, 0.18)
            self.particles.append(Particle(p_pos, vel, col, size, np.random.uniform(0.7, 1.3), gravity=-0.05, growth_rate=0.22))

    def spawn_pyrolysis_smoke(self, pos: np.ndarray, rate_g_s: float = 0.5, wind_vec: Optional[np.ndarray] = None):
        count = min(3, max(1, int(rate_g_s * 2.0)))
        wind = wind_vec if wind_vec is not None else np.zeros(3)
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            ox = np.random.uniform(-0.06, 0.06)
            oz = np.random.uniform(-0.06, 0.06)
            p_pos = pos + np.array([ox, 0.06, oz])
            vel = np.array([np.random.uniform(-0.03, 0.03), np.random.uniform(0.35, 0.65), np.random.uniform(-0.03, 0.03)]) + wind * 0.25
            col = [0.45, 0.42, 0.35, 0.60]
            size = np.random.uniform(0.12, 0.22)
            self.particles.append(Particle(p_pos, vel, col, size, np.random.uniform(1.8, 3.2), gravity=-0.02, growth_rate=0.35))

    def spawn_resin_sparks(self, pos: np.ndarray, count: int = 6):
        for _ in range(count):
            if len(self.particles) >= self.max_particles:
                break
            vel = np.array([
                np.random.uniform(-0.4, 0.4),
                np.random.uniform(0.8, 1.8),
                np.random.uniform(-0.4, 0.4)
            ])
            col = [1.0, 0.88, 0.35, 1.0]
            size = np.random.uniform(0.025, 0.045)
            self.particles.append(Particle(pos.copy(), vel, col, size, np.random.uniform(0.35, 0.65), gravity=-2.5))

    def spawn_weather(self, player_pos: np.ndarray, rain_intensity: float = 0.0, snow_accumulation: float = 0.0, wind_vec: Optional[np.ndarray] = None):
        wind = wind_vec if wind_vec is not None else np.zeros(3)
        if rain_intensity > 0.05:
            count = int(rain_intensity * 12)
            for _ in range(count):
                if len(self.particles) >= self.max_particles:
                    break
                ox = np.random.uniform(-10.0, 10.0)
                oz = np.random.uniform(-10.0, 10.0)
                p_pos = player_pos + np.array([ox, np.random.uniform(4.0, 8.0), oz])
                vel = np.array([0.0, -9.0, 0.0]) + wind * 0.2
                col = [0.75, 0.82, 0.90, 0.35]
                self.particles.append(Particle(p_pos, vel, col, 0.04, 0.7))
        elif snow_accumulation > 0.05:
            count = 4
            for _ in range(count):
                if len(self.particles) >= self.max_particles:
                    break
                ox = np.random.uniform(-10.0, 10.0)
                oz = np.random.uniform(-10.0, 10.0)
                p_pos = player_pos + np.array([ox, np.random.uniform(3.0, 6.0), oz])
                vel = np.array([np.random.uniform(-0.1, 0.1), -1.1, np.random.uniform(-0.1, 0.1)]) + wind * 0.15
                col = [0.98, 0.98, 1.0, 0.65]
                self.particles.append(Particle(p_pos, vel, col, 0.05, 3.5))

    def update(self, dt: float, wind_vec: Optional[np.ndarray] = None):
        wind = wind_vec if wind_vec is not None else np.zeros(3)
        alive: List[Particle] = []
        for p in self.particles:
            p.lifetime -= dt
            if p.lifetime <= 0.0:
                continue
            p.vel[1] += p.gravity * dt
            p.vel += wind * (0.12 * dt)
            p.pos += p.vel * dt
            p.size += p.growth_rate * dt
            life_ratio = max(0.0, p.lifetime / max(1e-4, p.max_lifetime))
            p.color[3] = p.color[3] * (life_ratio ** 0.5)
            alive.append(p)
        self.particles = alive

    def get_render_data(self, cam_right: np.ndarray, cam_up: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        n = len(self.particles)
        if n == 0:
            return np.zeros(0, dtype=np.float32), np.zeros(0, dtype=np.uint32)

        verts = np.zeros(n * 4 * 9, dtype=np.float32)
        inds = np.zeros(n * 6, dtype=np.uint32)

        for i, p in enumerate(self.particles):
            pos = p.pos
            s = p.size * 0.5
            r, g, b, a = p.color

            c0 = pos - cam_right * s - cam_up * s
            c1 = pos + cam_right * s - cam_up * s
            c2 = pos + cam_right * s + cam_up * s
            c3 = pos - cam_right * s + cam_up * s

            base = i * 36
            verts[base:base+9]    = [c0[0], c0[1], c0[2], 0.0, 0.0, r, g, b, a]
            verts[base+9:base+18]  = [c1[0], c1[1], c1[2], 1.0, 0.0, r, g, b, a]
            verts[base+18:base+27] = [c2[0], c2[1], c2[2], 1.0, 1.0, r, g, b, a]
            verts[base+27:base+36] = [c3[0], c3[1], c3[2], 0.0, 1.0, r, g, b, a]

            ib = i * 6
            vb = i * 4
            inds[ib:ib+6] = [vb, vb+1, vb+2, vb, vb+2, vb+3]

        return verts, inds
