def hourly_economic_effect(
    prices,
    p_charge,
    p_discharge,
    dt,
    c_deg
):

    effects = []

    for t in range(len(prices)):

        value = (

            (prices[t] / 1000)
            *
            (p_discharge[t] - p_charge[t])
            *
            dt

            -

            c_deg
            *
            (p_charge[t] + p_discharge[t])
            *
            dt

        )

        effects.append(value)

    return effects