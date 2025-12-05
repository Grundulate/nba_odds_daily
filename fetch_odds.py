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

    os.makedirs("data", exist_ok=True)

    today_date = datetime.now().strftime("%Y-%m-%d")

    # Filename suffix if the workflow is run manually
    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    suffix = "_M" if event_name == "workflow_dispatch" else ""

    filename = f"data/nba_spreads_{today_date}{suffix}.csv"

    # ------------------------------------------
    # 1. Discover all bookmakers that appear today
    # ------------------------------------------
    all_bookmakers = set()

    for game in data:
        for bookmaker in game.get("bookmakers", []):
            all_bookmakers.add(bookmaker["title"])

    all_bookmakers = sorted(list(all_bookmakers))

    # ------------------------------------------
    # 2. Build CSV header
    # ------------------------------------------
    header = [
        "date",
        "game_id",
        "home_team",
        "away_team",
    ]

    for book in all_bookmakers:
        safe = book.replace(" ", "_").replace("-", "_")
        header += [
            f"{safe}_home_point",
            f"{safe}_home_price",
            f"{safe}_away_point",
            f"{safe}_away_price",
        ]

    # ------------------------------------------
    # 3. Write data rows (one per game)
    # ------------------------------------------
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for game in data:
            home_team = game["home_team"]
            away_team = game["away_team"]
            game_id = game["id"]

            # Start row with basic info
            row = {
                "date": today_date,
                "game_id": game_id,
                "home_team": home_team,
                "away_team": away_team,
            }

            # Initialize all bookmaker fields blank
            for book in all_bookmakers:
                safe = book.replace(" ", "_").replace("-", "_")
                row[f"{safe}_home_point"] = ""
                row[f"{safe}_home_price"] = ""
                row[f"{safe}_away_point"] = ""
                row[f"{safe}_away_price"] = ""

            # Fill row with bookmaker data
            for bookmaker in game.get("bookmakers", []):
                book_name = bookmaker["title"]
                safe = book_name.replace(" ", "_").replace("-", "_")

                spreads_market = next(
                    (m for m in bookmaker.get("markets", []) if m.get("key") == "spreads"),
                    None
                )
                if not spreads_market:
                    continue

                # outcomes include home + away spreads
                outcomes = spreads_market.get("outcomes", [])

                home_outcome = next((o for o in outcomes if o.get("name") == home_team), None)
                away_outcome = next((o for o in outcomes if o.get("name") == away_team), None)

                if home_outcome:
                    row[f"{safe}_home_point"] = home_outcome.get("point")
                    row[f"{safe}_home_price"] = home_outcome.get("price")

                if away_outcome:
                    row[f"{safe}_away_point"] = away_outcome.get("point")
                    row[f"{safe}_away_price"] = away_outcome.get("price")

            # Write row in header order
            writer.writerow([row[col] for col in header])

    print(f"Saved {filename}")


if __name__ == "__main__":
    main()
