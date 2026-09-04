"""
AMIS Punjab Price Scraper for HarvestGuard  (v2 - auto-discovery)
--------------------------------------------------------------------
Fetches TODAY's wholesale prices from amis.pk for tracked crops and
merges them into data/market_prices.json (appends new dated entries,
never overwrites existing history).

v2 changes:
  - No price data is silently dropped. Any city AMIS reports a price
    for, but that HarvestGuard doesn't yet track as a market, is
    auto-geocoded (via free OpenStreetMap Nominatim) and added as a
    new market - flagged "_auto_discovered": true for later human
    review, but immediately usable by the recommendation engine.
  - Commodity-name safety check: verifies the fetched page actually
    is for the crop we asked for, before trusting its data. Protects
    against silently mislabeling one crop's prices as another's if
    AMIS's site behaves unexpectedly.

Usage:
    python amis_scraper.py          # run once, manually
    (or scheduled automatically via APScheduler in main.py)
"""

import re
import json
import time
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# CONFIG
# ---------------------------------------------------------------------------

# crop_id -> (AMIS commodityId, substring expected in the page's "Commodity:" name)
# The second value is a safety check - if AMIS returns a page whose commodity
# name doesn't contain this substring, we do NOT trust/store that data.
CROP_COMMODITY_MAP = {
    "mango_chaunsa": (48, "Chounsa"),
    "mango_sindhri": (56, "Sindhri"),
    "rice_basmati": (3, "Basmati"),
    "tomato": (26, "Tomato"),
    "potato": (21, "Potato"),
}

# Known AMIS city-name spelling quirks that don't match our market_id slugs
# cleanly. Only needed for existing markets with irregular naming - new
# cities are handled automatically via geocoding, no entry needed here.
CITY_NAME_OVERRIDES = {
    "DGKHAN": "Dera Ghazi Khan",
    "TALAGANG": "Talagang",
}

AMIS_BASE_URL = "http://www.amis.pk/ViewPrices.aspx"
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (HarvestGuard data collector)"}
REQUEST_TIMEOUT = 20

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"
# Nominatim's usage policy requires a descriptive User-Agent and max 1 req/sec.
NOMINATIM_HEADERS = {"User-Agent": "HarvestGuard-AgriTech-Hackathon/1.0 (contact: project email)"}
NOMINATIM_DELAY_SECONDS = 1.1

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRICES_FILE = DATA_DIR / "market_prices.json"
LOCATIONS_FILE = DATA_DIR / "markets.json"


# ---------------------------------------------------------------------------
# STEP 1 - fetch + parse one commodity's price table (with safety check)
# ---------------------------------------------------------------------------

def fetch_commodity_prices(crop_id: str, commodity_id: int, expected_name: str) -> list[dict]:
    """
    Fetch today's price table for one AMIS commodityId.
    Returns [] (with a warning) if the page's commodity name doesn't match
    what we expected - protects against silently storing mislabeled data.
    """
    url = f"{AMIS_BASE_URL}?searchType=0&commodityId={commodity_id}"
    response = requests.get(url, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    # --- Safety check: is this actually the commodity we asked for? ---
    page_text = soup.get_text()
    commodity_match = re.search(r"Commodity:\s*([^\n\[]+)", page_text)
    actual_name = commodity_match.group(1).strip() if commodity_match else ""
    if expected_name.lower() not in actual_name.lower():
        print(f"[SCRAPER]   SAFETY CHECK FAILED for {crop_id}: expected commodity "
              f"containing '{expected_name}', page shows '{actual_name}'. "
              f"Skipping this crop this run rather than risk mislabeled data.")
        return []

    # Find the actual price table (not one of the several layout tables AMIS
    # puts before it) by locating the one that contains "FQP".
    table = None
    for candidate in soup.find_all("table"):
        if "FQP" in candidate.get_text():
            table = candidate
            break
    if table is None:
        print(f"[SCRAPER]   WARNING: no price table found for {crop_id}")
        return []

    results = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 5:
            continue

        city_link = cells[0].find("a")
        city = city_link.get_text(strip=True) if city_link else \
            re.sub(r"^\d+\s*", "", cells[0].get_text(strip=True))

        min_txt = cells[2].get_text(strip=True)
        max_txt = cells[3].get_text(strip=True)
        fqp_txt = cells[4].get_text(strip=True)

        if "-" in (min_txt, max_txt, fqp_txt) or not min_txt:
            continue

        try:
            results.append({
                "city": city,
                "min": float(min_txt),
                "max": float(max_txt),
                "fqp": float(fqp_txt),
            })
        except ValueError:
            continue

    return results


def scrape_all_crops() -> dict:
    all_data = {}
    for crop_id, (commodity_id, expected_name) in CROP_COMMODITY_MAP.items():
        print(f"[SCRAPER] Fetching {crop_id} (commodityId={commodity_id})...")
        try:
            rows = fetch_commodity_prices(crop_id, commodity_id, expected_name)
            all_data[crop_id] = rows
            print(f"[SCRAPER]   -> {len(rows)} cities with live prices")
        except requests.RequestException as e:
            print(f"[SCRAPER]   -> ERROR fetching {crop_id}: {e}")
            all_data[crop_id] = []
    return all_data


# ---------------------------------------------------------------------------
# STEP 2 - geocoding for auto-discovered cities
# ---------------------------------------------------------------------------

def slugify_city(city: str) -> str:
    """'DunyaPur' -> 'dunyapur_mandi' style market_id."""
    slug = re.sub(r"[^a-z0-9]+", "_", city.lower()).strip("_")
    return f"{slug}_mandi"


def geocode_city(city: str, province: str = "Punjab"):
    """
    Look up lat/long for a city via free OpenStreetMap Nominatim.
    Returns (lat, lon) tuple or None if not found. Respects Nominatim's rate limit.
    """
    params = {
        "q": f"{city}, {province}, Pakistan",
        "format": "json",
        "limit": 1,
    }
    try:
        resp = requests.get(NOMINATIM_URL, params=params,
                             headers=NOMINATIM_HEADERS, timeout=10)
        resp.raise_for_status()
        results = resp.json()
        time.sleep(NOMINATIM_DELAY_SECONDS)  # be a polite API citizen
        if not results:
            return None
        return float(results[0]["lat"]), float(results[0]["lon"])
    except (requests.RequestException, KeyError, ValueError, IndexError) as e:
        print(f"[SCRAPER]   WARNING: geocoding failed for '{city}': {e}")
        return None


# ---------------------------------------------------------------------------
# STEP 3 - merge into market_prices.json + markets.json (auto-creating
#          new markets for cities we don't track yet, instead of dropping
#          their price data)
# ---------------------------------------------------------------------------

def load_json(path: Path, default):
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default


def save_json(path: Path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def update_market_prices_file(scraped_data: dict) -> dict:
    """
    Merges freshly-scraped prices into market_prices.json. Any city with
    real price data that we don't yet have a market entry for gets
    auto-geocoded and added to markets.json (flagged for review), rather
    than having its price data silently discarded.

    Returns a summary dict: {"new_entries": int, "new_markets": [city names]}
    """
    today = datetime.now().strftime("%Y-%m-%d")

    prices_data = load_json(PRICES_FILE, [])
    locations_data = load_json(LOCATIONS_FILE, [])

    market_by_id = {m["market_id"]: m for m in prices_data}
    location_by_id = {m["market_id"]: m for m in locations_data}

    # Build a live city -> market_id lookup from whatever markets we
    # currently know about (instead of a hardcoded dict that goes stale).
    city_to_market_id = {}
    for loc in locations_data:
        city_to_market_id[loc["city"]] = loc["market_id"]
    for amis_name, real_name in CITY_NAME_OVERRIDES.items():
        if real_name in city_to_market_id:
            city_to_market_id[amis_name] = city_to_market_id[real_name]

    new_entries_count = 0
    newly_discovered_cities = []

    for crop_id, price_rows in scraped_data.items():
        for row in price_rows:
            city = row["city"]
            market_id = city_to_market_id.get(city)

            if market_id is None:
                # --- Auto-discovery: don't drop this price data ---
                coords = geocode_city(city)
                if coords is None:
                    print(f"[SCRAPER]   Could not geocode new city '{city}' - "
                          f"price data for this city skipped this run "
                          f"(will retry next scrape).")
                    continue

                market_id = slugify_city(city)
                lat, lon = coords
                new_location = {
                    "market_id": market_id,
                    "market_name": f"{city} Mandi",
                    "city": city,
                    "province": "Punjab",
                    "latitude": round(lat, 4),
                    "longitude": round(lon, 4),
                    "market_type": "wholesale",
                    "primary_crops": [crop_id],
                    "is_premium": False,
                    "cold_storage_available": False,
                    "_auto_discovered": True,
                    "_discovered_date": today,
                    "_note": "Auto-added by scraper from live AMIS data. Verify "
                             "coordinates and enrich cold_storage_available / "
                             "is_premium / primary_crops manually when convenient - "
                             "safe to use for price/distance decisions as-is."
                }
                locations_data.append(new_location)
                location_by_id[market_id] = new_location
                city_to_market_id[city] = market_id
                newly_discovered_cities.append(city)
                print(f"[SCRAPER]   Auto-discovered new market: {city} "
                      f"-> {market_id} ({lat:.4f}, {lon:.4f})")

                prices_data.append({"market_id": market_id, "market_name": f"{city} Mandi",
                                     "city": city, "province": "Punjab", "prices": []})
                market_by_id[market_id] = prices_data[-1]

            if market_id not in market_by_id:
                # Market exists in locations but not yet in prices file - create it
                prices_data.append({"market_id": market_id,
                                     "market_name": location_by_id[market_id]["market_name"],
                                     "city": city, "province": "Punjab", "prices": []})
                market_by_id[market_id] = prices_data[-1]

            existing_prices = market_by_id[market_id]["prices"]
            already_scraped_today = any(
                p["crop_id"] == crop_id and p["date"] == today for p in existing_prices
            )
            if already_scraped_today:
                continue

            existing_prices.append({
                "crop_id": crop_id,
                "date": today,
                "price_min_per_kg": round(row["min"] / 100, 2),
                "price_max_per_kg": round(row["max"] / 100, 2),
                "price_avg_per_kg": round(row["fqp"] / 100, 2),
                "supply_level": "unknown",
                "demand_level": "unknown",
                "_source": "auto_scraped",
            })
            new_entries_count += 1

    save_json(PRICES_FILE, prices_data)
    if newly_discovered_cities:
        save_json(LOCATIONS_FILE, locations_data)

    return {"new_entries": new_entries_count, "new_markets": newly_discovered_cities}


# ---------------------------------------------------------------------------
# ENTRY POINT
# ---------------------------------------------------------------------------

def run_daily_scrape():
    print(f"\n[SCRAPER] ===== Starting AMIS scrape: {datetime.now()} =====")
    scraped_data = scrape_all_crops()
    summary = update_market_prices_file(scraped_data)
    print(f"[SCRAPER] Done. {summary['new_entries']} new price entries written "
          f"for {datetime.now().strftime('%Y-%m-%d')}.")
    if summary["new_markets"]:
        print(f"[SCRAPER] Auto-discovered {len(summary['new_markets'])} new "
              f"market(s): {summary['new_markets']}")
    print()
    return summary


if __name__ == "__main__":
    run_daily_scrape()