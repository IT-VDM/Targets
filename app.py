
import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

st.set_page_config(
    page_title="Target Verdeling & Commissie Tool",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# Basisdata Marcel
# -----------------------------
MONTHS = ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]

SALES_2025 = {
    "Jan": 6517.94,
    "Feb": 8571.23,
    "Mrt": 10415.83,
    "Apr": 15303.62,
    "Mei": 16938.59,
    "Jun": 15672.52,
    "Jul": 44562.66,
    "Aug": 24336.74,
    "Sep": 31857.59,
    "Okt": 30409.29,
    "Nov": 33193.43,
    "Dec": 37378.83,
}

ACTUAL_2026 = {
    "Jan": 47749.00,
    "Feb": 31948.23,
    "Mrt": 42226.93,
    "Apr": 41337.31,
    "Mei": 14608.85,
    "Jun": 0.0,
    "Jul": 0.0,
    "Aug": 0.0,
    "Sep": 0.0,
    "Okt": 0.0,
    "Nov": 0.0,
    "Dec": 0.0,
}

QUARTERS = {
    "Q1": ["Jan", "Feb", "Mrt"],
    "Q2": ["Apr", "Mei", "Jun"],
    "Q3": ["Jul", "Aug", "Sep"],
    "Q4": ["Okt", "Nov", "Dec"],
}

# -----------------------------
# Helpers
# -----------------------------
def eur(value):
    return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def eur0(value):
    return f"€ {value:,.0f}".replace(",", ".")

def pct(value):
    return f"{value:.2f}%".replace(".", ",")

def input_key(month):
    return f"target_input_{month}"

def init_targets_by_2025_season(annual_target):
    previous_total = sum(SALES_2025.values())
    factor = annual_target / previous_total if previous_total else 1
    return {m: SALES_2025[m] * factor for m in MONTHS}

def init_targets_equal(annual_target):
    monthly_target = annual_target / 12 if annual_target else 0
    return {m: monthly_target for m in MONTHS}

def normalize_targets_to_total(targets, annual_target):
    current_total = sum(targets.values())
    if current_total <= 0:
        return init_targets_equal(annual_target)
    factor = annual_target / current_total
    return {m: targets[m] * factor for m in MONTHS}

def apply_targets(new_targets):
    """
    Belangrijk:
    Streamlit number_input widgets bewaren hun eigen waarde in session_state.
    Daarom moeten we zowel st.session_state.targets als de widget-keys bijwerken,
    vóór de widgets opnieuw worden getekend.
    """
    st.session_state.targets = {m: float(new_targets[m]) for m in MONTHS}
    for m in MONTHS:
        st.session_state[input_key(m)] = float(round(new_targets[m], 2))

def build_detail_df(targets):
    return pd.DataFrame({
        "Maand": MONTHS,
        "Omzet 2025": [SALES_2025[m] for m in MONTHS],
        "Target 2026": [targets[m] for m in MONTHS],
        "Werkelijke omzet 2026": [ACTUAL_2026[m] for m in MONTHS],
    })

# -----------------------------
# Header
# -----------------------------
st.title("Target Verdeling & Commissie Tool")
st.caption("Eenvoudige tool om de jaartarget te verdelen, kwartaaldoelen te controleren en commissie te simuleren.")

# -----------------------------
# 1. Instellingen
# -----------------------------
st.subheader("1. Instellingen")

total_2025 = sum(SALES_2025.values())

c1, c2, c3, c4 = st.columns(4)

with c1:
    st.metric("Omzet 2025", eur0(total_2025))

with c2:
    growth_pct = st.number_input(
        "Groei t.o.v. 2025",
        min_value=0.0,
        max_value=200.0,
        value=45.0,
        step=1.0,
        format="%.2f",
        help="De gewenste groei op jaarbasis. De jaartarget wordt hiermee automatisch berekend."
    )

annual_target = total_2025 * (1 + growth_pct / 100)

with c3:
    st.metric("Jaartarget 2026", eur0(annual_target))

with c4:
    commission_pct = st.number_input(
        "Commissiepercentage",
        min_value=0.0,
        max_value=50.0,
        value=2.0,
        step=0.25,
        format="%.2f",
        help="Commissie wordt enkel berekend op omzet boven het kwartaaltarget."
    )

st.info(
    "Commissieformule: **commissie per kwartaal = max(0, werkelijke kwartaalomzet − kwartaaltarget) × commissiepercentage**."
)

# -----------------------------
# Session state initialisatie
# -----------------------------
if "targets" not in st.session_state:
    apply_targets(init_targets_by_2025_season(annual_target))

if "last_annual_target" not in st.session_state:
    st.session_state.last_annual_target = annual_target

# Wanneer groeipercentage wijzigt, behoud de maandverhouding maar pas totaal aan.
if abs(st.session_state.last_annual_target - annual_target) > 0.01:
    new_targets = normalize_targets_to_total(st.session_state.targets, annual_target)
    apply_targets(new_targets)
    st.session_state.last_annual_target = annual_target
    st.rerun()

# Zorg dat alle input-keys bestaan.
for m in MONTHS:
    if input_key(m) not in st.session_state:
        st.session_state[input_key(m)] = float(round(st.session_state.targets[m], 2))

# -----------------------------
# 2. Verdeling kiezen
# -----------------------------
st.subheader("2. Verdeling kiezen")

st.write("Kies eerst een startverdeling. Nadien kan je de maandtargets manueel aanpassen.")

b1, b2, b3 = st.columns(3)

with b1:
    if st.button("Verdeel volgens 2025-seizoen", use_container_width=True):
        apply_targets(init_targets_by_2025_season(annual_target))
        st.rerun()

with b2:
    if st.button("Verdeel gelijk over 12 maanden", use_container_width=True):
        apply_targets(init_targets_equal(annual_target))
        st.rerun()

with b3:
    if st.button("Maak totaal passend", use_container_width=True):
        current_targets = {m: float(st.session_state[input_key(m)]) for m in MONTHS}
        apply_targets(normalize_targets_to_total(current_targets, annual_target))
        st.rerun()

st.caption("**Maak totaal passend** behoudt de huidige verhouding tussen de maanden, maar zorgt dat de som exact gelijk is aan de jaartarget.")

# -----------------------------
# 3. Maandtargets
# -----------------------------
st.subheader("3. Maandtargets aanpassen")

cols = st.columns(4)
for idx, month in enumerate(MONTHS):
    with cols[idx % 4]:
        st.number_input(
            month,
            min_value=0.0,
            step=500.0,
            format="%.2f",
            key=input_key(month)
        )

# Synchroniseer inputvelden terug naar targets.
st.session_state.targets = {m: float(st.session_state[input_key(m)]) for m in MONTHS}

target_total = sum(st.session_state.targets.values())
amount_to_distribute = annual_target - target_total

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Som maandtargets", eur0(target_total))
with m2:
    st.metric("Te verdelen targetbedrag", eur0(amount_to_distribute))
with m3:
    if abs(amount_to_distribute) <= 1:
        st.success("Totaal klopt.")
    else:
        st.warning("Totaal wijkt af. Klik op ‘Maak totaal passend’.")

# -----------------------------
# 4. Maandoverzicht
# -----------------------------
st.subheader("4. Maandoverzicht")

detail_df = build_detail_df(st.session_state.targets)

with st.expander("Detail: maanddata 2025, targets 2026 en actuals 2026", expanded=True):
    display_detail = detail_df.copy()
    for col in ["Omzet 2025", "Target 2026", "Werkelijke omzet 2026"]:
        display_detail[col] = display_detail[col].map(eur)
    st.dataframe(display_detail, use_container_width=True, hide_index=True)

# -----------------------------
# 5. Kwartaalcontrole
# -----------------------------
st.subheader("5. Kwartaalcontrole")

q_left, q_right = st.columns(2)

with q_left:
    min_q_pct = st.slider(
        "Minimum aandeel per kwartaal",
        min_value=0,
        max_value=40,
        value=12,
        step=1,
        help="Voorkomt dat een kwartaal kunstmatig te laag wordt gezet."
    )

with q_right:
    max_q_pct = st.slider(
        "Maximum aandeel per kwartaal",
        min_value=25,
        max_value=60,
        value=40,
        step=1,
        help="Voorkomt dat te veel target naar één kwartaal wordt verschoven."
    )

quarter_rows = []
quarter_cols = st.columns(4)

for i, (q, months) in enumerate(QUARTERS.items()):
    q_target = sum(st.session_state.targets[m] for m in months)
    q_share = (q_target / annual_target * 100) if annual_target else 0
    status = "OK" if min_q_pct <= q_share <= max_q_pct else "Niet OK"

    actual = sum(ACTUAL_2026[m] for m in months)
    excess = max(0, actual - q_target)
    commission = excess * (commission_pct / 100)

    quarter_rows.append({
        "Kwartaal": q,
        "Maanden": ", ".join(months),
        "Kwartaaltarget": q_target,
        "Aandeel jaartarget": q_share,
        "Status verdeling": status,
        "Werkelijke omzet 2026": actual,
        "Omzet boven target": excess,
        "Commissie": commission,
    })

    with quarter_cols[i]:
        if status == "OK":
            st.success(f"{q} — OK")
        else:
            st.error(f"{q} — Niet OK")
        st.metric("Target", eur0(q_target))
        st.caption(f"Aandeel jaartarget: {pct(q_share)}")
        st.progress(min(1.0, q_share / 100))

# -----------------------------
# 6. Commissie
# -----------------------------
st.subheader("6. Commissie per kwartaal")

commission_df = pd.DataFrame(quarter_rows)

display_df = commission_df.copy()
for col in ["Kwartaaltarget", "Werkelijke omzet 2026", "Omzet boven target", "Commissie"]:
    display_df[col] = display_df[col].map(eur)
display_df["Aandeel jaartarget"] = display_df["Aandeel jaartarget"].map(pct)

st.dataframe(display_df, use_container_width=True, hide_index=True)

total_commission = commission_df["Commissie"].sum()
total_excess = commission_df["Omzet boven target"].sum()

cc1, cc2, cc3 = st.columns(3)
with cc1:
    st.metric("Totale omzet boven kwartaaltarget", eur0(total_excess))
with cc2:
    st.metric("Commissiepercentage", pct(commission_pct))
with cc3:
    st.metric("Totale berekende commissie", eur(total_commission))

with st.expander("Hoe wordt de commissie berekend?"):
    st.markdown("""
    De commissie wordt **per kwartaal** berekend.

    Per kwartaal kijkt de tool naar:

    **werkelijke omzet 2026 − kwartaaltarget**

    Alleen wanneer de werkelijke omzet hoger is dan het kwartaaltarget, wordt commissie berekend.

    Voorbeeld:

    - Kwartaaltarget: € 100.000
    - Werkelijke kwartaalomzet: € 125.000
    - Omzet boven target: € 25.000
    - Commissiepercentage: 2%

    Commissie = € 25.000 × 2% = € 500
    """)

# -----------------------------
# 7. Grafiek
# -----------------------------
st.subheader("7. Visuele vergelijking per maand")

st.write("De grafiek toont per maand drie balken naast elkaar: omzet 2025, target 2026 en werkelijke omzet 2026. Zo is vergelijken veel eenvoudiger.")

chart_df = detail_df.copy()
chart_long = chart_df.melt(
    id_vars=["Maand"],
    value_vars=["Omzet 2025", "Target 2026", "Werkelijke omzet 2026"],
    var_name="Reeks",
    value_name="Waarde"
)

month_order = MONTHS
series_order = ["Omzet 2025", "Target 2026", "Werkelijke omzet 2026"]

chart = alt.Chart(chart_long).mark_bar().encode(
    x=alt.X("Maand:N", sort=month_order, title="Maand"),
    xOffset=alt.XOffset("Reeks:N", sort=series_order),
    y=alt.Y("Waarde:Q", title="Bedrag (€)"),
    color=alt.Color("Reeks:N", sort=series_order, legend=alt.Legend(title="Legenda")),
    tooltip=[
        alt.Tooltip("Maand:N"),
        alt.Tooltip("Reeks:N"),
        alt.Tooltip("Waarde:Q", format=",.2f")
    ]
).properties(
    height=420
)

st.altair_chart(chart, use_container_width=True)

# -----------------------------
# 8. Export
# -----------------------------
st.subheader("8. Export")

quarter_export_df = commission_df.copy()

csv = detail_df.to_csv(index=False, sep=";").encode("utf-8-sig")
st.download_button(
    "Download maandtargets als CSV",
    data=csv,
    file_name="marcel_maandtargets_2026.csv",
    mime="text/csv",
)

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    detail_df.to_excel(writer, index=False, sheet_name="Maandtargets")
    quarter_export_df.to_excel(writer, index=False, sheet_name="Kwartaalcommissie")

st.download_button(
    "Download volledige Excel",
    data=excel_buffer.getvalue(),
    file_name="marcel_targets_en_commissie_2026.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
)
