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
    scenario

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

        # Punjenje samo iz PV
        if scenario == "PV + baterija":
            problem += (
                p_charge[t] <= p_pv[t],    #Punjenje baterije ograničeno je dostupnom PV proizvodnjom
                f"PV_limit_{t}"
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

        problem += lpSum(

            (

                c_deg
                *
                (p_charge[t] + p_discharge[t])
                * dt

                -

                (prices[t] / 1000)
                *
                p_discharge[t]
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

    return (
        soc_values,
        charge,
        discharge
    )