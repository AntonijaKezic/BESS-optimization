SOC_MIN = 0.20
SOC_MAX = 0.90

def update_soc( #Izračunava novo stanje napunjenosti baterije
    
    soc,
    p_ch,
    p_dis,
    eta_ch,
    eta_dis,
    dt,
    e_max
):

    soc_next = (

        soc + (eta_ch * p_ch - p_dis / eta_dis ) * dt / e_max
    )
    return max(SOC_MIN, min(soc_next, SOC_MAX))
    
def max_battery_power(
    
        c_rate,
        e_max
    ):
        return c_rate * e_max

def limit_power(
    power,
    p_max
):
    return max(0, min(power, p_max))