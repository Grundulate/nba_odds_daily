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

    # Create the data directory if it doesn't exist
    os.makedirs("data", exist_ok=True)

    today = datetime.now().strftime("%Y-%m-%d")
    filename = f"data/nba_spreads_{today}.csv"

    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["game_id", "home_team", "away_team", "bookmaker", "spread_point", "spread_price"])

        for game in data:
            home = game["home_team"]
            away = game["away_team"]

            for bookmaker in game.get("bookmakers", []):
                for market in bookmaker.get("markets", []):
                    for outcome in market.get("outcomes", []):
                        writer.writerow([
                            game["id"],
                            home,
                            away,
                            bookmaker["title"],
                            outcome.get("point"),
                            outcome.get("price")
                        ])

    print(f"Saved {filename}")

if __name__ == "__main__":
    main()
