"""
Firestarter - UI Renderer
Implements Section 5, 6, and 8:
Renders the Wilderness Smartphone OS (Store & Topo Map), Field Reference Compendium,
Time Fast-Forward Menu, HUD Crosshair, Stamina Bar, and Hearth Diagnostics.
"""

import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from typing import Tuple, Dict, Any

class UIRenderer:
    def __init__(self, width: int = 1280, height: int = 720):
        self.width = width
        self.height = height

    def render(
        self,
        world: Any,
        player: Any,
        hands: Any,
        smartphone: Any,
        ref_book: Any,
        input_mgr: Any
    ) -> Tuple[bytes, int, int]:
        img = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)

        self._draw_hud(draw, world, player, input_mgr)

        if smartphone.is_open:
            self._draw_smartphone(draw, smartphone, player.position, world.weather.ambient_temp_c)

        if ref_book.is_open:
            self._draw_reference_book(draw, ref_book)

        if world.time_engine.is_menu_open:
            self._draw_time_menu(draw, world.time_engine)

        if input_mgr.is_paused:
            self._draw_pause_menu(draw)

        return img.tobytes(), self.width, self.height

    def _draw_hud(self, draw: ImageDraw.Draw, world: Any, player: Any, input_mgr: Any):
        cx, cy = self.width // 2, self.height // 2

        draw.line([(cx - 7, cy), (cx + 7, cy)], fill=(240, 240, 240, 200), width=2)
        draw.line([(cx, cy - 7), (cx, cy + 7)], fill=(240, 240, 240, 200), width=2)

        hint = input_mgr.get_tutorial_hint()
        if hint:
            draw.rectangle([320, 20, 960, 58], fill=(20, 26, 22, 215), outline=(70, 160, 95, 255), width=2)
            draw.text((335, 32), hint, fill=(230, 245, 230, 255))

        if world.notification:
            draw.rectangle([340, 68, 940, 102], fill=(28, 24, 20, 215), outline=(220, 140, 50, 255), width=1)
            draw.text((355, 78), world.notification, fill=(255, 220, 160, 255))

        draw.rectangle([35, 650, 485, 695], fill=(20, 22, 20, 200), outline=(120, 110, 85, 220), width=1)
        tools = [("1", "Lighter"), ("2", "Knife"), ("3", "Axe"), ("4", "Bow Drill"), ("5", "Kindling")]
        tx = 45
        for slot_k, name in tools:
            is_active = (slot_k == "1" and player.primary_hand == "pocket_lighter") or                         (slot_k == "2" and player.primary_hand == "pocket_knife") or                         (slot_k == "3" and player.primary_hand == "felling_axe") or                         (slot_k == "4" and player.primary_hand == "bow_drill_spindle") or                         (slot_k == "5" and player.primary_hand == "kindling")
            col = (255, 215, 0, 255) if is_active else (180, 180, 180, 200)
            draw.text((tx, 665), f"[{slot_k}] {name}", fill=col)
            tx += 88

        draw.rectangle([515, 660, 765, 685], fill=(18, 22, 20, 210), outline=(80, 140, 90, 220), width=1)
        stamina_pct = max(0.0, min(1.0, player.stamina / 100.0))
        draw.rectangle([517, 662, 517 + int(244 * stamina_pct), 683], fill=(50, 180, 80, 240))
        draw.text((570, 666), f"STAMINA: {player.stamina:.0f}%   [F] Blow", fill=(240, 240, 240, 255))

        draw.rectangle([980, 545, 1245, 695], fill=(18, 20, 22, 215), outline=(210, 95, 30, 230), width=1)
        draw.text((995, 555), "CAMPFIRE THERMODYNAMICS", fill=(255, 145, 50, 255))
        draw.text((995, 578), f"Core Temp: {world.thermal_grid.core_coal_temp:.1f}°C", fill=(255, 205, 100, 255))
        draw.text((995, 600), f"Heat Flux: {world.thermal_grid.current_heat_flux:.0f} W", fill=(255, 205, 100, 255))
        draw.text((995, 622), f"Draft Speed: {world.thermal_grid.draft_velocity:.2f} m/s", fill=(200, 225, 255, 255))
        draw.text((995, 644), f"Oxygen Sat: {world.thermal_grid.oxygen_fraction*100.0:.1f}%", fill=(200, 225, 255, 255))
        draw.text((995, 666), f"Season: {world.weather.current_season.value} | {world.weather.ambient_temp_c:.1f}°C", fill=(180, 210, 180, 255))

    def _draw_smartphone(self, draw: ImageDraw.Draw, phone: Any, player_pos: np.ndarray, ambient_temp: float):
        px, py, pw, ph = 830, 35, 415, 650
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=24, fill=(15, 20, 18, 250), outline=(60, 145, 85, 255), width=3)

        state = phone.get_display_state(player_pos, ambient_temp)
        draw.text((px + 20, py + 16), f"GPS: {state['gps_coords'][0]}, {state['gps_coords'][1]} | BAT: {phone.battery_percent:.0f}% | {state['ambient_temp']}°C", fill=(160, 220, 170, 255))
        draw.line([(px + 12, py + 38), (px + pw - 12, py + 38)], fill=(60, 140, 80, 200), width=1)

        is_store = (phone.active_app.value == "Store ($)")
        draw.text((px + 30, py + 48), "[1] STORE ($)", fill=(120, 255, 140, 255) if is_store else (140, 160, 140, 200))
        draw.text((px + 220, py + 48), "[2] TOPO MAP", fill=(120, 255, 140, 255) if not is_store else (140, 160, 140, 200))
        draw.line([(px + 12, py + 70), (px + pw - 12, py + 70)], fill=(60, 140, 80, 200), width=1)

        if is_store:
            draw.text((px + 24, py + 80), f"BALANCE: {phone.credits.credits:.1f} CREDITS", fill=(255, 215, 0, 255))
            iy = py + 105
            for it in state["store_catalog"]:
                is_sel = it["is_selected"]
                bg = (38, 55, 42, 255) if is_sel else (20, 26, 22, 255)
                draw.rectangle([px + 18, iy, px + pw - 18, iy + 34], fill=bg, outline=(80, 180, 100, 255) if is_sel else None)
                cursor = "> " if is_sel else "  "
                draw.text((px + 24, iy + 4), f"{cursor}{it['name']}", fill=(255, 255, 255, 255) if is_sel else (180, 200, 180, 255))
                draw.text((px + pw - 78, iy + 4), f"{it['cost']:.0f} Cr", fill=(255, 215, 0, 255))
                draw.text((px + 38, iy + 18), f"[{it['cat']}]", fill=(120, 160, 130, 200))
                iy += 38

            sel_it = state["store_catalog"][phone.store.selected_index]
            dy = py + ph - 135
            draw.rectangle([px + 18, dy, px + pw - 18, dy + 85], fill=(22, 30, 25, 255), outline=(50, 100, 65, 255), width=1)
            draw.text((px + 24, dy + 6), sel_it["name"], fill=(255, 225, 120, 255))
            draw.text((px + 24, dy + 24), sel_it["desc"][:44], fill=(200, 220, 200, 255))
            if len(sel_it["desc"]) > 44:
                draw.text((px + 24, dy + 40), sel_it["desc"][44:88], fill=(200, 220, 200, 255))
            draw.text((px + 24, dy + 64), f"Status: {phone.status_message}", fill=(100, 220, 255, 255))
        else:
            mx, my, mw, mh = px + 20, py + 80, pw - 40, ph - 160
            draw.rectangle([mx, my, mx + mw, my + mh], fill=(20, 26, 22, 255), outline=(60, 120, 80, 255), width=1)
            draw.text((mx + 10, my + 8), f"ZONE: {state['zone_name']} ({state['humidity']:.0f}% RH)", fill=(140, 220, 160, 255))

            cx = mx + mw // 2
            cy = my + mh // 2
            scale = mw / 120.0

            for r in [20, 40, 60, 80, 100]:
                draw.ellipse([cx - r, cy - int(r*0.7), cx + r, cy + int(r*0.7)], outline=(50, 85, 60, 180), width=1)

            draw.rectangle([cx - 4, cy - 4, cx + 4, cy + 4], fill=(240, 80, 20, 255))
            draw.text((cx + 6, cy - 6), "Hearth", fill=(240, 140, 60, 255))

            rx = cx + int(3.5 * scale)
            ry = cy + int(1.5 * scale)
            draw.rectangle([rx - 3, ry - 3, rx + 3, ry + 3], fill=(80, 180, 240, 255))
            draw.text((rx + 5, ry - 6), "Rack", fill=(120, 200, 255, 255))

            px_m = cx + int(player_pos[0] * scale)
            py_m = cy + int(player_pos[2] * scale)
            draw.ellipse([px_m - 5, py_m - 5, px_m + 5, py_m + 5], fill=(255, 255, 255, 255), outline=(0, 220, 255, 255), width=2)
            draw.text((px_m + 7, py_m - 6), "YOU", fill=(255, 255, 255, 255))

        draw.text((px + 24, py + ph - 35), "[W/S] Nav  [E/Enter] Buy  [Q] App  [Tab] Exit", fill=(140, 170, 140, 220))

    def _draw_reference_book(self, draw: ImageDraw.Draw, ref_book: Any):
        bx, by, bw, bh = 140, 50, 1000, 620
        draw.rounded_rectangle([bx, by, bx + bw, by + bh], radius=16, fill=(35, 30, 24, 250), outline=(180, 150, 100, 255), width=3)
        pdata = ref_book.get_current_page_data()

        draw.text((bx + 40, by + 30), f"FIREMASTER'S FIELD COMPENDIUM - PAGE {pdata['page_number']} OF {pdata['total_pages']}", fill=(240, 215, 160, 255))
        draw.line([(bx + 35, by + 56), (bx + bw - 35, by + 56)], fill=(140, 110, 70, 200), width=2)

        draw.text((bx + 45, by + 75), pdata["title"], fill=(255, 235, 190, 255))
        draw.text((bx + 45, by + 102), pdata["subtitle"], fill=(200, 175, 130, 220))

        lines = pdata["content"].split("\n")
        cy = by + 140
        for line in lines:
            draw.text((bx + 45, cy), line, fill=(225, 215, 195, 255))
            cy += 28

        bp = pdata.get("blueprint")
        if bp:
            self._draw_blueprint_schematic(draw, bp, bx + bw - 260, by + 280)

        draw.line([(bx + 35, by + bh - 50), (bx + bw - 35, by + bh - 50)], fill=(140, 110, 70, 200), width=1)
        draw.text((bx + 45, by + bh - 38), "[A / Left] Previous Page    [D / Right] Next Page    [B / Esc] Close Journal", fill=(180, 160, 120, 220))

    def _draw_blueprint_schematic(self, draw: ImageDraw.Draw, bp: Any, cx: int, cy: int, scale: float = 160.0):
        bw, bh = 340, 230
        bx, by = cx - bw // 2, cy - bh // 2
        draw.rectangle([bx, by, bx + bw, by + bh], fill=(16, 22, 28, 240), outline=(70, 130, 190, 255), width=2)
        draw.text((bx + 12, by + 10), f"BLUEPRINT: {bp.name.upper()}", fill=(120, 190, 255, 255))

        for slot in bp.slots:
            sx = cx + int(slot.position[0] * scale)
            sy = cy - int(slot.position[2] * scale)
            dim_l = max(8, int(slot.dimensions[0] * scale * 0.35))
            dim_r = max(4, int(slot.dimensions[1] * scale * 0.8))

            if slot.expected_type == "tinder":
                draw.ellipse([sx - dim_r*2, sy - dim_r*2, sx + dim_r*2, sy + dim_r*2], fill=(240, 150, 50, 255))
            elif slot.expected_type == "kindling":
                draw.rectangle([sx - dim_l, sy - dim_r, sx + dim_l, sy + dim_r], outline=(220, 190, 90, 255), width=2)
            else:
                draw.rectangle([sx - dim_l, sy - dim_r, sx + dim_l, sy + dim_r], fill=(130, 95, 65, 255), outline=(210, 175, 135, 255), width=1)
            draw.text((sx + dim_r + 2, sy - 6), slot.slot_id, fill=(190, 215, 240, 200))

    def _draw_time_menu(self, draw: ImageDraw.Draw, time_engine: Any):
        tx, ty, tw, th = 380, 120, 520, 480
        draw.rounded_rectangle([tx, ty, tx + tw, ty + th], radius=14, fill=(24, 20, 16, 245), outline=(190, 130, 60, 255), width=2)
        draw.text((tx + 30, ty + 24), "FAST-FORWARD TIME ENGINE ('T')", fill=(255, 215, 140, 255))
        draw.line([(tx + 20, ty + 54), (tx + tw - 20, ty + 54)], fill=(140, 100, 50, 200), width=1)

        from firestarter.simulation.time_engine import TIME_SKIP_OPTIONS
        iy = ty + 75
        for i, opt in enumerate(TIME_SKIP_OPTIONS):
            is_sel = (i == time_engine.selected_option_index)
            bg = (55, 42, 28, 255) if is_sel else (26, 22, 18, 255)
            draw.rectangle([tx + 25, iy, tx + tw - 25, iy + 42], fill=bg, outline=(220, 160, 80, 255) if is_sel else None)
            cursor = "> " if is_sel else "  "
            draw.text((tx + 35, iy + 6), f"{cursor}{opt.label}", fill=(255, 255, 255, 255) if is_sel else (200, 180, 150, 255))
            draw.text((tx + 50, iy + 22), opt.description[:54], fill=(170, 150, 120, 220))
            iy += 50

        draw.text((tx + 30, ty + th - 35), "[W/S / Up/Down] Select   [Enter / E] Confirm   [T / Esc] Cancel", fill=(180, 150, 100, 220))

    def _draw_pause_menu(self, draw: ImageDraw.Draw):
        px, py, pw, ph = 460, 260, 360, 180
        draw.rounded_rectangle([px, py, px + pw, py + ph], radius=12, fill=(20, 22, 24, 240), outline=(120, 140, 160, 255), width=2)
        draw.text((px + 105, py + 35), "GAME PAUSED", fill=(240, 240, 240, 255))
        draw.text((px + 65, py + 85), "[Esc] Resume Physical Simulation", fill=(180, 210, 180, 255))
        draw.text((px + 65, py + 120), "[Tab] Open Wilderness Phone", fill=(180, 210, 240, 255))
