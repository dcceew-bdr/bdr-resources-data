# IDN Role Codes source

`resources/vocabs/items/data-roles.ttl` is a byte-for-byte copy of the RDF served on 18 November 2026 by the canonical scheme IRI <https://linked.data.gov.au/def/data-roles>. That IRI redirects to <https://agldwg.github.io/data-roles/vocabulary.ttl>.

The source identifies the scheme as **IDN Role Codes**, with 25 SKOS concepts and a CC BY 4.0 licence. Its 20 ISO-derived roles and five IDN additions have IRIs under `https://linked.data.gov.au/def/data-roles/`. Keep this scheme separate from the ISO RoleCode vocabulary already published by BDR: their concept IRIs differ.

SHA-256 of the copied Turtle file: `449e4d16b891d29a92b956fd4e16f4f5852ff7783a2ffd31a91a5cf28f1ae4da`.

The existing `vocabs/items/**/*.ttl` resource entry in `resources/manifest.ttl` includes this file in KGM sync. `resources/vocabs/_cat.ttl` registers the scheme in the Resources vocabulary catalogue. To update the copy, fetch the canonical IRI with `Accept: text/turtle`, review the RDF diff and provenance, then validate the manifest before syncing.
