"""Regression safeguards for source preservation and RDF equivalence checking."""

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from rdflib import BNode, Graph, Literal, RDF, URIRef

import convert
from verify import NSL, require_equivalent


def usage_graph(blank_id="a", name="https://example.org/name/1"):
    graph = Graph()
    usage = URIRef("https://example.org/usage/1")
    target = BNode(blank_id)
    graph.add((usage, NSL.citing, target))
    graph.add((target, RDF.type, NSL.TaxonNameUsage))
    graph.add((target, NSL.usageOf, URIRef(name)))
    graph.add((target, convert.SCHEMA.citation, Literal("Source citation")))
    return graph


class EquivalenceTests(unittest.TestCase):
    def test_prefix_order_and_blank_node_labels_do_not_matter(self):
        graph = usage_graph()
        graph.bind("nsl", NSL)
        # Parsing creates different blank-node identifiers.
        reserialized = Graph().parse(data=graph.serialize(format="turtle"), format="turtle")
        require_equivalent(graph, reserialized)

    def test_changed_mapping_is_rejected_even_when_counts_match(self):
        with self.assertRaisesRegex(ValueError, "graphs differ"):
            require_equivalent(usage_graph(), usage_graph("b", "https://example.org/name/2"))

    def test_changed_citation_is_rejected(self):
        baseline = usage_graph("b")
        baseline.set((BNode("b"), convert.SCHEMA.citation, Literal("Different source")))
        with self.assertRaisesRegex(ValueError, "graphs differ"):
            require_equivalent(usage_graph(), baseline)

    def test_unsupported_anonymous_structures_fail_closed(self):
        graph = usage_graph()
        graph.add((URIRef("https://example.org/other"), NSL.citing, BNode("a")))
        with self.assertRaisesRegex(ValueError, "Unsupported"):
            require_equivalent(graph, graph)


class InputTests(unittest.TestCase):
    def test_structural_aggregate_counts_are_checked(self):
        convert.validate_graph(usage_graph(), {"mapping_edges": 1, "broken_mapping_targets": 0})
        with self.assertRaisesRegex(ValueError, "mapping_edges"):
            convert.validate_graph(usage_graph(), {"mapping_edges": 2})

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


if __name__ == "__main__":
    unittest.main()
