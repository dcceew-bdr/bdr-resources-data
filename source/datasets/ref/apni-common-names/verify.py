"""Compare these usage graphs independently of Turtle prefixes and blank-node IDs.

The supported structure has one anonymous scientific usage per identified common
usage, joined by nsl:citing. Refuse other blank-node structures rather than treating
them as equal. This is a graph equivalence check for this dataset's documented
structure, not a general RDF canonicalization algorithm.
"""

import argparse
from pathlib import Path

from rdflib import BNode, Graph, Namespace, URIRef

NSL = Namespace("https://linked.data.gov.au/def/nsl/")


def anchored_blank_nodes(graph):
    nodes = {node for triple in graph for node in triple if isinstance(node, BNode)}
    by_owner = {}
    for node in nodes:
        incoming = list(graph.subject_predicates(node))
        if (len(incoming) != 1 or incoming[0][1] != NSL.citing
                or not isinstance(incoming[0][0], URIRef)):
            raise ValueError(f"Unsupported anonymous-node structure: {node}")
        owner = incoming[0][0]
        if owner in by_owner:
            raise ValueError(f"Multiple anonymous usages for one common usage: {owner}")
        by_owner[owner] = node
    return by_owner


def require_equivalent(generated, existing):
    baseline = existing if isinstance(existing, Graph) else Graph().parse(existing, format="turtle")
    if len(generated) != len(baseline):
        raise ValueError(f"RDF triple counts differ: {len(generated)} != {len(baseline)}")
    generated_nodes = anchored_blank_nodes(generated)
    baseline_nodes = anchored_blank_nodes(baseline)
    if generated_nodes.keys() != baseline_nodes.keys():
        raise ValueError("Anonymous scientific usages have different identified owners")
    rename = {node: generated_nodes[owner] for owner, node in baseline_nodes.items()}
    for triple in baseline:
        normalized = tuple(rename.get(node, node) for node in triple)
        if normalized not in generated:
            raise ValueError(f"RDF graphs differ; existing triple not reproduced: {triple}")
    print(f"RDF graphs match: {len(generated):,} triples; prefixes, order and blank-node labels ignored.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generated", type=Path)
    parser.add_argument("existing", type=Path)
    args = parser.parse_args()
    require_equivalent(Graph().parse(args.generated, format="turtle"), args.existing)
