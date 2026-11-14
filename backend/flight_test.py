"""Small FlightReady test: retrieve current flight status from Aviationstack.

Keep your API key in the project-root .env file. Never commit that file.
"""
import json
import os
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://api.aviationstack.com/v1/flights"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_local_env():
    """Load simple KEY=value entries from .env without extra packages."""
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return

    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(name.strip(), value)


def display_flight(flight, requested_iata=None):
    airline = flight.get("airline") or {}
    details = flight.get("flight") or {}
    codeshared = details.get("codeshared") or {}
    departure = flight.get("departure") or {}
    arrival = flight.get("arrival") or {}

    operating_number = details.get("iata") or details.get("number") or "Not provided"
    codeshare_number = codeshared.get("flight_iata")
    codeshare_airline = codeshared.get("airline_name")

    print("\n--- FlightReady: Flight information ---")
    if requested_iata and requested_iata == codeshare_number:
        print("Requested flight:", requested_iata)
        print("Marketing airline:", codeshare_airline or "Not provided")
        print("Operating flight:", operating_number)
        print("Operating airline:", airline.get("name") or "Not provided")
    else:
        print("Flight:", operating_number)
        print("Airline:", airline.get("name") or "Not provided")
    print("Status:", flight.get("flight_status") or "Not provided")
    print("\nDeparture")
    print("  Airport:", departure.get("airport") or "Not provided")
    print("  Scheduled:", departure.get("scheduled") or "Not provided")
    print("  Estimated:", departure.get("estimated") or "Not provided")
    print("  Actual:", departure.get("actual") or "Not available yet")
    print("\nArrival")
    print("  Airport:", arrival.get("airport") or "Not provided")
    print("  Scheduled:", arrival.get("scheduled") or "Not provided")
    print("  Estimated:", arrival.get("estimated") or "Not provided")
    print("  Actual:", arrival.get("actual") or "Not available yet")
    print("\nTimes are shown with the time-zone information returned by the API.")
    print("This is a data-retrieval test, not a connection-risk prediction.")


def flight_group_key(flight):
    """Group records that appear to describe the same scheduled journey."""
    departure = flight.get("departure") or {}
    arrival = flight.get("arrival") or {}
    return (
        departure.get("iata"),
        departure.get("scheduled"),
        arrival.get("iata"),
        arrival.get("scheduled"),
    )


def main():
    load_local_env()
    api_key = os.getenv("AVIATIONSTACK_API_KEY", "").strip()

    if not api_key or api_key == "your_api_key_here":
        print("API key not found.")
        print("Copy .env.example to .env and add your Aviationstack API key.")
        return 1

    flight_iata = sys.argv[1].strip().upper() if len(sys.argv) > 1 else input(
        "Enter a flight number (example: SQ318): "
    ).strip().upper()

    flight_iata = flight_iata.replace(" ", "")
    if not re.fullmatch(r"[A-Z0-9]{2,3}[0-9]{1,4}[A-Z]?", flight_iata):
        print("Please enter a valid-looking flight number, such as SQ318.")
        return 1

    params = urlencode({
        "access_key": api_key,
        "flight_iata": flight_iata,
        "limit": 5,
    })
    request = Request(
        f"{API_URL}?{params}",
        headers={"User-Agent": "FlightReady-Prototype/0.1"},
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        print(f"API request failed (HTTP {error.code}). Check your key and plan.")
        return 1
    except URLError:
        print("Could not connect. Check your internet connection and try again.")
        return 1
    except json.JSONDecodeError:
        print("The API returned data that could not be read.")
        return 1

    if payload.get("error"):
        error = payload["error"]
        print("Aviationstack error:", error.get("message", "Unknown API error"))
        print("Type:", error.get("type", "Not provided"))
        return 1

    flights = payload.get("data") or []
    if not flights:
        print(f"No flight records found for {flight_iata}.")
        print("Try a flight that is operating today, and check the flight number.")
        return 0

    # Aviationstack may return several airline flight numbers for one
    # journey (codeshare records). Group identical scheduled journeys.
    grouped = {}
    for flight in flights:
        key = flight_group_key(flight)
        grouped.setdefault(key, []).append(flight)

    print(
        f"Found {len(flights)} API record(s) for {flight_iata}, "
        f"representing {len(grouped)} distinct scheduled journey(s)."
    )

    for records in grouped.values():
        def matches_requested(record):
            details = record.get("flight") or {}
            codeshared = details.get("codeshared") or {}
            return (
                details.get("iata") == flight_iata
                or codeshared.get("flight_iata") == flight_iata
            )

        # Prefer a record that explicitly contains the requested flight number,
        # either as the operating flight or as a marketed codeshare flight.
        selected = next((r for r in records if matches_requested(r)), records[0])
        display_flight(selected, flight_iata)

        other_numbers = []
        for record in records:
            details = record.get("flight") or {}
            codeshared = details.get("codeshared") or {}
            for number in (
                details.get("iata") or details.get("number"),
                codeshared.get("flight_iata"),
            ):
                if number and number not in other_numbers:
                    other_numbers.append(number)

        if len(other_numbers) > 1:
            print("Other matching flight numbers:", ", ".join(other_numbers))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
