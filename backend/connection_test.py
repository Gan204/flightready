"""FlightReady connection-time calculator using Aviationstack flight data.

This prototype calculates the time between Flight A's actual/estimated arrival
and Flight B's scheduled departure. It does not invent a minimum connection time.
Keep the API key in the project-root .env file; never commit it.
"""
import json
import os
import re
from datetime import datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_URL = "https://api.aviationstack.com/v1/flights"
PROJECT_ROOT = Path(__file__).resolve().parent.parent


def load_local_env():
    """Load simple KEY=value entries from the project-root .env file."""
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


def normalise_flight_number(value):
    """Accept lower-, upper-, and mixed-case IATA flight numbers."""
    return re.sub(r"\s+", "", value).upper()


def valid_flight_number(value):
    """Allow common two- or three-letter airline codes followed by digits."""
    return bool(re.fullmatch(r"[A-Z0-9]{2,3}[0-9]{1,4}[A-Z]?", value))


def get_codeshare_objects(details):
    """Return codeshare data as a list, handling object or list responses."""
    codeshared = details.get("codeshared")
    if isinstance(codeshared, dict):
        return [codeshared]
    if isinstance(codeshared, list):
        return codeshared
    return []


def record_matches_flight(record, requested_number):
    details = record.get("flight") or {}
    if normalise_flight_number(details.get("iata") or "") == requested_number:
        return True

    for codeshare in get_codeshare_objects(details):
        if normalise_flight_number(codeshare.get("flight_iata") or "") == requested_number:
            return True
    return False


def record_date(record):
    """Use the provider's flight date, falling back to scheduled departure date."""
    date_value = record.get("flight_date")
    if date_value:
        return str(date_value)[:10]

    departure = record.get("departure") or {}
    scheduled = departure.get("scheduled")
    if scheduled:
        return str(scheduled)[:10]
    return None


def fetch_flight(api_key, flight_number, travel_date):
    """Fetch records, then select the exact flight/codeshare on the chosen date."""
    params = urlencode({
        "access_key": api_key,
        "flight_iata": flight_number,
        "limit": 100,
    })
    request = Request(
        f"{API_URL}?{params}",
        headers={"User-Agent": "FlightReady-Prototype/0.2"},
    )

    try:
        with urlopen(request, timeout=20) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        raise RuntimeError(
            f"Aviationstack returned HTTP {error.code}. Check the API key and plan."
        ) from error
    except URLError as error:
        raise RuntimeError(
            "Could not connect to Aviationstack. Check the internet connection."
        ) from error
    except json.JSONDecodeError as error:
        raise RuntimeError("Aviationstack returned unreadable data.") from error

    if payload.get("error"):
        error = payload["error"]
        message = error.get("message", "Unknown API error")
        error_type = error.get("type", "not provided")
        raise RuntimeError(f"Aviationstack error: {message} (type: {error_type})")

    records = payload.get("data") or []
    matching = [
        record for record in records
        if record_matches_flight(record, flight_number)
        and record_date(record) == travel_date
    ]

    if not matching:
        dates_found = sorted({
            record_date(record) for record in records if record_date(record)
        })
        if dates_found:
            raise RuntimeError(
                f"No exact record for {flight_number} on {travel_date}. "
                f"The API returned records dated: {', '.join(dates_found[:8])}. "
                "Try a date supported by your Aviationstack plan."
            )
        raise RuntimeError(
            f"No matching record for {flight_number} was returned. "
            "The flight may not be covered by the API or may not be operating."
        )

    # Prefer the record whose operating flight number matches the user's input.
    # If the input is a codeshare number, the matching codeshare record is used.
    for record in matching:
        details = record.get("flight") or {}
        if normalise_flight_number(details.get("iata") or "") == flight_number:
            return record
    return matching[0]


def parse_api_time(value, label):
    if not value:
        raise RuntimeError(f"{label} is missing from the API response.")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as error:
        raise RuntimeError(f"{label} has an invalid date/time value: {value}") from error

    if parsed.tzinfo is None:
        raise RuntimeError(
            f"{label} has no time-zone information. FlightReady cannot safely "
            "compare the two times."
        )
    return parsed


def get_flight_label(record, requested_number):
    airline = record.get("airline") or {}
    details = record.get("flight") or {}
    operating_number = details.get("iata") or details.get("number") or "Unknown"
    operating_airline = airline.get("name") or "Unknown"

    for codeshare in get_codeshare_objects(details):
        if normalise_flight_number(codeshare.get("flight_iata") or "") == requested_number:
            return (
                requested_number,
                codeshare.get("airline_name") or "Unknown",
                operating_number,
                operating_airline,
            )

    return (
        operating_number,
        operating_airline,
        operating_number,
        operating_airline,
    )


def show_flight_summary(label, record, requested_number, time_label, time_value):
    display_number, display_airline, operating_number, operating_airline = (
        get_flight_label(record, requested_number)
    )
    print(f"\n{label}: {display_airline} {display_number}")
    if display_number != operating_number:
        print(f"  Operated by: {operating_airline} ({operating_number})")

    airline_status = record.get("flight_status") or "not provided"
    print(f"  Status: {airline_status}")
    departure = record.get("departure") or {}
    arrival = record.get("arrival") or {}
    print(f"  From: {departure.get('airport') or 'Unknown'} "
          f"({departure.get('iata') or '---'})")
    print(f"  To: {arrival.get('airport') or 'Unknown'} "
          f"({arrival.get('iata') or '---'})")
    print(f"  {time_label}: {time_value.isoformat()}")


def format_duration(total_minutes):
    hours, minutes = divmod(abs(total_minutes), 60)
    return f"{hours} hour(s) {minutes} minute(s)"


def main():
    load_local_env()
    api_key = os.getenv("AVIATIONSTACK_API_KEY", "").strip()
    if not api_key or api_key == "your_api_key_here":
        print("API key not found. Add it to the project-root .env file.")
        return 1

    print("FlightReady - Connection Time Test")
    first_number = normalise_flight_number(
        input("Enter your first flight number (e.g. SQ318): ")
    )
    second_number = normalise_flight_number(
        input("Enter your connecting flight number (e.g. BA123): ")
    )
    travel_date = input("Enter the travel date (YYYY-MM-DD): ").strip()

    for label, number in (("First flight", first_number),
                          ("Connecting flight", second_number)):
        if not valid_flight_number(number):
            print(f"{label}: '{number}' does not look like a valid flight number.")
            return 1

    try:
        datetime.strptime(travel_date, "%Y-%m-%d")
    except ValueError:
        print("Please enter the date in YYYY-MM-DD format, for example 2026-11-14.")
        return 1

    try:
        print("\nRetrieving flight information...")
        first = fetch_flight(api_key, first_number, travel_date)
        second = fetch_flight(api_key, second_number, travel_date)

        first_arrival = first.get("arrival") or {}
        second_departure = second.get("departure") or {}

        # Prefer actual arrival when available; otherwise use estimated arrival.
        arrival_value = first_arrival.get("actual") or first_arrival.get("estimated")
        if not arrival_value:
            raise RuntimeError(
                "Flight A has no actual or estimated arrival time. "
                "The connection time cannot be calculated reliably yet."
            )

        arrival_time = parse_api_time(
            arrival_value, "Flight A actual/estimated arrival"
        )
        departure_time = parse_api_time(
            second_departure.get("scheduled"),
            "Flight B scheduled departure",
        )

        show_flight_summary(
            "Flight A", first, first_number, "Arrival used", arrival_time
        )
        show_flight_summary(
            "Flight B", second, second_number, "Scheduled departure",
            departure_time
        )

        first_airport = (first_arrival.get("iata") or "").upper()
        second_airport = (second_departure.get("iata") or "").upper()
        if first_airport and second_airport and first_airport != second_airport:
            print("\nWARNING: These flights use different connecting airports "
                  f"({first_airport} and {second_airport}).")
            print("This is not a same-airport connection calculation.")
            return 0

        difference = departure_time - arrival_time
        total_minutes = int(difference.total_seconds() // 60)

        print("\n--- FlightReady: Connection result ---")
        if total_minutes > 0:
            print("Available connection time:", format_duration(total_minutes))
            print(
                "Assessment: Time calculated, but a reliable Safe/At risk "
                "classification is not available yet."
            )
            print(
                "Why: The minimum connection time for this airport, terminal "
                "pair, airline and itinerary has not been verified."
            )
        elif total_minutes == 0:
            print("Available connection time: 0 minutes")
            print("Assessment: Likely to be missed based on the supplied times.")
        else:
            print(
                "Flight A is expected to arrive "
                f"{format_duration(total_minutes)} after Flight B's scheduled "
                "departure."
            )
            print("Assessment: Likely to be missed based on the supplied times.")

        print("\nImportant factors not yet assessed:")
        print("- Whether both flights are on one booking or separate tickets.")
        print("- Whether baggage must be collected and checked in again.")
        print("- Terminal changes, immigration, security and airport transfer time.")
        print("- The airline/airport's published minimum connection time.")

        print("\nFlightReady does not guarantee that a connection can be made.")
        print("Check the latest details with the airlines and airport.")
        print("Times are compared using the time-zone offsets returned by the API.")

    except RuntimeError as error:
        print("\nFlightReady could not complete the calculation:")
        print(error)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
