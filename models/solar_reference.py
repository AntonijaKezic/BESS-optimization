"""Analiticki referentni modeli Suncevog zracenja za normalizaciju
dnevne dozracene energije. Koristi se za bojanje kalendarskog
prikaza (postotak stvarnog zracenja u odnosu na idealni vedri dan).
"""

import math


def extraterrestrial_daily_kwh(day_of_year, latitude_deg):
    """Vraća dnevnu ekstraterestrijalnu insolaciju na horizontalnu
    povrsinu za zadani dan u godini i geografsku sirinu.

    Rezultat u kWh/m²/dan. Formula prema klasicnom astronomskom
    modelu (Duffie & Beckman): H_0 = (24*3600/pi) * I_sc * E_0 *
    (cos(lat)*cos(decl)*sin(w_s) + w_s*sin(lat)*sin(decl))."""

    lat = math.radians(latitude_deg)

    # Deklinacija Sunca (Cooperova formula)
    decl = math.radians(
        23.45
        * math.sin(math.radians(360.0 * (284 + day_of_year) / 365.0))
    )

    # Satni kut zalaska Sunca (radijani), s clamp-om za polarni dan/noc
    cos_ws = -math.tan(lat) * math.tan(decl)
    cos_ws = max(-1.0, min(1.0, cos_ws))
    ws = math.acos(cos_ws)

    # Solarna konstanta [W/m²]
    Isc = 1367.0

    # Korekcija ekscentricnosti orbite Zemlje
    e0 = 1.0 + 0.033 * math.cos(math.radians(360.0 * day_of_year / 365.0))

    H0_joules = (
        (24.0 * 3600.0 * Isc * e0 / math.pi)
        * (
            math.cos(lat) * math.cos(decl) * math.sin(ws)
            + ws * math.sin(lat) * math.sin(decl)
        )
    )

    return H0_joules / 3.6e6   # J -> kWh


def clearsky_daily_kwh(
    day_of_year,
    latitude_deg,
    attenuation=0.72
):
    """Priblizna dnevna insolacija idealnog vedrog dana na razini
    tla. Ekstraterestrijalna vrijednost pomnozena s prosjecnom
    atmosferskom transmitancijom (~0.72 za umjerene sirine).

    Za tocniju procjenu koristi Bird ili Ineichen model, no za
    normalizaciju bojenja kalendara ova aproksimacija je dovoljna."""

    return (
        extraterrestrial_daily_kwh(day_of_year, latitude_deg)
        * attenuation
    )
