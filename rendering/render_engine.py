"""
Firestarter - 3D RenderEngine Subsystem
Implements Section 8 ModernGL Rendering Pipeline:
Custom GLSL shaders, camera projection/view transforms, terrain, hearth stones,
procedural trees, drying racks, combustion bodies with stage-based emissive glows,
dual-hand first-person IK rigs, particle effects, and 2D UI overlay.
"""

import math
import numpy as np
from typing import Optional, Dict, Any, List

from firestarter.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, FOV_DEGREES, CAMERA_NEAR, CAMERA_FAR
)
from firestarter.thermodynamics.combustion_body import CombustionStage
from firestarter.rendering.shaders import (
    SCENE_VERTEX_SHADER, SCENE_FRAGMENT_SHADER,
    PARTICLE_VERTEX_SHADER, PARTICLE_FRAGMENT_SHADER,
    UI_VERTEX_SHADER, UI_FRAGMENT_SHADER
)
from firestarter.rendering.mesh_generator import (
    MeshData, create_cylinder_mesh, create_cone_mesh,
    create_box_mesh, create_terrain_mesh, create_hearth_ring_mesh,
    create_hand_mesh, create_quad_mesh
)
from firestarter.rendering.particle_system import ParticleSystem
from firestarter.rendering.ui_renderer import UIRenderer

def matrix_perspective(fov_deg: float, aspect: float, near: float, far: float) -> np.ndarray:
    f = 1.0 / math.tan(math.radians(fov_deg) * 0.5)
    m = np.zeros((4, 4), dtype=np.float32)
    m[0, 0] = f / aspect
    m[1, 1] = f
    m[2, 2] = (far + near) / (near - far)
    m[2, 3] = (2.0 * far * near) / (near - far)
    m[3, 2] = -1.0
    return m

def matrix_look_at(eye: np.ndarray, target: np.ndarray, up: np.ndarray = np.array([0.0, 1.0, 0.0])) -> np.ndarray:
    f = target - eye
    norm_f = np.linalg.norm(f)
    f = f / (norm_f if norm_f > 1e-6 else 1.0)
    s = np.cross(f, up)
    norm_s = np.linalg.norm(s)
    s = s / (norm_s if norm_s > 1e-6 else 1.0)
    u = np.cross(s, f)
    m = np.identity(4, dtype=np.float32)
    m[0, :3] = s
    m[1, :3] = u
    m[2, :3] = -f
    m[0, 3] = -float(np.dot(s, eye))
    m[1, 3] = -float(np.dot(u, eye))
    m[2, 3] = float(np.dot(f, eye))
    return m

def matrix_translate(x: float, y: float, z: float) -> np.ndarray:
    m = np.identity(4, dtype=np.float32)
    m[0, 3] = x
    m[1, 3] = y
    m[2, 3] = z
    return m

def matrix_scale(sx: float, sy: float, sz: float) -> np.ndarray:
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = sx
    m[1, 1] = sy
    m[2, 2] = sz
    return m

def matrix_rotate_y(deg: float) -> np.ndarray:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 2] = s
    m[2, 0] = -s
    m[2, 2] = c
    return m

def matrix_rotate_x(deg: float) -> np.ndarray:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    m = np.identity(4, dtype=np.float32)
    m[1, 1] = c
    m[1, 2] = -s
    m[2, 1] = s
    m[2, 2] = c
    return m

def matrix_rotate_z(deg: float) -> np.ndarray:
    r = math.radians(deg)
    c, s = math.cos(r), math.sin(r)
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = c
    m[0, 1] = -s
    m[1, 0] = s
    m[1, 1] = c
    return m

def matrix_ortho(left: float, right: float, bottom: float, top: float, near: float = -1.0, far: float = 1.0) -> np.ndarray:
    m = np.identity(4, dtype=np.float32)
    m[0, 0] = 2.0 / (right - left)
    m[1, 1] = 2.0 / (top - bottom)
    m[2, 2] = -2.0 / (far - near)
    m[0, 3] = -(right + left) / (right - left)
    m[1, 3] = -(top + bottom) / (top - bottom)
    m[2, 3] = -(far + near) / (far - near)
    return m

class RenderEngine:
    def __init__(self, width: int = WINDOW_WIDTH, height: int = WINDOW_HEIGHT):
        self.width = width
        self.height = height
        self.ctx = None
        self.is_gl_available = False

        self.particle_system = ParticleSystem()
        self.ui_renderer = UIRenderer(width, height)

        self._init_moderngl()

    def _init_moderngl(self):
        try:
            import moderngl
            self.ctx = moderngl.create_context()
            self.ctx.enable(moderngl.DEPTH_TEST | moderngl.CULL_FACE)
            self.is_gl_available = True

            self.scene_prog = self.ctx.program(vertex_shader=SCENE_VERTEX_SHADER, fragment_shader=SCENE_FRAGMENT_SHADER)
            self.particle_prog = self.ctx.program(vertex_shader=PARTICLE_VERTEX_SHADER, fragment_shader=PARTICLE_FRAGMENT_SHADER)
            self.ui_prog = self.ctx.program(vertex_shader=UI_VERTEX_SHADER, fragment_shader=UI_FRAGMENT_SHADER)

            self._build_buffers()
            self._init_ui_texture()
        except Exception:
            self.is_gl_available = False

    def _build_buffers(self):
        from firestarter.economy.topomap import TopographicalMap
        tm = TopographicalMap()
        self.terrain_mesh = create_terrain_mesh(size=130.0, resolution=42, elevation_fn=tm.get_elevation_at)
        self.terrain_vao = self._create_vao(self.scene_prog, self.terrain_mesh)

        self.hearth_mesh = create_hearth_ring_mesh()
        self.hearth_vao = self._create_vao(self.scene_prog, self.hearth_mesh)

        self.cylinder_mesh = create_cylinder_mesh(radius=1.0, length=1.0, segments=12)
        self.cylinder_vao = self._create_vao(self.scene_prog, self.cylinder_mesh)

        self.cone_mesh = create_cone_mesh(radius=1.0, height=1.0, segments=10)
        self.cone_vao = self._create_vao(self.scene_prog, self.cone_mesh)

        self.box_mesh = create_box_mesh(dimensions=(1.0, 1.0, 1.0))
        self.box_vao = self._create_vao(self.scene_prog, self.box_mesh)

        self.hand_left_mesh = create_hand_mesh(is_right_hand=False)
        self.hand_left_vao = self._create_vao(self.scene_prog, self.hand_left_mesh)
        self.hand_right_mesh = create_hand_mesh(is_right_hand=True)
        self.hand_right_vao = self._create_vao(self.scene_prog, self.hand_right_mesh)

        self.particle_vbo = self.ctx.buffer(reserve=1800 * 4 * 9 * 4)
        self.particle_ibo = self.ctx.buffer(reserve=1800 * 6 * 4)
        self.particle_vao = self.ctx.vertex_array(
            self.particle_prog,
            [(self.particle_vbo, '3f 2f 4f', 'in_position', 'in_uv', 'in_color')],
            self.particle_ibo
        )

        uverts, uinds = create_quad_mesh()
        self.ui_vbo = self.ctx.buffer(uverts.tobytes())
        self.ui_ibo = self.ctx.buffer(uinds.tobytes())
        self.ui_vao = self.ctx.vertex_array(
            self.ui_prog,
            [(self.ui_vbo, '2f 2f 4f', 'in_position', 'in_uv', 'in_color')],
            self.ui_ibo
        )

    def _create_vao(self, program: Any, mesh: MeshData) -> Any:
        vbo = self.ctx.buffer(mesh.vertices.tobytes())
        ibo = self.ctx.buffer(mesh.indices.tobytes())
        return self.ctx.vertex_array(
            program,
            [(vbo, '3f 3f 2f 4f', 'in_position', 'in_normal', 'in_uv', 'in_color')],
            ibo
        )

    def _init_ui_texture(self):
        self.ui_texture = self.ctx.texture((self.width, self.height), 4)
        self.ui_texture.filter = (self.ctx.NEAREST, self.ctx.NEAREST)

    def _set_uniform(self, program: Any, name: str, val: Any):
        if name in program:
            if isinstance(val, (bytes, bytearray)):
                program[name].write(val)
            else:
                program[name].value = val

    def handle_resize(self, width: int, height: int):
        self.width = max(100, width)
        self.height = max(100, height)
        if self.is_gl_available and self.ctx:
            self.ctx.viewport = (0, 0, self.width, self.height)
            self.ui_texture = self.ctx.texture((self.width, self.height), 4)
            self.ui_texture.filter = (self.ctx.NEAREST, self.ctx.NEAREST)

    def render(
        self,
        world: Any,
        player: Any,
        hands: Any,
        smartphone: Any,
        ref_book: Any,
        input_mgr: Any
    ):
        if not self.is_gl_available or not self.ctx:
            return

        aspect = self.width / float(self.height)
        m_proj = matrix_perspective(FOV_DEGREES, aspect, CAMERA_NEAR, CAMERA_FAR)

        yaw_rad = math.radians(player.yaw)
        pitch_rad = math.radians(player.pitch)
        forward = np.array([
            math.cos(pitch_rad) * math.cos(yaw_rad),
            math.sin(pitch_rad),
            math.cos(pitch_rad) * math.sin(yaw_rad)
        ], dtype=float)
        cam_pos = player.position
        cam_target = cam_pos + forward
        m_view = matrix_look_at(cam_pos, cam_target)

        hour = world.weather.time_of_day_hours
        if 6.0 <= hour <= 18.0:
            sky = (0.42, 0.62, 0.82, 1.0)
        elif 18.0 < hour <= 20.5:
            sky = (0.75, 0.38, 0.22, 1.0)
        elif 4.5 <= hour < 6.0:
            sky = (0.55, 0.40, 0.50, 1.0)
        else:
            sky = (0.04, 0.06, 0.12, 1.0)

        self.ctx.clear(sky[0], sky[1], sky[2], sky[3])
        self.ctx.enable(self.ctx.DEPTH_TEST | self.ctx.CULL_FACE)
        self.ctx.disable(self.ctx.BLEND)

        sun_dir = world.weather.get_sun_direction()
        sun_color = (0.95, 0.90, 0.80) if (6.0 <= hour <= 18.0) else (0.85, 0.45, 0.25)
        amb_color = (0.22, 0.24, 0.26) if (6.0 <= hour <= 18.0) else (0.08, 0.09, 0.12)

        core_t = world.thermal_grid.core_coal_temp
        fire_active = (core_t > 150.0)
        flicker = (1.0 + 0.15 * math.sin(world.physics_accumulator * 18.0)) if fire_active else 0.0
        fire_int = min(4.5, (core_t / 400.0) * flicker) if fire_active else 0.0

        p = self.scene_prog
        self._set_uniform(p, 'm_proj', m_proj.T.astype('f4').tobytes())
        self._set_uniform(p, 'm_view', m_view.T.astype('f4').tobytes())
        self._set_uniform(p, 'u_light_dir', tuple(sun_dir))
        self._set_uniform(p, 'u_light_color', sun_color)
        self._set_uniform(p, 'u_ambient_color', amb_color)
        self._set_uniform(p, 'u_camera_pos', tuple(cam_pos))

        self._set_uniform(p, 'u_fire_pos', tuple(world.fire_pit_pos + np.array([0.0, 0.12, 0.0])))
        self._set_uniform(p, 'u_fire_color', (1.0, 0.48, 0.12))
        self._set_uniform(p, 'u_fire_intensity', fire_int)
        self._set_uniform(p, 'u_fire_radius', 6.5)

        # 1. Terrain
        m_terrain = np.identity(4, dtype=np.float32)
        self._set_uniform(p, 'm_model', m_terrain.T.astype('f4').tobytes())
        self._set_uniform(p, 'u_base_color', (1.0, 1.0, 1.0, 1.0))
        self._set_uniform(p, 'u_glow_intensity', 0.0)
        self._set_uniform(p, 'u_roughness', 0.85)
        self.terrain_vao.render()

        # 2. Hearth Stone Ring
        m_hearth = matrix_translate(world.fire_pit_pos[0], world.fire_pit_pos[1], world.fire_pit_pos[2])
        self._set_uniform(p, 'm_model', m_hearth.T.astype('f4').tobytes())
        self._set_uniform(p, 'u_base_color', (1.0, 1.0, 1.0, 1.0))
        self._set_uniform(p, 'u_glow_intensity', 0.0)
        self._set_uniform(p, 'u_roughness', 0.90)
        self.hearth_vao.render()

        # 3. Trees
        for tree in world.ecosystem.trees:
            t_pos = tree.position
            m_t = matrix_translate(t_pos[0], t_pos[1] + tree.height_m * 0.5, t_pos[2]) @                   matrix_rotate_z(tree.fall_angle) @                   matrix_scale(tree.trunk_radius_m, tree.height_m, tree.trunk_radius_m)
            self._set_uniform(p, 'm_model', m_t.T.astype('f4').tobytes())
            trunk_color = (0.50, 0.38, 0.24, 1.0) if "Birch" not in tree.species.value else (0.85, 0.85, 0.80, 1.0)
            self._set_uniform(p, 'u_base_color', trunk_color)
            self._set_uniform(p, 'u_glow_intensity', 0.0)
            self.cylinder_vao.render()

            if not tree.is_fallen and tree.fall_angle < 10.0:
                for tier in range(3):
                    cone_y = t_pos[1] + tree.height_m * 0.5 + tier * (tree.height_m * 0.18)
                    cone_r = (tree.trunk_radius_m * 7.5) * (1.0 - tier * 0.22)
                    m_cone = matrix_translate(t_pos[0], cone_y, t_pos[2]) @ matrix_scale(cone_r, tree.height_m * 0.35, cone_r)
                    self._set_uniform(p, 'm_model', m_cone.T.astype('f4').tobytes())
                    foliage_col = (0.12 + tier*0.02, 0.30 + tier*0.04, 0.14, 1.0)
                    self._set_uniform(p, 'u_base_color', foliage_col)
                    self.cone_vao.render()

        # 4. Raised Drying Rack
        rack_pos = world.drying_rack.position
        post_offsets = [(-0.6, -0.3), (0.6, -0.3), (-0.6, 0.3), (0.6, 0.3)]
        for ox, oz in post_offsets:
            m_post = matrix_translate(rack_pos[0] + ox, rack_pos[1] + 0.3, rack_pos[2] + oz) @ matrix_scale(0.04, 0.6, 0.04)
            self._set_uniform(p, 'm_model', m_post.T.astype('f4').tobytes())
            self._set_uniform(p, 'u_base_color', (0.42, 0.32, 0.22, 1.0))
            self.cylinder_vao.render()

        m_bar1 = matrix_translate(rack_pos[0], rack_pos[1] + 0.55, rack_pos[2] - 0.28) @ matrix_rotate_z(90) @ matrix_scale(0.035, 1.25, 0.035)
        m_bar2 = matrix_translate(rack_pos[0], rack_pos[1] + 0.55, rack_pos[2] + 0.28) @ matrix_rotate_z(90) @ matrix_scale(0.035, 1.25, 0.035)
        self._set_uniform(p, 'm_model', m_bar1.T.astype('f4').tobytes())
        self.cylinder_vao.render()
        self._set_uniform(p, 'm_model', m_bar2.T.astype('f4').tobytes())
        self.cylinder_vao.render()

        if world.drying_rack.has_tarp:
            m_tarp = matrix_translate(rack_pos[0], rack_pos[1] + 0.72, rack_pos[2]) @ matrix_scale(1.4, 0.03, 0.85)
            self._set_uniform(p, 'm_model', m_tarp.T.astype('f4').tobytes())
            self._set_uniform(p, 'u_base_color', (0.15, 0.35, 0.65, 0.95))
            self.box_vao.render()

        # 5. Combustion Bodies
        for b in world.thermal_grid.bodies:
            bp = b.position
            l = float(b.dimensions[0])
            r = b.radius
            rot_y = float(b.orientation[1]) if len(b.orientation) > 1 else 0.0

            m_b = matrix_translate(bp[0], bp[1], bp[2]) @ matrix_rotate_y(rot_y) @ matrix_scale(r, l, r)
            self._set_uniform(p, 'm_model', m_b.T.astype('f4').tobytes())

            if b.stage == CombustionStage.AMBIENT:
                col = (0.58, 0.42, 0.28, 1.0)
                glow = 0.0
            elif b.stage == CombustionStage.DEHYDRATION:
                col = (0.48, 0.38, 0.30, 1.0)
                glow = 0.05
            elif b.stage == CombustionStage.PYROLYSIS:
                col = (0.22, 0.18, 0.15, 1.0)
                glow = 0.15
            elif b.stage == CombustionStage.FLAMING:
                col = (0.15, 0.10, 0.08, 1.0)
                glow = 0.95
            elif b.stage == CombustionStage.CHAR_OXIDATION:
                col = (0.85, 0.25, 0.08, 1.0)
                glow = 1.35 * min(1.2, b.t_surface / 700.0)
            else:
                col = (0.75, 0.75, 0.75, 1.0)
                glow = 0.0

            self._set_uniform(p, 'u_base_color', col)
            self._set_uniform(p, 'u_glow_intensity', glow)
            self.cylinder_vao.render()

            if b.flame_height > 0.05:
                self.particle_system.spawn_flame(bp, count=2, height=b.flame_height, draft_vel=world.thermal_grid.draft_velocity)
            if b.steam_rate > 0.0001:
                self.particle_system.spawn_steam(bp, rate_kg_s=b.steam_rate, wind_vec=world.weather.wind_vector)
            if b.smoke_rate > 0.01:
                self.particle_system.spawn_pyrolysis_smoke(bp, rate_g_s=b.smoke_rate, wind_vec=world.weather.wind_vector)
            if b.resin_pop_event:
                self.particle_system.spawn_resin_sparks(bp, count=8)

        self.particle_system.spawn_weather(
            cam_pos,
            rain_intensity=world.weather.rain_intensity,
            snow_accumulation=world.weather.snow_accumulation_m,
            wind_vec=world.weather.wind_vector
        )

        # 6. Hands
        hm = hands.get_hand_render_matrices()
        cam_right = np.array([m_view[0, 0], m_view[1, 0], m_view[2, 0]])
        cam_up = np.array([m_view[0, 1], m_view[1, 1], m_view[2, 1]])

        l_offset = cam_right * hm["left_pos"][0] + cam_up * hm["left_pos"][1] + forward * hm["left_pos"][2]
        l_world = cam_pos + l_offset
        m_hand_l = matrix_translate(l_world[0], l_world[1], l_world[2]) @                    matrix_rotate_y(-player.yaw - 90.0 + hm["left_rot"][1]) @                    matrix_rotate_x(player.pitch + hm["left_rot"][0])
        self._set_uniform(p, 'm_model', m_hand_l.T.astype('f4').tobytes())
        self._set_uniform(p, 'u_base_color', (1.0, 1.0, 1.0, 1.0))
        self._set_uniform(p, 'u_glow_intensity', 0.0)
        self.hand_left_vao.render()

        r_offset = cam_right * hm["right_pos"][0] + cam_up * hm["right_pos"][1] + forward * hm["right_pos"][2]
        r_world = cam_pos + r_offset
        m_hand_r = matrix_translate(r_world[0], r_world[1], r_world[2]) @                    matrix_rotate_y(-player.yaw - 90.0 + hm["right_rot"][1]) @                    matrix_rotate_x(player.pitch + hm["right_rot"][0])
        self._set_uniform(p, 'm_model', m_hand_r.T.astype('f4').tobytes())
        self.hand_right_vao.render()

        # 7. Particles
        self.particle_system.update(0.016, world.weather.wind_vector)
        pverts, pinds = self.particle_system.get_render_data(cam_right, cam_up)
        if len(pinds) > 0:
            import moderngl
            self.ctx.enable(self.ctx.BLEND)
            self.ctx.blend_func = (self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA)
            self.particle_prog['m_proj'].write(m_proj.T.astype('f4').tobytes())
            self.particle_prog['m_view'].write(m_view.T.astype('f4').tobytes())
            self.particle_vbo.write(pverts.tobytes())
            self.particle_ibo.write(pinds.tobytes())
            self.particle_vao.render(moderngl.TRIANGLES, vertices=len(pinds))

        # 8. UI Overlay
        ui_bytes, ui_w, ui_h = self.ui_renderer.render(world, player, hands, smartphone, ref_book, input_mgr)
        self.ui_texture.write(ui_bytes)
        self.ui_texture.use(location=0)

        self.ctx.disable(self.ctx.DEPTH_TEST)
        self.ctx.enable(self.ctx.BLEND)
        self.ctx.blend_func = (self.ctx.SRC_ALPHA, self.ctx.ONE_MINUS_SRC_ALPHA)

        m_ortho = matrix_ortho(0.0, float(self.width), float(self.height), 0.0, -1.0, 1.0)
        self.ui_prog['m_ortho'].write(m_ortho.T.astype('f4').tobytes())
        self.ui_prog['u_texture'].value = 0
        self.ui_prog['u_use_texture'].value = 1
        self.ui_vao.render()
