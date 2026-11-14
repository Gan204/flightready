# FlightReady API test

This is the first backend experiment. It asks Aviationstack for a flight number and displays the flight status, departure and arrival information.

## 1. Get an API key

Create an Aviationstack account and copy your API access key. The free plan currently advertises 100 requests per month. Do not share your key in chat or put it in GitHub.

## 2. Set up your key

In the main FlightReady folder, copy `.env.example` and name the copy `.env`.

Open `.env` and replace the placeholder with your key:

```text
AVIATIONSTACK_API_KEY=your_real_key_goes_here
```

The `.env` file is ignored by Git, so it should stay on your computer.

## 3. Run the test

Python 3.9 or newer is recommended. No extra Python packages are needed.

From the main FlightReady folder, run:

```bash
python backend/flight_test.py
```

When asked, enter a flight number such as `SQ318`.

You can also pass the flight number directly:

```bash
python backend/flight_test.py SQ318
```

Use a flight that is operating now or has recently operated. The free plan does not include future-flight schedule endpoints.

## What success looks like

The program should print the flight number, airline, status, departure airport and times, and arrival airport and times.

If no record is returned, try another flight number. API coverage can vary.

## Important limitations

- This is only a first API connection test; it does not calculate connection risk yet.
- Flight data may be delayed, incomplete or unavailable.
- Always confirm travel details with the airline or airport.
- Do not use this prototype as the sole basis for travel decisions.
