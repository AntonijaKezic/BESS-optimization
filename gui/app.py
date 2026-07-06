import sys
from pathlib import Path
from io import BytesIO
from datetime import datetime, date, timedelta

from openpyxl.styles import Font

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_model import run_model

from models.load_profile import (
    PROFILE_NAMES,
    DEFAULT_PROFILE
)

from models.solar_reference import clearsky_daily_kwh
from api.openmeteo_api import get_monthly_daily_totals, LATITUDE

from plots import (
    plot_soc_pv,
    plot_soc_grid,
    plot_pv,
    plot_prices,
    plot_power_pv,
    plot_power_grid,
    plot_costs,
    plot_costs_pv,
    plot_energy_balance,
    plot_month_heatmap
)

import calendar


@st.cache_data(show_spinner="Dohvaćam mjesečne podatke...")
def cached_monthly_totals(year, month):
    return get_monthly_daily_totals(year, month)


def clearsky_for_month(year, month):
    """Vraca dict {dan: idealna_dnevna_kwh} za sve dane u mjesecu."""

    _, days_in_month = calendar.monthrange(year, month)

    result = {}

    for d in range(1, days_in_month + 1):

        doy = date(year, month, d).timetuple().tm_yday

        result[d] = clearsky_daily_kwh(doy, LATITUDE)

    return result

# -------------------------------------------------
# POSTAVKE STRANICE
# -------------------------------------------------

st.set_page_config(
    page_title="BESS Optimization",
    page_icon="🔋",
    layout="wide"
)

st.title("🔋 BESS Optimization")

st.markdown(
    """
Optimizacija rada baterijskog spremnika uz fotonaponsku elektranu
na temelju vremenske prognoze i tržišnih cijena električne energije.
"""
)

tab_results, tab_model, tab_about = st.tabs([
    "📊 Rezultati",
    "📐 Matematički model",
    "ℹ️ O aplikaciji"
])

# -------------------------------------------------
# SIDEBAR
# -------------------------------------------------

with st.sidebar:

    st.header("Parametri sustava")
    
    scenario = st.radio(

        "Scenarij rada",

        [

            "PV + baterija",

            "Baterija spojena na mrežu"

        ]
    )

    data_mode = st.radio(
        "Izvor podataka",
        ["Sutra (prognoza)", "Povijesni datum"],
        help=
        "Sutra: prognoza Open-Meteo i day-ahead cijene za sutra. "
        "Povijesni datum: ERA5 reanaliza (Open-Meteo Archive) i "
        "day-ahead cijene za odabrani datum."
    )

    if data_mode == "Povijesni datum":

        historical_date = st.date_input(
            "Datum",
            value=(datetime.now() - timedelta(days=14)).date(),
            min_value=date(2016, 1, 1),
            max_value=(datetime.now() - timedelta(days=3)).date(),
            help=
            "Open-Meteo Archive ima oko 3 dana kašnjenja. "
            "ENTSO-E cijene za HR dostupne su od 2016."
        )

        # -----------------------------------------
        # Kalendarski heatmap dozracene energije
        # za mjesec odabranog datuma. Boja pokazuje
        # koji su dani bili suncani (zuto) i oblacni (sivo).
        # -----------------------------------------

        _daily = cached_monthly_totals(
            historical_date.year,
            historical_date.month
        )

        _clearsky = clearsky_for_month(
            historical_date.year,
            historical_date.month
        )

        if _daily:

            st.plotly_chart(
                plot_month_heatmap(
                    historical_date.year,
                    historical_date.month,
                    _daily,
                    _clearsky
                ),
                use_container_width=True,
                config={"displayModeBar": False}
            )

            sorted_days = sorted(_daily.items(), key=lambda kv: kv[1])
            worst_day, worst_kwh = sorted_days[0]
            best_day, best_kwh = sorted_days[-1]
            avg = sum(_daily.values()) / len(_daily)

            st.caption(
                f"☀️ Najsunčaniji: **{best_day:02d}.** "
                f"({best_kwh:.2f} kWh/m²) &nbsp;&nbsp; "
                f"☁️ Najoblačniji: **{worst_day:02d}.** "
                f"({worst_kwh:.2f} kWh/m²) &nbsp;&nbsp; "
                f"Prosjek: **{avg:.2f} kWh/m²/dan**",
                unsafe_allow_html=True
            )

        else:

            st.caption(
                "_Nema dostupnih podataka za odabrani mjesec._"
            )

    else:

        historical_date = None

    if scenario == "PV + baterija":

        p_nom_pv = st.number_input(
            "Nazivna snaga PV [kWp]",
            value=10.0,
            help=
            "Nazivna DC snaga PV instalacije pri STC "
            "(1000 W/m², 25 °C) - vršna snaga koja se "
            "naznačuje na tablici uređaja."
        )

        eta_pv = st.slider(
            "Derating sustava [-]",

            0.80,

            0.95,

            0.85,

            0.01,

            help=
            "Ukupni gubici sustava izvan STC: temperatura "
            "panela, kablovi, inverter, prljavština. Tipično 0.80-0.90."
        )

        daily_load_kwh = st.number_input(
            "Dnevna potrošnja [kWh]",
            value=30.0,
            min_value=0.0,
            step=1.0
        )

        profile_name = st.selectbox(
            "Profil potrošnje",
            PROFILE_NAMES,
            index=PROFILE_NAMES.index(DEFAULT_PROFILE),
            help=
            "Oblik krivulje dnevne potrošnje. Predlošci se "
            "automatski skaliraju na zadanu dnevnu potrošnju."
        )

    else:

        eta_pv = None

        p_nom_pv = None

        daily_load_kwh = None

        profile_name = None

    soc0 = st.slider(
        "Početni SOC",
        0.20,
        0.90,
        0.50,
        0.01
    )

    e_max = st.number_input(
        "Kapacitet baterije [kWh]",
        value=20.0
    )

    eta = st.slider(
        "Učinkovitost baterije",
        0.80,
        1.00,
        0.95,
        0.01
    )

    c_rate = st.number_input(
        "C-rate",
        value=0.5
    )

    c_deg = st.number_input(
        "Trošak degradacije [€/kWh]",
        value=0.01,
        step=0.001,
        format="%.3f"
    )

    p_max = st.number_input(
        "Maksimalna priključna snaga [kW]",
        value=10.0
    )

    dt = st.number_input(
        "Korak simulacije [h]",
        value=0.25,
        step=0.25,
        help=
        "Trajanje jednog vremenskog koraka. 0.25 h = 15 min "
        "raster (96 koraka/dan), 1.0 h = satni raster (24 koraka/dan)."
    )

    use_milp = st.checkbox(
        "Koristi MILP",
        value=True
    )

    run = st.button(
        "▶ Pokreni optimizaciju",
        use_container_width=True
    )

    st.markdown("---")

    st.caption(
        "Završni rad\n\nAntonija Kežić"+"\n2026."
    )
    
    if (
    "results" not in st.session_state
    or st.session_state.get("scenario") != scenario
    or st.session_state.get("data_mode") != data_mode
    ):

        st.session_state["scenario"] = scenario
        st.session_state["data_mode"] = data_mode

        st.session_state["results"] = run_model(
            eta_pv,
            p_nom_pv,
            soc0,
            e_max,
            eta,
            c_rate,
            c_deg,
            p_max,
            dt,
            scenario,
            use_milp,
            daily_load_kwh,
            profile_name,
            historical_date
        )

    if run:

        with st.spinner("Pokrećem optimizaciju..."):

            st.session_state["results"] = run_model(
                eta_pv,
                p_nom_pv,
                soc0,
                e_max,
                eta,
                c_rate,
                c_deg,
                p_max,
                dt,
                scenario,
                use_milp,
                daily_load_kwh,
                profile_name,
                historical_date
        )


# -------------------------------------------------
# PRIKAZ REZULTATA
# -------------------------------------------------

with tab_results:

    if "results" in st.session_state:

        results = st.session_state["results"]

        st.caption(
            f"📅 Datum optimizacije: **{results['optimization_date']}** "
            f"({'povijesni podaci' if results['price_day'] == 'historical' else 'prognoza'})"
        )

        if results["price_day"] == "today":
            st.warning(
            "Sutrašnje cijene nisu bile dostupne. Korištene su današnje cijene."
        )
            

    # -------------------------------------------------
    # KPI
    # -------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        cost = results["cost"]
        if cost < 0:
            c1.metric(
                "Procijenjena ušteda",
                f"{abs(cost):.2f} €"
            )
        else:
            c1.metric(
                "Procijenjeni trošak",
                f"{cost:.2f} €"
            )


        c2.metric(
            "Završni SOC",
            f"{results['soc'][-1]:.2f}"
        )

        step_dt = results.get("dt", 0.25)

        if scenario=="PV + baterija":

            c3.metric(

                "Maksimalna PV snaga",

                f"{max(results['pv']):.2f} kW"

            )

            c4.metric(

                "Ukupna PV energija",

                f"{sum(results['pv']) * step_dt:.2f} kWh"

            )

        else:

            c3.metric(

                "Maksimalna snaga punjenja",

                f"{max(results['p_charge']):.2f} kW"

            )

            c4.metric(

                "Ukupna energija punjenja",

                f"{sum(results['p_charge']) * step_dt:.2f} kWh"

            )
        
        c5, c6, c7 = st.columns(3)
        
        c5.metric(
            "Prosječna cijena",
            f"{sum(results['prices']) / len(results['prices']):.2f} €/MWh"
        )

        c6.metric(
            "Minimalna cijena",
            f"{min(results['prices']):.2f} €/MWh"
        )

        c7.metric(
            "Maksimalna cijena",
            f"{max(results['prices']):.2f} €/MWh"
        )

        st.divider()

    # -------------------------------------------------
    # GRAFOVI
    # -------------------------------------------------

        left, right = st.columns(2)

        with left:

            if scenario == "PV + baterija":

                st.plotly_chart(
                    plot_soc_pv(results["soc"]),
                    use_container_width=True
                )

            else:

                st.plotly_chart(
                    plot_soc_grid(results["soc"]),
                    use_container_width=True
                )

            st.plotly_chart(
                plot_prices(results["prices"]),
                use_container_width=True
            )

        with right:

            if scenario == "PV + baterija":

                st.plotly_chart(
                    plot_pv(results["pv"]),
                    use_container_width=True
                )

                st.plotly_chart(
                    plot_power_pv(
                        results["p_charge"],
                        results["p_discharge"]
                    ),
                    use_container_width=True
                )

            else:

                st.plotly_chart(
                    plot_power_grid(
                        results["p_charge"],
                        results["p_discharge"]
                    ),
                    use_container_width=True
                )

        if scenario == "PV + baterija":

            st.plotly_chart(
                plot_energy_balance(
                    results["pv_to_load"],
                    results["p_discharge"],
                    results["grid_imp"],
                    results["p_load"]
                ),
                use_container_width=True
            )

            st.plotly_chart(
                plot_costs_pv(
                    results["hourly_savings"]
                ),
                use_container_width=True
            )

        else:

            st.plotly_chart(
                plot_costs(
                    results["charge_costs"],
                    results["discharge_benefits"]
                ),
            use_container_width=True
            )

        st.divider()

        st.subheader("Analiza rezultata")

        min_price = min(results["prices"])
        max_price = max(results["prices"])

        min_idx = results["prices"].index(min_price)
        max_idx = results["prices"].index(max_price)

        sph = results.get("steps_per_hour", 4)
        step_minutes = 60 // sph

        def _fmt_slot(i):
            return (
                f"{(i // sph):02d}:"
                f"{(i % sph) * step_minutes:02d}"
            )

        min_time = _fmt_slot(min_idx)
        max_time = _fmt_slot(max_idx)

        cost = results["cost"]

        if cost < 0:
            economic_result = (
                f"Procijenjena dnevna ušteda "
                f"iznosi **{abs(cost):.2f} €**."
            )
        else:
            economic_result = (
                f"Procijenjeni dnevni trošak "
                f"**{cost:.2f} €**."
            )

        if scenario == "PV + baterija":

            pv_text = (
                f"Ukupna proizvedena energija iz fotonaponske elektrane iznosi "
                f"**{sum(results['pv']) * results.get('dt', 0.25):.2f} kWh**."
            )

        else:

            pv_text = ""

        st.markdown(f"""
        Najniža tržišna cijena iznosila je **{min_price:.2f} €/MWh**
        u **{min_time}**.

        Najviša tržišna cijena iznosila je **{max_price:.2f} €/MWh**
        u **{max_time}**.

        {pv_text}
        {economic_result}
        """)

        

    
    # -------------------------------------------------
    # TABLICA
    # -------------------------------------------------

        st.subheader("Rezultati po vremenskim koracima")

        n_slots = len(results["prices"])

        sph_tbl = results.get("steps_per_hour", 4)
        step_min = 60 // sph_tbl

        def _slot_range(i):
            start_h = i // sph_tbl
            start_m = (i % sph_tbl) * step_min
            end_slot = i + 1
            end_h = (end_slot // sph_tbl) % 24
            end_m = (end_slot % sph_tbl) * step_min
            return (
                f"{start_h:02d}:{start_m:02d} - "
                f"{end_h:02d}:{end_m:02d}"
            )

        razdoblja = [_slot_range(i) for i in range(n_slots)]

        if scenario == "PV + baterija":

            df = pd.DataFrame({

            "Razdoblje": razdoblja,

            "PV [kW]": results["pv"],

            "Potrošnja [kW]": results["p_load"],

            "Cijena [€/MWh]": results["prices"],

            "Iz PV → potrošnja [kW]": results["pv_to_load"],

            "Iz mreže [kW]": results["grid_imp"],

            "Punjenje [kW]": results["p_charge"],

            "Pražnjenje [kW]": results["p_discharge"],

            "SOC": results["soc"][:-1],

            "Ušteda [€]": results["hourly_savings"]

        })

        else:

            df = pd.DataFrame({

            "Razdoblje": razdoblja,

            "Cijena [€/MWh]": results["prices"],

            "Punjenje [kW]": results["p_charge"],

            "Pražnjenje [kW]": results["p_discharge"],

            "SOC": results["soc"][:-1],

            "Trošak [€]": results["hourly_costs"],

            })

        df = df.round(3)

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )

        st.divider()

    # -------------------------------------------------
    # PREUZIMANJE
    # -------------------------------------------------

        c1, c2 = st.columns(2)

        csv = df.to_csv(
            index=False,
            sep=";",
            decimal=","
        ).encode("utf-8-sig")

        with c1:

            st.download_button(
                "📄 Preuzmi CSV",
                csv,
                file_name="rezultati.csv",
                mime="text/csv",
                use_container_width=True
            )

        buffer = BytesIO()

        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df.to_excel(
                writer,
                index=False,
            sheet_name="Rezultati"
            )
            worksheet = writer.sheets["Rezultati"]
            
            for cell in worksheet[1]:

                cell.font = Font(bold=True)
                
            for column in worksheet.columns:

                length = max(

                    len(str(cell.value))
                    if cell.value is not None else 0
                    for cell in column

                )

                worksheet.column_dimensions[
                    column[0].column_letter
                ].width = length + 3
            
            worksheet.freeze_panes = "A2"
            
            worksheet.auto_filter.ref = worksheet.dimensions

        with c2:

            st.download_button(
                "📊 Preuzmi Excel",
                buffer.getvalue(),
                file_name="rezultati.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True
            )
        
        st.divider()

        st.caption(
"""
**Izvor podataka**

• Open-Meteo API – vremenska prognoza i Sunčevo zračenje

• ENTSO-E Transparency Platform – day-ahead cijene električne energije
"""
        )
        
# -------------------------------------------------
# TAB O MATEMATIČKOM MODELU
# -------------------------------------------------


with tab_model:

    st.header("Matematički model")

    st.markdown("""
Optimizacija rada baterijskog spremnika formulirana je kao problem
mješovitog cjelobrojnog linearnog programiranja (MILP). Model podržava
dva scenarija rada:

- **PV + baterija** – kućanstvo s vlastitom PV elektranom, baterijom i
  priključkom na mrežu. PV proizvodnja može napajati kućanstvo ili
  puniti bateriju; baterija se prazni isključivo u kućanstvo. Kućanstvo
  može kupovati energiju iz mreže, ali PV se ne izvozi i baterija se ne
  prazni u mrežu. Cilj je minimizirati trošak uvoza energije iz mreže
  uz optimalno korištenje baterije.

- **Baterija spojena na mrežu** – baterija se puni iz elektroenergetske
  mreže u satima nižih cijena te prazni pri višim cijenama radi
  ostvarivanja ekonomske koristi.

U oba scenarija uvažena su fizikalna ograničenja baterije i trošak degradacije.

**Vremenska rezolucija.** Optimizacijsko razdoblje pokriva jedan dan
podijeljen na *T* vremenskih koraka trajanja *Δt*. Zadano je *Δt = 0.25 h*
(15-minutni raster, *T = 96* koraka), no korisnik može odabrati i satni
raster (*Δt = 1 h*, *T = 24*). Sve niže navedene jednadžbe primjenjuju se
u svakom vremenskom koraku *k ∈ {1, …, T}*.
""")

    st.divider()

    # -------------------------------------------------
    # ULAZNI PODACI MODELA
    # -------------------------------------------------

    with st.expander("Ulazni podaci modela"):

        st.markdown("### Model PV proizvodnje")

        st.markdown("""
Snaga PV instalacije u svakom vremenskom koraku računa se linearnim
skaliranjem prema Standard Test Conditions (STC):
""")

        st.latex(r"""
P_{PV}(t)
=
\frac{G(t)}{1000}
\,\eta_{sys}\,
P_{STC}
""")

        st.markdown("""
gdje su:

- **G(t)** – kratkovalno Sunčevo zračenje [W/m²] dohvaćeno iz Open-Meteo
  API-ja. Podržana su dva izvora ovisno o odabiru u sučelju:

  * **Prognoza za sutra** – *Open-Meteo Forecast API*
    ([api.open-meteo.com/v1/forecast](https://api.open-meteo.com/v1/forecast)),
    numerička vremenska prognoza za sljedeći dan.
  * **Povijesni datum** – *Open-Meteo Archive API*
    ([archive-api.open-meteo.com/v1/archive](https://archive-api.open-meteo.com/v1/archive)),
    ERA5 reanaliza koja pokriva razdoblje od 1940. do prije nekoliko
    dana.

  Satne vrijednosti se u oba slučaja linearno interpoliraju na *Δt*.

- **P_STC** – nazivna DC snaga PV instalacije pri STC [kWp]
  (1000 W/m², 25 °C ćelije) – korisnički ulazni podatak

- **η_sys** – ukupni derating sustava (temperatura panela, kablovi,
  inverter, prljavština), tipično 0.80–0.95 – korisnički ulazni podatak.

Odabir povijesnog datuma omogućuje analizu utjecaja stvarnih vremenskih
uvjeta (sunčani ljetni dan / oblačan zimski dan) na rad baterijskog
sustava uz identično zadanu potrošnju i parametre baterije.
""")

        st.markdown("### Profil potrošnje (samo scenarij 1)")

        st.markdown(r"""
Dnevna potrošnja kućanstva zadaje se dvama parametrima:
korisnik unosi **ukupnu dnevnu potrošnju $E_{dan}$ [kWh]** i odabire
**oblik krivulje** iz fiksnog kataloga (rezidencijalni, poslovni, ravni,
noćna smjena). Odabrani predložak $s(t)$ (satne relativne vrijednosti)
linearno se interpolira na traženu vremensku rezoluciju i skalira tako
da vrijedi:
""")

        st.latex(r"""
\sum_{t=1}^{T} P_{load}(t)\,\Delta t = E_{dan}
""")

        st.markdown("""
Time se neovisno mijenjaju iznos i oblik potrošnje, dok apsolutne
vrijednosti unutar predloška nemaju značaj – važan je samo relativni
oblik krivulje.
""")

        st.markdown("### Cijene električne energije")

        st.markdown("""
Day-ahead cijene *c(t)* dohvaćaju se iz *ENTSO-E Transparency Platforma*
za područje Hrvatske (10YHR-HEP------M) u **prirodnoj rezoluciji koju
tržište objavljuje** – PT15M (96 vrijednosti dnevno) na modernim
tržištima, ili PT60M (24 satne vrijednosti) za starije objave. Parser
automatski detektira rezoluciju iz XML-a (`<Period><resolution>`).

Ovisno o odabiru u sučelju:

- **Prognoza za sutra** – dohvaćaju se cijene za sutrašnji dan, uz
  rezervno vraćanje na današnji dan ako sutrašnje objave još nema.
- **Povijesni datum** – dohvaćaju se stvarne day-ahead cijene za
  odabrani datum (dostupno od veljače 2016. kada je HR ušao u
  jedinstveno spajanje tržišta CROPEX-HUPX-EPEX-a).

Cijene se zatim prilagođavaju odabranom koraku simulacije *Δt*:
ako je nativna rezolucija jednaka *Δt*, koriste se direktno; ako je
nativna finija (PT15M s *Δt* = 1 h), susjedne se vrijednosti
usrednjuju; ako je nativna grublja (PT60M s *Δt* = 0.25 h), svaka
satna cijena ponavlja se 4 puta.
""")

    st.divider()

    # -------------------------------------------------
    # FUNKCIJA CILJA
    # -------------------------------------------------

    with st.expander(
        "Funkcija cilja",
        expanded=True
    ):

        st.markdown("### Scenarij 1 – PV + baterija")

        st.latex(r"""
\min
\sum_{t=1}^{T}
\left(
c(t)\,P_{grid}(t)
+
c_{deg}
\left(
P_{ch}(t)+P_{dis}(t)
\right)
\right)
\Delta t
""")

        st.markdown("""
Punjenje baterije odvija se isključivo iz PV proizvodnje te ne
predstavlja trošak kupnje energije iz mreže. Baterija se prazni
isključivo u kućanstvo, a ne u mrežu, pa nema izravnog prihoda od
pražnjenja. Funkcija cilja minimizira trošak uvoza energije iz mreže
i trošak degradacije baterije. Ekonomska korist nastaje neizravno –
kroz smanjenu potrebu za uvozom u satima viših tržišnih cijena.
""")

        st.markdown("### Scenarij 2 – Baterija spojena na mrežu")

        st.latex(r"""
\min
\sum_{t=1}^{T}
\left(
c(t)
\left(
P_{ch}(t)-P_{dis}(t)
\right)
+
c_{deg}
\left(
P_{ch}(t)+P_{dis}(t)
\right)
\right)
\Delta t
""")

        st.markdown("""
U ovom scenariju baterija kupuje električnu energiju iz mreže u satima
nižih tržišnih cijena te se prazni pri višim cijenama radi ostvarivanja
ekonomske koristi. U funkciju cilja uključen je i trošak degradacije
baterije.
""")

        st.markdown("""
gdje je:

- **c(t)** – cijena električne energije u vremenskom koraku *t* [€/kWh]

- **Pch(t)** – snaga punjenja baterije [kW]

- **Pdis(t)** – snaga pražnjenja baterije [kW]

- **Pgrid(t)** – snaga uvoza iz mreže *(samo scenarij 1)* [kW]

- **PPV(t)** – snaga PV proizvodnje *(samo scenarij 1)* [kW]

- **Pload(t)** – snaga potrošnje kućanstva *(samo scenarij 1)* [kW]

- **PPV→load(t)** – snaga PV-a koja izravno napaja potrošnju *(samo scenarij 1)* [kW]

- **Δt** – trajanje vremenskog koraka [h]

- **cdeg** – koeficijent troška degradacije baterije [€/kWh]
""")

    st.divider()

    # -------------------------------------------------
    # SOC
    # -------------------------------------------------

    with st.expander(
        "Jednadžba promjene stanja napunjenosti baterije"
    ):

        st.latex(r"""
SOC(k+1)=SOC(k)+
\left(
\eta_{ch}P_{ch}(k)
-
\frac{P_{dis}(k)}{\eta_{dis}}
\right)
\frac{\Delta t}{E_{max}}
""")

        st.markdown("""
gdje su:

- **ηch** – učinkovitost punjenja baterije

- **ηdis** – učinkovitost pražnjenja baterije

- **Emax** – nazivni kapacitet baterije [kWh]

- **SOC₀** – početno stanje napunjenosti baterije.
""")

    st.divider()

    # -------------------------------------------------
    # OGRANIČENJA
    # -------------------------------------------------

    with st.expander(
        "Ograničenja modela"
    ):

        st.markdown("### Ograničenje stanja napunjenosti")

        st.latex(r"""
SOC_{min}
\le
SOC(k)
\le
SOC_{max}
""")

        st.markdown("""
SOC baterije ograničen je na raspon od **0.2 do 0.9**
radi smanjenja degradacije i produljenja životnog vijeka baterije.
""")

        st.markdown("### Ograničenje snage")

        st.latex(r"""
0\le P_{ch}(k)\le P_{limit}
""")

        st.latex(r"""
0\le P_{dis}(k)\le P_{limit}
""")

        st.markdown("""
Parametar **Pmax** predstavlja najveću dopuštenu priključnu snagu sustava
koju korisnik definira kao ulazni podatak modela.
""")

        st.markdown("### Tehničko ograničenje baterije")

        st.latex(r"""
P_{bat}^{max}
=
C_{rate}\cdot E_{max}
""")

        st.markdown("""
gdje su:

- **Pbatmax** – najveća tehnički dopuštena snaga baterije [kW]

- **Crate** – C-rate baterije [h⁻¹]

- **Emax** – nazivni kapacitet baterije [kWh]
""")

        st.markdown("""
U implementaciji se koristi ograničenje:
""")

        st.latex(r"""
P_{limit}
=
\min
\left(
P_{max},
P_{bat}^{max}
\right)
""")

        st.markdown("""
Na taj način maksimalna dopuštena snaga punjenja i pražnjenja određena je
manjom vrijednošću između korisnički zadane priključne snage sustava i
tehničkog ograničenja baterije.
""")

        st.markdown("### Završno stanje napunjenosti")

        st.latex(r"""
SOC(T)\ge SOC_{0}
""")

        st.markdown("""
Na kraju optimizacijskog razdoblja stanje napunjenosti baterije mora biti
najmanje jednako početnom stanju napunjenosti. To sprječava trivijalno
"prosipanje" baterije koje bi umjetno povećalo prividnu uštedu unutar
jednog dana.
""")

        st.markdown("### Zabrana istodobnog punjenja i pražnjenja")

        st.markdown("""
U heurističkoj simulaciji uvjet da baterija ne može istodobno puniti i
pražniti može se zapisati kao:
""")

        st.latex(r"""
P_{ch}(k)\cdot P_{dis}(k)=0
""")

        st.markdown("""
U MILP formulaciji isti je uvjet implementiran pomoću binarne varijable:
""")

        st.latex(r"""
P_{ch}(k)\le P_{limit}\,u(k)
""")

        st.latex(r"""
P_{dis}(k)\le P_{limit}\left(1-u(k)\right)
""")

        st.latex(r"""
u(k)\in\{0,1\}
""")

        st.markdown("""
gdje je **u(k)** binarna varijabla koja određuje način rada baterije.

- **u(k)=1** → dopušteno je punjenje baterije.
- **u(k)=0** → dopušteno je pražnjenje baterije.

Na taj način u svakom vremenskom koraku može biti aktivan samo jedan način rada baterije.
""")

        st.markdown("### Dodatna ograničenja za PV scenarij")

        st.markdown("**Balans potrošnje** – potrošnja kućanstva pokriva se iz PV-a, pražnjenja baterije i uvoza iz mreže:")

        st.latex(r"""
P_{PV\to load}(k) + P_{dis}(k) + P_{grid}(k)
=
P_{load}(k)
""")

        st.markdown("**Raspodjela PV-a** – PV proizvodnja može istovremeno napajati kućanstvo i puniti bateriju; višak se ne izvozi u mrežu:")

        st.latex(r"""
P_{PV\to load}(k) + P_{ch}(k) \le P_{PV}(k)
""")

        st.markdown("**Nenegativnost varijabli tokova**:")

        st.latex(r"""
P_{PV\to load}(k) \ge 0,\quad
P_{grid}(k) \ge 0
""")

        st.markdown("""
Budući da su sve varijable tokova nenegativne, iz balansa potrošnje
automatski slijedi da pražnjenje baterije ne može premašiti potrebu
kućanstva – tj. baterija ne prazni u mrežu. Slično, iz nejednakosti
raspodjele PV-a slijedi da se višak PV-a nakon napajanja potrošnje i
punjenja baterije jednostavno odbacuje (curtailment).
""")
        
        st.markdown("### Heuristički algoritam")

        st.markdown("""
Kao alternativa MILP optimizaciji implementiran je heuristički algoritam
temeljen na unaprijed definiranim pravilima odlučivanja.
Za razliku od MILP pristupa, heuristički algoritam ne rješava optimizacijski
problem niti traži globalno optimalno rješenje, već odluke o punjenju i pražnjenju
donosi prema unaprijed definiranim pravilima.

- U scenariju **PV + baterija** primjenjuje se strategija maksimalne
  samopotrošnje (*self-consumption*). U svakom vremenskom koraku
  redoslijedom odlučivanja:
  1. PV najprije napaja potrošnju kućanstva,
  2. višak PV-a puni bateriju do gornje granice SOC-a,
  3. ako PV ne pokriva potrošnju, baterija se prazni za nadoknadu
     nedostatka do dostupne energije baterije,
  4. preostali dio potrošnje pokriva se uvozom iz mreže.

  Cijena električne energije ne utječe izravno na odluke – ušteda
  nastaje kroz smanjeni uvoz u satima viših cijena.

- U scenariju **Baterija spojena na mrežu** punjenje se provodi tijekom
  najjeftinijih vremenskih koraka koji ukupno pokrivaju približno 4 sata
  (16 slotova za 15-min raster, 4 slota za satni raster), dok se
  pražnjenje provodi tijekom najskupljih vremenskih koraka jednake
  ukupne duljine.

Tijekom simulacije heuristički algoritam poštuje ista fizikalna ograničenja
kao i MILP model, uključujući ograničenja stanja napunjenosti baterije,
maksimalne snage punjenja i pražnjenja te uvjet da završno stanje
napunjenosti baterije ne smije biti manje od početnog.

Punjenje i pražnjenje dodatno su ograničeni raspoloživim kapacitetom baterije,
maksimalnom dopuštenom snagom punjenja i pražnjenja te
uvjetom da završno stanje napunjenosti baterije ne bude manje od početnog.
""")

    st.divider()

    # -------------------------------------------------
    # IZRAČUN UŠTEDE
    # -------------------------------------------------

    with st.expander(
        "Izračun uštede (samo scenarij 1)"
    ):

        st.markdown("""
U scenariju **PV + baterija** ušteda se ne pojavljuje kao izravan prihod
od pražnjenja (baterija ne prodaje energiju u mrežu), već kao **razlika
u trošku uvoza** u odnosu na referentnu situaciju bez baterije.

**Referentni (baseline) scenarij bez baterije** – PV izravno napaja
potrošnju, a preostali dio potrošnje pokriva se uvozom iz mreže:
""")

        st.latex(r"""
P_{grid}^{base}(t)
=
\max\bigl(
0,\;
P_{load}(t)-\min\bigl(P_{PV}(t),\,P_{load}(t)\bigr)
\bigr)
""")

        st.latex(r"""
C_{base}
=
\sum_{t=1}^{T}
c(t)\,P_{grid}^{base}(t)\,\Delta t
""")

        st.markdown("""
**Optimizirani scenarij (s baterijom)** – ukupni trošak koji minimizira
funkcija cilja (uvoz + degradacija):
""")

        st.latex(r"""
C_{bat}
=
\sum_{t=1}^{T}
\left(
c(t)\,P_{grid}(t)
+
c_{deg}\bigl(P_{ch}(t)+P_{dis}(t)\bigr)
\right)\Delta t
""")

        st.markdown("**Dnevna ušteda:**")

        st.latex(r"""
\Delta C = C_{base} - C_{bat}
""")

        st.markdown("""
Pozitivna vrijednost *ΔC* znači da uporaba baterije donosi financijsku
korist – smanjeni trošak uvoza premašuje trošak degradacije. Ušteda
raste kada se vrhovi potrošnje poklapaju sa satima viših cijena, jer
baterija tada zamjenjuje skupi uvoz jeftinijom energijom uskladištenom
iz PV-a.
""")

    st.divider()

    st.info("""
Model je implementiran kao problem mješovitog cjelobrojnog linearnog
programiranja (MILP), pri čemu se optimizacija rješava pomoću biblioteke
PuLP i CBC solvera. Kao referentna metoda implementiran je i heuristički
algoritam koji koristi unaprijed definirana pravila punjenja i pražnjenja
baterije bez rješavanja optimizacijskog problema. Usporedbom rezultata
obaju pristupa moguće je procijeniti prednosti optimizacijskog modela u
odnosu na jednostavnu heurističku strategiju upravljanja baterijom.
""")
    
    # -------------------------------------------------
    # TAB O APLIKACIJI 
    #------------------------------------------------

with tab_about:

    st.header("O aplikaciji")

    st.markdown("""
Aplikacija omogućuje optimizaciju rada baterijskog spremnika (BESS)
u dva scenarija rada:

- **PV + baterija** – kućanstvo s vlastitom PV elektranom, baterijom i
  priključkom na elektroenergetsku mrežu. PV proizvodnja može napajati
  potrošnju ili puniti bateriju; baterija se prazni isključivo u
  kućanstvo. Uvoz iz mreže je dopušten, izvoz i pražnjenje baterije
  u mrežu nisu.
- **Baterija spojena na mrežu** – baterija kupuje energiju iz mreže u
  satima nižih cijena i prazni je u mrežu pri višim cijenama radi
  ostvarivanja arbitražne dobiti.

### Ključne značajke

- **MILP optimizacija** (PuLP + CBC solver) s degradacijom i binarnim
  ograničenjem istovremenog punjenja/pražnjenja.
- **Heuristička referentna metoda**: samopotrošnja (PV scenarij) ili
  odabir najjeftinijih/najskupljih koraka (grid scenarij).
- **15-minutni raster** (Δt = 0.25 h, 96 vremenskih koraka po danu),
  s podrškom i za satni raster.
- **Katalog profila potrošnje** kućanstva: rezidencijalni s večernjim
  vrhom, poslovni s dnevnim vrhom, ravni (industrijski), noćna smjena.
- **Analiza povijesnih dana** – Open-Meteo Archive (ERA5) + ENTSO-E
  povijesne cijene, za usporedbu scenarija pri različitim vremenskim
  i tržišnim uvjetima.
- **Izračun uštede** u odnosu na baseline scenarij bez baterije.

### Korištene tehnologije

- Python
- Streamlit (interaktivno sučelje)
- PuLP + CBC solver (MILP optimizacija)
- Plotly (interaktivni grafovi)
- Open-Meteo Forecast API (prognoza Sunčevog zračenja)
- Open-Meteo Archive API (povijesna ERA5 reanaliza)
- ENTSO-E Transparency Platform (day-ahead cijene, prognozne i povijesne)

### Završni rad
Fakultet elektrotehnike, strojarstva i brodogradnje (FESB)
Sveučilište u Splitu

Računarstvo (120)

Autor: Antonija Kežić

Mentor: Ivo Marinić-Kragić

Akademska godina: 2025./2026.
""")