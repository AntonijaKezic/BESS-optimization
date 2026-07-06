import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ENTSOE_API_KEY")


def _parse_prices_from_xml(xml_text):
    """
    Parsira ENTSO-E Publication_MarketDocument.

    Vraća cijene iz prvog TimeSeries/Period-a koji uspije dati
    kompletan niz. Ovo je važno jer ENTSO-E često vraća više
    TimeSeries u istom odgovoru (npr. tražiš današnji dan a dobiješ
    i sutrašnji ili prošli dan) - naivno spajanje svih Point-ova
    dovelo bi do miješanja podataka iz različitih dana.

    Podržava sparse enkoding (curveType=A03) gdje pozicije s istom
    cijenom kao prethodna nisu ponovno navedene - vrijednosti se
    forward-fill-aju do sljedeće eksplicitne pozicije.

    Detektira rezoluciju iz <ns:resolution>:
      - PT15M → 96 vrijednosti
      - PT30M → 48 vrijednosti
      - PT60M → 24 vrijednosti

    Vraća: (prices, resolution_minutes)
    """

    root = ET.fromstring(xml_text)

    ns = {
        "ns": "urn:iec62325.351:tc57wg16:451-3:publicationdocument:7:3"
    }

    for ts in root.findall(".//ns:TimeSeries", ns):

        for period in ts.findall(".//ns:Period", ns):

            res_el = period.find("ns:resolution", ns)

            if res_el is None or not res_el.text:
                continue

            text = res_el.text.upper()

            if "PT15M" in text:
                resolution_min = 15
            elif "PT30M" in text:
                resolution_min = 30
            elif "PT60M" in text or "PT1H" in text:
                resolution_min = 60
            else:
                continue

            n_expected = 24 * 60 // resolution_min

            explicit = {}

            for point in period.findall("ns:Point", ns):

                pos_el = point.find("ns:position", ns)
                price_el = point.find("ns:price.amount", ns)

                if pos_el is None or price_el is None:
                    continue

                try:
                    explicit[int(pos_el.text)] = float(price_el.text)
                except ValueError:
                    continue

            if not explicit:
                continue

            # Forward-fill za sparse enkoding (curveType=A03)
            prices = []
            last = None

            for p in range(1, n_expected + 1):

                if p in explicit:
                    last = explicit[p]

                prices.append(last)

            # Ako ni prva pozicija nije eksplicitna, ne možemo
            # forward-fill - preskoči ovaj period
            if prices[0] is None:
                continue

            return prices, resolution_min

    return [], 60


def get_prices(target_date=None):
    """Dohvaća day-ahead cijene iz ENTSO-E za područje Hrvatske.

    Ako je zadan target_date (datetime.date), dohvaća cijene samo
    za taj datum (za povijesne analize). U protivnom, pokušava
    prvo sutrašnji, a onda današnji datum (originalno ponašanje).

    Vraća dict s ključevima:
    - "prices": list[float] u prirodnoj rezoluciji (24 satne ili
      96 15-minutnih vrijednosti), ili prazna lista ako dohvat ne uspije
    - "day": "tomorrow" | "today" | "historical" | None
    - "resolution_minutes": 15 | 60 (ili None ako prazno)
    """

    session = requests.Session()

    if target_date is not None:

        # Povijesni datum - pokušaj samo taj jedan datum
        day = datetime.combine(
            target_date,
            datetime.min.time()
        )

        attempts = [(day, "historical")]

    else:

        # Default: prvo sutra, ako ne, danas
        today = datetime.now().replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )

        attempts = [
            (today + timedelta(days=1), "tomorrow"),
            (today, "today"),
        ]

    for day, label in attempts:

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

            prices, resolution_min = _parse_prices_from_xml(response.text)

            # Ako postoji barem jedan None, znači da nedostaju podaci
            if any(p is None for p in prices):

                print(
                    "Nedostaju neki intervali "
                    f"({sum(1 for p in prices if p is None)} od {len(prices)})."
                )

                continue

            expected = 24 * 60 // resolution_min

            if len(prices) == expected:

                return {

                    "prices": prices,

                    "day": label,

                    "resolution_minutes": resolution_min

                }

        except Exception as e:

            print(e)

    return {

        "prices": [],

        "day": None,

        "resolution_minutes": None

    }


if __name__ == "__main__":

    data = get_prices()

    print()

    print("Dan:", data["day"])
    print("Rezolucija:", data["resolution_minutes"], "min")
    print("Broj cijena:", len(data["prices"]))
    print(data["prices"])
