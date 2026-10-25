import csv
import sys
from datetime import date
from pathlib import Path

import requests
from bs4 import BeautifulSoup

URL = "https://www.screener.in/market/"
CSV_FILE = Path(__file__).with_name("median_pe_history.csv")
FIELDS = ["date", "industry", "median_pe"]
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def parse_number(text):
    cleaned = text.strip().replace(",", "").replace("%", "")
    try:
        float(cleaned)
        return cleaned
    except ValueError:
        return ""


def fetch_data():
    resp = requests.get(URL, headers=HEADERS, timeout=30)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    table = soup.find("table")
    if table is None:
        sys.exit("Table nahi mili.")

    pe_index = None
    for th in table.find_all("th"):
        if "median p/e" in th.get_text(strip=True).lower():
            pe_index = len(th.find_previous_siblings(["th", "td"]))
            break
    if pe_index is None:
        sys.exit("'Median P/E' column nahi mila.")

    rows = []
    for tr in table.find_all("tr"):
        cells = tr.find_all("td")
        if len(cells) <= pe_index or not cells[0].get_text(strip=True).rstrip(".").isdigit():
            continue
        industry = cells[1].get_text(strip=True)
        rows.append((industry, parse_number(cells[pe_index].get_text())))
    return rows


def save(rows):
    today = date.today().isoformat()

    existing = []
    if CSV_FILE.exists():
        with CSV_FILE.open(newline="", encoding="utf-8") as f:
            existing = [r for r in csv.DictReader(f) if r["date"] != today]

    with CSV_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(existing)
        for industry, pe in rows:
            writer.writerow({"date": today, "industry": industry, "median_pe": pe})


def main():
    rows = fetch_data()
    if len(rows) < 150:
        sys.exit(f"Sirf {len(rows)} industries mili. Save nahi kiya.")
    save(rows)
    print(f"{len(rows)} industries save ho gayi.")


if __name__ == "__main__":
    main()
