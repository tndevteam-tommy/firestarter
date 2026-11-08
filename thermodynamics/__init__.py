"""
Firestarter Thermodynamics Module
"""
from firestarter.thermodynamics.wood_properties import WoodSpeciesType, WoodProperties, get_wood_properties
from firestarter.thermodynamics.combustion_body import CombustionBody, CombustionStage
from firestarter.thermodynamics.moisture_diffusion import MoistureDiffusionEngine
from firestarter.thermodynamics.airflow_draft import AirflowDraftSolver
from firestarter.thermodynamics.thermal_grid import ThermodynamicGrid, ThermalConvectionSolver
