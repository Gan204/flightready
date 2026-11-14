# FlightReady ✈️

FlightReady is a flight connection risk assessment tool that aims to use real-world flight data.

## Problem

Flight delays can cause passengers to miss connecting flights. Passengers may struggle to understand how a delay affects their onward journey.

## Solution

FlightReady will retrieve flight information and estimate whether a connecting flight is safe, at risk, or likely to be missed.

## Planned Features

- Search using two flight numbers
- Retrieve flight information using an API
- Calculate available connection time
- Display a connection risk assessment

## Current Progress

- [x] Project concept established
- [x] GitHub repository created
- [x] Flight API selected for initial testing (Aviationstack)
- [x] Successful real-flight API test
- [x] First two-flight connection time calculator (prototype; needs validation)
- [ ] Basic user interface
- [ ] First version deployed

## Technology

- Python for the first backend API test
- Aviationstack for initial flight data research

## Repository Structure

- `backend/flight_test.py` — first flight-data retrieval test
- `backend/connection_test.py` — two-flight connection-time calculator prototype
- `backend/README.md` — setup and run instructions
- `.env.example` — safe API-key template
- `.gitignore` — keeps local API keys out of Git

## Disclaimer

FlightReady is an independent passenger-support prototype, not an official airline service. Flight information may be delayed or incomplete. Always verify travel details with the airline or airport.


## Run the connection calculator

In GitHub Codespaces, run:

```bash
python backend/connection_test.py
```

Enter the first flight number, connecting flight number, and each flight's
 departure date (`YYYY-MM-DD`). Press Enter for the connecting-flight date if
 it is the same as the first flight's date. Separate dates support connections
 that cross midnight. Flight numbers are accepted in upper-, lower-, or mixed-case,
and the lookup supports different airline codes.

The prototype calculates the time from Flight A's actual/estimated arrival to
Flight B's scheduled departure. It does not invent a minimum connection time:
until reliable airport/terminal/airline requirements are available, it will not
label a positive connection time as definitely safe or at risk. It also does
not provide a personalised action plan; those features are deferred in the MVP.

The current Aviationstack flights endpoint may not return every future flight
or every date on the free plan. If a flight/date is not returned, FlightReady
will show an error rather than inventing a result.
