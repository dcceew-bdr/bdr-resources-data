"""Extract scientific and common names from the SPRAT search results."""

import csv
from pathlib import Path


def main() -> None:
    directory = Path(__file__).resolve().parent
    input_path = directory / "sprat-search-results-20261118.csv"
    output_path = directory / "extract.csv"
    count = 0
    seen = set()

    with (
        input_path.open(encoding="utf-8-sig", newline="") as source,
        output_path.open("w", encoding="utf-8", newline="") as destination,
    ):
        reader = csv.DictReader(source)
        writer = csv.writer(destination)
        writer.writerow(["Current Scientific Name", "Common Names"])
        for row in reader:
            for common_name in row["Common Name"].split(","):
                common_name = common_name.strip().removeprefix("an ").strip()
                pair = (row["Current Scientific Name"], common_name)
                if common_name and pair not in seen:
                    seen.add(pair)
                    writer.writerow(pair)
                    count += 1

    print(f"Wrote {count} rows to {output_path}")


if __name__ == "__main__":
    main()
