# Execution-grounded re-check of INCORRECT verdicts — Dev

Total INCORRECT items: 94

## Auto-verdict summary

| Verdict | Count |
|---|---|
| INCORRECT | 14 |
| PARTIALLY_CORRECT | 19 |
| CORRECT | 0 |
| NEEDS_MANUAL | 61 |
| INCONCLUSIVE | 0 |
| EXEC_ERROR | 0 |

## Per-item

| ID | DB | verdict | complaint types | reason | evidence |
|---|---|---|---|---|---|
| 17 | concert_singer | NEEDS_MANUAL | agg,groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['agg', 'groupby'] |
| 34 | concert_singer | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 6 rows; complaint types=['inner_left'] |
| 48 | pets_1 | NEEDS_MANUAL | filter | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['filter'] |
| 49 | pets_1 | NEEDS_MANUAL | filter | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['filter'] |
| 60 | pets_1 | INCORRECT | setop,groupby | gold returns EMPTY result (defect or dirty-data; flag for data-quality check) | 0 rows |
| 96 | car_1 | INCORRECT | text_sort | lexicographic sort on TEXT column cars_data.horsepower differs from numeric order | col=horsepower |
| 97 | car_1 | INCORRECT | text_sort | lexicographic sort on TEXT column cars_data.horsepower differs from numeric order | col=horsepower |
| 103 | car_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 35 rows; complaint types=[] |
| 122 | car_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 36 rows; complaint types=[] |
| 123 | car_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 36 rows; complaint types=[] |
| 133 | car_1 | INCORRECT | text_sort | lexicographic sort on TEXT column cars_data.horsepower differs from numeric order | col=horsepower |
| 134 | car_1 | INCORRECT | text_sort | lexicographic sort on TEXT column cars_data.mpg differs from numeric order | col=mpg |
| 161 | car_1 | INCORRECT | text_sort | lexicographic sort on TEXT column cars_data.Horsepower differs from numeric order | col=Horsepower |
| 167 | car_1 | INCORRECT | text_sort | lexicographic sort on TEXT column cars_data.horsepower differs from numeric order | col=horsepower |
| 223 | flight_2 | INCORRECT | groupby | gold returns EMPTY result (defect or dirty-data; flag for data-quality check) | 0 rows |
| 228 | flight_2 | INCORRECT | inner_left | gold returns EMPTY result (defect or dirty-data; flag for data-quality check) | 0 rows |
| 229 | flight_2 | INCORRECT | inner_left | gold returns EMPTY result (defect or dirty-data; flag for data-quality check) | 0 rows |
| 242 | flight_2 | NEEDS_MANUAL | inner_left,agg | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 12 rows; complaint types=['inner_left', 'agg'] |
| 243 | flight_2 | NEEDS_MANUAL | agg | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 12 rows; complaint types=['agg'] |
| 252 | flight_2 | INCORRECT | text_sort | gold returns EMPTY result (defect or dirty-data; flag for data-quality check) | 0 rows |
| 336 | cre_Doc_Template_Mgt | NEEDS_MANUAL | groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['groupby'] |
| 346 | cre_Doc_Template_Mgt | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 347 | cre_Doc_Template_Mgt | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 362 | cre_Doc_Template_Mgt | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 2 rows; complaint types=[] |
| 363 | cre_Doc_Template_Mgt | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 2 rows; complaint types=['inner_left'] |
| 377 | cre_Doc_Template_Mgt | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['inner_left'] |
| 384 | course_teach | PARTIALLY_CORRECT | text_sort | TEXT column teacher.Age but lexical==numeric order on this data (fragile) | col=Age |
| 389 | course_teach | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 7 rows; complaint types=['inner_left'] |
| 392 | course_teach | PARTIALLY_CORRECT | text_sort | TEXT column teacher.Age but lexical==numeric order on this data (fragile) | col=Age |
| 393 | course_teach | PARTIALLY_CORRECT | text_sort | TEXT column teacher.Age but lexical==numeric order on this data (fragile) | col=Age |
| 408 | course_teach | PARTIALLY_CORRECT | distinct,groupby | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 1 rows, all distinct |
| 465 | wta_1 | NEEDS_MANUAL | groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['groupby'] |
| 470 | wta_1 | NEEDS_MANUAL | agg,groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 500 rows; complaint types=['agg', 'groupby'] |
| 471 | wta_1 | NEEDS_MANUAL | inner_left,agg,groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 500 rows; complaint types=['inner_left', 'agg', 'groupby'] |
| 472 | wta_1 | NEEDS_MANUAL | groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 500 rows; complaint types=['groupby'] |
| 473 | wta_1 | NEEDS_MANUAL | inner_left,groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 500 rows; complaint types=['inner_left', 'groupby'] |
| 484 | wta_1 | PARTIALLY_CORRECT | distinct | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 3 rows, all distinct |
| 485 | wta_1 | PARTIALLY_CORRECT | distinct | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 3 rows, all distinct |
| 494 | battle_death | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 8 rows; complaint types=[] |
| 501 | battle_death | NEEDS_MANUAL | agg,groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['agg', 'groupby'] |
| 522 | student_transcripts_tracking | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 523 | student_transcripts_tracking | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 526 | student_transcripts_tracking | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 11 rows; complaint types=['inner_left'] |
| 527 | student_transcripts_tracking | NEEDS_MANUAL | inner_left,agg | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 11 rows; complaint types=['inner_left', 'agg'] |
| 534 | student_transcripts_tracking | PARTIALLY_CORRECT | distinct,groupby | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 3 rows, all distinct |
| 535 | student_transcripts_tracking | PARTIALLY_CORRECT | distinct,groupby | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 3 rows, all distinct |
| 538 | student_transcripts_tracking | PARTIALLY_CORRECT | distinct,agg | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 1 rows, all distinct |
| 549 | student_transcripts_tracking | PARTIALLY_CORRECT | distinct | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 1 rows, all distinct |
| 550 | student_transcripts_tracking | NEEDS_MANUAL | inner_left,setop | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 2 rows; complaint types=['inner_left', 'setop'] |
| 551 | student_transcripts_tracking | NEEDS_MANUAL | inner_left,setop | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 2 rows; complaint types=['inner_left', 'setop'] |
| 579 | student_transcripts_tracking | PARTIALLY_CORRECT | distinct | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 1 rows, all distinct |
| 616 | tvshow | PARTIALLY_CORRECT | text_sort | TEXT column TV_series.Rating but lexical==numeric order on this data (fragile) | col=Rating |
| 617 | tvshow | PARTIALLY_CORRECT | text_sort | TEXT column TV_series.Rating but lexical==numeric order on this data (fragile) | col=Rating |
| 631 | tvshow | INCORRECT | text_sort | lexicographic sort on TEXT column Cartoon.original_air_date differs from numeric order | col=original_air_date |
| 642 | tvshow | NEEDS_MANUAL | agg,groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['agg', 'groupby'] |
| 688 | voter_1 | PARTIALLY_CORRECT | distinct | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 1 rows, all distinct |
| 699 | voter_1 | PARTIALLY_CORRECT | distinct,agg,groupby | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 1 rows, all distinct |
| 705 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 706 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 757 | world_1 | NEEDS_MANUAL | agg | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['agg'] |
| 760 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 258 rows; complaint types=[] |
| 773 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 238 rows; complaint types=[] |
| 774 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 238 rows; complaint types=[] |
| 775 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 58 rows; complaint types=[] |
| 778 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 51 rows; complaint types=[] |
| 817 | world_1 | NEEDS_MANUAL | filter,groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 233 rows; complaint types=['filter', 'groupby'] |
| 818 | world_1 | NEEDS_MANUAL | groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 233 rows; complaint types=['groupby'] |
| 819 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 28 rows; complaint types=[] |
| 820 | world_1 | NEEDS_MANUAL | groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 28 rows; complaint types=['groupby'] |
| 821 | world_1 | NEEDS_MANUAL | filter | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 28 rows; complaint types=['filter'] |
| 822 | world_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 28 rows; complaint types=[] |
| 833 | orchestra | INCORRECT | text_sort | lexicographic sort on TEXT column performance.SHARE differs from numeric order | col=SHARE |
| 868 | network_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 16 rows; complaint types=[] |
| 885 | network_1 | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 14 rows; complaint types=['inner_left'] |
| 886 | network_1 | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 14 rows; complaint types=['inner_left'] |
| 892 | network_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 893 | network_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 896 | network_1 | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 2 rows; complaint types=['inner_left'] |
| 897 | network_1 | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 2 rows; complaint types=['inner_left'] |
| 898 | network_1 | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 2 rows; complaint types=['inner_left'] |
| 907 | network_1 | NEEDS_MANUAL | groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['groupby'] |
| 908 | network_1 | NEEDS_MANUAL | groupby | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['groupby'] |
| 910 | network_1 | INCORRECT | groupby | gold returns EMPTY result (defect or dirty-data; flag for data-quality check) | 0 rows |
| 913 | network_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 914 | network_1 | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=[] |
| 917 | network_1 | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['inner_left'] |
| 918 | network_1 | NEEDS_MANUAL | inner_left | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['inner_left'] |
| 938 | dog_kennels | NEEDS_MANUAL | agg | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 1 rows; complaint types=['agg'] |
| 943 | dog_kennels | PARTIALLY_CORRECT | distinct | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 6 rows, all distinct |
| 944 | dog_kennels | PARTIALLY_CORRECT | distinct,agg | missing DISTINCT but NO duplicates on this data (fragile, not wrong here) | 6 rows, all distinct |
| 946 | dog_kennels | NEEDS_MANUAL | cartesian,agg,filter | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 15 rows; complaint types=['cartesian', 'agg', 'filter'] |
| 961 | dog_kennels | NEEDS_MANUAL |  | needs semantic control query (agg/filter/inner_left/setop/groupby) | gold returned 3 rows; complaint types=[] |
| 962 | dog_kennels | PARTIALLY_CORRECT | text_sort | TEXT column Dogs.age but lexical==numeric order on this data (fragile) | col=age |
| 989 | dog_kennels | PARTIALLY_CORRECT | text_sort | TEXT column Dogs.age but lexical==numeric order on this data (fragile) | col=age |
