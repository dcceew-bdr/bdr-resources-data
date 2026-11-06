# BDR taxonomic rank scheme using TERN concepts

The published vocabulary is BDR’s existing ConceptScheme, `https://linked.data.gov.au/dataset/bdr/taxonomic-rank`, expanded from ten to 33 existing TERN concepts. The file remains `resources/vocabs/items/nsl-taxonomic-rank.ttl`. Every concept retains its original HTTP TERN IRI and definition. Preferred labels follow TERN except for the explicitly documented local correction below. The BDR scheme provides a local management unit; TERN remains the source of the rank concepts.

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

`verification.json` records preservation of the ten original concepts, unchanged definitions for all 33 TERN concepts and unchanged preferred labels for the 32 without a local correction, flat scheme membership, the ordinary catalogue-to-scheme-to-concept route and a literal/IRI display example. The scoped shapes check the scheme and its members. These checks do not prove live deployment or complete NSL rank coverage.

## Local display-label correction

`label-overrides.json` changes the BDR publication’s English preferred label for `8d227e73-f906-4d5f-9f15-8ae8bf29b2ce` from `infragenericname` to `infrageneric name`. The builder checks the original label before applying this exception. The original source response remains unchanged, and the concept IRI, definition, GBIF exact match and `rdfs:isDefinedBy` are preserved. No label change is asserted in TERN’s source or any existing live reference graph.

The BDR publication does not contain TERN’s Categorical Concepts membership or self exact matches. These may still appear in the preserved upstream responses. A self exact match can arise through SKOS symmetry/transitivity; it is redundant for this publication and is filtered out. `skos:inScheme` itself states scheme membership; a scheme’s top-concept list is not a mandatory listing of every member.

## Pending TERN advice

Refs [bdr-ops issue 299](https://github.com/dcceew-bdr/bdr-ops/issues/299); leave the issue open.

Junrong’s 22 October reply accepted the alternative-label suggestion and said the data officers were still reviewing the changes. Final additional concept IRIs, publication of alternative labels and definition-review decisions remain pending. The BDR scheme can add those concepts when TERN supplies them. This version uses the 33 existing public concepts and their current definitions; no proposed definitions or placeholder IRIs are included.

NSL dataset values and ingestion scripts are not changed by this publication. Uncovered values remain their original literals. Consumers need an optional preferred-label lookup for IRIs and the supplied text for literals; `rank-display-example.rq` illustrates that fallback. The separate ABIS mapping export is outside this update.

## Deployment: update the existing scheme graph

Synchronize the expanded file into the existing BDR scheme graph according to the target service’s normal manifest handling. Keep `https://linked.data.gov.au/dataset/bdr/taxonomic-rank` as the management IRI. **Do not delete that graph**: it is the scheme being retained and expanded. Earlier advice to remove the temporary rank graph is superseded.

The existing ConceptScheme API routes can expose this vocabulary and its 33 concepts. No catalogue-level Collection route or special API extension is required. The companion site change withdraws only the unnecessary routes introduced for the previous collection-based design, preserving existing scheme, collection-within-scheme and dataset-container routes.

After synchronization, check the scheme and member-list endpoints and verify the original ten concept labels through the consuming API. The existing TERN reference graph and NSL version graph are unaffected. If the abandoned standalone collection graph was loaded, first confirm it is unused before considering a separate cleanup; its deletion is not part of updating the retained scheme.
