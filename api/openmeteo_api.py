from datetime import datetime, timedelta, date
from calendar import monthrange
import requests


LATITUDE = 43.5     # područje Splita
LONGITUDE = 16.4


def get_weather_tomorrow():
    """Dohvaća prognozu Sunčevog zračenja za područje Splita za
    sljedeća 24 sata koristeći Open-Meteo forecast API. Vraća listu
    od 24 satne vrijednosti [W/m²], ili praznu listu u slučaju
    greške."""

    url = "https://api.open-meteo.com/v1/forecast"

    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    parameters = {

        "latitude": LATITUDE,
        "longitude": LONGITUDE,

        "hourly": ["shortwave_radiation"],
        "start_date": tomorrow,
        "end_date": tomorrow,
    }

    response = requests.get(url, params=parameters)

    if response.status_code != 200:

        print("Greška pri dohvaćanju vremenske prognoze.")

        return []

    data = response.json()

    try:

        radiation = data["hourly"]["shortwave_radiation"]

    except KeyError:

        print("OpenMeteo nije vratio očekivane podatke.")

        return []

    if len(radiation) != 24:

        print("Nedovoljno podataka o zračenju za sutra.")

        return []

    return radiation


def get_weather_for_date(target_date):
    """Dohvaća povijesnu satnu vrijednost Sunčevog zračenja za
    zadani datum koristeći Open-Meteo Archive API. Podržava datume
    od 1940. do prije nekoliko dana (ovisno o vremenu obrade
    ERA5 reanalize).

    Parametri
    ---------
    target_date : datetime.date | str
        Datum (YYYY-MM-DD).

    Vraća
    -----
    list[float]
        24 satne vrijednosti kratkovalnog zračenja [W/m²], ili
        prazna lista u slučaju greške.
    """

    if hasattr(target_date, "strftime"):
        date_str = target_date.strftime("%Y-%m-%d")
    else:
        date_str = str(target_date)

    url = "https://archive-api.open-meteo.com/v1/archive"

    parameters = {

        "latitude": LATITUDE,
        "longitude": LONGITUDE,

        "hourly": ["shortwave_radiation"],
        "start_date": date_str,
        "end_date": date_str,
    }

    response = requests.get(url, params=parameters, timeout=30)

    if response.status_code != 200:

        print(
            "Greška pri dohvaćanju povijesne prognoze: "
            f"HTTP {response.status_code}"
        )

        return []

    data = response.json()

    try:

        radiation = data["hourly"]["shortwave_radiation"]

    except KeyError:

        print("Open-Meteo Archive nije vratio očekivane podatke.")

        return []

    # Popuni eventualne None vrijednosti nulom (rijetko)
    radiation = [r if r is not None else 0.0 for r in radiation]

    if len(radiation) != 24:

        print(
            f"Nedovoljno podataka o zračenju za datum {date_str} "
            f"(dobiveno {len(radiation)} vrijednosti)."
        )

        return []

    return radiation


def get_monthly_daily_totals(year, month):
    """Dohvaća sve satne vrijednosti kratkovalnog zračenja za
    zadani mjesec (jedan API poziv) i agregira ih u dnevne ukupne
    vrijednosti [kWh/m²/dan].

    Vraća dict {dan_u_mjesecu: ukupna_dnevna_energija_kwh_po_m2}.
    Prazan dict ako dohvat ne uspije.
    """

    _, days_in_month = monthrange(year, month)

    start = date(year, month, 1).strftime("%Y-%m-%d")
    end = date(year, month, days_in_month).strftime("%Y-%m-%d")

    url = "https://archive-api.open-meteo.com/v1/archive"

    parameters = {

        "latitude": LATITUDE,
        "longitude": LONGITUDE,

        "hourly": ["shortwave_radiation"],
        "start_date": start,
        "end_date": end,
    }

    try:

        response = requests.get(url, params=parameters, timeout=60)

    except Exception as e:

        print(f"Greška pri dohvaćanju mjesečnih podataka: {e}")

        return {}

    if response.status_code != 200:

        print(
            "Greška pri dohvaćanju mjesečnih podataka: "
            f"HTTP {response.status_code}"
        )

        return {}

    data = response.json()

    try:

        radiation = data["hourly"]["shortwave_radiation"]
        times = data["hourly"]["time"]

    except KeyError:

        print("Open-Meteo Archive nije vratio očekivane podatke.")

        return {}

    daily = {}

    for t, r in zip(times, radiation):

        if r is None:
            continue

        # t je oblika "2025-01-15T00:00"
        day = int(t[8:10])

        daily[day] = daily.get(day, 0.0) + r

    # Wh -> kWh (dt = 1 h po satu)
    return {
        d: v / 1000.0
        for d, v in daily.items()
    }

