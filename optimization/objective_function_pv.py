def objective_function_pv(

    prices,

    p_charge,

    p_discharge,

    dt,

    c_deg

):

    total=0

    for h in range(len(prices)):

        price=prices[h]/1000

        benefit=price*p_discharge[h]*dt

        degradation=c_deg*(

            p_charge[h]

            +

            p_discharge[h]

        )*dt

        total += (

            degradation

            -

            benefit

        )

    return total