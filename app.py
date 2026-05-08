
import streamlit as st
import pandas as pd
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

def init_targets(annual_target):
    previous_total = sum(SALES_2025.values())
    factor = annual_target / previous_total if previous_total else 1
    return {m: SALES_2025[m] * factor for m in MONTHS}

def normalize_targets_to_total(targets, annual_target):
    current_total = sum(targets.values())
    if current_total <= 0:
        return init_targets(annual_target)
    factor = annual_target / current_total
    return {m: targets[m] * factor for m in MONTHS}

def distribute_remaining_months(targets, annual_target, locked_months):
    """Adjusts only unlocked months proportionally so total equals annual target."""
    locked_total = sum(targets[m] for m in locked_months)
    unlocked_months = [m for m in MONTHS if m not in locked_months]
    unlocked_total = sum(targets[m] for m in unlocked_months)
    remaining = max(0, annual_target - locked_total)
    if not unlocked_months:
        return targets

    if unlocked_total <= 0:
        equal = remaining / len(unlocked_months)
        for m in unlocked_months:
            targets[m] = equal
    else:
        factor = remaining / unlocked_total
        for m in unlocked_months:
            targets[m] *= factor
    return targets

# -----------------------------
# Header
# -----------------------------
st.title("Target Verdeling & Commissie Tool")
st.caption("Voorbeeld op basis van de omzetcijfers van Marcel — targets verdelen en kwartaalcommissie simuleren.")

# -----------------------------
# Instellingen
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
        value=35.0,
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
# Session state
# -----------------------------
if "targets" not in st.session_state:
    st.session_state.targets = init_targets(annual_target)

if "last_annual_target" not in st.session_state:
    st.session_state.last_annual_target = annual_target

# Wanneer groeipercentage wijzigt, behoud de maandverhouding maar pas totaal aan.
if abs(st.session_state.last_annual_target - annual_target) > 0.01:
    st.session_state.targets = normalize_targets_to_total(st.session_state.targets, annual_target)
    st.session_state.last_annual_target = annual_target
    st.rerun()

# -----------------------------
# Actieknoppen vóór widgets
# -----------------------------
left, mid, right = st.columns([1, 1, 2])

with left:
    if st.button("Verdeel volgens 2025-seizoen", use_container_width=True):
        st.session_state.targets = init_targets(annual_target)
        st.rerun()

with mid:
    if st.button("Maak totaal passend", use_container_width=True):
        st.session_state.targets = normalize_targets_to_total(st.session_state.targets, annual_target)
        st.rerun()

with right:
    locked_actuals = st.checkbox(
        "Behaalden maanden 2026 vastzetten bij herverdeling",
        value=True,
        help="Wanneer actief worden de maanden waarvoor al omzet 2026 is ingevuld niet automatisch verlaagd of verhoogd bij herverdeling."
    )

# -----------------------------
# Maandtargets
# -----------------------------
st.subheader("2. Maandtargets verdelen")

st.write(
    "Pas de maandtargets aan. Het totaal moet gelijk zijn aan de jaartarget. "
    "Met **Maak totaal passend** wordt de verdeling proportioneel rechtgezet."
)

cols = st.columns(4)
for idx, month in enumerate(MONTHS):
    with cols[idx % 4]:
        st.session_state.targets[month] = st.number_input(
            month,
            min_value=0.0,
            value=float(round(st.session_state.targets[month], 2)),
            step=500.0,
            format="%.2f",
            key=f"target_input_{month}"
        )

target_total = sum(st.session_state.targets.values())
difference = annual_target - target_total

m1, m2, m3 = st.columns(3)
with m1:
    st.metric("Som maandtargets", eur0(target_total))
with m2:
    st.metric("Verschil met jaartarget", eur0(difference))
with m3:
    if abs(difference) <= 1:
        st.success("Totaal klopt.")
    else:
        st.warning("Totaal wijkt af. Klik op ‘Maak totaal passend’.")

# -----------------------------
# Kwartaalcontrole
# -----------------------------
st.subheader("3. Kwartaalcontrole")

min_q_pct = st.slider(
    "Minimum aandeel per kwartaal",
    min_value=0,
    max_value=40,
    value=12,
    step=1,
    help="Voorkomt dat een kwartaal kunstmatig te laag wordt gezet."
)

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
# Commissie
# -----------------------------
st.subheader("4. Commissie per kwartaal")

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
    st.markdown(
        """
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
        """
    )

# -----------------------------
# Detaildata
# -----------------------------
with st.expander("Detail: maanddata 2025, targets 2026 en actuals 2026"):
    detail_df = pd.DataFrame({
        "Maand": MONTHS,
        "Omzet 2025": [SALES_2025[m] for m in MONTHS],
        "Target 2026": [st.session_state.targets[m] for m in MONTHS],
        "Werkelijke omzet 2026": [ACTUAL_2026[m] for m in MONTHS],
    })
    display_detail = detail_df.copy()
    for col in ["Omzet 2025", "Target 2026", "Werkelijke omzet 2026"]:
        display_detail[col] = display_detail[col].map(eur)
    st.dataframe(display_detail, use_container_width=True, hide_index=True)

# -----------------------------
# Export
# -----------------------------
st.subheader("5. Export")

detail_df = pd.DataFrame({
    "Maand": MONTHS,
    "Omzet 2025": [SALES_2025[m] for m in MONTHS],
    "Target 2026": [st.session_state.targets[m] for m in MONTHS],
    "Werkelijke omzet 2026": [ACTUAL_2026[m] for m in MONTHS],
})

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
