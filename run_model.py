from api.entsoe_api import get_prices
from api.openmeteo_api import get_weather_tomorrow, get_weather_for_date

from datetime import datetime, timedelta
from models.pv_model import pv_output
from models.load_profile import load_profile, DEFAULT_PROFILE

from simulation.runner import simulate_battery
from optimization.milp import optimize_battery

from optimization.objective_function import objective_function
from optimization.costs import hourly_cost

from optimization.economic_effect import hourly_economic_effect

from optimization.costs import (
    hourly_cost,
    hourly_cost_components
)


STEPS_PER_HOUR = 4  # 15-min raster
SLOTS_PER_DAY = 24 * STEPS_PER_HOUR
DEFAULT_DT = 1.0 / STEPS_PER_HOUR


def _repeat_hourly(hourly, steps_per_hour):
    """Ekspanzija 24 satnih vrijednosti u 24*N koraka ponavljanjem
    (svaki sat 4 puta za 15-min raster). Prigodno za vrijednosti
    koje su konstantne unutar sata."""

    return [v for v in hourly for _ in range(steps_per_hour)]


def _adapt_prices_to_dt(prices_native, resolution_minutes, target_dt_h):
    """Prilagodi cijene iz prirodne ENTSO-E rezolucije na traženi
    korak simulacije. Podržava PT15M i PT60M na ulazu, te bilo koji
    korak koji je multiplo/djelo od nativne rezolucije.

    Ako je nativna rezolucija finija od ciljne, cijene se usredotoče
    (aritmetička sredina unutar većeg koraka). Ako je grublja,
    vrijednosti se ponavljaju."""

    target_minutes = int(round(target_dt_h * 60))

    if target_minutes == resolution_minutes:
        return list(prices_native)

    if target_minutes % resolution_minutes == 0:
        # cilj je grublji, usrednji blokove
        group = target_minutes // resolution_minutes
        return [
            sum(prices_native[i:i + group]) / group
            for i in range(0, len(prices_native), group)
        ]

    if resolution_minutes % target_minutes == 0:
        # cilj je finiji, ponovi svaku vrijednost
        repeat = resolution_minutes // target_minutes
        return [v for v in prices_native for _ in range(repeat)]

    raise ValueError(
        f"Nema jednostavne pretvorbe iz {resolution_minutes} min "
        f"u {target_minutes} min raster."
    )


def _interpolate_hourly(hourly, steps_per_hour):
    """Linearna interpolacija 24 satnih vrijednosti u 24*N koraka,
    s ciklickim spajanjem 23h -> 00h. Za vrijednosti koje se glatko
    mijenjaju kroz sat (npr. Sunčevo zračenje)."""

    n = len(hourly)

    result = []

    for i in range(n):

        next_val = hourly[(i + 1) % n]

        for k in range(steps_per_hour):

            frac = k / steps_per_hour

            result.append(
                hourly[i] * (1.0 - frac)
                +
                next_val * frac
            )

    return result


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
    use_milp=True,
    daily_load_kwh=None,
    profile_name=DEFAULT_PROFILE,
    historical_date=None
):

    eta_ch = eta
    eta_dis = eta

    steps_per_hour = int(round(1.0 / dt)) if dt > 0 else STEPS_PER_HOUR

    # -------------------
    # Open-Meteo (satni)
    # -------------------

    if historical_date is not None:

        radiation_hourly = get_weather_for_date(historical_date)

        if not radiation_hourly:
            raise ValueError(
                f"Nije moguće dohvatiti povijesnu prognozu za "
                f"{historical_date}."
            )

    else:

        radiation_hourly = get_weather_tomorrow()

        if not radiation_hourly:
            raise ValueError(
                "Nije moguće dohvatiti vremensku prognozu."
            )

    radiation = _interpolate_hourly(radiation_hourly, steps_per_hour)

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
    # ENTSO-E cijene (satne, ponavljaju se za 15-min raster)
    # -------------------

    if historical_date is not None:

        price_data = get_prices(target_date=historical_date)

    else:

        price_data = get_prices()

    prices_native = price_data["prices"]

    price_day = price_data["day"]

    resolution_minutes = price_data.get("resolution_minutes")

    if historical_date is not None:

        optimization_date = historical_date.strftime("%d.%m.%Y.")

    elif price_day == "tomorrow":

        optimization_date = (
            datetime.now() + timedelta(days=1)
        ).strftime("%d.%m.%Y.")

    elif price_day == "today":

        optimization_date = (
            datetime.now()
        ).strftime("%d.%m.%Y.")

    else:

        optimization_date = "Nepoznato"

    if not prices_native or resolution_minutes is None:

        raise ValueError(
            "ENTSO-E nije vratio cijene."
        )

    expected_native = 24 * 60 // resolution_minutes

    if len(prices_native) != expected_native:

        raise ValueError(
            f"ENTSO-E je vratio {len(prices_native)} cijena; "
            f"za rezoluciju {resolution_minutes} min očekivano "
            f"{expected_native}."
        )

    prices = _adapt_prices_to_dt(
        prices_native,
        resolution_minutes,
        dt
    )

    # -------------------
    # Provjera dimenzija
    # -------------------

    if len(prices) != len(p_pv):
        raise ValueError(
            f"Broj cijena ({len(prices)}) i PV vrijednosti "
            f"({len(p_pv)}) nije jednak."
        )

    # -------------------
    # Profil potrošnje (samo za PV scenarij)
    # -------------------

    p_load = None
    pv_to_load = None
    grid_imp = None
    baseline_grid = None
    baseline_hourly_cost = None
    baseline_cost = None
    hourly_savings = None
    total_savings = None

    if scenario == "PV + baterija":

        if daily_load_kwh is None:

            raise ValueError(
                "Dnevna potrošnja (daily_load_kwh) nije zadana."
            )

        p_load = load_profile(
            daily_load_kwh,
            profile_name=profile_name,
            steps_per_hour=steps_per_hour
        )

        if len(p_load) != len(prices):

            raise ValueError(
                f"Broj koraka potrošnje ({len(p_load)}) i cijena "
                f"({len(prices)}) nije jednak."
            )

    # -------------------
    # Optimizacija
    # -------------------

    if use_milp:

        if scenario == "PV + baterija":

            (
                soc,
                p_charge,
                p_discharge,
                pv_to_load,
                grid_imp
            ) = optimize_battery(
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
                scenario,
                p_load=p_load
            )

        else:

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

        if scenario == "PV + baterija":

            (
                soc,
                p_charge,
                p_discharge,
                pv_to_load,
                grid_imp
            ) = simulate_battery(
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
                p_load=p_load
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

        # Satni trošak s baterijom = trošak uvoza iz mreže + degradacija
        hourly_costs = [
            (prices[t] / 1000) * grid_imp[t] * dt
            +
            c_deg * (p_charge[t] + p_discharge[t]) * dt
            for t in range(len(prices))
        ]

        total_cost_with_battery = sum(hourly_costs)

        # Baseline: bez baterije PV pokriva potrošnju, ostatak iz mreže
        baseline_grid = [
            max(0.0, p_load[t] - min(p_pv[t], p_load[t]))
            for t in range(len(prices))
        ]

        baseline_hourly_cost = [
            (prices[t] / 1000) * baseline_grid[t] * dt
            for t in range(len(prices))
        ]

        baseline_cost = sum(baseline_hourly_cost)

        hourly_savings = [
            baseline_hourly_cost[t] - hourly_costs[t]
            for t in range(len(prices))
        ]

        total_savings = baseline_cost - total_cost_with_battery

        # Postojeći GUI KPI konvencija: cost < 0 -> ušteda
        total_cost = -total_savings

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
        "p_load": p_load,
        "pv_to_load": pv_to_load,
        "grid_imp": grid_imp,
        "baseline_grid": baseline_grid,
        "baseline_hourly_cost": baseline_hourly_cost,
        "baseline_cost": baseline_cost,
        "hourly_savings": hourly_savings,
        "total_savings": total_savings,
        "steps_per_hour": steps_per_hour,
        "dt": dt,
        "profile_name": profile_name,
        "price_resolution_minutes": resolution_minutes,
    }
