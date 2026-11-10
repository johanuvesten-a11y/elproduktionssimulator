import streamlit as st
from engine import SimulationEngine
from config import TECH_CATALOG

# Sätt titel och layout
st.set_page_config(page_title="Sveriges Elsimulator", layout="wide")

st.title("⚡ Sveriges Elproduktionssimulator")
st.caption("Modellera Sveriges elförsörjning och investera i framtidens kraftslag.")

# Initalisera simulator och historik i sessionsminnet
if "sim" not in st.session_state:
    st.session_state.sim = SimulationEngine()
    st.session_state.history = []

sim = st.session_state.sim

# Sido-panel: Status & Ekonomi
st.sidebar.header(f"Status - År {sim.year}")
st.sidebar.metric("Tillgänglig Budget", f"{sim.budget_msek:,.1f} MSEK")

tot_cap = sum(p.capacity_mw for p in sim.fleet)
st.sidebar.metric("Totalt installerad effekt", f"{tot_cap:,.0f} MW")

st.sidebar.subheader("Pågående byggprojekt")
if not sim.construction_queue:
    st.sidebar.write("Inga aktiva byggen.")
else:
    for c in sim.construction_queue:
        st.sidebar.write(f"• **{c.capacity_mw:.0f} MW {c.tech_name}** ({c.years_remaining} år kvar)")

st.sidebar.divider()

# Knapp för att återställa spelet
if st.sidebar.button("🔄 Börja om spelet", type="secondary", use_container_width=True):
    st.session_state.sim = SimulationEngine()
    st.session_state.history = []
    st.rerun()

# Huvudområde: Flikar för Investering och Resultat
tab1, tab2 = st.tabs(["🏗️ Investera & Bygg", "📊 Simuleringsresultat"])

with tab1:
    st.header("Bygg nytt kraftslag")
    
    col1, col2 = st.columns(2)
    with col1:
        tech_choice = st.selectbox(
            "Välj kraftslag:",
            options=list(TECH_CATALOG.keys()),
            format_func=lambda x: TECH_CATALOG[x].name
        )
        tech_info = TECH_CATALOG[tech_choice]
        st.info(
            f"**Kostnad:** {tech_info.capex_per_mw:.1f} MSEK/MW  \n"
            f"**Byggtid:** {tech_info.build_time_years} år  \n"
            f"**Marginalkostnad:** {tech_info.marginal_cost:.0f} SEK/MWh"
        )

    with col2:
        capacity_input = st.number_input("Kapacitet att bygga (MW):", min_value=10, max_value=10000, value=500, step=50)
        total_cost = capacity_input * tech_info.capex_per_mw
        st.write(f"**Total investeringskostnad:** {total_cost:,.1f} MSEK")

        if st.button("Starta Bygge"):
            success, msg = sim.start_construction(tech_choice, capacity_input)
            if success:
                st.success(msg)
                st.rerun()
            else:
                st.error(msg)

    st.divider()
    if st.button("⏩ Simulera Nästa År (1 år framåt)", type="primary", use_container_width=True):
        res = sim.run_year()
        st.session_state.history.append(res)
        st.rerun()

with tab2:
    st.header("Historik & Årsrapporter")
    if not st.session_state.history:
        st.write("Klicka på 'Simulera Nästa År' för att starta första året.")
    else:
        latest = st.session_state.history[-1]
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Efterfrågan", f"{latest['demand_twh']:.1f} TWh")
        m2.metric("Produktion", f"{latest['produced_twh']:.1f} TWh")
        m3.metric("Snittpris", f"{latest['avg_price_sek']:.1f} SEK/MWh")
        m4.metric("Nettoresultat", f"{latest['net_profit_msek']:,.1f} MSEK")

        if latest['blackout_hours'] > 0:
            st.error(f"🚨 VARNING: {latest['blackout_hours']} timmars elbrist inträffade under året!")
        else:
            st.success("✅ Stabil elförsörjning hela året.")

        # Visa historisk tabell
        st.subheader("Alla simulerade år")
        st.dataframe(st.session_state.history)
