# APNI common-name lookup dataset

This directory reproduces `resources/datasets/items/apni-common-names-nsl.ttl` from the APNI CSV downloaded on 30 October 2026. It implements the direct lookup pattern requested in [PR #7](https://github.com/dcceew-bdr/bdr-resources-data/pull/7) for [bdr-ops #312](https://github.com/dcceew-bdr/bdr-ops/issues/312).

The 64,714 source rows yield 37,160 distinct scientific-name IRI/common-name text pairs across 17,204 scientific-name IRIs: **54,364 mapping triples**, plus Dataset metadata. Repeated evidence and distinct common-name IDs with the same text produce the same lookup triple and are deduplicated. The CSV has 37,165 distinct name-ID pairs, which is a different measure from the number of lookup pairs.

## Reproduce and verify

Use Python 3.13 and uv. Dependencies are pinned by `pyproject.toml` and `uv.lock`. From the repository root:

```bash
cd source/datasets/ref/apni-common-names
uv run --locked python -m unittest -v
uv run --locked convert.py --check-existing ../../../../resources/datasets/items/apni-common-names-nsl.ttl
```

The converter verifies input hashes, source counts, exact scientific-name and vernacular-name coverage, and RDF structure. It checks that the generated graph equals the committed graph, independently of prefix names and statement order, then writes the generated file and a conversion report into ignored `build/`. This command does not overwrite the catalogue file. The converter makes no network requests; uv may download the locked Python environment and packages on first use.

To generate a reviewed replacement deliberately:

```bash
uv run --locked convert.py --output ../../../../resources/datasets/items/apni-common-names-nsl.ttl
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

The generated mapping resources contain only the two Darwin Core properties above. No NSL usage resources, common-name resource descriptions, citation evidence, mapping annotations or blank nodes are generated. The previous provisional `nsl:citing` translation and unresolved scientific usage identifiers are no longer needed. Supporting evidence is available from NSL and retained in the original CSV. API enrichment is not used; the two earlier worked-example API caches were removed from the method.

## Source, metadata, and checks

| File | Role |
| --- | --- |
| `inputs/APNI-common-names-2026-10-30-5314.csv` | Preserved full export, including its citations, common-name/usage IDs, licences and attribution |
| `source-manifest.json` | Source origin, acquisition date, byte checksum, expected source and output counts |
| `dataset-metadata.ttl` | Dataset identifier, explicit dates, description, licence, attribution and source provenance |
| `convert.py` | Offline deduplicated lookup generation and exact coverage checks |
| `checks.rq` | Counts and checks for orphan mappings, conflicting scientific labels, NSL relationships and anonymous nodes |
| `verify.py` | Exact RDF graph comparison; anonymous nodes are rejected |
| `test_workflow.py` | Tests for many-to-many preservation, deduplication, changed mappings, labels, attribution and source integrity |
| `pyproject.toml`, `uv.lock`, `.python-version` | Locked execution environment |

The source CSV is preserved unchanged. `schema:license` and `schema:creditText` record licence and attribution at Dataset level, and `prov:wasDerivedFrom` identifies the original bytes by SHA-256 URN. Every row's attribution IRI in this snapshot equals its scientific-name subject. The converter rejects changed attribution or licensing rather than silently dropping a future exception.

The catalogue file is generated from the maintained method and metadata. Do not maintain changes only in the generated output. No external working directory, API cache, or production GraphDB access is needed to reproduce it.

## Prefix policy

Prefixes are a readability convention, not the dataset's semantic identity. Prefer an ontology's declared `vann:preferredNamespacePrefix` for the matching `vann:preferredNamespaceUri` where available; otherwise follow existing repository usage. Resolve any local prefix collision explicitly without changing the namespace IRI. See the [VANN definitions](https://vocab.org/vann/).

Here, `apni:` matches the EPBC dataset's APNI name namespace; `dwc:`, `schema:`, and `prov:` follow existing repository usage. These are local serialization choices; this directory does not claim that APNI authoritatively declares those preferred prefixes. Namespace bindings are supplied to RDFLib, but no compaction pass, live vocabulary fetch, or prefix-specific validity rule is required. A different prefix spelling must not change the graph or fail the reproduction check.

## Refreshing

A refresh is a reviewed change, separate from reproduction. Preserve a new dated export, record its origin and checksum in the manifest, inspect changed mappings and any new attribution requirements, update expected counts and explicit Dataset dates/descriptions, then regenerate and review the RDF and catalogue changes. Unexpected or changed inputs are rejected. `.gitattributes` disables input line-ending conversion so downloaded-byte checksums survive cross-platform checkout.

## Licence

The source and derivative lookup data retain [CC BY 3.0](http://creativecommons.org/licenses/by/3.0/). Attribution is recorded in Dataset metadata and the source CSV. The repository's general CC BY 4.0 statement for novel content does not replace the input data's licence. No licence for a cited publication is inferred from the export licence.
