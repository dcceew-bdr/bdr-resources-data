"""Compare lookup RDF statements independently of prefixes and statement order."""

import argparse
from pathlib import Path
from rdflib import BNode, Graph


def require_equivalent(generated, existing):
    baseline = existing if isinstance(existing, Graph) else Graph().parse(existing, format="turtle")
    for graph in (generated, baseline):
        if any(isinstance(node, BNode) for triple in graph for node in triple):
            raise ValueError("Unexpected anonymous nodes in lookup dataset")
    if len(generated) != len(baseline):
        raise ValueError(f"RDF triple counts differ: {len(generated)} != {len(baseline)}")
    for triple in baseline:
        if triple not in generated:
            raise ValueError(f"RDF graphs differ; existing triple not reproduced: {triple}")
    print(f"RDF graphs match: {len(generated):,} triples; prefixes and order ignored.", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("generated", type=Path)
    parser.add_argument("existing", type=Path)
    args = parser.parse_args()
    require_equivalent(Graph().parse(args.generated, format="turtle"), args.existing)
