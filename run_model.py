from api.entsoe_api import get_prices
from api.openmeteo_api import get_weather_tomorrow

from datetime import datetime, timedelta
from models.pv_model import pv_output

from simulation.runner import simulate_battery
from optimization.milp import optimize_battery

from optimization.objective_function_pv import objective_function_pv
from optimization.objective_function import objective_function
from optimization.costs import hourly_cost
from optimization.costs_pv import hourly_cost_pv

from optimization.economic_effect import hourly_economic_effect

from optimization.costs import (
    hourly_cost,
    hourly_cost_components
)

def run_model(
    eta_pv,
    p_nom_pv,
    soc0,
    e_max,
    eta,
    c_rate,
    c_deg,
    p_max,
    dt,
    scenario,
    use_milp=True
):

    eta_ch = eta
    eta_dis = eta

    # -------------------
    # Open-Meteo
    # -------------------

    radiation = get_weather_tomorrow()

    if not radiation:
        raise ValueError(
            "Nije moguće dohvatiti vremensku prognozu."
        )

    # -------------------
    # PV proizvodnja
    # -------------------

    if scenario == "PV + baterija":

        p_pv = [
            pv_output(
                r,
                eta_pv,
                p_nom_pv
            )
            for r in radiation
        ]

    else:

        p_pv = [0.0] * len(radiation)

    # -------------------
    # TESTNE CIJENE
    # -------------------

    price_data = get_prices()

    prices = price_data["prices"]

    price_day = price_data["day"]

    if price_day == "tomorrow":

        optimization_date = (
            datetime.now() + timedelta(days=1)
        ).strftime("%d.%m.%Y.")

    elif price_day == "today":

        optimization_date = (
            datetime.now()
        ).strftime("%d.%m.%Y.")

    else:

        optimization_date = "Nepoznato"

    if len(prices) != 24:

        raise ValueError(
            "ENTSO-E nije vratio 24 satne cijene."
        )

    # -------------------
    # Provjera
    # -------------------

    if len(prices) != len(p_pv):
        raise ValueError(
            f"Broj cijena ({len(prices)}) i PV vrijednosti ({len(p_pv)}) nije jednak."
        )

    # -------------------
    # Optimizacija
    # -------------------

    if use_milp:

        soc, p_charge, p_discharge = optimize_battery(
            prices,
            p_pv,
            soc0,
            e_max,
            eta_ch,
            eta_dis,
            p_max,
            c_rate,
            c_deg,
            dt,
            scenario
        )

    else:

        soc, p_charge, p_discharge = simulate_battery(
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
        )

    # -------------------
    # Troškovi
    # -------------------

    economic_effect = None 
    
    charge_costs = None
    discharge_benefits = None

    if scenario=="PV + baterija":

        total_cost=objective_function_pv(
        prices,
        p_charge,
        p_discharge,
        dt,
        c_deg
        )
        
        hourly_costs = hourly_cost_pv(
            prices,
            p_charge,
            p_discharge,
            dt,
            c_deg
        )
        
    else:

        total_cost=objective_function(
            prices,
            p_charge,
            p_discharge,
            dt,
            c_deg
        )
        
        hourly_costs = hourly_cost(
            prices,
            p_charge,
            p_discharge,
            dt,
            c_deg
        )
        
        charge_costs, discharge_benefits = hourly_cost_components(
            prices,
            p_charge,
            p_discharge,
            dt,
            c_deg
        )

        economic_effect = hourly_economic_effect(
            prices,
            p_charge,
            p_discharge,
            dt,
            c_deg
        )

    # -------------------
    # Rezultati
    # -------------------
    
    return {
        "pv": p_pv,
        "prices": prices,
        "price_day": price_day,
        "optimization_date": optimization_date,
        "soc": soc,
        "p_charge": p_charge,
        "p_discharge": p_discharge,
        "cost": total_cost,
        "hourly_costs": hourly_costs,
        "economic_effect": economic_effect,
        "charge_costs": charge_costs,
        "discharge_benefits": discharge_benefits,
    }