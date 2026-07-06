# -----------------------------------------------------------------
# Katalog dnevnih predložaka potrošnje električne energije
# -----------------------------------------------------------------
#
# Svaki predložak sadrži 24 relativna udjela (satnih vrijednosti)
# koji opisuju oblik krivulje dnevne potrošnje. Vrijednosti se u
# funkciji load_profile() interpoliraju na traženu rezoluciju
# (npr. 4 koraka po satu za 15-minutni raster) i skaliraju prema
# ukupnoj dnevnoj potrošnji u kWh. Normalizacija se izvodi
# automatski, tako da apsolutne vrijednosti u predlošku nisu
# važne - samo relativni oblik krivulje.
# -----------------------------------------------------------------

PROFILES = {

    "Rezidencijalni (večernji vrh)": [
        0.025,  # 00:00
        0.023,  # 01:00
        0.021,  # 02:00
        0.020,  # 03:00
        0.020,  # 04:00
        0.022,  # 05:00
        0.028,  # 06:00
        0.038,  # 07:00
        0.043,  # 08:00
        0.043,  # 09:00
        0.043,  # 10:00
        0.043,  # 11:00
        0.043,  # 12:00
        0.043,  # 13:00
        0.043,  # 14:00
        0.043,  # 15:00
        0.045,  # 16:00
        0.055,  # 17:00
        0.065,  # 18:00
        0.070,  # 19:00
        0.060,  # 20:00
        0.048,  # 21:00
        0.038,  # 22:00
        0.030,  # 23:00
    ],

    "Poslovni (dnevni vrh 8-17h)": [
        0.010,  # 00:00
        0.010,  # 01:00
        0.010,  # 02:00
        0.010,  # 03:00
        0.010,  # 04:00
        0.012,  # 05:00
        0.020,  # 06:00
        0.035,  # 07:00
        0.060,  # 08:00
        0.070,  # 09:00
        0.075,  # 10:00
        0.075,  # 11:00
        0.070,  # 12:00
        0.075,  # 13:00
        0.075,  # 14:00
        0.075,  # 15:00
        0.070,  # 16:00
        0.060,  # 17:00
        0.040,  # 18:00
        0.025,  # 19:00
        0.020,  # 20:00
        0.015,  # 21:00
        0.015,  # 22:00
        0.012,  # 23:00
    ],

    "Ravni (industrijski)": [1.0 / 24.0] * 24,

    "Noćna smjena (peak 22-06h)": [
        0.055,  # 00:00
        0.060,  # 01:00
        0.060,  # 02:00
        0.060,  # 03:00
        0.055,  # 04:00
        0.050,  # 05:00
        0.040,  # 06:00
        0.030,  # 07:00
        0.020,  # 08:00
        0.020,  # 09:00
        0.025,  # 10:00
        0.030,  # 11:00
        0.030,  # 12:00
        0.030,  # 13:00
        0.030,  # 14:00
        0.030,  # 15:00
        0.030,  # 16:00
        0.035,  # 17:00
        0.040,  # 18:00
        0.045,  # 19:00
        0.050,  # 20:00
        0.055,  # 21:00
        0.055,  # 22:00
        0.055,  # 23:00
    ],

}


PROFILE_NAMES = list(PROFILES.keys())

DEFAULT_PROFILE = PROFILE_NAMES[0]


def _interpolate_cyclic(hourly, steps_per_hour):
    """Linearna interpolacija 24 satnih vrijednosti na N koraka po
    satu, s ciklickim spajanjem 23h -> 00h. Ukupna dnevna energija
    (suma * dt) ostaje sacuvana."""

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


def load_profile(
    daily_kwh,
    profile_name=DEFAULT_PROFILE,
    steps_per_hour=4
):
    """Vraća listu snage potrošnje [kW] po vremenskim koracima za
    zadanu dnevnu potrošnju [kWh] i ime predloška.

    Parametri
    ---------
    daily_kwh : float
        Ukupna dnevna potrošnja kućanstva u kWh.
    profile_name : str
        Ime predloška iz PROFILES (npr. "Rezidencijalni ...").
    steps_per_hour : int
        Broj vremenskih koraka unutar sata. 4 = 15-min raster,
        1 = satni raster. Default 4.

    Vraća
    -----
    list[float]
        Lista duljine 24 * steps_per_hour koja predstavlja snagu
        u kW u svakom vremenskom koraku. Vrijedi
        sum(P) * dt = daily_kwh, gdje je dt = 1 / steps_per_hour.
    """

    if profile_name not in PROFILES:

        raise ValueError(
            f"Nepoznat profil potrošnje: '{profile_name}'. "
            f"Dostupni: {PROFILE_NAMES}"
        )

    template = PROFILES[profile_name]

    fine = _interpolate_cyclic(template, steps_per_hour)

    dt = 1.0 / steps_per_hour

    total_energy = sum(fine) * dt

    scale = daily_kwh / total_energy

    return [v * scale for v in fine]
