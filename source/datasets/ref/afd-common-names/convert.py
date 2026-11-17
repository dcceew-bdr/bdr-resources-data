"""Generate the AFD common-name lookup graph from match.csv, offline."""

import csv
import json
import re
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import NAMESPACE_URL, uuid5

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT.parents[3] / "resources/datasets/items/afd-common-names.ttl"
DATASET = URIRef("https://linked.data.gov.au/dataset/afd-common-names")
AFD = Namespace("https://id.biodiversity.org.au/name/afd/")
DWC = Namespace("http://rs.tdwg.org/dwc/terms/")
SCHEMA = Namespace("https://schema.org/")
COLUMNS = ["COMPLETE_NAME", "COMMON_NAMES", "NSL_MATCH"]


def read_lookup_pairs(source: Path) -> tuple[set[tuple[URIRef, Literal]], int]:
    """Keep every distinct matched name pair and count matched source rows."""
    pairs = set()
    matched = 0
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != COLUMNS:
            raise ValueError(f"Unexpected CSV columns: {reader.fieldnames}")
        for number, row in enumerate(reader, start=2):
            match = (row["NSL_MATCH"] or "").strip()
            if not match:
                continue
            common = row["COMMON_NAMES"]
            if not re.fullmatch(re.escape(str(AFD)) + r"[0-9]+", match) or not (
                common and common.strip()
            ):
                raise ValueError(f"CSV row {number}: invalid AFD name or common name")
            pairs.add((URIRef(match), Literal(common)))
            matched += 1
    return pairs, matched


def build_graph(pairs: set[tuple[URIRef, Literal]]) -> Graph:
    graph = Graph().parse(ROOT / "dataset-metadata.ttl", format="turtle")
    if set(graph.subjects(RDF.type, SCHEMA.Dataset)) != {DATASET}:
        raise ValueError("Metadata must describe the AFD common names dataset")
    graph.bind("afd", AFD)
    graph.bind("dwc", DWC)
    graph.bind("", Namespace(f"{DATASET}/"), replace=True)

    for name, common in pairs:
        # Use stable UUIDs so reconversion preserves statement identities.
        key = json.dumps([str(DATASET), str(name), str(common)], ensure_ascii=False)
        statement = URIRef(f"{DATASET}/{uuid5(NAMESPACE_URL, key)}")
        graph.add((name, DWC.vernacularName, common))
        graph.add((DATASET, RDFS.member, statement))
        graph.add((statement, RDF.type, RDF.Statement))
        graph.add((statement, RDF.subject, name))
        graph.add((statement, RDF.predicate, DWC.vernacularName))
        graph.add((statement, RDF.object, common))
    return graph


def main() -> None:
    pairs, matched = read_lookup_pairs(ROOT / "match.csv")
    graph = build_graph(pairs)
    if next(graph.triples((None, DWC.scientificName, None)), None) is not None:
        raise ValueError("The dataset must not contain scientific-name triples")

    with TemporaryDirectory(dir=OUTPUT.parent) as staging:
        temporary = Path(staging) / OUTPUT.name
        graph.serialize(destination=temporary, format="longturtle")
        subprocess.run(["kurra", "file", "reformat", str(temporary)], check=True)
        formatted = Graph().parse(temporary, format="turtle")
        if set(formatted) != set(graph):
            raise ValueError("Serialized RDF differs from the generated graph")
        temporary.replace(OUTPUT)

    print(f"Wrote {len(pairs):,} distinct lookup pairs from {matched:,} matched rows.")
    print(f"{OUTPUT} ({len(graph):,} triples)")


if __name__ == "__main__":
    main()
