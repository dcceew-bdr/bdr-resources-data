"""Check the BDR scheme's reuse of TERN concepts and ordinary API routes."""
import json
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS, SKOS

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
COLLECTION = URIRef('http://linked.data.gov.au/def/tern-cv/c14559b5-6a80-4045-ab48-a70d1612a685')
SCHEME = URIRef('https://linked.data.gov.au/dataset/bdr/taxonomic-rank')


def main():
    current = Graph().parse(ROOT / 'resources/vocabs/items/nsl-taxonomic-rank.ttl')
    previous = Graph().parse(HERE / 'replaced-nsl-taxonomic-rank.ttl')
    members = set(current.subjects(SKOS.inScheme, SCHEME))
    assert members == set(current.objects(SCHEME, SKOS.hasTopConcept))
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
        source = Graph().parse(HERE / 'snapshots' / (str(member).rsplit('/', 1)[-1] + '.ttl'))
        for predicate in (SKOS.prefLabel, SKOS.definition, RDFS.isDefinedBy):
            assert set(source.objects(member, predicate)) == set(current.objects(member, predicate))
        assert not list(current.objects(member, RDFS.label))
        assert not any(str(p).startswith('http://purl.org/dc/terms/') for p in current.predicates(member))
    assert (SCHEME, RDF.type, SKOS.ConceptScheme) in current
    assert (COLLECTION, RDF.type, SKOS.ConceptScheme) not in current
    assert not list(current.subjects(RDF.type, SKOS.Collection))
    catalogue = Graph().parse(ROOT / 'resources/vocabs/_cat.ttl')
    schema_part = URIRef('https://schema.org/hasPart')
    assert (None, schema_part, SCHEME) in catalogue
    assert (None, schema_part, COLLECTION) not in catalogue
    route_data = current + catalogue
    query_members = route_data.query('''PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX schema: <https://schema.org/>
        SELECT ?member WHERE {
            ?catalogue a schema:DataCatalog ; schema:hasPart
                <https://linked.data.gov.au/dataset/bdr/taxonomic-rank> .
            <https://linked.data.gov.au/dataset/bdr/taxonomic-rank> a skos:ConceptScheme .
            ?member a skos:Concept ; skos:inScheme
                <https://linked.data.gov.au/dataset/bdr/taxonomic-rank> .
        }''')
    assert {row.member for row in query_members} == members
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
        'original_bdr_scheme_concepts': len(old_concepts),
        'all_ten_labels_and_definitions_preserved': True,
        'all_members_have_labels_and_definitions': True,
        'http_identifiers_preserved': True,
        'bdr_scheme_iri_retained': True,
        'tern_collection_not_retyped_as_scheme': True,
        'all_33_tern_labels_and_definitions_unchanged': True,
        'original_isDefinedBy_preserved': True,
        'concept_dcterms_and_rdfs_label_removed': True,
        'no_placeholder_concepts_added': True,
        'catalogue_references_bdr_scheme': True,
        'all_33_concepts_reachable_by_existing_scheme_path': True,
        'display_example_handles_iri_literal_and_unlabelled_iri': True,
        'scope': 'Local replacement and query verification; not live API or database deployment verification.',
    }
    (HERE / 'verification.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
