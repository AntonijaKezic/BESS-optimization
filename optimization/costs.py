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

def hourly_cost_components(

    prices,
    p_charge,
    p_discharge,
    dt,
    c_deg

):

    charge_costs = []

    discharge_benefits = []

    for h in range(len(prices)):

        price = prices[h] / 1000

        charge = (
            price * p_charge[h] * dt
            +
            c_deg * p_charge[h] * dt
        )

        discharge = (
            price * p_discharge[h] * dt
            -
            c_deg * p_discharge[h] * dt
        )

        charge_costs.append(charge)

        discharge_benefits.append(discharge)

    return charge_costs, discharge_benefits