# Taxon-rank labels and cultivar description

`resources/vocabs/items/abis-mapping/taxon_rank.ttl` is generated from `abis_mapping/vocabs/taxon_rank.py` in the ABIS mapping application. Its 33 TERN concept preferred labels are aligned with the reviewed BDR rank scheme in `resources/vocabs/items/nsl-taxonomic-rank.ttl`, preventing these two publications from asserting conflicting preferred labels for the same IRIs.

The corresponding ABIS source change is required when regenerating this file. From the updated ABIS mapping checkout, using its dependency environment:

```python
from pathlib import Path
from abis_mapping.vocabs.taxon_rank import TaxonRank

TaxonRank.export_as_rdf(
    Path("/path/to/bdr-resources-data/resources/vocabs/items/abis-mapping/taxon_rank.ttl")
)
```

ABIS lookup normalises case and punctuation. The label changes retain all 45 existing matching keys. The separate subkingdom identifier correction changes that key’s target to GBIF; the other 44 targets are unchanged. Alternative labels use lowercase spelling; the preferred labels follow BDR's reviewed spelling and hyphenation. Scheme membership is unchanged; the subkingdom identifier changes as described below. Definitions are unchanged except for the cultivar correction and aggregate definition/scope splits described below.

This corrects display labels, the cultivar description and the separation of aggregate definitions from scope notes. It also replaces the pre-existing ABIS `http://example.com/subkingdom` placeholder with GBIF’s `http://rs.gbif.org/vocabulary/gbif/rank/subkingdom`, records `dcterms:replaces`, and sets `rdfs:isDefinedBy` to `http://rs.gbif.org/vocabulary/gbif/rank`. The definition is BDR wording based on ICN Article 4.2. This changes future conversion output; stored placeholder uses need a separate migration.

Generate and inspect the complete vocabulary before publishing. After deployment, verify that the obsolete uppercase preferred-label triples have been removed from the live ABIS vocabulary graph, and that the shared concepts have a single consistent English preferred label across the two graphs. The source edit and local export do not change live data by themselves.

## Preserve the cultivar correction

The ABIS `CULTIVAR` term contains the reviewed definition, `scope_note` and `examples`, with the ICNCP citation in the source comment. The shared `Term` exporter writes these as `skos:definition`, `skos:scopeNote` and `skos:example`. These optional fields do not affect input matching. Regenerate from this updated application source; editing the generated Turtle alone will be lost. The BDR scheme has the corresponding documented override in `../tern-taxon-ranks/concept-overrides.json`; keep both authoring paths aligned. `tests/vocabs/test_taxon_rank.py` checks that the cultivar metadata survives export.

The species aggregate and subspecific aggregate terms likewise keep their definition and scope note in the ABIS Python source. The BDR scheme records matching overrides in `../tern-taxon-ranks/concept-overrides.json`. ICZN Article 6.2 supports the zoological naming guidance; original TERN snapshot text is retained for comparison.

## Preserve reviewed GBIF mappings

The 33 existing `skos:exactMatch` statements in the reviewed BDR/TERN scheme are carried unchanged into ABIS `Term.exact_matches` and its RDF exporter. No additional mappings or `skos:closeMatch` statements are inferred. GBIF subkingdom is used directly and has no self-match. The frozen fixture `tests/vocabs/data/taxon_rank_exact_matches.json` checks the complete export mapping set. Changes to the reviewed mapping set must be reviewed explicitly before updating source or fixture.

The scheme-level `skos:historyNote` records that these links were copied from the reviewed BDR scheme, which retained them from TERN source records. It distinguishes retained mappings from newly inferred mappings and explains why directly reused GBIF subkingdom has no self-match. This note is authored in `TaxonRank.history_note` and exported on each regeneration. The BDR scheme builder carries a corresponding provenance note.
