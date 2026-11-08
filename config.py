"""
Firestarter - Configuration & Thermodynamic Physical Constants
"""

import math

# Simulation Tick Rates
PHYSICS_HZ = 60.0
PHYSICS_DT = 1.0 / PHYSICS_HZ       # 60 Hz physics

THERMAL_HZ = 20.0
THERMAL_DT = 1.0 / THERMAL_HZ       # 20 Hz thermal grid

# Physical and Thermodynamic Constants
STEFAN_BOLTZMANN = 5.670374419e-8    # W/(m^2 * K^4)
H_VAP_WATER = 2.260e6                # J/kg (2260 kJ/kg latent heat of vaporization)
H_FUS_ICE = 3.340e5                  # J/kg (334 kJ/kg latent heat of fusion)
CP_DRY_WOOD = 1700.0                 # J/(kg * K)
CP_WATER = 4184.0                    # J/(kg * K)
CP_CHARCOAL = 1000.0                 # J/(kg * K)
CP_AIR = 1005.0                      # J/(kg * K)

# Combustion & Oxidation Chemistry
# Carbon oxidation: C + O2 -> CO2 + 393.5 kJ/mol
# Molar mass of Carbon = 0.012 kg/mol => 393.5 / 0.012 = 3.279e7 J/kg (32.79 MJ/kg)
CARBON_COMBUSTION_HEAT = 3.279e7     # J/kg
AIR_DENSITY_STP = 1.204              # kg/m^3 at 20°C, 101.325 kPa
STANDARD_PRESSURE = 101325.0         # Pa
GRAVITY = 9.80665                    # m/s^2

# Oxygen Thresholds
O2_AMBIENT_FRACTION = 0.2095         # 20.95% ambient oxygen
O2_FLAMING_MIN = 0.12                # Minimum oxygen fraction required for flaming combustion (>12%)
O2_CHOKED_MAX = 0.10                 # Threshold under which fire is choked/smothered (<10%)

# Temperature Ranges and Thresholds (Degrees Celsius)
TEMP_WATER_BOILING = 100.0           # °C (Dehydration clamp)
TEMP_WATER_SUPERHEAT = 120.0         # °C
TEMP_PYROLYSIS_START = 200.0         # °C
TEMP_PYROLYSIS_HEMICELLULOSE = (200.0, 260.0)  # °C
TEMP_PYROLYSIS_CELLULOSE = (240.0, 350.0)      # °C
TEMP_PYROLYSIS_LIGNIN = (280.0, 500.0)         # °C
TEMP_FLAMING_MIN = 450.0             # °C (Volatile gas auto-ignition)
TEMP_CHAR_GLOW_MIN = 500.0           # °C
TEMP_CHAR_GLOW_MAX = 900.0           # °C
TEMP_EMBER_FORMATION = 380.0         # °C (Bow drill dust coal formation)
TEMP_TINDER_IGNITION = 550.0         # °C (Volatile release from tinder nest bursts into flame)

# Airflow Geometry Thresholds
CHOKE_GAP_METERS = 0.02              # 2 cm: gap spacing below which discharge coefficient Cd -> 0

# Friction Physics
BOW_DRILL_FRICTION_MU_RANGE = (0.45, 0.65)  # Dry pine on cedar
BOW_DRILL_FORCE_RANGE = (30.0, 80.0)        # Normal force in Newtons
BOW_DRILL_OMEGA_RANGE = (10.0, 25.0)        # Angular velocity in rad/s
BOW_DRILL_SPINDLE_RADIUS = 0.01             # Default 1.0 cm radius (2.0 cm dia)

# Breath Dynamics
BREATH_O2_FRACTION = 0.2095          # 21% O2 in fresh breath
BREATH_OPTIMAL_VELOCITY = 2.5        # m/s
BREATH_MAX_VELOCITY = 6.0            # m/s (blows dust away)
BREATH_MIN_VELOCITY = 0.8            # m/s (insufficient cooling compensation)

# Window and Graphics Defaults
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720
WINDOW_TITLE = "Firestarter - Thermodynamics & Bushcraft Simulation"
FOV_DEGREES = 65.0
CAMERA_NEAR = 0.05
CAMERA_FAR = 300.0

# Economy
CREDIT_K_HEAT = 0.005                # Multiplier for core temperature
CREDIT_K_EFF = 0.02                  # Multiplier for energy/fuel efficiency
