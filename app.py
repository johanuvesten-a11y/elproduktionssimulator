import streamlit as st
import pandas as pd
from engine import SimulationEngine
from config import TECH_CATALOG

# Konfigurera sidan med bred layout
st.set_page_config(page_title="Sveriges Elsimulator", layout="wide", initial_sidebar_state="expanded")

# Initialisera simulator och historik i sessionsminnet
if "sim" not in st.session_state:
    st.session_state.sim = SimulationEngine()
    st.session_state.history = []

sim = st.session_state.sim

# ==============================================================================
# SIDOPANEL: Status & Huvudknappar (Alltid synliga utan scroll)
# ==============================================================================
st.sidebar.title("⚡ Elnätet i korthet")
st.sidebar.markdown(f"**Nuvarande år:** {sim.year}")

st.sidebar.metric("Tillgänglig Budget", f"{sim.budget_msek:,.1f} MSEK".replace(",", " "))

tot_cap = sum(p.capacity_mw for p in sim.fleet)
st.sidebar.metric("Installerad effekt", f"{tot_cap:,.0f} MW".replace(",", " "))

# Huvudåtgärd: Kör nästa år
st.sidebar.divider()
if st.sidebar.button("⏩ Simulera nästa år (1 år)", type="primary", use_container_width=True):
    res = sim.run_year()
    st.session_state.history.append(res)
    st.rerun()

st.sidebar.subheader("🏗️ Pågående byggprojekt")
if not sim.construction_queue:
    st.sidebar.info("Inga aktiva byggen.")
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
# HUVUDOMRÅDE - DASHBOARD LAYOUT
# ==============================================================================
st.title("⚡ Sveriges Elproduktionssimulator")

tab1, tab2 = st.tabs(["🎮 Manöverrum & Investering", "📊 Resultat & Historik"])

# ------------------------------------------------------------------------------
# FLIK 1: MANÖVERRUM (KOMPAKT 2-KOLUMNS-LAYOUT)
# ------------------------------------------------------------------------------
with tab1:
    col_left, col_right = st.columns([1, 1], gap="medium")
    
    # --------------------------------------------------------------------------
    # VÄNSTER KOLUMN: Nuvarande status & Elmix
    # --------------------------------------------------------------------------
    with col_left:
        st.subheader("1. Nuvarande Elmix & Kapacitet")
        
        fleet_summary = {}
        for plant in sim.fleet:
            name = TECH_CATALOG[plant.tech_name].name
            fleet_summary[name] = fleet_summary.get(name, 0.0) + plant.capacity_mw
            
        df_cap = pd.DataFrame(list(fleet_summary.items()), columns=["Kraftslag", "Kapacitet (MW)"])
        
        # Kompakt stapeldiagram
        st.bar_chart(df_cap.set_index("Kraftslag"), height=200)

        # Hopfällbar detaljerad teknikkatalog
        with st.expander("ℹ️ Visa alla kraftslag & Investeringskalkyl"):
            catalog_list = []
            for key, t in TECH_CATALOG.items():
                installed = sim.get_installed_capacity(key)
                catalog_list.append({
                    "Kraftslag": t.name,
                    "Nu/Max": f"{installed:,.0f}/{t.max_capacity_mw:,.0f} MW".replace(",", " "),
                    "Investering": t.capex_per_mw,
                    "Byggtid": t.build_time_years,
                    "Marginalkostnad": t.marginal_cost,
                    "Kapacitetsfaktor": t.base_cap_factor,
                })
            
            df_cat = pd.DataFrame(catalog_list)
            st.dataframe(
                df_cat,
                use_container_width=True,
                hide_index=True,
                column_config={
                    "Investering": st.column_config.NumberColumn("MSEK/MW", format="%.1f"),
                    "Byggtid": st.column_config.NumberColumn("Byggtid", format="%d år"),
                    "Marginalkostnad": st.column_config.NumberColumn("SEK/MWh", format="%.0f"),
                    "Kapacitetsfaktor": st.column_config.ProgressColumn("Utnyttjande", format="%.0f%%", min_value=0.0, max_value=1.0),
                }
            )

    # --------------------------------------------------------------------------
    # HÖGER KOLUMN: Investera och Renovera
    # --------------------------------------------------------------------------
    with col_right:
        st.subheader("2. Åtgärder & Investeringar")
        
        inv_tab1, inv_tab2 = st.tabs(["🏗️ Bygg nytt", "🔧 Renovera"])
        
        with inv_tab1:
            tech_choice = st.selectbox(
                "Välj kraftslag att bygga:",
                options=list(TECH_CATALOG.keys()),
                format_func=lambda x: TECH_CATALOG[x].name,
                key="build_select"
            )
            tech_info = TECH_CATALOG[tech_choice]
            curr_cap = sim.get_installed_capacity(tech_choice)
            
            st.caption(
                f"**{tech_info.name}:** Max-tak {curr_cap:,.0f}/{tech_info.max_capacity_mw:,.0f} MW | "
                f"Pris {tech_info.capex_per_mw:.1f} MSEK/MW | Byggtid {tech_info.build_time_years} år"
            )

            capacity_input = st.number_input(
                "Kapacitet (MW):",
                min_value=50, max_value=20000, value=500, step=50, key="build_mw"
            )
            total_cost = capacity_input * tech_info.capex_per_mw
            st.markdown(f"**Total kostnad:** `{total_cost:,.1f} MSEK`".replace(",", " "))

            if st.button("🔨 Starta Nybyggnation", type="primary", use_container_width=True):
                success, msg = sim.start_construction(tech_choice, capacity_input)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

        with inv_tab2:
            ren_choice = st.selectbox(
                "Välj kraftslag att renovera:",
                options=list(TECH_CATALOG.keys()),
                format_func=lambda x: TECH_CATALOG[x].name,
                key="ren_select"
            )
            ren_info = TECH_CATALOG[ren_choice]
            old_plants = [p for p in sim.fleet if p.tech_name == ren_choice and p.age >= int(ren_info.lifespan_years * 0.4)]
            avail_ren_mw = sum(p.capacity_mw for p in old_plants)
            
            ren_capex = ren_info.capex_per_mw * 0.35
            ren_time = max(1, ren_info.build_time_years // 2)

            st.caption(
                f"**Tillgängligt för renovering:** {avail_ren_mw:,.0f} MW | "
                f"Kostnad {ren_capex:.1f} MSEK/MW | Tid {ren_time} år"
            )

            ren_capacity_input = st.number_input(
                "Renovera volym (MW):",
                min_value=50, max_value=max(50, int(avail_ren_mw)), value=min(500, max(50, int(avail_ren_mw))), step=50, key="ren_mw"
            )
            total_ren_cost = ren_capacity_input * ren_capex
            st.markdown(f"**Total kostnad:** `{total_ren_cost:,.1f} MSEK`".replace(",", " "))

            if st.button("🔧 Starta Renovering", type="primary", use_container_width=True):
                success, msg = sim.renovate_fleet(ren_choice, ren_capacity_input)
                if success:
                    st.success(msg)
                    st.rerun()
                else:
                    st.error(msg)

# ------------------------------------------------------------------------------
# FLIK 2: RESULTAT & HISTORIK
# ------------------------------------------------------------------------------
with tab2:
    if not st.session_state.history:
        st.info("Ingen simulering har körts än. Klicka på **Simulera nästa år** i sidopanelen till vänster.")
    else:
        latest = st.session_state.history[-1]
        
        st.subheader(f"Årsrapport År {latest['year']}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Elbehov", f"{latest['demand_twh']:.1f} TWh")
        m2.metric("Produktion", f"{latest['produced_twh']:.1f} TWh")
        m3.metric("Medelpris", f"{latest['avg_price_sek']:.1f} SEK/MWh")
        m4.metric("Nettoresultat", f"{latest['net_profit_msek']:,.1f} MSEK".replace(",", " "))

        if latest['blackout_hours'] > 0:
            st.error(f"🚨 **Varning:** {latest['blackout_hours']} timmars effektbrist inträffade under året!")
        else:
            st.success("✅ **Stabil elförsörjning:** Inga timmar med effektbrist.")

        if latest['retired_mw'] > 0:
            st.warning(f"ℹ️ **Avveckling:** {latest['retired_mw']:,.0f} MW nådde sin livslängd och avvecklades.".replace(",", " "))

        st.divider()
        
        # Historisk tabell
        st.subheader("📜 Historisk årsöversikt")
        df_history = pd.DataFrame(st.session_state.history)
        
        column_mapping = {
            "year": "År",
            "demand_twh": "Elbehov (TWh)",
            "produced_twh": "Produktion (TWh)",
            "avg_price_sek": "Medelpris (SEK/MWh)",
            "revenue_msek": "Intäkter (MSEK)",
            "net_profit_msek": "Nettoresultat (MSEK)",
            "blackout_hours": "Effektbrist (timmar)",
            "retired_mw": "Avvecklad effekt (MW)",
            "budget_msek": "Budget (MSEK)"
        }
        
        df_display = df_history.rename(columns=column_mapping)
        st.dataframe(df_display, use_container_width=True, hide_index=True)

        st.divider()
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("**Elprisutveckling (SEK/MWh)**")
            st.line_chart(df_display.set_index("År")[["Medelpris (SEK/MWh)"]])
        with chart_col2:
            st.markdown("**Produktion vs Elbehov (TWh)**")
            st.line_chart(df_display.set_index("År")[["Elbehov (TWh)", "Produktion (TWh)"]])
