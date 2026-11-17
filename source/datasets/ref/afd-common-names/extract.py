"""
Extracts Anamalia_all_ranks sorted.zip - source data file receives from Matthew Lockett at the Australian Faunal
Directory, to extract.csv, a 2-colum CSV file containing Complete Names v. Common Names.
"""
import csv
from pathlib import Path
from zipfile import ZipFile


def main() -> None:
    directory = Path(__file__).resolve().parent
    source = directory / "Anamalia_all_ranks sorted.csv"
    archive = source.with_suffix(".zip")
    columns = ("COMPLETE_NAME", "COMMON_NAMES")

    with ZipFile(archive) as zipped:
        zipped.extract(source.name, directory)

    with (
        source.open(encoding="utf-8-sig", newline="") as input_file,
        (directory / "extract.csv").open(
            "w", encoding="utf-8", newline=""
        ) as output_file,
    ):
        reader = csv.DictReader(input_file)
        writer = csv.DictWriter(output_file, fieldnames=columns)
        writer.writeheader()
        for row in reader:
            for entry in (row["COMMON_NAMES"] or "").split(","):
                common_name = entry.strip()
                if common_name:
                    writer.writerow(
                        {
                            "COMPLETE_NAME": row["COMPLETE_NAME"],
                            "COMMON_NAMES": common_name,
                        }
                    )


if __name__ == "__main__":
    main()
