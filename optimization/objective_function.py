def objective_function(

    prices,
    p_charge,
    p_discharge,
    dt,
    c_deg

):

    total_cost = 0

    for hour in range(len(prices)):
        
        price = prices[hour] / 1000

        energy_cost = (price * (p_charge[hour] - p_discharge[hour]) * dt)

        degradation_cost = (c_deg * (p_charge[hour] + p_discharge[hour]) * dt)

        total_cost += (energy_cost + degradation_cost)


    return total_cost