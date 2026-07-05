import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ENTSOE_API_KEY")


def _parse_prices_from_xml(xml_text):
    """
    Parsira ENTSO-E XML.

    ENTSO-E vraća 15-minutne cijene (PT15M).
    Ova funkcija ih pretvara u 24 satne cijene.
    """

    root = ET.fromstring(xml_text)

    ns = {
        "ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"
    }

    # spremnik svih 96 intervala
    values = {}

    for point in root.findall(".//ns:Point", ns):

        pos = point.find("ns:position", ns)
        price = point.find("ns:price.amount", ns)

        if pos is None or price is None:
            continue

        try:
            values[int(pos.text)] = float(price.text)
        except ValueError:
            continue

    hourly_prices = []

    for hour in range(24):

        start = hour * 4 + 1

        block = []

        for p in range(start, start + 4):

            if p in values:
                block.append(values[p])

        if len(block) == 0:

            hourly_prices.append(None)

        else:

            hourly_prices.append(sum(block) / len(block))

    return hourly_prices


def get_prices():

    session = requests.Session()

    attempts = [

        (1, "tomorrow"),
        (0, "today")

    ]

    for offset, label in attempts:

        day = datetime.now() + timedelta(days=offset)

        start = day.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        end = start + timedelta(days=1)

        params = {

            "securityToken": API_KEY,

            "documentType": "A44",

            "processType": "A01",

            "in_Domain": "10YHR-HEP------M",

            "out_Domain": "10YHR-HEP------M",

            "periodStart": start.strftime("%Y%m%d%H%M"),

            "periodEnd": end.strftime("%Y%m%d%H%M")

        }

        try:

            response = session.get(
                "https://web-api.tp.entsoe.eu/api",
                params=params,
                timeout=30
            )

            if response.status_code != 200:

                print("HTTP:", response.status_code)

                continue

            prices = _parse_prices_from_xml(response.text)

            # ako postoji barem jedna None,
            # znači da nedostaju podaci
            if any(p is None for p in prices):

                print("Nedostaju neki intervali.")

                continue

            if len(prices) == 24:

                return {

                    "prices": prices,

                    "day": label

                }

        except Exception as e:

            print(e)

    return {

        "prices": [],

        "day": None

    }


if __name__ == "__main__":

    data = get_prices()

    print()

    print("Dan:", data["day"])

    print("Broj cijena:", len(data["prices"]))

    print(data["prices"])