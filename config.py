from models import PowerTech, PlantFleet

# Teknikdata (Siffror i MSEK/MW och SEK/MWh)
TECH_CATALOG = {
    "Vattenkraft": PowerTech(
        name="Vattenkraft",
        capex_per_mw=25.0, opex_fix_per_mw=0.3, opex_var_per_mwh=40,
        build_time_years=4, lifespan_years=80, marginal_cost=50,
        base_cap_factor=0.50, is_variable=False
    ),
    "Kärnkraft": PowerTech(
        name="Kärnkraft",
        capex_per_mw=65.0, opex_fix_per_mw=0.8, opex_var_per_mwh=120,
        build_time_years=7, lifespan_years=60, marginal_cost=180,
        base_cap_factor=0.88, is_variable=False
    ),
    "Vind_Land": PowerTech(
        name="Vindkraft (Land)",
        capex_per_mw=12.0, opex_fix_per_mw=0.25, opex_var_per_mwh=30,
        build_time_years=2, lifespan_years=25, marginal_cost=30,
        base_cap_factor=0.33, is_variable=True
    ),
    "Vind_Hav": PowerTech(
        name="Vindkraft (Hav)",
        capex_per_mw=28.0, opex_fix_per_mw=0.5, opex_var_per_mwh=45,
        build_time_years=4, lifespan_years=30, marginal_cost=35,
        base_cap_factor=0.48, is_variable=True
    ),
    "Solkraft": PowerTech(
        name="Solkraft (Park)",
        capex_per_mw=7.0, opex_fix_per_mw=0.1, opex_var_per_mwh=10,
        build_time_years=1, lifespan_years=25, marginal_cost=10,
        base_cap_factor=0.11, is_variable=True
    ),
    "Kraftvarme": PowerTech(
        name="Kraftvärme/Bio",
        capex_per_mw=18.0, opex_fix_per_mw=0.4, opex_var_per_mwh=350,
        build_time_years=3, lifespan_years=35, marginal_cost=450,
        base_cap_factor=0.40, is_variable=False
    ),
    "Spetseffekt": PowerTech(
        name="Gas/Olja (Spets)",
        capex_per_mw=8.0, opex_fix_per_mw=0.15, opex_var_per_mwh=1200,
        build_time_years=2, lifespan_years=30, marginal_cost=2200,
        base_cap_factor=0.05, is_variable=False
    )
}

# Startflotta i Sverige (~2026 baseline)
START_FLEET = [
    PlantFleet("Vattenkraft", 16200, age=40),
    PlantFleet("Kärnkraft", 6900, age=35),
    PlantFleet("Vind_Land", 14500, age=8),
    PlantFleet("Vind_Hav", 200, age=10),
    PlantFleet("Solkraft", 3500, age=3),
    PlantFleet("Kraftvarme", 3800, age=20),
    PlantFleet("Spetseffekt", 2000, age=25),
]
