from models import PowerTech, PlantFleet

TECH_CATALOG = {
    "Vattenkraft": PowerTech(
        name="Vattenkraft",
        capex_per_mw=25.0, opex_fix_per_mw=0.3, opex_var_per_mwh=40,
        build_time_years=4, lifespan_years=80, marginal_cost=50,
        base_cap_factor=0.50, is_variable=False, max_capacity_mw=18000.0
    ),
    "Karnkraft": PowerTech(
        name="Kärnkraft (Storskalig)",
        capex_per_mw=65.0, opex_fix_per_mw=0.8, opex_var_per_mwh=120,
        build_time_years=7, lifespan_years=60, marginal_cost=180,
        base_cap_factor=0.88, is_variable=False, max_capacity_mw=18000.0
    ),
    "SMR_Karnkraft": PowerTech(
        name="SMR-kärnkraft (Modulär)",
        capex_per_mw=50.0, opex_fix_per_mw=0.6, opex_var_per_mwh=140,
        build_time_years=3, lifespan_years=50, marginal_cost=190,
        base_cap_factor=0.90, is_variable=False, max_capacity_mw=10000.0
    ),
    "Vind_Land": PowerTech(
        name="Vindkraft (Land)",
        capex_per_mw=12.0, opex_fix_per_mw=0.25, opex_var_per_mwh=30,
        build_time_years=2, lifespan_years=25, marginal_cost=30,
        base_cap_factor=0.33, is_variable=True, max_capacity_mw=30000.0
    ),
    "Vind_Hav": PowerTech(
        name="Vindkraft (Hav)",
        capex_per_mw=28.0, opex_fix_per_mw=0.5, opex_var_per_mwh=45,
        build_time_years=4, lifespan_years=30, marginal_cost=35,
        base_cap_factor=0.48, is_variable=True, max_capacity_mw=25000.0
    ),
    "Solkraft": PowerTech(
        name="Solkraft (Park)",
        capex_per_mw=7.0, opex_fix_per_mw=0.1, opex_var_per_mwh=10,
        build_time_years=1, lifespan_years=25, marginal_cost=10,
        base_cap_factor=0.11, is_variable=True, max_capacity_mw=20000.0
    ),
    "Energilagring": PowerTech(
        name="Energilagring (Batteri/Vätgas)",
        capex_per_mw=10.0, opex_fix_per_mw=0.15, opex_var_per_mwh=60,
        build_time_years=1, lifespan_years=20, marginal_cost=350,
        base_cap_factor=0.85, is_variable=False, max_capacity_mw=15000.0
    ),
    "Kraftvarme": PowerTech(
        name="Kraftvärme/Bio",
        capex_per_mw=18.0, opex_fix_per_mw=0.4, opex_var_per_mwh=350,
        build_time_years=3, lifespan_years=35, marginal_cost=450,
        base_cap_factor=0.40, is_variable=False, max_capacity_mw=6000.0
    ),
    "Spetseffekt": PowerTech(
        name="Gas/Olja (Spets)",
        capex_per_mw=8.0, opex_fix_per_mw=0.15, opex_var_per_mwh=1200,
        build_time_years=2, lifespan_years=30, marginal_cost=2200,
        base_cap_factor=0.05, is_variable=False, max_capacity_mw=5000.0
    )
}

START_FLEET = [
    PlantFleet("Vattenkraft", 16200, age=40),
    PlantFleet("Karnkraft", 6900, age=35),
    PlantFleet("Vind_Land", 14500, age=8),
    PlantFleet("Vind_Hav", 200, age=10),
    PlantFleet("Solkraft", 3500, age=3),
    PlantFleet("Kraftvarme", 3800, age=20),
    PlantFleet("Spetseffekt", 2000, age=25),
]
