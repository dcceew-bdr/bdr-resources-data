# TERN Taxon ranks publication

This publication replaces the temporary `nsl-taxonomic-rank.ttl` resource with the existing TERN Taxon ranks collection and all 33 of its currently published concepts. It preserves the HTTP concept identifiers used by NSL, including the original ten concepts' preferred labels and definitions. It changes reference vocabulary content, not NSL dataset values or ingestion scripts.

The upstream collection remains a `skos:Collection`. It is not retyped as a concept scheme or wrapped in a new BDR scheme. The manifest identifies the collection explicitly through `schema:mainEntity` and `schema:contentLocation`, outside the block claiming VocPub scheme conformance. This is a different resource type, not an exception to a failed scheme validation. The catalogue links directly to the TERN collection.

## Sources and reproduction

`source-manifest.json` records the retrieved public collection, its 33 member IRIs, the request/resolved URLs and response SHA-256 values. `snapshots/` contains those responses. `replaced-nsl-taxonomic-rank.ttl` preserves the previous temporary resource for coverage comparison; neither it nor these snapshots is selected by the publication manifest.

Rebuild and verify using an environment containing RDFLib (the existing Kurra runtime is sufficient):

```bash
python source/vocabs/tern-taxon-ranks/build.py
python source/vocabs/tern-taxon-ranks/verify.py
kurra shacl validate resources/vocabs/items/tern-cv-taxon-ranks.ttl -s source/vocabs/tern-taxon-ranks/shapes.ttl
```

The builder copies each resource's vocabulary description from its own response, retaining upstream labels, definitions, source citations, non-self exact matches and available scheme membership. It omits server-generated display annotations, inferred semantic/mapping/close-match closure, and redundant self exact matches. It does not introduce rewritten definitions, repair upstream scheme membership, or mint concepts. `verification.json` records the local coverage checks. The SHACL shapes verify this scoped collection and its labels/definitions; they do not assert completeness of NSL rank coverage.

KGM successfully expands the full manifest and selects the new collection instead of the temporary resource. An isolated manifest for the collection passes KGM validation. Full-manifest validation currently stops on an existing ASLS soil-profile person record without a required email address; this change does not bypass or repair that unrelated error.

## What remains pending

Refs [bdr-ops issue 299](https://github.com/dcceew-bdr/bdr-ops/issues/299); this change does not close the issue.

Junrong's 22 October reply accepted adding alternative labels and said the data officers were still reviewing the changes. No final IRIs or completed review decisions have been supplied here for the seven proposed additions or four additional concepts under review. The richer existing-rank definitions also remain a separate review. This publication uses the existing public concepts and definitions and can be extended when TERN supplies those decisions.

Leave uncovered NSL values as their original literals. Temporary IRIs would add an identifier-migration obligation without confirmed equivalence to future TERN concepts. A mixture of rank IRIs and literals already exists in NSL; the publication does not alter it. Consumers must treat an IRI as a resource to label and a literal as the supplied text. A mandatory join to `skos:prefLabel` would discard literal-valued rows. `rank-display-example.rq` demonstrates an optional label lookup and literal fallback; it is an example, not a deployed API change. The existing ABIS mapping export is outside this replacement's scope.

## Deployment and removal of the old graph

The repository change replaces the temporary source artifact and catalogue entry atomically. It does not itself load production BDR GraphDB or the resources Fuseki database. During deployment, first deploy the companion `bdr-resources-site` endpoint change that admits `skos:Collection` at catalogue level and follows inverse `skos:member` paths for its concepts. Then load the new collection graph, check the original ten labels through the consuming API, then remove only the old temporary named graph `https://linked.data.gov.au/dataset/bdr/taxonomic-rank` and verify again. Manifest sync may preserve graphs no longer mentioned by the manifest, so removing a file is not proof that the old database graph is gone.

The replacement graph's main entity is `http://linked.data.gov.au/def/tern-cv/c14559b5-6a80-4045-ab48-a70d1612a685`. Confirm the actual graph naming/load convention separately in each target service. Do not remove the existing TERN reference graph or NSL version graph. Live service synchronization, API response checks and removal of the deployed temporary graph remain operational steps; the local checks do not claim those steps have happened.

The companion endpoint change preserves existing scheme and dataset-container routes. `endpoint-verification.json` records successful SHACL checks of the catalogue, collection and member route shapes against the replacement data, plus reachability of all 33 concepts. It is not a deployed HTTP test.
