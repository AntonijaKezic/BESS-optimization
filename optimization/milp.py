from pulp import (
    LpProblem,
    LpMinimize,
    LpVariable,
    lpSum,
    PULP_CBC_CMD,
    LpStatus,
    value
)

from models.battery import (
    SOC_MIN,
    SOC_MAX,
    max_battery_power
)


def optimize_battery(

    prices,
    p_pv,
    soc0,
    e_max,
    eta_ch,
    eta_dis,
    p_max,
    c_rate,
    c_deg,
    dt,
    scenario,
    p_load=None

):

    problem = LpProblem(
        "Battery_Optimization",
        LpMinimize
    )

    soc_hours = range(len(prices) + 1)

    hours = range(len(prices))

    if len(prices) != len(p_pv):
            raise ValueError(
            "Broj cijena i PV proizvodnje mora biti jednak."
        )

    if scenario == "PV + baterija":

        if p_load is None:

            raise ValueError(
                "Profil potrošnje (p_load) obavezan je za scenarij "
                "'PV + baterija'."
            )

        if len(p_load) != len(prices):

            raise ValueError(
                "Broj sati potrošnje i cijena mora biti jednak."
            )

    p_limit = min(
        p_max,
        max_battery_power(
            c_rate,
            e_max
        )
    )

    p_charge = LpVariable.dicts(
        "P_charge",
        hours,
        lowBound=0,
        upBound=p_limit
    )

    p_discharge = LpVariable.dicts(
        "P_discharge",
        hours,
        lowBound=0,
        upBound=p_limit
    )

    soc = LpVariable.dicts(
        "SOC",
        soc_hours,
        lowBound=SOC_MIN,
        upBound=SOC_MAX
    )

    is_charging = LpVariable.dicts(
        "IsCharging",
        hours,
        cat="Binary"
    )

    # PV-to-load i uvoz iz mreže uvode se samo u PV scenariju
    if scenario == "PV + baterija":

        p_pv_load = LpVariable.dicts(
            "P_pv_load",
            hours,
            lowBound=0
        )

        p_grid_imp = LpVariable.dicts(
            "P_grid_imp",
            hours,
            lowBound=0
        )

    # -------------------
    # POČETNI SOC
    # -------------------

    problem += (
        soc[0] == soc0,
        "Initial_SOC"
    )

    problem += (
        soc[len(prices)] >= soc0,    #Završni SOC mora biti najmanje jednak početnom SOC-u
        "Final_SOC"
    )

    # -------------------
    # OGRANIČENJA
    # -------------------

    for t in hours:

        # Dinamika SOC-a
        problem += (
            soc[t + 1]
            ==
            soc[t]
            +
            (
                eta_ch * p_charge[t]
                -
                p_discharge[t] / eta_dis
            )
            * dt
            / e_max,
            f"SOC_balance_{t}"
        )

        if scenario == "PV + baterija":

            # PV se raspoređuje na potrošnju i punjenje baterije;
            # višak (ako postoji) se ne izvozi u mrežu (curtailment).
            problem += (
                p_pv_load[t] + p_charge[t] <= p_pv[t],
                f"PV_split_{t}"
            )

            # Balans potrošnje - potrošnja se pokriva iz PV-a,
            # pražnjenja baterije i uvoza iz mreže. Budući da su
            # sve varijable >= 0, ovaj balans ujedno onemogućava
            # slanje viška discharge-a u mrežu.
            problem += (
                p_pv_load[t] + p_discharge[t] + p_grid_imp[t]
                ==
                p_load[t],
                f"Load_balance_{t}"
            )

        # Punjenje ili pražnjenje - istovremeno nije dopusteno
        problem += (
            p_charge[t]
            <=
            p_limit * is_charging[t],
            f"Charging_limit_{t}"
        )

        problem += (
            p_discharge[t]
            <=
            p_limit * (1 - is_charging[t]),
            f"Discharging_limit_{t}"
        )

    # -------------------
# FUNKCIJA CILJA
# -------------------

    if scenario == "PV + baterija":

        # Trošak uvoza iz mreže + trošak degradacije baterije.
        # Nema izravne "koristi" od pražnjenja jer se baterija ne
        # prazni u mrežu - ušteda se ostvaruje kroz smanjeni uvoz.
        problem += lpSum(

            (

                (prices[t] / 1000)
                *
                p_grid_imp[t]
                * dt

                +

                c_deg
                *
                (p_charge[t] + p_discharge[t])
                * dt

            )

            for t in hours

        ), "Total_Cost"

    else:

        problem += lpSum(

            (

                (prices[t] / 1000)
                *
                (p_charge[t] - p_discharge[t])
                * dt

                +

                c_deg
                *
                (p_charge[t] + p_discharge[t])
                * dt

            )

            for t in hours

        ), "Total_Cost"

    # -------------------
    # RJEŠAVANJE
    # -------------------

    problem.solve(

        PULP_CBC_CMD(
            msg=False,
            timeLimit=30
        )

    )

    if LpStatus[problem.status] != "Optimal":

        raise ValueError(
            "Optimalno rješenje nije pronađeno."
        )

    # -------------------
    # REZULTATI
    # -------------------

    charge = [

        value(p_charge[t])

        for t in hours

    ]

    discharge = [

        value(p_discharge[t])

        for t in hours

    ]

    soc_values = [

        value(soc[t])

        for t in  soc_hours

    ]

    if scenario == "PV + baterija":

        pv_load = [value(p_pv_load[t]) for t in hours]

        grid_imp = [value(p_grid_imp[t]) for t in hours]

        return (
            soc_values,
            charge,
            discharge,
            pv_load,
            grid_imp
        )

    return (
        soc_values,
        charge,
        discharge
    )
