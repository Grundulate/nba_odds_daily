import requests
import csv
from datetime import datetime
import os

def main():
    API_KEY = os.getenv("ODDS_API_KEY")
    SPORT = "basketball_nba"
    REGIONS = "us"
    MARKETS = "spreads"
    ODDS_FORMAT = "american"

    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds"

    params = {
        "apiKey": API_KEY,
        "regions": REGIONS,
        "markets": MARKETS,
        "oddsFormat": ODDS_FORMAT,
    }

    response = requests.get(url, params=params)
    response.raise_for_status()
    data = response.json()

    # Prepare output directory
    os.makedirs("data", exist_ok=True)

    # Date for filename + CSV column
    today_date = datetime.now().strftime("%Y-%m-%d")

    # Add _M to the filename if run manually
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    suffix = "_M" if event_name == "workflow_dispatch" else ""

    filename = f"data/nba_spreads_{today_date}{suffix}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)

        # Add date column + other columns
        writer.writerow([
            "date",
            "game_id",
            "home_team",
            "away_team",
            "bookmaker",
            "home_spread_point",
            "home_spread_price"
        ])

        for game in data:
            home = game["home_team"]
            away = game["away_team"]
            game_id = game["id"]

            for bookmaker in game.get("bookmakers", []):
                # Each bookmaker has one "spreads" market
                spreads_market = next(
                    (m for m in bookmaker.get("markets", []) if m.get("key") == "spreads"),
                    None
                )
                if not spreads_market:
                    continue

                # Outcomes contain home & away spreads — find home outcome
                home_outcome = next(
                    (o for o in spreads_market.get("outcomes", []) if o.get("name") == home),
                    None
                )
                if not home_outcome:
                    continue

                writer.writerow([
                    today_date,
                    game_id,
                    home,
                    away,
                    bookmaker["title"],
                    home_outcome.get("point"),
                    home_outcome.get("price")
                ])

    print(f"Saved {filename}")

if __name__ == "__main__":
    main()
