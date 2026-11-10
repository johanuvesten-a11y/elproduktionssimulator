from dataclasses import dataclass

@dataclass
class PowerTech:
    name: str
    capex_per_mw: float       # Investeringskostnad (MSEK / MW)
    opex_fix_per_mw: float    # Fast driftkostnad (MSEK / MW / år)
    opex_var_per_mwh: float   # Rörlig driftkostnad (SEK / MWh)
    build_time_years: int     # Byggtid (år)
    lifespan_years: int       # Livslängd (år)
    marginal_cost: float      # Marginalkostnad för Merit Order (SEK / MWh)
    base_cap_factor: float    # Kapacitetsfaktor (0.0 - 1.0)
    is_variable: bool         # Väderberoende (sol/vind)

@dataclass
class ConstructionProject:
    tech_name: str
    capacity_mw: float
    years_remaining: int
    total_capex: float

@dataclass
class PlantFleet:
    tech_name: str
    capacity_mw: float
    age: int
