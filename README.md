# Firestarter

> *"Life will grow, fire will come, and the cycle will repeat."*

**Firestarter** is a high-fidelity wilderness thermodynamics and chemistry simulation game written in Python. Unlike traditional survival games that treat fire as a simple toggle timer or single-item recipe, *Firestarter* models the real-world physics and organic chemistry of combustion: moisture gradients (surface vs. core), cellular decay, density variations across tree species, airflow vacuum/draft dynamics, volatile gasification, and fuel geometry.

Beginning with a simple guided tutorial and a pocket lighter with limited fuel, you will learn to construct your first tinder nest and coax flame from dry shavings. As supplies run out, you must turn to ancient primitive survival skills—carving bow drills from green bark cordage, grinding spindle sticks against notched hearthboards, foraging smoldering bracket fungi, and felling timber with makeshift axes to season on covered racks across changing seasons.

---

## Key Features

### 1. Rigorous Thermodynamic & Organic Simulation
* **Moisture Gradient Modeling**: Wood is simulated with independent surface and core moisture values. A log wet on the outside but dry inside will steam briefly before catching; a log dry on the outside but wet inside will ignite readily, only to sputter and choke as core moisture vaporizes and saps thermal energy.
* **Species-Specific Wood Chemistry**:
  * **Softwoods (Pine, Cedar)**: Rich in volatile terpenes and resins; low density; ignite at lower thresholds; produce intense, fast-burning flames.
  * **Hardwoods (Oak, Birch)**: Dense cellular structure; difficult to ignite; yield long-lasting, high-caloric charcoal beds.
  * **Punk Wood (Decayed Wood)**: Highly porous sponge. Bone-dry rot catches the faintest spark and smolders relentlessly; damp rot acts as a thermal heat sink that refuses to burn.
* **Airflow, Draft & The Vacuum Effect**: Construct fire structures (Teepee, Log Cabin, Swedish Torch, Lean-to) to generate natural convective chimneys. A well-designed draft pulls ambient oxygen into the ember bed, exponentially multiplying heat. Pack logs too tightly, and the fire suffocates.
* **Four-Phase Combustion**: Dehydration (endothermic steam release) → Pyrolysis (release of volatile smoke and gases) → Flaming Combustion (gas phase reaction) → Smoldering Charcoal (slow carbon oxidation) → Inert Ash.

### 2. Primitive Bushcraft & Tool Crafting
* **Hand-Operated Physicality**: First-person interactive hands reach, grab, align, carve, and strike.
* **Cordage & Bow Drills**: Use your pocket knife to strip inner fibrous bark from living trees, twist it into cordage, string a bow branch, cut a 45° V-notch into a dry hearthboard, and generate embers through sustained friction.
* **Hand Drill & Stone Bearing**: Use a smooth flat river stone as a palm protector and a long hardwood spindle to drill into flat bases.
* **Ember Management & Coal Preservation**: Catch microscopic glowing coals in dry tinder nests (dry grass, pine needles, cedar shavings). Blow rhythmically to coax ember glow into self-sustaining flame. Harvest polypore and bracket mushrooms from rotting tree trunks to transport smoldering embers over miles and through days.

### 3. Forestry, Seasoning & Ecological Lifecycle
* **Wood Seasoning Systems**: Freshly cut green wood is saturated with sap. Build elevated drying racks to keep logs off moist soil, and cover them with tarps to shield against rain while allowing lateral airflow.
* **Time Passage Engine**: Advance time by hours, days, weeks, or months. Watch green oak logs slowly season to ideal 12% equilibrium moisture content, or watch unshielded ground logs rot into spongey decay.
* **Living Ecosystem**: Dynamic weather brings scorching summer sun, persistent autumn rains, and sub-zero winter blizzards. Trees drop seeds, saplings sprout, mature into forest canopy, die, rot into fungal host logs, and return nutrients to the soil.

### 4. Economy, The Smartphone & Tech Progression
* **Credit System**: Successfully building and maintaining hot, efficient fires awards research and survival credits.
* **Tab-Activated Smartphone**: Pull up your modern lifeline with the `Tab` key.
  * **Store App (`$`)**: Purchase essential gear—from replacement lighters and tarps to high-efficiency axes and costly liquid accelerants (lighter fluid, high-octane gasoline).
  * **Topo Map App**: View detailed topographical contours, forest biomes, moisture zones, and marked drying racks.
* **Firemaster's Reference Guide**: Unlock discovered and purchasable fire building recipes, cross-sections, and thermodynamic schematics.

---

## Controls

| Input | Action | Description |
| :--- | :--- | :--- |
| **W, A, S, D** | Move | Walk through the forest, slopes, and river valleys |
| **Mouse Look** | Look / Aim | Direct gaze and interaction crosshair |
| **Left Mouse Button (LMB)** | Primary Hand / Strike / Carve | Grab item, strike lighter, carve notch with knife, stroke bow drill |
| **Right Mouse Button (RMB)** | Secondary Hand / Place / Hold | Position fuel, hold bearing block stone, secure hearthboard |
| **Middle Mouse / Scroll** | Rotate Item | Adjust orientation of sticks/logs prior to placement |
| **F** | Blow on Ember | Deliver controlled breaths of air into ember nests or low coals |
| **Tab** | Smartphone | Toggle smartphone interface (Store & Topo Map) |
| **B** | Reference Book | Open fire recipe index, wood characteristics, and thermodynamic logs |
| **T** | Pass Time | Open the time-skipping menu (Advance hours, days, or months) |
| **Escape** | Pause / Settings | Open system menu, audio settings, and graphic presets |

---

## Installation & Getting Started

### Prerequisites
* **Python 3.10+** (Python 3.11+ recommended for performance optimizations)
* Dedicated GPU supporting OpenGL 3.3+ / Vulkan

### Setup Virtual Environment
```bash
# Clone the repository
git clone https://github.com/tndevteam-tommy/firestarter.git
cd firestarter

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Dependencies
* `moderngl` / `moderngl-window` (High-performance 3D rendering pipeline)
* `pyglm` (OpenGL Mathematics for Python)
* `numpy` (Thermodynamic grid calculations and moisture diffusion arrays)
* `scipy` (Thermal convection differential equations)
* `pygame-ce` (Input handling, audio mixer, and windowing context)
* `pillow` (Texture and UI surface handling)

### Running the Game
```bash
python main.py
```

---

## Early-Game Tutorial Walkthrough

1. **The Basics**: The game launches with an interactive tutorial. Inspect your surroundings; pick up dry birch shavings and fallen pine needles with `LMB`.
2. **Fuel Hierarchy**: Place fine tinder first, stack light kindling (dry twigs) in a mini-teepee above it, leaving an air channel facing upwind.
3. **The First Spark**: Equip your pocket lighter. Note the lighter fluid gauge. Click and hold near the tinder. The volatile sparks ignite the shavings.
4. **Airflow Balance**: Press `F` to blow gently if the flame wavers. Do not drop heavy damp sticks immediately—wait until kindling reaches 300°C (pyrolysis threshold) before adding pencil-sized twigs.
5. **Cashing In**: As your fire stabilizes into glowing coals, open your phone (`Tab`) to receive your first fire rewards and purchase a field tarp or cordage for the nights ahead.

---

## Visual & Atmospheric Philosophy
*Firestarter* avoids blocky/voxel designs in favor of stylized, painterly low-poly aesthetics paired with atmospheric physical shaders:
* Volumetric smoke plumes that change from white steam (moisture evaporation) to thick yellow/brown smoke (pyrolysis volatiles) to clear wavy heat shimmers (pure carbon oxidation).
* Dynamic day-night lighting with accurate sun vectors, dusk rim-lighting, and flickering fire illumination.
* ASMR-grade field audio: crackling dry pine resin, the hissing whistle of escaping sap in green logs, mountain wind, and rhythmic friction strokes.