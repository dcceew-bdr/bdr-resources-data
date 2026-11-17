# Matches AFD complete names in extract.csv against the BDR and writes match.csv
# with an NSL_MATCH column. Unmatched names are retried first without any
# parenthetical text, then with only a parenthesized second word removed.

import argparse
import csv
import json
import re
from pathlib import Path

from httpx2 import Client
from kurra.db.sparql import query
from rdflib import Literal

COLUMNS = ("COMPLETE_NAME", "COMMON_NAMES", "NSL_MATCH")


def strip_parentheticals(name: str) -> str:
    parts = []
    depth = 0
    for char in name:
        if char == "(":
            depth += 1
        elif char == ")" and depth:
            depth -= 1
        elif not depth:
            parts.append(char)
    return " ".join("".join(parts).split())


def lookup(endpoint: str, name: str, client: Client) -> str:
    statement = f"""PREFIX dwc: <http://rs.tdwg.org/dwc/terms/>
SELECT ?x
WHERE {{
    ?x dwc:scientificName {Literal(name).n3()} .
}}
LIMIT 1"""
    response = query(endpoint, statement, http_client=client)
    bindings = json.loads(response)["results"]["bindings"] if response else []
    return bindings[0]["x"]["value"] if bindings else ""


def strip_second_word(name: str) -> str:
    words = name.split()
    if len(words) > 1 and re.fullmatch(r"\([^()]+\)", words[1]):
        return " ".join(words[:1] + words[2:])
    return ""


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group()
    modes.add_argument(
        "--fallback-only",
        action="store_true",
        help="Retry unmatched rows in the existing match.csv.",
    )
    modes.add_argument(
        "--second-word-only",
        action="store_true",
        help="Retry unmatched rows in match.csv by removing a parenthesized second word.",
    )
    args = parser.parse_args()
    directory = Path(__file__).resolve().parent
    settings = dict(
        line.strip().split("=", 1)
        for line in (directory / ".env").read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    )
    endpoint = settings["SPARQL_ENDPOINT"]

    output_path = directory / "match.csv"
    retry_existing = args.fallback_only or args.second_word_only
    input_path = output_path if retry_existing else directory / "extract.csv"
    with input_path.open(encoding="utf-8-sig", newline="") as source:
        rows = list(csv.DictReader(source))

    matches: dict[str, str] = {}
    passes = []
    if not args.second_word_only:
        passes.append(("All parentheses", strip_parentheticals))
    passes.append(("Parenthesized second word", strip_second_word))
    with Client(
        auth=(settings["SPARQL_USERNAME"], settings["SPARQL_PASSWORD"])
    ) as client:
        if not retry_existing:
            for row in rows:
                name = row["COMPLETE_NAME"]
                if name not in matches:
                    matches[name] = lookup(endpoint, name, client)
                row["NSL_MATCH"] = matches[name]

        for label, clean_name in passes:
            previous_queries = len(matches)
            new_matches = 0
            for row in rows:
                if row["NSL_MATCH"]:
                    continue
                name = clean_name(row["COMPLETE_NAME"])
                if not name:
                    continue
                if name not in matches:
                    matches[name] = lookup(endpoint, name, client)
                row["NSL_MATCH"] = matches[name]
                new_matches += bool(matches[name])
            print(
                f"{label}: {len(matches) - previous_queries:,} queries; "
                f"{new_matches:,} newly matched rows."
            )

    with output_path.open("w", encoding="utf-8", newline="") as output:
        writer = csv.DictWriter(output, fieldnames=COLUMNS)
        writer.writeheader()
        writer.writerows(rows)

    matched = sum(bool(row["NSL_MATCH"]) for row in rows)
    print(
        f"Queried {len(matches):,} distinct names; matched {matched:,} of {len(rows):,} rows."
    )


if __name__ == "__main__":
    main()
