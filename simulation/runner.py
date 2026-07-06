from models.battery import (
    max_battery_power,
    update_soc,
    limit_power,
    SOC_MAX,
    SOC_MIN
)


def simulate_battery(

    soc0,
    p_pv,
    prices,
    p_max,
    eta_ch,
    eta_dis,
    dt,
    e_max,
    c_rate,
    scenario

):

    soc = [soc0]

    p_charge = []

    p_discharge = []

    current_soc = soc0

    p_limit = min(
        p_max,
        max_battery_power(
            c_rate,
            e_max
        )
    )

    # ----------------------------------------
    # Heuristički odabir sati
    # ----------------------------------------

    cheap_hours = sorted(
        range(len(prices)),
        key=lambda i: prices[i]
    )[:4]

    expensive_hours = sorted(
        range(len(prices)),
        key=lambda i: prices[i],
        reverse=True
    )[:4]

    # ----------------------------------------
    # Simulacija
    # ----------------------------------------

    for hour in range(len(prices)):

        charge = 0.0
        discharge = 0.0

        # Maksimalna energija koju još možemo pohraniti

        available_capacity = (
            (SOC_MAX - current_soc)
            * e_max
        )

        # Energija trenutno pohranjena iznad SOC_MIN

        stored_energy = (
            (current_soc - SOC_MIN)
            * e_max
        )

        # Energija koju moramo ostaviti da završni SOC
        # bude barem jednak početnom

        required_energy = max(
            0,
            (soc0 - SOC_MIN)
            * e_max
        )

        # Energija koju smijemo isprazniti

        available_for_discharge = max(
            0,
            stored_energy - required_energy
        )

        # -----------------------------------
        # PV + baterija
        # -----------------------------------

        if scenario == "PV + baterija":

            # Punjenje samo iz PV

            if p_pv[hour] > 0 and current_soc < SOC_MAX:

                charge = min(

                    p_pv[hour],

                    p_limit,

                    available_capacity
                    /
                    (eta_ch * dt)

                )

            # Pražnjenje samo u najskupljim satima

            elif (
                hour in expensive_hours
                and available_for_discharge > 0
            ):

                discharge = min(

                    p_limit,

                    available_for_discharge
                    *
                    eta_dis
                    /
                    dt

                )

        # -----------------------------------
        # Baterija spojena na mrežu
        # -----------------------------------

        else:

            # Punjenje u najjeftinijim satima

            if (
                hour in cheap_hours
                and current_soc < SOC_MAX
            ):

                charge = min(

                    p_limit,

                    available_capacity
                    /
                    (eta_ch * dt)

                )

            # Pražnjenje u najskupljim satima

            elif (
                hour in expensive_hours
                and available_for_discharge > 0
            ):

                discharge = min(

                    p_limit,

                    available_for_discharge
                    *
                    eta_dis
                    /
                    dt

                )

        charge = limit_power(
            charge,
            p_limit
        )

        discharge = limit_power(
            discharge,
            p_limit
        )

        current_soc = update_soc(

            current_soc,

            charge,

            discharge,

            eta_ch,

            eta_dis,

            dt,

            e_max

        )

        p_charge.append(charge)
        p_discharge.append(discharge)
        soc.append(current_soc)

    return (
        soc,
        p_charge,
        p_discharge
    )