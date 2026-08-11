# Control-query adjudication — Train, 100 random (non-empty DB)

| Verdict | Count |
|---|---|
| INCORRECT | 5 |
| PARTIALLY_CORRECT | 23 |
| NEEDS_MANUAL | 72 |
| INCONCLUSIVE | 0 |
| EXEC_ERROR | 0 |

Auto-decided with control query: 28/100

| ID | DB | verdict | transform | gold_n | ctrl_n | reason |
|---|---|---|---|---|---|---|
| 90 | student_assessment | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 203 | bike_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 290 | twitter_1 | PARTIALLY_CORRECT | distinct | 2 | 2 | no duplicates on this data (fragile) |
| 316 | product_catalog | NEEDS_MANUAL |  | 8 | None | no mechanical transform (types=none) |
| 317 | product_catalog | NEEDS_MANUAL |  | 8 | None | no mechanical transform (types=none) |
| 325 | product_catalog | PARTIALLY_CORRECT | text_sort | 1 | 1 | text_sort: gold == control here (fragile) |
| 327 | product_catalog | PARTIALLY_CORRECT | text_sort | 1 | 1 | text_sort: gold == control here (fragile) |
| 330 | product_catalog | INCORRECT | distinct | 5 | 4 | DISTINCT changes result (duplicates present) |
| 333 | product_catalog | NEEDS_MANUAL |  | 6 | None | no mechanical transform (types=none) |
| 435 | flight_1 | NEEDS_MANUAL |  | 5 | None | no mechanical transform (types=none) |
| 439 | flight_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 872 | chinook_1 | NEEDS_MANUAL |  | 2 | None | no mechanical transform (types=none) |
| 1007 | university_basketball | NEEDS_MANUAL |  | 5 | None | no mechanical transform (types=none) |
| 1022 | university_basketball | INCORRECT | text_sort | 4 | 4 | text_sort: gold != control (defect materialises) |
| 1221 | apartment_rentals | NEEDS_MANUAL |  | 15 | None | no mechanical transform (types=none) |
| 1225 | apartment_rentals | NEEDS_MANUAL |  | 15 | None | no mechanical transform (types=none) |
| 1233 | apartment_rentals | NEEDS_MANUAL |  | 15 | None | no mechanical transform (types=none) |
| 1259 | apartment_rentals | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 1297 | soccer_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 1397 | college_2 | PARTIALLY_CORRECT | distinct | 47 | 47 | no duplicates on this data (fragile) |
| 1404 | college_2 | PARTIALLY_CORRECT | distinct | 20 | 20 | no duplicates on this data (fragile) |
| 1407 | college_2 | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 1415 | college_2 | NEEDS_MANUAL |  | 117 | None | no mechanical transform (types=none) |
| 1449 | college_2 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 1514 | insurance_and_eClaims | PARTIALLY_CORRECT | distinct | 3 | 3 | no duplicates on this data (fragile) |
| 1518 | insurance_and_eClaims | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 1525 | insurance_and_eClaims | PARTIALLY_CORRECT | distinct | 5 | 5 | no duplicates on this data (fragile) |
| 1684 | theme_gallery | NEEDS_MANUAL |  | 0 | None | no mechanical transform (types=none) |
| 1687 | theme_gallery | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 1861 | wrestler | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 1907 | school_finance | NEEDS_MANUAL |  | 5 | None | no mechanical transform (types=none) |
| 1909 | school_finance | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 2038 | gas_company | NEEDS_MANUAL |  | 3 | None | no mechanical transform (types=none) |
| 2277 | entrepreneur | PARTIALLY_CORRECT | distinct | 5 | 5 | no duplicates on this data (fragile) |
| 2295 | entrepreneur | NEEDS_MANUAL |  | 6 | None | no mechanical transform (types=none) |
| 2350 | csu_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 2364 | csu_1 | NEEDS_MANUAL |  | 12 | None | no mechanical transform (types=none) |
| 2506 | movie_1 | NEEDS_MANUAL |  | 8 | None | no mechanical transform (types=none) |
| 2520 | movie_1 | NEEDS_MANUAL |  | 6 | None | no mechanical transform (types=none) |
| 2526 | movie_1 | NEEDS_MANUAL |  | 3 | None | no mechanical transform (types=none) |
| 2583 | inn_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 2586 | inn_1 | NEEDS_MANUAL |  | 0 | None | no mechanical transform (types=none) |
| 2852 | customer_deliveries | PARTIALLY_CORRECT | distinct | 4 | 4 | no duplicates on this data (fragile) |
| 2901 | icfp_1 | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 3127 | assets_maintenance | NEEDS_MANUAL |  | 2 | None | no mechanical transform (types=none) |
| 3144 | assets_maintenance | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 3152 | assets_maintenance | PARTIALLY_CORRECT | text_sort | 1 | 1 | text_sort: gold == control here (fragile) |
| 3252 | college_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 3261 | college_1 | NEEDS_MANUAL |  | 22 | None | no mechanical transform (types=none) |
| 3274 | college_1 | NEEDS_MANUAL |  | 14 | None | no mechanical transform (types=none) |
| 3292 | college_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 3356 | sports_competition | NEEDS_MANUAL |  | 15 | None | no mechanical transform (types=none) |
| 3446 | hr_1 | NEEDS_MANUAL |  | 0 | None | no mechanical transform (types=none) |
| 3536 | music_1 | NEEDS_MANUAL |  | 2 | None | no mechanical transform (types=none) |
| 3560 | music_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=['text_sort']) |
| 3638 | baseball_1 | NEEDS_MANUAL |  | 78 | None | no mechanical transform (types=none) |
| 3643 | baseball_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 3660 | baseball_1 | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 3670 | baseball_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 3679 | baseball_1 | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 3690 | baseball_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 3703 | baseball_1 | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 3841 | e_learning | NEEDS_MANUAL |  | 10 | None | no mechanical transform (types=none) |
| 3851 | insurance_policies | PARTIALLY_CORRECT | distinct | 2 | 2 | no duplicates on this data (fragile) |
| 3887 | insurance_policies | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 3950 | hospital_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 3959 | hospital_1 | INCORRECT | text_sort | 1 | 1 | text_sort: gold != control (defect materialises) |
| 3972 | hospital_1 | NEEDS_MANUAL |  | 3 | None | no mechanical transform (types=none) |
| 4061 | student_1 | NEEDS_MANUAL |  | 0 | None | no mechanical transform (types=none) |
| 4065 | student_1 | NEEDS_MANUAL |  | 0 | None | no mechanical transform (types=none) |
| 4070 | student_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 4231 | cre_Doc_Tracking_DB | PARTIALLY_CORRECT | distinct | 3 | 3 | no duplicates on this data (fragile) |
| 4338 | tracking_grants_for_research | NEEDS_MANUAL |  | 10 | None | no mechanical transform (types=none) |
| 4364 | tracking_grants_for_research | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 4392 | tracking_grants_for_research | NEEDS_MANUAL |  | 15 | None | no mechanical transform (types=none) |
| 4481 | network_2 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 4483 | network_2 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 4511 | document_management | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 4522 | document_management | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 4904 | store_product | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 4994 | soccer_2 | NEEDS_MANUAL |  | 4 | None | no mechanical transform (types=none) |
| 5147 | cre_Drama_Workshop_Groups | INCORRECT | distinct | 14 | 10 | DISTINCT changes result (duplicates present) |
| 5169 | cre_Drama_Workshop_Groups | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 5310 | manufactory_1 | NEEDS_MANUAL |  | 6 | None | no mechanical transform (types=none) |
| 5312 | manufactory_1 | NEEDS_MANUAL |  | 6 | None | no mechanical transform (types=none) |
| 5440 | shop_membership | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 5577 | products_gen_characteristics | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 5760 | dorm_1 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 5777 | customer_complaints | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 5813 | customer_complaints | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 6133 | customers_and_addresses | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
| 6214 | roller_coaster | PARTIALLY_CORRECT | text_sort | 1 | 1 | text_sort: gold == control here (fragile) |
| 6303 | city_record | INCORRECT | text_sort | 6 | 6 | text_sort: gold != control (defect materialises) |
| 6477 | scientist_1 | PARTIALLY_CORRECT | distinct | 1 | 1 | no duplicates on this data (fragile) |
| 6498 | scientist_1 | NEEDS_MANUAL |  | 4 | None | no mechanical transform (types=none) |
| 6607 | train_station | NEEDS_MANUAL |  | 2 | None | no mechanical transform (types=none) |
| 6796 | activity_1 | NEEDS_MANUAL |  | 18 | None | no mechanical transform (types=none) |
| 6801 | activity_1 | NEEDS_MANUAL |  | 18 | None | no mechanical transform (types=none) |
| 6803 | activity_1 | NEEDS_MANUAL |  | 30 | None | no mechanical transform (types=none) |
| 6823 | flight_4 | NEEDS_MANUAL |  | 1 | None | no mechanical transform (types=none) |
