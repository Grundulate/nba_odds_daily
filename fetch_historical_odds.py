import requests
import csv
from datetime import datetime, timedelta, timezone
import time
import os
import sys

API_KEY = os.getenv("ODDS_API_KEY")
if not API_KEY:
    print("ERROR: ODDS_API_KEY environment variable is not set.")
    sys.exit(1)

SPORT = "basketball_nba"
REGIONS = "us"
MARKETS = "spreads"
ODDS_FORMAT = "american"

# Historical endpoint
ODDS_URL = "https://api.the-odds-api.com/v4/historical/sports/{sport}/odds"

# ---- CONFIG ----
START_DATE = datetime(2020, 7, 1)   # earliest supported date for NBA historical
END_DATE = datetime(2020, 11, 1)
THROTTLE_SECONDS = 1                # avoid rate limit
# -----------------

os.makedirs("data", exist_ok=True)

current = START_DATE

def get_snapshot_iso(dt):
    """Return ISO string for 4pm Central (22:00 UTC)."""
    return dt.replace(hour=22, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


while current <= END_DATE:
    iso_timestamp = get_snapshot_iso(current)
    print(f"Fetching historical odds for: {iso_timestamp}")

    url = ODDS_URL.format(sport=SPORT)
    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "date": iso_timestamp
    }

    resp = requests.get(url, params=params)

    # Debug: Show raw API response (first 300 chars)
    print(f"Raw response for {current.date()}: {resp.text[:300]}")

    if resp.status_code != 200:
        print(f"[{current.date()}] Error {resp.status_code}: {resp.text}")
        current += timedelta(days=1)
        time.sleep(THROTTLE_SECONDS)
        continue

    # Safely attempt JSON decoding
    try:
        data = resp.json()
    except Exception as e:
        print(f"[{current.date()}] JSON decode error: {e}")
        current += timedelta(days=1)
        time.sleep(THROTTLE_SECONDS)
        continue

    # Ensure the response is a list (as expected)
    if not isinstance(data, list):
        print(f"[{current.date()}] Unexpected API response (not a list). Full response:")
        print(data)
        current += timedelta(days=1)
        time.sleep(THROTTLE_SECONDS)
        continue

    if not data:
        print(f"[{current.date()}] No odds available.")
        current += timedelta(days=1)
        time.sleep(THROTTLE_SECONDS)
        continue



    # Collect all bookmakers
    all_books = set()
    for game in data:
        for b in game.get("bookmakers", []):
            all_books.add(b["key"])

    # Base columns
    header = ["date", "game_id", "home_team", "away_team"]

    # For each bookmaker produce: home_spread, home_price, away_spread, away_price
    for book in sorted(all_books):
        header.extend([
            f"{book}_home_spread",
            f"{book}_home_price",
            f"{book}_away_spread",
            f"{book}_away_price",
        ])

    output_date = current.strftime("%Y-%m-%d")
    filename = f"data/nba_spreads_{output_date}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for game in data:
            row = [
                output_date,
                game.get("id", ""),
                game.get("home_team", ""),
                game.get("away_team", "")
            ]

            # Build a dictionary for lookup
            book_dict = {b["key"]: b for b in game.get("bookmakers", [])}

            for book in sorted(all_books):
                entry = book_dict.get(book)

                if entry:
                    markets = entry.get("markets", [])
                    spread_market = next((m for m in markets if m["key"] == "spreads"), None)

                    if spread_market:
                        outcomes = spread_market["outcomes"]

                        # Initialize values
                        home_spread = home_price = away_spread = away_price = ""

                        for o in outcomes:
                            if o["name"] == game["home_team"]:
                                home_spread = o.get("point", "")
                                home_price = o.get("price", "")
                            elif o["name"] == game["away_team"]:
                                away_spread = o.get("point", "")
                                away_price = o.get("price", "")

                        row.extend([home_spread, home_price, away_spread, away_price])
                    else:
                        row.extend(["", "", "", ""])
                else:
                    row.extend(["", "", "", ""])

            writer.writerow(row)

    print(f"Saved: {filename}")
    current += timedelta(days=1)
    time.sleep(THROTTLE_SECONDS)

print("\nDone fetching historical NBA odds.\n")
