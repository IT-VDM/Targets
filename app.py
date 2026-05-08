
import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

st.set_page_config(page_title="Target Verdeling & Commissie Tool", layout="wide", initial_sidebar_state="collapsed")

MONTHS = ["Jan", "Feb", "Mrt", "Apr", "Mei", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dec"]

DEFAULT_SALES_2025 = {
    "Jan": 6517.94, "Feb": 8571.23, "Mrt": 10415.83, "Apr": 15303.62,
    "Mei": 16938.59, "Jun": 15672.52, "Jul": 44562.66, "Aug": 24336.74,
    "Sep": 31857.59, "Okt": 30409.29, "Nov": 33193.43, "Dec": 37378.83,
}

DEFAULT_ACTUAL_2026 = {
    "Jan": 47749.00, "Feb": 31948.23, "Mrt": 42226.93, "Apr": 41337.31,
    "Mei": 14608.85, "Jun": 0.0, "Jul": 0.0, "Aug": 0.0,
    "Sep": 0.0, "Okt": 0.0, "Nov": 0.0, "Dec": 0.0,
}

QUARTERS = {
    "Q1": ["Jan", "Feb", "Mrt"],
    "Q2": ["Apr", "Mei", "Jun"],
    "Q3": ["Jul", "Aug", "Sep"],
    "Q4": ["Okt", "Nov", "Dec"],
}

ADMIN_LOGIN = "admin"
ADMIN_PASSWORD = "vdlx1234"


# -----------------------------
# Formatting helpers
# -----------------------------
def eur(value):
    return f"€ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def eur0(value):
    return f"€ {value:,.0f}".replace(",", ".")


def pct(value):
    return f"{value:.2f}%".replace(".", ",")


def input_key(month):
    return f"target_input_{month}"


def progress_pct(actual, target):
    if target <= 0:
        return 0.0
    return (actual / target) * 100


def progress_bar_value(actual, target):
    if target <= 0:
        return 0.0
    return min(1.0, actual / target)


def remaining_amount(actual, target):
    return max(0.0, target - actual)


def target_status(actual, target):
    if target <= 0:
        return "Geen target"
    if actual < target:
        return "Target niet gehaald"
    if actual == target:
        return "Target gehaald"
    return "Commissie actief"


def render_status(status):
    if status == "Commissie actief":
        st.success(status)
    elif status == "Target gehaald":
        st.info(status)
    elif status == "Geen target":
        st.warning(status)
    else:
        st.error(status)


# -----------------------------
# Data/state helpers
# -----------------------------
def init_config():
    st.session_state.setdefault("growth_pct", 60.0)
    st.session_state.setdefault("commission_pct", 2.0)
    st.session_state.setdefault("min_q_pct", 12)
    st.session_state.setdefault("max_q_pct", 40)
    st.session_state.setdefault("admin_logged_in", False)

    # Editable turnover data
    st.session_state.setdefault("sales_2025", DEFAULT_SALES_2025.copy())
    st.session_state.setdefault("actual_2026", DEFAULT_ACTUAL_2026.copy())

    # Forecast settings
    st.session_state.setdefault("forecast_enabled", False)
    st.session_state.setdefault("forecast_start_month", "Mei")
    st.session_state.setdefault("forecast_monthly_growth_pct", 0.0)


def get_sales_2025():
    return st.session_state.sales_2025


def get_effective_2026():
    """
    Returns a tuple:
    - values dict used for calculations
    - source dict with "Effectief" or "Prognose" per month

    Prognose-logica:
    De ingestelde maand is de referentiemaand.
    De prognose start vanaf de maand NA de referentiemaand.

    Voorbeeld:
    Referentiemaand = Mrt
    Prognosegroei = 10%
    Apr = Mrt x 1,10
    Mei = Apr x 1,10
    Jun = Mei x 1,10
    """
    actual = st.session_state.actual_2026.copy()
    values = actual.copy()
    sources = {m: "Effectief" if actual.get(m, 0.0) > 0 else "Geen omzet" for m in MONTHS}

    if not st.session_state.forecast_enabled:
        return values, sources

    reference_month = st.session_state.forecast_start_month
    reference_idx = MONTHS.index(reference_month)
    growth = float(st.session_state.forecast_monthly_growth_pct) / 100

    reference_value = actual.get(reference_month, 0.0)

    # Als de referentiemaand geen omzet heeft, zoek terug naar de laatste effectieve omzet.
    # Zo blijft de prognose bruikbaar, maar de tool blijft duidelijk gebaseerd op de ingestelde referentiemaand.
    if reference_value <= 0:
        for i in range(reference_idx - 1, -1, -1):
            if actual[MONTHS[i]] > 0:
                reference_value = actual[MONTHS[i]]
                break

    # Als er nergens effectieve omzet is, gebruik 0 als basis.
    previous_value = reference_value if reference_value > 0 else 0.0

    # Maanden t.e.m. de referentiemaand blijven effectief of leeg.
    for i in range(0, reference_idx + 1):
        month = MONTHS[i]
        values[month] = actual[month]
        sources[month] = "Effectief" if actual[month] > 0 else "Geen omzet"

    # Prognose start vanaf de maand na de referentiemaand.
    for i in range(reference_idx + 1, len(MONTHS)):
        month = MONTHS[i]
        if actual[month] > 0:
            values[month] = actual[month]
            sources[month] = "Effectief"
            previous_value = actual[month]
        else:
            forecast_value = previous_value * (1 + growth)
            values[month] = forecast_value
            sources[month] = "Prognose"
            previous_value = forecast_value

    return values, sources


def init_targets_by_2025_season(annual_target):
    sales_2025 = get_sales_2025()
    previous_total = sum(sales_2025.values())
    factor = annual_target / previous_total if previous_total else 1
    return {m: sales_2025[m] * factor for m in MONTHS}


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
    st.session_state.targets = {m: float(new_targets[m]) for m in MONTHS}
    for m in MONTHS:
        st.session_state[input_key(m)] = float(round(new_targets[m], 2))


def build_detail_df(targets, values_2026, source_2026):
    sales_2025 = get_sales_2025()
    return pd.DataFrame({
        "Maand": MONTHS,
        "Omzet 2025": [sales_2025[m] for m in MONTHS],
        "Target 2026": [targets[m] for m in MONTHS],
        "Omzet 2026 / prognose": [values_2026[m] for m in MONTHS],
        "Type 2026": [source_2026[m] for m in MONTHS],
    })


def current_annual_target():
    return sum(get_sales_2025().values()) * (1 + float(st.session_state.growth_pct) / 100)


def sync_targets_after_config_change(new_annual_target):
    old_target = st.session_state.get("last_annual_target", new_annual_target)
    if abs(old_target - new_annual_target) > 0.01 and "targets" in st.session_state:
        new_targets = normalize_targets_to_total(st.session_state.targets, new_annual_target)
        apply_targets(new_targets)
    st.session_state.last_annual_target = new_annual_target


def make_turnover_editor_df():
    return pd.DataFrame({
        "Maand": MONTHS,
        "Omzet 2025": [st.session_state.sales_2025[m] for m in MONTHS],
        "Effectieve omzet 2026": [st.session_state.actual_2026[m] for m in MONTHS],
    })


def apply_turnover_editor_df(df):
    for _, row in df.iterrows():
        month = row["Maand"]
        if month in MONTHS:
            st.session_state.sales_2025[month] = float(row["Omzet 2025"] or 0.0)
            st.session_state.actual_2026[month] = float(row["Effectieve omzet 2026"] or 0.0)


# -----------------------------
# Init
# -----------------------------
init_config()
annual_target = current_annual_target()

if "targets" not in st.session_state:
    apply_targets(init_targets_by_2025_season(annual_target))

st.session_state.setdefault("last_annual_target", annual_target)
sync_targets_after_config_change(annual_target)

for m in MONTHS:
    st.session_state.setdefault(input_key(m), float(round(st.session_state.targets[m], 2)))


# -----------------------------
# Navigation
# -----------------------------
st.sidebar.title("Navigatie")
page = st.sidebar.radio("Pagina", ["Target tool", "Config / Admin"], label_visibility="collapsed")


# -----------------------------
# Config / Admin
# -----------------------------
if page == "Config / Admin":
    st.title("Config / Admin")
    st.caption("Beheer de afgeschermde instellingen, omzetcijfers en prognose-instellingen.")

    if not st.session_state.admin_logged_in:
        st.warning("Log in als admin om de instellingen te wijzigen.")
        with st.form("admin_login_form"):
            username = st.text_input("Login")
            password = st.text_input("Wachtwoord", type="password")
            submitted = st.form_submit_button("Inloggen")
        if submitted:
            if username == ADMIN_LOGIN and password == ADMIN_PASSWORD:
                st.session_state.admin_logged_in = True
                st.success("Ingelogd als admin.")
                st.rerun()
            else:
                st.error("Onjuiste login of wachtwoord.")
        st.stop()

    top_left, top_right = st.columns([3, 1])
    with top_left:
        st.success("Ingelogd als admin. Je kan de instellingen hieronder aanpassen.")
    with top_right:
        if st.button("Uitloggen", use_container_width=True):
            st.session_state.admin_logged_in = False
            st.rerun()

    tab_settings, tab_turnover, tab_forecast = st.tabs(["Algemene instellingen", "Omzetcijfers", "Prognose"])

    with tab_settings:
        st.subheader("Algemene instellingen")
        c1, c2 = st.columns(2)
        with c1:
            new_growth_pct = st.number_input(
                "Groei % t.o.v. 2025",
                min_value=0.0,
                max_value=200.0,
                value=float(st.session_state.growth_pct),
                step=1.0,
                format="%.2f"
            )
        with c2:
            new_commission_pct = st.number_input(
                "Commissiepercentage",
                min_value=0.0,
                max_value=50.0,
                value=float(st.session_state.commission_pct),
                step=0.25,
                format="%.2f"
            )

        st.subheader("Kwartaalcontrole")
        q1, q2 = st.columns(2)
        with q1:
            new_min_q_pct = st.slider(
                "Minimum aandeel per kwartaal",
                min_value=0,
                max_value=40,
                value=int(st.session_state.min_q_pct),
                step=1
            )
        with q2:
            new_max_q_pct = st.slider(
                "Maximum aandeel per kwartaal",
                min_value=25,
                max_value=60,
                value=int(st.session_state.max_q_pct),
                step=1
            )

        if new_min_q_pct > new_max_q_pct:
            st.error("Minimum aandeel per kwartaal mag niet hoger zijn dan maximum aandeel per kwartaal.")
        elif st.button("Algemene instellingen bewaren", type="primary"):
            st.session_state.growth_pct = float(new_growth_pct)
            st.session_state.commission_pct = float(new_commission_pct)
            st.session_state.min_q_pct = int(new_min_q_pct)
            st.session_state.max_q_pct = int(new_max_q_pct)
            sync_targets_after_config_change(current_annual_target())
            st.success("Algemene instellingen bewaard.")
            st.rerun()

        st.divider()
        preview_annual_target = sum(get_sales_2025().values()) * (1 + float(new_growth_pct) / 100)
        p1, p2, p3, p4 = st.columns(4)
        p1.metric("Omzet 2025", eur0(sum(get_sales_2025().values())))
        p2.metric("Groei", pct(float(new_growth_pct)))
        p3.metric("Jaartarget", eur0(preview_annual_target))
        p4.metric("Commissie", pct(float(new_commission_pct)))

    with tab_turnover:
        st.subheader("Omzetcijfers aanpassen")
        st.write(
            "Pas hier de basisomzet 2025 en de effectieve omzet 2026 aan. "
            "De effectieve omzet 2026 wordt gebruikt voor progress bars en commissie-preview."
        )

        editor_df = make_turnover_editor_df()
        edited_df = st.data_editor(
            editor_df,
            use_container_width=True,
            hide_index=True,
            disabled=["Maand"],
            column_config={
                "Omzet 2025": st.column_config.NumberColumn("Omzet 2025", min_value=0.0, step=500.0, format="%.2f"),
                "Effectieve omzet 2026": st.column_config.NumberColumn("Effectieve omzet 2026", min_value=0.0, step=500.0, format="%.2f"),
            },
            key="turnover_editor"
        )

        c_save, c_reset = st.columns(2)
        with c_save:
            if st.button("Omzetcijfers bewaren", type="primary", use_container_width=True):
                apply_turnover_editor_df(edited_df)
                sync_targets_after_config_change(current_annual_target())
                st.success("Omzetcijfers bewaard.")
                st.rerun()

        with c_reset:
            if st.button("Omzetcijfers resetten naar standaard", use_container_width=True):
                st.session_state.sales_2025 = DEFAULT_SALES_2025.copy()
                st.session_state.actual_2026 = DEFAULT_ACTUAL_2026.copy()
                sync_targets_after_config_change(current_annual_target())
                st.success("Omzetcijfers gereset.")
                st.rerun()

    with tab_forecast:
        st.subheader("Prognose-instellingen")
        st.write(
            "Gebruik prognose om toekomstige maanden automatisch aan te vullen. "
            "Maanden met prognose worden apart aangeduid, zodat duidelijk blijft wat effectief en wat simulatie is."
        )

        new_forecast_enabled = st.toggle(
            "Prognose gebruiken voor lege toekomstige maanden",
            value=bool(st.session_state.forecast_enabled)
        )

        f1, f2 = st.columns(2)
        with f1:
            new_forecast_start_month = st.selectbox(
                "Referentiemaand voor prognose",
                MONTHS,
                index=MONTHS.index(st.session_state.forecast_start_month)
            )
        with f2:
            new_forecast_growth = st.number_input(
                "Prognosegroei per maand na referentiemaand",
                min_value=-50.0,
                max_value=100.0,
                value=float(st.session_state.forecast_monthly_growth_pct),
                step=1.0,
                format="%.2f",
                help="Voorbeeld: referentiemaand maart en 10% groei betekent: april = maart × 1,10; mei = april × 1,10."
            )

        if st.button("Prognose-instellingen bewaren", type="primary"):
            st.session_state.forecast_enabled = bool(new_forecast_enabled)
            st.session_state.forecast_start_month = new_forecast_start_month
            st.session_state.forecast_monthly_growth_pct = float(new_forecast_growth)
            st.success("Prognose-instellingen bewaard.")
            st.rerun()

        values_2026_preview, source_2026_preview = get_effective_2026()
        preview_df = pd.DataFrame({
            "Maand": MONTHS,
            "Effectief/prognose 2026": [values_2026_preview[m] for m in MONTHS],
            "Type": [source_2026_preview[m] for m in MONTHS],
        })
        display_preview = preview_df.copy()
        display_preview["Effectief/prognose 2026"] = display_preview["Effectief/prognose 2026"].map(eur)
        st.dataframe(display_preview, use_container_width=True, hide_index=True)

    st.stop()


# -----------------------------
# Target Tool
# -----------------------------
values_2026, source_2026 = get_effective_2026()

st.title("Target Verdeling & Commissie Tool")
st.caption("Eenvoudige tool om de jaartarget te verdelen, kwartaaldoelen te controleren en commissie te simuleren.")

st.subheader("1. Instellingen")
total_2025 = sum(get_sales_2025().values())
growth_pct = float(st.session_state.growth_pct)
commission_pct = float(st.session_state.commission_pct)
min_q_pct = int(st.session_state.min_q_pct)
max_q_pct = int(st.session_state.max_q_pct)
annual_target = current_annual_target()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Omzet 2025", eur0(total_2025))
c2.metric("Groei t.o.v. 2025", pct(growth_pct))
c3.metric("Jaartarget 2026", eur0(annual_target))
c4.metric("Commissiepercentage", pct(commission_pct))

st.info("Groei, commissiepercentage, kwartaalgrenzen, omzetcijfers en prognose-instellingen zijn afgeschermd. Deze kunnen enkel aangepast worden via **Config / Admin**.")
st.info("Commissieformule: **commissie per kwartaal = max(0, werkelijke/prognose kwartaalomzet − kwartaaltarget) × commissiepercentage**.")

if st.session_state.forecast_enabled:
    st.warning(
        f"Prognosemodus actief: {st.session_state.forecast_start_month} is de referentiemaand. Lege maanden erna worden aangevuld met "
        f"{pct(float(st.session_state.forecast_monthly_growth_pct))} groei per maand t.o.v. de vorige maand. Prognosewaarden worden apart aangeduid."
    )

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

st.subheader("3. Maandtargets aanpassen")
cols = st.columns(4)
for idx, month in enumerate(MONTHS):
    with cols[idx % 4]:
        st.number_input(month, min_value=0.0, step=500.0, format="%.2f", key=input_key(month))
st.session_state.targets = {m: float(st.session_state[input_key(m)]) for m in MONTHS}

target_total = sum(st.session_state.targets.values())
amount_to_distribute = annual_target - target_total
m1, m2, m3 = st.columns(3)
m1.metric("Som maandtargets", eur0(target_total))
m2.metric("Te verdelen targetbedrag", eur0(amount_to_distribute))
if abs(amount_to_distribute) <= 1:
    m3.success("Totaal klopt.")
else:
    m3.warning("Totaal wijkt af. Klik op ‘Maak totaal passend’.")

st.subheader("4. Maandoverzicht")
detail_df = build_detail_df(st.session_state.targets, values_2026, source_2026)
with st.expander("Detail: maanddata 2025, targets 2026 en omzet/prognose 2026", expanded=True):
    display_detail = detail_df.copy()
    for col in ["Omzet 2025", "Target 2026", "Omzet 2026 / prognose"]:
        display_detail[col] = display_detail[col].map(eur)
    st.dataframe(display_detail, use_container_width=True, hide_index=True)
    st.caption("Rijen met type **Prognose** zijn simulaties en geen effectieve omzet.")

# -----------------------------
# 5. Maandprogress
# -----------------------------
st.subheader("5. Maandprogress")
st.caption("Opvolging per maand: target, effectieve/prognose omzet, nog te behalen bedrag en status.")

month_cols = st.columns(4)
monthly_progress_rows = []

for idx, month in enumerate(MONTHS):
    month_target = float(st.session_state.targets[month])
    month_actual = float(values_2026[month])
    month_source = source_2026[month]
    month_remaining = remaining_amount(month_actual, month_target)
    month_progress = progress_pct(month_actual, month_target)
    month_status = target_status(month_actual, month_target)

    monthly_progress_rows.append({
        "Maand": month,
        "Target 2026": month_target,
        "Omzet/prognose 2026": month_actual,
        "Type 2026": month_source,
        "Nog te behalen": month_remaining,
        "Progress": month_progress,
        "Status": month_status,
    })

    with month_cols[idx % 4]:
        title = f"**{month}**"
        if month_source == "Prognose":
            title += "  _prognose_"
        st.markdown(title)
        st.progress(progress_bar_value(month_actual, month_target))
        st.caption(f"{pct(month_progress)} van target")
        st.write(f"Target: **{eur0(month_target)}**")
        if month_source == "Prognose":
            st.markdown(f"Omzet/prognose: _{eur0(month_actual)}_")
        else:
            st.write(f"Omzet: **{eur0(month_actual)}**")
        st.write(f"Nog te behalen: **{eur0(month_remaining)}**")
        render_status(month_status)

with st.expander("Detail: maandprogress in tabel"):
    monthly_progress_df = pd.DataFrame(monthly_progress_rows)
    display_monthly_progress = monthly_progress_df.copy()
    for col in ["Target 2026", "Omzet/prognose 2026", "Nog te behalen"]:
        display_monthly_progress[col] = display_monthly_progress[col].map(eur)
    display_monthly_progress["Progress"] = display_monthly_progress["Progress"].map(pct)
    st.dataframe(display_monthly_progress, use_container_width=True, hide_index=True)

# -----------------------------
# 6. Kwartaalcontrole & kwartaalprogress
# -----------------------------
st.subheader("6. Kwartaalcontrole & kwartaalprogress")
st.caption(
    f"Controlegrenzen voor de verdeling: minimum {min_q_pct}% en maximum {max_q_pct}% van de jaartarget per kwartaal. "
    "Deze grenzen kunnen enkel aangepast worden via Config / Admin."
)

st.write("**Targetverdeling = plannen · Progress bars = opvolgen · Commissieoverzicht = resultaat**")

quarter_rows = []
quarter_cols = st.columns(4)

for i, (q, months) in enumerate(QUARTERS.items()):
    q_target = sum(st.session_state.targets[m] for m in months)
    q_share = (q_target / annual_target * 100) if annual_target else 0
    distribution_status = "OK" if min_q_pct <= q_share <= max_q_pct else "Niet OK"

    actual = sum(values_2026[m] for m in months)
    has_forecast = any(source_2026[m] == "Prognose" for m in months)
    excess = max(0, actual - q_target)
    remaining = remaining_amount(actual, q_target)
    q_progress = progress_pct(actual, q_target)
    commission = excess * (commission_pct / 100)
    q_status = target_status(actual, q_target)

    quarter_rows.append({
        "Kwartaal": q,
        "Maanden": ", ".join(months),
        "Kwartaaltarget": q_target,
        "Aandeel jaartarget": q_share,
        "Status verdeling": distribution_status,
        "Omzet/prognose 2026": actual,
        "Bevat prognose": "Ja" if has_forecast else "Nee",
        "Progress t.o.v. target": q_progress,
        "Nog te behalen": remaining,
        "Omzet boven target": excess,
        "Commissie preview": commission,
        "Status target": q_status,
    })

    with quarter_cols[i]:
        if distribution_status == "OK":
            st.success(f"{q} — verdeling OK")
        else:
            st.error(f"{q} — verdeling niet OK")

        st.metric("Kwartaaltarget", eur0(q_target))
        st.caption(f"Aandeel jaartarget: {pct(q_share)}")

        st.progress(progress_bar_value(actual, q_target))
        st.caption(f"Progress: {pct(q_progress)}")

        if has_forecast:
            st.markdown(f"Omzet/prognose: _{eur0(actual)}_")
        else:
            st.write(f"Behaald: **{eur0(actual)}**")

        st.write(f"Nog te behalen: **{eur0(remaining)}**")
        st.write(f"Boven target: **{eur0(excess)}**")
        st.write(f"Commissie preview: **{eur(commission)}**")
        if has_forecast:
            st.caption("_Bevat prognosewaarden_")
        render_status(q_status)

# -----------------------------
# 7. Commissie per kwartaal
# -----------------------------
st.subheader("7. Commissie per kwartaal")
commission_df = pd.DataFrame(quarter_rows)
display_df = commission_df.copy()

for col in ["Kwartaaltarget", "Omzet/prognose 2026", "Nog te behalen", "Omzet boven target", "Commissie preview"]:
    display_df[col] = display_df[col].map(eur)

display_df["Aandeel jaartarget"] = display_df["Aandeel jaartarget"].map(pct)
display_df["Progress t.o.v. target"] = display_df["Progress t.o.v. target"].map(pct)

st.dataframe(display_df, use_container_width=True, hide_index=True)

total_commission = commission_df["Commissie preview"].sum()
total_excess = commission_df["Omzet boven target"].sum()
total_remaining = commission_df["Nog te behalen"].sum()
total_2026_projection = sum(values_2026.values())

cc1, cc2, cc3, cc4 = st.columns(4)
cc1.metric("Omzet boven kwartaaltarget", eur0(total_excess))
cc2.metric("Nog te behalen t.o.v. kwartalen", eur0(total_remaining))
cc3.metric("Commissiepercentage", pct(commission_pct))
cc4.metric("Totale commissie preview", eur(total_commission))

if st.session_state.forecast_enabled:
    st.info(f"Geprojecteerde omzet 2026 incl. prognose: **{eur(total_2026_projection)}**")

with st.expander("Hoe wordt de commissie berekend?"):
    voorbeeld_target = 100000
    voorbeeld_omzet = 125000
    voorbeeld_boven_target = voorbeeld_omzet - voorbeeld_target
    voorbeeld_commissie = voorbeeld_boven_target * (commission_pct / 100)
    st.markdown(f"""
    De commissie wordt **per kwartaal** berekend.

    Per kwartaal kijkt de tool naar:

    **werkelijke/prognose omzet 2026 − kwartaaltarget**

    Alleen wanneer de omzet hoger is dan het kwartaaltarget, wordt commissie berekend.

    Voorbeeld:

    - Kwartaaltarget: {eur0(voorbeeld_target)}
    - Werkelijke kwartaalomzet: {eur0(voorbeeld_omzet)}
    - Omzet boven target: {eur0(voorbeeld_boven_target)}
    - Commissiepercentage: {pct(commission_pct)}

    Commissie = {eur0(voorbeeld_boven_target)} × {pct(commission_pct)} = {eur(voorbeeld_commissie)}
    """)

# -----------------------------
# 8. Visuele vergelijking per maand
# -----------------------------
st.subheader("8. Visuele vergelijking per maand")
st.write("De grafiek toont per maand drie balken naast elkaar: omzet 2025, target 2026 en effectieve/prognose omzet 2026.")

chart_long = detail_df.melt(
    id_vars=["Maand", "Type 2026"],
    value_vars=["Omzet 2025", "Target 2026", "Omzet 2026 / prognose"],
    var_name="Reeks",
    value_name="Waarde"
)

series_order = ["Omzet 2025", "Target 2026", "Omzet 2026 / prognose"]

chart = alt.Chart(chart_long).mark_bar().encode(
    x=alt.X("Maand:N", sort=MONTHS, title="Maand"),
    xOffset=alt.XOffset("Reeks:N", sort=series_order),
    y=alt.Y("Waarde:Q", title="Bedrag (€)"),
    color=alt.Color("Reeks:N", sort=series_order, legend=alt.Legend(title="Legenda")),
    tooltip=[
        alt.Tooltip("Maand:N"),
        alt.Tooltip("Reeks:N"),
        alt.Tooltip("Type 2026:N"),
        alt.Tooltip("Waarde:Q", format=",.2f")
    ]
).properties(height=420)

st.altair_chart(chart, use_container_width=True)

# -----------------------------
# 9. Export
# -----------------------------
st.subheader("9. Export")
csv = detail_df.to_csv(index=False, sep=";").encode("utf-8-sig")
st.download_button("Download maandtargets als CSV", data=csv, file_name="marcel_maandtargets_2026.csv", mime="text/csv")

excel_buffer = BytesIO()
with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
    detail_df.to_excel(writer, index=False, sheet_name="Maandtargets")
    pd.DataFrame(monthly_progress_rows).to_excel(writer, index=False, sheet_name="Maandprogress")
    commission_df.to_excel(writer, index=False, sheet_name="Kwartaalcommissie")

st.download_button(
    "Download volledige Excel",
    data=excel_buffer.getvalue(),
    file_name="marcel_targets_en_commissie_2026.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)
