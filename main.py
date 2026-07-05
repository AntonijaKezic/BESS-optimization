from run_model import run_model

USE_MILP = True      # True -> MILP
                     # False -> heuristička simulacija


# -------------------
# FUNKCIJA ZA UNOS
# -------------------

def read_float(message, minimum=None, maximum=None, inclusive_min=True):

    while True:

        try:

            value = float(
                input(message).replace(",", ".")
            )

            if minimum is not None:

                if inclusive_min:

                    if value < minimum:
                        print(f"Vrijednost mora biti ≥ {minimum}.")
                        continue

                else:

                    if value <= minimum:
                        print(f"Vrijednost mora biti > {minimum}.")
                        continue

            if maximum is not None:

                if value > maximum:
                    print(f"Vrijednost mora biti ≤ {maximum}.")
                    continue

            return value

        except ValueError:

            print("Unesi ispravan broj.")


# -------------------
# KORISNIČKI UNOS
# -------------------

eta_pv = read_float(
    "Unesi učinkovitost PV [0–1]: ",
    minimum=0,
    maximum=1,
    inclusive_min=False
)

p_nom_pv = read_float(
    "Unesi nazivnu snagu PV [kW]: ",
    minimum=0,
    inclusive_min=False
)

soc0 = read_float(
    "Unesi početni SOC [0–1]: ",
    minimum=0,
    maximum=1
)

e_max = read_float(
    "Unesi kapacitet baterije [kWh]: ",
    minimum=0,
    inclusive_min=False
)

eta = read_float(
    "Unesi učinkovitost baterije [0–1]: ",
    minimum=0,
    maximum=1,
    inclusive_min=False
)

c_rate = read_float(
    "Unesi C-rate [h⁻¹]: ",
    minimum=0,
    inclusive_min=False
)

c_deg = read_float(
    "Unesi trošak degradacije [€/kWh]: ",
    minimum=0
)

p_max = read_float(
    "Unesi maksimalnu snagu punjenja/pražnjenja [kW]: ",
    minimum=0,
    inclusive_min=False
)

dt = read_float(
    "Unesi korak simulacije [h]: ",
    minimum=0,
    inclusive_min=False
)


# -------------------
# POKRETANJE MODELA
# -------------------

results = run_model(

    eta_pv=eta_pv,
    p_nom_pv=p_nom_pv,
    soc0=soc0,
    e_max=e_max,
    eta=eta,
    c_rate=c_rate,
    c_deg=c_deg,
    p_max=p_max,
    dt=dt,
    use_milp=USE_MILP

)


# -------------------
# ISPIS
# -------------------

print("\nPV proizvodnja [kW]:")
print(results["pv"])

print("\nCijene [€/MWh]:")
print(results["prices"])

print("\nSOC:")
print(results["soc"])

print("\nPunjenje baterije [kW]:")
print(results["p_charge"])

print("\nPražnjenje baterije [kW]:")
print(results["p_discharge"])

print("\nUkupan trošak [€]:")
print(round(results["cost"], 2))

print("\nSatni troškovi:")
print(results["hourly_costs"])