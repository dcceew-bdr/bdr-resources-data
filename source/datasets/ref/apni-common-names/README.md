# APNI common-name reference dataset

This directory contains the preserved inputs and method for regenerating `resources/datasets/items/apni-common-names-nsl.ttl`. It implements the draft NSL usage pattern developed for [bdr-ops #312](https://github.com/dcceew-bdr/bdr-ops/issues/312).

The source snapshot is the APNI common-name CSV downloaded on 30 October 2026. It contains 64,714 records, 28,022 common-name IDs, 17,204 scientific-name IDs, and 37,165 distinct name-ID pairs. The CSV's 28,014 distinct common-name strings should not be mistaken for its number of name resources. Different source usage IDs supporting the same pair are retained.

## Reproduce and check

Use Python 3.13 and uv. `pyproject.toml` and `uv.lock` pin RDFLib and its dependency versions. The initial run may download the locked packages and Python; the conversion itself reads local files only and never fetches live APNI data.

From the repository root:

```bash
cd source/datasets/ref/apni-common-names
uv run --locked python -m unittest -v
uv run --locked convert.py --check-existing ../../../../resources/datasets/items/apni-common-names-nsl.ttl
```

The converter verifies all input checksums, validates source and output counts, checks the RDF structure, and compares the generated graph with the checked-in catalogue graph. It exits unsuccessfully if the graphs differ. It then writes the generated Turtle and reports into ignored `build/`. The checked-in catalogue file is not overwritten by that command.

The comparison ignores Turtle prefixes, statement order, and anonymous-node labels. It checks every RDF triple after matching anonymous scientific usages by their identified common-usage owner. It refuses unsupported anonymous-node structures instead of silently accepting them. This comparison is specific to the documented structure; it is not a general RDF canonicalization tool.

To generate a reviewed replacement deliberately:

```bash
uv run --locked convert.py --output ../../../../resources/datasets/items/apni-common-names-nsl.ttl
```

Changing only serialization is unnecessary for an update. Do not replace the checked-in file just to reproduce a different prefix layout. The PR workflow runs the tests and full regeneration/comparison when the method or generated dataset changes. It has read-only repository permissions and does not publish to an RDF database.

## Files and authority

| File | Purpose |
| --- | --- |
| `inputs/APNI-common-names-2026-10-30-5314.csv` | Preserved source export; authoritative evidence for this snapshot's rows |
| `inputs/enrichment/*.json` | Unmodified public APNI responses used to resolve the worked example |
| `source-manifest.json` | Acquisition details, SHA-256 hashes, file sizes, dataset IRI, and expected snapshot counts |
| `dataset-metadata.ttl` | Maintained Dataset metadata; dates are explicit snapshot metadata, not the runtime date |
| `convert.py` | Offline CSV-to-RDF transformation |
| `checks.rq` | Independent SPARQL counts and structural error checks |
| `verify.py` | RDF graph equivalence check supporting this usage structure |
| `test_workflow.py` | Tests that changed mappings, citations, and source evidence are detected |
| `pyproject.toml`, `uv.lock`, `.python-version` | Reproduction environment |

The catalogue Turtle is a generated publication copy. Change the preserved-input selection, transformation, or metadata here before regenerating it; do not maintain corrections only in that output. The original CSV and API responses remain evidence, not editable master RDF. The earlier local working directory is not required to reproduce this dataset.

## Mapping rules

No new classes or predicates are introduced. Both common and scientific names retain their APNI name IRIs and receive `nsl:TaxonName` and their verbatim CSV text as `rdfs:label`. Common names additionally receive `schema:additionalType nt:common`, using `https://linked.data.gov.au/def/nsl/tn-types/`. Scientific-name subtypes and ranks are not guessed: an autonym is not reclassified as an ordinary scientific name.

| CSV evidence | RDF representation |
| --- | --- |
| `common_name_id`, `common_name` | Common-name resource and label |
| `scientific_name_id`, `scientific_name` | Scientific-name resource and label |
| `instance_id` | Identified common-name `nsl:TaxonNameUsage`, linked to its common name by `nsl:usageOf` |
| Common/scientific association | Common-name usage `nsl:citing` scientific-name usage; the latter has `nsl:usageOf` the scientific name |
| `citation` | Verbatim `schema:citation` literal on both usages |
| `license` | `dcterms:license` on the common-name usage and `schema:license` on the Dataset |
| `ccAttributionIRI` | `cc:attributionURL` on the common-name usage |
| `datasetName` | Dataset `schema:identifier` |

The checksum URN identifies the source CSV. Usage resources and Dataset provenance refer to it via `prov:wasDerivedFrom`.

The two cached API responses, retrieved on 30 October 2026, resolve common usage `51267250` to scientific usage `51266104`, reference `43053`, and page 326. The converter checks that the cached name IDs and citation agree with the CSV before using them. Its scientific usage type and reference metadata are taken from that evidence.

For the other 64,713 records, the scientific usage IRI is absent from the CSV. Anonymous scientific-usage nodes preserve the association without fabricating an APNI identifier. These nodes do not assert that the underlying real-world usages are distinct. Reference IRIs, page numbers, and scientific usage types are not guessed. No `nsl:cited` targets are invented.

The `citedBy` to `nsl:citing` conversion is still a modelling proposal requiring NSL maintainer confirmation. Reproducibility verifies implementation of that proposal, not its taxonomic correctness. Concept-valued common-name types supplement rather than remove literal types already held in production.

## Prefix policy

Prefixes are a readability convention, not the dataset's semantic identity. Prefer an ontology's declared `vann:preferredNamespacePrefix` for the matching `vann:preferredNamespaceUri` where available; otherwise follow existing repository usage. Resolve any local prefix collision explicitly without changing the namespace IRI. See the [VANN definitions](https://vocab.org/vann/).

Here, `apni:` matches the EPBC dataset's APNI name namespace, `inst:` identifies APNI instances, and `nsl:`, `schema:`, `prov:`, and the other bindings follow the existing work. These are local serialization choices; this directory does not claim that APNI authoritatively declares those preferred prefixes. Namespace bindings are supplied to RDFLib, but no compaction pass, live vocabulary fetch, or prefix-specific validity rule is required. A different prefix spelling must not change the graph or fail the reproduction check.

## Refreshing or extending

A refresh is a separate reviewed change, not part of reproduction. Preserve a new dated export and any new API evidence; record their origins and checksums in `source-manifest.json`; review row additions, removals, changed associations, and modelling assumptions; update the expected counts and structural expectations in the manifest (and `checks.rq` if the model changes); update explicit Dataset dates and descriptions; regenerate and review the output and catalogue changes in a PR.

The manifest deliberately rejects unexpected or changed input files. Do not bypass checksum checking to replace the historical evidence. If manual RDF curation becomes the authoring source of truth later, record that transition before treating this converter as authoritative.

The local `.gitattributes` disables line-ending conversion for preserved inputs so their downloaded-byte checksums survive checkout on different platforms.

## Licence and attribution

The APNI CSV declares [CC BY 3.0](http://creativecommons.org/licenses/by/3.0/) and supplies row-level attribution IRIs. The input and its derivative data retain those terms; the repository's general CC BY 4.0 statement for novel content does not replace them. API responses are retained as public source evidence with their original URLs in the manifest. No licence for the cited book is inferred from the export licence.
