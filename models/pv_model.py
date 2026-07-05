def pv_output(
    gti,
    eta_pv,
    p_nom_pv
):

    return (
        gti
        / 1000
        * eta_pv
        * p_nom_pv
    )