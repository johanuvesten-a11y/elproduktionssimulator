import sys
from engine import SimulationEngine
from config import TECH_CATALOG

def print_header(title: str):
    print("\n" + "=" * 60)
    print(f" {title.upper()} ".center(60, "="))
    print("=" * 60)

def main():
    sim = SimulationEngine()
    print_header("Sveriges Elproduktionssimulator")
    print("Välkommen! Du är energisystemansvarig för Sveriges elnät.")
    print("Målet är att bygga ut elnätet, möta den ökande efterfrågan och undvika elbrist.")

    while True:
        print_header(f"Status - År {sim.year}")
        print(f"Tillgänglig budget:  {sim.budget_msek:,.1f} MSEK")
        
        # Sammanställ nuvarande flotta
        tot_cap = sum(p.capacity_mw for p in sim.fleet)
        print(f"Total installerad effekt: {tot_cap:,.0f} MW")
        
        print("\nPågående investerings- & byggprojekt:")
        if not sim.construction_queue:
            print("  - inga aktiva byggen.")
        else:
            for c in sim.construction_queue:
                print(f"  • {c.capacity_mw:.0f} MW {c.tech_name} — {c.years_remaining} år kvar till färdigställande.")

        print("\nVALMÖJLIGHETER:")
        print(" [1] Visa teknikkatalog (Kalkyl & Priser)")
        print(" [2] Investera i ny kraftproduktion")
        print(" [3] Simulera nästa år (1 år framåt)")
        print(" [4] Avsluta simulatorn")

        choice = input("\nVälj handling (1-4): ").strip()

        if choice == "1":
            print_header("Teknikkatalog & Kostnadskalkyler")
            print(f"{'Kod':<12} {'Namn':<20} {'CAPEX (MSEK/MW)':<16} {'Byggtid':<10} {'Marginalkostnad':<15}")
            print("-" * 75)
            for key, t in TECH_CATALOG.items():
                print(f"{key:<12} {t.name:<20} {t.capex_per_mw:<16.1f} {t.build_time_years:<2} år       {t.marginal_cost:.0f} SEK/MWh")
            input("\nTryck Enter för att gå tillbaka...")

        elif choice == "2":
            print_header("Investera i ny kapactet")
            print("Tillgängliga nycklar:")
            for k in TECH_CATALOG.keys():
                print(f" - {k}")
            
            tech_key = input("\nAnge kod för kraftslag: ").strip()
            if tech_key not in TECH_CATALOG:
                print("⚠️ Ogiltig kod!")
                continue
                
            try:
                mw = float(input("Ange kapacitet att bygga (i MW): "))
                if mw <= 0:
                    print("⚠️ Kapacitet måste vara större än 0.")
                    continue
                success, msg = sim.start_construction(tech_key, mw)
                print(f"\n{ '✅' if success else '❌' } {msg}")
            except ValueError:
                print("⚠️ Vänligen ange ett giltigt tal.")
            input("\nTryck Enter för att fortsätta...")

        elif choice == "3":
            res = sim.run_year()
            print_header(f"Rapport för År {res['year']}")
            print(f"Efterfrågan:         {res['demand_twh']:.2f} TWh")
            print(f"Producerat:          {res['produced_twh']:.2f} TWh")
            print(f"Genomsnittligt elpris: {res['avg_price_sek']:.1f} SEK/MWh")
            print(f"Intäkter:            {res['revenue_msek']:,.1f} MSEK")
            print(f"Nettoresultat:       {res['net_profit_msek']:,.1f} MSEK")
            
            if res['blackout_hours'] > 0:
                print(f"🚨 VARNING: Nätet drabbades av {res['blackout_hours']} timmars effektbrist!")
            else:
                print("✅ Stabil elförsörjning upprätthölls hela året.")

            if res['retired_mw'] > 0:
                print(f"ℹ️ {res['retired_mw']:.0f} MW gammal anläggningskapacitet nådde sin livslängd och avvecklades.")
            
            input("\nTryck Enter för nästa år...")

        elif choice == "4":
            print("\nTack för att du spelade Sveriges Elproduktionssimulator!")
            sys.exit()

if __name__ == "__main__":
    main()
