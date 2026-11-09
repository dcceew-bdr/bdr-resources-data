# BDR taxonomic rank scheme using TERN and GBIF concepts

The published vocabulary is BDR’s existing ConceptScheme, `https://linked.data.gov.au/dataset/bdr/taxonomic-rank`, expanded from ten to 33 existing TERN concepts plus the GBIF subkingdom concept (34 total). The file remains `resources/vocabs/items/nsl-taxonomic-rank.ttl`. Every reused concept retains its publisher’s original HTTP IRI. Labels and definitions follow TERN except for the explicitly documented BDR editorial corrections below. The BDR scheme provides a local management unit; TERN remains the source of the rank concepts.

This follows Nick’s advice on bdr-ops issue 299. A BDR scheme can reuse TERN concept IRIs without adopting TERN’s collection as its catalogue management structure. The previously proposed catalogue-level Collection publication and its extra API routes are superseded. TERN’s own collection is not retyped or changed.

## Rebuild the flat scheme

`build.py` reads the preserved individual TERN concept responses, verifies their checksums and bundles the concepts into the BDR scheme. No live download or database access occurs during a rebuild. All 33 concepts receive `skos:inScheme` and `skos:topConceptOf` pointing to the BDR scheme, which lists them with `skos:hasTopConcept`. No broader/narrower rank hierarchy is invented.

```bash
python source/vocabs/tern-taxon-ranks/build.py
python source/vocabs/tern-taxon-ranks/verify.py
kurra shacl validate resources/vocabs/items/nsl-taxonomic-rank.ttl -s source/vocabs/tern-taxon-ranks/shapes.ttl
```

Use an environment with RDFLib; the existing Kurra runtime is sufficient. The file is selected by the ordinary VocPub-conforming ResourceData entry in `resources/manifest.ttl`, with the BDR scheme linked from the vocabulary catalogue. An isolated KGM/VocPub check validates this resource independently of the existing ASLS full-catalogue validation issue.

`source-manifest.json` records the original TERN collection, its member IRIs, request/resolved URLs and response checksums. `snapshots/` preserves the collection and individual concept responses. `replaced-nsl-taxonomic-rank.ttl` preserves the original ten-concept BDR version for comparison. These source files are outside the publication manifest.

The builder copies only the basic concept fields from each response: RDF type, SKOS labels, definition, any scope note/notation, non-self exact matches and the original `rdfs:isDefinedBy`. All concept-level DCTERMS, `rdfs:label`, `rdfs:seeAlso`, duplicate `skos:note` descriptions, inferred mapping closure and self exact matches are omitted. The full upstream metadata remains in the source snapshots. The native BDR scheme keeps its own publication metadata and source citation. In this publication, membership is stated in the BDR scheme; the upstream TERN membership remains recorded in the source snapshots. The BDR scheme cites the TERN collection as its source.

`verification.json` records preservation of the ten original concepts, unchanged definitions for the 29 concepts without a definition correction and unchanged preferred labels for the 27 without a label correction, flat scheme membership, the ordinary catalogue-to-scheme-to-concept route and a literal/IRI display example. The scoped shapes check the scheme and its members. These checks do not prove live deployment or complete NSL rank coverage.

## Local display-label correction

`label-overrides.json` preserves six reviewed BDR label corrections, including Nick’s November spelling refinements such as `infra-generic name`, `infra-order` and `infra-specific name`. The builder checks each original label before applying its replacement. Source snapshots, concept IRIs and original `rdfs:isDefinedBy` statements are retained.

## Local cultivar correction

`concept-overrides.json` replaces the cultivar naming-convention text with a definition of the plant grouping, adds a `skos:scopeNote` distinguishing cultivar from botanical variety/form, and separates the name example into `skos:example`. Its citation is ICNCP, ninth edition (2016), Article 2.3 and Article 2.1 Note 1, printed page 6. The definition is a BDR paraphrase, not a quotation or a claim that TERN has published this correction. The override records the previous definition, source URL and editorial reason outside the published vocabulary.

The builder verifies the exact previous definition before applying the override. A changed upstream definition stops regeneration and requires reconciliation; do not bypass this check or overwrite the source snapshots to force the build. To incorporate a future TERN release, review changes against these local corrections and retire an override once upstream wording is accepted. Editing generated Turtle alone is not durable.

ABIS has a separate generator: maintain the same definition, scope note and example in `abis_mapping/vocabs/taxon_rank.py`, then regenerate its export as described in `../abis-mapping/taxon-rank-labels.md`. Both generators must remain aligned for this shared concept.

The BDR publication does not contain TERN’s Categorical Concepts membership or self exact matches. These may still appear in the preserved upstream responses. A self exact match can arise through SKOS symmetry/transitivity; it is redundant for this publication and is filtered out. `skos:inScheme` itself states scheme membership; a scheme’s top-concept list is not a mandatory listing of every member.

## Pending TERN advice

Refs [bdr-ops issue 299](https://github.com/dcceew-bdr/bdr-ops/issues/299); leave the issue open.

Junrong’s 22 October reply accepted the alternative-label suggestion and said the data officers were still reviewing the changes. Final additional concept IRIs, publication of alternative labels and definition-review decisions remain pending. The BDR scheme can add those concepts when TERN supplies them. This version uses 33 existing TERN concepts plus GBIF subkingdom, with documented local editorial corrections; no placeholder IRIs are added.

NSL dataset values and ingestion scripts are not changed by this publication. Uncovered values remain their original literals. Consumers need an optional preferred-label lookup for IRIs and the supplied text for literals; `rank-display-example.rq` illustrates that fallback. The separate ABIS mapping export is outside this update.

## Deployment: update the existing scheme graph

Synchronize the expanded file into the existing BDR scheme graph according to the target service’s normal manifest handling. Keep `https://linked.data.gov.au/dataset/bdr/taxonomic-rank` as the management IRI. **Do not delete that graph**: it is the scheme being retained and expanded. Earlier advice to remove the temporary rank graph is superseded.

The existing ConceptScheme API routes can expose this vocabulary and its 33 concepts. No catalogue-level Collection route or special API extension is required. The companion site change withdraws only the unnecessary routes introduced for the previous collection-based design, preserving existing scheme, collection-within-scheme and dataset-container routes.

After synchronization, check the scheme and member-list endpoints and verify the original ten concept labels through the consuming API. The existing TERN reference graph and NSL version graph are unaffected. If the abandoned standalone collection graph was loaded, first confirm it is unused before considering a separate cleanup; its deletion is not part of updating the retained scheme.

The concept override file also preserves Nick’s existing `infra-order` definition spelling (the snapshot says `infraorder`). That is a preservation of the reviewed publication, not an additional definition rewrite in this change.

## Aggregate definitions and scope

The species aggregate and subspecific aggregate overrides retain short grouping definitions and separate zoological context and naming conventions into `skos:scopeNote`. These are BDR editorial splits, not new concepts or a restriction of all aggregate use to zoology. Naming guidance is paraphrased from [ICZN Article 6.2](https://code.iczn.org/chapter-2-the-number-of-words-in-the-scientific-names-of-animals/article-6-interpolated-names/). The old Berlin/MoreTax implementation commentary is omitted from the published description; the full original definitions remain in the checksum-verified snapshots and override records. No assertion that aggregates universally lack taxonomic rank is made. Both ABIS source terms contain the same definitions and scope notes.

## GBIF subkingdom

`supplemental-concepts.ttl` is the maintained BDR description of `http://rs.gbif.org/vocabulary/gbif/rank/subkingdom`. The builder adds it alongside the 33 TERN concepts (34 total) and assigns flat BDR scheme membership. Its `rdfs:isDefinedBy` is the GBIF vocabulary IRI `http://rs.gbif.org/vocabulary/gbif/rank`, not the BDR scheme or the dated XML document. The GBIF XML declares that vocabulary IRI on its root element.

GBIF supplies the identifier and preferred label but an empty description. The BDR definition is “A taxonomic rank below kingdom and above phylum (division).”, paraphrased from [ICN Article 4.2](https://www.iapt-taxon.org/nomen/pages/main/art_4.html). `supplemental-sources.json` records provenance, a checksum-verified GBIF snapshot, and replacement of the old ABIS `http://example.com/subkingdom` placeholder. The preserved XML document is evidence, not the `rdfs:isDefinedBy` target.

The ABIS Python term uses the same GBIF IRI, definition and defining vocabulary, and exports `dcterms:replaces` for the previous placeholder. All 45 input keys remain accepted; the subkingdom key now produces the GBIF IRI. Existing data containing the placeholder is not rewritten by this source change. Inventory and migration of stored uses are a separate deployment/data task. A future TERN subkingdom concept does not automatically replace the GBIF identifier: review equivalence before changing identifiers again.
