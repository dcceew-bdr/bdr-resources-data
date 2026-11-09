# APNI common-name lookup dataset

This directory reproduces `resources/datasets/items/apni-common-names.ttl` from the APNI CSV downloaded on 30 October 2026. It implements the direct lookup pattern requested in [PR #7](https://github.com/dcceew-bdr/bdr-resources-data/pull/7) for [bdr-ops #312](https://github.com/dcceew-bdr/bdr-ops/issues/312).

The 64,714 source rows yield 37,160 distinct scientific-name IRI/common-name text pairs across 17,204 scientific-name IRIs: **54,364 mapping triples**, 185,800 statement/membership triples, and 14 Dataset metadata triples: **240,178 triples** in published version 3. Repeated evidence and distinct common-name IDs with the same text produce the same lookup triple and are deduplicated. The CSV has 37,165 distinct name-ID pairs, which is a different measure from the number of lookup pairs.

## Reproduce and verify

Use Python 3.13 and uv. Dependencies are pinned by `pyproject.toml` and `uv.lock`. From the repository root:

```bash
cd source/datasets/ref/apni-common-names
uv run --locked python -m unittest -v
uv run --locked convert.py --check-existing ../../../../resources/datasets/items/apni-common-names.ttl
```

The converter verifies input hashes, source counts, exact scientific-name and vernacular-name coverage, and RDF structure. It checks that the generated graph equals the committed graph, independently of prefix names and statement order, then writes the generated file and a conversion report into ignored `build/`. This command does not overwrite the catalogue file. The converter makes no network requests; uv may download the locked Python environment and packages on first use.

To generate a reviewed replacement deliberately:

```bash
uv run --locked convert.py --output ../../../../resources/datasets/items/apni-common-names.ttl
```

The read-only PR workflow runs the tests and full reproduction check when the source method or output changes. It performs no database publication.

## Mapping

```turtle
@prefix apni: <https://id.biodiversity.org.au/name/apni/> .
@prefix dwc: <http://rs.tdwg.org/dwc/terms/> .

apni:92084
    dwc:scientificName "Ficus opposita Miq. var. opposita" ;
    dwc:vernacularName "Sandpaper Fig" .
```

The subject comes from `scientific_name_id`, scientific text from `scientific_name`, and common-name text from `common_name`, with literal text preserved. APNI name IRIs are reused as supplied. These are name identifiers: no taxon class assertion or new identifier is added. Multiple common names per scientific name and common names shared by different scientific names are retained. The source-to-graph coverage check compares exact sets of pairs so unchanged totals cannot conceal a changed mapping.

The scientific-name resources contain only the two Darwin Core properties above. Version 3 additionally has one UUID-identified `rdf:Statement` per lookup pair, with `rdf:subject`, `rdf:predicate dwc:vernacularName`, and `rdf:object`. The Dataset links to these statement resources using `rdfs:member`. The direct lookup triples are still asserted, so API search need not traverse the statement resources. No NSL usage nodes or blank nodes are generated.

`inputs/published-statement-ids.csv` pins all 37,160 published statement IDs, extracted from the reviewed version 3 artifact at main commit `a2031a4b05257762649e6105c34bf2c6c0383481`. The manifest records that artifact's origin and byte checksum. This compact identity table preserves the existing publication identifiers without consulting the generated output or minting random UUIDs during each build. Missing, extra, duplicate, or malformed identities fail validation. Supporting name-usage and citation evidence remains available from NSL and the original CSV; API enrichment is not required.

## Source, metadata, and checks

| File | Role |
| --- | --- |
| `inputs/APNI-common-names-2026-10-30-5314.csv` | Preserved full export, including its citations, common-name/usage IDs, licences and attribution |
| `inputs/published-statement-ids.csv` | Reviewed UUID identity for each scientific-name/common-name lookup pair |
| `source-manifest.json` | Input origins/checksums, separate source and publication licence declarations, expected source and output counts |
| `dataset-metadata.ttl` | Dataset identifier, explicit dates, description, licence, attribution and source provenance |
| `convert.py` | Offline deduplicated lookup generation and exact coverage checks |
| `checks.rq` | Lookup and statement membership counts, malformed/unasserted members, conflicting labels, NSL relationships and anonymous nodes |
| `verify.py` | Exact RDF graph comparison; anonymous nodes are rejected |
| `test_workflow.py` | Tests for many-to-many preservation, deduplication, changed mappings, labels, attribution and source integrity |
| `pyproject.toml`, `uv.lock`, `.python-version` | Locked execution environment |

The source CSV is preserved unchanged. Source provenance and byte checksums are recorded in the manifest. `schema:license` and `schema:creditText` reproduce the reviewed Dataset metadata. Every row's attribution IRI in this snapshot equals its scientific-name subject; changed attribution fails validation.

The generator validates CSV row licences against `source_license` and the Dataset's `schema:license` against `dataset_license`. It does not require the two declarations to be identical. Both values and the observed source licence counts are included in the build report. The metadata template contains exactly the 14 Dataset triples in the reviewed version 3 artifact; it does not restore the earlier provenance triple that was removed from the publication.

The catalogue file is generated from the maintained method and metadata. Do not maintain changes only in the generated output. No external working directory, API cache, or production GraphDB access is needed to reproduce it.

## Prefix policy

Prefixes are a readability convention, not the dataset's semantic identity. Prefer an ontology's declared `vann:preferredNamespacePrefix` for the matching `vann:preferredNamespaceUri` where available; otherwise follow existing repository usage. Resolve any local prefix collision explicitly without changing the namespace IRI. See the [VANN definitions](https://vocab.org/vann/).

Here, `apni:` matches the EPBC dataset's APNI name namespace; `dwc:`, `rdf:`, `rdfs:`, and `schema:` follow existing repository usage. These are local serialization choices; this directory does not claim that APNI authoritatively declares those preferred prefixes. Namespace bindings are supplied to RDFLib, but no compaction pass, live vocabulary fetch, or prefix-specific validity rule is required. A different prefix spelling must not change the graph or fail the reproduction check.

## Refreshing

A refresh is a reviewed change, separate from reproduction. Preserve a new dated export, record its origin and checksum in the manifest, inspect changed mappings and any new attribution requirements, review and extend the published statement identity table for any changed lookup pairs, update input checksums, expected counts and explicit Dataset dates/descriptions, then regenerate and review the RDF and catalogue changes. Unexpected or changed inputs are rejected. `.gitattributes` disables input line-ending conversion so downloaded-byte checksums survive cross-platform checkout.

## Licence

The preserved APNI source export declares [CC BY 3.0](http://creativecommons.org/licenses/by/3.0/), recorded verbatim as `source_license`. The reviewed published version 3 Dataset declares [CC BY 4.0](http://purl.org/NET/rdflicense/cc-by4.0), recorded separately as `dataset_license`. This workflow preserves both recorded declarations; it does not rewrite the source CSV's licence or change the published Dataset's declaration. Attribution remains in the CSV and the Dataset's credit text. Changes to either licence value require an explicit metadata/manifest review, rather than removing a failing validation check.
