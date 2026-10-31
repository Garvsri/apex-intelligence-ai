
import re
import unicodedata

import fastf1
import pandas as pd

from apex.ingestion import ingest_f1_session, load_manifest
SEASONS = range(2021, 2027)
SESSION_TYPE = "R"


def make_dataset_id(year, event_name):
    normalized = unicodedata.normalize("NFKD", event_name)
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")

    slug = re.sub(
        r"[^a-z0-9]+", "_", ascii_name.lower()
    ).strip("_")

    return f"f1_{year}_{slug}_race_tyres"


def dataset_already_registered(dataset_id):
    manifest = load_manifest()

    return any(
        entry.get("dataset_id") == dataset_id
        for entry in manifest["datasets"]
    )


def main():
    successful = []
    skipped = []
    failed = []

    for year in SEASONS:
        print("\n" + "#" * 70)
        print(f"STARTING F1 {year} SEASON")
        print("#" * 70)

        try:
            schedule = fastf1.get_event_schedule(
                year,
                include_testing=False,
            )

            races = schedule[schedule["RoundNumber"] > 0]

        except Exception as error:
            print(f"Could not load {year} schedule: {error}")
            failed.append({
                "season": year,
                "race": "SEASON SCHEDULE",
                "error": str(error),
            })
            continue

        print(f"Grand Prix discovered: {len(races)}")

        for event in races.itertuples(index=False):
            event_name = event.EventName
            round_number = event.RoundNumber

            dataset_id = make_dataset_id(year, event_name)

            print("\n" + "-" * 60)
            print(f"{year} Round {round_number}: {event_name}")

            if dataset_already_registered(dataset_id):
                print("SKIPPED: Already registered.")
                skipped.append((year, event_name))
                continue

            try:
                result = ingest_f1_session(
                    year=year,
                    grand_prix=event_name,
                    session_type=SESSION_TYPE,
                    dataset_id=dataset_id,
                )

                df = pd.read_csv(result["csv_path"])

                tyre_records = 0
                compounds = []

                if "compound" in df.columns:
                    tyre_records = int(
                        df["compound"].notna().sum()
                    )

                    compounds = sorted(
                        df["compound"]
                        .dropna()
                        .unique()
                        .tolist()
                    )

                item = {
                    "season": year,
                    "race": event_name,
                    "dataset_id": dataset_id,
                    "rows": result["rows_imported"],
                    "tyre_records": tyre_records,
                    "compounds": compounds,
                    "status": (
                        "imported_with_tyre_data"
                        if tyre_records > 0
                        else "imported_without_tyre_data"
                    ),
                }

                successful.append(item)

                print("SUCCESS")
                print(f"Rows: {item['rows']}")
                print(f"Tyre records: {tyre_records}")
                print(f"Compounds: {compounds}")

            except Exception as error:
                print(f"FAILED: {error}")

                failed.append({
                    "season": year,
                    "race": event_name,
                    "error": str(error),
                })

    print("\n" + "=" * 70)
    print("MULTI-SEASON TYRE INGESTION SUMMARY")
    print("=" * 70)

    print(f"Seasons processed: 2021–2026")
    print(f"Successful: {len(successful)}")
    print(f"Skipped: {len(skipped)}")
    print(f"Failed: {len(failed)}")

    print("\nSUCCESSFUL IMPORTS")

    for item in successful:
        print(
            f"{item['season']} | {item['race']} | "
            f"{item['tyre_records']} tyre records | "
            f"{item['status']}"
        )

    print("\nSKIPPED IMPORTS")

    for year, race in skipped:
        print(f"{year} | {race}")

    print("\nFAILED IMPORTS")

    for item in failed:
        print(
            f"{item['season']} | {item['race']} | "
            f"{item['error']}"
        )

    report = pd.DataFrame(successful + failed)

    report.to_csv(
        "tyre_ingestion_2021_2026_report.csv",
        index=False,
    )

    print("\nReport saved:")
    print("tyre_ingestion_2021_2026_report.csv")


if __name__ == "__main__":
    main()
