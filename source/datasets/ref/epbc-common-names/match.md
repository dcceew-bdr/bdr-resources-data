# NSL Matching

This is the process that was used to match scientific names in extract.csv to the NSL in the BDR.

As per  https://github.com/dcceew-bdr/bdr-query-utilities/blob/main/docs/nsl_matching.md#matching-an-arbitrary-csv:

```bash
 python main.py --phase match \
  --names-csv epbc-extract.csv --csv-column "Current Scientific Name" \
  --out-dir epbc_match_out
```

Output:

```bash
[match] started 2026-11-19 15:22:09
NSL index: 485202 rows
  exact keys     : 482078 (2527 ambiguous)
  canonical keys : 399193 (8910 ambiguous)
  uninomial keys : 72546 (2468 ambiguous)
  no canonical   : 0
[match] 2572 distinct names from epbc-extract.csv

--- match report ---------------------------------------
tier / reason          names       %    occurrences       %
exact                     13    0.5%             13    0.5%
exact_ws                   0    0.0%              0    0.0%
canonical               2446   95.1%           2446   95.1%
autonym                    1    0.0%              1    0.0%
uninomial                 21    0.8%             21    0.8%
ambiguous                  1    0.0%              1    0.0%
author_mismatch           10    0.4%             10    0.4%
not_found                 80    3.1%             80    3.1%
indeterminate              0    0.0%              0    0.0%
unparseable                0    0.0%              0    0.0%
TOTAL                   2572                   2572

--- summary ------
outcome                names       %    occurrences       %
matched.csv             2481   96.5%           2481   96.5%
ambiguous.csv              1    0.0%              1    0.0%
unmatched.csv             90    3.5%             90    3.5%
--------------------------------------------------------

[match] finished 2026-11-19 15:22:12 - took 0:00:03 (3.0s)
```

The resulting files are:

* match/ambiguous.csv
* match/matched.csv
* match/unmatched.csv

Only terms from mathes.csv have been used by extract.py to make the RDF dataset.
