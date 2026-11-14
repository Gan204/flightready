from datetime import datetime
import os

from flask import Flask, render_template, request

from backend.connection_test import (
    fetch_flight,
    format_duration,
    get_flight_label,
    load_local_env,
    normalise_flight_number,
    parse_api_time,
    valid_flight_number,
)

load_local_env()
app = Flask(__name__)


def flight_card(record, requested_number, kind):
    display_number, display_airline, operating_number, operating_airline = (
        get_flight_label(record, requested_number)
    )
    departure = record.get("departure") or {}
    arrival = record.get("arrival") or {}

    if kind == "arrival":
        value = arrival.get("actual") or arrival.get("estimated")
        time_label = "Arrival time used"
    else:
        value = departure.get("scheduled")
        time_label = "Scheduled departure"

    parsed_time = parse_api_time(value, time_label)
    return {
        "airline": display_airline,
        "number": display_number,
        "operating": (
            f"{operating_airline} · {operating_number}"
            if display_number != operating_number else None
        ),
        "status": record.get("flight_status") or "Status unavailable",
        "from": departure.get("airport") or "Airport unavailable",
        "from_code": departure.get("iata") or "—",
        "to": arrival.get("airport") or "Airport unavailable",
        "to_code": arrival.get("iata") or "—",
        "time": parsed_time.strftime("%d %b %Y · %H:%M %Z"),
        "time_iso": parsed_time.isoformat(),
        "datetime": parsed_time,
    }


@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    error = None
    values = {
        "first_number": "",
        "second_number": "",
        "first_date": "",
        "second_date": "",
    }

    if request.method == "POST":
        values = {
            "first_number": normalise_flight_number(
                request.form.get("first_number", "")
            ),
            "second_number": normalise_flight_number(
                request.form.get("second_number", "")
            ),
            "first_date": request.form.get("first_date", "").strip(),
            "second_date": request.form.get("second_date", "").strip(),
        }

        if not values["second_date"]:
            values["second_date"] = values["first_date"]

        if not valid_flight_number(values["first_number"]):
            error = "Check the first flight number. Example: SQ318."
        elif not valid_flight_number(values["second_number"]):
            error = "Check the connecting flight number. Example: BA123."
        else:
            try:
                datetime.strptime(values["first_date"], "%Y-%m-%d")
                datetime.strptime(values["second_date"], "%Y-%m-%d")
            except ValueError:
                error = "Please enter both dates in YYYY-MM-DD format."
        
        api_key = os.getenv("AVIATIONSTACK_API_KEY", "").strip()
        if not error and not api_key:
            error = "The API key is not set. Add AVIATIONSTACK_API_KEY to your private .env file."

        if not error:
            try:
                first_record = fetch_flight(
                    api_key, values["first_number"], values["first_date"]
                )
                second_record = fetch_flight(
                    api_key, values["second_number"], values["second_date"]
                )

                first = flight_card(
                    first_record, values["first_number"], "arrival"
                )
                second = flight_card(
                    second_record, values["second_number"], "departure"
                )

                first_airport = (
                    (first_record.get("arrival") or {}).get("iata") or ""
                ).upper()
                second_airport = (
                    (second_record.get("departure") or {}).get("iata") or ""
                ).upper()

                if first_airport and second_airport and first_airport != second_airport:
                    error = (
                        f"These flights use different airports "
                        f"({first_airport} and {second_airport}). "
                        "This calculator currently checks same-airport connections only."
                    )
                else:
                    minutes = int(
                        (second["datetime"] - first["datetime"]).total_seconds()
                        // 60
                    )
                    result = {
                        "first": first,
                        "second": second,
                        "minutes": minutes,
                        "positive": minutes > 0,
                        "duration": format_duration(minutes),
                        "airport": first_airport or second_airport or "Airport not confirmed",
                    }
            except RuntimeError as exc:
                message = str(exc)
                if "No matching record" in message or "No exact record" in message:
                    error = (
                        message
                        + " Check the flight number and date. The API may not cover "
                        "this flight or future schedules on your current plan. "
                        "Try a flight with a record available in your API account."
                    )
                else:
                    error = message
            except Exception:
                error = (
                    "Something unexpected happened while checking the flights. "
                    "Please try again. No connection result has been estimated."
                )

    return render_template("index.html", result=result, error=error, values=values)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
