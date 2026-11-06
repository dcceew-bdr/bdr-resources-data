"""Rebuild the TERN rank publication from checksummed public responses."""
import hashlib
import json
from pathlib import Path

from rdflib import Graph, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parents[2] / 'resources/vocabs/items/tern-cv-taxon-ranks.ttl'

# Publish vocabulary descriptions, not the server's inferred mapping closure or
# display annotations. Self-matches in the expanded response are also omitted.
PREDICATES = {
    RDF.type, RDFS.isDefinedBy, RDFS.seeAlso,
    SKOS.prefLabel, SKOS.altLabel, SKOS.hiddenLabel, SKOS.definition,
    SKOS.note, SKOS.scopeNote, SKOS.notation, SKOS.inScheme, SKOS.member,
    SKOS.exactMatch, DCTERMS.created, DCTERMS.modified, DCTERMS.source,
    DCTERMS.contributor, DCTERMS.publisher, DCTERMS.creator,
    DCTERMS.license, DCTERMS.rights,
}


def main():
    metadata = json.loads((HERE / 'source-manifest.json').read_text())
    collection = URIRef(metadata['collection'])
    members = {URIRef(iri) for iri in metadata['members']}
    result = Graph()
    for prefix, ns in [('skos', SKOS), ('rdf', RDF), ('rdfs', RDFS), ('dcterms', DCTERMS)]:
        result.bind(prefix, ns)
    for resource in metadata['resources']:
        raw = (HERE / resource['file']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != resource['sha256']:
            raise ValueError(f"Source checksum mismatch: {resource['file']}")
        source = Graph().parse(data=raw, format='turtle')
        subject = URIRef(resource['iri'])
        for s, p, o in source.triples((subject, None, None)):
            if p in PREDICATES and not (p == SKOS.exactMatch and s == o):
                result.add((s, p, o))
    assert set(result.objects(collection, SKOS.member)) == members
    assert len(members) == 33
    assert (collection, RDF.type, SKOS.Collection) in result
    assert (collection, RDF.type, SKOS.ConceptScheme) not in result
    assert set(result.subjects(RDF.type, SKOS.Concept)) == members
    for member in members:
        assert list(result.objects(member, SKOS.prefLabel)), member
        assert list(result.objects(member, SKOS.definition)), member
        assert str(member).startswith('http://linked.data.gov.au/def/tern-cv/')
    OUTPUT.write_text(result.serialize(format='longturtle'))
    print(f'Published {len(members)} existing rank concepts and their collection: {OUTPUT}')


if __name__ == '__main__':
    main()
