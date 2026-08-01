# LLM complaint taxonomy — Train (n=867, model=gpt-5.5)

## By verifiability tier

| Tier | Count | % |
|---|---|---|
| A_DETERMINISTIC | 45 | 5% |
| B_LLM_CONTROL | 518 | 60% |
| C_NOT_ON_DATA | 304 | 35% |

## By primary category

| Category | Tier | Count | % |
|---|---|---|---|
| empty_db | C_NOT_ON_DATA | 304 | 35% |
| wrong_filter | B_LLM_CONTROL | 97 | 11% |
| groupby | B_LLM_CONTROL | 76 | 9% |
| wrong_table_col | B_LLM_CONTROL | 69 | 8% |
| join_semantics | B_LLM_CONTROL | 68 | 8% |
| wrong_projection | B_LLM_CONTROL | 62 | 7% |
| aggregation | B_LLM_CONTROL | 55 | 6% |
| join_condition | B_LLM_CONTROL | 37 | 4% |
| text_sort | A_DETERMINISTIC | 34 | 4% |
| count_distinct | B_LLM_CONTROL | 32 | 4% |
| other | B_LLM_CONTROL | 22 | 3% |
| top_n_tie | A_DETERMINISTIC | 11 | 1% |

## Agreement with regex baseline (primary label)

Agree: 222/563 (39%)

| ID | regex | LLM |
|---|---|---|
| 1 | unclassified | wrong_filter |
| 91 | top_n_tie | wrong_table_col |
| 104 | wrong_table_col | wrong_projection |
| 105 | groupby | wrong_projection |
| 156 | top_n_tie | groupby |
| 157 | top_n_tie | groupby |
| 173 | join_semantics | aggregation |
| 209 | count_distinct | wrong_filter |
| 274 | wrong_filter | wrong_table_col |
| 286 | groupby | join_condition |
| 287 | groupby | join_condition |
| 289 | wrong_projection | join_condition |
| 290 | wrong_filter | join_condition |
| 316 | groupby | wrong_table_col |
| 317 | groupby | wrong_table_col |
| 333 | unclassified | wrong_table_col |
| 431 | wrong_projection | join_semantics |
| 432 | top_n_tie | other |
| 433 | top_n_tie | other |
| 434 | wrong_projection | groupby |
| 435 | wrong_projection | groupby |
| 438 | top_n_tie | wrong_projection |
| 443 | count_distinct | wrong_table_col |
| 457 | count_distinct | wrong_table_col |
| 459 | groupby | wrong_table_col |
| 510 | count_distinct | wrong_filter |
| 511 | count_distinct | wrong_filter |
| 567 | top_n_tie | wrong_filter |
| 607 | top_n_tie | other |
| 633 | wrong_projection | wrong_filter |
| 641 | dup_rows | wrong_filter |
| 778 | wrong_projection | wrong_filter |
| 870 | unclassified | wrong_projection |
| 871 | groupby | wrong_projection |
| 872 | wrong_table_col | wrong_projection |
| 873 | wrong_table_col | wrong_projection |
| 925 | unclassified | wrong_filter |
| 959 | top_n_tie | count_distinct |
| 1007 | unclassified | wrong_filter |
| 1221 | unclassified | wrong_projection |
| 1222 | unclassified | wrong_projection |
| 1259 | unclassified | groupby |
| 1297 | wrong_projection | wrong_table_col |
| 1299 | unclassified | wrong_table_col |
| 1306 | unclassified | aggregation |
| 1307 | unclassified | aggregation |
| 1402 | aggregation | groupby |
| 1449 | top_n_tie | wrong_filter |
| 1450 | top_n_tie | wrong_filter |
| 1455 | wrong_projection | join_semantics |
| 1456 | wrong_projection | join_semantics |
| 1518 | aggregation | wrong_filter |
| 1519 | top_n_tie | wrong_filter |
| 1523 | dup_rows | wrong_table_col |
| 1525 | count_distinct | join_semantics |
| 1611 | groupby | wrong_filter |
| 1684 | wrong_projection | join_semantics |
| 1695 | unclassified | aggregation |
| 1736 | count_distinct | aggregation |
| 1795 | join_semantics | wrong_table_col |
| 1796 | wrong_filter | wrong_table_col |
| 1907 | wrong_projection | join_semantics |
| 1976 | wrong_projection | join_semantics |
| 2003 | aggregation | groupby |
| 2038 | unclassified | wrong_filter |
| 2039 | unclassified | wrong_filter |
| 2153 | aggregation | wrong_projection |
| 2174 | unclassified | join_semantics |
| 2177 | unclassified | wrong_table_col |
| 2198 | unclassified | wrong_projection |
| 2199 | text_sort | wrong_projection |
| 2224 | text_sort | wrong_filter |
| 2225 | text_sort | wrong_filter |
| 2226 | groupby | wrong_filter |
| 2277 | dup_rows | join_semantics |
| 2294 | unclassified | other |
| 2295 | unclassified | wrong_projection |
| 2349 | unclassified | wrong_projection |
| 2350 | wrong_table_col | wrong_projection |
| 2364 | wrong_filter | wrong_table_col |

## Per-item

| ID | DB | primary | all labels | tier | fix_hint |
|---|---|---|---|---|---|
| 1 | department_management | wrong_filter | wrong_filter,count_distinct | B_LLM_CONTROL | Join head to management to restrict to actual department heads older than 56, and count DISTINCT head_IDs if a head can manage multiple departments. |
| 2 | department_management | wrong_filter | wrong_filter,dup_rows | B_LLM_CONTROL | Join/filter head through management to list only heads who lead departments, using DISTINCT on name, born_state, age if needed. |
| 59 | student_assessment | top_n_tie | top_n_tie | A_DETERMINISTIC | Compute course counts per student and return all student_id values whose count equals the minimum count. |
| 69 | student_assessment | top_n_tie | top_n_tie,dup_rows | A_DETERMINISTIC | Return all DISTINCT student_details for students whose registration_date equals the maximum registration_date. |
| 88 | student_assessment | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Query student_course_registrations, not student_course_attendance, with WHERE course_id = 301. |
| 89 | student_assessment | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use Student_Course_Registrations to select student_id where course_id = 301. |
| 90 | student_assessment | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use student_course_registrations for course_id = 301 and order by registration_date DESC to get the most recent registration. |
| 91 | student_assessment | wrong_table_col | wrong_table_col,top_n_tie | B_LLM_CONTROL | Query Student_Course_Registrations for course_id = 301 and return all student_id values with the maximum registration_date. |
| 104 | student_assessment | wrong_projection | wrong_projection,join_condition | B_LLM_CONTROL | Select student details from Students/People, and if the intent is unattended registered courses, anti-join attendance on both student_id and course_id. |
| 105 | student_assessment | wrong_projection | wrong_projection,dup_rows | B_LLM_CONTROL | Select DISTINCT student details from Students/People for students with registrations and no attendance records. |
| 156 | bike_1 | groupby | groupby | B_LLM_CONTROL | Find zip_code values whose AVG(weather.mean_temperature_f) > 60, then return all trip.id rows in those zip codes without grouping away trip ids. |
| 157 | bike_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Return each qualifying zip_code and all trip ids for zip codes whose average mean_temperature_f is above 60, rather than selecting one arbitrary trip id per zip group. |
| 168 | bike_1 | wrong_filter | wrong_filter,interpretation | B_LLM_CONTROL | Clarify the double-negative intent; for days with no Fog or Rain, filter with EVENTS NOT LIKE '%Fog%' AND EVENTS NOT LIKE '%Rain%'. |
| 173 | bike_1 | aggregation | aggregation,join_semantics | B_LLM_CONTROL | Filter status rows with bikes_available > 10 and station.city <> 'San Jose' directly, avoiding AVG and name-based EXCEPT. |
| 180 | bike_1 | groupby | groupby | B_LLM_CONTROL | Group trips by start_station_id and start_station_name, then HAVING COUNT(*) >= 200. |
| 181 | bike_1 | groupby | groupby | B_LLM_CONTROL | Count trips per start_station_id, start_station_name group and return those with COUNT(*) >= 200. |
| 203 | bike_1 | top_n_tie | top_n_tie | A_DETERMINISTIC | Return all dates whose max_temperature_f - min_temperature_f equals the minimum temperature range, along with that range. |
| 209 | bike_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Remove the HAVING count(*) > 100 condition and exclude Palo Alto stations that appear as any end station, preferably by station id. |
| 273 | musical | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter Award with IN ('Bob Fosse', 'Cleavant Derricks') instead of using 'Tony Award'. |
| 274 | musical | wrong_table_col | wrong_table_col,wrong_filter | B_LLM_CONTROL | Use Nominee IN ('Bob Fosse', 'Cleavant Derricks') to identify the relevant awards, then return nominees associated with those awards. |
| 278 | twitter_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Return a per-user identifier and count followers grouped by the followed user, e.g. SELECT f2, COUNT(*) FROM follows GROUP BY f2. |
| 279 | twitter_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Group by the followed-user column f2 and return that user id with COUNT(*), rather than grouping by follower f1. |
| 286 | twitter_1 | join_condition | join_condition | B_LLM_CONTROL | Count followers by joining/grouping on follows.f2 for each user and compare that follower count to Tyler Swift's follower count. |
| 287 | twitter_1 | join_condition | join_condition | B_LLM_CONTROL | Join user_profiles.uid to follows.f2 and GROUP BY the followed user, HAVING COUNT(*) > 1. |
| 289 | twitter_1 | join_condition | join_condition,wrong_projection | B_LLM_CONTROL | Treat Mary and Susan as followers: join their uid to follows.f1 and return the common followed user ids from follows.f2. |
| 290 | twitter_1 | join_condition | join_condition,wrong_projection | B_LLM_CONTROL | Join Mary/Susan to follows.f1 and return the users they follow from follows.f2, optionally with DISTINCT. |
| 297 | twitter_1 | join_semantics | join_semantics | B_LLM_CONTROL | Use a LEFT JOIN from user_profiles to tweets and HAVING COUNT(tweets.id) < 2 to include users with zero tweets. |
| 316 | product_catalog | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Find the most common attribute by grouping on attribute_id, then return catalog entries having that attribute. |
| 317 | product_catalog | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Group Catalog_Contents_Additional_Attributes by attribute_id/name, not attribute_value, to find the attribute with the most entries. |
| 324 | product_catalog | text_sort | text_sort | A_DETERMINISTIC | Order by a numeric cast of height, e.g. ORDER BY CAST(height AS REAL) DESC, before taking the top row. |
| 325 | product_catalog | text_sort | text_sort | A_DETERMINISTIC | Cast height to a numeric type in ORDER BY before selecting the maximum-height catalog entry. |
| 326 | product_catalog | text_sort | text_sort,wrong_filter | A_DETERMINISTIC | Exclude NULL capacity values and order by CAST(capacity AS REAL) ASC to find the numerically smallest capacity. |
| 327 | product_catalog | text_sort | text_sort,wrong_filter | A_DETERMINISTIC | Filter out NULL capacity and sort by numeric CAST(capacity AS REAL) ASC rather than text capacity. |
| 330 | product_catalog | wrong_table_col | wrong_table_col,join_semantics,dup_rows | B_LLM_CONTROL | Query Catalog_Contents directly with WHERE Catalog_Contents.catalog_level_number = 8 and select catalog_entry_name. |
| 331 | product_catalog | wrong_table_col | wrong_table_col,join_semantics,dup_rows | B_LLM_CONTROL | Filter on Catalog_Contents.catalog_level_number = 8 without joining to Additional_Attributes. |
| 332 | product_catalog | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use height > 5 in the second predicate: WHERE length < 3 OR height > 5. |
| 333 | product_catalog | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use length > 5, not width > 5: WHERE length < 3 OR length > 5. |
| 339 | product_catalog | groupby | groupby | B_LLM_CONTROL | Group by the date portion, e.g. DATE(date_of_latest_revision), and HAVING COUNT(*) > 1. |
| 366 | flight_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use salary >= 100000 instead of salary > 100000. |
| 367 | flight_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter with salary >= 100000 to include exactly 100000. |
| 431 | flight_1 | join_semantics | join_semantics | B_LLM_CONTROL | Perform the anti-set difference by employee id/eid, then select the corresponding employee names. |
| 432 | flight_1 | other | other,join_semantics,top_n_tie | B_LLM_CONTROL | Count certificates per aircraft with a LEFT JOIN, order/count for the minimum ascending, and return all aircraft tied for the fewest certifications. |
| 433 | flight_1 | other | other,join_semantics,top_n_tie | B_LLM_CONTROL | Use LEFT JOIN to include zero-certification aircraft, find the minimum certificate count, and return all aircraft with that count. |
| 434 | flight_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Select aircraft name and distance, group by aircraft, and use HAVING COUNT(*) >= 5 rather than ORDER BY as the filter. |
| 435 | flight_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Return T2.name and T2.distance, and filter groups with HAVING COUNT(T1.eid) >= 5. |
| 438 | flight_1 | wrong_projection | wrong_projection,top_n_tie | B_LLM_CONTROL | Select both Employee.salary and Employee.name, and handle ties if multiple employees have the maximum certificate count. |
| 439 | flight_1 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select both T1.salary and T1.name for the employee with the most qualifying certificates. |
| 443 | allergy_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Count distinct allergy names with COUNT(DISTINCT Allergy) from Allergy_Type. |
| 457 | allergy_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Join Has_Allergy to Allergy_Type and count student allergy occurrences grouped by AllergyType. |
| 459 | allergy_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use Has_Allergy joined to Allergy_Type and group by AllergyType to find the least common type among students. |
| 510 | allergy_1 | wrong_filter | wrong_filter,count_distinct | B_LLM_CONTROL | Use WHERE sex='F' AND allergy IN ('Milk','Eggs') and count DISTINCT student ids. |
| 511 | allergy_1 | wrong_filter | wrong_filter,count_distinct | B_LLM_CONTROL | Parenthesize the allergy condition as sex='F' AND allergy IN ('Milk','Eggs') and COUNT(DISTINCT T1.StuID). |
| 565 | store_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Remove WHERE billing_country = 'USA' and group all invoices by billing_state. |
| 567 | store_1 | wrong_filter | wrong_filter,top_n_tie | B_LLM_CONTROL | Count invoices by billing_state across all countries and return all states tied for the maximum count. |
| 607 | store_1 | other | other,join_semantics | B_LLM_CONTROL | Remove LIMIT 1 and use a LEFT self-join from each employee to their reports, grouping by each employee to include zero-report employees. |
| 609 | store_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter on first_name = 'Luca' and last_name = 'Mancini'. |
| 624 | store_1 | join_condition | join_condition | B_LLM_CONTROL | Join albums.id to tracks.album_id, then filter tracks.name = 'Balls to the Wall'. |
| 625 | store_1 | join_condition | join_condition | B_LLM_CONTROL | Use albums.id = tracks.album_id instead of albums.id = tracks.genre_id. |
| 626 | store_1 | join_condition | join_condition | B_LLM_CONTROL | Join albums.id = tracks.album_id and filter albums.title = 'Balls to the Wall'. |
| 627 | store_1 | join_condition | join_condition | B_LLM_CONTROL | Join tracks.album_id to albums.id before selecting track names for the album title. |
| 633 | store_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use AND in the WHERE clause so tracks satisfy both genres.name = 'Rock' and media_types.name = 'MPEG audio file'. |
| 641 | store_1 | wrong_filter | wrong_filter,dup_rows | B_LLM_CONTROL | Filter for first_name = 'Dean' and last_name = 'Peeters', and use SELECT DISTINCT tracks.name if duplicate purchases should not repeat tracks. |
| 682 | customers_card_transactions | join_semantics | join_semantics | B_LLM_CONTROL | Start from Customers and LEFT JOIN Accounts, then count Accounts per customer and order by the count ascending. |
| 683 | customers_card_transactions | join_semantics | join_semantics | B_LLM_CONTROL | Use Customers LEFT JOIN Accounts and count account_id per customer so customers with zero accounts can be returned. |
| 718 | customers_card_transactions | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Count rows from Accounts grouped by Accounts.customer_id, joined to Customers, instead of counting Customers_cards. |
| 719 | customers_card_transactions | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use the Accounts table grouped by customer_id to find the fewest accounts, not the Customers_cards table. |
| 778 | race_track | wrong_filter | wrong_filter | B_LLM_CONTROL | Find year_opened values having at least one track with seating >= 5000 and at least one track with seating <= 4000, e.g. via self-join or GROUP BY with conditional HAVING. |
| 858 | chinook_1 | join_semantics | join_semantics | B_LLM_CONTROL | Filter customers by CustomerId with NOT EXISTS/anti-join for invoices where total > 20, then return their LastName. |
| 859 | chinook_1 | join_semantics | join_semantics | B_LLM_CONTROL | Use a per-customer anti-join or NOT EXISTS on CustomerId for invoices with Total > 20, then project LastName. |
| 870 | chinook_1 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select Employee.FirstName and the employee/support rep id, grouping by the support rep employee id with HAVING COUNT(*) >= 10. |
| 871 | chinook_1 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select T2.FirstName from Employee, not T1.FirstName from Customer, for support reps serving at least 10 customers. |
| 872 | chinook_1 | wrong_projection | wrong_projection,join_semantics | B_LLM_CONTROL | Select Employee.LastName and use a LEFT JOIN from Employee to Customer if employees with zero customers should count as at most 20. |
| 873 | chinook_1 | wrong_projection | wrong_projection,join_semantics | B_LLM_CONTROL | Return T2.LastName from Employee, grouping by employee; use LEFT JOIN to include employees serving 0 customers. |
| 900 | insurance_fnol | count_distinct | count_distinct,wrong_table_col | B_LLM_CONTROL | Join Available_Policies to Customers_Policies and group by policy_type_code with HAVING COUNT(DISTINCT Customer_ID) > 4. |
| 901 | insurance_fnol | count_distinct | count_distinct,wrong_table_col | B_LLM_CONTROL | Join Available_Policies with Customers_Policies and count distinct Customer_ID per policy_type_code, requiring more than 4. |
| 925 | insurance_fnol | wrong_filter | wrong_filter | B_LLM_CONTROL | Use service_name = 'Upgrade a policy' in the second INTERSECT branch instead of 'New policy application'. |
| 959 | medicine_enzyme_interaction | count_distinct | count_distinct,top_n_tie | B_LLM_CONTROL | Return the most-common interaction_type values, including ties, and also compute the total COUNT(DISTINCT interaction_type). |
| 970 | medicine_enzyme_interaction | wrong_filter | wrong_filter | B_LLM_CONTROL | Exclude medicines interacting with enzymes where enzyme.product = 'Heme', not 'Protoporphyrinogen IX'. |
| 971 | medicine_enzyme_interaction | wrong_filter | wrong_filter | B_LLM_CONTROL | Change the enzyme product filter to T3.product = 'Heme' when excluding interacting medicines. |
| 995 | university_basketball | wrong_table_col | wrong_table_col,wrong_filter | B_LLM_CONTROL | Filter on the university school name column, e.g. university.school = 'Clemson', rather than basketball_match.team_name. |
| 1007 | university_basketball | wrong_filter | wrong_filter | B_LLM_CONTROL | Use founded < 1850 OR affiliation = 'Public'. |
| 1022 | university_basketball | text_sort | text_sort | A_DETERMINISTIC | Parse or cast the numeric home-score component of All_Home and order by that numeric value descending. |
| 1023 | university_basketball | text_sort | text_sort | A_DETERMINISTIC | Extract the numeric wins/score from All_Home and sort numerically descending instead of ordering the text value directly. |
| 1221 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Select T2.apt_number, T1.booking_start_date, and T1.booking_end_date. |
| 1222 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Replace the repeated T1.booking_start_date in the third SELECT position with T1.booking_end_date. |
| 1223 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Select T1.booking_start_date and T1.booking_end_date for apartments where apt_type_code = 'Duplex'. |
| 1224 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Use T1.booking_end_date as the second selected column instead of repeating T1.booking_start_date. |
| 1225 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Return T1.booking_start_date and T1.booking_end_date for bookings of apartments with bedroom_count > 2. |
| 1226 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Select booking_start_date and booking_end_date, not booking_start_date twice, for apartments with more than two bedrooms. |
| 1233 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Select T2.guest_first_name, T1.booking_start_date, and T1.booking_end_date. |
| 1234 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Replace the repeated booking_start_date with booking_end_date in the SELECT list. |
| 1235 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Select booking_start_date and booking_end_date for bookings made by guests with gender_code = 'Female'. |
| 1236 | apartment_rentals | wrong_projection | wrong_projection | B_LLM_CONTROL | Return both T1.booking_start_date and T1.booking_end_date for female guests' bookings. |
| 1252 | apartment_rentals | text_sort | text_sort | A_DETERMINISTIC | Order by CAST(room_count AS INTEGER) ASC rather than the CHAR room_count value. |
| 1259 | apartment_rentals | groupby | groupby,aggregation | B_LLM_CONTROL | Group by apt_type_code and aggregate bathroom_count and bedroom_count meaningfully per type while ordering by the summed numeric room_count. |
| 1297 | soccer_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Compute SELECT MAX(height), MIN(height) FROM Player. |
| 1299 | soccer_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Compare T2.dribbling to SELECT MAX(dribbling) FROM Player_Attributes, not MAX(overall_rating). |
| 1306 | soccer_1 | aggregation | aggregation,groupby | B_LLM_CONTROL | Aggregate Player_Attributes per player, such as MAX(overall_rating) per player_api_id, then order players by that value and limit to 3. |
| 1307 | soccer_1 | aggregation | aggregation,groupby | B_LLM_CONTROL | Compute each player's potential, e.g. MAX(potential) per player_api_id, then order players by that aggregate and return the top five names and birthdays. |
| 1397 | college_2 | count_distinct | count_distinct | B_LLM_CONTROL | Group by title and use HAVING COUNT(DISTINCT dept_name) > 1. |
| 1398 | college_2 | count_distinct | count_distinct | B_LLM_CONTROL | Group by course.title and use HAVING COUNT(DISTINCT dept_name) > 1. |
| 1402 | college_2 | groupby | groupby | B_LLM_CONTROL | First identify dept_name values with AVG(salary) above the overall average, then return a single MIN(salary) over instructors in those departments. |
| 1403 | college_2 | count_distinct | count_distinct | B_LLM_CONTROL | Group SECTION by semester and year and count COUNT(DISTINCT course_id). |
| 1404 | college_2 | count_distinct | count_distinct | B_LLM_CONTROL | Use COUNT(DISTINCT course_id) per semester, year instead of COUNT(*). |
| 1407 | college_2 | count_distinct | count_distinct | B_LLM_CONTROL | Group SECTION by semester and year and order by COUNT(DISTINCT course_id) DESC. |
| 1413 | college_2 | count_distinct | count_distinct | B_LLM_CONTROL | Group takes by semester and year and order by COUNT(DISTINCT ID) ascending. |
| 1414 | college_2 | count_distinct | count_distinct | B_LLM_CONTROL | Use COUNT(DISTINCT ID) per semester and year to find the period with the fewest students. |
| 1415 | college_2 | groupby | groupby | B_LLM_CONTROL | Group advisor rows by i_id and require the count of advised History students to equal the total count of History students. |
| 1449 | college_2 | wrong_filter | wrong_filter,groupby | B_LLM_CONTROL | Restrict instructors to department(s) whose department.budget equals MAX(budget), then compute AVG(salary) and COUNT(*). |
| 1450 | college_2 | wrong_filter | wrong_filter,groupby | B_LLM_CONTROL | Filter or group to the highest-budget department before computing COUNT(*) and AVG(instructor.salary). |
| 1455 | college_2 | join_semantics | join_semantics | B_LLM_CONTROL | Start from department and LEFT JOIN student and instructor, grouping by department.dept_name with distinct counts. |
| 1456 | college_2 | join_semantics | join_semantics | B_LLM_CONTROL | Use department as the driver table with LEFT JOINs to student and instructor so departments with zero of either are included. |
| 1514 | insurance_and_eClaims | count_distinct | count_distinct | B_LLM_CONTROL | Group policies by policy_type_code and use HAVING COUNT(DISTINCT customer_id) > 2. |
| 1515 | insurance_and_eClaims | count_distinct | count_distinct | B_LLM_CONTROL | Use COUNT(DISTINCT customer_id) per policy_type_code and keep counts greater than 2. |
| 1518 | insurance_and_eClaims | wrong_filter | wrong_filter,aggregation | B_LLM_CONTROL | Select the latest claims_documents.created_date using MAX(created_date) or ORDER BY created_date DESC, then sum the matching claim amount without duplicate inflation. |
| 1519 | insurance_and_eClaims | wrong_filter | wrong_filter,aggregation | B_LLM_CONTROL | Use ORDER BY created_date DESC or MAX(created_date) for the most recent document and avoid double-counting claim_headers rows. |
| 1523 | insurance_and_eClaims | wrong_table_col | wrong_table_col,dup_rows | B_LLM_CONTROL | Compare claim_headers.amount_claimed to MIN(amount_claimed), then return DISTINCT matching customer_details. |
| 1525 | insurance_and_eClaims | join_semantics | join_semantics | B_LLM_CONTROL | Find customers with no policies by anti-joining on customer_id, then project customer_details. |
| 1571 | customers_and_invoices | join_semantics | join_semantics | B_LLM_CONTROL | LEFT JOIN Customers to Accounts and group by customer_id, first name, and last name to include customers with zero accounts. |
| 1580 | customers_and_invoices | groupby | groupby | B_LLM_CONTROL | Group Financial_transactions by account_id and select account_id with COUNT(*). |
| 1581 | customers_and_invoices | groupby | groupby | B_LLM_CONTROL | Add GROUP BY account_id so the count is computed separately for each account. |
| 1611 | customers_and_invoices | wrong_filter | wrong_filter | B_LLM_CONTROL | Use HAVING COUNT(*) >= 2 for orders with two or more invoices. |
| 1615 | customers_and_invoices | join_semantics | join_semantics | B_LLM_CONTROL | Identify unordered products by anti-joining on product_id, then return product_name. |
| 1622 | customers_and_invoices | count_distinct | count_distinct | B_LLM_CONTROL | Group by product and count COUNT(DISTINCT Orders.customer_id) for customers who ordered each product. |
| 1623 | customers_and_invoices | count_distinct | count_distinct,groupby | B_LLM_CONTROL | Group by product_id/product_name and use COUNT(DISTINCT Orders.customer_id). |
| 1684 | theme_gallery | join_semantics | join_semantics | B_LLM_CONTROL | Find exhibition_id values having both attendance < 100 and attendance > 500, then return their exhibition.theme. |
| 1686 | theme_gallery | count_distinct | count_distinct,join_semantics | B_LLM_CONTROL | Count DISTINCT exhibition.exhibition_id satisfying attendance > 100 or ticket_price < 10, using a LEFT JOIN to keep exhibitions with no records. |
| 1687 | theme_gallery | count_distinct | count_distinct,join_semantics | B_LLM_CONTROL | Use COUNT(DISTINCT exhibition_id) and a LEFT JOIN so each qualifying exhibition is counted once. |
| 1695 | epinions_1 | aggregation | aggregation | B_LLM_CONTROL | Use MAX(rank) from review to get the highest rank. |
| 1736 | riding_club | aggregation | aggregation,groupby | B_LLM_CONTROL | Determine the club with the most coaches by counting coach rows per club before joining to match_result, and aggregate/select gold deterministically for that club. |
| 1795 | small_bank_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Filter customers by custid from savings where savings.balance exceeds the average, then return their checking.balance. |
| 1796 | small_bank_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use custid, not name, to match checking accounts to savings accounts above the average savings balance. |
| 1806 | small_bank_1 | join_semantics | join_semantics,groupby | B_LLM_CONTROL | LEFT JOIN accounts to checking and group by custid and name, counting checking.custid so customers with zero checking accounts remain. |
| 1848 | wrestler | text_sort | text_sort | A_DETERMINISTIC | Order by CAST(Days_held AS INTEGER) DESC instead of sorting the TEXT value lexicographically. |
| 1849 | wrestler | text_sort | text_sort | A_DETERMINISTIC | Find the minimum using numeric ordering, e.g. ORDER BY CAST(Days_held AS INTEGER) ASC. |
| 1850 | wrestler | text_sort | text_sort,top_n_tie | A_DETERMINISTIC | Cast Days_held to a numeric type when finding the minimum, and return all wrestlers tied for that minimum if needed. |
| 1861 | wrestler | top_n_tie | top_n_tie | A_DETERMINISTIC | Return elimination.Time for every wrestler whose Days_held equals the maximum Days_held, rather than LIMIT 1. |
| 1907 | school_finance | join_semantics | join_semantics,groupby | B_LLM_CONTROL | Use school as the base table with LEFT JOINs or pre-aggregates by school_id so schools meeting either budget or endowment condition are retained. |
| 1909 | school_finance | wrong_filter | wrong_filter,count_distinct | B_LLM_CONTROL | Filter endowment.amount < 8.5 and group by school_id with COUNT(DISTINCT donator_id) > 1, then count those schools. |
| 1976 | products_for_hire | join_semantics | join_semantics | B_LLM_CONTROL | Intersect or group on coupon_id to find coupons owned by both good and bad customers, then return their coupon_amount. |
| 1992 | phone_market | wrong_filter | wrong_filter,groupby | B_LLM_CONTROL | Use HAVING SUM(T1.Num_of_stock) > 2000 and group by the phone identifier, e.g. T2.Phone_ID, while selecting T2.Name. |
| 2003 | gas_company | groupby | groupby,wrong_projection | B_LLM_CONTROL | Select the company identifier/name and GROUP BY company to compute MIN, MAX, and AVG(market_value) per company. |
| 2038 | gas_company | wrong_filter | wrong_filter,other | B_LLM_CONTROL | First select the top 3 company_ids by Assets_billion, then return all gas_station location and Representative_Name rows for those companies. |
| 2039 | gas_company | wrong_filter | wrong_filter,other | B_LLM_CONTROL | Apply LIMIT 3 in a subquery over company by Assets_billion, then join to station_company and gas_station to list all stations for those companies. |
| 2130 | cre_Doc_Control_Systems | groupby | groupby | B_LLM_CONTROL | Group Circulation_History by employee_id/employee_name and count that employee’s circulation records, then order by the count descending. |
| 2153 | local_govt_in_alabama | wrong_projection | wrong_projection,aggregation | B_LLM_CONTROL | Return SELECT DISTINCT participant_id FROM participants_in_Events instead of COUNT(DISTINCT participant_id). |
| 2174 | formula_1 | join_semantics | join_semantics | B_LLM_CONTROL | Count drivers from the drivers table whose driverId is not among drivers appearing in results for races with races.year = 2009. |
| 2175 | formula_1 | join_semantics | join_semantics | B_LLM_CONTROL | Compute all drivers minus drivers who have results in 2009 races, then count the remaining distinct driverIds. |
| 2177 | formula_1 | wrong_table_col | wrong_table_col,dup_rows | B_LLM_CONTROL | Filter on drivers.surname = 'Lewis' and use DISTINCT on race name/year if duplicate race rows can occur. |
| 2186 | formula_1 | wrong_filter | wrong_filter,other | B_LLM_CONTROL | Remove the T2.wins = 1 filter or use T2.wins > 0, and ensure distinctness is by driver rather than collapsing unrelated drivers with the same forename. |
| 2198 | formula_1 | wrong_projection | wrong_projection,wrong_filter | B_LLM_CONTROL | Select only DISTINCT driverid, and restrict the outer pitstops rows to raceid = 841 before comparing durations. |
| 2199 | formula_1 | wrong_projection | wrong_projection,text_sort,aggregation | B_LLM_CONTROL | Select driverid and duration, compare numeric duration such as milliseconds rather than TEXT duration, and use the intended reference stop/driver instead of MIN(duration) if required. |
| 2224 | formula_1 | wrong_filter | wrong_filter,groupby,text_sort | B_LLM_CONTROL | Use T1.year > 2004, group at the proper race name/year grain, and cast fastestLapSpeed to numeric before applying MAX. |
| 2225 | formula_1 | wrong_filter | wrong_filter,groupby,text_sort | B_LLM_CONTROL | Filter with T1.year > 2004, group by race name and year or raceId, and compute MAX(CAST(T2.fastestLapSpeed AS numeric)). |
| 2226 | formula_1 | wrong_filter | wrong_filter,groupby | B_LLM_CONTROL | Use WHERE T1.year > 2004 and group by race name plus year, then order the grouped results by year. |
| 2227 | formula_1 | wrong_filter | wrong_filter,groupby | B_LLM_CONTROL | Filter races with T1.year > 2004 and group by each race event, e.g. raceId or name plus year, before ordering by year. |
| 2233 | formula_1 | top_n_tie | top_n_tie | A_DETERMINISTIC | Count races per driver and return every driver whose count equals the maximum count, rather than using LIMIT 1. |
| 2244 | machine_repair | top_n_tie | top_n_tie | A_DETERMINISTIC | Return Starting_Year for all technicians with Age = (SELECT MAX(Age) FROM technician). |
| 2259 | machine_repair | count_distinct | count_distinct,groupby | B_LLM_CONTROL | Group by technician_ID/name and use COUNT(DISTINCT T1.Machine_ID) for the number of machines assigned. |
| 2277 | entrepreneur | join_semantics | join_semantics,wrong_filter,dup_rows | B_LLM_CONTROL | Use an anti-join or NOT EXISTS to exclude any entrepreneur with Investor = 'Rachel Elnaugh', and return DISTINCT names. |
| 2294 | entrepreneur | other | other | B_LLM_CONTROL | Order by T1.Money_Requested DESC. |
| 2295 | entrepreneur | wrong_projection | wrong_projection,other | B_LLM_CONTROL | Select T2.Name and T1.Investor, and order by T1.Money_Requested DESC. |
| 2349 | csu_1 | wrong_projection | wrong_projection,wrong_table_col | B_LLM_CONTROL | Join degrees.campus to Campuses.id and select the campus name while summing degrees by campus. |
| 2350 | csu_1 | wrong_projection | wrong_projection,wrong_table_col | B_LLM_CONTROL | Join degrees to Campuses and return the campus name, not the campus id from degrees. |
| 2357 | csu_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Remove the campus column and GROUP BY, and return SUM(T2.degrees) for years 1998 through 2002 across all campuses. |
| 2358 | csu_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Aggregate a single overall SUM(degrees) for 1998–2002 without grouping by campus. |
| 2364 | csu_1 | wrong_table_col | wrong_table_col,wrong_filter | B_LLM_CONTROL | Filter on Campuses.Year = 1956, not enrollments.year, along with FTE_AY > 200 and TotalEnrollment_AY > 400. |
| 2379 | csu_1 | wrong_table_col | wrong_table_col,wrong_filter | B_LLM_CONTROL | Apply the year condition to faculty.year = 2004, while keeping faculty between 600 and 1000. |
| 2380 | csu_1 | wrong_table_col | wrong_table_col,wrong_filter | B_LLM_CONTROL | Use T2.year = 2004 from the faculty table instead of T1.year from campuses. |
| 2388 | csu_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Query the degrees table and sum degrees for San Francisco State University where degrees.year = 2004. |
| 2407 | candidate_poll | text_sort | text_sort | A_DETERMINISTIC | Parse date_of_birth from DD.MM.YYYY into a real date or YYYY-MM-DD expression and order chronologically ascending for oldest to youngest. |
| 2417 | candidate_poll | groupby | groupby,wrong_projection | B_LLM_CONTROL | Find the minimum oppose_rate per sex, then join/filter candidates whose oppose_rate equals that per-sex minimum and return their names. |
| 2420 | candidate_poll | groupby | groupby,aggregation | B_LLM_CONTROL | Do not group by sex; order candidates by T2.unsure_rate DESC or filter to MAX(unsure_rate), then return that candidate’s sex. |
| 2461 | movie_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use WHERE T2.ratingDate IS NULL instead of comparing ratingDate to the string 'null'. |
| 2462 | movie_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use ratingDate IS NULL to find ratings without a date. |
| 2463 | movie_1 | groupby | groupby,join_semantics | B_LLM_CONTROL | For movies in the minimum year, group by movie id/title to compute each movie’s average rating, using a LEFT JOIN if unrated oldest movies should be retained. |
| 2464 | movie_1 | groupby | groupby,join_semantics | B_LLM_CONTROL | Group ratings by the oldest movie’s mID/title instead of averaging all oldest-year movies together, and use LEFT JOIN if no-rating movies must appear. |
| 2499 | movie_1 | top_n_tie | top_n_tie | A_DETERMINISTIC | Compute average stars per movie and return all movies whose average equals the global lowest average, not just LIMIT 1. |
| 2500 | movie_1 | top_n_tie | top_n_tie | A_DETERMINISTIC | Filter grouped movie averages to the minimum average value so all tied lowest-rated movies are returned. |
| 2503 | movie_1 | groupby | groupby,wrong_filter | B_LLM_CONTROL | For each non-NULL director, return the movie row(s) whose stars equal that director’s maximum rating, using director IS NOT NULL. |
| 2505 | movie_1 | groupby | groupby | B_LLM_CONTROL | Compute MIN(stars) per Rating.rID in a subquery/window and join/filter Rating rows where stars equals that minimum, then return the matching movie title, reviewer id, and stars. |
| 2506 | movie_1 | groupby | groupby | B_LLM_CONTROL | Find the per-rID MIN(stars) and return Rating/Movie rows whose stars equal that minimum, so title and rating come from the minimum-rated movie(s). |
| 2507 | movie_1 | groupby | groupby | B_LLM_CONTROL | Compute the minimum Rating.stars per Movie.director and return the movie title and stars only for rows matching that per-director minimum. |
| 2508 | movie_1 | groupby | groupby | B_LLM_CONTROL | For each director, filter joined Rating/Movie rows to those with stars equal to that director’s minimum rating instead of selecting arbitrary grouped columns. |
| 2517 | movie_1 | join_semantics | join_semantics,wrong_table_col | B_LLM_CONTROL | Start from all Movie.mID values and exclude mIDs reviewed by reviewer name 'Brittany Harris', so unrated movies are included. |
| 2518 | movie_1 | join_semantics | join_semantics,wrong_table_col,wrong_filter | B_LLM_CONTROL | Select all Movie.mID values and anti-join/subtract those reviewed by the specified Brittany/Britanny Harris name, rather than starting from Rating. |
| 2520 | movie_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use GROUP BY mID HAVING COUNT(*) > 3 before computing AVG(stars). |
| 2524 | movie_1 | join_semantics | join_semantics,wrong_filter,dup_rows | B_LLM_CONTROL | Select distinct reviewers whose rID has no Rating row with stars = 4, using NOT EXISTS/anti-join or GROUP BY HAVING. |
| 2525 | movie_1 | join_semantics | join_semantics | B_LLM_CONTROL | Use Movie as the base table with a LEFT JOIN/EXISTS condition, or UNION post-2000 movies with movies reviewed by Brittany Harris. |
| 2526 | movie_1 | join_semantics | join_semantics | B_LLM_CONTROL | Include all Movie rows made after 2000 regardless of ratings, plus movies reviewed by Brittany Harris, using LEFT JOIN/EXISTS or UNION. |
| 2530 | movie_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Return distinct reviewer names from ratings where stars IN (3, 4), rather than intersecting 3-star and 4-star reviewers. |
| 2532 | movie_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Return distinct movie titles with Rating.stars IN (3, 4), or use UNION instead of INTERSECT. |
| 2579 | inn_1 | aggregation | aggregation | B_LLM_CONTROL | Use SUM(kids) over Reservations filtered to FirstName='ROY' and LastName='SWEAZY' to return the total number of kids. |
| 2580 | inn_1 | aggregation | aggregation,wrong_filter | B_LLM_CONTROL | Filter for FirstName='ROY' and LastName='SWEAZ' as stated, and return SUM(kids) across that person’s reservations. |
| 2583 | inn_1 | groupby | groupby | B_LLM_CONTROL | Remove GROUP BY and order all joined Reservations/Rooms rows by Rate DESC, returning the roomName, Rate, CheckIn, and CheckOut for the highest-rate reservation. |
| 2584 | inn_1 | groupby | groupby | B_LLM_CONTROL | Do not group by room; sort all Reservations joined to Rooms by Rate DESC and return the row with the maximum rate and its dates. |
| 2586 | inn_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Compare CheckIn to the stored date format, e.g. '23-OCT-10', along with FirstName='CONRAD' and LastName='SELBIG'. |
| 2588 | inn_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use the stored CheckIn literal format such as '21-SEP-10' for DAMIEN TRACHSEL, then select Kids. |
| 2687 | party_host | text_sort | text_sort,top_n_tie | A_DETERMINISTIC | Order by CAST(Age AS INTEGER) DESC or filter to the numeric maximum age, and return all hosts tied for the oldest age. |
| 2688 | party_host | text_sort | text_sort,top_n_tie | A_DETERMINISTIC | Compare Age numerically by casting it to an integer, and avoid dropping tied highest-age hosts if ties should be returned. |
| 2731 | storm_record | top_n_tie | top_n_tie | A_DETERMINISTIC | Find the maximum storm.Number_Deaths, then return all region_name values for region/storm rows whose storm has that maximum death count. |
| 2732 | storm_record | top_n_tie | top_n_tie,dup_rows | A_DETERMINISTIC | Filter to storm(s) with the maximum Number_Deaths and return all affected regions, using DISTINCT if needed. |
| 2844 | customer_deliveries | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Aggregate product order counts from Actual_Order_Products joined to products, not regular_order_products templates. |
| 2852 | customer_deliveries | join_semantics | join_semantics,groupby,dup_rows | B_LLM_CONTROL | Group or anti-join at the state_province_county level to return distinct states for which no address is an employee address. |
| 2857 | customer_deliveries | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Join Delivery_Routes through Delivery_Route_Locations to Order_Deliveries and count actual deliveries per route. |
| 2901 | icfp_1 | count_distinct | count_distinct | B_LLM_CONTROL | Group by inst.country and order by COUNT(DISTINCT authorship.paperID) to count unique papers per country. |
| 2903 | icfp_1 | count_distinct | count_distinct,groupby | B_LLM_CONTROL | Group by institution id/name and count COUNT(DISTINCT authorship.paperID) per organization before selecting the maximum. |
| 2904 | icfp_1 | count_distinct | count_distinct | B_LLM_CONTROL | Count distinct paper IDs per institution, e.g. COUNT(DISTINCT t2.paperID), rather than authorship rows. |
| 2913 | icfp_1 | aggregation | aggregation,groupby | B_LLM_CONTROL | Group authorship by paperID, count authors per paper, find the maximum count, and return the corresponding paper title(s). |
| 2914 | icfp_1 | aggregation | aggregation,groupby | B_LLM_CONTROL | Use GROUP BY paperID with COUNT(authID) or COUNT(DISTINCT authID) to find paper(s) with the most authors, then return their titles. |
| 3023 | loan_1 | groupby | groupby | B_LLM_CONTROL | Group loans by customer ID, not only cust_name, and order each customer’s row by SUM(loan.amount). |
| 3024 | loan_1 | groupby | groupby | B_LLM_CONTROL | Aggregate by cust_id with cust_name and order by that customer’s total loan amount, avoiding merging duplicate names. |
| 3035 | loan_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Return one row per customer from Utah or Texas, selecting a customer identifier/name with SUM(acc_bal) and grouping by that customer. |
| 3036 | loan_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Select each customer and SUM(acc_bal) for Utah/Texas customers, with GROUP BY customer id/name instead of one grand total. |
| 3054 | loan_1 | groupby | groupby | B_LLM_CONTROL | Group loans by cust_id and select the corresponding cust_name, ordering by SUM(amount) DESC to find the greatest total. |
| 3063 | loan_1 | groupby | groupby | B_LLM_CONTROL | Group by customer ID and count that customer’s loans, then return names for customers with COUNT(*) > 1. |
| 3064 | loan_1 | groupby | groupby | B_LLM_CONTROL | Use GROUP BY cust_id, not cust_name alone, and HAVING COUNT(*) > 1 before returning the customer names. |
| 3065 | loan_1 | wrong_projection | wrong_projection,groupby | B_LLM_CONTROL | Select cust_name and acc_bal, group by customer ID, and keep customers whose SUM(loan.amount) > 5000. |
| 3066 | loan_1 | wrong_projection | wrong_projection,groupby | B_LLM_CONTROL | Return customer name and acc_bal, not acc_type, and aggregate loan totals by customer ID before applying HAVING SUM(amount) > 5000. |
| 3125 | behavior_monitoring | join_semantics | join_semantics,join_condition | B_LLM_CONTROL | Anti-join Teachers to Detention by teacher_id, then select the last_name of teachers with no matching detention rows. |
| 3127 | assets_maintenance | join_semantics | join_semantics | B_LLM_CONTROL | Count parts and fault logs per asset using LEFT JOIN to Fault_Log so assets with 0 or 1 fault logs are included. |
| 3132 | assets_maintenance | join_condition | join_condition | B_LLM_CONTROL | Join Maintenance_Engineers to Engineer_Visits with ON T1.engineer_id = T2.engineer_id before counting visits. |
| 3140 | assets_maintenance | aggregation | aggregation,wrong_projection | B_LLM_CONTROL | Return COUNT(DISTINCT fault_status) from Fault_Log_Parts instead of listing the distinct statuses. |
| 3144 | assets_maintenance | groupby | groupby | B_LLM_CONTROL | Group skills by Part_Faults.part_fault_id, find the fault with the highest skill count, then return its part_id and part_name. |
| 3145 | assets_maintenance | wrong_table_col | wrong_table_col,join_semantics | B_LLM_CONTROL | Count actual fault occurrences from Fault_Log_Parts joined via Part_Faults, using LEFT JOIN from Parts to include parts with zero faults. |
| 3152 | assets_maintenance | text_sort | text_sort,top_n_tie | A_DETERMINISTIC | Cast chargeable_amount to a numeric type for ordering/comparison and return all parts tied for the minimum amount. |
| 3154 | assets_maintenance | wrong_table_col | wrong_table_col,wrong_projection | B_LLM_CONTROL | Use the actual company type column/table in the schema and select the company type description for the company with the latest contract_end_date. |
| 3191 | college_1 | wrong_projection | wrong_projection,aggregation | B_LLM_CONTROL | Select DISTINCT dept_address from department where school_code = 'BUS' instead of counting them. |
| 3252 | college_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Filter by the professor’s department by joining CLASS to PROFESSOR to DEPARTMENT, then count enrollments. |
| 3253 | college_1 | wrong_table_col | wrong_table_col,count_distinct | B_LLM_CONTROL | Join CLASS to PROFESSOR to DEPARTMENT for Accounting professors and COUNT(DISTINCT enroll.stu_num). |
| 3258 | college_1 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select CLASS.crs_code, ideally DISTINCT, for rows where class_room = 'KLR209'. |
| 3259 | college_1 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select CLASS.crs_code, ideally DISTINCT, for classes located in room KLR209. |
| 3261 | college_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Join EMPLOYEE to PROFESSOR on emp_num to identify professors, then select emp_fname ordered by emp_dob. |
| 3274 | college_1 | join_semantics | join_semantics | B_LLM_CONTROL | Find non-teaching professors by anti-joining or EXCEPTing on emp_num, then project emp_fname. |
| 3275 | college_1 | join_semantics | join_semantics | B_LLM_CONTROL | Compare professors by EMP_NUM with NOT EXISTS or EXCEPT, then return their first names. |
| 3276 | college_1 | join_semantics | join_semantics | B_LLM_CONTROL | Use an anti-join on emp_num for History professors with no CLASS rows, then select emp_fname. |
| 3292 | college_1 | join_semantics | join_semantics | B_LLM_CONTROL | Match professors by EMP_NUM, e.g. intersect EMP_NUMs or self-join CLASS for CIS-220 and QM-261, then return emp_fname. |
| 3324 | college_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Filter by the department of the course being taught via CLASS -> COURSE -> DEPARTMENT, not PROFESSOR.dept_code. |
| 3356 | sports_competition | wrong_projection | wrong_projection | B_LLM_CONTROL | Select club.name and player.name instead of player.Player_id. |
| 3357 | sports_competition | wrong_projection | wrong_projection,join_semantics | B_LLM_CONTROL | Select player.name and use a LEFT JOIN from club to player if clubs without players must be included. |
| 3364 | sports_competition | groupby | groupby,wrong_filter | B_LLM_CONTROL | Group by player.Position and use HAVING AVG(Points) > 20. |
| 3365 | sports_competition | groupby | groupby,wrong_filter | B_LLM_CONTROL | Group by Position and filter with HAVING AVG(Points) > 20. |
| 3375 | sports_competition | join_semantics | join_semantics | B_LLM_CONTROL | Use the intended set operation for the two point conditions, such as UNION for positions from either group rather than INTERSECT. |
| 3412 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use WHERE department_id IS NULL instead of comparing department_id to the string 'null'. |
| 3413 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use WHERE department_id IS NULL to find employees without a department number. |
| 3424 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use commission_pct IS NOT NULL and parentheses so salary BETWEEN 8000 AND 12000 applies with the intended commission/dept condition. |
| 3425 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use commission_pct IS NOT NULL and parenthesize the OR condition so only salaries between 8000 and 12000 are returned. |
| 3426 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use WHERE commission_pct IS NULL instead of commission_pct = 'null'. |
| 3427 | hr_1 | wrong_filter | wrong_filter,wrong_projection | B_LLM_CONTROL | Use commission_pct IS NULL, and concatenate first_name and last_name if a single full-name column is required. |
| 3443 | hr_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Filter on max_salary > 9000, or actual employee salaries if intended, rather than min_salary > 9000. |
| 3446 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use commission_pct IS NULL along with salary BETWEEN 7000 AND 12000 and department_id = 50. |
| 3447 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use commission_pct IS NULL to match null commissions. |
| 3453 | hr_1 | wrong_table_col | wrong_table_col,groupby | B_LLM_CONTROL | Use departments.manager_id to identify each department’s manager and count that manager’s employee reports, then return qualifying department_id values. |
| 3454 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use commission_pct IS NOT NULL before grouping by department_id and averaging salary. |
| 3455 | hr_1 | groupby | groupby,wrong_filter | B_LLM_CONTROL | Return a single AVG(salary) for employees where commission_pct IS NOT NULL, without grouping by department_id. |
| 3466 | hr_1 | wrong_table_col | wrong_table_col,wrong_projection | B_LLM_CONTROL | Join job_history to jobs and employees, filter employees.salary >= 12000, and select jobs.*. |
| 3475 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Correlate the minimum salary by department_id so each employee’s salary is compared to the minimum in their own department. |
| 3482 | hr_1 | join_condition | join_condition | B_LLM_CONTROL | Join employees directly to departments on employees.employee_id = departments.manager_id to find employees who manage a department. |
| 3483 | hr_1 | join_condition | join_condition,wrong_projection,dup_rows | B_LLM_CONTROL | Select employees.* where employee_id appears as a departments.manager_id, avoiding the department_id join and duplicate department rows. |
| 3498 | hr_1 | wrong_table_col | wrong_table_col,wrong_projection | B_LLM_CONTROL | Select employee_id from employees whose department_id is not among departments containing employees with manager_id BETWEEN 100 AND 200. |
| 3501 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use department_id IN (SELECT DISTINCT department_id FROM employees WHERE first_name = 'Clara') to handle multiple Claras/departments. |
| 3503 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use department_id IN (SELECT DISTINCT department_id FROM employees WHERE first_name = 'Clara') and keep the filter excluding Clara. |
| 3504 | hr_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Select employees whose department_id is in departments having an employee with first_name LIKE '%T%' OR last_name LIKE '%T%'. |
| 3508 | hr_1 | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Compare salary against the appropriate aggregate over employees whose job title is MK_MAN, joining jobs and using the judge-requested MAX salary for 'smaller than any'. |
| 3510 | hr_1 | wrong_projection | wrong_projection,aggregation | B_LLM_CONTROL | Join jobs to return job_title instead of job_id, and use the judge-requested MIN salary comparison for 'more than any'. |
| 3513 | hr_1 | groupby | groupby | B_LLM_CONTROL | Use HAVING COUNT(*) > 2, not >= 2, after grouping employees by department_id. |
| 3516 | hr_1 | groupby | groupby | B_LLM_CONTROL | Return employee rows whose salary equals the MAX(salary) for their department, including ties, instead of selecting arbitrary non-grouped columns. |
| 3517 | hr_1 | groupby | groupby | B_LLM_CONTROL | Filter employees to salary = department maximum per department and return their department_id, names, and salary, including ties. |
| 3532 | music_1 | text_sort | text_sort,wrong_table_col | A_DETERMINISTIC | Join song to files and compare duration after parsing it as a real time/seconds value, then return the song/file id for the longest song. |
| 3533 | music_1 | text_sort | text_sort,wrong_table_col | A_DETERMINISTIC | Restrict to rows in song joined to files and order/compare parsed numeric durations rather than the text duration string. |
| 3536 | music_1 | wrong_table_col | wrong_table_col,wrong_projection | B_LLM_CONTROL | Join song to files on f_id, filter files.formats = 'mp3', and select the song identifier column requested by the schema/judge. |
| 3543 | music_1 | top_n_tie | top_n_tie,text_sort | A_DETERMINISTIC | Parse duration to seconds and return all artist_name values for songs whose duration equals the minimum duration. |
| 3551 | music_1 | aggregation | aggregation,groupby | B_LLM_CONTROL | For female artists, count songs per artist with GROUP BY artist, then take AVG of those per-artist counts. |
| 3560 | music_1 | aggregation | aggregation | B_LLM_CONTROL | Convert files.duration from text mm:ss to seconds before applying AVG for mp3 songs with resolution < 800. |
| 3569 | music_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Join song to files on f_id and count songs grouped by files.formats, rather than counting all files. |
| 3588 | music_1 | wrong_projection | wrong_projection,groupby | B_LLM_CONTROL | Select languages, group by languages, order by COUNT(*) descending for songs with resolution > 500, and return the most frequent language. |
| 3589 | music_1 | groupby | groupby,aggregation | B_LLM_CONTROL | For each languages value, count songs per artist_name with resolution > 500 and choose the artist(s) with the maximum count within that language. |
| 3603 | music_1 | text_sort | text_sort | A_DETERMINISTIC | Convert duration text to seconds before taking MAX(duration) per language; keep MAX(resolution), GROUP BY languages, and ORDER BY languages. |
| 3604 | music_1 | text_sort | text_sort | A_DETERMINISTIC | Convert duration text to seconds before taking MIN(duration) per genre; keep MIN(rating), GROUP BY genre_is, and ORDER BY genre_is. |
| 3605 | music_1 | aggregation | aggregation,text_sort | B_LLM_CONTROL | Identify the actual song row per genre satisfying the requested shortest/lowest-rated criterion, and parse duration text before comparing durations. |
| 3633 | baseball_1 | join_condition | join_condition,aggregation | B_LLM_CONTROL | Join salary to team with the correct team key and align years, e.g. salary.team_id = team.team_id and salary.year = team.year, before averaging salary. |
| 3638 | baseball_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Add WHERE inducted = 'Y' and then count Hall of Fame entrants grouped by yearid. |
| 3639 | baseball_1 | wrong_filter | wrong_filter,count_distinct | B_LLM_CONTROL | Filter hall_of_fame to inducted = 'Y' and count inducted players per year, preferably COUNT(DISTINCT player_id). |
| 3642 | baseball_1 | join_condition | join_condition,groupby | B_LLM_CONTROL | Join/filter team for the 2014 season as well as team_id so the selected rank belongs to the 2014 team. |
| 3643 | baseball_1 | join_condition | join_condition,aggregation | B_LLM_CONTROL | Join home_game to team on team_id and year = 2014, and compute the judge-requested attendance rate metric before choosing the highest average. |
| 3660 | baseball_1 | join_condition | join_condition,aggregation,groupby | B_LLM_CONTROL | Join team and salary on both team_id and year to avoid cross-season duplication before computing AVG(salary), and select a deterministic team name/id. |
| 3662 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Add ON player.player_id = player_award.player_id in both 1960 and 1961 subqueries before intersecting players. |
| 3663 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Join player to player_award on player_id and return players with awards in both 1960 and 1961. |
| 3668 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Use the correct team identifier/year-safe lookup for Boston Red Stockings when matching postseason.team_id_loser, avoiding duplicate team-year joins. |
| 3669 | baseball_1 | aggregation | aggregation,join_condition | B_LLM_CONTROL | Sum postseason losses for Boston Red Stockings in 2009 and use the correct non-duplicating team join/key. |
| 3670 | baseball_1 | aggregation | aggregation,join_condition | B_LLM_CONTROL | Aggregate postseason game wins with SUM(wins) for 2008 and join to the proper 2008 team row to get the name. |
| 3671 | baseball_1 | join_condition | join_condition,aggregation | B_LLM_CONTROL | Join postseason winners to the team table with the 2008 year constraint and use SUM(wins) if counting game wins. |
| 3672 | baseball_1 | aggregation | aggregation,wrong_filter | B_LLM_CONTROL | For each year, sum games won by Boston Red Stockings as wins when they are team_id_winner and losses when they are team_id_loser. |
| 3673 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Align postseason rows with the matching team year when joining to Boston Red Stockings so yearly win counts are not duplicated. |
| 3674 | baseball_1 | aggregation | aggregation | B_LLM_CONTROL | Sum wins + losses + ties over postseason rows where Boston Red Stockings was either winner or loser, instead of counting series rows. |
| 3675 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Use the correct non-duplicating team key/year-safe lookup when matching Boston Red Stockings as winner or loser in postseason. |
| 3679 | baseball_1 | join_condition | join_condition,aggregation | B_LLM_CONTROL | Constrain the team match to the correct 2010 team row or proper franchise/team mapping before summing 2010 salaries. |
| 3680 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Constrain the team table to year 2000 and use the proper team identifier mapping before counting salary/player rows. |
| 3686 | baseball_1 | wrong_filter | wrong_filter,count_distinct | B_LLM_CONTROL | Filter hall_of_fame to inducted = 'Y' before grouping by yearid and counting entrants, preferably distinct player_id. |
| 3687 | baseball_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Add WHERE inducted = 'Y' before grouping by yearid and ordering by the entrant count ascending. |
| 3690 | baseball_1 | aggregation | aggregation | B_LLM_CONTROL | Use SUM(T1.games) for home_game rows in 1907 at park_name = 'Columbia Park' instead of COUNT(*). |
| 3691 | baseball_1 | aggregation | aggregation | B_LLM_CONTROL | Sum home_game.games for Columbia Park in 1907 rather than counting home_game rows. |
| 3692 | baseball_1 | aggregation | aggregation | B_LLM_CONTROL | Use SUM(T1.games) for 2000 home_game rows whose park city is Atlanta, not COUNT(*). |
| 3693 | baseball_1 | aggregation | aggregation | B_LLM_CONTROL | Sum home_game.games for parks in Atlanta in 2000 instead of counting records. |
| 3694 | baseball_1 | join_condition | join_condition,aggregation | B_LLM_CONTROL | Join home_game.team_id to team.team_id and align the year, then sum home_game.attendance for Boston Red Stockings from 2000 to 2010. |
| 3695 | baseball_1 | wrong_table_col | wrong_table_col,join_condition | B_LLM_CONTROL | Sum home_game.games rather than attendance, and join home_game.team_id to team.team_id with the proper year alignment. |
| 3698 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Join salary.team_id to team.team_id and include salary.year = team.year in both 2005 and 2007 branches before intersecting players. |
| 3699 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Use salary.team_id = team.team_id and salary.year = team.year when filtering Washington Nationals salaries for both years. |
| 3700 | baseball_1 | join_condition | join_condition | B_LLM_CONTROL | Join home_game.team_id to team.team_id instead of team.team_id_br when summing games for Boston Red Stockings. |
| 3701 | baseball_1 | join_condition | join_condition,wrong_table_col | B_LLM_CONTROL | Join home_game/team on team_id with year alignment, and use the appropriate total-games column such as team.g if total rather than home-only games are requested. |
| 3702 | baseball_1 | aggregation | aggregation,groupby,join_condition | B_LLM_CONTROL | Aggregate attendance per team for 1980, join home_game.team_id to team.team_id with matching year, then choose the team with the minimum total. |
| 3703 | baseball_1 | aggregation | aggregation,groupby,join_condition | B_LLM_CONTROL | Group by team for 1980 and compare total attendance per team, using the correct team join key and year condition. |
| 3710 | baseball_1 | aggregation | aggregation,groupby | B_LLM_CONTROL | Group 2008 home_game rows by park_id and order by SUM(attendance) DESC to find the park with the highest total attendance. |
| 3711 | baseball_1 | aggregation | aggregation,groupby | B_LLM_CONTROL | Aggregate attendance by park for 2008 with SUM(attendance), then rank parks by that total. |
| 3718 | mountain_photos | wrong_projection | wrong_projection,wrong_filter | B_LLM_CONTROL | Select photos.id and photos.name for photos linked to mountains, and remove the unrelated mountain.height > 4000 filter. |
| 3720 | mountain_photos | count_distinct | count_distinct,top_n_tie | B_LLM_CONTROL | Count COUNT(DISTINCT photos.mountain_id) per camera_lens and return all camera names tied for the maximum count. |
| 3721 | mountain_photos | wrong_projection | wrong_projection | B_LLM_CONTROL | Select photos.name, not camera_lens.name, for photos whose lens brand is Sigma or Olympus. |
| 3756 | program_share | join_semantics | join_semantics,wrong_projection | B_LLM_CONTROL | Identify program_id values that broadcast in both Morning and Night, then return the owners of those same programs. |
| 3792 | e_learning | aggregation | aggregation | B_LLM_CONTROL | Use MAX(date_of_latest_logon) over students with family_name in ('Jaskolski','Langosh'). |
| 3802 | e_learning | count_distinct | count_distinct | B_LLM_CONTROL | Join Student_Tests_Taken to Student_Course_Enrolment by registration_id and count DISTINCT student_id per test_result. |
| 3823 | e_learning | groupby | groupby | B_LLM_CONTROL | Group enrollments by Courses.course_id, selecting course_name, and keep groups with COUNT(*) = 1. |
| 3824 | e_learning | groupby | groupby | B_LLM_CONTROL | Group by the course primary key course_id rather than course_name when counting enrollments per course. |
| 3825 | e_learning | groupby | groupby | B_LLM_CONTROL | Group by Courses.course_id, with course_name and course_description, before applying HAVING COUNT(*) > 2. |
| 3826 | e_learning | groupby | groupby | B_LLM_CONTROL | Count enrollments per course_id, not per course_name, and select that course's description and name when the count is greater than two. |
| 3831 | e_learning | wrong_projection | wrong_projection,wrong_table_col | B_LLM_CONTROL | Select Student_Tests_Taken.date_test_taken for rows where test_result = 'Fail', not Student_Course_Enrolment.date_of_completion. |
| 3841 | e_learning | join_semantics | join_semantics | B_LLM_CONTROL | Start from Students and LEFT JOIN Student_Course_Enrolment, then keep students with COUNT(enrolment rows) <= 2 so zero-enrollment students are included. |
| 3844 | e_learning | join_semantics | join_semantics | B_LLM_CONTROL | Find unenrolled students by student_id using NOT EXISTS or a LEFT JOIN anti-join, then select their personal_name. |
| 3851 | insurance_policies | join_semantics | join_semantics | B_LLM_CONTROL | For the maximum Amount_Claimed branch, select matching claims directly from Claims or use a LEFT JOIN so claims with no settlements are not excluded. |
| 3863 | insurance_policies | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Compare Amount_Claimed to AVG(Amount_Claimed), using the correct claim/settlement columns, and return the relevant claim start dates. |
| 3864 | insurance_policies | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Filter Claims by Amount_Claimed <= (SELECT AVG(Amount_Claimed) FROM Claims), not by Amount_Settled. |
| 3870 | insurance_policies | aggregation | aggregation,wrong_table_col,groupby | B_LLM_CONTROL | For each claim, count settlements and order by MAX(Settlements.Date_Claim_Settled), not by an arbitrary Claims date column. |
| 3887 | insurance_policies | count_distinct | count_distinct | B_LLM_CONTROL | Group Customer_Policies by Policy_Type_Code and order by COUNT(DISTINCT Customer_ID) DESC. |
| 3895 | insurance_policies | wrong_projection | wrong_projection,wrong_table_col | B_LLM_CONTROL | For claims with exactly one settlement, return Date_Claim_Made plus the settlement date and Settlements.Amount_Settled. |
| 3896 | insurance_policies | wrong_projection | wrong_projection,wrong_table_col | B_LLM_CONTROL | Include the amount settled and use the settlement row's date/amount for claims having exactly one settlement. |
| 3899 | hospital_1 | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Join Department to Affiliated_With and count affiliated physicians per department, then choose the department with the largest count. |
| 3900 | hospital_1 | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Count employees via Affiliated_With grouped by department, rather than counting rows in Department. |
| 3901 | hospital_1 | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Join departments to Affiliated_With, count employees per department, order by that count ascending, and select the head. |
| 3902 | hospital_1 | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Use Affiliated_With to count employees per department and return the head of the department with the minimum count. |
| 3903 | hospital_1 | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Count affiliated physicians per department using Affiliated_With, find the department with the least employees, then join to Physician for the head's name and position. |
| 3904 | hospital_1 | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Join through Affiliated_With to compute employee counts per department, pick the least, and return that department head's physician name and position. |
| 3945 | hospital_1 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select T1.brand (not T1.name) with COUNT(*) while grouping by T1.brand. |
| 3946 | hospital_1 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select T1.brand (not T1.name) with the prescription count grouped by T1.brand. |
| 3949 | hospital_1 | other | other | B_LLM_CONTROL | Order treatments by dateundergoes DESC before applying LIMIT 1 to get the most recent treatment. |
| 3950 | hospital_1 | other | other | B_LLM_CONTROL | Use ORDER BY DateUndergoes DESC so the first row is the most recent treatment. |
| 3959 | hospital_1 | text_sort | text_sort,top_n_tie,dup_rows | A_DETERMINISTIC | Compare T2.dose numerically, find the global maximum dose, and return DISTINCT physician names tied at that max. |
| 3960 | hospital_1 | text_sort | text_sort | A_DETERMINISTIC | Cast T2.Dose to a numeric type when ordering or computing the maximum dose before selecting the physician name. |
| 3965 | hospital_1 | wrong_projection | wrong_projection,wrong_table_col,dup_rows | B_LLM_CONTROL | Join On_Call.nurse to Nurse.employeeid and select DISTINCT Nurse.name for blockfloor=1 and blockcode=1. |
| 3971 | hospital_1 | other | other | B_LLM_CONTROL | Sort procedures by cost DESC and then LIMIT 3 to return the three most expensive procedures. |
| 3972 | hospital_1 | other | other | B_LLM_CONTROL | Use ORDER BY cost DESC LIMIT 3 to get the three most costly procedures. |
| 4061 | student_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter the teacher as T2.lastname='MARROTTE' and T2.firstname='KIRK' before returning student first and last names. |
| 4065 | student_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter the student as T1.lastname='GELL' and T1.firstname='TAMI' before selecting teacher last names. |
| 4069 | student_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter the teacher as T2.lastname='KAWA' and T2.firstname='GORDON' before counting joined students. |
| 4070 | student_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use T2.lastname='KAWA' and T2.firstname='GORDON' in the teacher filter. |
| 4071 | student_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter teachers with T2.lastname='TARRING' and T2.firstname='LEIA' before counting their students. |
| 4072 | student_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use T2.lastname='TARRING' and T2.firstname='LEIA' in the WHERE clause. |
| 4079 | student_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | For third-grade students, exclude only NOT (T2.lastname='COVIN' AND T2.firstname='JEROME'). |
| 4080 | student_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Replace the separate != predicates with NOT (T2.lastname='COVIN' AND T2.firstname='JEROME') for the teacher exclusion. |
| 4108 | company_employee | other | other | B_LLM_CONTROL | Add DESC to the ORDER BY: ORDER BY T1.Year_working DESC. |
| 4112 | company_employee | other | other | B_LLM_CONTROL | Order by Sales_in_Billion DESC, then Profits_in_Billion DESC for companies with sales over 200. |
| 4231 | cre_Doc_Tracking_DB | count_distinct | count_distinct | B_LLM_CONTROL | Group by location_code and use HAVING COUNT(DISTINCT Document_ID) >= 3. |
| 4232 | cre_Doc_Tracking_DB | count_distinct | count_distinct | B_LLM_CONTROL | Count DISTINCT Document_ID per Location_Code and keep locations with at least three documents. |
| 4234 | cre_Doc_Tracking_DB | join_semantics | join_semantics,count_distinct | B_LLM_CONTROL | Start from Ref_locations, LEFT JOIN Document_locations, group by location code/name, and order by COUNT(DISTINCT Document_ID) ASC. |
| 4321 | tracking_grants_for_research | join_semantics | join_semantics | B_LLM_CONTROL | Apply both date filters to the same Grants.grant_id, then select DISTINCT Grants.grant_amount. |
| 4322 | tracking_grants_for_research | join_semantics | join_semantics | B_LLM_CONTROL | Join Documents to Grants and require both conditions on the same grant_id before returning distinct grant_amount values. |
| 4327 | tracking_grants_for_research | join_semantics | join_semantics | B_LLM_CONTROL | Remove the UNION with leader rows and return date_from/date_to only for staff on the project with the highest staff count. |
| 4328 | tracking_grants_for_research | join_semantics | join_semantics | B_LLM_CONTROL | Find project_id values that both have the maximum staff count and include a leader role, then return Project_Staff date_from/date_to for those projects. |
| 4334 | tracking_grants_for_research | groupby | groupby | B_LLM_CONTROL | Group staff counts by individual organisation_id, rank organisations by staff count, and return the organisation_type of the top organisation. |
| 4338 | tracking_grants_for_research | wrong_filter | wrong_filter | B_LLM_CONTROL | Use AND between T2.document_description='Regular' and T3.grant_amount>100. |
| 4341 | tracking_grants_for_research | groupby | groupby,aggregation | B_LLM_CONTROL | First identify projects with project_details='omnis' or with COUNT outcomes > 2, then join to Tasks to return all task_details, task_id, and project_id. |
| 4342 | tracking_grants_for_research | groupby | groupby,aggregation | B_LLM_CONTROL | Use a subquery counting outcomes per project_id with HAVING COUNT(*) >= 3, then join those projects to Tasks to list all tasks. |
| 4364 | tracking_grants_for_research | groupby | groupby,aggregation,wrong_table_col | B_LLM_CONTROL | For each staff_id, count DISTINCT Project_Staff.project_id by role_code without Project_outcomes, rank roles per staff, and return the max role description. |
| 4367 | tracking_grants_for_research | join_semantics | join_semantics | B_LLM_CONTROL | Find grant_id values that have both document descriptions, then select their grant_start_date. |
| 4368 | tracking_grants_for_research | join_semantics | join_semantics | B_LLM_CONTROL | Intersect or group by grant_id for grants having both 'Regular' and 'Initial Application', then return grant_start_date. |
| 4392 | tracking_grants_for_research | wrong_projection | wrong_projection,join_semantics | B_LLM_CONTROL | Select Projects.project_id with COUNT(Tasks.task_id), using a LEFT JOIN if projects with zero tasks should be included. |
| 4394 | tracking_grants_for_research | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter Project_Staff rows whose date range overlaps the given interval, using inclusive bounds and handling NULL endpoints if applicable. |
| 4439 | network_2 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select both name and age from Person where gender='male', ordered by age. |
| 4440 | network_2 | wrong_projection | wrong_projection | B_LLM_CONTROL | Return name and age for each male person and order the results by age. |
| 4441 | network_2 | wrong_table_col | wrong_table_col,join_condition,wrong_filter | B_LLM_CONTROL | Find common T2.friend values from rows where T2.name='Dan' and T2.name='Alice', then join Person.name to that friend value for name and age. |
| 4443 | network_2 | wrong_table_col | wrong_table_col,join_condition,wrong_filter | B_LLM_CONTROL | Filter PersonFriend.name IN ('Dan','Alice') and join Person.name = PersonFriend.friend to return those friends' names and ages. |
| 4444 | network_2 | wrong_table_col | wrong_table_col,join_condition,wrong_filter | B_LLM_CONTROL | Use PersonFriend.name IN ('Dan','Alice') and select DISTINCT Person.name, Person.age by joining Person.name to PersonFriend.friend. |
| 4448 | network_2 | wrong_filter | wrong_filter,join_semantics | B_LLM_CONTROL | Filter Person.age > 40 for the person, and use NOT EXISTS/anti-join to ensure they have no friends whose Person.age < 30, including people with no friends. |
| 4456 | network_2 | wrong_filter | wrong_filter,wrong_projection | B_LLM_CONTROL | Filter PersonFriend.name = 'Bob' and select PersonFriend.friend as Bob's friends. |
| 4462 | network_2 | wrong_filter | wrong_filter | B_LLM_CONTROL | Remove the gender='male' condition and return Alice's friends whose joined Person.job = 'doctor'. |
| 4464 | network_2 | wrong_projection | wrong_projection | B_LLM_CONTROL | Select the friend name, i.e. PersonFriend.friend or the joined Person.name, for friends whose Person.city is New York. |
| 4466 | network_2 | wrong_projection | wrong_projection,wrong_filter | B_LLM_CONTROL | Select DISTINCT the friend name (T1.name/T2.friend) and compare friend ages against the average age computed over people who appear as friends. |
| 4468 | network_2 | join_condition | join_condition,wrong_filter | B_LLM_CONTROL | Join Person.name to PersonFriend.name so the age filter applies to the person, then return that person's name, friend, and age. |
| 4476 | network_2 | wrong_filter | wrong_filter,join_condition | B_LLM_CONTROL | Use PersonFriend.name = 'Alice', join Person on Person.name = PersonFriend.friend, and compute the max year among Alice's outgoing friendships. |
| 4481 | network_2 | join_semantics | join_semantics,wrong_filter | B_LLM_CONTROL | Count people from Person for whom NOT EXISTS any PersonFriend row whose friend lives in Austin, including people with zero friends. |
| 4482 | network_2 | join_semantics | join_semantics,wrong_filter | B_LLM_CONTROL | Count Person rows where no joined friend has city = 'Austin', using NOT EXISTS or a LEFT anti-join. |
| 4483 | network_2 | join_semantics | join_semantics | B_LLM_CONTROL | Find Alice's two-hop friends by selecting DISTINCT T3.friend from Alice -> friend -> friend, without the extra join requiring those nodes to have friends. |
| 4484 | network_2 | join_semantics | join_semantics | B_LLM_CONTROL | Select DISTINCT T3.friend as Alice's friends-of-friends and remove the unnecessary T4 PersonFriend join. |
| 4505 | document_management | wrong_filter | wrong_filter | B_LLM_CONTROL | Use HAVING COUNT(*) >= 4 for document_type_code groups. |
| 4510 | document_management | aggregation | aggregation,wrong_table_col,groupby | B_LLM_CONTROL | Order documents by documents.access_count ASC and return the joined document_structure_description for the least-accessed document. |
| 4511 | document_management | aggregation | aggregation,wrong_table_col,groupby | B_LLM_CONTROL | Select the document with the minimum access_count, then join to document_structures to return its structure description. |
| 4514 | document_management | groupby | groupby | B_LLM_CONTROL | First identify the top 3 document_type_code values and top 3 document_structure_code values by count, then return all documents whose type and structure are both in those sets. |
| 4515 | document_management | groupby | groupby | B_LLM_CONTROL | Compute top-3 type codes and top-3 structure codes in subqueries, then filter documents by both and select all matching document_name values. |
| 4517 | document_management | wrong_filter | wrong_filter | B_LLM_CONTROL | Use HAVING SUM(access_count) <= 10000 for document_type_code groups. |
| 4522 | document_management | groupby | groupby | B_LLM_CONTROL | Find the most frequent role_code, then select user_name and password for all users with that role. |
| 4523 | document_management | groupby | groupby,top_n_tie | B_LLM_CONTROL | Identify the most frequent role_code or all tied most frequent role_codes, then list every user's user_name and password with those roles. |
| 4546 | company_office | text_sort | text_sort | A_DETERMINISTIC | Order by CAST(Market_Value_billion AS REAL) DESC when sorting company names by market value. |
| 4547 | company_office | text_sort | text_sort | A_DETERMINISTIC | Cast Companies.Market_Value_billion to a numeric type in the ORDER BY before sorting descending. |
| 4676 | college_3 | join_semantics | join_semantics | B_LLM_CONTROL | LEFT JOIN DEPARTMENT to MEMBER_OF and count MEMBER_OF rows so departments with zero members are included. |
| 4677 | college_3 | join_semantics | join_semantics | B_LLM_CONTROL | Use DEPARTMENT LEFT JOIN MEMBER_OF, group by DEPARTMENT.DNO, and order by COUNT(MEMBER_OF.FacID) ASC. |
| 4699 | college_3 | join_condition | join_condition | B_LLM_CONTROL | Join DEPARTMENT to MEMBER_OF on DNO, then MEMBER_OF to FACULTY on FacID, filtering DName = 'Computer Science'. |
| 4710 | department_store | aggregation | aggregation,text_sort | B_LLM_CONTROL | Group by product_id and order by SUM(CAST(total_amount_purchased AS numeric)) DESC to get the top three products. |
| 4711 | department_store | aggregation | aggregation,text_sort | B_LLM_CONTROL | Aggregate purchase amounts per product_id with SUM after casting the amount to numeric, then sort descending and limit to 3. |
| 4730 | department_store | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Order assignments by date_assigned_from DESC, not date_assigned_to, to find the most recently assigned staff. |
| 4731 | department_store | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use staff_department_assignments.date_assigned_from as the assignment date for determining the latest assignment. |
| 4751 | department_store | aggregation | aggregation,groupby,other | B_LLM_CONTROL | Compute total assignment duration per staff_id by summing date_assigned_to - date_assigned_from, handling NULL end dates appropriately, then choose the minimum. |
| 4756 | department_store | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Compare assignment start dates against MIN(date_assigned_from) for Clerical Staff, rather than using MAX(date_assigned_to). |
| 4757 | department_store | aggregation | aggregation,wrong_table_col,dup_rows | B_LLM_CONTROL | Return DISTINCT staff_id values whose date_assigned_from is earlier than MIN(date_assigned_from) for Clerical Staff. |
| 4772 | department_store | wrong_table_col | wrong_table_col,interpretation | B_LLM_CONTROL | Use the numeric total_value_purchased column for amount comparisons/averages; if interpreting per-product strictly, test each product amount rather than only the supplier-wide AVG. |
| 4904 | store_product | wrong_table_col | wrong_table_col,groupby | B_LLM_CONTROL | Use the store_product relationship and group by the relevant listed entity with more than 3 products, then determine the max_page_size for those products. |
| 4913 | store_product | aggregation | aggregation | B_LLM_CONTROL | First select the top 3 districts by city_area in a subquery, then SUM their city_population. |
| 4914 | store_product | aggregation | aggregation | B_LLM_CONTROL | Use a subquery ordered by city_area DESC LIMIT 3, then aggregate SUM(city_population) over those rows. |
| 4939 | store_product | wrong_table_col | wrong_table_col,top_n_tie | B_LLM_CONTROL | Compare product.max_page_size, not product name, against all most-frequent max_page_size values and return products whose size is not one of them. |
| 4940 | store_product | wrong_table_col | wrong_table_col,top_n_tie | B_LLM_CONTROL | Filter on max_page_size NOT IN the set of tied most-frequent max_page_size values, selecting product names. |
| 4961 | soccer_2 | wrong_projection | wrong_projection,aggregation | B_LLM_CONTROL | Select DISTINCT pPos from Tryout instead of COUNT(DISTINCT pPos). |
| 4962 | soccer_2 | wrong_projection | wrong_projection,aggregation | B_LLM_CONTROL | Return the list of distinct pPos values with SELECT DISTINCT pPos, not the count. |
| 4993 | soccer_2 | groupby | groupby,top_n_tie | B_LLM_CONTROL | For each state, return college rows whose enr equals that state's minimum enrollment, including ties. |
| 4994 | soccer_2 | groupby | groupby | B_LLM_CONTROL | Compute MIN(enr) per state in a subquery and join back to college on state and enr to return the cName(s) for the minimum, including ties. |
| 5103 | cre_Drama_Workshop_Groups | text_sort | text_sort | A_DETERMINISTIC | Cast INVOICES.Order_Quantity to a numeric type, or use a numeric order quantity source, before applying MIN/AVG/MAX. |
| 5117 | cre_Drama_Workshop_Groups | count_distinct | count_distinct | B_LLM_CONTROL | Group by payment_method_code and count COUNT(DISTINCT Order_ID) rather than invoice rows. |
| 5131 | cre_Drama_Workshop_Groups | wrong_table_col | wrong_table_col,aggregation | B_LLM_CONTROL | Join Ref_Service_Types to Services and Bookings_Services, then count booking occurrences per Service_Type_Code. |
| 5132 | cre_Drama_Workshop_Groups | wrong_table_col | wrong_table_col,aggregation | B_LLM_CONTROL | Join Services to Bookings_Services and aggregate bookings by Service_Type_Code to find the most performed service type. |
| 5135 | cre_Drama_Workshop_Groups | wrong_projection | wrong_projection | B_LLM_CONTROL | Select Drama_Workshop_Groups.Store_Name, preferably DISTINCT, for groups whose Services.Product_Name = 'film'. |
| 5136 | cre_Drama_Workshop_Groups | wrong_projection | wrong_projection | B_LLM_CONTROL | Select Drama_Workshop_Groups.Store_Name, preferably DISTINCT, instead of phone and email for services with Product_Name = 'film'. |
| 5147 | cre_Drama_Workshop_Groups | aggregation | aggregation,wrong_filter,wrong_table_col,dup_rows | B_LLM_CONTROL | Compute each order's total price, e.g. SUM(Product_Price * Order_Quantity), filter totals > 1000, return order dates distinctly, and include relevant Bookings/Services orders if they are part of the o |
| 5148 | cre_Drama_Workshop_Groups | aggregation | aggregation,wrong_filter,wrong_table_col,dup_rows | B_LLM_CONTROL | Group items by order, SUM(Product_Price * Order_Quantity), filter orders with total > 1000, return order dates distinctly, and include Bookings/Services orders if applicable. |
| 5169 | cre_Drama_Workshop_Groups | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Aggregate Invoice_Items.Product_ID, not INVOICES.Product_ID, to find the most frequently ordered item on invoices. |
| 5194 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5198 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5199 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5200 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5205 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5209 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5228 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5233 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5242 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5253 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5254 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5259 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5260 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5266 | music_2 | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 5309 | manufactory_1 | groupby | groupby | B_LLM_CONTROL | Find the max revenue per Headquarter/city and join back to manufacturers to return the name and revenue rows matching that max, including ties. |
| 5310 | manufactory_1 | groupby | groupby | B_LLM_CONTROL | Use a per-Headquarter max-revenue subquery and join back to manufacturers so the returned name belongs to the max-revenue company, including ties. |
| 5312 | manufactory_1 | aggregation | aggregation,groupby | B_LLM_CONTROL | Return each manufacturer identified by Code/Name with its Revenue directly, rather than summing by non-unique Name. |
| 5317 | manufactory_1 | wrong_filter | wrong_filter,wrong_table_col,aggregation | B_LLM_CONTROL | Filter products by Manufacturer not belonging to Sony's manufacturer code and count product rows or product IDs, not DISTINCT product names. |
| 5318 | manufactory_1 | wrong_filter | wrong_filter,wrong_table_col,aggregation | B_LLM_CONTROL | Join/filter on products.Manufacturer versus Sony's manufacturer code and count products, avoiding NOT IN on product names and COUNT(DISTINCT name). |
| 5349 | manufactory_1 | groupby | groupby,join_semantics | B_LLM_CONTROL | For each manufacturer, find max product price and join back to products to return the product name(s) with that price; use LEFT JOIN if manufacturers without products must be kept. |
| 5350 | manufactory_1 | groupby | groupby | B_LLM_CONTROL | Find each manufacturer's maximum product price and join back to products so the returned product name and price correspond to the max, including tied products. |
| 5351 | manufactory_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Find the minimum price per product category/name and join back to products to return only the code(s) of products at that minimum price. |
| 5385 | tracking_software_problems | wrong_projection | wrong_projection | B_LLM_CONTROL | Select Problems.problem_id instead of product_id for problems reported by Dameon Frami or Jolie Weber. |
| 5386 | tracking_software_problems | wrong_projection | wrong_projection | B_LLM_CONTROL | Return T1.problem_id, not T1.product_id, for problems reported by the specified staff members. |
| 5388 | tracking_software_problems | join_semantics | join_semantics | B_LLM_CONTROL | Apply both staff conditions to the same Problems row, joining staff aliases for reported_by_staff_id and closure_authorised_by_staff_id. |
| 5408 | shop_membership | groupby | groupby,aggregation,wrong_filter | B_LLM_CONTROL | Group branches by city and use HAVING SUM(membership_amount) > 100, not a per-branch membership_amount >= 100 filter. |
| 5411 | shop_membership | text_sort | text_sort | A_DETERMINISTIC | Cast branch.membership_amount to a numeric type before applying MIN and MAX. |
| 5412 | shop_membership | text_sort | text_sort | A_DETERMINISTIC | Use MIN(CAST(membership_amount AS numeric)) and MAX(CAST(membership_amount AS numeric)) with the existing 2011-or-London filter. |
| 5416 | shop_membership | wrong_projection | wrong_projection | B_LLM_CONTROL | Select DISTINCT Level FROM member instead of counting the distinct levels. |
| 5424 | shop_membership | wrong_projection | wrong_projection,aggregation | B_LLM_CONTROL | Select DISTINCT T1.branch_id and T2.name for registrations after 2015, without COUNT(*) aggregation. |
| 5433 | shop_membership | wrong_filter | wrong_filter,dup_rows | B_LLM_CONTROL | Return DISTINCT cities that have an open_year = 2001 branch and also have a membership_amount > 100 branch, using EXISTS/self-join by city. |
| 5434 | shop_membership | wrong_filter | wrong_filter,dup_rows | B_LLM_CONTROL | Use city-level existence checks or a self-join so one branch can satisfy open_year = 2001 and another can satisfy membership_amount > 100; return DISTINCT cities. |
| 5440 | shop_membership | aggregation | aggregation | B_LLM_CONTROL | For level 6 members, sum purchase.Total_pounds rather than counting purchase rows. |
| 5476 | voter_2 | join_condition | join_condition,wrong_table_col | B_LLM_CONTROL | Join STUDENT.StuID to VOTING_RECORD.Class_President_Vote, not CLASS_Senator_VOTE. |
| 5495 | voter_2 | join_semantics | join_semantics,wrong_filter | B_LLM_CONTROL | Apply T1.city_code <> 'PIT' directly to the student rows joined on VICE_PRESIDENT_Vote, then select DISTINCT Fname. |
| 5496 | voter_2 | join_semantics | join_semantics,wrong_filter | B_LLM_CONTROL | Filter the joined candidate student rows with T1.city_code <> 'PIT' instead of EXCEPTing first names. |
| 5497 | voter_2 | join_semantics | join_semantics,wrong_filter | B_LLM_CONTROL | Apply T1.Advisor <> 2192 to the same student row joined on PRESIDENT_Vote, rather than EXCEPTing last names. |
| 5498 | voter_2 | join_semantics | join_semantics,wrong_filter | B_LLM_CONTROL | Filter the joined student rows with T1.Advisor <> 2192 before selecting DISTINCT LName. |
| 5499 | voter_2 | join_semantics | join_semantics,wrong_filter | B_LLM_CONTROL | Apply Advisor = 8741 to the same student row that is joined on PRESIDENT_Vote, instead of INTERSECTing last-name sets. |
| 5500 | voter_2 | join_semantics | join_semantics,interpretation | B_LLM_CONTROL | Avoid INTERSECT on LName; apply Advisor = 8741 to the same qualifying student row, or if interpreting the question as voters, join on VOTING_RECORD.StuID and require President_Vote IS NOT NULL. |
| 5535 | products_gen_characteristics | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Filter product_category_code = 'Spices' and typical_selling_price > 1000, not typical_buying_price. |
| 5557 | products_gen_characteristics | wrong_filter | wrong_filter | B_LLM_CONTROL | Use WHERE t1.product_name = 'cumin' instead of 'sesame'. |
| 5558 | products_gen_characteristics | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter products.product_name = 'cumin' while counting DISTINCT characteristic_name. |
| 5577 | products_gen_characteristics | count_distinct | count_distinct,join_semantics | B_LLM_CONTROL | Count DISTINCT t1.product_id and use LEFT JOIN or EXISTS logic so white products without characteristics are not excluded. |
| 5578 | products_gen_characteristics | count_distinct | count_distinct,join_semantics | B_LLM_CONTROL | Start from products, LEFT JOIN characteristics/colors as needed, apply the white-or-hot condition, and COUNT(DISTINCT products.product_id). |
| 5590 | products_gen_characteristics | wrong_filter | wrong_filter | B_LLM_CONTROL | Use ref_colors.color_description != 'white' together with unit_of_measure != 'Handful'. |
| 5630 | swimming | count_distinct | count_distinct,top_n_tie | B_LLM_CONTROL | Group by stadium, count COUNT(DISTINCT record.swimmer_id), and return all stadiums tied for the maximum count. |
| 5636 | railway | wrong_filter | wrong_filter | B_LLM_CONTROL | Compare Country to the exact literal 'Australia' with no trailing tab, e.g. Country <> 'Australia'. |
| 5702 | dorm_1 | groupby | groupby,wrong_projection | B_LLM_CONTROL | Return one row per student, including the student id/name, and GROUP BY the student when computing the distinct major and city_code counts. |
| 5708 | dorm_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Use logic sex = 'F' OR city_code = 'BAL' OR (sex = 'M' AND age < 20). |
| 5735 | dorm_1 | groupby | groupby | B_LLM_CONTROL | Compare each student's age to the average age for that same sex, e.g. with a correlated subquery on sex, then count grouped by sex. |
| 5736 | dorm_1 | groupby | groupby | B_LLM_CONTROL | Compare age against the gender-specific average age, not the global average, before grouping/counting by sex. |
| 5740 | dorm_1 | wrong_filter | wrong_filter,join_semantics | B_LLM_CONTROL | Remove the student_capacity > 100 filter and LEFT JOIN dorm to has_amenity so every dorm is counted, including zero-amenity dorms. |
| 5759 | dorm_1 | join_semantics | join_semantics | B_LLM_CONTROL | Use LEFT JOIN from dorm to has_amenity and count non-null amenity ids so dorms with zero amenities can be the minimum. |
| 5760 | dorm_1 | join_semantics | join_semantics | B_LLM_CONTROL | Use LEFT JOIN from dorm to has_amenity and count T2.amenid so zero-amenity dorms are included when finding the fewest amenities. |
| 5766 | dorm_1 | join_semantics | join_semantics | B_LLM_CONTROL | Include dorms with a TV Lounge using IN or an INNER JOIN/filter on dorm_amenity.amenity_name = 'TV Lounge', not NOT IN. |
| 5775 | customer_complaints | join_semantics | join_semantics,groupby | B_LLM_CONTROL | LEFT JOIN products to complaints, group by product_id/product_name, and COUNT(complaints.complaint_id) so products with zero complaints are listed. |
| 5777 | customer_complaints | groupby | groupby,wrong_table_col,other | B_LLM_CONTROL | First find the product_id with the greatest complaint count, then return emails of all customers who filed complaints for that product. |
| 5778 | customer_complaints | groupby | groupby,wrong_table_col,other | B_LLM_CONTROL | Group complaints by product_id to find the product with the greatest count, then select all customer emails for complaints on that product. |
| 5779 | customer_complaints | join_condition | join_condition,groupby | B_LLM_CONTROL | Join customers to complaints on customer_id, identify the customer(s) with the fewest complaints, then list all distinct product names from their complaints. |
| 5780 | customer_complaints | join_condition | join_condition,groupby | B_LLM_CONTROL | Properly join customers, complaints, and products; find the customer(s) with the fewest complaints and return all distinct products they complained about. |
| 5811 | customer_complaints | other | other | B_LLM_CONTROL | Order staff complaint counts with ORDER BY COUNT(*) DESC before LIMIT 5. |
| 5812 | customer_complaints | other | other | B_LLM_CONTROL | Use ORDER BY COUNT(*) DESC so the five staff with the most handled complaints are returned. |
| 5813 | customer_complaints | other | other | B_LLM_CONTROL | Sort state groups by COUNT(*) DESC to return the state with the most customers. |
| 5814 | customer_complaints | other | other | B_LLM_CONTROL | Use ORDER BY COUNT(*) DESC when grouping customers by state. |
| 5830 | workshop_paper | count_distinct | count_distinct | B_LLM_CONTROL | Group by College and order by COUNT(DISTINCT Author) DESC to find the college with the most authors with submissions. |
| 5843 | workshop_paper | join_semantics | join_semantics,dup_rows | B_LLM_CONTROL | Return distinct authors for whom no submission_id appears in acceptance, e.g. with NOT EXISTS at the author level. |
| 5844 | workshop_paper | join_semantics | join_semantics | B_LLM_CONTROL | Filter at the author level so only authors with no submissions in acceptance are returned. |
| 5856 | tracking_share_transactions | text_sort | text_sort | A_DETERMINISTIC | Cast share_count to a numeric type before applying MAX, while filtering amount_of_transaction < 10000. |
| 5865 | tracking_share_transactions | join_condition | join_condition | B_LLM_CONTROL | Join LOTS to TRANSACTIONS_LOTS using T1.lot_id = T2.lot_id, then join to TRANSACTIONS on transaction_id. |
| 5866 | tracking_share_transactions | join_condition | join_condition | B_LLM_CONTROL | Use T1.lot_id = T2.lot_id for the LOTS-to-TRANSACTIONS_LOTS join, then filter transactions by share_count > 100 and type code 'PUR'. |
| 5900 | cre_Theme_park | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Filter Tourist_Attractions.Name = 'UK Gallery' and join to Locations by Location_ID to get the address. |
| 5923 | cre_Theme_park | wrong_projection | wrong_projection | B_LLM_CONTROL | Select the tourist attraction name/details from TOURIST_ATTRACTIONS along with How_to_Get_There for attractions related to the royal family. |
| 5946 | cre_Theme_park | wrong_table_col | wrong_table_col,aggregation | B_LLM_CONTROL | Join Visits to Tourist_Attractions and count visits grouped by How_to_Get_There, then take the highest count. |
| 5956 | cre_Theme_park | join_semantics | join_semantics | B_LLM_CONTROL | LEFT JOIN Tourist_Attractions to Visits and HAVING COUNT(Visits.Visit_ID) <= 1 so zero-visit attractions are included. |
| 5957 | cre_Theme_park | join_semantics | join_semantics | B_LLM_CONTROL | Use a LEFT JOIN to Visits and count non-null visit ids, keeping attractions with 0 or 1 visits. |
| 5960 | cre_Theme_park | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter Features.feature_Details for 'parking' or 'shopping', not 'park'. |
| 5961 | cre_Theme_park | wrong_filter | wrong_filter | B_LLM_CONTROL | Use Features.feature_Details IN ('parking', 'shopping') when selecting the attraction names. |
| 5999 | game_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Remove HAVING COUNT(*) >= 2 and return all distinct advisor values from Student. |
| 6015 | game_1 | wrong_table_col | wrong_table_col,join_semantics,aggregation | B_LLM_CONTROL | Start from Student, LEFT JOIN the sports and games participation tables, and compute each student's sport count and game count including zeros. |
| 6060 | customers_and_addresses | aggregation | aggregation | B_LLM_CONTROL | First SUM order_quantity per order_id, then take the AVG of those per-order totals. |
| 6061 | customers_and_addresses | aggregation | aggregation,groupby | B_LLM_CONTROL | Aggregate at the order_id level first rather than averaging all line items directly; compute the intended per-order quantity measure from order_items. |
| 6086 | customers_and_addresses | count_distinct | count_distinct,wrong_filter | B_LLM_CONTROL | Count DISTINCT customers.customer_id per city and apply the appropriate residential/current address filters. |
| 6100 | customers_and_addresses | aggregation | aggregation,wrong_table_col | B_LLM_CONTROL | Find Tillman Ernser's contact channel with the latest active_from_date and return that row's active_to_date. |
| 6108 | customers_and_addresses | aggregation | aggregation,text_sort | B_LLM_CONTROL | Aggregate order_items.order_quantity per order_id with SUM(CAST(order_quantity AS numeric)), choose the max-total order, then return its customer_name. |
| 6109 | customers_and_addresses | aggregation | aggregation,text_sort | B_LLM_CONTROL | SUM(CAST(order_items.order_quantity AS numeric)) by order_id, pick the order with the largest total goods amount, and return the corresponding customer_name. |
| 6112 | customers_and_addresses | groupby | groupby | B_LLM_CONTROL | Group by the unique customer key t1.customer_id (and select/group compatible columns) before ordering by SUM(t3.order_quantity) to return the correct payment_method. |
| 6113 | customers_and_addresses | groupby | groupby | B_LLM_CONTROL | Group totals by t1.customer_id rather than customer_name, then return that customer's payment_method for the minimum total ordered quantity. |
| 6132 | customers_and_addresses | other | other | B_LLM_CONTROL | Order by SUM(t1.order_quantity) DESC before LIMIT 1 to get the product with the largest total order quantity. |
| 6133 | customers_and_addresses | other | other | B_LLM_CONTROL | Use ORDER BY SUM(t1.order_quantity) DESC so the most-bought product is selected. |
| 6141 | customers_and_addresses | join_semantics | join_semantics | B_LLM_CONTROL | Exclude ordered customers by customer_id using NOT EXISTS or EXCEPT on customer_id, then return customer_name. |
| 6207 | roller_coaster | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter out any country whose Languages contains German, e.g. WHERE Languages NOT LIKE '%German%'. |
| 6214 | roller_coaster | text_sort | text_sort | A_DETERMINISTIC | Order by CAST(Speed AS REAL) DESC to find the numerically highest speed, then return Park. |
| 6227 | ship_1 | text_sort | text_sort | A_DETERMINISTIC | Sort captains with ORDER BY CAST(age AS INTEGER) DESC. |
| 6228 | ship_1 | text_sort | text_sort | A_DETERMINISTIC | Use ORDER BY CAST(age AS INTEGER) DESC so ages sort numerically from oldest to youngest. |
| 6232 | ship_1 | other | other,top_n_tie | B_LLM_CONTROL | Order ranks by COUNT(*) ASC and, if all fewest ranks are required, return every rank whose count equals the minimum count. |
| 6243 | ship_1 | text_sort | text_sort,wrong_filter | A_DETERMINISTIC | Cast age to a numeric type in ORDER BY and exclude NULL ages before taking the youngest captain. |
| 6244 | ship_1 | text_sort | text_sort,top_n_tie | A_DETERMINISTIC | Order by CAST(age AS INTEGER) ASC and return all captains tied at the minimum age if ties must be preserved. |
| 6264 | ship_1 | text_sort | text_sort | A_DETERMINISTIC | Order joined ships/captains by CAST(t2.age AS INTEGER) ASC before selecting the youngest captain's ship. |
| 6299 | city_record | wrong_filter | wrong_filter | B_LLM_CONTROL | Use regional_population > 8000000 OR regional_population < 5000000. |
| 6300 | city_record | wrong_filter | wrong_filter | B_LLM_CONTROL | Replace the > 10000000 threshold with > 8000000 while keeping the < 5000000 condition. |
| 6303 | city_record | text_sort | text_sort | A_DETERMINISTIC | Parse the TEXT date values into real dates and order by that parsed date DESC. |
| 6325 | e_government | wrong_table_col | wrong_table_col,text_sort | B_LLM_CONTROL | For the organization with the numeric maximum uk_vat_number, order contacts by t2.date_contact_from ASC, not date_contact_to, and return individual_last_name. |
| 6326 | e_government | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Order organization_contact_individuals by date_contact_from ASC to identify the first contacted individual. |
| 6334 | e_government | count_distinct | count_distinct | B_LLM_CONTROL | Use COUNT(DISTINCT town_city) from addresses where state_province_county = 'Colorado'. |
| 6371 | flight_company | aggregation | aggregation | B_LLM_CONTROL | Select velocity values directly from flight where pilot = 'Thompson' instead of averaging them. |
| 6376 | flight_company | groupby | groupby | B_LLM_CONTROL | Group flights by airport id, e.g. GROUP BY T1.id, T1.name, T1.IATA, then order by COUNT(*) DESC. |
| 6436 | cre_Docs_and_Epenses | wrong_filter | wrong_filter | B_LLM_CONTROL | Use HAVING COUNT(*) >= 2 for projects with at least two documents. |
| 6466 | cre_Docs_and_Epenses | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Find document_id values having both budget_type_code 'GV' and 'SF' first, then return those documents' document_date values. |
| 6467 | cre_Docs_and_Epenses | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Intersect or group by document_id, not document_date, to ensure the same document has both 'GV' and 'SF', then output document_date. |
| 6468 | cre_Docs_and_Epenses | text_sort | text_sort | A_DETERMINISTIC | Compare Account_details numerically, e.g. CAST(Account_details AS numeric), when finding the largest value, and union with Account_details LIKE '%5%'. |
| 6476 | scientist_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Count projects by their unique project identifier, e.g. COUNT(*) or COUNT(DISTINCT Code), not DISTINCT name. |
| 6477 | scientist_1 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Use COUNT(*) or COUNT(DISTINCT Code) from projects rather than COUNT(DISTINCT name). |
| 6493 | scientist_1 | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter the second project name as 'A Puzzling Pattern' instead of 'A Puzzling Parallax'. |
| 6497 | scientist_1 | join_semantics | join_semantics,groupby | B_LLM_CONTROL | Use Projects LEFT JOIN assignedto and group by project Code and name so projects with zero scientists are included without merging same-named projects. |
| 6498 | scientist_1 | groupby | groupby,interpretation,count_distinct | B_LLM_CONTROL | For per-project counts, group by project code/name; if a single total is intended, count DISTINCT T2.scientist across projects with hours > 300. |
| 6500 | scientist_1 | groupby | groupby,join_semantics | B_LLM_CONTROL | Group by scientist SSN and name, and use a LEFT JOIN if scientists with zero projects should be included. |
| 6501 | scientist_1 | groupby | groupby,join_semantics | B_LLM_CONTROL | Use a LEFT JOIN from scientists to assignedto and group by SSN and name to avoid merging same-named scientists and omitting zero-project scientists. |
| 6518 | wine_1 | other | other | B_LLM_CONTROL | Order wines by Score DESC before LIMIT 1 to get the highest-rated wine. |
| 6519 | wine_1 | other | other | B_LLM_CONTROL | Use ORDER BY Score DESC or filter by MAX(Score) to return the wine with the highest score. |
| 6520 | wine_1 | other | other | B_LLM_CONTROL | Order by SCORE DESC before LIMIT 1 to return the winery of the highest-scoring wine. |
| 6521 | wine_1 | other | other | B_LLM_CONTROL | Use ORDER BY SCORE DESC or a MAX(score) filter to find the winery for the highest-scored wine. |
| 6559 | wine_1 | aggregation | aggregation | B_LLM_CONTROL | Compare Price to SELECT MAX(Price) FROM wine WHERE Winery = 'John Anthony', not MIN(Price). |
| 6562 | wine_1 | other | other | B_LLM_CONTROL | Derive one price per distinct Name, e.g. GROUP BY Name with MIN(Price), and order the distinct names by that derived price. |
| 6564 | wine_1 | wrong_filter | wrong_filter,groupby | B_LLM_CONTROL | Move the pre-2010 condition to WHERE: filter WINE.year < 2010 before GROUP BY Appelation, then order by COUNT(*) DESC. |
| 6565 | wine_1 | wrong_filter | wrong_filter,groupby | B_LLM_CONTROL | Use WHERE T2.year < 2010 before grouping appellations, then count only those wines and order by COUNT(*) DESC. |
| 6607 | train_station | wrong_filter | wrong_filter | B_LLM_CONTROL | Return DISTINCT locations with per-location checks, e.g. EXISTS a station with number_of_platforms >= 15 and EXISTS a station with total_passengers > 25. |
| 6621 | train_station | join_semantics | join_semantics,dup_rows | B_LLM_CONTROL | Select trains for which NOT EXISTS any joined train_station/station row with station.location = 'London', using DISTINCT if listing train names. |
| 6651 | driving_school | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Join Staff to Addresses on Staff.staff_address_id = Addresses.address_id and count staff whose state_province_county = 'Georgia'. |
| 6652 | driving_school | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Join Staff to Addresses on Staff.staff_address_id = Addresses.address_id and count employees/staff with state_province_county = 'Georgia'. |
| 6666 | driving_school | wrong_projection | wrong_projection | B_LLM_CONTROL | Select customer_status_code, phone_number, and email_address from Customers for first_name = 'Marina' OR last_name = 'Kohler'. |
| 6678 | driving_school | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter Customers with first_name = 'Ryan' and last_name = 'Goodwin', plus Lessons.lesson_status_code = 'Completed'. |
| 6713 | driving_school | join_semantics | join_semantics | B_LLM_CONTROL | Find staff with no Lessons by staff_id using NOT EXISTS or LEFT JOIN IS NULL, then select their first_name. |
| 6796 | activity_1 | wrong_projection | wrong_projection,join_condition | B_LLM_CONTROL | Select Faculty.Fname and join Faculty_participates_in.actid to Activity.actid before filtering activity_name IN ('Canoeing','Kayaking'). |
| 6797 | activity_1 | wrong_projection | wrong_projection,join_condition | B_LLM_CONTROL | Select Faculty.Fname and use the correct join T2.actid = T3.actid to link faculty participation to Canoeing or Kayaking. |
| 6798 | activity_1 | wrong_projection | wrong_projection,join_condition | B_LLM_CONTROL | Select professors' Fname and correctly join Faculty_participates_in.actid = Activity.actid when excluding Canoeing/Kayaking participants. |
| 6799 | activity_1 | wrong_projection | wrong_projection,join_condition,join_semantics | B_LLM_CONTROL | Use faculty IDs to identify professors who do not participate in Canoeing or Kayaking, join on T2.actid = T3.actid, then select Fname. |
| 6800 | activity_1 | wrong_projection | wrong_projection,join_condition | B_LLM_CONTROL | Select Faculty.Fname and correctly join Faculty_participates_in.actid = Activity.actid in both Canoeing and Kayaking subqueries. |
| 6801 | activity_1 | wrong_projection | wrong_projection,join_condition,join_semantics | B_LLM_CONTROL | Identify the same faculty by facID as participating in both activities, join on T2.actid = T3.actid, then output Fname. |
| 6802 | activity_1 | join_condition | join_condition | B_LLM_CONTROL | Join participates_in.actid to activity.actid in each subquery, then intersect student IDs for Canoeing and Kayaking. |
| 6803 | activity_1 | join_condition | join_condition | B_LLM_CONTROL | Use JOIN activity AS T2 ON T1.actid = T2.actid so each subquery returns students actually participating in the named activity. |
| 6823 | flight_4 | wrong_filter | wrong_filter | B_LLM_CONTROL | Filter airports.name with LIKE '%Interanation%' to match the term in the question. |
| 6832 | flight_4 | wrong_table_col | wrong_table_col | B_LLM_CONTROL | Order airports by latitude column y DESC, not elevation, and select name, city, country. |
| 6853 | flight_4 | aggregation | aggregation,wrong_projection | B_LLM_CONTROL | Count the grouped cities: SELECT COUNT(*) FROM a subquery of United States cities GROUP BY city HAVING COUNT(*) > 3. |
| 6885 | flight_4 | wrong_filter | wrong_filter,wrong_table_col | B_LLM_CONTROL | Join routes.src_apid to a source airports alias, filter source.country = 'China', group by destination airport, and order by route count DESC. |
| 6940 | tracking_orders | join_semantics | join_semantics | B_LLM_CONTROL | Start from Customers and LEFT JOIN Orders, group by customer_id, and HAVING COUNT(orders.order_id) <= 2 to include zero-order customers. |
| 6948 | architecture | groupby | groupby,aggregation | B_LLM_CONTROL | Select bridge.length_meters and architect.name for bridge rows whose length_meters equals SELECT MAX(length_meters) FROM bridge. |
| 7012 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7045 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7074 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7075 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7130 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7137 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7147 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7162 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7163 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7164 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7165 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7166 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7167 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7169 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7180 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7184 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7214 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7215 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7225 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7226 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7227 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7228 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7229 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7231 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7240 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7242 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7244 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7245 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7246 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7247 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7255 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7259 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7272 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7282 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7283 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7284 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7302 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7305 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7306 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7307 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7308 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7309 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7310 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7311 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7312 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7314 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7323 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7324 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7328 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7329 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7330 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7331 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7334 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7335 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7336 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7338 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7341 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7357 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7359 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7360 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7363 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7369 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7379 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7380 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7390 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7393 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7408 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7409 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7410 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7424 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7428 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7434 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7436 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7437 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7439 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7440 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7442 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7448 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7449 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7450 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7451 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7461 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7463 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7464 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7475 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7476 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7498 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7499 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7500 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7507 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7510 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7517 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7521 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7525 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7527 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7528 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7529 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7530 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7533 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7536 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7541 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7542 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7545 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7547 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7556 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7558 | geo | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7576 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7587 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7592 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7597 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7611 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7632 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7633 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7635 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7652 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7678 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7680 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7689 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7692 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7693 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7694 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7695 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7703 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7714 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7715 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7718 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7746 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7747 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7749 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7753 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7766 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7780 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7799 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7800 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7814 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7837 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7838 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7839 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7842 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7843 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7844 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7848 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7849 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7851 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7852 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7853 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7855 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7862 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7865 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7867 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7868 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7869 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7870 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7871 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7875 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7876 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7877 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7878 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7879 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7880 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7891 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7894 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7905 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7906 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7935 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7949 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7951 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7960 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7989 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7990 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7991 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7992 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7994 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 7995 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8003 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8004 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8005 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8006 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8026 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8033 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8035 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8056 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8061 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8062 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8069 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8071 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8072 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8073 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8075 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8076 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8078 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8085 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8086 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8089 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8095 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8102 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8103 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8105 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8112 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8113 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8116 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8123 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8124 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8125 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8127 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8130 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8131 | scholar | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8138 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8147 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8148 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8163 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8172 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8186 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8187 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8189 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8194 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8198 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8199 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8203 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8204 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8205 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8206 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8207 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8208 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8211 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8215 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8216 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8217 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8221 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8223 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8224 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8225 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8226 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8228 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8230 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8231 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8235 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8240 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8242 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8243 | yelp | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8322 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8323 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8324 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8325 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8335 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8342 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8351 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8361 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8362 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8368 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8375 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8376 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8381 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8385 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8387 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8390 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8391 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8397 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8402 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8414 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8416 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8418 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8419 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8420 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8421 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8422 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8423 | academic | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8430 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8441 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8442 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8443 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8444 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8475 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8498 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8504 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8505 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8518 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8519 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8529 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8530 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8533 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8534 | imdb | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8540 | restaurants | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8541 | restaurants | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8584 | restaurants | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8586 | restaurants | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8649 | restaurants | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8650 | restaurants | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8651 | restaurants | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
| 8657 | restaurants | empty_db | empty_db | C_NOT_ON_DATA | empty DB - cannot verify on data |
