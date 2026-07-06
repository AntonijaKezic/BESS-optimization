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
    scenario,
    p_load=None

):

    soc = [soc0]

    p_charge = []

    p_discharge = []

    pv_to_load_list = []

    grid_imp_list = []

    current_soc = soc0

    p_limit = min(
        p_max,
        max_battery_power(
            c_rate,
            e_max
        )
    )

    # ----------------------------------------
    # Heuristički odabir sati (samo za grid scenarij).
    # Cilja ~4 sata jeftinih/skupih neovisno o rezoluciji dt -
    # za 15-min raster to je 16 slotova.
    # ----------------------------------------

    n_target_slots = max(1, int(round(4.0 / dt)))

    cheap_hours = sorted(
        range(len(prices)),
        key=lambda i: prices[i]
    )[:n_target_slots]

    expensive_hours = sorted(
        range(len(prices)),
        key=lambda i: prices[i],
        reverse=True
    )[:n_target_slots]

    # ----------------------------------------
    # Simulacija
    # ----------------------------------------

    for hour in range(len(prices)):

        charge = 0.0
        discharge = 0.0
        pv_to_load = 0.0
        grid_imp = 0.0

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
        # PV + baterija (self-consumption)
        # -----------------------------------

        if scenario == "PV + baterija":

            if p_load is None:

                raise ValueError(
                    "Profil potrošnje (p_load) obavezan je za "
                    "scenarij 'PV + baterija'."
                )

            load = p_load[hour]

            pv = p_pv[hour]

            # 1) PV prvo pokriva potrošnju

            pv_to_load = min(pv, load)

            pv_surplus = pv - pv_to_load
            load_deficit = load - pv_to_load

            # 2) Višak PV-a puni bateriju (višak preko toga se ne
            #    izvozi u mrežu - curtailment)

            if pv_surplus > 0 and current_soc < SOC_MAX:

                charge = min(

                    pv_surplus,

                    p_limit,

                    available_capacity
                    /
                    (eta_ch * dt)

                )

            # 3) Kad PV ne pokriva potrošnju, baterija se prazni
            #    da nadoknadi nedostatak

            if load_deficit > 0 and available_for_discharge > 0:

                discharge = min(

                    load_deficit,

                    p_limit,

                    available_for_discharge
                    *
                    eta_dis
                    /
                    dt

                )

            # 4) Preostali dio potrošnje pokriva se iz mreže

            grid_imp = max(
                0.0,
                load_deficit - discharge
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
        pv_to_load_list.append(pv_to_load)
        grid_imp_list.append(grid_imp)
        soc.append(current_soc)

    if scenario == "PV + baterija":

        return (
            soc,
            p_charge,
            p_discharge,
            pv_to_load_list,
            grid_imp_list
        )

    return (
        soc,
        p_charge,
        p_discharge
    )
