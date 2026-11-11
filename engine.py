import random
from typing import List, Dict, Tuple
from models import PlantFleet, ConstructionProject
from config import TECH_CATALOG, START_FLEET

class SimulationEngine:
    def __init__(self):
        self.year = 2026
        self.budget_msek = 45000.0
        self.fleet: List[PlantFleet] = [PlantFleet(p.tech_name, p.capacity_mw, p.age) for p in START_FLEET]
        self.construction_queue: List[ConstructionProject] = []
        self.base_annual_demand_twh = 140.0
        self.demand_growth_rate = 0.025  # Startar på 2.5 % per år
        self.max_import_mw = 8000.0       # Max utlandskapacitet
        self.efficiency_level = 0

    def get_installed_capacity(self, tech_key: str) -> float:
        fleet_cap = sum(p.capacity_mw for p in self.fleet if p.tech_name == tech_key)
        building_cap = sum(c.capacity_mw for c in self.construction_queue if c.tech_name == tech_key and not c.is_refurbishment)
        return fleet_cap + building_cap

    def start_construction(self, tech_key: str, capacity_mw: float) -> Tuple[bool, str]:
        tech = TECH_CATALOG.get(tech_key)
        if not tech:
            return False, "Okänt kraftslag."

        current_cap = self.get_installed_capacity(tech_key)
        if current_cap + capacity_mw > tech.max_capacity_mw:
            remaining_mw = max(0.0, tech.max_capacity_mw - current_cap)
            return False, (
                f"Kapacitetstaket nått! {tech.name} har ett max-tak på {tech.max_capacity_mw:,.0f} MW i Sverige. "
                f"Du kan maximalt bygga {remaining_mw:,.0f} MW till."
            )

        cost = capacity_mw * tech.capex_per_mw
        if cost > self.budget_msek:
            return False, f"Otillräcklig budget. Kräver {cost:,.1f} MSEK (Du har {self.budget_msek:,.1f} MSEK)."

        self.budget_msek -= cost
        self.construction_queue.append(
            ConstructionProject(
                tech_name=tech_key,
                capacity_mw=capacity_mw,
                years_remaining=tech.build_time_years,
                total_capex=cost,
                is_refurbishment=False
            )
        )
        return True, f"Bygge startat! {capacity_mw:,.0f} MW {tech.name}. Klart om {tech.build_time_years} år. Kostnad: {cost:,.1f} MSEK."

    def renovate_fleet(self, tech_key: str, capacity_mw: float) -> Tuple[bool, str]:
        tech = TECH_CATALOG.get(tech_key)
        if not tech:
            return False, "Okänt kraftslag."

        old_plants = [p for p in self.fleet if p.tech_name == tech_key and p.age >= int(tech.lifespan_years * 0.4)]
        available_mw = sum(p.capacity_mw for p in old_plants)

        if capacity_mw > available_mw:
            return False, f"Det finns bara {available_mw:,.0f} MW äldre {tech.name} tillgängligt att renovera."

        cost = capacity_mw * (tech.capex_per_mw * 0.35)
        if cost > self.budget_msek:
            return False, f"Otillräcklig budget för renovering. Kräver {cost:,.1f} MSEK."

        build_time = max(1, tech.build_time_years // 2)

        self.budget_msek -= cost
        self.construction_queue.append(
            ConstructionProject(
                tech_name=tech_key,
                capacity_mw=capacity_mw,
                years_remaining=build_time,
                total_capex=cost,
                is_refurbishment=True
            )
        )
        return True, f"Renovering startad! {capacity_mw:,.0f} MW {tech.name}. Klart om {build_time} år. Kostnad: {cost:,.1f} MSEK."

    def invest_efficiency(self) -> Tuple[bool, str]:
        cost = 4000.0
        if self.budget_msek < cost:
            return False, f"Otillräcklig budget för energieffektivisering ({cost:,.0f} MSEK krävs)."
        if self.demand_growth_rate <= 0.005:
            return False, "Maximal energieffektivisering uppnådd (0,5 % lägsta tillväxt)."

        self.budget_msek -= cost
        self.demand_growth_rate = max(0.005, self.demand_growth_rate - 0.003)
        self.efficiency_level += 1
        return True, f"Energieffektivisering genomförd! Årlig efterfrågetillväxt sänkt till {self.demand_growth_rate * 100:.1f} %."

    def run_year(self) -> Dict:
        annual_demand_twh = self.base_annual_demand_twh * ((1 + self.demand_growth_rate) ** (self.year - 2026))

        # Uppdatera bygg- och renoveringsprojekt
        finished_projects = []
        for proj in self.construction_queue:
            proj.years_remaining -= 1
            if proj.years_remaining <= 0:
                finished_projects.append(proj)
                if proj.is_refurbishment:
                    renovated_remaining = proj.capacity_mw
                    for plant in sorted(self.fleet, key=lambda x: x.age, reverse=True):
                        if plant.tech_name == proj.tech_name and renovated_remaining > 0:
                            take_mw = min(plant.capacity_mw, renovated_remaining)
                            plant.age = 0
                            renovated_remaining -= take_mw
                else:
                    self.fleet.append(PlantFleet(proj.tech_name, proj.capacity_mw, age=0))

        for p in finished_projects:
            self.construction_queue.remove(p)

        # Åldring & avveckling
        retired_capacity = 0.0
        active_fleet = []
        for plant in self.fleet:
            plant.age += 1
            tech = TECH_CATALOG[plant.tech_name]
            if plant.age > tech.lifespan_years:
                retired_capacity += plant.capacity_mw
            else:
                active_fleet.append(plant)
        self.fleet = active_fleet

        # Kör 12 månaders elproduktion
        total_produced_twh = 0.0
        total_imported_twh = 0.0
        total_revenue_msek = 0.0
        total_var_opex_msek = 0.0
        blackout_hours = 0
        monthly_prices = []

        demand_weights = [1.3, 1.25, 1.1, 0.9, 0.8, 0.7, 0.65, 0.75, 0.95, 1.1, 1.2, 1.3]
        wind_factors = [1.2, 1.1, 1.0, 0.8, 0.7, 0.6, 0.6, 0.7, 0.9, 1.1, 1.2, 1.25]
        sun_factors =  [0.1, 0.3, 0.7, 1.1, 1.4, 1.6, 1.5, 1.2, 0.8, 0.4, 0.1, 0.05]

        for m in range(12):
            m_demand_mwh = (annual_demand_twh * 1e6 / 12) * demand_weights[m]
            
            avail_cap = {}
            for plant in self.fleet:
                tech = TECH_CATALOG[plant.tech_name]
                cf = tech.base_cap_factor
                if plant.tech_name in ["Vind_Land", "Vind_Hav"]:
                    cf *= wind_factors[m] * random.uniform(0.85, 1.15)
                elif plant.tech_name == "Solkraft":
                    cf *= sun_factors[m] * random.uniform(0.9, 1.1)
                
                avail_cap[plant.tech_name] = avail_cap.get(plant.tech_name, 0.0) + (plant.capacity_mw * cf)

            sorted_techs = sorted(TECH_CATALOG.values(), key=lambda x: x.marginal_cost)
            
            hours_in_month = 730
            m_produced_mwh = 0.0
            m_needed_mwh = m_demand_mwh
            m_spot_price = 50.0

            for tech in sorted_techs:
                if m_needed_mwh <= 0:
                    break
                cap_mw = avail_cap.get(tech.name, 0.0)
                max_potential_mwh = cap_mw * hours_in_month
                
                dispatch_mwh = min(m_needed_mwh, max_potential_mwh)
                m_produced_mwh += dispatch_mwh
                m_needed_mwh -= dispatch_mwh
                
                if dispatch_mwh > 0:
                    m_spot_price = tech.marginal_cost

                total_var_opex_msek += (dispatch_mwh * tech.opex_var_per_mwh) / 1e6

            # Elimport vid inhemskt underskott (upp till 8 000 MW till 1 500 SEK/MWh)
            if m_needed_mwh > 0:
                max_import_mwh = self.max_import_mw * hours_in_month
                import_mwh = min(m_needed_mwh, max_import_mwh)
                m_needed_mwh -= import_mwh
                total_imported_twh += import_mwh / 1e6
                m_spot_price = max(m_spot_price, 1500.0)
                total_var_opex_msek += (import_mwh * 1500.0) / 1e6

            # Om underskott kvarstår efter max import -> Effektbrist
            if m_needed_mwh > 0:
                blackout_hours += int((m_needed_mwh / (m_demand_mwh / hours_in_month)))
                m_spot_price = 3000.0

            monthly_prices.append(m_spot_price)
            total_produced_twh += m_produced_mwh / 1e6
            total_revenue_msek += (m_produced_mwh * m_spot_price) / 1e6

        total_fix_opex_msek = sum(
            plant.capacity_mw * TECH_CATALOG[plant.tech_name].opex_fix_per_mw 
            for plant in self.fleet
        )

        avg_price = sum(monthly_prices) / 12
        net_profit_msek = total_revenue_msek - (total_var_opex_msek + total_fix_opex_msek)
        
        self.budget_msek += net_profit_msek
        self.year += 1

        return {
            "year": self.year - 1,
            "demand_twh": annual_demand_twh,
            "produced_twh": total_produced_twh,
            "imported_twh": total_imported_twh,
            "avg_price_sek": avg_price,
            "revenue_msek": total_revenue_msek,
            "net_profit_msek": net_profit_msek,
            "blackout_hours": blackout_hours,
            "retired_mw": retired_capacity,
            "budget_msek": self.budget_msek,
            "growth_rate": self.demand_growth_rate
        }
