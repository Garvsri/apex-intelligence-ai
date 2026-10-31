
import csv
import json
from pathlib import Path
from urllib.parse import quote
from urllib.request import urlopen
from urllib.error import HTTPError, URLError

MANIFEST_PATH = Path("data/processed/manifest.json")
API_BASE = "http://127.0.0.1:8000"

manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))

datasets = [
    entry
    for entry in manifest["datasets"]
    if "race_tyres" in entry.get("dataset_id", "")
    and entry.get("status") == "imported"
    and entry.get("session_type") == "R"
]

results = []

print(f"Testing {len(datasets)} Grand Prix datasets...\n")

for entry in sorted(
    datasets,
    key=lambda x: (int(x["season"]), x["grand_prix"])
):
    season = int(entry["season"])
    grand_prix = entry["grand_prix"]

    url = (
        f"{API_BASE}/race/{season}/"
        f"{quote(grand_prix, safe='')}/stints"
    )

    try:
        with urlopen(url, timeout=30) as response:
            data = json.loads(response.read().decode("utf-8"))

        expected_id = entry["dataset_id"]
        actual_id = data.get("dataset_id")

        stints = data.get("stints", [])
        drivers = len({
            stint["driver"] for stint in stints
        })

        success = (
            actual_id == expected_id
            and len(stints) > 0
        )

        results.append({
            "season": season,
            "grand_prix": grand_prix,
            "drivers": drivers,
            "total_stints": len(stints),
            "status": "SUCCESS" if success else "CHECK",
            "dataset_id": actual_id,
        })

    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        results.append({
            "season": season,
            "grand_prix": grand_prix,
            "drivers": 0,
            "total_stints": 0,
            "status": "FAILED",
            "dataset_id": str(exc),
        })

    result = results[-1]

    print(
        f"{season} | {grand_prix:35} | "
        f"Drivers: {result['drivers']:2} | "
        f"Stints: {result['total_stints']:3} | "
        f"{result['status']}"
    )

output = Path("tyre_api_validation_report.csv")

with output.open("w", newline="", encoding="utf-8") as file:
    writer = csv.DictWriter(
        file,
        fieldnames=[
            "season",
            "grand_prix",
            "drivers",
            "total_stints",
            "status",
            "dataset_id",
        ],
    )
    writer.writeheader()
    writer.writerows(results)

successful = sum(r["status"] == "SUCCESS" for r in results)
failed = len(results) - successful

print("\n========== VALIDATION SUMMARY ==========")
print(f"Total races tested : {len(results)}")
print(f"Successful         : {successful}")
print(f"Failed / Check     : {failed}")
print(f"Report saved       : {output}")
