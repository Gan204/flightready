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
- [ ] Successful real-flight API test
- [ ] Connection time calculation
- [ ] Basic user interface
- [ ] First version deployed

## Technology

- Python for the first backend API test
- Aviationstack for initial flight data research

## Repository Structure

- `backend/flight_test.py` — first flight-data retrieval test
- `backend/README.md` — setup and run instructions
- `.env.example` — safe API-key template
- `.gitignore` — keeps local API keys out of Git

## Disclaimer

FlightReady is an independent passenger-support prototype, not an official airline service. Flight information may be delayed or incomplete. Always verify travel details with the airline or airport.
