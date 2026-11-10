import streamlit as st
import pandas as pd
from engine import SimulationEngine
from config import TECH_CATALOG

# Konfigurera sidan
st.set_page_config(page_title="Sveriges Elsimulator", layout="wide", initial_sidebar_state="expanded")

# Initialisera simulator och historik i sessionsminnet
if "sim" not in st.session_state:
    st.session_state.sim = SimulationEngine()
    st.session_state.history = []

sim = st.session_state.sim

# ==============================================================================
# SIDOPANEL: Status & Snabbåtgärder
# ==============================================================================
st.sidebar.title("⚡ Elnätet i korthet")
st.sidebar.markdown(f"**Nuvarande år:** {sim.year}")

st.sidebar.metric("Tillgänglig Budget", f"{sim.budget_msek:,.1f} MSEK".replace(",", " "))

tot_cap = sum(p.capacity_mw for p in sim.fleet)
st.sidebar.metric("Total installerad effekt", f"{tot_cap:,.0f} MW".replace(",", " "))

st.sidebar.subheader("🏗️ Pågående byggprojekt")
if not sim.construction_queue:
    st.sidebar.info("Inga aktiva byggprojekt för tillfället.")
else:
    for c in sim.construction_queue:
        tech_name = TECH_CATALOG.get(c.tech_name, None)
        disp_name = tech_name.name if tech_name else c.tech_name
        st.sidebar.warning(f"• **{c.capacity_mw:,.0f} MW {disp_name}** ({c.years_remaining} år kvar)")

st.sidebar.divider()

if st.sidebar.button("🔄 Börja om spelet", type="secondary", use_container_width=True):
    st.session_state.sim = SimulationEngine()
    st.session_state.history = []
    st.rerun()

# ==============================================================================
# HUVUDOMRÅDE
# ==============================================================================
st.title("⚡ Sveriges Elproduktionssimulator")
st.caption("Modellera Sveriges elförsörjning, analysera kraftslag och investera strategiskt för att möta framtidens elbehov.")

tab1, tab2 = st.tabs(["🏗️ Översikt & Investering", "📊 Resultat & Historik"])

# ------------------------------------------------------------------------------
# FLIK 1: ÖVERSIKT & INVESTERING (FÖRSTASIDAN)
# ------------------------------------------------------------------------------
with tab1:
    # 1. Nuvarande Kapacitetsfördelning
    st.subheader("1. Nuvarande installerad kapacitet i elnätet")
    
    fleet_summary = {}
    for plant in sim.fleet:
        name = TECH_CATALOG[plant.tech_name].name
        fleet_summary[name] = fleet_summary.get(name, 0.0) + plant.capacity_mw
    
    cols = st.columns(len(fleet_summary))
    for idx, (tech_name, cap) in enumerate(fleet_summary.items()):
        cols[idx].metric(label=tech_name, value=f"{cap:,.0f} MW".replace(",", " "))
    
    st.divider()

    # 2. Teknikkatalog & Jämförelsetabell
    st.subheader("2. Jämförelse av alla kraftslag & Investeringskalkyl")
    
    catalog_data = []
    for key, t in TECH_CATALOG.items():
        catalog_data.append({
            "Kod": key,
            "Kraftslag": t.name,
            "Investering (MSEK/MW)": f"{t.capex_per_mw:.1f}",
            "Fast drift (MSEK/MW/år)": f"{t.opex_fix_per_mw:.2f}",
            "Byggtid (år)": t.build_time_years,
            "Livslängd (år)": t.lifespan_years,
            "Marginalkostnad (SEK/MWh)": f"{t.marginal_cost:.0f}",
            "Kapacitetsfaktor": f"{t.base_cap_factor*100:.0f}%",
            "Väderberoende": "Ja" if t.is_variable else "Nej"
        })
    
    st.dataframe(pd.DataFrame(catalog_data), use_container_width=True, hide_index=True)
    
    st.divider()

    # 3. Investeringsformulär
    st.subheader("3. Bygg ny produktionskapacitet")
    col_inv1, col_inv2 = st.columns(2)
    
    with col_inv1:
        tech_choice = st.selectbox(
            "Välj kraftslag att bygga:",
            options=list(TECH_CATALOG.keys()),
            format_func=lambda x: TECH_CATALOG[x].name
        )
        tech_info = TECH_CATALOG[tech_choice]
        
        st.info(
            f"**Teknikfakta ({tech_info.name}):**  \n"
            f"• **Investeringskostnad:** {tech_info.capex_per_mw:.1f} MSEK / MW  \n"
            f"• **Byggtid:** {tech_info.build_time_years} år  \n"
            f"• **Marginalkostnad:** {tech_info.marginal_cost:.0f} SEK / MWh  \n"
            f"• **Kapacitetsutnyttjande:** {tech_info.base_cap_factor*100:.0f}%"
        )

    with col_inv2:
        capacity_input = st.number_input(
            "Ange kapacitet att bygga (MW):",
            min_value=50,
            max_value=20000,
            value=500,
            step=50
        )
        total_cost = capacity_input * tech_info.capex_per_mw
        st.metric("Beräknad total investeringskostnad", f"{total_cost:,.1f} MSEK".replace(",", " "))

        if st.button("🔨 Starta Byggprojekt", type="primary", use_container_width=True):
            success, msg = sim.start_construction(tech_choice, capacity_input)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    
    # Kör simulering
    st.subheader("4. Kör simulering")
    if st.button("⏩ Simulera
