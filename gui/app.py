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
    plot_soc_pv,
    plot_soc_grid,
    plot_pv,
    plot_prices,
    plot_power_pv,
    plot_power_grid,
    plot_costs,
    plot_costs_pv
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
    
    scenario = st.radio(

        "Scenarij rada",

        [

            "PV + baterija",

            "Baterija spojena na mrežu"

        ]
    )

    if scenario == "PV + baterija":

        eta_pv = st.slider(
            "Učinkovitost PV [%]",

            0.10,

            0.25,

            0.20,

            0.01
        )

        p_nom_pv = st.number_input(
            "Nazivna snaga PV [kW]",
            value=10.0
        )

    else:

        eta_pv = None

        p_nom_pv = None

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
    
    if (
    "results" not in st.session_state
    or st.session_state.get("scenario") != scenario
    ):

        st.session_state["scenario"] = scenario

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
                scenario,
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

        if scenario=="PV + baterija":

            c3.metric(

                "Maksimalna PV snaga",

                f"{max(results['pv']):.2f} kW"

            )

            c4.metric(

                "Ukupna PV energija",

                f"{sum(results['pv']):.2f} kWh"

            )

        else:

            c3.metric(

                "Maksimalna snaga punjenja",

                f"{max(results['p_charge']):.2f} kW"

            )

            c4.metric(

                "Ukupna energija punjenja",

                f"{sum(results['p_charge']):.2f} kWh"

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
                plot_costs_pv(
                    results["hourly_costs"]
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

        min_hour = results["prices"].index(min_price)
        max_hour = results["prices"].index(max_price)
        
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
                f"**{sum(results['pv']):.2f} kWh**."
            )

        else:

            pv_text = ""

        st.markdown(f"""
        Najniža tržišna cijena iznosila je **{min_price:.2f} €/MWh**
        u **{min_hour:02d}:00 h**.

        Najviša tržišna cijena iznosila je **{max_price:.2f} €/MWh**
        u **{max_hour:02d}:00 h**.
        
        {pv_text}
        {economic_result}
        """)

        

    
    # -------------------------------------------------
    # TABLICA
    # -------------------------------------------------

        st.subheader("Rezultati po satima")

        if scenario == "PV + baterija":

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

            "Ušteda [€]": [abs(x) if x < 0 else 0 for x in results["hourly_costs"]]

        })

        else:

            df = pd.DataFrame({

            "Razdoblje": [
                f"{h:02d}:00 - {(h+1)%24:02d}:00"
                for h in range(24)
            ],

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

- **PV + baterija** – baterija se puni isključivo iz fotonaponske elektrane te se
  prazni u satima viših tržišnih cijena električne energije.

- **Baterija spojena na mrežu** – baterija se puni iz elektroenergetske mreže u
  te se prazni radi ostvarivanja ekonomske koristi
  uzimajući u obzir tržišne cijene električne energije.

U oba scenarija uvažena su fizikalna ograničenja baterije i trošak degradacije.
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
\sum_{t=1}^{24}
\left(
c_{deg}
\left(
P_{ch}(t)+P_{dis}(t)
\right)
-
c(t)P_{dis}(t)
\right)
\Delta t
""")

        st.markdown("""
Punjenje baterije odvija se isključivo iz fotonaponske elektrane te ne
predstavlja trošak kupnje električne energije iz mreže. Funkcija cilja
minimizira trošak degradacije baterije i minimizira ukupni trošak rada 
baterije, pri čemu se ostvaruje ekonomska korist korištenjem prethodno 
pohranjene energije u satima viših tržišnih cijena."
""")

        st.markdown("### Scenarij 2 – Baterija spojena na mrežu")

        st.latex(r"""
\min
\sum_{t=1}^{24}
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
SOC_{24}\ge SOC_{0}
""")

        st.markdown("""
Na kraju optimizacijskog razdoblja stanje napunjenosti baterije mora biti
najmanje jednako početnom stanju napunjenosti.
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

        st.markdown("### Dodatno ograničenje za PV scenarij")

        st.latex(r"""
P_{ch}(k)\le P_{PV}(k)
""")

        st.markdown("""
U scenariju **PV + baterija** snaga punjenja ograničena je raspoloživom
proizvodnjom fotonaponske elektrane.
""")
        
        st.markdown("### Heuristički algoritam")

        st.markdown("""
Kao alternativa MILP optimizaciji implementiran je heuristički algoritam
temeljen na unaprijed definiranim pravilima odlučivanja.
Za razliku od MILP pristupa, heuristički algoritam ne rješava optimizacijski 
problem niti traži globalno optimalno rješenje, već odluke o punjenju i pražnjenju 
donosi prema unaprijed definiranim pravilima.

- U scenariju **PV + baterija** baterija se puni isključivo iz raspoložive
  proizvodnje fotonaponske elektrane, dok se pražnjenje provodi tijekom
  četiri sata s najvišom tržišnom cijenom električne energije.

- U scenariju **Baterija spojena na mrežu** punjenje se provodi tijekom
  četiri sata s najnižom cijenom električne energije, dok se pražnjenje
  provodi tijekom četiri sata s najvišom cijenom.

Tijekom simulacije heuristički algoritam poštuje ista fizikalna ograničenja
kao i MILP model, uključujući ograničenja stanja napunjenosti baterije,
maksimalne snage punjenja i pražnjenja te uvjet da završno stanje
napunjenosti baterije ne smije biti manje od početnog.

Punjenje i pražnjenje dodatno su ograničeni raspoloživim kapacitetom baterije, 
maksimalnom dopuštenom snagom punjenja i pražnjenja te 
uvjetom da završno stanje napunjenosti baterije ne bude manje od početnog.
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
Aplikacija omogućuje optimizaciju rada baterijskog 
spremnika u dva scenarija: baterija spojena na 
fotonaponsku elektranu ili baterija spojena 
izravno na elektroenergetsku mrežu.

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