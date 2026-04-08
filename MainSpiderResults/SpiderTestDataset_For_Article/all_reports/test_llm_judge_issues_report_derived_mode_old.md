# LLM Judge Semantic Validation Report

**Generated:** 2025-11-03 02:41:34

## Summary

- **Total Queries Evaluated:** 2,147
- **Majority CORRECT:** 1,512 (70.4%)
    *of which Unanimous CORRECT: 1,512 (100.0%)*
- **Majority PARTIALLY_CORRECT:** 52 (2.4%)
    *of which Unanimous PARTIALLY_CORRECT: 52 (100.0%)*
- **Majority INCORRECT:** 174 (8.1%)
    *of which Unanimous INCORRECT: 174 (100.0%)*
- **Mixed (No Majority):** 396 (18.5%)
    *(Mixed results have no consensus by definition)*
- **Majority UNANSWERABLE:** 13 (0.6%)
    *of which Unanimous UNANSWERABLE: 13 (100.0%)*

---

## ✅ Majority CORRECT (Non-Unanimous)

*No non-unanimous majority CORRECT queries found.*

## ⚡ Majority PARTIALLY_CORRECT

**Found 50 queries where majority of voters said PARTIALLY_CORRECT** (showing up to 50)

These queries are mostly correct but may have minor issues.

### Item: `2` (DB: `soccer_3`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate club names if a club has multiple players with Wins_count > 2; should use DISTINCT or GROUP BY to list each club once.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing DISTINCT. If a club has multiple players with more than 2 wins, the club name will be listed multiple times in the result set.

### Item: `3` (DB: `soccer_3`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate club names if multiple qualifying players per club; add DISTINCT or GROUP BY to ensure unique club names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies the clubs, but it will return duplicate club names if a club has multiple players who have won more than twice. Using SELECT DISTINCT would be more precise.

### Item: `25` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns full timestamps instead of day/date; may produce duplicate rows for the same product and shipment. Use DATE(T4.shipment_date) and DISTINCT to list unique product-day pairs.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly retrieves the product names and their shipment dates. However, it may return duplicate rows if a product was shipped multiple times. Using SELECT DISTINCT would be more precise.

### Item: `27` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Semantically joins are right, but missing DISTINCT may return duplicate product name/color when the same product appears in multiple shipped order items/shipments.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies all shipped products but may return duplicate product names and colors if a product has been shipped more than once. Using SELECT DISTINCT would be more precise.

### Item: `59` (DB: `tv_shows`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies the transmitters for radios not associated with any city channel, but it omits the DISTINCT keyword, which was explicitly requested in the question.
  - **gpt-5** (PARTIALLY_CORRECT): Missing DISTINCT; may return duplicate transmitters. Use: SELECT DISTINCT Transmitter FROM radio WHERE Radio_ID NOT IN (SELECT Radio_ID FROM city_channel_radio)

### Item: `74` (DB: `vehicle_driver`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and filter, but may return duplicate driver rows if a driver drove multiple vehicles with model 'DJ1'. Use DISTINCT on name/citizenship to ensure unique drivers.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate rows if a driver has driven multiple vehicles of the model 'DJ1'. Using SELECT DISTINCT would provide a unique list of drivers.

### Item: `130` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate customers if they have multiple matching interactions; use SELECT DISTINCT to list unique customer details.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate customer details if a customer has multiple interactions that meet the conditions. Using SELECT DISTINCT would provide a unique list of customers.

### Item: `161` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns duplicate rows for students with multiple above-average loans; use DISTINCT or GROUP BY to list each student once.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies students with loans above the average amount, but it may return duplicate student records if a student has multiple qualifying loans. Using SELECT DISTINCT would be more precise.

### Item: `162` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns correct students but may include duplicate rows if a student has multiple loans above average. Add DISTINCT or group by student to de-duplicate results.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies students with loans above the average. However, if a student has multiple loans above the average, they will be listed multiple times. Using SELECT DISTINCT would be more precise.

### Item: `219` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies clients who ordered the book, but it may return duplicate names if a client ordered 'Pride and Prejudice' more than once. Using SELECT DISTINCT T3.name would be more precise.
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and filter, but may return duplicate names if a client has multiple orders/line items for that book. Add DISTINCT on client name (or group by client) to list unique names.

### Item: `220` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Joins and filter are correct, but missing DISTINCT. Clients who ordered the book multiple times (or in multiple orders) will appear multiple times; question implies unique client names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is correct, but it might return duplicate names if a client has ordered the book 'Pride and Prejudice' more than once. Using SELECT DISTINCT would be more precise.

### Item: `301` (DB: `sing_contest`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate participants when multiple songs qualify; use DISTINCT or GROUP BY to return unique ids/names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate participants if a participant meets the criteria in multiple performances. Using SELECT DISTINCT would ensure each participant appears only once.

### Item: `306` (DB: `sing_contest`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly filters and orders the results. However, it may return duplicate artists if an artist has multiple songs that meet the criteria. The question 'Find the original artists' implies a unique list, which would require using SELECT DISTINCT.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate artists when multiple performances meet the tempo condition. Likely needs DISTINCT (or grouping) to list unique original artists ordered by voice sound quality.

### Item: `323` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Orders by distance and limits to 1, so it misses ties. If multiple pairs share the maximum distance, it returns only one instead of all such city code pairs.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query only returns one pair of cities. If there is a tie for the maximum distance, it will not return all pairs that share that distance.

### Item: `361` (DB: `boat_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate boat names if a qualifying sailor makes multiple reservations or multiple sailors book the same boat. Use DISTINCT to return unique boat names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly finds boats reserved by sailors in the age range, but it may return duplicate boat names if a boat is booked by multiple qualifying sailors. Using SELECT DISTINCT would be more precise.

### Item: `362` (DB: `boat_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate boat names if the same boat is reserved multiple times. Use DISTINCT to list unique boat names reserved by sailors aged 20–30.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies the boats, but it may return duplicate boat names if a boat is reserved by multiple sailors in the specified age range. Using SELECT DISTINCT T3.name would be more precise.

### Item: `452` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic and joins are correct, but it may return duplicates when multiple Canadian staff attend the same conference. Use DISTINCT to list unique conference names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies conferences attended by Canadian staff, but it may return duplicate conference names if multiple staff from Canada attend the same conference. Using SELECT DISTINCT is needed.

### Item: `453` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate conference names when multiple Canadian staff attend the same conference; add DISTINCT (or GROUP BY) to ensure unique conference names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate conference names if multiple staff members from Canada attend the same conference. Using SELECT DISTINCT would provide a unique list of names.

### Item: `464` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names since pilots can have multiple plane rows; should use DISTINCT or aggregate per pilot. ORDER BY age may be inconsistent if a pilot has multiple ages across rows.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate pilot names if a pilot is associated with multiple planes. Using SELECT DISTINCT pilot_name would provide a unique list of pilots as implied by the question.

### Item: `478` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May double-count planes if several pilots over 40 control the same plane. Use COUNT(DISTINCT plane_name).
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts the number of pilot-plane assignments for pilots over 40. The question asks for the number of unique planes. If multiple pilots over 40 fly the same plane, it will be counted multiple times.

### Item: `479` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts the total number of pilot-plane pairings, not the number of unique planes. It should use COUNT(DISTINCT plane_name) to avoid counting the same plane multiple times.
  - **gpt-5** (PARTIALLY_CORRECT): Counts pilot-plane rows; may double-count a plane if multiple pilots >40 fly it. Use COUNT(DISTINCT plane_name) to count unique planes.

### Item: `480` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is correct but might return duplicate pilot names if a pilot who meets the age criteria flies multiple planes. Using SELECT DISTINCT pilot_name would provide a unique list of pilots.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names if a pilot has multiple plane entries; use DISTINCT or group by pilot_name. Sorting by age is per row, not per unique pilot.

### Item: `481` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names because pilots can have multiple plane entries (composite PK). Use DISTINCT on pilot_name to list unique names ordered by age.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query should use SELECT DISTINCT pilot_name to return each pilot only once. A pilot may appear multiple times in the source table if they are skilled with multiple planes.

### Item: `482` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names since pilots can have multiple planes. Should deduplicate or aggregate per pilot (e.g., GROUP BY pilot_name ORDER BY MAX(age) DESC) to sort uniquely by age.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly sorts by age, but it may return duplicate pilot names if a pilot is associated with multiple planes. Using SELECT DISTINCT pilot_name would be more precise.

### Item: `483` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names if a pilot has multiple plane entries; likely need DISTINCT (and define per-pilot age) to list unique names ordered by age.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate pilot names if a pilot is associated with multiple planes. The question implies a unique list of pilots, which would require using SELECT DISTINCT.

### Item: `496` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot_name if a pilot has both planes; use SELECT DISTINCT to return unique pilots.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly filters for the specified planes. However, it may return duplicate pilot names if a pilot can fly both planes. Using SELECT DISTINCT would provide a unique list of pilots.

### Item: `497` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names if a pilot has both planes; use SELECT DISTINCT pilot_name to return unique names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies pilots for the specified planes, but it may return duplicate names if a pilot can fly both. Using SELECT DISTINCT would provide a unique list of pilots.

### Item: `505` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts and averages are over pilot-skill rows, not unique pilots per location. Missing DISTINCT can overcount and skew the average when a pilot is linked to multiple planes at the same location.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts pilot-skill records per location, not the number of distinct pilots. If a pilot can fly multiple planes housed in the same location, they will be counted multiple times. Using COUNT(DISTINCT T1.pilot_name) would be more precise.

### Item: `508` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate locations if multiple youngest pilots are associated with planes in the same location. Using SELECT DISTINCT would make the result more precise.
  - **gpt-5** (PARTIALLY_CORRECT): Semantics are right, but it may return duplicate locations if multiple youngest pilots or multiple planes share a location. Using DISTINCT on location would avoid duplicates.

### Item: `509` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate locations if multiple youngest pilots flew the same plane; add DISTINCT to avoid duplicates.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies planes flown by the youngest pilot(s). However, it may return duplicate locations if multiple youngest pilots fly the same plane. Using SELECT DISTINCT would be more precise.

### Item: `512` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names if a pilot has multiple plane entries; add DISTINCT to match “names of pilots” uniquely.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate pilot names if a pilot who meets the age criteria flies more than one type of plane. Using SELECT DISTINCT would be more precise for a list of names.

### Item: `514` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query should count distinct pilots using COUNT(DISTINCT pilot_name) instead of COUNT(*), as a single pilot who meets the age criteria but flies multiple planes would be counted more than once.
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows, not unique pilots; should use COUNT(DISTINCT pilot_name). Also MIN-based comparison fails when no 'F-14 Fighter' pilots exist (NULL), while universal quantification should return all pilots.

### Item: `516` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies pilots older than the youngest 'Piper Cub' pilot, but it counts pilot-plane records, not unique pilots. It should use COUNT(DISTINCT pilot_name) to avoid overcounting.
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows in pilotskills, not unique pilots. Should use COUNT(DISTINCT pilot_name) to get number of pilots. MIN(age) for “some” is correct.

### Item: `550` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Semantically correct but may return duplicate birth years if the same artist has multiple 1884 canvas paintings; DISTINCT would avoid duplicates.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing a DISTINCT keyword. If an artist created multiple paintings that satisfy the conditions, their birth year would be returned for each painting, leading to duplicate results.

### Item: `560` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return a row with NULL year (NULLs sort first) and only picks one if multiple paintings share the minimum year; better to filter NULL and handle ties.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query does not handle potential NULL values in the 'year' column. In SQLite, NULLs are sorted first in ascending order, so a painting with an unknown year could be incorrectly returned as the oldest.

### Item: `562` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing a DISTINCT keyword. If an artist has multiple sculptures with 'female' in the title, their name will be returned multiple times.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate artists if multiple matching sculptures exist; also matches substrings (e.g., 'femalesque') instead of the word 'female'.

### Item: `591` (DB: `car_road_race`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct filtering, but may return duplicate drivers across multiple races. Use DISTINCT to list unique winning drivers.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct but may return duplicate winning drivers. Using SELECT DISTINCT Winning_driver would provide a unique list of drivers as implied by the question.

### Item: `597` (DB: `car_road_race`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies races with drivers aged 26 or older, but it may return duplicate race names if a race has multiple drivers meeting the age criteria. Using SELECT DISTINCT is needed.
  - **gpt-5** (PARTIALLY_CORRECT): Logic and join are correct, but it may return duplicate race names if multiple qualifying drivers are linked to the same race. Using DISTINCT on Race_Name would ensure unique race names.

### Item: `613` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Missing DISTINCT; should return unique country–city pairs. Current query may include duplicates for multiple addresses with the same country and city.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly selects the country and city. However, it will return a row for every address, leading to duplicate country-city pairs. Adding DISTINCT would provide the unique list implied by the question.

### Item: `622` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies the age categories for the specified users. However, it may return duplicate age categories. Using SELECT DISTINCT would provide a unique list as implied by the question.
  - **gpt-5** (PARTIALLY_CORRECT): LIKE pattern "%Mother" only matches strings ending with 'Mother'; should be "%Mother%" to mean contains. Also may need DISTINCT to avoid duplicate age_category_code values across users.

### Item: `627` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate city names if multiple properties/features exist in the same city. Use DISTINCT or GROUP BY to return unique cities with a swimming pool.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly finds cities with properties that have a swimming pool, but it will return duplicate city names if a city has multiple such properties. Using SELECT DISTINCT would provide the unique list of cities implied by the question.

### Item: `628` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Missing DISTINCT on town_city; duplicates may appear if multiple properties or features exist in the same city. Use SELECT DISTINCT T2.town_city (or GROUP BY) to match the request.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly finds the cities that have properties with swimming pools. However, it should use SELECT DISTINCT to return each city only once, as a city could have multiple properties with this feature.

### Item: `675` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly selects flavors for croissants, but it may return duplicate flavor names. Using `SELECT DISTINCT flavor` would provide a unique list, which is likely the user's intent.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate flavors if multiple Croissant rows exist (e.g., different sizes). Use SELECT DISTINCT flavor to list unique flavors.

### Item: `676` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is correct but could return duplicate flavors. Using 'SELECT DISTINCT flavor' would be more precise to list each unique flavor only once.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate flavors; use SELECT DISTINCT flavor to list all unique croissant flavors.

### Item: `680` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing the DISTINCT keyword. If a customer buys multiple croissants on the same receipt, the receipt number will be returned multiple times.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate receipt numbers if a receipt has multiple croissant items. Use SELECT DISTINCT to ensure unique receipt numbers.

### Item: `734` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic and join are correct, but missing DISTINCT may return the same country multiple times if it has multiple qualifying drivers.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing a DISTINCT keyword. If a country has multiple drivers with more than 150 points, the country name will be listed multiple times in the result.

### Item: `735` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing the DISTINCT keyword. As a result, if a country has multiple drivers with more than 150 points, that country will be listed multiple times in the output.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate countries if multiple drivers from the same country have >150 points. Use DISTINCT, GROUP BY, or EXISTS to return each country only once.

### Item: `791` (DB: `university_rank`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is semantically correct but lacks a DISTINCT clause. If a university has multiple majors named 'Accounting' ranked 3 or higher, its name will appear multiple times in the result set.
  - **gpt-5** (PARTIALLY_CORRECT): Correct filters and joins, but may return duplicate university names if a university has multiple Accounting ranking rows (e.g., multiple ranks <= 3). Use SELECT DISTINCT.

### Item: `804` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate movie titles if a movie plays in both cinemas; add DISTINCT to return unique names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate movie titles if a movie is shown in both 'Odeon' and 'Imperial'. Using SELECT DISTINCT would provide a unique list of movies.

### Item: `805` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and filters, but may return duplicates if a movie appears in multiple matching theater rows; DISTINCT should be used to ensure unique titles.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate movie titles if a movie plays in both the 'Odeon' and 'Imperial' theaters. Using SELECT DISTINCT would provide a unique list of titles.

## ❌ Majority INCORRECT

**Found 174 queries where majority of voters said INCORRECT** (showing ALL)

These queries are likely semantically incorrect and need review.

### Item: `9` (DB: `soccer_3`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses INTERSECT, which finds countries that have players in both earning categories. The question asks for countries of players that satisfy either condition, which requires a UNION or an OR clause.
  - **gpt-5** (INCORRECT): Uses INTERSECT, returning only countries appearing in both groups. The request asks for countries of players either >1,400,000 or <1,100,000 (OR/UNION), not their overlap.

### Item: `11` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will exclude orders that have no items. The question asks for results 'For every order', which requires a LEFT JOIN from Orders to Order_items to include all orders.
  - **gpt-5** (INCORRECT): Uses INNER JOIN, so orders with no items are omitted. To answer “for every order,” use LEFT JOIN and count Order_items (e.g., COUNT(T2.order_item_id)) to include orders with zero products.

### Item: `15` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses EXCEPT on name fields instead of customer_id. If two customers share the same name and only one has orders, the tuple is removed, omitting the non-ordering customer. Use NOT EXISTS/LEFT JOIN on customer_id.
  - **gemini-2.5-pro** (INCORRECT): The query uses EXCEPT on customer names, which may not be unique. If a customer with no orders shares the same full name as a customer with an order, they will be incorrectly excluded from the result.

### Item: `17` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes products that have never been ordered (0 orders). It also counts order items (COUNT(*)) instead of distinct orders (COUNT(DISTINCT order_id)).
  - **gpt-5** (INCORRECT): Counts order_items rows, not distinct orders, and inner joins exclude products with zero orders. Should use LEFT JOIN and HAVING COUNT(DISTINCT t2.order_id) < 2 to match the question.

### Item: `20` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Query returns only one product due to LIMIT 1. The question asks for all products that are most frequently ordered (ties). Should select all products with the maximum order-item count.
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1`, which returns only one product. It fails to return all products in case of a tie for the most frequently ordered item, as requested by the plural 'products'.

### Item: `24` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner join excludes invoices with no shipments. Use a LEFT JOIN from Invoices to include all invoices’ statuses and dates, with NULL shipment_date where no shipment exists.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will only return invoices that have a shipment. The question asks for 'all invoices', so a LEFT JOIN is required to include those that have not been shipped.

### Item: `52` (DB: `bbc_channels`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns channels that have at least one director who is not 'Hank Baskett'. It will incorrectly include a channel if it is directed by 'Hank Baskett' and also by another director.
  - **gpt-5** (INCORRECT): WHERE t3.name != 'Hank Baskett' returns channels that have any non‑Hank director, not those with no Hank at all. It also excludes channels with no directors due to inner joins.

### Item: `53` (DB: `tv_shows`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `ERP_kW` column is of type TEXT. The query will perform a lexicographical (alphabetical) sort, not a numerical sort as implied by the question. For example, '100' would be sorted before '20'.
  - **gpt-5** (INCORRECT): ERP_kW is stored as TEXT; ORDER BY erp_kw will sort lexicographically, not numerically. To order by ERP kW ascending, it should cast/convert ERP_kW to a number before ordering.

### Item: `55` (DB: `tv_shows`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The ERP_kW column is of type TEXT. The query performs a lexicographical (alphabetical) sort, but a numerical sort is required to correctly identify the largest value.
  - **gpt-5** (INCORRECT): ERP_kW is TEXT; ORDER BY sorts lexicographically, not numerically, and may rank values like '100' < '99' or even 'N/A' highest. CAST to numeric (e.g., CAST(ERP_kW AS REAL)) or use MAX().

### Item: `69` (DB: `vehicle_driver`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Compares by model, not vehicle instance. If any vehicle of a model was driven, the model is excluded even if other vehicles of that model were never driven. Should anti-join on Vehicle_ID.
  - **gemini-2.5-pro** (INCORRECT): The query finds models for which *no vehicle of that model* has ever been driven. The question asks for the models of *any specific vehicle* that has never been driven. The query incorrectly eliminates a model if at least one vehicle of that model has been driven.

### Item: `70` (DB: `vehicle_driver`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner join/groups on vehicle_driver exclude Ziyang-built vehicles with no driver records. Query should include builder='Ziyang' vehicles even without drivers (use LEFT JOIN or UNION).
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes vehicles that have no drivers. This means a vehicle built by 'Ziyang' but never driven will be incorrectly omitted from the results.

### Item: `71` (DB: `vehicle_driver`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which filters out vehicles with no drivers. Consequently, the condition `T1.builder = 'Ziyang'` is only checked for vehicles that have been driven, missing Ziyang-built vehicles with zero drivers.
  - **gpt-5** (INCORRECT): Inner join and GROUP BY on vehicle_driver exclude Ziyang-built vehicles with no driver rows; should use LEFT JOIN and count distinct drivers per vehicle (group by vehicle_id).

### Item: `103` (DB: `region_building`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses region.Capital instead of region.Name. Should return the building address and the region name (T1.Address, T2.Name).
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly selects the region's capital (`T2.Capital`) instead of the region's name (`T2.Name`) as requested by the question.

### Item: `116` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by customer_details, which may not be unique, merging different customers and miscounting. Should group by Customer_ID (and select its details) to identify the top user correctly.
  - **gemini-2.5-pro** (INCORRECT): The query groups by `customer_details`, which is not guaranteed to be unique. If multiple customers share the same details, their service counts will be incorrectly combined. Grouping should be by `t1.customer_id`.

### Item: `117` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by customer_details, which may not be unique, merging different customers. Also counts rows instead of distinct services. Should group by customer_id and use COUNT(DISTINCT service_id).
  - **gemini-2.5-pro** (INCORRECT): The query groups by `customer_details` instead of the unique customer identifier `Customer_ID`. If two different customers share the same details, their service counts will be incorrectly combined.

### Item: `118` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of service usages with COUNT(*), but the question asks for the most 'types of services', which requires counting the distinct services, i.e., COUNT(DISTINCT T2.Service_ID).
  - **gpt-5** (INCORRECT): Should count distinct Service_ID per customer. Query uses COUNT(*) and may double-count usages. Also groups by customer_details, merging same-name customers; should group by customer_id.

### Item: `122` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The subquery incorrectly counts service usage from the `services` table instead of the `customers_and_services` table. This will not correctly identify the least-used service.
  - **gpt-5** (INCORRECT): Counts rows in services (always 1 per service), not actual usage. Should group by service_id in customers_and_services to find least-used (and handle ties, e.g., with IN).

### Item: `123` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The subquery incorrectly identifies the least used service by counting entries in the `services` table. It should count service usage from the `customers_and_services` table.
  - **gpt-5** (INCORRECT): Counts are taken from services (count(*)=1 per service), not usage in customers_and_services. Also picks a single service_id, ignoring ties among least-used services.

### Item: `125` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly joins all four tables. This requires a service to both be used by a customer and have an interaction to be considered, which is not what the question asks. The two conditions should be independent.
  - **gpt-5** (INCORRECT): Inner join to customer_interactions filters out Hardy’s used services with no interactions, and it also requires ‘good’-rated services to exist in customers_and_services. Should UNION the two sets or use LEFT JOINs.

### Item: `132` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Missing join between integration_platform and customer_interactions; this creates a CROSS JOIN and can return all customers whenever any 'Fail' exists. Should join on Customer_Interaction_ID.
  - **gemini-2.5-pro** (INCORRECT): The query is missing the JOIN condition between the `customer_interactions` and `integration_platform` tables. It should join on `customer_interaction_id` to correctly link customers to their specific interactions.

### Item: `142` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The second part of the UNION incorrectly finds students with less than 2 detentions. It uses an INNER JOIN, which excludes students with zero detentions, thus only returning students with exactly one detention.
  - **gpt-5** (INCORRECT): Students with 0 detentions are excluded due to INNER JOIN on Detention. Use LEFT JOIN (count of detention rows) to include zero-detention students for the “< 2 detentions” group.

### Item: `143` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The second part of the UNION uses an INNER JOIN on the Detention table, which incorrectly excludes students with zero detentions. The condition 'less than two detentions' includes students with 0 or 1.
  - **gpt-5** (INCORRECT): Misses students with 0 detentions. The second SELECT uses an INNER JOIN, so COUNT(*)<2 only captures students with exactly 1 detention. Use LEFT JOIN or counts including 0 to include <2.

### Item: `153` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts DISTINCT student_id but orders by count(*). The question asks for the occurrence count of each behaviour_monitoring_details. Should select count(*) with the details; current count value is wrong.
  - **gemini-2.5-pro** (INCORRECT): The query orders by the total count of records (`count(*)`) to find the most common detail, but it selects the count of distinct students (`count(DISTINCT student_id)`). The selected count does not match the metric used for ordering.

### Item: `156` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly finds students who *only* have the most common behaviour detail. The `EXCEPT` clause wrongly removes students who have the most common detail in addition to other details.
  - **gpt-5** (INCORRECT): EXCEPT removes students who also have any non-mode detail, but the question only requires students who have the most common detail. Also LIMIT 1 picks a single mode and ignores ties.

### Item: `158` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts event rows, not distinct students. Should use COUNT(DISTINCT T2.student_id) per event type. Join to Students is unnecessary. Overcounts if a student has multiple events of the same type.
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of event participations using COUNT(*). The question asks for the number of unique students, which requires using COUNT(DISTINCT T1.student_id).

### Item: `167` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query finds only one teacher associated with the earliest transcript record, not all teachers of the student who has the earliest transcript. The `LIMIT 1` incorrectly restricts the final result to a single teacher.
  - **gpt-5** (INCORRECT): Uses ORDER BY/LIMIT to pick a single joined row. It doesn’t restrict to the student(s) with the minimum transcript date nor return all their teachers. Should filter by MIN(date) and return DISTINCT teachers.

### Item: `168` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `ORDER BY ... LIMIT 1` on the joined result, which returns only one teacher. It fails to find all teachers who taught the student with the earliest transcript if that student had multiple.
  - **gpt-5** (INCORRECT): Returns only one teacher due to LIMIT 1 and doesn’t target the student(s) with the minimum transcript date. Should filter on MIN(date_of_transcript) and return all matching teachers (use DISTINCT if needed).

### Item: `180` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will exclude authors who have not written any books. The question asks for 'all the authors', so a LEFT JOIN is required to include authors with a book count of zero.
  - **gpt-5** (INCORRECT): Inner join omits authors with zero books. Use LEFT JOIN from Author to Author_Book and COUNT(T2.ISBN) to include all authors with zero counts.

### Item: `188` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): INNER JOIN excludes clients with no orders, contradicting “all the clients.” Use LEFT JOIN from Client to Orders and count orders (e.g., COUNT(T1.IdOrder)) to include zero-order clients.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will exclude clients who have not placed any orders. The question asks for 'all the clients', which implies clients with zero orders should also be returned.

### Item: `200` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1`, which will only return one book title. It fails to retrieve all titles if multiple books share the same lowest sale price, as requested by the question.
  - **gpt-5** (INCORRECT): Uses ORDER BY ... LIMIT 1, returning only one title. The question asks for all titles at the minimum sale price; should filter by saleprice = (SELECT MIN(saleprice) FROM book).

### Item: `201` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `ORDER BY ... LIMIT 1`, which will only return a single book title. It fails to return all titles if multiple books share the same lowest sale price, as requested by the question.
  - **gpt-5** (INCORRECT): Uses ORDER BY ... LIMIT 1, returning only one title. The question requires all books with the minimum sale price (including ties); should filter by saleprice = (SELECT MIN(saleprice) FROM book).

### Item: `202` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses ORDER BY ... LIMIT 1, returning only one title. It fails to include all titles tied for the highest PurchasePrice; should filter titles where PurchasePrice equals the max.
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1`, which will only return a single book title. It fails to retrieve all titles if multiple books share the same highest purchase price.

### Item: `203` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns only one title due to LIMIT 1. Must return all books with the maximum PurchasePrice (handle ties), e.g., WHERE PurchasePrice = (SELECT MAX(PurchasePrice) FROM book).
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1`, which will only return a single book title. It fails to return all titles in the case where multiple books share the same highest purchase price.

### Item: `221` (DB: `book_review`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the overall maximum and minimum chapters across all books, but the question asks for this information 'for each book', which requires grouping by a book identifier.
  - **gpt-5** (INCORRECT): Returns overall max/min chapters across all books, not per book. Needs GROUP BY (e.g., Book_ID or Title) to report max and min for each book.

### Item: `235` (DB: `restaurant_bills`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for card credit less than 50 and greater than 75. The question asks for nations with customers having credit `above 50` and `below 75`.
  - **gpt-5** (INCORRECT): Wrong thresholds in WHERE clauses. Query uses Card_Credit < 50 and > 75, but the question requires > 50 and < 75 to find nations having both categories.

### Item: `236` (DB: `restaurant_bills`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query groups by customer name, which is not guaranteed to be unique. If multiple customers share the same name, their order quantities will be incorrectly aggregated together. Grouping should be by `Customer_ID`.
  - **gpt-5** (INCORRECT): Groups by Name only, merging different customers with same name. Also uses INNER JOIN, excluding customers with no orders. Should group by Customer_ID (and Name) and use LEFT JOIN with COALESCE.

### Item: `238` (DB: `restaurant_bills`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query groups by customer name, which is not guaranteed to be unique. If two different customers share the same name, their order quantities will be incorrectly summed together, leading to wrong results.
  - **gpt-5** (INCORRECT): Groups by Name, which can merge different customers sharing the same name and yield wrong totals. Should group by Customer_ID (and optionally Name) to compute per-customer sum(Quantity) > 1.

### Item: `240` (DB: `club_leader`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query performs a case-sensitive comparison with the literal "england". It will fail to exclude records where the nationality is 'England' (with a capital E), which contradicts the question's intent.
  - **gpt-5** (INCORRECT): Case-sensitive comparison uses "england" instead of "England", so rows with nationality = 'England' won’t be excluded. Use proper case or a case-insensitive comparison.

### Item: `243` (DB: `club_leader`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filter is reversed: query uses Overall_Ranking < 100, but the question asks for higher than 100 (> 100). It also returns Club_Name though only leader names were requested.
  - **gemini-2.5-pro** (INCORRECT): The query filters for clubs with an overall ranking less than 100 (`Overall_Ranking < 100`), but the question asks for clubs with a ranking 'higher than 100'.

### Item: `254` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Wrong column selected. The query returns Parent_Document_Object_ID, but the question asks for Document_Object_ID of objects owned by Marlin.
  - **gemini-2.5-pro** (INCORRECT): The query selects the Parent_Document_Object_ID, but the question asks for the Document_Object_ID of the objects owned by 'Marlin'.

### Item: `263` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query finds documents owned by 'Ransom' but returns their own IDs. It should join on one ID column from `document_subset_members` to find Ransom's documents and select the other ID column to find the related documents.
  - **gpt-5** (INCORRECT): Returns IDs of Ransom-owned documents, not the documents related to them. Should filter by owner on one side and output the opposite side (e.g., select related_document_object_id); may need DISTINCT/bidirectional handling.

### Item: `264` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query selects `t1.document_object_id`, which is the ID of the document owned by 'Ransom'. The question asks for the IDs of the documents *related to* the ones owned by 'Ransom', which should be `t1.Related_Document_Object_ID`.
  - **gpt-5** (INCORRECT): Selects t1.document_object_id instead of the related IDs. Should return Related_Document_Object_ID for rows where Document_Object_ID belongs to owner 'Ransom'. Also uses 'ransom' (wrong case).

### Item: `267` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses INNER JOIN and LIMIT 1, returning only the parent with the most children and excluding parents with zero children. Should list all Document_Object_IDs with child counts (use LEFT JOIN) and no LIMIT.
  - **gemini-2.5-pro** (INCORRECT): The query includes `ORDER BY count(*) DESC LIMIT 1`, which incorrectly returns only the single document object with the most children. The question asks for the count for *each* document object.

### Item: `270` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query selects the owner of the document that is already filtered to be 'Braeden'. It should join the Document_Objects table again on T1.Document_Object_ID to find the owner of the related document.
  - **gpt-5** (INCORRECT): Selects T2.Owner (the Braeden docs) instead of owners of the related docs. Needs a join from T1.Document_Object_ID to Document_Objects and select that Owner (and possibly handle both relation directions).

### Item: `271` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects T2.Owner (the Braeden-owned related doc), yielding ‘Braeden’. It should return owners of the other documents in the relation, requiring a join to the opposite side’s Document_Objects.
  - **gemini-2.5-pro** (INCORRECT): The query finds documents owned by 'Braeden' but then returns 'Braeden' as the owner, instead of finding the owners of the documents they are related to via the `Document_Subset_Members` table.

### Item: `276` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query orders the results by `count(*)`, which is the total number of member entries. It should order by `count(distinct t1.document_object_id)` to find the subset with the most distinct documents.
  - **gpt-5** (INCORRECT): Orders by COUNT(*) instead of COUNT(DISTINCT document_object_id), so the subset ranking can be wrong when duplicates exist. It should order by the distinct count used in SELECT.

### Item: `277` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query orders the results by `count(*)`, which is the total number of members in a subset. The question asks for the subset with the most *different* documents, so the ordering should be by `count(distinct t1.document_object_id)`.
  - **gpt-5** (INCORRECT): Orders by count(*) instead of distinct document count, and counts only Document_Object_ID. Should count unique documents across both Document_Object_ID and Related_Document_Object_ID and order by that.

### Item: `281` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly self-joins `document_subset_members`. It finds the subsets that a related document belongs to, not the subsets that the original document belongs to as requested by the question.
  - **gpt-5** (INCORRECT): Self-join pulls subset names from the related document’s memberships (t2), not from each document’s own subset relations. Should join document_subsets using t1.document_subset_id.

### Item: `282` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause filters for the owner 'ransom', but the question specifies the owner 'Ransom ' with a trailing space. This mismatch will lead to incorrect filtering.
  - **gpt-5** (INCORRECT): WHERE clause uses 'ransom' (lowercase, no trailing space) instead of 'Ransom ' from the question, risking no matches. Also may need DISTINCT to avoid duplicate collection names.

### Item: `286` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns a list of document object IDs, but the question asks for the count (the number) of them. The query is missing the COUNT() aggregation function.
  - **gpt-5** (INCORRECT): Returns list of Document_Object_IDs, not the count. Should aggregate with COUNT for rows where Collection_Name = 'Best'.

### Item: `287` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for a specific collection with `WHERE T1.Collection_Name = "Best"`. The question asks to find the collection with the most documents among all collections.
  - **gpt-5** (INCORRECT): Adds WHERE Collection_Name='Best', restricting to one collection. The task is to find the max across all collections. Remove the filter and aggregate per collection, then order by count DESC.

### Item: `292` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses INNER JOINs across all tables, which incorrectly requires a document to be in both a document subset AND a collection. The question asks for documents in either one OR the other.
  - **gpt-5** (INCORRECT): Inner joins force documents to exist in both a subset and a collection. This fails the OR logic. Should UNION results from the subset and the collection (or use LEFT JOIN/EXISTS) to include either set.

### Item: `293` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses INNER JOINs, which requires a document to be in both a subset and a collection. The question asks for documents that are in either the specified subset OR the specified collection.
  - **gpt-5** (INCORRECT): Inner joins force intersection, excluding docs that are only in the subset or only in the 'Best' collection. Also only selects Document_Object_ID, ignoring Related_Document_Object_ID from subset membership.

### Item: `294` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Unnecessary self-join on Collection_Subset_Members (T1→T2) restricts results to related collections that themselves appear as Collection_ID in another row, potentially omitting valid related collections.
  - **gemini-2.5-pro** (INCORRECT): The query only finds collections where 'Best' is the Collection_ID. It fails to find related collections where 'Best' is the Related_Collection_ID, thus missing half of the potential results.

### Item: `295` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Unnecessary self-join on Collection_Subset_Members (T2) restricts results to related collections that also appear as Collection_ID, potentially excluding valid ones. Should join T4 on T1.Related_Collection_ID.
  - **gemini-2.5-pro** (INCORRECT): The query only finds collections where 'Best' is the `Collection_ID` in the relationship table. It fails to find related collections where 'Best' is the `Related_Collection_ID`, thus providing an incomplete answer.

### Item: `303` (DB: `sing_contest`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `WHERE language = 'English'`, which will only match songs exclusively in English. Based on the schema's example data ('English , Russian'), a `LIKE '%English%'` condition is needed to correctly identify all songs that include English.
  - **gpt-5** (INCORRECT): Language field can contain multiple languages (e.g., 'English , Russian'); using = 'English' misses those. Should use a contains check like WHERE T3.language LIKE '%English%'.

### Item: `304` (DB: `sing_contest`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `language = 'Croatian'` for an exact match. The schema example `language TEXT /* ex: ['English , Russian'] */` suggests the column can contain multiple languages, so the query should use `LIKE '%Croatian%'` instead.
  - **gpt-5** (INCORRECT): Intersects on (name,popularity) instead of participant_id, so different participants sharing those values can falsely match. Also uses '=' on songs.language; should use LIKE to match multi-language entries.

### Item: `317` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only checks for the distance in one direction (BAL to CHI). It fails to consider the reverse direction (CHI to BAL), which would also answer the question about the distance 'between' the two cities.
  - **gpt-5** (INCORRECT): The query assumes a specific direction (BAL->CHI). The question is order-agnostic; it should consider both (BAL, CHI) and (CHI, BAL) to ensure the distance is found.

### Item: `318` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only checks for the distance in one direction (Boston to Newark). It fails to consider the case where the distance is stored from Newark to Boston, which would also answer the question.
  - **gpt-5** (INCORRECT): Only matches Boston as city1 and Newark as city2. “Between” should be order-agnostic; must allow both (Boston, Newark) and (Newark, Boston) pairs.

### Item: `319` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only checks for the distance in one direction (Boston to Newark). It fails to consider the reverse direction (Newark to Boston), which is also implied by the question 'distance between'.
  - **gpt-5** (INCORRECT): Only matches Boston as city1 and Newark as city2; the question is orderless. Should consider both directions (Boston–Newark or Newark–Boston) to avoid missing the distance.

### Item: `327` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where 'BAL' is the origin city (city1_code). It misses cases where 'BAL' is the destination city (city2_code), resulting in an incomplete sum.
  - **gpt-5** (INCORRECT): Filters only city1_code='BAL'. To sum distances between BAL and other cities, it should include rows where BAL appears in either city1_code or city2_code (and exclude BAL-BAL if present).

### Item: `328` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where Boston is in the `city1_code` column. It fails to find distances where Boston's code is in the `city2_code` column, leading to an incomplete and incorrect result.
  - **gpt-5** (INCORRECT): Filters only where Boston is city1_code, missing rows where Boston is city2_code, and doesn’t exclude potential Boston-to-Boston rows. Must consider both sides and exclude self to average over all other cities.

### Item: `329` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where Boston is in the `city1_code` column. It fails to check for cases where Boston is in the `city2_code` column, resulting in an incomplete calculation.
  - **gpt-5** (INCORRECT): Only filters rows where Boston is city1. Should include pairs where Boston is either city1 or city2 and exclude any Boston–Boston self-pair to get the average to other cities.

### Item: `330` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers cases where Chicago is `city1_code`. It fails to check for distances where Chicago is `city2_code`, potentially missing the correct closest city if the data is not symmetric.
  - **gpt-5** (INCORRECT): Considers only rows where Chicago is city1; misses cases where Chicago is city2. Also doesn’t exclude self-pairs, so it could return “Chicago” if a 0-distance self-row exists.

### Item: `331` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query will incorrectly return 'Chicago' if the dataset contains a distance entry from Chicago to itself (with distance 0), as it does not exclude the origin city from the potential results.
  - **gpt-5** (INCORRECT): Considers only rows where Chicago is city1_code. It should handle both city1_code and city2_code to capture all distances from Chicago and then choose the nearest other city.

### Item: `333` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Only checks rows where Boston is city1; distances where Boston is city2 are ignored. Must consider both directions to find the farthest city from Boston.
  - **gemini-2.5-pro** (INCORRECT): The query only considers cases where Boston is in the `city1_code` column. It will miss the correct answer if the greatest distance from Boston is in a row where Boston is listed in the `city2_code` column.

### Item: `334` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only sums distances where a city is in the `city1_code` column. It fails to include distances where the city is in the `city2_code` column, thus not calculating the total distance to all other cities.
  - **gpt-5** (INCORRECT): Aggregates only by city1_code, so cities appearing only as city2_code are missing. Also doesn’t exclude self-pairs; “to all other cities” should omit city1_code = city2_code.

### Item: `339` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only finds the distance if Linda's city is city1 and Tracy's is city2. It fails to consider the reverse case where Tracy's city is city1 and Linda's is city2.
  - **gpt-5** (INCORRECT): Joins assume Linda’s city is city1 and Tracy’s is city2. If Direct_distance stores the pair in reverse order, the query returns no result. It should allow either city ordering.

### Item: `341` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly assumes Linda Smith's city is always in the `city1_code` column of the `Direct_distance` table. It fails to check for her city in the `city2_code` column, potentially missing the correct answer.
  - **gpt-5** (INCORRECT): Only matches distances where Linda’s city is in city1_code; misses reversed rows where it’s in city2_code. Must consider both directions (e.g., UNION/OR) to find the true farthest student.

### Item: `347` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Wrong aggregation: uses MIN. “Older than any” means older than all, so age > MAX(age) (or > ALL). Current query only checks > MIN and also returns none if no rating > 7 exists.
  - **gemini-2.5-pro** (INCORRECT): The question asks for sailors older than *any* sailor with a rating > 7, which implies being older than *all* of them. The query should use MAX(age) in the subquery, but it incorrectly uses MIN(age).

### Item: `349` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of reservations per sailor (COUNT(*)), not the number of distinct boats. It should use COUNT(DISTINCT T2.bid) > 1 to correctly identify sailors who reserved more than one boat.
  - **gpt-5** (INCORRECT): Counts reservations instead of distinct boats; a sailor reserving the same boat multiple times would be wrongly included. Should use COUNT(DISTINCT T2.bid) > 1 and group by sid.

### Item: `350` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts reservations per sailor, not distinct boats. Should use COUNT(DISTINCT t2.bid) >= 2; also ideally return only names as requested.
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of reservations using `COUNT(*)`, but the question asks for sailors who reserved two or more distinct boats. The aggregation should be `COUNT(DISTINCT T2.bid)`.

### Item: `351` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The phrase 'higher than any sailor named Luis' implies the rating must be greater than the rating of *every* sailor named Luis. The query should use MAX(rating) in the subquery, not MIN(rating).
  - **gpt-5** (INCORRECT): Uses MIN(rating) for Luis; should compare to MAX(rating) or use > ALL to ensure rating is higher than every Luis. Current query returns sailors only higher than the lowest-rated Luis.

### Item: `352` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses MIN(rating), so it finds sailors rated above the lowest Luis, not above every Luis. Should compare to MAX(rating) or use > ALL (SELECT rating ...).
  - **gemini-2.5-pro** (INCORRECT): The question 'higher than any sailor named Luis' implies a rating greater than the maximum rating among all sailors named Luis. The query incorrectly compares against the minimum rating.

### Item: `370` (DB: `headphone_store`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Condition is reversed. HAVING count(*) > 2 returns classes with more than two headphones; it should be HAVING count(*) <= 2 to find classes that do not exceed two.
  - **gemini-2.5-pro** (INCORRECT): The query finds classes with more than two headphones (HAVING count(*) > 2), but the question asks for classes that do not contain more than two headphones (i.e., HAVING count(*) <= 2).

### Item: `379` (DB: `headphone_store`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Date_Opened` column is of type TEXT with a format like 'Month Day, Year'. Sorting this column alphabetically will not result in a correct chronological order.
  - **gpt-5** (INCORRECT): Orders by Date_Opened as TEXT, causing lexicographic not chronological sort for values like 'October 29, 2005'. Needs proper date parsing/casting to sort by actual open date.

### Item: `380` (DB: `headphone_store`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query is incorrect because the `date_opened` column is of type TEXT. Ordering by this column will result in an alphabetical sort (e.g., 'June' before 'October'), not a chronological sort as the question requires.
  - **gpt-5** (INCORRECT): Orders by Date_Opened as TEXT, which sorts lexicographically (e.g., by month name) rather than chronologically. Needs date parsing/casting to sort by actual open date.

### Item: `390` (DB: `headphone_store`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query fails to check the 'Quantity' column in the 'stock' table. It incorrectly assumes that any entry in the stock table means items are in stock, even if the quantity is zero.
  - **gpt-5** (INCORRECT): Excludes neighborhoods based on any stock row, ignoring Quantity. Should exclude only if any store in the neighborhood has Quantity > 0; neighborhoods with only zero stock should be included.

### Item: `394` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns distinct pairs of (venue, year), which allows a single venue to appear multiple times in the result. The question asks for a list of distinct venues, meaning each venue should appear only once.
  - **gpt-5** (INCORRECT): Returns distinct (venue, year) pairs, not distinct venues. Ordering venues by year requires picking one year per venue (e.g., MIN(year)) and selecting only venue.

### Item: `401` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause searches for author names with extra spaces around the comma (e.g., 'Mckeown , Kathleen'), which does not match the names specified in the natural language question ('Mckeown, Kathleen').
  - **gpt-5** (INCORRECT): WHERE filters use wrong name strings with extra spaces around the comma (e.g., 'Mckeown ,  Kathleen'). Should match 'Mckeown, Kathleen' or 'Rambow, Owen', otherwise papers won’t be selected correctly.

### Item: `404` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query orders the results in descending order, but the question asks for ascending order. Additionally, the aggregation COUNT(*) counts the number of authors per affiliation, not the number of distinct papers.
  - **gpt-5** (INCORRECT): Orders DESC instead of ascending; counts Author_list rows (authors) rather than distinct papers; inner join excludes affiliations with zero papers.

### Item: `405` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts author-affiliation rows, not distinct papers, and inner join drops affiliations with zero papers. Should use LEFT JOIN and COUNT(DISTINCT paper_id) to include all affiliations and count papers.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly orders by the count of authorships (COUNT(*)) instead of the number of unique papers. It should use COUNT(DISTINCT T2.paper_id) to correctly count the papers for each affiliation.

### Item: `411` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by cited_paper_id but selects paper_id, returning an arbitrary citing paper. Should select cited_paper_id with its count to identify the most cited paper.
  - **gemini-2.5-pro** (INCORRECT): The query selects `paper_id` (the citing paper) instead of `cited_paper_id` (the cited paper). The question asks for the ID of the most cited paper, which is `cited_paper_id`.

### Item: `412` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query selects `paper_id` (the citing paper) but groups by `cited_paper_id`. To return the ID of the most cited paper, it should select `cited_paper_id`.
  - **gpt-5** (INCORRECT): Selects paper_id while grouping by cited_paper_id, returning an arbitrary citing paper’s id. Should select cited_paper_id with COUNT(*) to get the most-cited paper and its citation count.

### Item: `414` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects paper_id while grouping by cited_paper_id. The result shows a non-deterministic citing paper, not the cited paper. Should select cited_paper_id with COUNT(*) to get most cited papers.
  - **gemini-2.5-pro** (INCORRECT): The query correctly groups by `cited_paper_id` to count citations, but it incorrectly selects `paper_id` (the citing paper) instead of `cited_paper_id` (the paper that was cited).

### Item: `415` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects paper_id while grouping by cited_paper_id. It should return cited_paper_id with COUNT(*); current query may show arbitrary paper_id and wrong papers as most cited.
  - **gemini-2.5-pro** (INCORRECT): The query correctly groups by `cited_paper_id` to count citations, but it incorrectly selects `paper_id` (the citing paper) instead of `cited_paper_id` (the paper that was cited).

### Item: `432` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts author-list rows (authors per paper) instead of papers. Should aggregate by COUNT(DISTINCT T2.paper_id) for affiliations with address LIKE '%China%'.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of author-paper associations (`count(*)`) instead of the number of distinct papers (`COUNT(DISTINCT T2.paper_id)`), which could lead to an incorrect result.

### Item: `438` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner query groups by cited_paper_id but selects T2.author_id, so it returns only one arbitrary author per highly cited paper, missing coauthors. Should collect all authors of papers with >50 citations.
  - **gemini-2.5-pro** (INCORRECT): The subquery incorrectly identifies authors of highly-cited papers. By grouping by paper ID but selecting author ID, it will only return one arbitrary author for a co-authored paper, not all of them.

### Item: `439` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Subquery groups by cited_paper_id but selects author_id without grouping, yielding only one arbitrary author per highly cited paper and missing co-authors. This wrongly counts some co-authors as not having such papers.
  - **gemini-2.5-pro** (INCORRECT): The subquery groups by paper to find those with >50 citations, but then selects `author_id`. For a paper with multiple authors, this non-deterministically returns only one author, not all of them.

### Item: `448` (DB: `conference`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The user asks for the count of staff members and their names. The query only returns the count of staff members but omits their names.
  - **gpt-5** (INCORRECT): Missing institution_id in SELECT; returns institution names instead of staff names if that’s intended; INNER JOIN omits institutions with zero staff—should use LEFT JOIN for complete counts.

### Item: `451` (DB: `conference`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Missing WHERE filter for nationality. It returns max/min ages for all staff, not restricted to those from the United States.
  - **gemini-2.5-pro** (INCORRECT): The query is missing a WHERE clause to filter for staff from the 'United States'. It calculates the max and min age for all staff, not just those from the specified country.

### Item: `461` (DB: `conference`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filters out participating staff, not institutions. It can return institutions that had some staff participate in 2004 via other staff. Also inner join omits institutions with no staff. Should exclude by institution.
  - **gemini-2.5-pro** (INCORRECT): The query returns institutions that have at least one staff member who did not participate in a 2004 conference. It should return institutions where *no* staff members participated in any 2004 conference.

### Item: `462` (DB: `conference`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns institutions if they have at least one staff member who did not participate in a 2004 conference. It should only return institutions where *no* staff members participated at all.
  - **gpt-5** (INCORRECT): Filters per staff, not per institution; it returns universities if any staff didn’t participate even if others did. Also uses INNER JOIN, omitting institutions with no staff, and can produce duplicates.

### Item: `486` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an ORDER BY clause for filtering instead of a WHERE clause. The condition on age should be used to filter the rows before the count aggregation is applied.
  - **gpt-5** (INCORRECT): Uses ORDER BY instead of WHERE, so no filtering occurs; also counts rows (pilot-plane pairs) rather than distinct pilots. Should count DISTINCT pilot_name with age > 40 OR age < 30.

### Item: `487` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses ORDER BY for the age condition instead of WHERE, so no filtering is applied. Also counts rows, not distinct pilots; should use COUNT(DISTINCT pilot_name) with the age filter.
  - **gemini-2.5-pro** (INCORRECT): The query uses an ORDER BY clause for filtering, which is incorrect. The condition `age > 40 OR age < 30` should be in a WHERE clause to filter the rows before counting.

### Item: `494` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average age over all rows in the table. Since a pilot can appear multiple times, their age will be counted more than once, leading to an incorrect average pilot age.
  - **gpt-5** (INCORRECT): Aggregates over all rows in pilotskills, potentially counting pilots multiple times. Should aggregate per pilot (e.g., GROUP BY pilot_name) before computing average and minimum across pilots.

### Item: `499` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query correctly finds the maximum age for each plane but selects an arbitrary pilot_name from the group, not necessarily the pilot corresponding to that maximum age.
  - **gpt-5** (INCORRECT): pilot_name is neither grouped nor linked to max(age); SQLite may return any pilot in the group, not necessarily the oldest. Need to restrict pilot_name to the row(s) with the max age per plane.

### Item: `500` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Non-aggregated pilot_name with GROUP BY plane_name is arbitrary in SQLite; it may not correspond to the max(age). Also fails to return all pilots in case of ties for oldest per plane.
  - **gemini-2.5-pro** (INCORRECT): The query correctly finds the maximum age for each plane but fails to select the corresponding pilot's name. The selected 'pilot_name' is from an arbitrary row within the group, not the one associated with the max age.

### Item: `501` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): pilot_name is not linked to the max(age) per plane_name; with GROUP BY plane_name only, SQLite can return an arbitrary pilot. It also fails to include all tied oldest pilots.
  - **gemini-2.5-pro** (INCORRECT): The query selects a non-aggregated column `pilot_name` which is not in the GROUP BY clause. This returns an arbitrary pilot name for each plane, not necessarily the one corresponding to the max age.

### Item: `502` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): pilot_name is neither grouped nor tied to max(age); SQLite may return an arbitrary pilot per plane, not the oldest. Also fails to return all oldest pilots when ties occur. Use join to max(age).
  - **gemini-2.5-pro** (INCORRECT): The query correctly finds the maximum age per plane, but the selected `pilot_name` is arbitrary and not guaranteed to be the pilot associated with that maximum age.

### Item: `513` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses MIN(age), returning pilots older than the youngest Piper Cub pilot. Must be older than every Piper Cub pilot: age > (SELECT MAX(age) ...). Also consider DISTINCT to avoid duplicate names.
  - **gemini-2.5-pro** (INCORRECT): The question asks for pilots older than *any* pilot who flew a 'Piper Cub', which implies being older than the *oldest* of that group. The query incorrectly compares against the *youngest* pilot's age (`min(age)`).

### Item: `519` (DB: `district_spokesman`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Sums population over all districts. ORDER BY/LIMIT occur after aggregation. Needs subquery to select top 3 by area_km before SUM.
  - **gemini-2.5-pro** (INCORRECT): The query calculates the SUM of the population for the entire table. The ORDER BY and LIMIT clauses are applied after the aggregation, not before, so they do not filter the rows that are being summed.

### Item: `551` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Adds an unnecessary filter mediumOn='canvas'. The question asks for artists with any painting in 1884, regardless of medium/support; this extra condition can exclude correct results.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly adds a filter `mediumOn = "canvas"`, which is not specified in the natural language question and could lead to an incomplete or wrong answer.

### Item: `572` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Aggregating max(height_mm) while selecting paintingID without GROUP BY returns an arbitrary ID, not the ID of the tallest pre-1900 painting. It doesn’t link the ID to the max height.
  - **gemini-2.5-pro** (INCORRECT): The query returns the overall maximum height but an arbitrary paintingID from the filtered rows, not the ID of the painting that actually has the maximum height.

### Item: `573` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects MAX(height_mm) with a non-aggregated paintingID, so the ID may not correspond to the tallest painting. Use ORDER BY height_mm DESC LIMIT 1 or a subquery to tie ID to the max.
  - **gemini-2.5-pro** (INCORRECT): The query correctly finds the maximum height but fails to return the corresponding `paintingID`. The `paintingID` returned will be from an arbitrary row that meets the WHERE clause, not necessarily the one with the maximum height.

### Item: `578` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes artists with zero paintings. The condition 'at most 3 paintings' should include artists with 0 paintings, but the query only considers those with at least one.
  - **gpt-5** (INCORRECT): Inner join excludes artists with 0 paintings. “At most 3” includes zero. Should use LEFT JOIN and count of paintings <= 3 (e.g., COUNT(T2.paintingID)).

### Item: `579` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner join excludes artists with 0 paintings, yet 0 < 4 should be included. Use LEFT JOIN from artists to paintings and count paintings per artist.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes artists who have created zero paintings. The condition 'less than 4 paintings' should also include artists with no paintings in the database.

### Item: `580` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes artists who have made zero sculptures. The artist with the 'least number' could have zero, so a LEFT JOIN is required to include all artists.
  - **gpt-5** (INCORRECT): Uses INNER JOIN, excluding artists with zero sculptures. This can miss the true minimum. Should LEFT JOIN artists to sculptures and count per artist (and optionally handle ties).

### Item: `581` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will exclude any artists who have made zero sculptures. The artist with the 'fewest' sculptures could be one with zero, but this query will not consider them.
  - **gpt-5** (INCORRECT): Inner join excludes artists with zero sculptures. To find the artist with the fewest sculptures (possibly zero), use LEFT JOIN from artists to sculptures and count per artist.

### Item: `583` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses LIMIT 3 to return top three artists by oil paintings, but the question asks for the artist(s) with the maximum count (including ties). It should select only those with the highest count, not an arbitrary three.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly uses `LIMIT 3`. The question asks for the artists with "the most" paintings, which implies finding the maximum count and returning all artists with that count. The query arbitrarily returns the top 3 artists.

### Item: `590` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters individual paintings. It should identify locations that have paintings before 1885, and separately ensure those locations have no paintings on canvas at all, regardless of year.
  - **gpt-5** (INCORRECT): It only requires a pre-1885 non-canvas painting. It doesn’t exclude locations that also have canvas works (any year). Need a NOT EXISTS/HAVING to ensure zero canvas works at that location.

### Item: `592` (DB: `car_road_race`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query requests a unique list of constructors but tries to sort them by a non-aggregated column (Age) that is not in the SELECT list. This leads to an ambiguous and incorrect sorting order.
  - **gpt-5** (INCORRECT): Using DISTINCT collapses multiple drivers per constructor, making ORDER BY Age ambiguous and not aligned with “sorted by drivers’ age.” Should return one row per driver ordered by Age (no DISTINCT).

### Item: `593` (DB: `car_road_race`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query selects distinct constructors but orders them by the age of individual drivers. Since a constructor can have multiple drivers with different ages, the ordering is ambiguous and incorrect.
  - **gpt-5** (INCORRECT): Orders DISTINCT constructors by Age, which isn’t defined per constructor. Use aggregation (e.g., MIN(Age)) per constructor and order by that.

### Item: `618` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query groups by `feature_name`, which may not be unique. If different features share a name, their counts will be wrongly combined. It should group by the primary key `feature_id` to count each unique feature correctly.
  - **gpt-5** (INCORRECT): Groups by feature_name, conflating different feature_ids; also uses COUNT(*) instead of counting distinct properties. Should group by feature_id (with name/description) and use COUNT(DISTINCT T2.property_id).

### Item: `620` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `room_count` column is of type VARCHAR. Applying the MIN() function will perform a lexicographical (alphabetical) comparison, not a numerical one, which is required to answer the question correctly.
  - **gpt-5** (INCORRECT): room_count is TEXT; MIN(room_count) uses lexicographic order (e.g., '10' < '2'). Cast to numeric to get the true minimum: MIN(CAST(room_count AS INTEGER)).

### Item: `621` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `room_count` column is of type VARCHAR. Applying MIN() will perform a lexicographical (text) comparison, not a numerical one, which is required by the question and can lead to incorrect results (e.g., '10' < '2').
  - **gpt-5** (INCORRECT): room_count is VARCHAR; MIN computes lexicographic min and may return '' or a string like '10' over '2'. Should cast to numeric and exclude empty/non-numeric values.

### Item: `633` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by user_id but selects search_seq (nondeterministic) and doesn’t return search_string. Should first find users with count>=2, then list their search_string(s) for those users.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly selects `search_seq` instead of `search_string`. Also, grouping by `user_id` returns only one arbitrary search per user, not all searches as the question asks.

### Item: `634` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query groups by user_id but selects the non-aggregated column search_seq. This will return an arbitrary, single search_seq for each user, not all search sequences for users with multiple searches.
  - **gpt-5** (INCORRECT): Groups by user_id but selects non-aggregated search_seq, yielding an arbitrary sequence per user. The query should first find users with COUNT(*)>=2, then return all their search_seq rows.

### Item: `656` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly uses EXCEPT on `search_string`. This removes a search string if any property owner has searched for it, even if a non-property owner also searched for the same string.
  - **gpt-5** (INCORRECT): Filters by search_string instead of user_id. If an owner searched the same text, it wrongly excludes non-owners’ searches. Also EXCEPT makes results DISTINCT. Should filter users with no properties.

### Item: `689` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Should compare against MIN(price) for Tarts to be less than every Tart. Using MAX(price) returns items less than the highest-priced Tart, not less than all Tarts.
  - **gemini-2.5-pro** (INCORRECT): The phrase 'less than any Tart' means the price should be less than the price of *every* Tart. The query should use MIN() to find the price of the cheapest Tart, not MAX().

### Item: `695` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query assumes ordering the 'date' TEXT column lexicographically will find the latest date. For the format 'DD-Mon-YYYY', this is not true (e.g., '31-Jan-2023' comes after '01-Feb-2023').
  - **gpt-5** (INCORRECT): Date is stored as TEXT like 'DD-Mon-YYYY'; ordering DESC on this string is lexicographic, not chronological, so latest date may be wrong across months/years. Needs proper date parsing/normalization.

### Item: `696` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query finds the latest date by sorting a TEXT column. With the format 'DD-Mon-YYYY', this sort is lexicographical, not chronological, and will not reliably identify the latest date.
  - **gpt-5** (INCORRECT): Orders Date TEXT lexicographically ('DD-Mon-YYYY'), not chronologically, so latest may be wrong. Also returns all receipts for that date, not a single receipt.

### Item: `699` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Operator precedence causes all Cookies to be returned regardless of price. Use parentheses: (food IN ('Cookie','Cake')) AND price BETWEEN 3 AND 7.
  - **gemini-2.5-pro** (INCORRECT): The query is incorrect due to SQL operator precedence. The `AND` is evaluated before `OR`, so the query returns all cookies regardless of price, plus cakes that cost between 3 and 7.

### Item: `700` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause is logically incorrect due to operator precedence. The query returns all cookies regardless of price, plus cakes priced between 3 and 7. The OR conditions should be grouped in parentheses.
  - **gpt-5** (INCORRECT): Operator precedence bug: AND binds before OR, so it returns all Cookies regardless of price. Should be (food IN ('Cookie','Cake')) AND price BETWEEN 3 AND 7.

### Item: `701` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'Date' column lexicographically as it is a TEXT type. This will not correctly identify the earliest date for formats like 'DD-Mon-YYYY'. A date function is required for proper sorting.
  - **gpt-5** (INCORRECT): Orders by Date TEXT lexicographically; with format 'DD-Mon-YYYY' this won’t yield the true earliest date. Should compute MIN(Date) (or parse to real date) and then select customer(s) for that date.

### Item: `702` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query performs a lexicographical sort on the 'date' column, which is a TEXT field in 'DD-Mon-YYYY' format. This will not correctly identify the chronologically earliest date.
  - **gpt-5** (INCORRECT): Orders by TEXT date in 'DD-Mon-YYYY' format lexicographically, not chronologically, so earliest may be wrong. Also LIMIT 1 arbitrarily breaks ties if multiple customers share the earliest date.

### Item: `706` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The question asks for the 'cheapest good', which implies identifying the item. The query returns only the minimum price, not the name or ID of the good itself.
  - **gpt-5** (INCORRECT): Query returns only the minimum price, not the cheapest good. It should return the item(s) (e.g., Id/Food) with flavor='Cheese' that have the minimum price, handling ties if any.

### Item: `711` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query compares the price to the average price, but the question asks for prices above 'twice the average price'. The WHERE clause is missing the multiplication by 2.
  - **gpt-5** (INCORRECT): Uses avg(price) instead of twice the average; should be price > 2 * (SELECT AVG(price) FROM goods).

### Item: `712` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Compares price to avg(price) instead of twice the average. Should be: price > 2 * (SELECT AVG(price) FROM goods).
  - **gemini-2.5-pro** (INCORRECT): The query compares the price to the average price, but the question asks for goods that are more than *twice* the average price. The condition should be `price > 2 * (SELECT avg(price) FROM goods)`.

### Item: `723` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by team instead of make. Should group by make and count teams per make (e.g., GROUP BY make HAVING COUNT(*) > 1 or COUNT(DISTINCT team) > 1).
  - **gemini-2.5-pro** (INCORRECT): The query groups by `team` instead of `make`. To find makes with more than one team, the query should group by `make` and then count the number of teams in each group.

### Item: `724` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query groups by `team` instead of `make`. To find which make has more than one team, the aggregation should be performed on the `make` column.
  - **gpt-5** (INCORRECT): Groups by team instead of make, so it counts duplicates per team rather than number of teams per make. Should group by make and count teams (e.g., COUNT(DISTINCT team)) with HAVING > 1.

### Item: `726` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Applying MIN() and MAX() on a text column performs a lexicographical (string) comparison, not a numerical one, which will produce an incorrect result. The column should be cast to a numeric type.
  - **gpt-5** (INCORRECT): Points is TEXT; MAX/MIN on TEXT compare lexicographically, not numerically. Cast to a number, e.g., MAX(CAST(Points AS INTEGER)), MIN(CAST(Points AS INTEGER)) to get correct extremes.

### Item: `727` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Applying MIN() and MAX() functions will result in a lexicographical (alphabetical) comparison, not a numerical one, which will produce an incorrect answer.
  - **gpt-5** (INCORRECT): Points is stored as TEXT; MAX/MIN will compare lexicographically, not numerically. Must CAST Points to INTEGER/REAL to get true highest and lowest values.

### Item: `730` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. The query performs a lexicographical (alphabetical) sort, which is incorrect for numerical values. For example, '9' would be sorted higher than '185'.
  - **gpt-5** (INCORRECT): Orders by Points as TEXT (lexicographic) instead of numeric. Must cast Points to a number to sort correctly in descending order.

### Item: `731` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Ordering it directly results in a lexicographical (alphabetical) sort, not the numerical sort implied by the question. The column should be cast to a numeric type.
  - **gpt-5** (INCORRECT): Orders by Points as TEXT, causing lexicographic sort instead of numeric. Should cast Points to a number (e.g., ORDER BY CAST(Points AS INTEGER) DESC or Points+0) to rank correctly.

### Item: `736` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Ordering by this column directly will result in lexicographical (alphabetical) sorting, not numerical sorting, which is required to find the driver with the most points.
  - **gpt-5** (INCORRECT): Points is TEXT; ORDER BY sorts lexicographically, not numerically, so it may not pick the true max points. Should cast Points to a number before ordering.

### Item: `737` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. The query performs a lexicographical (string) sort instead of a numerical sort, which will not correctly identify the driver with the highest points.
  - **gpt-5** (INCORRECT): Orders by Points as TEXT; should cast to numeric to find the highest points. Lexicographic sort can mis-rank values (e.g., '950' > '1000'). Use CAST on Points in ORDER BY.

### Item: `755` (DB: `institution_sports`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly calculates the sum of enrollments. The question asks to return all individual enrollment values for the specified cities, not their total.
  - **gpt-5** (INCORRECT): Uses SUM to aggregate enrollments; the question asks for all individual enrollment values for institutions in Vancouver or Calgary, not a single total.

### Item: `758` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Needs SUM(Value) grouped by Contents and select the max total. Current query orders by individual box Value, not total per content.
  - **gemini-2.5-pro** (INCORRECT): The query finds the content of the single box with the highest individual value, not the content with the highest total (sum of) values. It is missing a GROUP BY on Contents and a SUM aggregation on Value.

### Item: `760` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns the count of distinct locations instead of listing the distinct location values.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of distinct locations, but the question asks to return the actual distinct locations themselves. The aggregation function COUNT is incorrect.

### Item: `761` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Query returns the count of distinct locations, but the question asks for the list of distinct warehouse locations.
  - **gemini-2.5-pro** (INCORRECT): The question asks for the list of different locations, but the query returns the count of the number of different locations. The COUNT aggregation is incorrect.

### Item: `762` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The question asks for all contents from warehouses in Chicago OR New York. The query uses INTERSECT, which finds contents present in BOTH Chicago AND New York, which is a different question.
  - **gpt-5** (INCORRECT): Uses INTERSECT, returning only contents present in both cities. The question asks for all contents in Chicago and New York (union), not just the overlap.

### Item: `774` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses MIN(value) of Rocks; should compare to MAX(value) or use > ALL to be greater than every Rocks box value. Current query returns boxes > the minimum Rocks value, which is too weak.
  - **gemini-2.5-pro** (INCORRECT): The question asks for boxes with a value greater than *any* box containing 'Rocks', which implies the value must be greater than the *maximum* value of all such boxes. The query incorrectly compares against the *minimum* value.

### Item: `777` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the sum of values for all boxes. The `ORDER BY ... LIMIT 1` is applied after the `SUM` aggregation and does not correctly filter for only the boxes in the warehouse with the largest capacity.
  - **gpt-5** (INCORRECT): It sums all boxes, not just those in the largest-capacity warehouse. ORDER BY/LIMIT on an aggregate has no effect. Should filter to warehouses with MAX(capacity) before summing.

### Item: `778` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query aggregates the sum over all boxes from all warehouses first, and then attempts to order and limit the single resulting row. It should first find the warehouse with the max capacity, then sum the values of boxes only in that warehouse.
  - **gpt-5** (INCORRECT): SUM aggregates all boxes; ORDER BY/LIMIT on a non-grouped aggregate query doesn’t filter rows. It doesn’t restrict to the warehouse with max capacity (missing WHERE capacity = (SELECT MAX(...))).

### Item: `792` (DB: `university_rank`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filter uses rank >= 5; should be rank <= 5 to capture universities with overall rank 5 or below.
  - **gemini-2.5-pro** (INCORRECT): The query filters for universities with a rank of 5 or higher (`rank >= 5`), but the question asks for a rank of 5 or below, which corresponds to `rank <= 5`.

### Item: `793` (DB: `university_rank`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The question asks for universities with a rank of 5 or below (rank <= 5), but the SQL query filters for universities with a rank of 5 or greater (rank >= 5).
  - **gpt-5** (INCORRECT): Filter direction is wrong: it uses rank >= 5. For 'rank of 5 or below' it should filter Rank <= 5.

### Item: `795` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Query compares rating to the literal string 'null'. To find movies without any rating, it must check for NULL values (use IS NULL), not the string 'null'.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for the string literal 'null'. To find movies with no rating, it should use the `IS NULL` operator, i.e., `WHERE rating IS NULL`.

### Item: `796` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly compares the rating to the string literal 'null'. To check for the absence of a value, the `IS NULL` operator should be used, e.g., `WHERE rating IS NULL`.
  - **gpt-5** (INCORRECT): Filters for the literal string 'null' instead of missing values. Should use WHERE rating IS NULL to get movies without ratings.

### Item: `810` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query groups the results by rating, which provides a count for each rating instead of the total count. It also incorrectly filters for the string 'null' instead of using `IS NOT NULL`.
  - **gpt-5** (INCORRECT): Returns counts per rating and filters against string 'null'. Should return a single total count using WHERE rating IS NOT NULL without GROUP BY.

### Item: `811` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query groups results by rating, returning a count for each rating, but the question asks for a single total count. The WHERE clause also incorrectly checks for the string 'null' instead of using `IS NOT NULL`.
  - **gpt-5** (INCORRECT): Needs a single total count of non-NULL ratings. Query groups by rating and uses rating != 'null' instead of IS NOT NULL, which can wrongly exclude literal 'null' values and returns multiple rows.

### Item: `814` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly compares the `Movie` column to the string literal 'null'. To find theaters not showing a movie, the condition should check for `NULL` values using `WHERE Movie IS NULL`.
  - **gpt-5** (INCORRECT): Should test for NULL with IS NULL. Using Movie = 'null' compares to the string/0, not SQL NULL, so it misses theaters where Movie is actually NULL.

### Item: `815` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly compares the 'Movie' column to the string literal 'null'. To find cinemas not showing any movies, it should check for actual NULL values using `WHERE Movie IS NULL`.
  - **gpt-5** (INCORRECT): To find cinemas not showing any movies, Movie must be NULL. Use WHERE Movie IS NULL. The current query compares to the string 'null' (or coerces to 0), returning wrong results.

### Item: `817` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Unrated means Rating is NULL. The query compares to the string 'null' instead of checking IS NULL, so it misses NULL ratings and only matches literal 'null' strings.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for the string literal 'null' instead of checking for actual NULL values. To find unrated movies, the condition should be `WHERE rating IS NULL`.

### Item: `818` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Unrated should mean NULL ratings, but the query checks for the literal string 'null'. It should use WHERE rating IS NULL to return unrated movies.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for the string literal 'null'. To find movies with a missing rating, the condition should be `WHERE rating IS NULL`.

### Item: `820` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly attempts to filter NULL values by comparing the 'Movie' column to the string literal 'null'. The correct syntax for this operation is 'WHERE Movie IS NOT NULL'.
  - **gpt-5** (INCORRECT): Wrong NULL handling: compares Movie to string 'null' and may exclude code 0; NOT IN depends on this and can mis-handle NULLs. Use NOT EXISTS or Movie IS NOT NULL to find movies not shown.

### Item: `828` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns a list of package numbers, but the question asks for the total number (count) of packages. The query is missing an aggregation function like COUNT(*).
  - **gpt-5** (INCORRECT): Returns PackageNumber values for Leo Wong’s packages, not the count. Should aggregate with COUNT(*) to return the number of packages he sent.

### Item: `832` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns package numbers instead of a count, and INTERSECT on PackageNumber ignores Shipment, potentially matching different packages. Should filter sender and recipient together and COUNT rows (or include Shipment).
  - **gemini-2.5-pro** (INCORRECT): The query correctly identifies the packages, but it returns a list of their numbers instead of the count of packages as requested by the question.

### Item: `833` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns package numbers, not a count. Uses INTERSECT on PackageNumber only, which isn’t unique across shipments, causing false matches. Should filter sender and recipient on the same row and COUNT.
  - **gemini-2.5-pro** (INCORRECT): The question asks for the number of packages ('How many'), which requires a COUNT aggregation. The query returns a list of package numbers instead of their total count.

### Item: `836` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly combines a non-aggregated column `PackageNumber` with an aggregate function `max(Weight)`. This will return the correct max weight, but an arbitrary `PackageNumber` which may not correspond to the heaviest package. Additionally, `LIKE "John"` is an exact match, not a substring search as implied by "part of their name".
  - **gpt-5** (INCORRECT): Name filter lacks wildcards (should use '%John%'). Also selects PackageNumber with max(Weight) without linking them, so PackageNumber may be wrong; and it returns a single row even if multiple max-weight packages tie.

### Item: `837` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filters only exact 'John' (should match similar names, e.g., '%John%'). Also selects PackageNumber with MAX(Weight) without linking them; returns arbitrary PackageNumber, not the heaviest row.
  - **gemini-2.5-pro** (INCORRECT): The query selects PackageNumber alongside the aggregate max(Weight) without a GROUP BY. This returns the correct max weight but an arbitrary PackageNumber, not the one for the heaviest package.

### Item: `849` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses OR between planet and manager filters. The question requires shipments on Mars that Turanga Leela manages, so both conditions must hold (use AND).
  - **gemini-2.5-pro** (INCORRECT): The query uses an OR condition in the WHERE clause, but the question requires shipments that are both on the planet Mars AND managed by Turanga Leela. The correct logical operator is AND.

### Item: `855` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The question asks for the 'number of packages', which implies a count. The query selects the individual package numbers instead of using an aggregate function like COUNT(*) to return the total number.
  - **gpt-5** (INCORRECT): Returns package numbers instead of the requested count. Use COUNT(*) with the same joins and filters to get the number of packages.

### Item: `856` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The question asks for 'the number of packages', which requires a COUNT aggregation. The query incorrectly returns a list of individual package numbers instead of a single count.
  - **gpt-5** (INCORRECT): Returns package identifiers instead of the requested count. Should use COUNT(*) (optionally COUNT(DISTINCT Shipment, PackageNumber)) over packages where sender is Zapp Brannigan or shipment planet is Omicron Persei 8.

### Item: `864` (DB: `video_game`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause `developers != 'Nintendo'` incorrectly includes games co-developed by Nintendo (e.g., 'Nintendo / GameFreak'). It should exclude any game where 'Nintendo' is part of the developer string.
  - **gpt-5** (INCORRECT): Filter developers != 'Nintendo' only removes exact matches. It still includes games co-developed by Nintendo (e.g., 'Nintendo / GameFreak'). Should exclude rows where Developers contains 'Nintendo'.

### Item: `865` (DB: `video_game`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause `developers != 'Nintendo'` only excludes games where the developer is exactly 'Nintendo'. It will incorrectly include games co-developed by Nintendo, such as 'Nintendo / GameFreak'.
  - **gpt-5** (INCORRECT): Uses developers != 'Nintendo', which only excludes exact matches. It will include rows like 'Nintendo / GameFreak'. To exclude any Nintendo-developed games, use NOT LIKE '%Nintendo%'.

### Item: `866` (DB: `video_game`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses <= 3, but the question asks for rank smaller than 3, which requires < 3.
  - **gemini-2.5-pro** (INCORRECT): The question asks for players with a rank 'smaller than 3', which corresponds to the condition `Rank_of_the_year < 3`. The query incorrectly uses `<= 3`, which includes players with a rank of exactly 3.

### Item: `876` (DB: `video_game`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses INTERSECT, which finds games played by players from both Oklahoma and Auburn colleges. The question asks for games played by players from either Oklahoma OR Auburn college.
  - **gpt-5** (INCORRECT): Uses INTERSECT, which returns games with both Oklahoma and Auburn players. The question asks for OR (either college). Should use OR/IN in one query or UNION of the two sets.

### Item: `879` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns overall average and max across all presses. The question asks per press; need GROUP BY (e.g., Press_ID or Name) and include that identifier in the SELECT.
  - **gemini-2.5-pro** (INCORRECT): The query calculates the overall average and maximum profit across all presses. It is missing a GROUP BY clause to provide these metrics 'for each press' as requested.

### Item: `882` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): sale_amount is TEXT; ordering lexicographically may mis-rank amounts. Should cast to numeric (e.g., ORDER BY CAST(sale_amount AS REAL) DESC) to correctly get the top 5.
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'Sale_Amount' column, which is of type TEXT, lexicographically. To find the 'best' books, it should be sorted numerically by casting the column to an integer or real type.

### Item: `888` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'Sale_Amount' column lexicographically (as text) instead of numerically. This will produce an incorrect ranking for the top-selling books.
  - **gpt-5** (INCORRECT): Orders by sale_amount as TEXT, causing lexicographic ranking instead of numeric. Should cast/convert sale_amount to numeric to get true top 3 by sales.

### Item: `889` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'Sale_Amount' column, which is of type TEXT, lexicographically. This will not produce the correct order for 'best selling'. The column should be cast to a numeric type for sorting.
  - **gpt-5** (INCORRECT): Orders by sale_amount as TEXT, yielding lexicographic rather than numeric ranking. Should sort by numeric value (e.g., ORDER BY CAST(t2.sale_amount AS REAL) DESC) to get true top 3.

### Item: `895` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query performs a lexicographical (text) sort on the `Sale_Amount` column, which is of type TEXT. This will not produce the correct numerical order (e.g., '99' > '100'), leading to an incorrect result.
  - **gpt-5** (INCORRECT): sale_amount is TEXT; ORDER BY sorts lexicographically, not numerically, so it may pick the wrong best-selling book. CAST sale_amount to a numeric type before ordering/max.

### Item: `916` (DB: `advertising_agencies`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Aggregates only by meeting_type across all clients. The question asks for counts per client and type. Should include client_id and GROUP BY client_id, meeting_type.
  - **gemini-2.5-pro** (INCORRECT): The query groups by `meeting_type` to count meetings per type, but the question asks for the number of meetings 'for each client', which requires grouping by `client_id`.

## ⚠️ Mixed (No Majority)

**Found 396 queries with mixed voter verdicts (no majority)** (showing ALL)

These queries have no clear majority verdict and require manual review.

### Item: `1` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Excludes clubs with NULL Manufacturer; those also “do not have the manufacturer Nike.” Use WHERE Manufacturer <> 'Nike' OR Manufacturer IS NULL to include them.

### Item: `5` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Query may return NULL if multiple clubs have unknown manufacturer. Add WHERE Manufacturer IS NOT NULL to restrict to actual manufacturers.

### Item: `7` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN on player.Club_ID; if any NULL exists, SQLite causes the predicate to be UNKNOWN for all rows, returning none. Use NOT EXISTS or filter NULLs in subquery to handle clubs with zero players.

### Item: `8` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN, which fails if player.Club_ID contains NULL; this could return no clubs. Use NOT EXISTS or filter NULLs in subquery to correctly find clubs with no players.
  - **gemini-2.5-pro** (CORRECT)

### Item: `13` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): UNION removes duplicate dates. If multiple qualifying orders share the same date/time, only one row is returned. Use UNION ALL to preserve one row per order’s date.

### Item: `14` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is done on name fields, not customer_id. If two customers share the same name and one has orders, both names are excluded. Use customer_id (e.g., WHERE NOT EXISTS) to filter.

### Item: `18` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts order items, not distinct products. Use COUNT(DISTINCT T2.product_id) >= 2 in HAVING to ensure orders have at least two different products.

### Item: `22` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts rows per payment method, not distinct customers. If a customer has multiple rows for the same method, results are inflated. Should use COUNT(DISTINCT customer_id).
  - **gemini-2.5-pro** (CORRECT)

### Item: `23` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN; this excludes customers without a payment method. To include all customers as asked, use a LEFT JOIN from Customers to Customer_Payment_Methods.
  - **gemini-2.5-pro** (CORRECT)

### Item: `28` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Orders table is missing. We cannot determine which orders are unshipped; filtering invoices not in Shipments does not reliably represent “orders which have not been shipped.”

### Item: `29` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses inner joins, so orders with no items are omitted. Question asks for all orders; should LEFT JOIN order_items/products and COALESCE(SUM(product_price),0). Otherwise logic is fine.

### Item: `30` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner joins exclude orders with no items; “for each order” implies all orders should appear (with 0 total). Use LEFT JOIN from Orders and COALESCE SUM to 0. Otherwise logic is fine.

### Item: `35` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Schema lacks product identifiers or quantities. Shipment_Items only links shipments to order_item_id; cannot determine number of products shipped or handle split shipments accurately.

### Item: `36` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average price per order item, not per unique product. The JOIN causes products that are ordered more frequently to be over-represented in the final average calculation.

### Item: `37` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Fails on ties: subquery with LIMIT 1 picks a single gender when multiple genders share the minimum count; should return customers for all least-common genders.
  - **gemini-2.5-pro** (CORRECT)

### Item: `39` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Should use COUNT(DISTINCT T2.payment_method_code). COUNT(*) may overcount if duplicate payment method rows exist, potentially including customers without 2 distinct methods.
  - **gemini-2.5-pro** (CORRECT)

### Item: `40` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Should count distinct payment methods. Use COUNT(DISTINCT T2.payment_method_code) >= 2; COUNT(*) may overcount duplicate rows and include customers with fewer than 2 unique methods.

### Item: `44` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses != max(price), which excludes rows with NULL product_price. To capture all products not at the maximum, use product_price < (select max(...)) or include NULLs explicitly.

### Item: `45` (DB: `bbc_channels`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one name due to LIMIT 1; if multiple directors share the maximum age, it should return all of them instead of an arbitrary single result.

### Item: `47` (DB: `bbc_channels`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so channels with zero programs are omitted. Use LEFT JOIN and COUNT(t2.Program_ID) to include all channels.
  - **gemini-2.5-pro** (CORRECT)

### Item: `48` (DB: `bbc_channels`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if program.channel_id contains NULL, the predicate evaluates to unknown and may return 0. Use NOT EXISTS or filter out NULLs to handle this correctly.
  - **gemini-2.5-pro** (CORRECT)

### Item: `49` (DB: `bbc_channels`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Title isn’t unique; if multiple programs titled 'Dracula' exist, this can return duplicate or multiple names. Use DISTINCT or additional filters to ensure a single director name.

### Item: `57` (DB: `tv_shows`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'ERP_kW' column lexicographically because its data type is TEXT. To correctly answer the question, it should be cast to a numeric type for proper numerical sorting.
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and selected columns, but ORDER BY uses ERP_kW TEXT, causing lexicographic sort. Should cast to numeric (e.g., ORDER BY CAST(T3.ERP_kW AS REAL) DESC) to match ERP descending.

### Item: `58` (DB: `tv_shows`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by Transmitter only, merging multiple radios that share a transmitter; should group by Radio_ID (and Transmitter). Also inner join omits radios with zero city channels.

### Item: `62` (DB: `vehicle_driver`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses builder = 'Zhuzhou', which may exclude entries like 'Zhuzhou Siemens , Germany'. Use a substring match (e.g., LIKE '%Zhuzhou%') to include all vehicles built by Zhuzhou.

### Item: `63` (DB: `vehicle_driver`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): No table records driving events/usage counts. vehicle_driver only links drivers to vehicles, so “times driven” cannot be determined from the schema.

### Item: `64` (DB: `vehicle_driver`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): No event/log table exists to count drive occurrences. vehicle_driver only records unique driver–vehicle pairs, so counts reflect number of drivers, not times driven.

### Item: `67` (DB: `vehicle_driver`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query compares the 'total_production' column, which is of TEXT type, with an integer (100). This will result in a lexicographical comparison, not a numerical one, leading to incorrect results.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate model names if multiple rows share the same model. Use SELECT DISTINCT model to ensure unique models.

### Item: `68` (DB: `vehicle_driver`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query compares the 'total_production' column, which is of type TEXT, with an integer value (100). This can lead to incorrect string-based comparisons instead of the intended numerical comparison.
  - **gpt-5** (CORRECT)

### Item: `75` (DB: `vehicle_driver`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate drivers if multiple vehicles share model 'DJ1' or multiple links exist. Use SELECT DISTINCT to ensure unique driver name/citizenship pairs.

### Item: `83` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Doesn’t exclude NULL prices; in SQLite NULLs sort first, so a NULL-priced Hardware may be returned as “cheapest.” Also returns only one row if multiple products tie for the minimum price.

### Item: `85` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly finds the most frequent code, but returns only one and arbitrarily breaks ties if multiple codes share the maximum count.

### Item: `86` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts NULL payment_method_code and returns an arbitrary code on ties; should exclude NULLs and/or return all top ties for full correctness.

### Item: `87` (DB: `customers_and_orders`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query fails to handle ties. If multiple payment methods share the minimum count of customers, the subquery with `LIMIT 1` will only return one of them, thus omitting customers who used the other tied methods.
  - **gpt-5** (PARTIALLY_CORRECT): Returns customers for only one least-used payment_method_code (ties ignored). Also breaks if least-used code is NULL since = NULL yields no matches.

### Item: `88` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Picks only one least-common payment method due to LIMIT 1; ignores ties where multiple methods share the minimum count. May also duplicate names without DISTINCT.

### Item: `89` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May include NULL as a distinct value; add WHERE payment_method_code IS NOT NULL to list only actual methods used.

### Item: `91` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one least-common product_type_code due to LIMIT 1; if multiple codes tie for least frequency, it won’t return them all.

### Item: `92` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): INNER JOIN omits customers with zero orders. For 'each customer', use a LEFT JOIN from Customers to Customer_orders and group by customer_id/name to include customers with 0 orders.

### Item: `93` (DB: `customers_and_orders`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner join excludes customers with zero orders; the question asks for each customer. Use LEFT JOIN from Customers to Customer_orders and COUNT(order_id) to include zero-order customers.
  - **gemini-2.5-pro** (CORRECT)

### Item: `95` (DB: `customers_and_orders`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Compares by product_name, not product_id. If two products share a name and one is ordered, the unordered product’s name is wrongly excluded. Should use product_id (LEFT JOIN/NOT EXISTS). Also forces DISTINCT.

### Item: `96` (DB: `customers_and_orders`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Subtracts by product_name instead of product_id. If two products share a name and one is ordered, the unordered product’s name is wrongly excluded. Use anti-join on product_id, then select names.

### Item: `99` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): The second part counts order_items rows, not distinct products. For “more than 3 products” it should use COUNT(DISTINCT T2.product_id) per order.

### Item: `100` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): The second branch counts order_items rows (count(*)) rather than distinct products. To match “more than 3 products,” it should use COUNT(DISTINCT T2.product_id) > 3. Otherwise logic is fine.

### Item: `102` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN; if any building lacks a matching region (NULL or no match), it will be omitted. A LEFT JOIN would include every building as requested.

### Item: `105` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one year via LIMIT 1; if multiple years tie for the maximum count, it arbitrarily picks one instead of all tied years.

### Item: `106` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Potential NULL issue: NOT IN returns no rows if building.Region_ID contains NULL. Use NOT EXISTS or filter NULLs in the subquery to correctly find regions without buildings.

### Item: `107` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): NOT IN may return no rows if building.Region_ID contains NULL. Use NOT EXISTS or filter NULLs: WHERE Region_ID NOT IN (SELECT Region_ID FROM building WHERE Region_ID IS NOT NULL).

### Item: `112` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate services if the customer used the same service multiple times; add DISTINCT to return unique services.
  - **gemini-2.5-pro** (CORRECT)

### Item: `113` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate service_details if multiple rows exist per customer-service in the link table. Use SELECT DISTINCT to list unique services used by Hardy Kutch.
  - **gemini-2.5-pro** (CORRECT)

### Item: `114` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by Service_Details, which may not be unique. This can merge different services and miscount usages. Should group by Service_ID (and return its details) to count uses per service correctly.

### Item: `115` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by Service_Details, which may not be unique. This can merge counts from different services and produce false positives. Should group by Service_ID and return its details.

### Item: `119` (DB: `government_shift`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of service usages with COUNT(*), not the number of distinct service types. It should use COUNT(DISTINCT t2.Service_ID) to find the customer with the most types of services.
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows instead of distinct service types; should use COUNT(DISTINCT Service_ID). Also groups by customer_details, which might not be unique—should group by Customer_ID to avoid merging different customers.

### Item: `120` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN without filtering NULLs; if customers_and_services.customer_id has NULLs, it can return no rows. Use NOT EXISTS or exclude NULLs in the subquery.
  - **gemini-2.5-pro** (CORRECT)

### Item: `121` (DB: `government_shift`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): NOT IN can misbehave if customers_and_services.customer_id contains NULLs, potentially returning no rows. Use NOT EXISTS or a LEFT JOIN ... IS NULL to handle NULLs correctly.
  - **gemini-2.5-pro** (INCORRECT): The query uses `NOT IN` with a subquery on the `customers_and_services.customer_id` column. Since this column is nullable, if the subquery returns even one `NULL` value, the `NOT IN` condition will never evaluate to true, resulting in an incorrect empty set.

### Item: `124` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of distinct `customers_and_services_details` values. The question asks for the 'total number', which implies counting all rows in the table, not just the unique types of details.

### Item: `126` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join to customer_interactions forces Hardy’s services without interactions to be excluded and restricts ‘good’ services to those also in customers_and_services. Use UNION or LEFT JOIN to match the OR logic.

### Item: `127` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): The query doesn’t ensure the ‘bad’ interaction is by Hardy Kutch; it only requires any bad interaction for that service. Add a condition tying t4.customer_id to t1.customer_id.

### Item: `128` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Bad interactions aren’t restricted to the same customer. The query joins interactions only on service_id; it should also filter t4.customer_id = t1.customer_id to reflect Hardy Kutch’s ratings.
  - **gemini-2.5-pro** (CORRECT)

### Item: `129` (DB: `government_shift`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The question asks for 'all the details of the customers', which implies selecting all columns from the customers table (t1.*). The query only selects the `customer_details` column.
  - **gpt-5** (PARTIALLY_CORRECT): Returns only customer_details instead of all customer fields, and may produce duplicates if a customer has multiple matching interactions. Use SELECT DISTINCT and/or select all customer columns.

### Item: `131` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Missing join condition to link t2 and t3 (should join on Customer_Interaction_ID). This causes unrelated failed integrations to match any customer. Also case 'fail' may not match 'Fail'.

### Item: `133` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Subtracts by Service_Details instead of Service_ID. If two services share the same details and one is used, the unused one is wrongly excluded. Should filter by Service_ID (e.g., NOT EXISTS/LEFT JOIN).

### Item: `134` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Compares by service_details rather than Service_ID. If two services share the same details and one is used, the unused one’s detail is wrongly excluded. Should filter by Service_ID not present in mapping.

### Item: `137` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Excludes vehicles with no rentals due to INNER JOIN. To include every vehicle, use LEFT JOIN from vehicles to renting_history and COALESCE(SUM(total_hours),0).

### Item: `138` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN; vehicles with no rental records are omitted. To cover each vehicle, LEFT JOIN from vehicles and COALESCE(SUM(total_hours),0), grouping by vehicle.

### Item: `139` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if renting_history.vehicles_id contains NULL, the predicate may exclude all rows. Prefer NOT EXISTS or LEFT JOIN ... IS NULL to safely find vehicles with no history.

### Item: `140` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if renting_history.vehicles_id contains NULL, the predicate yields no results. Use NOT EXISTS or filter out NULLs in subquery to handle this edge case.
  - **gemini-2.5-pro** (CORRECT)

### Item: `144` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is done on teacher_details, not teacher_id. If two teachers share the same details (or NULL), one teaching a 'net%' class will incorrectly exclude the other. Use teacher_id for the set.

### Item: `145` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set subtraction is done on teacher_details, not teacher identity. If two teachers share the same details, a 'net%' class by one could exclude the other who qualifies. Use teacher_id for filtering.

### Item: `146` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one teacher due to LIMIT 1; if multiple teachers tie for most classes, others are omitted. Should return all teachers with the maximum course count.

### Item: `147` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOINs, so students without address records are excluded. To list details for all students, use LEFT JOIN from Students to Students_Addresses and Ref_Address_Types.

### Item: `148` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses inner joins, so students without any address mapping are omitted. A LEFT JOIN from Students would include all students as “each student” suggests.

### Item: `149` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner joins exclude students without addresses; to cover each student, start from Students and LEFT JOIN through Students_Addresses to Addresses. Also may duplicate pairs if multiple address records exist.

### Item: `150` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, which omits students without transcripts. For “all the students,” a LEFT JOIN is needed so students without transcripts appear with NULL dates.

### Item: `151` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits students without transcripts. To answer for “each student,” use LEFT JOIN so students with no transcript still appear (with NULL date).

### Item: `154` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on bio_data and student_details, not student_id, so different students sharing these values can be falsely returned. Should intersect by student_id, then select attributes. Also ignores ties for most common.

### Item: `155` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses bio_data in EXCEPT, so students with identical bio_data may be wrongly excluded; set difference should be by student_id. Also picks a single mode; ties among most common details are mishandled.

### Item: `157` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of event participations (`count(*)`) for the most common event type, not the number of unique students (`count(DISTINCT student_id)`) as requested by the question.
  - **gpt-5** (PARTIALLY_CORRECT): Counts event rows per type (COUNT(*)) rather than distinct students. Should use COUNT(DISTINCT T2.student_id) to match “how many students” joined the most common event type.

### Item: `160` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Joins are correct, but it may return duplicate teacher–student pairs if they share multiple classes. Use DISTINCT to get unique pairs of their details as requested.

### Item: `163` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): ORDER BY ... LIMIT 1 will return NULL first if any date_of_loan is NULL in SQLite. Use MIN(date_of_loan) or add WHERE date_of_loan IS NOT NULL to get the actual earliest date.
  - **gemini-2.5-pro** (CORRECT)

### Item: `164` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): In SQLite, NULLs sort first; if date_of_loan can be NULL, this may return NULL instead of the earliest date. Use MIN(date_of_loan) or filter NULLs in WHERE.

### Item: `165` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join limits to students with transcripts; if the max-loan student has none, it returns another student. Also, if that student has multiple transcripts, an arbitrary date is chosen.

### Item: `166` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns a transcript date for the largest single loan, not per-student total. If that student has multiple transcripts, the chosen date is arbitrary. Needs aggregation/tie-breaking for determinism.

### Item: `169` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join omits students with no courses. Use LEFT JOIN and count class rows (e.g., COUNT(T2.class_id)) to include all students and return 0 for those without classes.

### Item: `170` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses INNER JOIN, excluding students with no classes. To cover “for each student,” use LEFT JOIN and COUNT on a class field (e.g., COUNT(T2.class_id)) to include zero-course students.
  - **gemini-2.5-pro** (CORRECT)

### Item: `172` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is done on bio_data, which may not be unique. If two students share the same bio_data, a loan for one will exclude both. Should compare by student_id (e.g., NOT EXISTS) and then select bio_data.

### Item: `173` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is on bio_data, not student_id. If two students share the same bio_data and only one has a loan, the other is wrongly excluded. The anti-join must be based on student_id.

### Item: `174` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns full datetime, not just the date portion requested. Use DATE(datetime_detention_start) to get only the start date.

### Item: `179` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so authors with zero books are omitted. Should use LEFT JOIN from Author to Author_Book (and COALESCE count to 0) to show all authors.

### Item: `187` (DB: `book_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Inner join counts orders per client but omits clients with no orders. Use LEFT JOIN from Client to Orders and group by client to include all names with zero count.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which omits clients with zero orders. The request to show 'all client names' requires a LEFT JOIN from the Client table to include clients who have never ordered.

### Item: `189` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly counts orders per client and returns the top name, but does not handle ties—returns one arbitrary client if multiple share the maximum.

### Item: `192` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner joins exclude clients with no orders (and orders without items), whereas the question asks for all clients. Use LEFT JOIN from Client and COALESCE(sum(amount),0) to include zero totals.

### Item: `195` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on title, not ISBN. If two books share a title and one has orders, the title is wrongly excluded for the unordered book; also forces DISTINCT. Should filter by ISBN (e.g., LEFT JOIN IS NULL).

### Item: `196` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is on title, not ISBN. If multiple books share a title and any one is ordered, the title is removed even for unordered books. Should filter by ISBN (e.g., NOT EXISTS) then select title.

### Item: `197` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on name instead of client ID. If two clients share a name and one has orders, the name is removed entirely, hiding non-ordering clients. Should anti-join by IdClient/NOT EXISTS.

### Item: `198` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Subtracting by name assumes names are unique. If two clients share a name and one has orders, the non-ordering client is wrongly excluded. Use anti-join on IdClient (then project Name).

### Item: `209` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and filter, but may return duplicate author names if multiple ISBNs share the title (multiple editions). Use DISTINCT to deduplicate.

### Item: `210` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate titles if a book has multiple matching 'Plato' author rows. Use SELECT DISTINCT to ensure unique titles.

### Item: `211` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Semantically correct joins and filter, but may return duplicate titles if a book has multiple matching authors. Use DISTINCT on title to ensure unique book titles.

### Item: `212` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per ISBN-order pair; if multiple ISBNs share the title in the same order, it overcounts. Should count distinct orders (COUNT(DISTINCT T2.IdOrder)) for the title.

### Item: `222` (DB: `book_review`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY Chapters DESC LIMIT 1, which returns an arbitrary single rating if multiple books share the max chapters. Should filter by Chapters = (SELECT MAX(Chapters)...) to return all.

### Item: `226` (DB: `book_review`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns titles ordered by rating, but may duplicate titles if a book has multiple reviews. Use DISTINCT or aggregation if one title per book is intended.

### Item: `227` (DB: `book_review`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join excludes books without reviews, violating “all books”. It can also duplicate books if multiple reviews exist. Use LEFT JOIN and DISTINCT/aggregation, then order by Readers_in_Million DESC.

### Item: `228` (DB: `book_review`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right, but NOT IN can return no rows if review.Book_ID contains NULLs. Use NOT EXISTS or filter NULLs in the subquery to avoid NULL-related pitfalls.
  - **gemini-2.5-pro** (CORRECT)

### Item: `230` (DB: `book_review`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on (type,title) instead of Book_ID. If two books share the same type/title and one has a review, the unrated one is excluded too. Use anti-join/NOT IN by Book_ID (and consider NULL Rating).

### Item: `231` (DB: `restaurant_bills`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns one card credit for the highest Level_of_Membership but ignores ties; if multiple customers share the top level, it arbitrarily picks one instead of all.

### Item: `237` (DB: `restaurant_bills`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by Name, which may not be unique, merging different customers with the same name. Should group by Customer_ID (and optionally Name); consider LEFT JOIN if including customers with no orders.

### Item: `239` (DB: `restaurant_bills`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by Name, merging different customers with the same name. Should group by Customer_ID (and select Name) to sum quantities per customer, not per name.

### Item: `242` (DB: `club_leader`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Includes NULL as a nationality and returns only one row in case of ties (arbitrary among top counts).

### Item: `244` (DB: `club_leader`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns both member name and club name, but the question asks only for names of leaders. Joins and filter (Year_Join < 2018) are otherwise correct.

### Item: `247` (DB: `club_leader`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): A member leading multiple clubs will be counted multiple times, skewing the average. De-duplicate by member (e.g., DISTINCT member_id) before averaging ages.

### Item: `256` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate owners if multiple rows have Description = 'Braeden Collection'. Use SELECT DISTINCT Owner to return unique owners.

### Item: `257` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate owner rows if multiple documents owned by 'Marlin' share the same parent. Use DISTINCT to avoid duplicates.

### Item: `259` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Could return multiple/duplicate parent names if multiple collections are named 'Nice'. Use DISTINCT or ensure Collection_Name is unique.

### Item: `260` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate parent names if multiple 'Nice' rows share the same parent; add DISTINCT to ensure unique parent collection names.

### Item: `261` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on Collection_Name. If names are not unique, any parent with a given name removes all rows with that name, excluding non-parent collections. Should anti-join by Collection_ID instead.

### Item: `262` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Name-based EXCEPT may drop non-parent duplicates if a name also belongs to a parent; also treats self-parenting as being a parent despite “other collections” implying T1.Collection_ID <> T2.Collection_ID.

### Item: `265` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows in members (pairings) rather than distinct collections, so may overcount. Also uses INNER JOIN, omitting subsets with zero members. Should use COUNT(DISTINCT ...) and LEFT JOIN.

### Item: `266` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts pair rows in Collection_Subset_Members, not the number of collections; also inner join omits subsets with zero members. Use LEFT JOIN and count distinct collections per subset.

### Item: `268` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses LIMIT 1, so it returns only one document even if multiple documents share the minimum number of related documents. Should return all ties.

### Item: `272` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Only checks membership via Document_Subset_Members.Document_Object_ID. A document could appear as Related_Document_Object_ID; those subsets would be missed. Should consider both columns.

### Item: `273` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Joins only on T2.Document_Object_ID. If Braeden’s documents can appear as Related_Document_Object_ID, their subset names would be missed. Should consider both columns.

### Item: `274` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join on members omits subsets with no documents. Use LEFT JOIN from Document_Subsets to include all subsets and count 0 where applicable.

### Item: `275` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join excludes subsets with no members. “For each subset” implies including subsets with zero documents. Use LEFT JOIN from Document_Subsets and GROUP BY subset id to include zero counts.

### Item: `278` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Only selects Document_Subset_Members.Document_Object_ID; documents that appear only in Related_Document_Object_ID within the subset are omitted. Must union both columns to list all document IDs.

### Item: `279` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Only selects Document_Object_ID; documents that appear solely as Related_Document_Object_ID in the subset are omitted. Should UNION both columns (DISTINCT) for the subset name.

### Item: `280` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Self-join returns subsets associated with the related document (T2), not the subsets of relations for each document id. Should join Document_Subsets on T1.Document_Subset_ID; self-join not needed.

### Item: `283` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate collection names if multiple Ransom-owned documents exist in the same collection; use DISTINCT to de-duplicate results.

### Item: `285` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and filter, but may return duplicate document IDs if multiple collections share the name 'Best' and contain the same document. DISTINCT would ensure unique IDs.

### Item: `288` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): INNER JOIN excludes 'Best' collections with zero documents. Use LEFT JOIN and COUNT(T2.Document_Object_ID) to include zero-count collections; otherwise may return no row when all have zero.

### Item: `289` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Query only uses Document_Subset_Members.Document_Object_ID. Documents that appear in the subset only as Related_Document_Object_ID (and are in the collection) would be missed; need union of both columns.

### Item: `290` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Document_Subset_Members models pairs; a doc is in a subset if it appears in either Document_Object_ID or Related_Document_Object_ID. Query excludes only the first, so docs present only as related aren’t removed.

### Item: `291` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Subtracts only Document_Subset_Members.Document_Object_ID. If subset membership includes docs via Related_Document_Object_ID as well, those won’t be excluded. Should subtract union of both doc-id columns.

### Item: `296` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Misses subsets where ‘Best’ appears as Related_Collection_ID. Should match Best against both Collection_Subset_Members.Collection_ID and Related_Collection_ID to capture all memberships.

### Item: `297` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Matches Best only via Collection_Subset_Members.Collection_ID. If Best appears as Related_Collection_ID, those subsets are missed. Should filter on either column (OR) to include all subsets.

### Item: `299` (DB: `sing_contest`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an exact match `WHERE T1.language = 'English'`. Based on the schema's example data like 'English , Russian', a song can have multiple languages. The query should use `LIKE '%English%'` to find all songs that include English.
  - **gpt-5** (CORRECT)

### Item: `300` (DB: `sing_contest`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join excludes participants with zero songs. The question implies all participants ordered by their song count. Should use LEFT JOIN and COUNT(T2.songs_id) to include zeros.

### Item: `302` (DB: `sing_contest`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses equality on language; values may be multi-valued (e.g., 'English , Russian'), so it should match English as a substring (LIKE/INSTR). Otherwise the join and selected column are correct.

### Item: `311` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will exclude countries that have zero students. The country with the 'least number' of students could have zero, but this query will not find it.
  - **gpt-5** (PARTIALLY_CORRECT): Inner join excludes countries with zero students; a LEFT JOIN with COUNT(Student.StuID) would include them. Also, LIMIT 1 arbitrarily picks one country if there’s a tie for least.

### Item: `312` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes countries with zero students. A country with zero students could be the correct answer for 'fewest students', so a LEFT JOIN is required.
  - **gpt-5** (PARTIALLY_CORRECT): INNER JOIN excludes countries with zero students; it finds the minimum among countries with students only. To include zero-count countries, use LEFT JOIN from City and count Student rows.

### Item: `314` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Set-difference includes students with NULL/unmatched city_code (unknown country). Should join Student->City and filter WHERE country <> 'USA' to return only non-USA residents.

### Item: `315` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Set-difference includes students with NULL/unmatched city_code as not in USA. A join with WHERE country <> 'USA' would exclude unknown locations and match intent more precisely.

### Item: `316` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only checks for the distance in one direction (BAL to CHI). It fails to consider the reverse direction (CHI to BAL), which could also contain the requested distance.
  - **gpt-5** (PARTIALLY_CORRECT): Assumes an ordered pair (BAL->CHI). If the table stores only the reverse (CHI->BAL), this query would miss it. Should handle both orderings to match “between BAL and CHI.”

### Item: `320` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct aggregates on the right table, but it may include self-distances and double-count reciprocal city pairs. Should filter city1_code <> city2_code and dedupe unordered pairs (e.g., city1_code < city2_code).

### Item: `321` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May double-count both directions and include self-pairs. Should restrict to unique unordered city pairs (e.g., city1 < city2) to compute avg/min/max.

### Item: `324` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns city1_code and city2_code per pair with distance > avg, not a single list of city codes. Duplicates likely. Use UNION/DISTINCT to get unique city codes participating in above-average distances.

### Item: `325` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns both city1_code and city2_code per pair with distance <1000, causing duplicates and pair rows. Likely need a distinct list of city codes involved (e.g., DISTINCT over union of both columns).

### Item: `326` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where 'BAL' is the origin city (city1_code). It fails to include distances where 'BAL' is the destination city (city2_code), resulting in an incomplete total.
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude BAL-to-BAL distance. To match “all other cities,” add AND city2_code <> 'BAL'.

### Item: `332` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filters only rows where Boston is city1; must consider both city1 and city2 cases and return the opposite city to find the farthest city from Boston.
  - **gemini-2.5-pro** (CORRECT)

### Item: `335` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only calculates the sum of distances for cities appearing in `city1_code`. It fails to provide a result for 'each city', as some cities may only exist in the `city2_code` column.
  - **gpt-5** (CORRECT)

### Item: `336` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Includes self-distances in the average; should exclude city1=city2. Also, using Direct_distance as the driving table omits cities with no outgoing rows, contrary to “all city names.”

### Item: `338` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only finds the distance if Linda's city is in `city1_code` and Tracy's city is in `city2_code`. It fails to consider the reverse case where the cities are swapped, which would miss the result.
  - **gpt-5** (PARTIALLY_CORRECT): Assumes distance row is city1=Linda’s city and city2=Tracy’s; if stored reversed, it returns nothing. Also may duplicate if multiple students share names. Handle both orders and consider DISTINCT.

### Item: `340` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only finds distances where Linda Smith's city is in the `city1_code` column. It fails to consider cases where her city is in the `city2_code` column, potentially missing the furthest student.
  - **gpt-5** (CORRECT)

### Item: `342` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and filter, but may return multiple rows/duplicates if there are multiple students named Linda or multiple Lindas in the same state. Use DISTINCT or handle uniqueness if needed.

### Item: `343` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and filter, but may return duplicate states if multiple students named Linda exist. Use DISTINCT or ensure uniqueness to avoid duplicates.

### Item: `344` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate names if a sailor reserved boat 102 multiple times; use DISTINCT to list unique sailors.
  - **gemini-2.5-pro** (CORRECT)

### Item: `345` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate names if a sailor reserved boat 102 multiple times. Use SELECT DISTINCT to return unique sailor names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `346` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query finds all sailors who are not the youngest by comparing age to the minimum age. The question 'older than any sailors' implies finding the oldest sailor(s), which requires comparing to the maximum age.
  - **gpt-5** (UNANSWERABLE): 'older than any sailors' is ambiguous: could mean older than every sailor (> ALL, i.e., max) or just older than at least one (> MIN). The schema/context doesn’t disambiguate.

### Item: `353` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Using > (SELECT MAX(rating) ...) fails if no 'Luis' exists (MAX returns NULL -> no rows). “Higher than all Luis” should be vacuously true; use > ALL (SELECT rating ...) or handle NULL with COALESCE.

### Item: `354` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): If no sailor named 'Luis' exists, MAX returns NULL and the comparison yields no rows. By vacuous truth, all sailors should be returned in that case; otherwise logic is correct.

### Item: `359` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Duplicates possible: sailors with multiple red reservations are counted multiple times, skewing the average. Should deduplicate sailors (e.g., DISTINCT by sid) before averaging by rating.

### Item: `360` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Duplicates: sailors with multiple red reservations are counted multiple times, biasing the average age. Should aggregate per unique sailor (e.g., dedupe by sid) before averaging by rating.

### Item: `363` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Fails for empty set: if no red-boat reservations, MAX returns NULL and no rows match though all sailors should qualify (vacuous truth). May also need DISTINCT to avoid duplicate names.

### Item: `364` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Fails when no red-boat reservations exist: MAX(...) returns NULL, so rating > NULL yields no rows, but the condition should be vacuously true and return all sailors.

### Item: `365` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and filter, but may return duplicate sailor names if they reserved Melon multiple times. Use DISTINCT to ensure unique names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `366` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate sailor names if a sailor reserved 'Melon' multiple times or if multiple boats named 'Melon' exist. Use DISTINCT to ensure unique names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `368` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one model due to LIMIT 1. If multiple headphones share the highest price, others are omitted. Use WHERE price = (SELECT MAX(price) FROM headphone) to include ties.

### Item: `369` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one model due to LIMIT 1; if multiple models share the highest price, others are omitted. Use WHERE price = (SELECT MAX(price) FROM headphone) to return all ties.

### Item: `373` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one headphone. If multiple share the lowest price, others are omitted. Use WHERE price = (SELECT MIN(price) FROM headphone) to include all cheapest options.

### Item: `376` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query uses INTERSECT, which finds classes that have headphones with 'Bowls' earpads and ALSO have headphones with 'Comfort Pads' earpads. The question asks for classes that contain headphones with EITHER 'Bowls' OR 'Comfort Pads' earpads. The correct operator should be UNION, not INTERSECT.

### Item: `377` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): EXCEPT removes any earpad type that appears with plastic at all, not just plastic rows. Should select earpads from rows WHERE construction <> 'Plastic' (optionally DISTINCT)
  - **gemini-2.5-pro** (CORRECT)

### Item: `378` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate model names if multiple rows share the same model; use DISTINCT to return unique models.
  - **gemini-2.5-pro** (CORRECT)

### Item: `383` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, excluding stores with no stock rows. Stores with zero headphones are ignored, though they could tie for maximum. A LEFT JOIN with COALESCE would include zero-stock stores.

### Item: `384` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses ORDER BY and LIMIT 1 to return only the top store, but the question requests all stores with stock and their total quantities. It also doesn’t ensure Quantity > 0.

### Item: `385` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Ignores Quantity. It only excludes stores with any stock row, missing stores whose stock rows all have Quantity=0. Should check absence of stock with Quantity > 0 (e.g., NOT IN subquery filtered by Quantity>0).

### Item: `386` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Ignores Quantity; it only excludes stores absent from stock. Stores with stock rows but all quantities = 0 still have no headphones in stock and should be included. Must check for quantity > 0.

### Item: `387` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Ignores Quantity; it only excludes models present in stock, missing models that have entries but zero quantity in all stores. Should ensure total quantity across stores is 0.

### Item: `388` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Misinterprets “in stock”: it only excludes models absent from the stock table. It should also include models that have stock rows but no store with Quantity > 0.

### Item: `389` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Treats any stock row as in-stock without checking Quantity. Must filter stock on Quantity > 0 to find neighborhoods where no store has any headphones available.

### Item: `391` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses DISTINCT, which can collapse multiple affiliations sharing the same name and address; the request asks for all affiliations, not deduplicated pairs.
  - **gemini-2.5-pro** (CORRECT)

### Item: `392` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses DISTINCT, which may collapse multiple affiliations sharing the same name/address; the question asks for all affiliations.
  - **gemini-2.5-pro** (CORRECT)

### Item: `393` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Adds DISTINCT, which removes duplicate (venue, year) rows. The question suggests listing all papers’ venue and year, not unique pairs. Ordering by year is correct.

### Item: `397` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate papers if a paper has multiple authors whose names contain 'Mckeown'. Use SELECT DISTINCT to ensure unique paper_id/title pairs.

### Item: `398` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate rows if multiple authors named like 'Mckeown' are on the same paper. Use DISTINCT on (title, paper_id) to de-duplicate.

### Item: `400` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): The WHERE clause uses LIKE patterns with extra spaces around the comma (e.g., 'Mckeown ,  Kathleen'), which likely won’t match actual names like 'Mckeown, Kathleen' or 'Rambow, Owen', leading to wrong/no results.

### Item: `402` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join omits authors with zero papers. Use LEFT JOIN from Author to Author_list and COUNT(T2.paper_id) (or COALESCE) to include all authors as requested.

### Item: `403` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Excludes authors with zero papers. Use LEFT JOIN from Author to Author_list and COUNT(T2.paper_id) (with COALESCE if desired) to include all authors; ordering and grouping otherwise correct.

### Item: `409` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one venue due to LIMIT 1; if multiple venues tie for the fewest publications, it should return all of them.

### Item: `418` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts the total number of citations made, not the number of unique papers cited. If two papers by the author cite the same paper, it will be counted twice. COUNT(DISTINCT t1.cited_paper_id) is likely intended.
  - **gpt-5** (CORRECT)

### Item: `419` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of citations made by the author's papers, but the question asks for the number of unique papers that were cited.

### Item: `425` (DB: `aan_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly counts the number of author-paper associations using `count(*)`. To count the number of unique papers per affiliation as requested, it should use `COUNT(DISTINCT T1.paper_id)`.
  - **gpt-5** (PARTIALLY_CORRECT): Counts author-affiliation rows, not distinct papers. Use COUNT(DISTINCT T1.paper_id) or group on DISTINCT (T2.affiliation_id, T1.paper_id) to avoid overcounting when multiple authors share an affiliation on a paper.

### Item: `426` (DB: `aan_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of authors from each affiliation (`COUNT(*)`), not the number of distinct papers. A paper with multiple authors from the same affiliation will be counted multiple times.
  - **gpt-5** (PARTIALLY_CORRECT): Counts author_list rows per affiliation, not distinct papers. Affiliations with multiple authors on the same 2009 paper are overcounted. Use COUNT(DISTINCT T2.paper_id) for correct totals.

### Item: `433` (DB: `aan_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of author-paper associations using COUNT(*), not the number of distinct papers. To correctly answer the question, it should use COUNT(DISTINCT T2.paper_id).
  - **gpt-5** (PARTIALLY_CORRECT): Counts author-paper rows, not distinct papers. Should use COUNT(DISTINCT T2.paper_id) to get number of papers per affiliation with address containing 'China'.

### Item: `435` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so affiliations with zero papers are omitted. Use LEFT JOIN from Affiliation to Author_list to include all affiliations with 0 counts.

### Item: `436` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): INNER JOIN omits affiliations with no papers. Use LEFT JOIN from Affiliation to Author_list to include affiliations with zero publications (COUNT DISTINCT paper_id).
  - **gemini-2.5-pro** (CORRECT)

### Item: `443` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one year due to LIMIT 1; if multiple years tie for the fewest conferences, others are omitted. Should return all years with the minimum count.

### Item: `444` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one year; if multiple years tie for the fewest conferences, LIMIT 1 arbitrarily picks one instead of returning all tied years.

### Item: `446` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one institution due to LIMIT 1; if multiple share the most recent Founded year, it should return all names and locations.

### Item: `447` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join excludes institutions with zero staff, but the request is for each institution founded after 1800. Use LEFT JOIN and group by the institution to include zero-counts (COUNT(staff_ID)).

### Item: `449` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if staff.institution_id contains NULL, the predicate becomes UNKNOWN and can return no rows. Use NOT EXISTS or LEFT JOIN to correctly find institutions with no staff.
  - **gemini-2.5-pro** (CORRECT)

### Item: `450` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic matches the question, but NOT IN can fail if staff.Institution_ID contains NULLs, yielding no rows. Prefer NOT EXISTS or LEFT JOIN ... IS NULL to handle NULLs safely.
  - **gemini-2.5-pro** (CORRECT)

### Item: `454` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INTERSECT on names, not staff_id. If different staff share the same name, it will incorrectly include that name even if no single staff member held both roles. Should intersect by staff_id.

### Item: `456` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects by name instead of staff_ID, so two different people with the same name could appear as having attended both. Also mixes 'Conference' and 'conference'; should use the same table tied to participation.

### Item: `457` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on staff names instead of unique staff IDs. Two different people with the same name could be incorrectly returned. Should intersect by staff_id and then select the corresponding names.

### Item: `458` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner join excludes conferences with no participants. The request is for each conference, so use a LEFT JOIN and COUNT of participation rows (e.g., COUNT(T2.staff_ID)) grouped by conference_id.
  - **gemini-2.5-pro** (CORRECT)

### Item: `459` (DB: `conference`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner join drops conferences with no participants. Also doesn’t return conference_id though requested. Use LEFT JOIN, GROUP BY conference_id, and COUNT(T2.staff_id) to include zeros.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query uses an INNER JOIN, which will exclude conferences that have no participants. A LEFT JOIN would be more accurate to ensure all conferences are included, even those with a participant count of zero.

### Item: `465` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query should use SELECT DISTINCT pilot_name to return unique pilot names, as a pilot may be listed multiple times for different planes.
  - **gpt-5** (INCORRECT): Computes average over PilotSkills rows (pilot-plane) instead of per pilot, skewing the threshold when pilots have multiple planes; also may return duplicate pilot names. Should group by pilot_name.

### Item: `466` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts pilot-plane rows, not unique pilots. Should use COUNT(DISTINCT pilot_name) to get number of pilots older than 40.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of rows (pilot-plane skills) for pilots older than 40, not the number of unique pilots. It should use COUNT(DISTINCT pilot_name) to correctly answer the question.

### Item: `467` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows in pilotskills (pilot-plane pairs), not unique pilots. Use COUNT(DISTINCT pilot_name) to count pilots with age > 40.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of pilot-skill records, not the number of unique pilots. A single pilot can have multiple entries. The query should use COUNT(DISTINCT pilot_name) to count unique pilots.

### Item: `468` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Doesn't handle NULL ages—SQLite orders NULLs first, so a pilot with unknown age could be returned. Add WHERE age IS NOT NULL.

### Item: `469` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right, but in SQLite NULL ages sort first, so a NULL-age pilot could be returned; also if multiple pilots share the minimum age, this returns an arbitrary one without handling ties.

### Item: `470` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): No table records flight occurrences or frequency. pilotskills only maps pilots to planes, not how often planes are flown. A flights/usage log is needed to answer this.

### Item: `472` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): No data on flight frequency. pilotskills lists which pilots can fly which planes, not how often planes are flown. A flights/usage table is needed to answer this.
  - **gemini-2.5-pro** (CORRECT)

### Item: `473` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Ownership is not represented in the provided schema. pilotskills links pilots to planes (skills), not ownership; no owner field or Hangar table details to infer owned planes.

### Item: `485` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query fails to select the `plane_name` column. Without it, the association between a plane and its location is lost, which is essential to answering the question completely.

### Item: `491` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Ownership is not represented in the schema; pilotskills records skills, not ownership. Cannot determine who owns these planes without an ownership relation/table.

### Item: `493` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Aggregates over pilotskills rows; pilots may have multiple plane entries, skewing the average. Should deduplicate by pilot (e.g., avg from DISTINCT pilot_name, age) before computing avg and min.
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average age over all rows, not unique pilots. A pilot's age is counted for each plane they can fly, which incorrectly skews the average.

### Item: `498` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): pilotskills stores pilot-to-plane skills; it doesn’t list actual planes. A planes inventory table (e.g., Hangar) is needed to count planes per type.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of pilots for each plane type by counting rows in the `pilotskills` table. The question asks for the number of planes, which is different information.

### Item: `504` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts pilot-plane pairings per city, not the number of unique pilots. The average age is also calculated over these pairings, which is incorrect if a pilot flies multiple planes in one city.
  - **gpt-5** (PARTIALLY_CORRECT): May double count pilots with multiple planes in the same city; COUNT and AVG should be computed over distinct pilots per city (e.g., deduplicate pilot_name,location) to avoid skewed results.

### Item: `510` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilots if a pilot has multiple planes in Austin. Use DISTINCT on (pilot_name, age) to list each pilot once.
  - **gemini-2.5-pro** (CORRECT)

### Item: `511` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot rows if a pilot has multiple planes in Austin; add DISTINCT on (pilot_name, age) to ensure unique pilots.
  - **gemini-2.5-pro** (CORRECT)

### Item: `515` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts pilot-plane rows, not unique pilots. Should use COUNT(DISTINCT pilot_name) to count pilots younger than min age of F-14 Fighter pilots.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of rows (pilot-skill entries) rather than the number of distinct pilots. A single pilot meeting the age criteria would be counted multiple times if they fly multiple planes.

### Item: `517` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows not distinct pilots. Pilots with multiple planes are overcounted. Use COUNT(DISTINCT pilot_name) for pilots older than MIN age of Piper Cub pilots.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of pilot-skill records, not the number of unique pilots. It should use COUNT(DISTINCT pilot_name) to avoid overcounting pilots who can fly multiple planes.

### Item: `520` (DB: `district_spokesman`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses LIKE '%gov%', which may match non-domain substrings (e.g., 'government.org'). To target gov domains, use a pattern like '%.gov%'.

### Item: `521` (DB: `district_spokesman`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY DESC LIMIT 1, which returns a single row and may arbitrarily break ties. Also NULL ages could be chosen as oldest. Prefer WHERE age = (SELECT MAX(age)) to return all oldest.

### Item: `523` (DB: `district_spokesman`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, so districts with no spokesmen are omitted. For “each district,” use LEFT JOIN from district and GROUP BY district, counting t2.Spokesman_ID to include zero counts.

### Item: `524` (DB: `district_spokesman`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersecting on district name can merge different districts with the same name, yielding false positives. Should identify by District_ID (e.g., intersect/group by District_ID) and then return names.

### Item: `525` (DB: `district_spokesman`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN which can misbehave if spokesman_district.District_ID contains NULL; prefer NOT EXISTS or LEFT JOIN ... IS NULL to avoid the NULL trap.
  - **gemini-2.5-pro** (CORRECT)

### Item: `526` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one title; if multiple sculptures share the most recent year, it arbitrarily picks one due to LIMIT 1. Should return all titles where year = (SELECT MAX(year) FROM sculptures).

### Item: `528` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL years; in SQLite NULL sorts first, so it may return a painting with unknown year instead of the oldest. Add WHERE year IS NOT NULL.

### Item: `529` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Orders by year and returns one row, but doesn’t handle ties (multiple oldest paintings) and doesn’t exclude NULL years (which sort first), potentially returning an unknown-year painting.
  - **gemini-2.5-pro** (CORRECT)

### Item: `533` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses location != 'Gallery 226', which excludes NULL locations. If unknown locations should be included as “not in Gallery 226,” use location IS NULL OR location <> 'Gallery 226'.

### Item: `536` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): DISTINCT is applied only to birthYear, merging different artists who share the same birth year. Use DISTINCT on artist (e.g., DISTINCT artistID, birthYear) to deduplicate by artist, not by year.
  - **gemini-2.5-pro** (CORRECT)

### Item: `537` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Selects lname then fname; the question asks for first then last name. Should return fname, lname in that order.

### Item: `538` (DB: `art_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Potential NULL handling: rows with NULL birthYear/deathYear yield NULL and sort first, so LIMIT 1 may return NULL instead of the shortest lifespan. Add WHERE birthYear IS NOT NULL AND deathYear IS NOT NULL.
  - **gemini-2.5-pro** (INCORRECT): The query uses `ORDER BY ... LIMIT 1` to find the minimum value. However, if `birthYear` or `deathYear` is NULL, the calculated age will be NULL. NULLs sort first, so the query will incorrectly return NULL instead of the shortest known lifespan.

### Item: `539` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Doesn’t exclude NULL birthYear/deathYear; NULL arithmetic sorts first in SQLite, so it may return NULL instead of the shortest lifespan. Add WHERE birthYear IS NOT NULL AND deathYear IS NOT NULL.

### Item: `541` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner join excludes artists with zero paintings. If the longest-lived artist made none, the query won’t return 0. Use LEFT JOIN from artists and count paintings per artist.
  - **gemini-2.5-pro** (CORRECT)

### Item: `542` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses INNER JOIN, excluding artists with zero paintings. If the longest-lived artist has none, it returns another artist’s count. Should use LEFT JOIN and COUNT(paintingID).
  - **gemini-2.5-pro** (CORRECT)

### Item: `545` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): The question asks for locations and the mediums paintings are created on; this corresponds to paintings.mediumOn. Query returns paintings.medium instead of mediumOn.

### Item: `546` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on names (lname,fname) instead of artistID. If different artists share the same name, it can return that name even though no single artist has both a painting and a sculpture.

### Item: `547` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): The INTERSECT is on (lname,fname) rather than artistID. Different artists with the same name (one painter, one sculptor) would incorrectly qualify. Intersect by artistID (then select names).

### Item: `548` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on lname,fname instead of artistID. Different artists sharing the same name (one with oil, another with lithograph) would be falsely returned. Should intersect/group by artistID.

### Item: `549` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct set logic (artists with both oil and lithograph works), but column order is reversed. It returns lname, fname while the question asks for first then last (fname, lname).

### Item: `559` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): In SQLite, NULLs sort first; this query may return a painting with NULL year instead of the oldest. Should exclude NULL years (e.g., WHERE year IS NOT NULL).
  - **gemini-2.5-pro** (CORRECT)

### Item: `561` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Selects last then first name instead of first then last, and may return duplicates if an artist has multiple matching sculptures. Use SELECT DISTINCT fname, lname with the same filter.
  - **gemini-2.5-pro** (CORRECT)

### Item: `563` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): “Length” is ambiguous; schema provides height_mm and width_mm. Cannot determine which dimension to sort by from the question.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly assumes "length" is equivalent to "height_mm". "Length" is ambiguous and more likely refers to the longest dimension, which would be the maximum of height and width.

### Item: `564` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Orders by height_mm while selecting DISTINCT title. If multiple paintings share a title with different heights, the sort is ambiguous. Should aggregate (e.g., MIN(height_mm)) per title before ordering.

### Item: `565` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses UNION which deduplicates titles across paintings and sculptures; the question doesn’t specify deduplication. UNION ALL would preserve all names created between 1900 and 1950.

### Item: `566` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses UNION, which removes duplicate titles across paintings and sculptures. If different works share the same title, some names will be dropped. UNION ALL would preserve all names.

### Item: `567` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is correct, but UNION removes duplicate titles. If the artist has multiple works with the same title across mediums, one would be dropped. UNION ALL would preserve all titles.

### Item: `576` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Painter names are not available in the provided schema. Only painterID exists, so results cannot be ordered by painter name as requested; an Artists.name column is required.
  - **gemini-2.5-pro** (INCORRECT): The query correctly calculates the average dimensions and groups by painter. However, it incorrectly orders the results by the painting's title (`ORDER BY title`) instead of the painter's name as requested.

### Item: `582` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): If no paintings have year > 1900, MAX returns NULL and the predicate is never true; logically it should return all paintings (vacuous truth).

### Item: `584` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Selects correct rows and sorts by year, but output column order doesn’t match request (returns paintingID, title, location instead of paintingID, location, title).

### Item: `588` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is done on names, not artistID, so artists sharing the same name can be incorrectly excluded. Also selects last name before first name, opposite of the request.

### Item: `589` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Subtracts sculptors by name instead of artistID. Homonymous artists can be wrongly removed. Should exclude sculptors by artistID (e.g., NOT EXISTS or EXCEPT on IDs) and then return names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `595` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits drivers with zero races. Use LEFT JOIN and COUNT(T2.Road) (or COUNT of a nullable T2 column) to include all drivers with 0 counts.

### Item: `596` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits drivers with zero races. Use LEFT JOIN and COUNT(T2.Road) to include all drivers as requested by “each driver.”

### Item: `598` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate race names if multiple drivers aged 26 or older participated in the same race. The question implies a unique list of races, which would require using SELECT DISTINCT.

### Item: `600` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Gets the engine with highest count but doesn’t handle ties; if multiple engines are equally most common, it returns an arbitrary one.

### Item: `601` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN on race.Driver_ID; if any NULLs exist, no rows return. Prefer NOT EXISTS or LEFT JOIN to handle NULL correctly.

### Item: `602` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN, which returns no rows if race.Driver_ID contains NULLs. Use NOT EXISTS or filter NULLs in subquery to correctly find drivers with no race participation.

### Item: `603` (DB: `car_road_race`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query excludes drivers who participated in a race where 'James Hinchcliffe' was the pole sitter. The question asks to exclude the driver who actually had the pole position, i.e., 'James Hinchcliffe' himself.
  - **gpt-5** (CORRECT)

### Item: `604` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate names if the table contains repeated language names; use DISTINCT to ensure unique names.

### Item: `605` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by language name, which may not be unique; this can merge different languages sharing the same name. Group by language_id (or id and name) to ensure correct counts.

### Item: `606` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by language name, which may not be unique. Should group by language_id (or id and name) to avoid merging distinct languages with the same name.

### Item: `608` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May double-count countries if the join yields multiple rows per country (e.g., duplicate 'English' entries). Should deduplicate by country_id before averaging.

### Item: `610` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, excluding countries with zero official languages; the max should consider all countries. Use LEFT JOIN and COUNT(T2.language_id) to include zero-count countries. Otherwise fine.

### Item: `614` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Returns only distinct state values, not one row per property. The question asks for the state of each property; should include property_id (or property) with county_state_province instead of collapsing duplicates.

### Item: `615` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Returns unique states only and omits property-level granularity. The query should produce one state/province per property (ideally with property_id), not a DISTINCT list.

### Item: `619` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by feature_name only, merging different features and yielding arbitrary description. Also counts rows instead of DISTINCT property_id. Should group by feature_id (or name+description) and count DISTINCT properties.

### Item: `623` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly retrieves the age categories but may return duplicates. Using SELECT DISTINCT would provide a unique list of age categories, which is likely the user's intent.
  - **gpt-5** (INCORRECT): Filter uses LIKE "%Mother" (suffix match) instead of contains; should be LIKE "%Mother%". Also consider DISTINCT to avoid duplicate age categories.

### Item: `625` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Joins/filters are right, but without deduplication a property with multiple 'garden' feature rows will be counted multiple times. Use DISTINCT property_id (e.g., avg over a DISTINCT subquery) to avoid bias.

### Item: `626` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May overcount: if Property_Features has multiple 'garden' rows per property, the join duplicates properties and skews AVG. Deduplicate by property_id (e.g., DISTINCT in a subquery) before averaging.

### Item: `629` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL vendor_requested_price; in SQLite NULLs sort first, so it may return a NULL instead of the lowest actual price. Add WHERE vendor_requested_price IS NOT NULL.
  - **gemini-2.5-pro** (INCORRECT): The query is incorrect because it does not handle potential NULL values in the 'vendor_requested_price' column. In SQLite, `ORDER BY ... ASC` sorts NULLs first, so the query will return a property with no price instead of the one with the lowest actual price.

### Item: `630` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL vendor_requested_price values; in SQLite NULLs sort first, so it may return a NULL row instead of the true lowest price. Add WHERE vendor_requested_price IS NOT NULL.

### Item: `632` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `room_count` column is of type VARCHAR. Applying the `avg()` function directly is incorrect as non-numeric text values will be implicitly cast to 0, leading to a wrong average.
  - **gpt-5** (CORRECT)

### Item: `636` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic correctly selects properties owned by users with >2 properties. However, it may return duplicate zip_postcode values; add DISTINCT if unique zip codes are intended.

### Item: `637` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Orders by search_datetime without excluding NULLs; in SQLite NULLs sort first, so it may pick a NULL timestamp row instead of the true earliest search.

### Item: `638` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL search_datetime values (which sort first in SQLite), so it may pick a NULL row instead of the true earliest. Ties at the earliest timestamp are also resolved arbitrarily.

### Item: `643` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate addresses if multiple Senior Citizens share the same address. Use SELECT DISTINCT on building, street, city to list unique locations.

### Item: `644` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate address rows if multiple senior citizens share the same address; use DISTINCT to list unique buildings, streets, and cities.

### Item: `647` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join excludes owners whose properties have zero photos. Use LEFT JOIN and COUNT of the photo rows (e.g., COUNT(T2.photo_seq)) to include owners with zero photos.

### Item: `651` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Filters on age_category_code='Over 60', but per examples 'Over 60' is a description. Should filter by description or correct code, e.g., WHERE age_category_description LIKE 'Over 60%'.

### Item: `653` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate countries if multiple users have first_name = 'Robbie' (or multiple matches in same country). Use DISTINCT or restrict to a unique user identifier.

### Item: `654` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right (owners whose property address equals their user address), but may return duplicate names if multiple properties match. Use DISTINCT to ensure unique users.
  - **gemini-2.5-pro** (CORRECT)

### Item: `655` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate names if a user owns multiple qualifying properties; add DISTINCT on the name columns to list each user once.

### Item: `657` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on search_string values, removing any string used by an owner even if also entered by a non-owner. Should filter by user_id not owning properties, not by string values.

### Item: `658` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN to User_Searches, excluding users with 0 searches. “At most twice” should include 0–2 searches. Use LEFT JOIN and count search rows (e.g., COALESCE(COUNT(T2.user_id),0) <= 2).

### Item: `659` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN to User_Searches, excluding users with zero searches. The question includes users with two or fewer searches (0–2). Should use LEFT JOIN and count search rows.

### Item: `660` (DB: `bike_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Schema has no attribute to identify 'racing' bikes, so the required filter cannot be applied. Only general bikes and ownerships are available.

### Item: `661` (DB: `bike_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INTERSECT on product_name and price instead of bike_id; if different bikes share the same name/price, it may return false positives. Intersect by bike_id, then select name and price.

### Item: `664` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Finds a cheapest cookie, but: 1) NULL prices would sort first and be chosen; 2) If multiple cookies share the minimum price, it returns only one arbitrarily.

### Item: `669` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses inner joins, so food types with no purchases are omitted. To include all foods (with 0 customers), start from goods and LEFT JOIN to items and receipts.

### Item: `670` (DB: `bakery_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The provided schema does not contain any information about the location or type of store (e.g., 'bakery'). It's impossible to filter receipts for a specific store.
  - **gpt-5** (PARTIALLY_CORRECT): May include NULL CustomerId if receipts exist without a customer, returning NULL as an id. Add WHERE CustomerId IS NOT NULL to ensure only actual customer ids are returned.

### Item: `671` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema does not contain information about where a purchase was made. It is impossible to filter for customers who shopped specifically 'at the bakery'.
  - **gpt-5** (CORRECT)

### Item: `673` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts cake rows, not distinct types. Use COUNT(DISTINCT Flavor) WHERE Food = 'Cake' to count types.

### Item: `674` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts cake rows, not distinct types. Should use COUNT(DISTINCT Flavor) for Food = 'Cake' to get number of cake types.

### Item: `679` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate receipt numbers if a receipt has multiple Croissant items. Use DISTINCT or GROUP BY to ensure unique receipt numbers.

### Item: `681` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Tie-handling missing: if multiple receipts include items at the maximum price, ORDER BY price DESC LIMIT 1 picks an arbitrary one. Filter price = (SELECT MAX(price)) and use DISTINCT to return all.

### Item: `682` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts purchases per item correctly but returns only one result. If multiple items tie for the minimum count, all should be returned (e.g., via HAVING COUNT(*) = MIN over grouped counts).

### Item: `686` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct filters, but may return duplicate flavors if multiple cake rows share the same flavor. Use SELECT DISTINCT flavor to list unique flavors as the question implies.

### Item: `687` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate flavors if multiple cake rows share a flavor; use DISTINCT to list unique flavors.
  - **gemini-2.5-pro** (CORRECT)

### Item: `691` (DB: `bakery_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses DISTINCT, which removes duplicate last names. The request is for last names of all customers, implying duplicates should be included. Ordering is correct.
  - **gemini-2.5-pro** (INCORRECT): The question asks for the last names of *all* customers, which implies returning one last name for each customer. The `DISTINCT` keyword incorrectly removes duplicates if multiple customers share the same last name.

### Item: `692` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses DISTINCT, removing duplicate last names. The question didn’t request uniqueness; it should list all customers’ last names alphabetically, including duplicates if any.

### Item: `697` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Earliest date is computed by ORDER BY on TEXT like 'dd-Mon-YYYY', which sorts lexicographically, not chronologically. This can pick the wrong earliest receipts; date parsing/conversion is needed.

### Item: `698` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic for price>10 receipts and earliest-date receipts is right, but earliest date uses lexicographic TEXT ordering ('dd-Mon-yyyy'), which may not reflect true chronological earliest across months/years.

### Item: `704` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Computes one overall average across both flavors. The question asks for average prices by flavor (Blackberry and Blueberry), so it should group by flavor.

### Item: `714` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join filters out chocolate items never purchased; ‘at most 10 times’ could include zero. Use LEFT JOIN from goods and COUNT(items.item) to include 0. DISTINCT is redundant.

### Item: `717` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): It computes overall average spending per customer (AVG(price) > 5). The question requires per-good averages > 5 for each good a customer buys (e.g., enforce MIN(price) > 5 or per-good HAVING).

### Item: `718` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): It computes average spend per customer across all goods. The question implies per-good averages (“for each good”), requiring grouping by customer and good (or returning customer-good pairs), which is missing.

### Item: `720` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. The query performs a string comparison ('185' > '150'), not a numeric one. To correctly filter for points greater than 150, the column should be cast to a number (e.g., `CAST(points AS INTEGER) > 150`).
  - **gpt-5** (CORRECT)

### Item: `728` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Comparing a TEXT column with a numeric value (`< 150`) will result in a lexicographical (string) comparison, not a numerical one, leading to incorrect results.
  - **gpt-5** (CORRECT)

### Item: `729` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. The query performs a comparison with a number, which results in a lexicographical (string) comparison, not a numerical one. This is incorrect as, for example, '99' would be considered greater than '150'.

### Item: `732` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. The MAX() function will perform a lexicographical (string) comparison instead of a numerical one, which will produce an incorrect result for finding the highest score.
  - **gpt-5** (CORRECT)

### Item: `733` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query applies the MAX function to the 'Points' column which is of TEXT type. This will perform a lexicographical comparison instead of a numerical one, leading to incorrect results (e.g., '9' would be considered greater than '100').

### Item: `738` (DB: `car_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one make; should return all makes tied for the highest driver count (ties not handled).

### Item: `743` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query applies numerical aggregation functions (SUM, AVG) to the 'Points' column, which is defined with a TEXT data type. This is semantically incorrect and can lead to erroneous calculations.

### Item: `744` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query applies numeric aggregate functions (SUM, AVG) to the 'Points' column, which is defined with a TEXT data type. These operations are not semantically valid for text data.
  - **gpt-5** (CORRECT)

### Item: `745` (DB: `car_racing`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if driver.country contains NULL, the condition becomes UNKNOWN and may return no rows. Use NOT EXISTS or exclude NULLs in subquery for correct semantics.
  - **gemini-2.5-pro** (INCORRECT): The query uses `NOT IN` with a subquery. If the subquery `(SELECT country FROM driver)` returns any NULL values, the entire query will incorrectly return an empty result set due to how SQL handles `NOT IN` with NULLs.

### Item: `746` (DB: `car_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN with driver.country; if any NULL exists in that column, the condition becomes unknown and may return no rows. Prefer NOT EXISTS or LEFT JOIN to handle NULLs safely.

### Item: `747` (DB: `car_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so teams with zero drivers are excluded; if the maximum driver count is 0, it returns no result. Also breaks ties arbitrarily with LIMIT 1.

### Item: `748` (DB: `institution_sports`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns affiliations for non-Vancouver institutions but may include duplicates; DISTINCT likely intended to list unique affiliations.

### Item: `750` (DB: `institution_sports`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, which restricts to institutions present in championship. If the smallest-enrollment institution lacks a championship row, it’s excluded. Should base on institution with LEFT JOIN.

### Item: `753` (DB: `institution_sports`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct grouping for years with multiple institutions, but may include NULL as a “year” if there are multiple NULLs. Add WHERE Founded IS NOT NULL to avoid this.

### Item: `754` (DB: `institution_sports`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Lowercase city literals; string equality is case-sensitive in SQLite, so rows like 'Vancouver'/'Calgary' may be missed. Use proper case or a case-insensitive compare.

### Item: `759` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Picks only one row via LIMIT 1. If multiple boxes share the greatest value, it returns an arbitrary content instead of all with the max value. Should use WHERE value = (SELECT MAX(value)).

### Item: `763` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Compares by location, not by warehouse. If multiple warehouses share a location, any with Scissors will exclude that location even if another warehouse there has only Rocks. Filter by warehouse code first.

### Item: `764` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): EXCEPT is applied on location, not per warehouse. A city with any Scissors box is excluded even if another warehouse there has Rocks-only. Must filter by warehouse code, then return its location.

### Item: `767` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on location, not on warehouse. If multiple warehouses share a location, it can return a location where different warehouses hold Rocks and Scissors. Intersect by warehouse code, then select location.

### Item: `768` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on location instead of warehouse. If multiple warehouses share a location, it may return that location even when no single warehouse stores both Rocks and Scissors.

### Item: `773` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Needs > ALL (or > MAX(value)) of Rocks boxes. Using MIN returns boxes greater than the smallest Rocks value, not greater than every Rocks box, and fails when no Rocks exist (NULL).

### Item: `775` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Fails when there are no 'Scissors' rows: MAX returns NULL and value > NULL filters out all rows. For universal quantification over empty set, use NOT EXISTS instead.

### Item: `776` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Edge case: if no 'Scissors' boxes exist, MAX returns NULL and no rows are returned, whereas the condition “greater than all Scissors values” should be vacuously true. Use > ALL or handle empty set.

### Item: `780` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts distinct locations, not distinct warehouses. Should count DISTINCT T1.warehouse or T2.code for boxes where Contents='Rocks'.
  - **gemini-2.5-pro** (CORRECT)

### Item: `781` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query compares the number of boxes to the capacity, but the question asks if the warehouse is 'above capacity'. This is ambiguous. It could mean the total value of boxes, or the physical space they occupy, which is not available in the schema.
  - **gpt-5** (CORRECT)

### Item: `784` (DB: `university_rank`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one conference due to LIMIT 1; the question asks for all home conferences with the minimal total enrollment. Should return all ties (min SUM(enrollment)).
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1` which will only return a single conference. The question asks for 'conferences' (plural), implying all conferences that are tied for the fewest enrollments should be returned.

### Item: `786` (DB: `university_rank`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by University_Name instead of University_ID, which can merge different universities sharing a name. Also, ties for top count are returned arbitrarily due to LIMIT 1.

### Item: `787` (DB: `university_rank`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by University_Name instead of unique University_ID; if names collide, counts merge and the result can be wrong. Group by University_ID (and select the name) to avoid conflation.

### Item: `789` (DB: `university_rank`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN; question asks for every Wisconsin university. If some lack a ranking, they will be omitted. A LEFT JOIN from University to Overall_ranking would include all and show NULL rank.

### Item: `794` (DB: `university_rank`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `ORDER BY ... LIMIT 3` which does not correctly handle ties. It will return exactly 3 universities, but the question 'top 3 and above' implies including all universities with the top 3 scores.
  - **gpt-5** (PARTIALLY_CORRECT): Orders by reputation and limits to 3, but “top 3 and above” suggests including all ties at the 3rd-highest reputation point. LIMIT 3 may exclude additional tied universities.

### Item: `798` (DB: `movie_2`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of movie showings, not the number of distinct movies. The question asks for the number of unique movies, which would require COUNT(DISTINCT T2.movie).
  - **gpt-5** (PARTIALLY_CORRECT): Counts theater-movie rows, not unique movies. If a movie plays in multiple theaters it’s counted multiple times. Use COUNT(DISTINCT T1.code) or COUNT(DISTINCT T2.movie) instead.

### Item: `799` (DB: `movie_2`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of movie showings, not the number of distinct movies. It should use COUNT(DISTINCT T1.code) or COUNT(DISTINCT T2.movie) to correctly answer the question.
  - **gpt-5** (PARTIALLY_CORRECT): Counts theater rows, not unique movies. If a movie is in multiple theaters it’s overcounted. Use COUNT(DISTINCT T2.movie) (or DISTINCT T1.code) to get the number of movies playing.

### Item: `800` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counting DISTINCT name may merge different theaters sharing a name. Use COUNT(*) or COUNT(DISTINCT Code) to count theaters (Code is the PK).

### Item: `801` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts distinct theater names, not distinct theaters. Use COUNT(*) or COUNT(DISTINCT Code) to count theaters by their primary key.
  - **gemini-2.5-pro** (CORRECT)

### Item: `806` (DB: `movie_2`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per theater, but should count distinct movies. Use COUNT(DISTINCT Movie) to avoid overcounting duplicates.

### Item: `807` (DB: `movie_2`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per theater name, not distinct movies; duplicates of the same movie at a theater may be overcounted. Use COUNT(DISTINCT movie) to align with “most movies.”

### Item: `808` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by title instead of movie ID; movies with the same title would have their theater counts merged, producing wrong results. Group by movie code (or T2.movie) and then select title.

### Item: `809` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by title, not movie identity. If different movies share the same title, their theater counts are combined. Should group by movie code (and title) to count per film correctly.

### Item: `812` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Returns any theater with a row, even if Movie is NULL. It doesn't ensure a movie is playing. Should filter Movie IS NOT NULL or use HAVING COUNT(Movie)>=1.

### Item: `813` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Doesn’t ensure a movie is playing. It returns all theater names with any row, even if Movie is NULL. Should filter Movie IS NOT NULL or join to Movies; HAVING count(*)>=1 is redundant.

### Item: `819` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for the string literal 'null' using `!= 'null'`. The correct way to exclude SQL NULL values is with the `IS NOT NULL` operator.
  - **gpt-5** (CORRECT)

### Item: `825` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Clearance Level is defined per (Employee, Planet). The question doesn’t specify a planet or ensure a unique physician, so a single “level” cannot be determined from the schema.

### Item: `826` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Ambiguous: clearance level is per Employee and Planet. The question doesn’t specify which physician or which planet, so a unique level cannot be determined.

### Item: `829` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Name filter is case-sensitive; using "leo wong" may miss rows where the stored name is "Leo Wong". Use correct casing or a case-insensitive comparison (e.g., COLLATE NOCASE).

### Item: `830` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): PackageNumber is only unique per Shipment; selecting only PackageNumber may return duplicates across different shipments. Use DISTINCT or include Shipment to disambiguate.

### Item: `831` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Selects only PackageNumber, but packages are identified by (Shipment, PackageNumber). DISTINCT may merge different packages across shipments. Should include Shipment or return full package rows.

### Item: `838` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts only clients present in package (excludes clients with zero received packages) and returns a single client even if multiple tie for the minimum. Should left join from client and return all with the min.

### Item: `839` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses LIMIT 1, so only one recipient is returned. The question implies returning all recipients with the smallest received-count; should include all ties for the minimum.

### Item: `841` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns an extra count column; the question asks only for client names.

### Item: `850` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join counts only planets that have shipments. “Each planet” suggests including planets with zero shipments; use LEFT JOIN from Planet to Shipment to include those.

### Item: `851` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join from Shipment excludes planets with zero shipments. To answer “each planet,” use LEFT JOIN from Planet to Shipment and GROUP BY planet to include zero counts.

### Item: `857` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on Name, not employee identity. If two employees share the same name and one has Mars clearance, both are excluded. Should filter by EmployeeID (e.g., NOT EXISTS) and then output Name.

### Item: `858` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is on Name, not per employee. If two employees share a name and one has Mars clearance, the name is removed entirely, excluding the other. Should filter by EmployeeID/NOT EXISTS.

### Item: `860` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average salary from the `employee` table but applies the filter to the `Employee` table. The average should be calculated from the same table that is being filtered.
  - **gpt-5** (CORRECT)

### Item: `862` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Planet name filter uses 'mars' (case-sensitive in SQLite). If stored as 'Mars', no match occurs, leading to an incorrect count. Use proper case or a case-insensitive comparison.

### Item: `863` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is correct, but filter uses t3.name = 'mars'. SQLite string comparison is case-sensitive; if stored as 'Mars', it returns no matches. Use 'Mars' or a case-insensitive comparison.

### Item: `868` (DB: `video_game`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate players if multiple game rows share the title. Use DISTINCT (or GROUP BY) on player fields to ensure unique name/rank pairs.

### Item: `870` (DB: `video_game`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Averaging over game-player rows can double-count games with multiple Guard players. Use DISTINCT on games (e.g., AVG(DISTINCT Units_sold_Millions) or GROUP BY Game_ID) to get unique games.
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average units sold per player-game instance, not per unique game. If a game is played by multiple 'Guard' players, its sales will be counted multiple times, skewing the average.

### Item: `871` (DB: `video_game`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Duplicates possible: games with multiple Guard players are counted multiple times, skewing the average. Should average over distinct games (e.g., select distinct Game_ID before averaging).
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly includes a game's sales figures multiple times in the average if that game was played by more than one 'Guard'. The average should be calculated over the distinct set of games.

### Item: `873` (DB: `video_game`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one franchise due to LIMIT 1; if multiple franchises tie for most games, others are omitted.

### Item: `877` (DB: `video_game`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logical set difference is done on Title, so duplicate titles can cause incorrect exclusion/inclusion. Should operate on Game_ID (e.g., NOT EXISTS) to avoid duplicates issue.

### Item: `878` (DB: `video_game`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is done on Title, not Game_ID. If two games share a title and only one has a Guard player, the title is removed entirely. Exclude by Game_ID (e.g., NOT EXISTS or EXCEPT on Game_ID).

### Item: `880` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses LIMIT 1; if multiple publishers share the highest monthly profit, it returns only one instead of all.

### Item: `881` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): sale_amount is TEXT; ORDER BY sorts lexicographically, not numerically. Must CAST sale_amount to a number (e.g., ORDER BY CAST(sale_amount AS REAL) DESC) to get the top 5 best sales.
  - **gemini-2.5-pro** (CORRECT)

### Item: `884` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on author names instead of author IDs. If two authors share the same name (one in MM, one in LT), the name could appear even though no single author has both. Intersect on author_id, then get names.

### Item: `885` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on author name instead of author_id, so two different authors with the same name could be wrongly included. Should match by author_id (then select names).

### Item: `886` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if any book.author_id is NULL, SQLite returns no rows. Use NOT EXISTS or filter out NULLs to correctly find authors with no books.

### Item: `887` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN on book.author_id; if any NULL appears in the subquery, it returns no rows. Prefer NOT EXISTS or filter NULLs in subquery for correctness.
  - **gemini-2.5-pro** (CORRECT)

### Item: `890` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join excludes presses with no books; the request for totals for each press implies including presses with zero sales. A LEFT JOIN with COALESCE would cover this.

### Item: `891` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, which excludes presses with no books. For “each press,” use LEFT JOIN from press to book and group by press so presses with zero sales are included.

### Item: `892` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so publishers with zero books > 1000 are omitted. For “each publisher,” use LEFT JOIN from press and conditional counting to include zeros.

### Item: `893` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Excludes presses with zero qualifying books (INNER JOIN + WHERE). Also groups by name, merging presses that share a name. Should LEFT JOIN from press and count conditionally, grouping by press_id (and name).

### Item: `894` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query performs a lexicographical (text) sort on the `Sale_Amount` column because its data type is TEXT. To find the best-selling book, a numerical sort is required, e.g., by casting the column to a numeric type.
  - **gpt-5** (CORRECT)

### Item: `897` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Compares by Name in EXCEPT. If two authors share a name and one published with 'Accor', the other is wrongly excluded. Should compute by Author_ID then return their names.

### Item: `900` (DB: `cre_Doc_Workflow`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct tables and filter; however, it may return duplicate rows if multiple documents named 'Travel to China' exist for the same author. Using DISTINCT would avoid duplicates.

### Item: `903` (DB: `cre_Doc_Workflow`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts staff-role assignments per role, not distinct document processes. Should count DISTINCT (document_id, process_id) for each staff_role_code to match “number of document processes.”
  - **gemini-2.5-pro** (CORRECT)

### Item: `904` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join excludes agencies with zero clients; the maximum should consider zero-client agencies too. Use LEFT JOIN and COUNT(T2.client_id) to include them.

### Item: `905` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate agency_details if multiple 'Mac' clients exist under the same agency. Use DISTINCT to return unique agency details.
  - **gemini-2.5-pro** (CORRECT)

### Item: `906` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and filter, but may return duplicate agency_details if multiple 'Mac' clients share an agency. Use DISTINCT to ensure unique agency details.

### Item: `911` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Missing DISTINCT; may return duplicate outcome–purpose pairs instead of the unique set of all outcomes and purposes.
  - **gemini-2.5-pro** (CORRECT)

### Item: `912` (DB: `advertising_agencies`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (UNANSWERABLE): The question asks for the 'statuses of the payments', but the database schema does not contain a column for payment status. The `Invoices` table has an `invoice_status`, but this is not the same.

### Item: `914` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so invoices with zero payments are excluded. Should start from Invoices with LEFT JOIN to Payments to ensure invoices with zero payments are considered.

### Item: `915` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses LIMIT 1, so only one invoice is returned even if multiple tie for most payments. Also counts only invoices present in Payments, excluding invoices with zero payments.

### Item: `917` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per meeting; may overcount if duplicate (meeting_id, staff_id) rows exist. Use COUNT(DISTINCT staff_id) to get the number of staff per meeting.

### Item: `918` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Could overcount if duplicate staff-meeting rows exist; COUNT(DISTINCT staff_id) is safer. Also excludes meetings with zero staff if those should be included.

### Item: `919` (DB: `advertising_agencies`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses LIMIT 1 so returns only one staff member, not all with the lowest attendance. Also should count DISTINCT meeting_id to avoid duplicate rows inflating counts.

### Item: `920` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows, not distinct meetings; duplicates per staff/meeting would inflate counts. LIMIT 1 also arbitrarily picks one id if multiple staff share the minimum.

## 🚫 Majority UNANSWERABLE

**Found 13 queries where majority of voters said UNANSWERABLE** (showing ALL)

These queries cannot be answered from the schema (missing data, ambiguous question, etc.).

### Item: `38` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Schema has only Customers; no orders or purchasing data. Cannot determine which gender orders less often to filter customers accordingly.
  - **gemini-2.5-pro** (UNANSWERABLE): The schema lacks information about customer orders. It is impossible to determine which gender 'orders less often' without an orders table or equivalent data.

### Item: `474` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema does not contain information about plane ownership. The 'pilotskills' table indicates which planes a pilot can fly, not which planes they own.
  - **gpt-5** (UNANSWERABLE): Ownership is not represented in the schema. pilotskills links pilots to planes (skills) and age, but no ownership table/column exists. Cannot determine which planes Smith owns.

### Item: `475` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema provides information on which planes pilots have skills for, but it does not contain any information about plane ownership.
  - **gpt-5** (UNANSWERABLE): Ownership isn’t modeled. The schema only shows pilot-plane skills (pilotskills) with no owner info. Cannot determine “owned” planes; the query counts planes pilots are associated with, not owned.

### Item: `476` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema provides information about pilot skills with certain planes, not plane ownership. The concept of 'owned' is not available in the provided DDL.
  - **gpt-5** (UNANSWERABLE): Ownership is not represented in the schema. 'pilotskills' captures which planes a pilot can fly, not which they own. A table/column linking pilots to plane ownership is required.

### Item: `477` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema provides information about which pilots can fly which planes (skills), but it does not contain any information about plane ownership. The question cannot be answered.
  - **gpt-5** (UNANSWERABLE): Schema lacks ownership info; pilotskills lists pilot-plane skills, not ownership. No table/column associates pilots with owned planes. The query counts planes Smith can fly, not owns.

### Item: `577` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema is missing the 'Artists' table, which is required to retrieve the painter's name for the 'ORDER BY' clause as requested in the natural language question.
  - **gpt-5** (UNANSWERABLE): Painter names are not in the schema (only painterID in paintings; Artists table not provided), so ordering by painter name as requested isn’t possible.

### Item: `645` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): No table or column records property features or their counts. With only Properties given, we can’t determine which properties have at least 2 features.
  - **gemini-2.5-pro** (UNANSWERABLE): The schema does not define what constitutes a 'feature' of a property. There is no table or set of columns that can be unambiguously interpreted and counted as 'features'.

### Item: `646` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The question is ambiguous as the term 'features' is not defined in the database schema. There is no column or table that can be used to identify and count the features of a property.
  - **gpt-5** (UNANSWERABLE): The schema has no notion of property “features” (no features table or columns to count per property). Thus we cannot count properties with >=2 features from the given schema.

### Item: `662` (DB: `bike_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The question requires filtering for 'racing bike', but the schema is missing the 'bike' table. Without it, there is no way to determine the type of bike a cyclist purchased.
  - **gpt-5** (UNANSWERABLE): Schema lacks bike details (e.g., type). Without a bike table/attributes, we cannot identify ‘racing’ bikes to determine who did not purchase any.

### Item: `802` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The provided schema contains a 'movies' table but lacks any information about 'cinemas' or the relationship between movies and cinemas. Therefore, the question cannot be answered.
  - **gpt-5** (UNANSWERABLE): Schema has only movies(Code, Title, Rating); no cinema table/columns or relationships. Cannot determine cinema names playing G or PG movies from given schema.

### Item: `803` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Schema has only movies (Code, Title, Rating). No theaters or showings tables/columns to link movies to theaters, so theater names playing G/PG movies cannot be derived.
  - **gemini-2.5-pro** (UNANSWERABLE): The question asks for the names of movie theaters, but the database schema only contains information about movies (e.g., title, rating) and does not have any data about theaters.

### Item: `921` (DB: `advertising_agencies`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema does not contain any information about meetings or staff attendance. It is impossible to determine which staff members have attended at least one meeting.
  - **gpt-5** (UNANSWERABLE): Schema lacks any meetings/attendance data. With only the staff table, we cannot determine who attended at least one meeting; only the 'details contains s' filter is possible.

### Item: `922` (DB: `advertising_agencies`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema does not contain any information about meetings or staff attendance. It is impossible to determine which staff members have attended at least one meeting.
  - **gpt-5** (UNANSWERABLE): Schema only has staff; there is no meetings/attendance table or column to identify staff who attended at least one meeting.
