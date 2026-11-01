"""Convert the entire preserved APNI CSV to a draft NSL usage graph, offline.

Run with `uv run --locked convert.py` from this directory. No network requests or database writes occur.
"""

import argparse
import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import urlsplit

from rdflib import BNode, Graph, Literal, Namespace, RDF, RDFS, URIRef
from rdflib.namespace import DCTERMS, PROV, XSD

ROOT = Path(__file__).resolve().parent
DEFAULT_OUTPUT = ROOT / "build/apni-common-names-nsl.ttl"
SCHEMA = Namespace("https://schema.org/")
NSL = Namespace("https://linked.data.gov.au/def/nsl/")
NT = Namespace("https://linked.data.gov.au/def/nsl/tn-types/")
CC = Namespace("http://creativecommons.org/ns#")
BIBO = Namespace("http://purl.org/ontology/bibo/")
EXPECTED = ["common_name_id", "common_name", "instance_id", "citation",
            "scientific_name_id", "scientific_name", "datasetName", "license",
            "ccAttributionIRI"]


def permalink(obj):
    links = obj.get("_links", {})
    if "permalink" in links:
        return links["permalink"]["link"]
    candidates = links.get("permalinks", [])
    return next((x["link"] for x in candidates if x.get("preferred")), None)


def verify_inputs():
    """Require exactly the versioned evidence set; never fetch newer API data."""
    manifest = json.loads((ROOT / "source-manifest.json").read_text())
    listed = {item["path"] for item in manifest["files"]}
    actual = {path.relative_to(ROOT).as_posix() for path in (ROOT / "inputs").rglob("*") if path.is_file()}
    if actual != listed:
        raise ValueError(f"Source evidence list changed: missing={listed - actual}, extra={actual - listed}")
    for item in manifest["files"]:
        payload = (ROOT / item["path"]).read_bytes()
        if len(payload) != item["bytes"] or hashlib.sha256(payload).hexdigest() != item["sha256"]:
            raise ValueError(f"Source checksum mismatch: {item['path']}")
    return manifest


def validate_graph(graph, expected):
    """Check the independently maintained SPARQL expectations before writing."""
    counts = {str(row["metric"]): int(row["count"]) for row in graph.query((ROOT / "checks.rq").read_text())}
    for metric, value in expected.items():
        if counts.get(metric, 0) != value:
            raise ValueError(f"RDF structural check failed: {metric}: {counts.get(metric, 0)} != {value}")
    print("RDF structure checks passed.", flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT,
                        help="Generated Turtle; defaults to ignored build/ output.")
    parser.add_argument("--check-existing", type=Path,
                        help="Require RDF graph equivalence with an existing Turtle file.")
    args = parser.parse_args()
    manifest = verify_inputs()
    source = ROOT / manifest["csv"]
    output = args.output.resolve()
    if args.check_existing and output == args.check_existing.resolve():
        parser.error("--output must differ from --check-existing")
    out = ROOT / "build"
    out.mkdir(exist_ok=True)
    checksum = hashlib.sha256(source.read_bytes()).hexdigest()
    source_iri = URIRef("urn:sha256:" + checksum)
    dataset = URIRef(manifest["dataset_iri"])
    with source.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != EXPECTED:
            raise ValueError(f"Unexpected columns: {reader.fieldnames}")
        rows = list(reader)

    g = Graph().parse(ROOT / "dataset-metadata.ttl", format="turtle")
    for prefix, namespace in [("nsl", NSL), ("nt", NT), ("schema", SCHEMA),
                              ("prov", PROV), ("dcterms", DCTERMS), ("bibo", BIBO),
                              ("cc", CC), ("rdfs", RDFS),
                              ("apni", "https://id.biodiversity.org.au/name/apni/"),
                              ("inst", "https://id.biodiversity.org.au/instance/apni/")]:
        g.bind(prefix, namespace, replace=True)
    g.add((source_iri, RDF.type, PROV.Entity))
    g.add((source_iri, SCHEMA.name, Literal(source.name)))
    g.add((source_iri, DCTERMS.format, Literal("text/csv")))

    cached = {}
    for path in sorted((ROOT / "inputs/enrichment").glob("*.json")):
        value = json.loads(path.read_text())
        iri = permalink(value)
        if iri:
            cached[iri] = value

    issues = []
    counters = Counter({"rejected_rows": 0, "enrichment_mismatch_rows": 0})
    names = defaultdict(set)
    pairs = set()
    seen_instances = set()
    unresolved = []
    actual_common_ids = set()
    scientific_ids = set()
    enriched_sources = []

    for number, row in enumerate(rows, start=2):
        errors = []
        for column in EXPECTED:
            if not row.get(column):
                errors.append(f"missing {column}")
        for column, segment in [("common_name_id", "name"),
                                ("scientific_name_id", "name"),
                                ("instance_id", "instance")]:
            if not re.fullmatch(r"https://id\.biodiversity\.org\.au/" + segment + r"/apni/[0-9]+", row[column] or ""):
                errors.append(f"invalid APNI {column}")
        for column in ("license", "ccAttributionIRI"):
            parsed = urlsplit(row[column] or "")
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                errors.append(f"invalid {column} IRI")
        if row["instance_id"] in seen_instances:
            errors.append("duplicate instance_id")
        if errors:
            issues.append({"csv_row": number, "instance_id": row["instance_id"], "errors": errors})
            counters["rejected_rows"] += 1
            continue
        seen_instances.add(row["instance_id"])
        common = URIRef(row["common_name_id"])
        scientific = URIRef(row["scientific_name_id"])
        usage = URIRef(row["instance_id"])
        actual_common_ids.add(str(common))
        scientific_ids.add(str(scientific))
        names[str(common)].add(row["common_name"])
        names[str(scientific)].add(row["scientific_name"])
        pairs.add((str(common), str(scientific)))
        for node, label in [(common, row["common_name"]), (scientific, row["scientific_name"])]:
            g.add((node, RDF.type, NSL.TaxonName))
            g.add((node, RDFS.label, Literal(label)))
        g.add((common, SCHEMA.additionalType, NT.common))
        # The CSV does not supply the scientific name's precise type or rank.
        # Do not overwrite existing autonym/hybrid/etc. classifications.
        g.add((usage, RDF.type, NSL.TaxonNameUsage))
        g.add((usage, NSL.usageOf, common))
        g.add((usage, SCHEMA.additionalType, Literal("common name")))
        g.add((usage, SCHEMA.citation, Literal(row["citation"])))
        g.add((usage, PROV.wasDerivedFrom, source_iri))
        g.add((usage, DCTERMS.license, URIRef(row["license"])))
        g.add((usage, CC.attributionURL, URIRef(row["ccAttributionIRI"])))
        g.add((dataset, SCHEMA.license, URIRef(row["license"])))
        g.add((dataset, SCHEMA.identifier, Literal(row["datasetName"])))

        evidence = cached.get(str(usage))
        scientific_usage = None
        if evidence:
            target = evidence.get("citedBy", {})
            target_iri = permalink(target)
            target_data = cached.get(target_iri)
            matches = (
                permalink(evidence.get("name", {})) == str(common)
                and evidence.get("reference", {}).get("citation") == row["citation"]
                and target_data is not None
                and permalink(target_data.get("name", {})) == str(scientific)
            )
            if matches:
                scientific_usage = URIRef(target_iri)
                counters["resolved_scientific_usage_rows"] += 1
                enriched_sources.append(str(usage))
                for node, data in [(usage, evidence), (scientific_usage, target_data)]:
                    reference = permalink(data.get("reference", {}))
                    if reference:
                        reference = URIRef(reference)
                        g.add((node, SCHEMA.citation, reference))
                        g.add((reference, RDF.type, SCHEMA.CreativeWork))
                        g.add((reference, SCHEMA.name, Literal(data["reference"]["citation"])))
                    if data.get("page"):
                        g.add((node, BIBO.pages, Literal(data["page"])))
                    if data.get("instanceType", {}).get("name"):
                        g.add((node, SCHEMA.additionalType, Literal(data["instanceType"]["name"])))
                g.add((usage, PROV.wasDerivedFrom, URIRef(str(usage) + ".json")))
            else:
                issues.append({"csv_row": number, "instance_id": str(usage),
                               "errors": ["cached API evidence does not match this CSV mapping"]})
                counters["enrichment_mismatch_rows"] += 1
        if scientific_usage is None:
            scientific_usage = BNode("scientificusage" + row["instance_id"].rsplit("/", 1)[1])
            unresolved.append({"csv_row": number, "instance_id": str(usage),
                               "common_name_id": str(common), "scientific_name_id": str(scientific),
                               "issue": "scientific usage IRI, reference IRI, page and exact usage type unavailable in CSV"})
        g.add((scientific_usage, RDF.type, NSL.TaxonNameUsage))
        g.add((scientific_usage, NSL.usageOf, scientific))
        g.add((scientific_usage, SCHEMA.citation, Literal(row["citation"])))
        g.add((scientific_usage, PROV.wasDerivedFrom, source_iri))
        # PROVISIONAL: use the conversion proposed in Option B; no invented predicate.
        g.add((usage, NSL.citing, scientific_usage))
        counters["converted_rows"] += 1

    with (out / "unresolved-enrichment.csv").open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["csv_row", "instance_id", "common_name_id", "scientific_name_id", "issue"])
        writer.writeheader()
        writer.writerows(unresolved)
    name_conflicts = {key: sorted(values) for key, values in names.items() if len(values) > 1}
    summary = {
        "status": "draft: source conversion complete; NSL mapping confirmation and enrichment outstanding",
        "source_file": str(source.relative_to(ROOT)), "source_sha256": checksum,
        "source_rows": len(rows), **dict(counters),
        "unresolved_scientific_usage_rows": len(unresolved),
        "distinct_common_name_ids": len(actual_common_ids),
        "distinct_common_name_strings": len({r['common_name'] for r in rows}),
        "distinct_scientific_name_ids": len(scientific_ids),
        "distinct_name_id_pairs": len(pairs),
        "distinct_string_scientific_id_pairs": len({(r['common_name'], r['scientific_name_id']) for r in rows}),
        "conflicting_name_labels": name_conflicts,
        "common_scientific_id_overlap": sorted(actual_common_ids & scientific_ids),
        "licenses": dict(Counter(r['license'] for r in rows)),
        "attribution_different_from_scientific_id_rows": sum(r['ccAttributionIRI'] != r['scientific_name_id'] for r in rows),
        "enriched_common_usages": enriched_sources,
        "triples": len(g), "dataset_iri": str(dataset),
        "assumptions": [
            "APNI common-name mapping rows are represented as common-name TaxonNameUsage resources.",
            "APNI citedBy is provisionally translated to nsl:citing on the common-name usage.",
            "Unidentified scientific-name usages are anonymous nodes; distinct blank nodes do not assert distinct real-world usages.",
            "Concept-valued nt:common supplements, rather than replaces, production literal name types.",
            "Scientific-name subtypes, ranks, page numbers and publication IRIs are not guessed.",
            "nsl:cited is omitted, not fabricated, when source cites evidence is unavailable.",
        ],
        "issues": issues,
    }
    # Fail before serializing or replacing any output if this snapshot changed.
    for key, expected in manifest["expected"].items():
        if summary.get(key) != expected:
            raise ValueError(f"Snapshot check failed: {key}: {summary.get(key)!r} != {expected!r}")
    if issues or name_conflicts or summary["common_scientific_id_overlap"]:
        raise ValueError("Source/evidence conflicts found; refusing to generate output")
    validate_graph(g, manifest["structural_checks"])
    if args.check_existing:
        from verify import require_equivalent
        require_equivalent(g, args.check_existing)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(output.name + ".tmp")
    g.serialize(destination=temporary, format="turtle")
    temporary.replace(output)
    summary['rdf_sha256'] = hashlib.sha256(output.read_bytes()).hexdigest()
    summary['rdf_bytes'] = output.stat().st_size
    common_ids_by_label = defaultdict(set)
    for row in rows:
        common_ids_by_label[row['common_name']].add(row['common_name_id'])
    repeated_labels = {k: sorted(v) for k, v in common_ids_by_label.items() if len(v) > 1}
    summary['common_name_strings_with_multiple_name_ids'] = len(repeated_labels)
    (out / 'repeated-common-name-labels.json').write_text(json.dumps(repeated_labels, indent=2) + '\n')
    (out / 'conversion-report.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2), flush=True)
    print(f"Wrote {output}", flush=True)
    if counters['rejected_rows'] or counters['enrichment_mismatch_rows']:
        raise SystemExit("Conversion has row-level errors; inspect conversion-report.json")


if __name__ == "__main__":
    main()
