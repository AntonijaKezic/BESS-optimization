from models.battery import (max_battery_power, update_soc, limit_power)

def simulate_battery(
    soc0,
    p_pv,
    p_max,
    eta_ch,
    eta_dis,
    dt,
    e_max,
    c_rate
):

    soc=[soc0]
    
    p_charge=[]

    p_discharge=[]

    current_soc=soc0
    
    p_limit = min(
        p_max,
        max_battery_power(c_rate, e_max)
    )

    for hour in range(len(p_pv)):

        charge = min(
            p_pv[hour],
            p_limit
        )

        charge = limit_power(
            #Dodatna provjera da snaga ne prelazi dopuštenu granicu
            #imat ce smisla kad bude dodan MILP
            charge,
            p_limit
        )

        discharge = 0
            
        current_soc = update_soc(
            current_soc,
            charge,
            discharge,
            eta_ch,
            eta_dis,
            dt,
            e_max
        )
        
        p_charge.append(
            charge
        )

        p_discharge.append(
            discharge
        )

        soc.append(
            current_soc
        )
     
    return (soc, p_charge, p_discharge)