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
    
    # 4. Kör simulering
    st.subheader("4. Kör simulering")
    if st.button("⏩ Simulera nästa år (1 år framåt)", type="primary", use_container_width=True):
        res = sim.run_year()
        st.session_state.history.append(res)
        st.rerun()

# ------------------------------------------------------------------------------
# FLIK 2: RESULTAT, EKONOMI & HISTORIK
# ------------------------------------------------------------------------------
with tab2:
    st.header("📊 Resultat, Ekonomi & Historik")
    
    if not st.session_state.history:
        st.info("Ingen simulering har körts än. Gå till fliken **Översikt & Investering** och klicka på **Simulera nästa år**.")
    else:
        latest = st.session_state.history[-1]
        
        st.subheader(f"Årsrapport för År {latest['year']}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Elbehov", f"{latest['demand_twh']:.1f} TWh")
        m2.metric("Produktion", f"{latest['produced_twh']:.1f} TWh")
        m3.metric("Medelpris", f"{latest['avg_price_sek']:.1f} SEK/MWh")
        m4.metric("Nettoresultat", f"{latest['net_profit_msek']:,.1f} MSEK".replace(",", " "))

        if latest['blackout_hours'] > 0:
            st.error(f"🚨 **Varning:** Nätet drabbades av **{latest['blackout_hours']} timmars effektbrist** under året!")
        else:
            st.success("✅ **Stabil elförsörjning:** Inga timmar med effektbrist uppstod.")

        if latest['retired_mw'] > 0:
            st.warning(f"ℹ️ **Avveckling:** {latest['retired_mw']:,.0f} MW anläggningar nådde sin livslängd och togs ur bruk.".replace(",", " "))

        st.divider()
        
        # Snygg historisk tabell med svenska rubriker och enhetsformatering
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
            "budget_msek": "Kvarvarande budget (MSEK)"
        }
        
        df_display = df_history.rename(columns=column_mapping)
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True,
            column_config={
                "År": st.column_config.NumberColumn("År", format="%d"),
                "Elbehov (TWh)": st.column_config.NumberColumn("Elbehov", format="%.2f TWh"),
                "Produktion (TWh)": st.column_config.NumberColumn("Produktion", format="%.2f TWh"),
                "Medelpris (SEK/MWh)": st.column_config.NumberColumn("Medelpris", format="%.1f SEK"),
                "Intäkter (MSEK)": st.column_config.NumberColumn("Intäkter", format="%,.1f MSEK"),
                "Nettoresultat (MSEK)": st.column_config.NumberColumn("Nettoresultat", format="%,.1f MSEK"),
                "Effektbrist (timmar)": st.column_config.NumberColumn("Effektbrist", format="%d tim"),
                "Avvecklad effekt (MW)": st.column_config.NumberColumn("Avvecklat", format="%,.0f MW"),
                "Kvarvarande budget (MSEK)": st.column_config.NumberColumn("Budget", format="%,.1f MSEK"),
            }
        )

        st.divider()
        st.subheader("📈 Trendanalys över tid")
        
        chart_col1, chart_col2 = st.columns(2)
        with chart_col1:
            st.markdown("**Elprisutveckling (SEK/MWh)**")
            st.line_chart(df_display.set_index("År")[["Medelpris (SEK/MWh)"]])
            
        with chart_col2:
            st.markdown("**Produktion vs Elbehov (TWh)**")
            st.line_chart(df_display.set_index("År")[["Elbehov (TWh)", "Produktion (TWh)"]])
