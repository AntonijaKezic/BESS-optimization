def hourly_cost_pv(

    prices,
    p_charge,
    p_discharge,
    dt,
    c_deg

):

    costs=[]

    for h in range(len(prices)):

        price = prices[h]/1000

        benefit = price * p_discharge[h] * dt

        degradation = c_deg * (

            p_charge[h]
            +
            p_discharge[h]

        ) * dt

        costs.append(

            degradation
            -
            benefit

        )

    return costs