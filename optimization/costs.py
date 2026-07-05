def hourly_cost(

    prices,
    p_charge,
    p_discharge,
    dt,
    c_deg

):

    costs=[]

    for hour in range(len (prices)):
        
        price = prices[hour] / 1000

        energy=(price * (p_charge[hour] - p_discharge[hour]) * dt)

        degradation=(c_deg * (p_charge[hour] + p_discharge[hour]) * dt)

        costs.append(
            energy + degradation
        )

    return costs