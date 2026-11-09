"""Generate the APNI common-name lookup graph from the preserved CSV, offline."""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from uuid import UUID

from rdflib import BNode, Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF, RDFS

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "build/apni-common-names.ttl"
SCHEMA = Namespace("https://schema.org/")
DWC = Namespace("http://rs.tdwg.org/dwc/terms/")
EXPECTED_COLUMNS = [
    "common_name_id",
    "common_name",
    "instance_id",
    "citation",
    "scientific_name_id",
    "scientific_name",
    "datasetName",
    "license",
    "ccAttributionIRI",
]
NAME_IRI = re.compile(r"https://id\.biodiversity\.org\.au/name/apni/[0-9]+")


def verify_inputs():
    manifest = json.loads((ROOT / "source-manifest.json").read_text())
    listed = {item["path"] for item in manifest["files"]}
    actual = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "inputs").rglob("*")
        if path.is_file()
    }
    if actual != listed:
        raise ValueError(
            f"Source evidence list changed: missing={listed - actual}, extra={actual - listed}"
        )
    for item in manifest["files"]:
        payload = (ROOT / item["path"]).read_bytes()
        if (
            len(payload) != item["bytes"]
            or hashlib.sha256(payload).hexdigest() != item["sha256"]
        ):
            raise ValueError(f"Source checksum mismatch: {item['path']}")
    return manifest


def build_lookup(rows, source_license_iri):
    """Keep all supported lookup pairs; discard only duplicate RDF statements."""
    graph = Graph()
    scientific_labels = defaultdict(set)
    common_labels = defaultdict(set)
    name_id_pairs = set()
    for number, row in enumerate(rows, start=2):
        required = (
            "common_name_id",
            "common_name",
            "scientific_name_id",
            "scientific_name",
            "license",
            "ccAttributionIRI",
        )
        if any(not row.get(column) or not row[column].strip() for column in required):
            raise ValueError(f"CSV row {number}: missing mapping or attribution field")
        for column in ("common_name_id", "scientific_name_id"):
            if not NAME_IRI.fullmatch(row[column]):
                raise ValueError(f"CSV row {number}: invalid APNI {column}")
        if row["license"] != source_license_iri:
            raise ValueError(f"CSV row {number}: licence differs from recorded source licence")
        # All attribution IRIs in this snapshot are the scientific-name subjects.
        # Fail rather than silently drop different attribution in a future export.
        if row["ccAttributionIRI"] != row["scientific_name_id"]:
            raise ValueError(
                f"CSV row {number}: unsupported attribution IRI; review Dataset attribution"
            )
        scientific_labels[row["scientific_name_id"]].add(row["scientific_name"])
        common_labels[row["common_name_id"]].add(row["common_name"])
        name_id_pairs.add((row["common_name_id"], row["scientific_name_id"]))
        subject = URIRef(row["scientific_name_id"])
        graph.add((subject, DWC.scientificName, Literal(row["scientific_name"])))
        graph.add((subject, DWC.vernacularName, Literal(row["common_name"])))
    conflicts = {
        key: sorted(values)
        for labels in (scientific_labels, common_labels)
        for key, values in labels.items()
        if len(values) > 1
    }
    if conflicts:
        raise ValueError(f"Conflicting source labels: {conflicts}")
    summary = {
        "source_rows": len(rows),
        "converted_rows": len(rows),
        "distinct_common_name_ids": len(common_labels),
        "distinct_scientific_name_ids": len(scientific_labels),
        "distinct_name_id_pairs": len(name_id_pairs),
        "lookup_pairs": len(set(graph.subject_objects(DWC.vernacularName))),
        "mapping_triples": len(graph),
    }
    return graph, summary


def read_statement_ids(path, dataset):
    """Read the pinned published identities, without consulting generated RDF."""
    identities = {}
    used = set()
    with path.open(encoding="utf-8", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != ["scientific_name_id", "common_name", "statement_id"]:
            raise ValueError("Unexpected statement identity columns")
        for row in reader:
            name, common, statement = (row.get(key) for key in reader.fieldnames)
            if not name or not NAME_IRI.fullmatch(name) or not common or not statement:
                raise ValueError("Invalid statement identity row")
            namespace = str(dataset) + "/"
            if not statement.startswith(namespace):
                raise ValueError("Statement identity is outside the Dataset namespace")
            suffix = statement[len(namespace):]
            if str(UUID(suffix)) != suffix:
                raise ValueError("Noncanonical statement UUID")
            pair = (URIRef(name), Literal(common))
            if pair in identities or statement in used:
                raise ValueError("Duplicate statement pair or UUID")
            identities[pair] = URIRef(statement)
            used.add(statement)
    return identities


def add_statement_members(graph, identities, dataset):
    """Reproduce version 3's reified lookup membership with stable UUIDs."""
    pairs = set(graph.subject_objects(DWC.vernacularName))
    if pairs != identities.keys():
        raise ValueError("Published statement identities do not exactly cover lookup pairs")
    for (name, common), statement in identities.items():
        graph.add((dataset, RDFS.member, statement))
        graph.add((statement, RDF.type, RDF.Statement))
        graph.add((statement, RDF.subject, name))
        graph.add((statement, RDF.predicate, DWC.vernacularName))
        graph.add((statement, RDF.object, common))


def add_dataset_metadata(graph, metadata, manifest):
    """Validate publication metadata independently of the preserved source licence."""
    dataset = URIRef(manifest["dataset_iri"])
    expected = {URIRef(manifest["dataset_license"])}
    if set(metadata.objects(dataset, SCHEMA.license)) != expected:
        raise ValueError("Dataset licence does not match recorded publication licence")
    for triple in metadata:
        graph.add(triple)


def validate_source_coverage(graph, rows):
    """Compare exact emitted lookup/scientific-name pairs with the source sets."""
    expected_common = {
        (URIRef(r["scientific_name_id"]), Literal(r["common_name"])) for r in rows
    }
    expected_scientific = {
        (URIRef(r["scientific_name_id"]), Literal(r["scientific_name"])) for r in rows
    }
    for predicate, expected in (
        (DWC.vernacularName, expected_common),
        (DWC.scientificName, expected_scientific),
    ):
        actual = set(graph.subject_objects(predicate))
        if actual != expected:
            raise ValueError(
                f"Source coverage differs for {predicate}: missing={len(expected - actual)}, extra={len(actual - expected)}"
            )
    if any(isinstance(node, BNode) for triple in graph for node in triple):
        raise ValueError("Unexpected anonymous nodes in lookup dataset")
    for subject in {subject for subject, _ in expected_scientific}:
        if any(
            predicate not in (DWC.scientificName, DWC.vernacularName)
            for predicate, _ in graph.predicate_objects(subject)
        ):
            raise ValueError(
                f"Unexpected background statements on scientific-name resource {subject}"
            )
    print(
        "Every distinct CSV lookup and scientific-name pair is preserved.", flush=True
    )


def validate_graph(graph, expected):
    counts = {
        str(row["metric"]): int(row["count"])
        for row in graph.query((ROOT / "checks.rq").read_text())
    }
    for metric, value in expected.items():
        if counts.get(metric, 0) != value:
            raise ValueError(
                f"RDF structural check failed: {metric}: {counts.get(metric, 0)} != {value}"
            )
    print("RDF structure checks passed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument(
        "--check-existing",
        type=Path,
        help="Require equality with an existing RDF graph.",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    if args.check_existing and output == args.check_existing.resolve():
        parser.error("--output must differ from --check-existing")
    manifest = verify_inputs()
    source = ROOT / manifest["csv"]
    with source.open(encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if reader.fieldnames != EXPECTED_COLUMNS:
            raise ValueError(f"Unexpected CSV columns: {reader.fieldnames}")
        rows = list(reader)
    graph, summary = build_lookup(rows, manifest["source_license"])
    metadata = Graph().parse(ROOT / "dataset-metadata.ttl", format="turtle")
    dataset = URIRef(manifest["dataset_iri"])
    identities = read_statement_ids(ROOT / manifest["statement_ids"], dataset)
    add_statement_members(graph, identities, dataset)
    graph.bind("apni", Namespace("https://id.biodiversity.org.au/name/apni/"))
    graph.bind("dwc", DWC)
    graph.bind("", Namespace(str(dataset) + "/"), replace=True)
    graph.bind("rdfs", RDFS)
    add_dataset_metadata(graph, metadata, manifest)
    for prefix, namespace in metadata.namespaces():
        graph.bind(prefix, namespace, replace=True)
    summary.update(
        {
            "triples": len(graph),
            "dataset_iri": str(dataset),
            "source_file": manifest["csv"],
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "source_licenses": dict(Counter(r["license"] for r in rows)),
            "source_license": manifest["source_license"],
            "dataset_license": manifest["dataset_license"],
            "statement_members": len(identities),
        }
    )
    for key, expected in manifest["expected"].items():
        if summary.get(key) != expected:
            raise ValueError(
                f"Snapshot check failed: {key}: {summary.get(key)!r} != {expected!r}"
            )
    validate_source_coverage(graph, rows)
    validate_graph(graph, manifest["structural_checks"])
    if args.check_existing:
        from verify import require_equivalent

        require_equivalent(graph, args.check_existing)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    graph.serialize(destination=temporary, format="longturtle")
    temporary.write_bytes(temporary.read_bytes().rstrip(b"\n") + b"\n")
    temporary.replace(output)
    summary["rdf_bytes"] = output.stat().st_size
    summary["rdf_sha256"] = hashlib.sha256(output.read_bytes()).hexdigest()
    (ROOT / "build").mkdir(exist_ok=True)
    (ROOT / "build/conversion-report.json").write_text(
        json.dumps(summary, indent=2) + "\n"
    )
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Wrote {output}", flush=True)


if __name__ == "__main__":
    main()
