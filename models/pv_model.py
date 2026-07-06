def pv_output(
    gti,
    eta_pv,
    p_nom_pv
):
    """Snaga PV instalacije [kW] pri trenutnom Sunčevom zračenju.

    Parametri
    ---------
    gti : float
        Kratkovalno zračenje [W/m²] iz Open-Meteo prognoze.
    eta_pv : float
        Derating cijelog sustava [-]: temperatura panela, gubici u
        kablovima, inverter, prljavština. Tipično 0.80-0.90.
    p_nom_pv : float
        Nazivna DC snaga PV instalacije pri STC [kWp] (1000 W/m²,
        25 °C ćelije) - vrijednost s tablice inverter-panel sustava.

    Model: linearno skaliranje na STC.

        P_pv = (gti / 1000) * p_nom_pv * eta_pv
    """

    return (
        gti
        / 1000
        * eta_pv
        * p_nom_pv
    )
