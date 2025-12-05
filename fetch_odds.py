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

    event_name = os.getenv("GITHUB_EVENT_NAME", "")
    suffix = "_M" if event_name == "workflow_dispatch" else ""
    filename = f"data/nba_spreads_{today_date}{suffix}.csv"

    # ------------------------------------------
    # 1. First pass — discover all bookmakers
    # ------------------------------------------
    all_bookmakers = set()

    for game in data:
        for bookmaker in game.get("bookmakers", []):
            all_bookmakers.add(bookmaker["title"])

    # Sort for consistent column order
    all_bookmakers = sorted(list(all_bookmakers))

    # ------------------------------------------
    # 2. Build CSV header dynamically
    # ------------------------------------------
    header = [
        "date",
        "game_id",
        "home_team",
        "away_team",
    ]

    # Add columns: bookmaker_point, bookmaker_price
    for book in all_bookmakers:
        safe_book = book.replace(" ", "_").replace("-", "_")
        header.append(f"{safe_book}_point")
        header.append(f"{safe_book}_price")

    # ------------------------------------------
    # 3. Write data row per game
    # ------------------------------------------
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        for game in data:
            row = {
                "date": today_date,
                "game_id": game["id"],
                "home_team": game["home_team"],
                "away_team": game["away_team"],
            }

            home = game["home_team"]

            # Initialize all bookmaker columns as blank
            for book in all_bookmakers:
                safe_book = book.replace(" ", "_").replace("-", "_")
                row[f"{safe_book}_point"] = ""
                row[f"{safe_book}_price"] = ""

            # Fill in data for each bookmaker
            for bookmaker in game.get("bookmakers", []):
                book_name = bookmaker["title"]
                safe_book = book_name.replace(" ", "_").replace("-", "_")

                # extract spreads market
                spreads_market = next(
                    (m for m in bookmaker.get("markets", []) if m.get("key") == "spreads"),
                    None
                )
                if not spreads_market:
                    continue

                # extract home spread only
                home_outcome = next(
                    (o for o in spreads_market.get("outcomes", []) if o.get("name") == home),
                    None
                )
                if not home_outcome:
                    continue

                row[f"{safe_book}_point"] = home_outcome.get("point")
                row[f"{safe_book}_price"] = home_outcome.get("price")

            # Write row in the correct header column order
            writer.writerow([row[col] for col in header])

    print(f"Saved {filename}")


if __name__ == "__main__":
    main()
