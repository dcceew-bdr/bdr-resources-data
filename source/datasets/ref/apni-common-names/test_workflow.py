"""Regression tests for many-to-many lookups and source preservation."""
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from rdflib import BNode, Graph, Literal, URIRef, RDF, RDFS
import convert
from verify import require_equivalent

LICENSE = "http://creativecommons.org/licenses/by/3.0/"
PUBLISHED_LICENSE = "http://purl.org/NET/rdflicense/cc-by4.0"
DATASET = URIRef("https://linked.data.gov.au/dataset/apni-common-names")

def row(common_id, common, scientific_id, scientific):
    return {
        "common_name_id": f"https://id.biodiversity.org.au/name/apni/{common_id}",
        "common_name": common,
        "scientific_name_id": f"https://id.biodiversity.org.au/name/apni/{scientific_id}",
        "scientific_name": scientific,
        "license": LICENSE,
        "ccAttributionIRI": f"https://id.biodiversity.org.au/name/apni/{scientific_id}",
    }

class LookupTests(unittest.TestCase):
    def test_many_to_many_pairs_survive_duplicate_evidence_and_name_ids(self):
        rows = [row(1, "Shared", 10, "Species A"), row(2, "Other", 10, "Species A"),
                row(1, "Shared", 11, "Species B"), row(3, "Shared", 10, "Species A")]
        rows.append(dict(rows[0]))
        graph, summary = convert.build_lookup(rows, LICENSE)
        self.assertEqual(summary["lookup_pairs"], 3)
        self.assertEqual(summary["distinct_name_id_pairs"], 4)
        self.assertEqual(len(graph), 5)
        convert.validate_source_coverage(graph, rows)

    def test_changed_mapping_is_detected_even_when_counts_match(self):
        rows = [row(1, "Common", 10, "Species A")]
        graph, _ = convert.build_lookup(rows, LICENSE)
        graph.set((URIRef(rows[0]["scientific_name_id"]), convert.DWC.vernacularName, Literal("Wrong")))
        with self.assertRaisesRegex(ValueError, "Source coverage differs"):
            convert.validate_source_coverage(graph, rows)

    def test_conflicting_scientific_labels_are_rejected(self):
        rows = [row(1, "Common", 10, "Species A"), row(2, "Other", 10, "Species B")]
        with self.assertRaisesRegex(ValueError, "Conflicting source labels"):
            convert.build_lookup(rows, LICENSE)

    def test_changed_licence_or_attribution_requires_review(self):
        for column in ("license", "ccAttributionIRI"):
            source = row(1, "Common", 10, "Species A")
            source[column] = "https://example.org/changed"
            with self.subTest(column=column), self.assertRaises(ValueError):
                convert.build_lookup([source], LICENSE)

    def test_same_graph_with_different_prefixes_matches(self):
        graph, _ = convert.build_lookup([row(1, "Common", 10, "Species A")], LICENSE)
        graph.bind("alternative", convert.DWC)
        parsed = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        require_equivalent(graph, parsed)
        parsed.set((URIRef("https://id.biodiversity.org.au/name/apni/10"),
                    convert.DWC.scientificName, Literal("Changed")))
        with self.assertRaisesRegex(ValueError, "graphs differ"):
            require_equivalent(graph, parsed)

    def test_anonymous_nodes_are_rejected(self):
        graph = Graph()
        graph.add((BNode(), convert.DWC.vernacularName, Literal("Unexpected")))
        with self.assertRaisesRegex(ValueError, "anonymous"):
            require_equivalent(graph, graph)

    def test_structural_aggregate_counts_are_checked(self):
        graph, _ = convert.build_lookup([row(1, "Common", 10, "Species A")], LICENSE)
        convert.validate_graph(graph, {"lookup_pairs": 1, "lookups_without_scientific_name": 0})
        with self.assertRaisesRegex(ValueError, "lookup_pairs"):
            convert.validate_graph(graph, {"lookup_pairs": 2})

class InputTests(unittest.TestCase):
    def test_changed_or_extra_source_files_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "inputs").mkdir()
            source = root / "inputs/source.csv"
            source.write_bytes(b"preserved source\n")
            item = {"path": "inputs/source.csv", "bytes": source.stat().st_size,
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest()}
            (root / "source-manifest.json").write_text(json.dumps({"files": [item]}))
            with patch.object(convert, "ROOT", root):
                convert.verify_inputs()
                source.write_bytes(b"changed source\n")
                with self.assertRaisesRegex(ValueError, "checksum"):
                    convert.verify_inputs()
                source.write_bytes(b"preserved source\n")
                (root / "inputs/extra.json").write_text("{}")
                with self.assertRaisesRegex(ValueError, "list changed"):
                    convert.verify_inputs()


class PublicationTests(unittest.TestCase):
    def test_source_and_publication_licences_are_validated_independently(self):
        source = row(1, "Common", 10, "Species A")
        graph, _ = convert.build_lookup([source], LICENSE)
        metadata = Graph()
        metadata.add((DATASET, convert.SCHEMA.license, URIRef(PUBLISHED_LICENSE)))
        manifest = {"dataset_iri": str(DATASET), "source_license": LICENSE,
                    "dataset_license": PUBLISHED_LICENSE}
        convert.add_dataset_metadata(graph, metadata, manifest)
        self.assertEqual(source["license"], LICENSE)
        self.assertEqual(set(graph.objects(DATASET, convert.SCHEMA.license)),
                         {URIRef(PUBLISHED_LICENSE)})
        metadata.set((DATASET, convert.SCHEMA.license, URIRef(LICENSE)))
        with self.assertRaisesRegex(ValueError, "publication licence"):
            convert.add_dataset_metadata(Graph(), metadata, manifest)
        with self.assertRaisesRegex(ValueError, "source licence"):
            convert.build_lookup([source], PUBLISHED_LICENSE)

    def test_published_uuid_is_preserved_for_a_quoted_common_name(self):
        source = row(1, 'Common, "quoted" name', 10, "Species A")
        statement = str(DATASET) + "/0001346f-e401-4419-a64f-438dd5f0f917"
        with tempfile.TemporaryDirectory() as directory:
            import csv
            path = Path(directory) / "identities.csv"
            with path.open("w", newline="") as stream:
                writer = csv.writer(stream)
                writer.writerow(["scientific_name_id", "common_name", "statement_id"])
                writer.writerow([source["scientific_name_id"], source["common_name"], statement])
            identities = convert.read_statement_ids(path, DATASET)
            graph, _ = convert.build_lookup([source], LICENSE)
            convert.add_statement_members(graph, identities, DATASET)
            self.assertIn((DATASET, RDFS.member, URIRef(statement)), graph)
            self.assertIn((URIRef(statement), RDF.object, Literal(source["common_name"])), graph)
            self.assertEqual(len(graph), 7)
            convert.validate_source_coverage(graph, [source])
            convert.validate_graph(graph, {"statement_members": 1, "reified_statements": 1,
                                           "invalid_statement_members": 0})
            second, _ = convert.build_lookup([source], LICENSE)
            convert.add_statement_members(second, identities, DATASET)
            require_equivalent(graph, second)

    def test_missing_or_extra_statement_identities_are_rejected(self):
        graph, _ = convert.build_lookup([row(1, "Common", 10, "Species A")], LICENSE)
        with self.assertRaisesRegex(ValueError, "exactly cover"):
            convert.add_statement_members(graph, {}, DATASET)
        wrong = {(URIRef("https://id.biodiversity.org.au/name/apni/11"), Literal("Common")):
                 URIRef(str(DATASET) + "/0001346f-e401-4419-a64f-438dd5f0f917")}
        with self.assertRaisesRegex(ValueError, "exactly cover"):
            convert.add_statement_members(graph, wrong, DATASET)

    def test_malformed_statement_members_are_detected(self):
        graph, _ = convert.build_lookup([row(1, "Common", 10, "Species A")], LICENSE)
        graph.add((DATASET, RDFS.member, URIRef("urn:broken:member")))
        with self.assertRaisesRegex(ValueError, "invalid_statement_members"):
            convert.validate_graph(graph, {"invalid_statement_members": 0})

if __name__ == "__main__":
    unittest.main()
