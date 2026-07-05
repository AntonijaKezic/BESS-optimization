from datetime import datetime, timedelta
import requests


def get_weather_tomorrow():
    #Dohvaća prognozu Sunčevog zračenja
    #za područje Splita za sljedeća 24 sata
    #koristeći OpenMeteo API.

    url = "https://api.open-meteo.com/v1/forecast"
    
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")

    parameters = { 

        "latitude": 43.5,      #parametri za podrucje Splita
        "longitude": 16.4,

        "hourly": ["shortwave_radiation"],     #W/m^2]
        "start_date": tomorrow,  # Početak: sutra
        "end_date": tomorrow,  # Kraj: sutra (progoza za 24 sata)
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