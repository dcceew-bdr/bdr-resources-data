"""Check the replacement's coverage and its literal/IRI display example."""
import json
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, SKOS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COLLECTION = URIRef('http://linked.data.gov.au/def/tern-cv/c14559b5-6a80-4045-ab48-a70d1612a685')


def main():
    current = Graph().parse(ROOT / 'resources/vocabs/items/tern-cv-taxon-ranks.ttl')
    previous = Graph().parse(HERE / 'replaced-nsl-taxonomic-rank.ttl')
    members = set(current.objects(COLLECTION, SKOS.member))
    old_concepts = set(previous.subjects(RDF.type, SKOS.Concept))
    assert len(members) == 33 and len(old_concepts) == 10
    assert old_concepts <= members
    for concept in old_concepts:
        assert set(previous.objects(concept, SKOS.prefLabel)) == set(current.objects(concept, SKOS.prefLabel))
        assert set(previous.objects(concept, SKOS.definition)) == set(current.objects(concept, SKOS.definition))
    for member in members:
        assert (member, RDF.type, SKOS.Concept) in current
        assert str(member).startswith('http://linked.data.gov.au/def/tern-cv/')
        assert list(current.objects(member, SKOS.prefLabel))
        assert list(current.objects(member, SKOS.definition))
        assert 'example.com' not in str(member)
    assert (COLLECTION, RDF.type, SKOS.Collection) in current
    assert (COLLECTION, RDF.type, SKOS.ConceptScheme) not in current
    catalogue = Graph().parse(ROOT / 'resources/vocabs/_cat.ttl')
    schema_part = URIRef('https://schema.org/hasPart')
    assert (None, schema_part, COLLECTION) in catalogue
    assert (None, schema_part, URIRef('https://linked.data.gov.au/dataset/bdr/taxonomic-rank')) not in catalogue
    query = (HERE / 'rank-display-example.rq').read_text()
    # Sample dataset statements are local query controls, never publication data.
    for index, rank in enumerate([
        URIRef('http://linked.data.gov.au/def/tern-cv/2b6fae57-f28e-4f24-b6f9-19f114dbb61e'),
        Literal('subclass'), URIRef('urn:unlabelled-rank'),
    ]):
        current.add((URIRef(f'urn:test:name:{index}'), URIRef('http://rs.tdwg.org/dwc/terms/taxonRank'), rank))
    displays = {str(row.rank): str(row.displayLabel) for row in current.query(query)}
    assert displays['http://linked.data.gov.au/def/tern-cv/2b6fae57-f28e-4f24-b6f9-19f114dbb61e'] == 'species'
    assert displays['subclass'] == 'subclass'
    assert displays['urn:unlabelled-rank'] == 'urn:unlabelled-rank'
    report = {
        'existing_tern_rank_concepts': len(members),
        'replaced_temporary_concepts': len(old_concepts),
        'all_ten_labels_and_definitions_preserved': True,
        'all_members_have_labels_and_definitions': True,
        'http_identifiers_preserved': True,
        'collection_not_retyped_as_scheme': True,
        'no_placeholder_concepts_added': True,
        'catalogue_references_collection_instead_of_temporary_scheme': True,
        'display_example_handles_iri_literal_and_unlabelled_iri': True,
        'scope': 'Local replacement and query verification; not live API or database deployment verification.',
    }
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
