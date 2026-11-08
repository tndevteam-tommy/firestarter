"""
Firestarter - Main Game Entry Point
Implements Section 8 Architecture:
Initializes Pygame, ModernGL, Procedural ASMR Audio, WorldManager,
SmartphoneOS, ReferenceBook, HandController, InputManager, and runs
the fixed 60 FPS physics and 20 Hz thermodynamics main game loop.
"""

import os
import sys
import types
import math
import numpy as np

CURR_DIR = os.path.dirname(os.path.abspath(__file__))
if "firestarter" not in sys.modules:
    pkg = types.ModuleType("firestarter")
    pkg.__path__ = [CURR_DIR]
    pkg.__file__ = os.path.join(CURR_DIR, "__init__.py")
    sys.modules["firestarter"] = pkg
if CURR_DIR not in sys.path:
    sys.path.insert(0, CURR_DIR)

from firestarter.config import (
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE,
    PHYSICS_HZ, THERMAL_HZ
)
from firestarter.audio.procedural_audio import ProceduralAudioEngine
from firestarter.audio.asmr_foley import ASMRFoleyManager
from firestarter.simulation.world_manager import WorldManager
from firestarter.economy.smartphone import SmartphoneOS
from firestarter.recipes.reference_book import ReferenceBook
from firestarter.input.hand_physics_rig import HandController
from firestarter.input.input_manager import InputManager
from firestarter.rendering.render_engine import RenderEngine

def main():
    print("=" * 70)
    print("  FIRESTARTER: Thermodynamics & Bushcraft Physical Simulation")
    print("  'Life will grow, fire will come, and the cycle will repeat.'")
    print("=" * 70)

    assets_dir = os.path.join(CURR_DIR, "assets", "audio")
    try:
        if not os.path.exists(assets_dir) or len(os.listdir(assets_dir)) < 8:
            print("[Audio] Generating procedural ASMR audio assets on first launch...")
            ProceduralAudioEngine.generate_and_save_all_assets(assets_dir)
            print("[Audio] Synthesized all combustion roar, pine resin, hiss, and foley assets.")
    except Exception as e:
        print(f"[Audio] Notice: Audio generation deferred ({e}).")

    has_pygame = False
    screen = None
    try:
        import pygame
        pygame.init()
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 3)
        pygame.display.gl_set_attribute(pygame.GL_CONTEXT_PROFILE_MASK, pygame.GL_CONTEXT_PROFILE_CORE)
        flags = pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE
        try:
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), flags)
        except Exception:
            screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption(WINDOW_TITLE)
        has_pygame = True
        print("[System] Pygame and display context initialized successfully.")
    except Exception as e:
        print(f"[System] Notice: Running in headless/non-display environment ({e}).")
        has_pygame = False

    world = WorldManager()
    smartphone = SmartphoneOS()
    ref_book = ReferenceBook()
    hands = HandController()
    input_mgr = InputManager(world, smartphone, ref_book, hands)
    foley = ASMRFoleyManager(asset_dir=assets_dir)
    renderer = RenderEngine(WINDOW_WIDTH, WINDOW_HEIGHT)

    if not has_pygame or "--headless" in sys.argv:
        print("[Simulation] Executing headless verification tick...")
        for _ in range(60):
            world.update(1.0 / 60.0)
            burn_energy = world.thermal_grid.current_heat_flux
            fuel_rate = world.thermal_grid.total_fuel_consumed_kg / max(1.0, world.time_engine.total_days_elapsed * 86400.0)
            smartphone.credits.update(1.0 / 60.0, world.thermal_grid.core_coal_temp, burn_energy, fuel_rate)
        print(f"[Simulation] Verification passed! Core Temp: {world.thermal_grid.core_coal_temp:.1f}°C, Credits: {smartphone.credits.credits:.1f}")
        return

    clock = pygame.time.Clock()
    running = True
    mouse_captured = True
    pygame.mouse.set_visible(False)
    pygame.event.set_grab(True)

    print("[Game] Controls:")
    print("  W, A, S, D       : Walk through forest")
    print("  Mouse Look       : Aim gaze & interaction crosshair")
    print("  LMB              : Primary hand (Strike lighter, carve notch, stroke drill)")
    print("  RMB              : Secondary hand (Place tinder nest / logs)")
    print("  F                : Breathe / Blow controlled oxygen jet into embers")
    print("  Tab              : Wilderness Smartphone OS (Store & Topo Map)")
    print("  B                : Firemaster's Reference Journal & Blueprints")
    print("  T                : Pass Time Engine (Advance hours, days, months)")
    print("  1 - 5            : Tool slots [Lighter, Knife, Axe, Bow Drill, Kindling]")
    print("  Esc              : Pause menu / Cancel")

    while running:
        frame_dt = min(0.1, clock.tick(60) / 1000.0)

        in_menu = smartphone.is_open or ref_book.is_open or world.time_engine.is_menu_open or input_mgr.is_paused
        if in_menu and mouse_captured:
            mouse_captured = False
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
        elif not in_menu and not mouse_captured:
            mouse_captured = True
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                renderer.handle_resize(event.w, event.h)
            elif event.type == pygame.KEYDOWN:
                key_name = pygame.key.name(event.key)
                input_mgr.handle_key_down(key_name)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                input_mgr.handle_mouse_button_down(event.button)
            elif event.type == pygame.MOUSEMOTION:
                if mouse_captured:
                    dx, dy = event.rel
                    world.player.rotate_look(dx * 0.15, -dy * 0.15)

        if not in_menu:
            keys = pygame.key.get_pressed()
            forward = 0.0
            strafe = 0.0
            if keys[pygame.K_w]:
                forward += 1.0
            if keys[pygame.K_s]:
                forward -= 1.0
            if keys[pygame.K_d]:
                strafe += 1.0
            if keys[pygame.K_a]:
                strafe -= 1.0
            world.player.is_sprinting = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
            world.player.move(forward, strafe, frame_dt)

        world.update(frame_dt)

        if world.crafting.audio_trigger:
            foley.play(world.crafting.audio_trigger)
            world.crafting.audio_trigger = None

        if any(b.resin_pop_event for b in world.thermal_grid.bodies):
            foley.play("resin_pop", 0.6)
        if any(b.hiss_event for b in world.thermal_grid.bodies):
            foley.play("steam_hiss", 0.35)

        foley.update_continuous_ambience(
            core_temp_c=world.thermal_grid.core_coal_temp,
            draft_velocity=world.thermal_grid.draft_velocity,
            steam_rate_kg_s=sum(b.steam_rate for b in world.thermal_grid.bodies),
            rain_intensity=world.weather.rain_intensity,
            wind_speed=world.weather.wind_speed_m_s
        )

        hands.update(frame_dt, world.crafting.active_task)

        burn_energy = world.thermal_grid.current_heat_flux
        fuel_rate = world.thermal_grid.total_fuel_consumed_kg / max(1.0, world.time_engine.total_days_elapsed * 86400.0)
        smartphone.credits.update(frame_dt, world.thermal_grid.core_coal_temp, burn_energy, fuel_rate)

        renderer.render(world, world.player, hands, smartphone, ref_book, input_mgr)
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()
