# TERN Feature Type source

The published vocabulary is `resources/vocabs/non-vocpub/tern-cv-feature-type.ttl`. Its scheme IRI is `http://linked.data.gov.au/def/tern-cv/68af3d25-c801-4089-afff-cf701e2bd61d` (HTTP is intentional and matches the ABIS profile).

On 21 November 2026, the 1,390 triples for that scheme and its 126 exact `skos:inScheme` concepts were retrieved from TERN's public GraphDB repository at `https://graphdb.tern.org.au/repositories/tern_vocabs_core`, explicitly from named graph `http://linked.data.gov.au/def/tern-cv/`. The query selected every predicate and object of the scheme and those concepts:

```sparql
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
CONSTRUCT { ?s ?p ?o }
WHERE {
  GRAPH <http://linked.data.gov.au/def/tern-cv/> {
    { BIND(<http://linked.data.gov.au/def/tern-cv/68af3d25-c801-4089-afff-cf701e2bd61d> AS ?s) }
    UNION
    { ?s skos:inScheme <http://linked.data.gov.au/def/tern-cv/68af3d25-c801-4089-afff-cf701e2bd61d> }
    ?s ?p ?o
  }
}
```

The live result was compared as RDF triples with `tern-cv-fix/source/20261019-tern-cv-applied.nq` in the BDR workspace. Both had the same 126 concept IRIs and the same 1,390 selected triples. That local file is a dated copy of Junrong's `after.nq`; it is not the source of authority for future refreshes. The Turtle file is a format conversion of the live RDF with no added or removed triples.

This file uses the manifest's `vocabs/non-vocpub/*.ttl` resource path because TERN's current source does not pass the repository's pinned VocPub shape. In particular, some concepts lack a complete hierarchy, and the scheme lacks the required creator and publisher assertions. The data is kept as TERN supplied it; those assertions should not be invented for publication. The catalogue registration and TERN scope tag are in `resources/vocabs/_cat.ttl`.

To refresh, rerun the query against the TERN repository, compare the resulting RDF graph with this file, and review any differences before replacing it. The manifest sync workflow publishes the file and catalogue entry to Resources DEV Fuseki after a release or manual dispatch.
