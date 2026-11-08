"""
Firestarter - Procedural Low-Poly Mesh Generators
Generates stylized geometry for cylinders (logs, kindling, trunks), cones (canopies, teepees),
boxes (drying racks, phone, stone bearing blocks), terrain height grids, hearth stone rings,
and first-person player hands.
"""

import math
import numpy as np
from typing import Tuple, List, Callable, Optional

class MeshData:
    def __init__(self, vertices: np.ndarray, indices: np.ndarray):
        self.vertices = vertices.astype(np.float32)
        self.indices = indices.astype(np.uint32)
        self.vertex_count = len(vertices) // 12
        self.index_count = len(indices)

def create_box_mesh(
    dimensions: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    color: Tuple[float, float, float, float] = (0.55, 0.42, 0.30, 1.0)
) -> MeshData:
    dx, dy, dz = dimensions[0] * 0.5, dimensions[1] * 0.5, dimensions[2] * 0.5
    faces = [
        ((0.0, 0.0, 1.0), [(-dx, -dy, dz), (dx, -dy, dz), (dx, dy, dz), (-dx, dy, dz)]),
        ((0.0, 0.0, -1.0), [(dx, -dy, -dz), (-dx, -dy, -dz), (-dx, dy, -dz), (dx, dy, -dz)]),
        ((-1.0, 0.0, 0.0), [(-dx, -dy, -dz), (-dx, -dy, dz), (-dx, dy, dz), (-dx, dy, -dz)]),
        ((1.0, 0.0, 0.0), [(dx, -dy, dz), (dx, -dy, -dz), (dx, dy, -dz), (dx, dy, dz)]),
        ((0.0, 1.0, 0.0), [(-dx, dy, dz), (dx, dy, dz), (dx, dy, -dz), (-dx, dy, -dz)]),
        ((0.0, -1.0, 0.0), [(-dx, -dy, -dz), (dx, -dy, -dz), (dx, -dy, dz), (-dx, -dy, dz)]),
    ]
    verts: List[float] = []
    inds: List[int] = []
    v_idx = 0
    uvs = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]

    for n, corners in faces:
        for i, c in enumerate(corners):
            u, v = uvs[i]
            verts.extend([c[0], c[1], c[2], n[0], n[1], n[2], u, v, color[0], color[1], color[2], color[3]])
        inds.extend([v_idx, v_idx + 1, v_idx + 2, v_idx, v_idx + 2, v_idx + 3])
        v_idx += 4

    return MeshData(np.array(verts, dtype=np.float32), np.array(inds, dtype=np.uint32))

def create_cylinder_mesh(
    radius: float = 0.05,
    length: float = 0.5,
    segments: int = 12,
    color: Tuple[float, float, float, float] = (0.55, 0.40, 0.25, 1.0)
) -> MeshData:
    verts: List[float] = []
    inds: List[int] = []
    half_l = length * 0.5

    for i in range(segments + 1):
        theta = (2.0 * np.pi * i) / segments
        cos_t = float(np.cos(theta))
        sin_t = float(np.sin(theta))
        u = i / segments
        verts.extend([radius * cos_t, -half_l, radius * sin_t, cos_t, 0.0, sin_t, u, 0.0, color[0], color[1], color[2], color[3]])
        verts.extend([radius * cos_t, half_l, radius * sin_t, cos_t, 0.0, sin_t, u, 1.0, color[0], color[1], color[2], color[3]])

    for i in range(segments):
        idx = i * 2
        inds.extend([idx, idx + 1, idx + 2, idx + 1, idx + 3, idx + 2])

    base_idx = (segments + 1) * 2
    verts.extend([0.0, -half_l, 0.0, 0.0, -1.0, 0.0, 0.5, 0.5, color[0] * 0.85, color[1] * 0.85, color[2] * 0.85, color[3]])
    verts.extend([0.0, half_l, 0.0, 0.0, 1.0, 0.0, 0.5, 0.5, color[0] * 1.15, color[1] * 1.15, color[2] * 1.15, color[3]])

    for i in range(segments):
        idx = i * 2
        inds.extend([base_idx, (idx + 2) % base_idx, idx])
        inds.extend([base_idx + 1, idx + 1, (idx + 3) % base_idx])

    return MeshData(np.array(verts, dtype=np.float32), np.array(inds, dtype=np.uint32))

def create_cone_mesh(
    radius: float = 0.5,
    height: float = 1.0,
    segments: int = 10,
    color: Tuple[float, float, float, float] = (0.18, 0.38, 0.18, 1.0)
) -> MeshData:
    verts: List[float] = []
    inds: List[int] = []

    verts.extend([0.0, height, 0.0, 0.0, 1.0, 0.0, 0.5, 1.0, color[0], color[1], color[2], color[3]])

    for i in range(segments + 1):
        theta = (2.0 * np.pi * i) / segments
        cos_t = float(np.cos(theta))
        sin_t = float(np.sin(theta))
        u = i / segments
        n = np.array([cos_t, radius / max(0.01, height), sin_t])
        n = n / np.linalg.norm(n)
        verts.extend([radius * cos_t, 0.0, radius * sin_t, n[0], n[1], n[2], u, 0.0, color[0], color[1], color[2], color[3]])

    for i in range(segments):
        inds.extend([0, i + 1, i + 2])

    base_center_idx = len(verts) // 12
    verts.extend([0.0, 0.0, 0.0, 0.0, -1.0, 0.0, 0.5, 0.5, color[0] * 0.8, color[1] * 0.8, color[2] * 0.8, color[3]])
    for i in range(segments):
        inds.extend([base_center_idx, i + 2, i + 1])

    return MeshData(np.array(verts, dtype=np.float32), np.array(inds, dtype=np.uint32))

def create_terrain_mesh(
    size: float = 130.0,
    resolution: int = 40,
    elevation_fn: Optional[Callable[[float, float], float]] = None
) -> MeshData:
    if elevation_fn is None:
        elevation_fn = lambda x, z: 0.0

    half = size * 0.5
    xs = np.linspace(-half, half, resolution)
    zs = np.linspace(-half, half, resolution)
    dx = xs[1] - xs[0]
    dz = zs[1] - zs[0]

    verts: List[float] = []
    for i, x in enumerate(xs):
        for j, z in enumerate(zs):
            y = elevation_fn(x, z)
            h_l = elevation_fn(x - dx, z)
            h_r = elevation_fn(x + dx, z)
            h_d = elevation_fn(x, z - dz)
            h_u = elevation_fn(x, z + dz)

            norm = np.array([h_l - h_r, 2.0 * dx, h_d - h_u], dtype=float)
            norm_len = np.linalg.norm(norm)
            norm = (norm / norm_len) if norm_len > 1e-4 else np.array([0.0, 1.0, 0.0])

            u = i / (resolution - 1)
            v = j / (resolution - 1)

            if y < 8.5:
                color = (0.20, 0.28, 0.16, 1.0)
            elif y > 15.5:
                color = (0.42, 0.38, 0.32, 1.0)
            else:
                color = (0.28, 0.22, 0.15, 1.0)

            verts.extend([x, y, z, norm[0], norm[1], norm[2], u, v, color[0], color[1], color[2], color[3]])

    inds: List[int] = []
    for i in range(resolution - 1):
        for j in range(resolution - 1):
            top_l = i * resolution + j
            top_r = (i + 1) * resolution + j
            bot_l = i * resolution + (j + 1)
            bot_r = (i + 1) * resolution + (j + 1)
            inds.extend([top_l, bot_l, top_r, top_r, bot_l, bot_r])

    return MeshData(np.array(verts, dtype=np.float32), np.array(inds, dtype=np.uint32))

def create_hearth_ring_mesh(
    inner_r: float = 0.45,
    outer_r: float = 0.65,
    stone_count: int = 14
) -> MeshData:
    verts: List[float] = []
    inds: List[int] = []
    np.random.seed(42)

    for i in range(stone_count):
        angle = (2.0 * np.pi * i) / stone_count
        r_mid = 0.5 * (inner_r + outer_r) + np.random.uniform(-0.02, 0.02)
        cx = float(r_mid * np.cos(angle))
        cz = float(r_mid * np.sin(angle))
        cy = 0.06 + float(np.random.uniform(-0.01, 0.02))

        sx = 0.12 + float(np.random.uniform(-0.02, 0.02))
        sy = 0.08 + float(np.random.uniform(-0.01, 0.02))
        sz = 0.12 + float(np.random.uniform(-0.02, 0.02))

        g_val = float(np.random.uniform(0.36, 0.48))
        color = (g_val * 1.05, g_val, g_val * 0.95, 1.0)

        box = create_box_mesh(dimensions=(sx, sy, sz), color=color)
        base_v = len(verts) // 12
        rot_a = angle + np.pi * 0.5

        for v_i in range(box.vertex_count):
            bx = box.vertices[v_i * 12 + 0]
            by = box.vertices[v_i * 12 + 1]
            bz = box.vertices[v_i * 12 + 2]

            rx = bx * np.cos(rot_a) - bz * np.sin(rot_a)
            rz = bx * np.sin(rot_a) + bz * np.cos(rot_a)

            nx = box.vertices[v_i * 12 + 3]
            ny = box.vertices[v_i * 12 + 4]
            nz = box.vertices[v_i * 12 + 5]
            rnx = nx * np.cos(rot_a) - nz * np.sin(rot_a)
            rnz = nx * np.sin(rot_a) + nz * np.cos(rot_a)

            verts.extend([
                cx + rx, cy + by, cz + rz,
                rnx, ny, rnz,
                box.vertices[v_i * 12 + 6], box.vertices[v_i * 12 + 7],
                box.vertices[v_i * 12 + 8], box.vertices[v_i * 12 + 9],
                box.vertices[v_i * 12 + 10], box.vertices[v_i * 12 + 11]
            ])

        for idx in box.indices:
            inds.append(base_v + idx)

    return MeshData(np.array(verts, dtype=np.float32), np.array(inds, dtype=np.uint32))

def create_hand_mesh(is_right_hand: bool = True) -> MeshData:
    verts: List[float] = []
    inds: List[int] = []
    skin_color = (0.76, 0.58, 0.46, 1.0)
    sign = 1.0 if is_right_hand else -1.0

    forearm = create_cylinder_mesh(radius=0.038, length=0.22, segments=8, color=(0.72, 0.54, 0.42, 1.0))
    base_v = len(verts) // 12
    for v_i in range(forearm.vertex_count):
        x = forearm.vertices[v_i * 12 + 0]
        y = forearm.vertices[v_i * 12 + 1] - 0.12
        z = forearm.vertices[v_i * 12 + 2] - 0.10
        verts.extend([x, y, z, forearm.vertices[v_i * 12 + 3], forearm.vertices[v_i * 12 + 4], forearm.vertices[v_i * 12 + 5],
                      forearm.vertices[v_i * 12 + 6], forearm.vertices[v_i * 12 + 7],
                      forearm.vertices[v_i * 12 + 8], forearm.vertices[v_i * 12 + 9], forearm.vertices[v_i * 12 + 10], forearm.vertices[v_i * 12 + 11]])
    for idx in forearm.indices:
        inds.append(base_v + idx)

    palm = create_box_mesh(dimensions=(0.068, 0.024, 0.075), color=skin_color)
    base_v = len(verts) // 12
    for v_i in range(palm.vertex_count):
        verts.extend([palm.vertices[v_i * 12 + 0], palm.vertices[v_i * 12 + 1], palm.vertices[v_i * 12 + 2],
                      palm.vertices[v_i * 12 + 3], palm.vertices[v_i * 12 + 4], palm.vertices[v_i * 12 + 5],
                      palm.vertices[v_i * 12 + 6], palm.vertices[v_i * 12 + 7],
                      palm.vertices[v_i * 12 + 8], palm.vertices[v_i * 12 + 9], palm.vertices[v_i * 12 + 10], palm.vertices[v_i * 12 + 11]])
    for idx in palm.indices:
        inds.append(base_v + idx)

    fingers = create_box_mesh(dimensions=(0.062, 0.020, 0.065), color=(0.78, 0.60, 0.48, 1.0))
    base_v = len(verts) // 12
    for v_i in range(fingers.vertex_count):
        verts.extend([fingers.vertices[v_i * 12 + 0], fingers.vertices[v_i * 12 + 1], fingers.vertices[v_i * 12 + 2] + 0.065,
                      fingers.vertices[v_i * 12 + 3], fingers.vertices[v_i * 12 + 4], fingers.vertices[v_i * 12 + 5],
                      fingers.vertices[v_i * 12 + 6], fingers.vertices[v_i * 12 + 7],
                      fingers.vertices[v_i * 12 + 8], fingers.vertices[v_i * 12 + 9], fingers.vertices[v_i * 12 + 10], fingers.vertices[v_i * 12 + 11]])
    for idx in fingers.indices:
        inds.append(base_v + idx)

    thumb = create_box_mesh(dimensions=(0.022, 0.020, 0.040), color=(0.75, 0.57, 0.45, 1.0))
    base_v = len(verts) // 12
    for v_i in range(thumb.vertex_count):
        verts.extend([thumb.vertices[v_i * 12 + 0] - 0.045 * sign, thumb.vertices[v_i * 12 + 1] + 0.005, thumb.vertices[v_i * 12 + 2] + 0.02,
                      thumb.vertices[v_i * 12 + 3], thumb.vertices[v_i * 12 + 4], thumb.vertices[v_i * 12 + 5],
                      thumb.vertices[v_i * 12 + 6], thumb.vertices[v_i * 12 + 7],
                      thumb.vertices[v_i * 12 + 8], thumb.vertices[v_i * 12 + 9], thumb.vertices[v_i * 12 + 10], thumb.vertices[v_i * 12 + 11]])
    for idx in thumb.indices:
        inds.append(base_v + idx)

    return MeshData(np.array(verts, dtype=np.float32), np.array(inds, dtype=np.uint32))

def create_quad_mesh() -> Tuple[np.ndarray, np.ndarray]:
    verts = np.array([
        0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0,
        1280.0, 0.0, 1.0, 0.0, 1.0, 1.0, 1.0, 1.0,
        1280.0, 720.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
        0.0, 720.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0,
    ], dtype=np.float32)
    inds = np.array([0, 1, 2, 0, 2, 3], dtype=np.uint32)
    return verts, inds
