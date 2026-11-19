"""Convert matched EPBC common names and dataset metadata to RDF."""

import csv
import json
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import NAMESPACE_URL, uuid5
from zoneinfo import ZoneInfo

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS, XSD

DIRECTORY = Path(__file__).resolve().parent
OUTPUT = DIRECTORY.parents[3] / "resources/datasets/items/epbc-common-names.ttl"
DATASET = URIRef("https://linked.data.gov.au/dataset/bdr/epbc-common-names")
DWC = Namespace("http://rs.tdwg.org/dwc/terms/")
SCHEMA = Namespace("https://schema.org/")


def read_pairs() -> set[tuple[URIRef, Literal]]:
    common_names = defaultdict(set)
    with (DIRECTORY / "extract.csv").open(encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            common_names[row["Current Scientific Name"]].add(row["Common Names"])

    pairs = set()
    with (DIRECTORY / "match/matched.csv").open(
        encoding="utf-8-sig", newline=""
    ) as source:
        for number, row in enumerate(csv.DictReader(source), start=2):
            submitted = row["submitted_name"]
            if submitted not in common_names:
                raise ValueError(
                    f"Matched row {number}: no exact extract name {submitted!r}"
                )
            taxon_name = row["taxon_name"]
            if not taxon_name.startswith(("https://", "http://")) or any(
                character.isspace() for character in taxon_name
            ):
                raise ValueError(
                    f"Matched row {number}: invalid taxon_name {taxon_name!r}"
                )
            for common_name in common_names[submitted]:
                if common_name.strip():
                    pairs.add((URIRef(taxon_name), Literal(common_name)))
    return pairs


def build_graph(pairs: set[tuple[URIRef, Literal]]) -> Graph:
    metadata = Graph().parse(DIRECTORY / "dataset-metadata.ttl", format="turtle")
    datasets = set(metadata.subjects(RDF.type, SCHEMA.Dataset))
    if len(datasets) != 1:
        raise ValueError("Metadata must describe exactly one dataset")
    original = datasets.pop()
    graph = Graph()
    for subject, predicate, obj in metadata:
        graph.add(
            (
                DATASET if subject == original else subject,
                predicate,
                DATASET if obj == original else obj,
            )
        )
    version = graph.value(DATASET, SCHEMA.version, any=False)
    graph.set((DATASET, SCHEMA.version, Literal(str(int(str(version)) + 1))))
    today = datetime.now(ZoneInfo("Australia/Brisbane")).date()
    graph.set((DATASET, SCHEMA.dateModified, Literal(today, datatype=XSD.date)))
    for prefix, namespace in (
        ("", f"{DATASET}/"),
        ("d", str(DATASET)),
        ("dwc", DWC),
        ("rdf", RDF),
        ("rdfs", RDFS),
        ("schema", SCHEMA),
        ("xsd", XSD),
    ):
        graph.bind(prefix, namespace)

    for taxon_name, common_name in sorted(pairs):
        key = json.dumps(
            [str(DATASET), str(taxon_name), str(common_name)], ensure_ascii=False
        )
        statement = URIRef(f"{DATASET}/{uuid5(NAMESPACE_URL, key)}")
        graph.add((taxon_name, DWC.vernacularName, common_name))
        graph.add((statement, RDF.type, RDF.Statement))
        graph.add((statement, RDF.subject, taxon_name))
        graph.add((statement, RDF.predicate, DWC.vernacularName))
        graph.add((statement, RDF.object, common_name))
        graph.add((DATASET, RDFS.member, statement))
    return graph


def main() -> None:
    pairs = read_pairs()
    graph = build_graph(pairs)
    with TemporaryDirectory(dir=OUTPUT.parent) as staging:
        temporary = Path(staging) / OUTPUT.name
        graph.serialize(destination=temporary, format="longturtle")
        subprocess.run(
            ["kurra", "file", "reformat", str(temporary), "-f", "longturtle"],
            check=True,
        )
        formatted = Graph().parse(temporary, format="turtle")
        statements = set(formatted.objects(DATASET, RDFS.member))
        restored_pairs = set()
        for statement in statements:
            subject = formatted.value(statement, RDF.subject, any=False)
            obj = formatted.value(statement, RDF.object, any=False)
            assert (statement, RDF.type, RDF.Statement) in formatted
            assert (statement, RDF.predicate, DWC.vernacularName) in formatted
            assert (subject, DWC.vernacularName, obj) in formatted
            restored_pairs.add((subject, obj))
        metadata = {
            triple
            for triple in graph
            if triple[0] == DATASET and triple[1] != RDFS.member
        }
        if (
            restored_pairs != pairs
            or len(statements) != len(pairs)
            or len(formatted) != len(graph)
            or not metadata.issubset(formatted)
            or set(formatted) != set(graph)
        ):
            raise ValueError("Formatted output does not match the generated RDF")
        temporary.replace(OUTPUT)
    print(
        f"Wrote {len(pairs):,} distinct name pairs and {len(graph):,} triples to {OUTPUT}"
    )


if __name__ == "__main__":
    main()
