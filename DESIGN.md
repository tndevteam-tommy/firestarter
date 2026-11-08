# Firestarter: Technical Design & Architecture Specification (DESIGN.md)

---

## 1. Executive Summary & Core Pillars

### 1.1 Vision
**Firestarter** is a scientifically grounded, relaxing yet unforgiving physical simulation game focused on the craft, chemistry, and thermodynamics of fire-making and forestry. The game explores the full cyclical life of wood—from living tissue, to felled timber, seasoned fuel, glowing coals, and fertile ash.

### 1.2 Core Pillars
1. **Scientific Integrity**: Moisture, heat transfer (conduction, convection, radiation), cellular decay, density, and airflow follow real-world chemistry and thermodynamic equations.
2. **Tactile Bushcraft Physicality**: Real-time two-handed manipulation where players carve notches, twist cordage, drill for embers, and blow tinder into flame.
3. **Environmental Permanence**: Seasons, weather, and time cycles govern the seasoning of wood and forest ecology.
4. **Stylized Realism**: A painterly, high-fidelity visual aesthetic avoiding voxel blocks while retaining soothing, high-immersion wilderness audio.

---

## 2. Thermodynamic & Chemical Combustion Engine

Every combustive object in the game world inherits from `CombustionBody`. The simulation runs on a fixed tick rate ($60\text{ Hz}$ physics, $20\text{ Hz}$ thermal grid).

### 2.1 The Four-Stage Combustion State Machine

```
               [ Ambient Fuel ]
                      │
                      ▼ (Absorbs Heat: T > 100°C)
            ┌───────────────────┐
            │   1. Dehydration  │ ──> Emits White Water Vapor (Steam)
            └───────────────────┘     (Endothermic: Absorb 2260 kJ/kg)
                      │ (Moisture drops to ~0%)
                      ▼ (T > 250°C - 300°C)
            ┌───────────────────┐
            │   2. Pyrolysis    │ ──> Emits Dense Volatile Smoke
            └───────────────────┘     (Tar, CO, Methanol, Formic Acid)
                      │
        ┌─────────────┴─────────────┐
        ▼ (Oxygen + T > 450°C)       ▼ (Smoldering Phase)
┌───────────────────┐       ┌───────────────────┐
│ 3. Flaming Phase  │       │ 4. Glowing Coals  │
│ (Gas Oxidation)   │       │ (Char Oxidation)  │
└───────────────────┘       └───────────────────┘
        │                           │
        └─────────────┬─────────────┘
                      ▼
               [ Inert Ash ]
```

1. **Dehydration ($T \approx 100^\circ\text{C} - 120^\circ\text{C}$)**:
   * Endothermic reaction: Log absorbs $2{,}260\text{ kJ/kg}$ of water evaporated.
   * Internal temperature remains clamped near $100^\circ\text{C}$ until the localized zone is dry.
   * Visual: Dense white water steam, distinct crackling hiss.

2. **Pyrolysis ($T \approx 200^\circ\text{C} - 450^\circ\text{C}$)**:
   * Thermal decomposition of hemicellulose ($200-260^\circ\text{C}$), cellulose ($240-350^\circ\text{C}$), and lignin ($280-500^\circ\text{C}$).
   * Emits heavy volatile gases (tar, carbon monoxide, methane).
   * Visual: Acrid yellow-grey smoke.

3. **Flaming Combustion ($T > 450^\circ\text{C}$ with $O_2 > 12\%$)**:
   * Ignition of volatile gases above fuel surface.
   * Highly exothermic: radiates heat back into adjacent wood pieces.
   * Flame height and heat flux $\dot{Q}$ proportional to volatile emission rate and air draft velocity.

4. **Char Oxidation / Glowing Coals ($T \approx 500^\circ\text{C} - 900^\circ\text{C}$)**:
   * Solid carbon reacts directly with oxygen: $\text{C} + \text{O}_2 \rightarrow \text{CO}_2 + 393.5\text{ kJ/mol}$.
   * Low flame, sustained long-wavelength infrared radiation.
   * Lasts significantly longer in high-density hardwoods than low-density softwoods.

5. **Ash Deposition**:
   * Non-combustible mineral content (silica, calcium, potassium carbonates).
   * Ash layer acts as an insulating blanket, reducing oxygen diffusion to coals unless cleared or blown upon.

---

### 2.2 Moisture Gradient Formulation

Wood moisture is discretized into radial layers: $M_{\text{surface}}$ and $M_{\text{core}}$.

$$\frac{\partial M}{\partial t} = D_m \left( \nabla^2 M \right) - R_{\text{evap}}(T)$$

* **Surface Wet / Core Dry**:
  * $M_{\text{surface}} = 0.65$, $M_{\text{core}} = 0.12$
  * Requires constant pilot flame to steam off surface moisture. Once dried, core ignites immediately with rapid combustion.
* **Surface Dry / Core Wet**:
  * $M_{\text{surface}} = 0.08$, $M_{\text{core}} = 0.85$
  * Easily catches a spark. As thermal wave penetrates inward, moisture boils, expanding outward and quenching surface flames with steam.
* **Green Log**:
  * $M_{\text{surface}} = 0.80$, $M_{\text{core}} = 1.10$ (110% dry-basis moisture content).
  * Incapable of sustaining combustion without continuous massive external heat flux or high-octane accelerants.

---

### 2.3 Wood Species & Cellular Property Matrix

| Species | Classification | Bulk Density ($\text{kg/m}^3$) | Resin Content (Volatiles) | Charcoal Caloric Value | Moisture Diffusion Coeff ($D_m$) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **White Pine** | Softwood | 380 | 18.5% (Terpenes) | 18.2 MJ/kg (Fast burn) | $1.8 \times 10^{-5}\text{ m}^2/\text{s}$ |
| **Red Cedar** | Softwood | 360 | 22.0% (Resinous oils) | 17.8 MJ/kg (Flaring) | $2.1 \times 10^{-5}\text{ m}^2/\text{s}$ |
| **Paper Birch** | Hardwood | 650 | 14.0% (Betulin in bark) | 22.4 MJ/kg (Balanced) | $1.2 \times 10^{-5}\text{ m}^2/\text{s}$ |
| **White Oak** | Hardwood | 780 | 4.2% (Low volatiles) | 28.6 MJ/kg (Enduring) | $0.6 \times 10^{-5}\text{ m}^2/\text{s}$ |
| **Punk Wood** | Decayed Fibers | 120 | 1.0% (Lignin-depleted) | 12.0 MJ/kg (Smolder only) | $8.5 \times 10^{-5}\text{ m}^2/\text{s}$ (Sponge) |

---

### 2.4 Airflow, Convective Chimney & Draft Vacuum

The thermal updraft velocity $U_{\text{draft}}$ in a fire structure is governed by the Stack Effect:

$$U_{\text{draft}} = C_d \sqrt{2 g H \frac{T_{\text{int}} - T_{\text{amb}}}{T_{\text{int}}}}$$

Where:
* $H$ = Vertical height of fire structure.
* $T_{\text{int}}$ = Internal temperature of combustion chamber.
* $T_{\text{amb}}$ = Ambient air temperature.
* $C_d$ = Discharge coefficient determined by log clearance.

A low-pressure vacuum zone is induced at the base of the fire:
$$P_{\text{base}} = P_{\text{amb}} - \frac{1}{2} \rho_{\text{air}} U_{\text{draft}}^2$$

* **Teepee Design**: Maximizes $H$, creating high updraft speed $U_{\text{draft}}$ for rapid ignition.
* **Log Cabin / Cross-Hatch**: Balances vertical draft with ample lateral intake pathways, sustaining large stable coal beds.
* **Choked Layout**: If fuel logs are placed edge-to-edge without gap spacing ($< 2\text{ cm}$), $C_d \rightarrow 0$. Oxygen saturation drops below $10\%$, extinguishing open flame and generating smothering carbon monoxide smoke.

---

## 3. Bushcraft & Friction Physics Simulation

### 3.1 The Bow Drill System

A bow drill consists of 5 physical components:
1. **Bow**: Flexible green branch tied with hand-twisted bark cordage.
2. **Cordage**: Strip of inner basswood/cedar cambium twisted into a two-ply reverse wrap.
3. **Spindle**: Straight dry softwood dowel ($1.5 - 2.5\text{ cm}$ diameter).
4. **Hearthboard**: Flat dry softwood piece ($1.5 - 2.0\text{ cm}$ thick).
5. **Bearing Block / Socket**: Hard flat river stone or oiled hardwood held in off-hand to apply downward normal force $F_N$.

#### Mathematical Friction & Coal Formation Model:
The mechanical power dissipated into thermal energy at the spindle-board contact is:
$$P = \mu \cdot F_N \cdot \omega \cdot r_{\text{spindle}}$$

Where:
* $\mu$ = Coefficient of kinetic friction ($0.45 - 0.65$ for dry pine on cedar).
* $F_N$ = Downward player pressure ($30 - 80\text{ N}$).
* $\omega$ = Angular velocity generated by back-and-forth bow strokes ($10 - 25\text{ rad/s}$).
* $r_{\text{spindle}}$ = Spindle radius.

#### The V-Notch Collector:
* The player must use their pocket knife to carve a $45^\circ$ wedge into the edge of the hearthboard directly touching the friction socket.
* As friction grinds wood fibers, it generates fine wood dust (char cloth equivalent).
* Once local temperature exceeds $380^\circ\text{C}$, the dust falling into the notch oxidizes into a self-sustaining microscopic ember ($1 - 3\text{ mm}$).

### 3.2 Hand Drill & Stone Spindle Method
* Employs longer spindle ($40 - 60\text{ cm}$) rotated directly between hands or with a flat bearing stone handle.
* Requires greater player stamina and rapid downward hand travel.

### 3.3 Tinder Preparation & Blowing Dynamics
* An ember cannot ignite a log directly. The player must nest the ember inside dry tinder (fine cedar shavings, dry pine needles, cattail fluff).
* **Breathing Mechanic (`F` key)**:
  * Delivers a pulsed jet of oxygen ($21\% \text{ O}_2$, velocity $v_{\text{breath}}$).
  * Too weak: Heat dissipates into ambient air faster than generation rate ($dQ/dt < 0$).
  * Too strong: Blows hot charcoal dust away, disrupting the fragile thermal core.
  * Optimal rhythm: Deep rhythmic puffs elevate ember temperature to $> 550^\circ\text{C}$, igniting volatile gases from the tinder nest into open flame.

### 3.4 Smoldering Fungi (Amadou & Chaga)
* Birch Polypore (*Piptoporus betulinus*) and Tinder Fungus (*Fomes fomentarius*) can be harvested from standing dead timber.
* When dried, their internal trama layer smolders at a controlled rate ($0.5 - 1.5\text{ cm/hour}$) without producing open flame, serving as a biological ember carrier across travel.

---

## 4. Forestry, Seasoning & Temporal Progression

### 4.1 Tree Anatomy & Felling
* Trees have bark, sapwood, and heartwood layers.
* Using a crafted stone axe or purchased steel axe, players make a directional notch followed by a back-cut.
* Dynamic rigid-body tree collapse calculates branch break-off upon ground impact.

### 4.2 Seasoning Physics & Time Dilation
* Freshly cut timber has living moisture ($M > 80\%$).
* Building **Raised Platforms** lifts logs off soil:
  * Eliminates capillary water transfer: $J_{\text{ground}} = 0$.
  * Exposes undersides to ambient wind airflow ($v_{\text{wind}}$).
* Adding a **Waterproof Tarp**:
  * Prevents rain penetration: $P_{\text{rain}} = 0$.
  * Creates an open-sided microclimate accelerating convective moisture loss.
* **Time Passage Engine (`T` key)**:
  * Fast-forward simulation over days, weeks, and seasons.
  * An unshielded log on dirt in autumn/winter: $M \rightarrow 95\%$, fungal rot spores colonize, converting log into soaked sponge punk wood.
  * A tarped, elevated log in summer: $M \rightarrow 12\%$ (ideal equilibrium moisture content) in 60 in-game days.

```
       [ Seasoning Performance Over 90 In-Game Days ]
  Moisture (%)
   100% ┌─────────────────────── Uncovered on Ground (Decaying)
    80% │   ╲  .-.     .-.  .-.
    60% │    ╲/   ╲   /   ╲/   ╲ Ground Capillary + Rain Soaking
    40% │     ╲    '-'
    20% │      ╲
     0% └───────┴──────────────────── Tarped on Raised Rack (Cured)
        0d     30d     60d     90d
```

---

## 5. Economy & Smartphone OS Architecture

### 5.1 The Smartphone Interface (`Tab` Key)
* Modeled as a rugged wilderness smartphone with low-power e-ink / OLED UI.
* Fixed screen overlay rendered via UI shader pipeline.

#### App 1: Store (`$`)
* Currency: **Credits** earned via fire mastery score:
  $$\text{Credits} = \int \left( k_{\text{heat}} \cdot T_{\text{core}} + k_{\text{eff}} \cdot \frac{\text{Energy Produced}}{\text{Fuel Consumed}} \right) dt$$
* **Catalog Items**:
  * *Pocket Lighter Refill Fluid* (Mid-tier expense; small lighter holds 4 fire starts)
  * *Waterproof Polyethylene Tarp* (Essential for log seasoning)
  * *High-Carbon Steel Pocket Knife* (Durable carving and bark stripping)
  * *Drop-Forged Felling Axe* (Felling mature hardwoods)
  * *Gasoline Canister (1 Gallon)* (Endgame accelerant: explosive volatility, instantly overcomes high moisture)
  * *Field Reference Book Editions* (Unlocks advanced fire architectural blueprints)

#### App 2: Topographical Map
* Real-time GPS topomap displaying contour lines (elevation intervals $5\text{ m}$).
* Displays microclimate humidity zones (marshy creek beds vs. dry, sun-baked ridge tops).
* Marks user-constructed log drying racks, historical fire pits, and known fungal stands.

---

## 6. Fire Recipes & Architectural Reference Book

Players construct fires either freeform or guided by holographic recipe bounds:

1. **Teepee Fire**:
   * *Ideal for*: Fast initial warmth, rapid ignition.
   * *Draft Profile*: Concentrated vertical draft. Consumes fuel quickly.
2. **Log Cabin Fire**:
   * *Ideal for*: Cooking, enduring coal beds.
   * *Draft Profile*: High volume, multi-directional intake. Stable internal heat trap.
3. **Lean-To Fire**:
   * *Ideal for*: High wind resistance.
   * *Draft Profile*: Uses a large windward back-log as a thermal reflector and wind deflector.
4. **Swedish Torch (Canadian Candle)**:
   * *Ideal for*: Single-log, self-contained, long-duration burning.
   * *Method*: Single vertical log split with chainsaw/axe into quarters, packed with shavings down the center bore. Emits vertical torch flame for hours.
5. **Star Fire**:
   * *Ideal for*: Low fuel consumption.
   * *Method*: Logs pushed into central ember bed tip-first; advanced inward as consumed.

---

## 7. Procedural World, Weather & Ecosystem Cycle

### 7.1 Environmental Parameters
* **Summer**: High solar radiation ($I_{\text{sun}} > 900\text{ W/m}^2$), high ambient temp ($25 - 35^\circ\text{C}$), rapid moisture evaporation.
* **Autumn**: Continuous rain showers, falling dry leaves providing temporary tinder, rising ground moisture.
* **Winter**: Freezing temperatures ($-15^\circ\text{C}$ to $-2^\circ\text{C}$), snow accumulation. Wood freezes; fire requires extra preheat enthalpy to melt ice before dehydration begins.
* **Spring**: Snowmelt saturation, river flooding, abundant sap flow in green wood.

### 7.2 Forest Lifecycle Dynamics
* **Seeds**: Pine cones and acorns fall based on seasonal wind vectors.
* **Sapling Growth**: Soil fertility influenced by historical ash deposits from past campfires.
* **Tree Decay & Mycological Colonization**: Fallen logs progress from Sound Hardwood → Seasoned Wood → Wet Punk Wood → Decomposed Humus. Bracket mushrooms fruit during late decay stages.

---

## 8. Software Architecture & Technical Implementation

```
┌────────────────────────────────────────────────────────┐
│                      main.py                           │
└──────────────────────────┬─────────────────────────────┘
                           │
 ┌─────────────────────────┼───────────────────────────┐
 │                         │                           │
 ▼                         ▼                           ▼
┌──────────────┐   ┌──────────────┐            ┌──────────────┐
│ RenderEngine │   │ WorldManager │            │ InputManager │
│ (ModernGL)   │   │ (Terrain,    │            │ (Keyboard,   │
│ - Shaders    │   │  Weather,    │            │  Mouse Hands)│
│ - Post-Proc  │   │  Ecosystem)  │            └──────────────┘
└──────┬───────┘   └──────┬───────┘                   │
       │                  │                           │
       └──────────┬───────┴───────────────────────────┘
                  ▼
        ┌───────────────────────────────────┐
        │       Simulation Subsystems       │
        ├───────────────────────────────────┤
        │ • ThermodynamicGrid               │
        │ • MoistureDiffusionEngine         │
        │ • AirflowDraftSolver              │
        │ • BushcraftCraftingController     │
        │ • HandPhysicsRig (IK Dual Hands)  │
        │ • SmartphoneOS (UI Overlay)       │
        └───────────────────────────────────┘
```

### 8.1 Key Python Classes
* `CombustionBody`: Base class for logs, twigs, shavings, tinder nests, and coal embers. Tracks $M_{\text{surface}}, M_{\text{core}}, T_{\text{internal}}, \text{mass},\text{ash\_mass}$, and spatial bounding mesh.
* `ThermalConvectionSolver`: Solves 3D cellular convection currents and draft vectors between adjacent logs using finite-difference Navier-Stokes approximations.
* `HandController`: Procedural inverse kinematics (IK) system animating player hands for reach, grasp, two-handed cordage twisting, and bow drill stroking.
* `SmartphoneApp`: State machine rendering dynamic vector UI onto an in-game phone screen texture with interactive app switching.

---

## 9. Audio & ASMR Sensory Design

1. **Combustion Acoustics**:
   * Multilayered procedural sound: low-frequency roar (draft air intake), high-frequency resin pops (steam bursts inside pine cells), and continuous fine hiss (drying moisture).
2. **Bushcraft Foley**:
   * Crisp whittling of dry cedar ribbons.
   * Rhythmic friction squeak and groan of hardwood dowel on pine baseboard under heavy load.
   * Soft, breathy blowing audio with instantaneous pitch response to key press velocity.
3. **Environmental Ambience**:
   * Wind whistling through mountain passes, patter of raindrops on stretched tarp canvas, and forest silence muffled by falling winter snow.
