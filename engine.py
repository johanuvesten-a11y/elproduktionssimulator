import random
from typing import List, Dict, Tuple
from models import PlantFleet, ConstructionProject
from config import TECH_CATALOG, START_FLEET

class SimulationEngine:
    def __init__(self):
        self.year = 2026
        self.budget_msek = 45000.0  # Investeringskapital (MSEK)
        self.fleet: List[PlantFleet] = list(START_FLEET)
        self.construction_queue: List[ConstructionProject] = []
        self.base_annual_demand_twh = 140.0  # Sveriges basbehov
        self.demand_growth_rate = 0.025      # 2.5% årlig ökning p.g.a. elektrifiering

    def run_year(self) -> Dict:
        # 1. Årlig tillväxt i efterfrågan
        annual_demand_twh = self.base_annual_demand_twh * ((1 + self.demand_growth_rate) ** (self.year - 2026))
        
        # 2. Uppdatera pågående byggprojekt (tidsaspekt)
        finished_projects = []
        for proj in self.construction_queue:
            proj.years_remaining -= 1
            if proj.years_remaining <= 0:
                finished_projects.append(proj)
                self.fleet.append(PlantFleet(proj.tech_name, proj.capacity_mw, age=0))
        
        for p in finished_projects:
            self.construction_queue.remove(p)

        # 3. Åldring & avveckling
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

        # 4. Kör 12 månaders elproduktion & prissättning
        total_produced_twh = 0.0
        total_revenue_msek = 0.0
        total_var_opex_msek = 0.0
        blackout_hours = 0
        monthly_prices = []

        # Säsongsprofiler (Månad 1..12)
        # Efterfrågekoefficienter (vinter hög, sommar låg)
        demand_weights = [1.3, 1.25, 1.1, 0.9, 0.8, 0.7, 0.65, 0.75, 0.95, 1.1, 1.2, 1.3]
        # Väderfaktorer
        wind_factors = [1.2, 1.1, 1.0, 0.8, 0.7, 0.6, 0.6, 0.7, 0.9, 1.1, 1.2, 1.25]
        sun_factors =  [0.1, 0.3, 0.7, 1.1, 1.4, 1.6, 1.5, 1.2, 0.8, 0.4, 0.1, 0.05]

        for m in range(12):
            m_demand_mwh = (annual_demand_twh * 1e6 / 12) * demand_weights[m]
            
            # Beräkna tillgänglig kapacitet per kraftslag för månaden
            avail_cap = {}
            for plant in self.fleet:
                tech = TECH_CATALOG[plant.tech_name]
                cf = tech.base_cap_factor
                if plant.tech_name in ["Vind_Land", "Vind_Hav"]:
                    cf *= wind_factors[m] * random.uniform(0.85, 1.15)
                elif plant.tech_name == "Solkraft":
                    cf *= sun_factors[m] * random.uniform(0.9, 1.1)
                
                avail_cap[plant.tech_name] = avail_cap.get(plant.tech_name, 0.0) + (plant.capacity_mw * cf)

            # Merit Order-sortering efter marginalkostnad
            sorted_techs = sorted(TECH_CATALOG.values(), key=lambda x: x.marginal_cost)
            
            hours_in_month = 730
            m_produced_mwh = 0.0
            m_needed_mwh = m_demand_mwh
            m_spot_price = 50.0 # Minsta pris SEK/MWh

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

                # Rörliga driftkostnader
                total_var_opex_msek += (dispatch_mwh * tech.opex_var_per_mwh) / 1e6

            # Om produktionen inte täcker behovet drabbas nätet av effektbrist
            if m_needed_mwh > 0:
                blackout_hours += int((m_needed_mwh / (m_demand_mwh / hours_in_month)))
                m_spot_price = 3000.0 # Maxpriskoppling vid brist

            monthly_prices.append(m_spot_price)
            total_produced_twh += m_produced_mwh / 1e6
            total_revenue_msek += (m_produced_mwh * m_spot_price) / 1e6

        # 5. Fasta driftkostnader för alla anläggningar
        total_fix_opex_msek = sum(
            plant.capacity_mw * TECH_CATALOG[plant.tech_name].opex_fix_per_mw 
            for plant in self.fleet
        )

        avg_price = sum(monthly_prices) / 12
        net_profit_msek = total_revenue_msek - (total_var_opex_msek + total_fix_opex_msek)
        
        # Uppdatera spelarbudget
        self.budget_msek += net_profit_msek
        self.year += 1

        return {
            "year": self.year - 1,
            "demand_twh": annual_demand_twh,
            "produced_twh": total_produced_twh,
            "avg_price_sek": avg_price,
            "revenue_msek": total_revenue_msek,
            "net_profit_msek": net_profit_msek,
            "blackout_hours": blackout_hours,
            "retired_mw": retired_capacity,
            "budget_msek": self.budget_msek
        }

    def start_construction(self, tech_key: str, capacity_mw: float) -> Tuple[bool, str]:
        tech = TECH_CATALOG.get(tech_key)
        if not tech:
            return False, "Okänt kraftslag."

        cost = capacity_mw * tech.capex_per_mw
        if cost > self.budget_msek:
            return False, f"Otillräcklig budget. Kräver {cost:,.1f} MSEK (Du har {self.budget_msek:,.1f} MSEK)."

        self.budget_msek -= cost
        self.construction_queue.append(
            ConstructionProject(
                tech_name=tech_key,
                capacity_mw=capacity_mw,
                years_remaining=tech.build_time_years,
                total_capex=cost
            )
        )
        return True, f"Bygge startat! {capacity_mw} MW {tech.name}. Klart om {tech.build_time_years} år. Kostnad: {cost:,.1f} MSEK."
