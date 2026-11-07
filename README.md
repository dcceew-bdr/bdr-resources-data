# resources.bdr.gov.au Data

This repository contains the static (file-based) data available at <https://resources.bdr.gov.au> which is the catalogue 
of reference data supporting the [Biodiversity Data repository](https://bdr.gov.au). It also contains information about 
all other resources listed in that catalogue, whether it contains the static data or not.

Content here is _not_ the main data of the BDR - observations of species occurrence - which is available from 
<https://bdr.gov.au>.

## Data Management

The resources are managed using [kgm](https://kurrawong.github.io/kgm/), so there is a manifest at `resources/manifest.ttl`
that links to and indicates roles for all the static resources.

The [APNI common-name dataset source](source/datasets/ref/apni-common-names/README.md) includes the preserved CSV, locked conversion environment, mapping rules, and commands to regenerate and verify its direct scientific-name/common-name lookups. Its reproduction workflow checks exact source coverage and compares RDF statements independently of Turtle prefixes and ordering.

## License & Copyright

The license for novel content in this repository is the standard Australian government open source license:

* [CC BY 4.0 - Creative Commons Attribution 4.0 International](https://creativecommons.org/licenses/by/4.0/)

Copyright is

© Department of Climate Change, Energy, the Environment and Water

## Contacts

**Biodiversity Data Repository Team**  
[Department of Climate Change, Energy, the Environment and Water](https://www.dcceew.gov.au)  
<https://bdr.gov.au>  
<bdr@dcceew.gov.au>

For technical contributions, please use the [Issue Tracker](https://github.com/dcceew-bdr/resources.bdr.gov.au-data/issues) 
for this repository.
