"""Group the published TERN rank concepts in BDR's existing SKOS scheme."""
import hashlib
import json
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DCTERMS, RDF, RDFS, SKOS, XSD

HERE = Path(__file__).resolve().parent
OUTPUT = HERE.parents[2] / 'resources/vocabs/items/nsl-taxonomic-rank.ttl'
SCHEME = URIRef('https://linked.data.gov.au/dataset/bdr/taxonomic-rank')
SCHEMA = Namespace('https://schema.org/')

# Keep the basic concept description and original definition authority. All
# concept-level DCTERMS, display annotations and duplicate notes stay in sources.
PREDICATES = {
    RDF.type, RDFS.isDefinedBy,
    SKOS.prefLabel, SKOS.altLabel, SKOS.hiddenLabel, SKOS.definition,
    SKOS.scopeNote, SKOS.notation, SKOS.exactMatch,
}


def main():
    metadata = json.loads((HERE / 'source-manifest.json').read_text())
    collection = URIRef(metadata['collection'])
    members = {URIRef(iri) for iri in metadata['members']}
    overrides = json.loads((HERE / 'label-overrides.json').read_text())
    assert set(overrides) <= {str(member) for member in members}
    result = Graph()
    for prefix, ns in [('skos', SKOS), ('rdf', RDF), ('rdfs', RDFS), ('dcterms', DCTERMS), ('schema', SCHEMA)]:
        result.bind(prefix, ns)
    for resource in metadata['resources']:
        raw = (HERE / resource['file']).read_bytes()
        if hashlib.sha256(raw).hexdigest() != resource['sha256']:
            raise ValueError(f"Source checksum mismatch: {resource['file']}")
        source = Graph().parse(data=raw, format='turtle')
        subject = URIRef(resource['iri'])
        if subject == collection:
            assert set(source.objects(collection, SKOS.member)) == members
            continue
        for s, p, o in source.triples((subject, None, None)):
            if p in PREDICATES and not (p == SKOS.exactMatch and s == o):
                result.add((s, p, o))
        if str(subject) in overrides:
            override = overrides[str(subject)]
            original = Literal(override['source_label'], lang=override['language'])
            assert set(result.objects(subject, SKOS.prefLabel)) == {original}, subject
            result.remove((subject, SKOS.prefLabel, original))
            result.add((subject, SKOS.prefLabel,
                        Literal(override['preferred_label'], lang=override['language'])))
        # This publication states membership in BDR's management scheme; it
        # does not change the concept's IRI or its TERN definition.
        result.add((subject, SKOS.inScheme, SCHEME))
        result.add((subject, SKOS.topConceptOf, SCHEME))
        result.add((SCHEME, SKOS.hasTopConcept, subject))
    result.add((SCHEME, RDF.type, SKOS.ConceptScheme))
    result.add((SCHEME, SKOS.prefLabel, Literal('NSL Taxonomic Rank', lang='en')))
    result.add((SCHEME, SKOS.definition, Literal(
        'A BDR-managed grouping of TERN taxonomic rank concepts for use with National Species List data. '
        'Concept IRIs, labels and definitions are reused from TERN.', lang='en')))
    result.add((SCHEME, DCTERMS.source, collection))
    result.add((SCHEME, SCHEMA.creator, URIRef('https://linked.data.gov.au/org/dcceew')))
    result.add((SCHEME, SCHEMA.publisher, URIRef('https://linked.data.gov.au/org/dcceew')))
    result.add((SCHEME, SCHEMA.license, URIRef('http://purl.org/NET/rdflicense/cc-by4.0')))
    result.add((SCHEME, SCHEMA.dateCreated, Literal('2026-10-19', datatype=XSD.date)))
    result.add((SCHEME, SCHEMA.dateModified, Literal('2026-11-06', datatype=XSD.date)))
    result.add((SCHEME, SCHEMA.version, Literal('2')))
    result.add((SCHEME, SKOS.historyNote, Literal(
        'Expanded from the original ten-rank BDR scheme to include the 33 published TERN rank concepts, '
        'while retaining the BDR scheme IRI and TERN concept IRIs.', lang='en')))
    # Include the local creator/publisher description needed for standalone
    # VocPub validation, using the existing BDR organizations vocabulary values.
    publisher = URIRef('https://linked.data.gov.au/org/dcceew')
    result.add((publisher, RDF.type, SCHEMA.Organization))
    result.add((publisher, SCHEMA.name, Literal(
        'Department of Climate Change, Energy, the Environment and Water')))
    result.add((publisher, SCHEMA.url, Literal('https://www.dcceew.gov.au', datatype=XSD.anyURI)))
    assert set(result.objects(SCHEME, SKOS.hasTopConcept)) == members
    assert len(members) == 33
    assert (collection, RDF.type, SKOS.ConceptScheme) not in result
    assert not list(result.subjects(RDF.type, SKOS.Collection))
    assert set(result.subjects(RDF.type, SKOS.Concept)) == members
    for member in members:
        assert list(result.objects(member, SKOS.prefLabel)), member
        assert list(result.objects(member, SKOS.definition)), member
        assert str(member).startswith('http://linked.data.gov.au/def/tern-cv/')
    OUTPUT.write_text(result.serialize(format='longturtle'))
    print(f'Grouped {len(members)} existing TERN rank concepts in the BDR scheme: {OUTPUT}')


if __name__ == '__main__':
    main()
