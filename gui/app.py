import sys
from pathlib import Path
from io import BytesIO

from openpyxl.styles import Font

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from run_model import run_model

from plots import (
    plot_soc,
    plot_pv,
    plot_prices,
    plot_power,
    plot_costs
)

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

    eta_pv = st.slider(
        "Učinkovitost PV",
        0.05,
        0.30,
        0.20,
        0.01
    )

    p_nom_pv = st.number_input(
        "Nazivna snaga PV [kW]",
        value=10.0
    )

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
        "Maksimalna snaga [kW]",
        value=10.0
    )

    dt = st.number_input(
        "Korak simulacije [h]",
        value=1.0
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
    
    if "results" not in st.session_state:

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
            use_milp
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
                use_milp
        )

# -------------------------------------------------
# POKRETANJE MODELA
# -------------------------------------------------

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
            use_milp
        )

# -------------------------------------------------
# PRIKAZ REZULTATA
# -------------------------------------------------

with tab_results:

    if "results" in st.session_state:

        results = st.session_state["results"]

        if results["price_day"] == "today":
            st.warning(
            "Sutrašnje cijene nisu bile dostupne. Korištene su današnje cijene."
        )
            

    # -------------------------------------------------
    # KPI
    # -------------------------------------------------

        c1, c2, c3, c4 = st.columns(4)

        c1.metric(
            "Ukupan trošak",
            f"{results['cost']:.2f} €"
        )

        c2.metric(
            "Završni SOC",
            f"{results['soc'][-1]:.2f}"
        )

        c3.metric(
            "Maksimalna PV snaga",
            f"{max(results['pv']):.2f} kW"
        )

        c4.metric(
            "Ukupna PV energija",
            f"{sum(results['pv']):.2f} kWh"
        )
        
        c5, c6, c7 = st.columns(3)
        
        c5.metric(
            "Prosječna cijena",
            f"{sum(results['prices'])/24:.2f} €/MWh"
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

            st.plotly_chart(
                plot_soc(results["soc"]),
                use_container_width=True
            )

            st.plotly_chart(
                plot_prices(results["prices"]),
                use_container_width=True
            )

        with right:

            st.plotly_chart(
                plot_pv(results["pv"]),
                use_container_width=True
            )

            st.plotly_chart(
                plot_power(
                    results["p_charge"],
                    results["p_discharge"]
                ),
                use_container_width=True
            )

        st.plotly_chart(
            plot_costs(results["hourly_costs"]),
            use_container_width=True
        )

        st.divider()
        
        st.subheader("Analiza rezultata")
        
        min_price = min(results["prices"])
        max_price = max(results["prices"])

        min_hour = results["prices"].index(min_price)
        max_hour = results["prices"].index(max_price)
        
        st.markdown(f"""
        Najniža tržišna cijena iznosila je **{min_price:.2f} €/MWh**
        u **{min_hour:02d}:00 h**.

        Najviša tržišna cijena iznosila je **{max_price:.2f} €/MWh**
        u **{max_hour:02d}:00 h**.

        Ukupna proizvedena energija iz fotonaponske elektrane
        iznosi **{sum(results["pv"]):.2f} kWh**.

        Ukupan trošak optimizacije iznosi
        **{results["cost"]:.2f} €**.
        """)

    # -------------------------------------------------
    # TABLICA
    # -------------------------------------------------

        st.subheader("Rezultati po satima")

        df = pd.DataFrame({

            "Razdoblje": [
                f"{h:02d}:00 - {(h+1)%24:02d}:00"
                for h in range(24)
            ],
            "PV [kW]": results["pv"],
            "Cijena [€/MWh]": results["prices"],
            "Punjenje [kW]": results["p_charge"],
            "Pražnjenje [kW]": results["p_discharge"],
            "SOC": results["soc"][:-1],
            "Trošak [€]": results["hourly_costs"]
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
        

with tab_model:

    st.header("Matematički model")

    st.markdown("""
Optimizacija rada baterijskog spremnika formulirana je kao problem
mješovitog cjelobrojnog linearnog programiranja (MILP). Cilj optimizacije
je minimizirati ukupni trošak rada baterijskog spremnika uz uvažavanje
troška degradacije baterije i svih fizikalnih ograničenja sustava.
""")

    st.divider()

    # -------------------------------------------------
    # FUNKCIJA CILJA
    # -------------------------------------------------
    
    with st.expander(
        "Ciljna funkcija",
        expanded=True
    ):

        st.latex(r"""
\min f(x)=
\sum_{t=1}^{24}
c(t)\left(
P_{ch}(t)-P_{dis}(t)
\right)\Delta t
+
c_{deg}
\sum_{t=1}^{24}
\left(
P_{ch}(t)+P_{dis}(t)
\right)\Delta t
""")

        st.markdown("""
gdje je:

- **f(x)** – ukupni trošak sustava [€]

- **c(t)** – cijena električne energije u vremenskom koraku *t* [€/kWh]

- **Δt** – trajanje vremenskog koraka [h]

- **c₍deg₎** – koeficijent troška degradacije baterije [€/kWh]

- **Pch(t)+Pdis(t)** – aproksimacija ukupne prenesene energije kroz bateriju.
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
\frac{1}{\eta_{dis}}P_{dis}(k)
\right)
\frac{\Delta t}{E_{max}}
""")

        st.markdown("""
gdje su:

- **Pch(k)** ≥ 0 i **Pdis(k)** ≥ 0 snage punjenja i pražnjenja baterije u vremenskom koraku *k*

- **ηch** i **ηdis** učinkovitosti punjenja i pražnjenja baterije

- **SOC₀** početno stanje napunjenosti baterije.
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
Ovo ograničenje sprječava prekomjerno punjenje i duboko pražnjenje
baterije. U modelu se koristi raspon od **0.2 do 0.9** kako bi se
smanjila degradacija baterije.
""")

        st.markdown("### Ograničenje snage")

        st.latex(r"""
0\le P_{ch}(k)\le P_{ch}^{max}
""")

        st.latex(r"""
0\le P_{dis}(k)\le P_{dis}^{max}
""")

        st.markdown("""
Pretpostavlja se:

""")

        st.latex(r"""
P_{ch}^{max}
=
P_{dis}^{max}
=
P_{max}
""")

        st.markdown("""
Maksimalna snaga dodatno je ograničena priključnom snagom mreže.
""")

        st.latex(r"""
P_{max}
\le
P_{conn}^{max}
""")

        st.markdown("### Maksimalna snaga baterije")

        st.latex(r"""
P_{max}
=
C_{rate}
\cdot
E_{max}
""")

        st.markdown("""
gdje su:

- **Pmax** – maksimalna snaga punjenja i pražnjenja [kW]

- **Crate** – C-rate baterije [h⁻¹]

- **Emax** – kapacitet baterije [kWh]
""")

        st.markdown("""
Primjer:

Ako je

- **Crate = 0.5**

- **Emax = 200 kWh**

tada je maksimalna snaga

**Pmax = 100 kW**.
""")

        st.markdown("### Komplementarnost")

        st.markdown("""
Kako bi se spriječilo istodobno punjenje i pražnjenje baterije,
uvodi se uvjet komplementarnosti:
""")

        st.latex(r"""
P_{ch}(k)\cdot P_{dis}(k)=0
""")

    st.divider()

    st.info(
        """
Model je implementiran kao problem mješovitog cjelobrojnog linearnog
programiranja (MILP), a optimizacija se rješava pomoću biblioteke
PuLP i CBC solvera.
"""
    )
    
    
with tab_about:

    st.header("O aplikaciji")

    st.markdown("""
Aplikacija omogućuje optimizaciju rada baterijskog spremnika
spojenog na fotonaponsku elektranu. Model predstavlja linearni optimizacijski problem (MILP)
kojim se određuje optimalno punjenje i pražnjenje
baterijskog spremnika uz minimizaciju ukupnog troška.

Korištene tehnologije

- Python
- Streamlit
- PuLP (MILP optimizacija)
- Open-Meteo API
- ENTSO-E Transparency Platform

### Završni rad
Fakultet elektrotehnike, strojarstva i brodogradnje (FESB)
Sveučilište u Splitu
\n
Računarstvo (120)\n
Autor: Antonija Kežić\n
Mentor: Ivo Marinić-Kragić\n
Akademska godina: 2025./2026.
""")   