# LLM Judge Semantic Validation Report

**Generated:** 2025-11-29 05:17:10

## Summary

- **Total Queries Evaluated:** 2,147
- **Majority CORRECT:** 1,409 (65.6%)
    *of which Unanimous CORRECT: 1,409 (65.6%)*
- **Majority PARTIALLY_CORRECT:** 43 (2.0%)
    *of which Unanimous PARTIALLY_CORRECT: 43 (2.0%)*
- **Majority INCORRECT:** 171 (8.0%)
    *of which Unanimous INCORRECT: 171 (8.0%)*
- **Mixed (No Majority):** 522 (24.3%)
    *(Mixed results have no consensus by definition)*
- **Majority UNANSWERABLE:** 2 (0.1%)
    *of which Unanimous UNANSWERABLE: 2 (0.1%)*

---

## ✅ Majority CORRECT (Non-Unanimous)

*No non-unanimous majority CORRECT queries found.*

## ⚡ Majority PARTIALLY_CORRECT

**Found 43 queries where majority of voters said PARTIALLY_CORRECT** (showing up to 50)

These queries are mostly correct but may have minor issues.

### Item: `19` (DB: `soccer_3`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right but may return duplicate club names if a club has multiple players with >2 wins. Use DISTINCT or GROUP BY to return unique club names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies clubs with players who have more than 2 wins, but it may return duplicate club names if a club has multiple such players. Using SELECT DISTINCT would be more accurate.

### Item: `20` (DB: `soccer_3`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns club names for players with >2 wins but may include duplicates if multiple players from the same club qualify. Use DISTINCT or GROUP BY to get unique club names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is correct, but it might return duplicate club names if a club has more than one player with over two wins. Using SELECT DISTINCT would be more precise.

### Item: `33` (DB: `soccer_3`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN, which fails if any player.Club_ID is NULL (NULL in subquery makes comparisons UNKNOWN). Use NOT EXISTS or a LEFT JOIN IS NULL to correctly find clubs without players.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is conceptually correct, but using `NOT IN` with a subquery can produce an incorrect empty result set if any row in the subquery evaluates to NULL. Since `player.Club_ID` is nullable, a `NOT EXISTS` or `LEFT JOIN` approach would be more robust.

### Item: `72` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Joins correctly identify shipped products, but results may contain duplicates if a product shipped multiple times. Use SELECT DISTINCT to return unique product name/color pairs.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies all shipped products but may return duplicate product names and colors if a product has been shipped more than once. Using SELECT DISTINCT would provide a unique list.

### Item: `151` (DB: `tv_shows`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Missing DISTINCT. Query may return duplicate transmitter names if multiple unassociated radios share the same transmitter; question asks for distinct transmitters.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing the DISTINCT keyword to return only unique transmitter names as requested by the question.

### Item: `384` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies customers based on their interactions. However, it will return duplicate customer details if a customer has more than one interaction that meets the criteria. Using SELECT DISTINCT would be more accurate.
  - **gpt-5** (PARTIALLY_CORRECT): Selects only Customer_Details instead of all customer fields, and may return duplicates (no DISTINCT). Also uses 'stuck' vs 'Stuck' case from the question.

### Item: `593` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns duplicate client names if a client ordered the book multiple times or across multiple orders. Use SELECT DISTINCT to list each client once.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies clients who ordered 'Pride and Prejudice', but it may return duplicate names if a client ordered the book more than once. Using SELECT DISTINCT would be more precise.

### Item: `677` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate rows when multiple Marlin-owned documents share the same parent; use DISTINCT to get unique parent owners.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly finds the owners of the parent documents. However, it may return duplicate owner names if multiple documents owned by 'Marlin' share the same parent. Using SELECT DISTINCT would be more precise.

### Item: `761` (DB: `sing_contest`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate original artists when multiple performances of the same song have rhythm_tempo > 5. Use DISTINCT or aggregate to return unique artists.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly filters and orders the results. However, it may return duplicate artist names if an artist has multiple songs that meet the criteria. Using SELECT DISTINCT would provide a unique list of artists.

### Item: `910` (DB: `boat_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Missing DISTINCT; may return duplicate boat names if a qualifying sailor makes multiple reservations or multiple qualifying sailors book the same boat.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate boat names if a boat is reserved by multiple sailors meeting the age criteria. Using SELECT DISTINCT would ensure a unique list of names.

### Item: `911` (DB: `boat_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is correct but might return duplicate boat names if a boat is booked by multiple sailors in the age range. Using SELECT DISTINCT T3.name would be more precise.
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and filter, but may return duplicate boat names if multiple reservations exist; use DISTINCT to list unique boat names.

### Item: `1074` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits institutions (founded >1800) with no staff. Use LEFT JOIN from institution to staff and group by institution, e.g., COUNT(T2.staff_ID), to include zero-staff institutions.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query uses an INNER JOIN, which will omit institutions founded after 1800 that have no staff members. A LEFT JOIN would be more accurate to include all such institutions, showing a count of 0.

### Item: `1082` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate conference names if multiple Canadian staff attend the same conference. Use DISTINCT to list each conference once.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may produce duplicate conference names if multiple staff from Canada attended the same conference. Using SELECT DISTINCT would provide a unique list of names.

### Item: `1083` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate conference names if multiple Canadian staff attend the same conference; add DISTINCT or GROUP BY to ensure unique conference names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies conferences attended by staff from Canada, but it will return duplicate conference names if a single conference has multiple Canadian attendees. Using SELECT DISTINCT would be more precise.

### Item: `1117` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return a pilot with NULL age as youngest since NULLs sort first. Add WHERE age IS NOT NULL to ensure the minimum actual age is selected.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query incorrectly handles NULL values in the 'age' column. In SQLite, ORDER BY ASC places NULLs first, so the query could return a pilot with an unknown age as the 'youngest'.

### Item: `1130` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts pilot-plane rows for age > 40, not unique planes. Use COUNT(DISTINCT plane_name) to get the number of planes controlled by older pilots.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts the total number of pilot-skill records for pilots over 40. To count the number of unique planes, it should use COUNT(DISTINCT plane_name).

### Item: `1131` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts pilot-plane rows, not planes. Use COUNT(DISTINCT plane_name) to count unique planes flown by pilots older than 40.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts the total number of pilot-plane pairings, not the number of distinct planes. It should use COUNT(DISTINCT plane_name) to count each plane only once.

### Item: `1132` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns duplicate pilot names if a pilot has multiple plane entries; should use DISTINCT (or GROUP BY) to list unique pilot names while ordering by age.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate pilot names if a pilot has multiple skills and falls within the age range. Using SELECT DISTINCT pilot_name would be more precise.

### Item: `1133` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate pilot names if a pilot is skilled in multiple planes. Using SELECT DISTINCT pilot_name would provide a unique list as implied by the question.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names since PilotSkills can have multiple rows per pilot. Use DISTINCT or group by pilot_name (and order by age) to return unique names.

### Item: `1134` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names since PilotSkills can have multiple rows per pilot; should deduplicate (e.g., DISTINCT or GROUP BY) when listing pilot names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly lists pilot names ordered by age, but it may return duplicate names for pilots who can fly multiple planes. Using SELECT DISTINCT would provide a unique list of pilots.

### Item: `1135` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names if a pilot has skills for multiple planes. Use DISTINCT (or group by pilot_name) to list unique pilots ordered by age DESC.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate pilot names if a pilot can fly more than one plane. Using SELECT DISTINCT pilot_name would provide a unique list of pilots, which is implied by the question.

### Item: `1152` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names if a pilot has both planes; use DISTINCT to list unique pilots.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly filters for the specified planes, but it may return duplicate pilot names if a pilot is skilled in both. Using SELECT DISTINCT would ensure a unique list of pilots.

### Item: `1153` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names if a pilot has both planes. Use SELECT DISTINCT pilot_name to list unique names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing the DISTINCT keyword. If a pilot is skilled in both the 'Piper Cub' and the 'F-14 Fighter', their name will be returned twice, which is likely not the user's intent.

### Item: `1172` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot names because pilots can have multiple plane entries. Use SELECT DISTINCT pilot_name to list unique pilot names in alphabetical order.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate pilot names if a qualifying pilot flies multiple planes. The question 'List... the names of pilots' implies a unique list, so SELECT DISTINCT pilot_name is more appropriate.

### Item: `1175` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows in PilotSkills, not unique pilots. A pilot with multiple plane entries could be counted multiple times. Should use COUNT(DISTINCT pilot_name).
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts the number of pilot-skill records, not unique pilots. A pilot meeting the age criteria who is skilled with multiple planes would be counted more than once.

### Item: `1178` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts pilot rows (skills) rather than unique pilots; should use COUNT(DISTINCT pilot_name) to match “number of all pilots.”
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies pilots older than the youngest 'Piper Cub' pilot, but it counts all their skills instead of unique pilots. Using COUNT(DISTINCT pilot_name) would be more accurate.

### Item: `1179` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows in PilotSkills rather than unique pilots. Use COUNT(DISTINCT pilot_name). Subquery for MIN age among Piper Cub pilots is correct.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts pilot-skill records, not unique pilots. A pilot with multiple skills who is older than the target age would be counted multiple times. Using COUNT(DISTINCT pilot_name) is required.

### Item: `1339` (DB: `car_road_race`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate race names if multiple qualifying drivers participate in the same race; add DISTINCT to return unique race names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate race names if multiple drivers aged 26 or older participated in the same race. Using SELECT DISTINCT would provide a unique list of races.

### Item: `1340` (DB: `car_road_race`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic and join are correct, but it can return duplicate race names if multiple >=26 drivers (or rows) map to the same race. Use DISTINCT on Race_Name to ensure unique names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing a DISTINCT keyword. If multiple drivers aged 26 or older participated in the same race, the race name will be listed multiple times.

### Item: `1399` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Missing DISTINCT: the query may return duplicate country-city pairs. Use SELECT DISTINCT country, town_city FROM Addresses to list unique countries and cities included.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly selects the country and city from the addresses table, but it may return duplicate pairs. Using SELECT DISTINCT would provide a unique list of countries and cities.

### Item: `1412` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Filter uses "%Mother" (suffix match) instead of contains; should be "%Mother%". Also consider DISTINCT to avoid duplicate age categories across multiple users.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies the age categories for users whose description contains 'Mother', but it may return duplicate age category codes. Using SELECT DISTINCT would be more precise.

### Item: `1417` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Missing DISTINCT; may return duplicate city names when multiple properties or multiple pool-feature rows exist in the same city.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies cities with properties that have a swimming pool, but it will return duplicate city names if a city has multiple such properties. Using SELECT DISTINCT would be more precise.

### Item: `1418` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and filter for swimming pool, but may return duplicate cities if multiple properties/features exist per city. Add DISTINCT to town_city.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies cities with properties that have swimming pools, but it may return duplicate city names. Using SELECT DISTINCT would be more precise.

### Item: `1514` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate receipt numbers if multiple Croissant items exist on the same receipt. Use SELECT DISTINCT ReceiptNumber to ensure unique receipts.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing the DISTINCT keyword. If a customer purchases multiple 'Croissant' items on a single receipt, that receipt number will be listed multiple times in the result.

### Item: `1620` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate country names. Using SELECT DISTINCT would provide a unique list of countries as implied by the question.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate country names if multiple drivers from the same country have >150 points; use DISTINCT (or GROUP BY) to return unique countries.

### Item: `1621` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing a DISTINCT keyword. It may return duplicate country names if multiple drivers from the same country have more than 150 points.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate countries if multiple drivers from the same country have >150 points. Use DISTINCT or GROUP BY to list each country once.

### Item: `1652` (DB: `institution_sports`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query should use SELECT DISTINCT Affiliation to return the unique set of affiliations, as the question implies a request for a set of unique values.
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate affiliations; use DISTINCT to get unique affiliations for institutions not in Vancouver.

### Item: `1777` (DB: `university_rank`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correctly sums enrollment by home_conference but uses LIMIT 1, returning only one result and missing ties for the minimum total enrollment.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query uses `ORDER BY ... LIMIT 1` to find the minimum, which will only return one conference in the case of a tie for the fewest enrolled people, while the question asks for 'conferences' (plural).

### Item: `1815` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts theater-movie rows, not unique movies. Should use COUNT(DISTINCT T2.movie) (or DISTINCT T1.code) to avoid duplicates when the same movie plays in multiple theaters.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts the total number of movie showings across all theaters. To count the number of unique movies playing, it should use COUNT(DISTINCT T1.Code).

### Item: `1824` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate titles if a movie plays in both Odeon and Imperial; add DISTINCT to return unique movie names.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query may return duplicate movie titles if a movie is shown in both 'Odeon' and 'Imperial'. Using SELECT DISTINCT would provide a unique list of movies.

### Item: `1825` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate titles if a movie appears in multiple matching theater rows. Use DISTINCT to ensure unique movie titles for Odeon or Imperial.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is correct but may produce duplicate movie titles if a movie is shown in both the 'Odeon' and 'Imperial' theaters. Using SELECT DISTINCT would be more precise.

### Item: `2080` (DB: `advertising_agencies`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns duplicate agencies when an agency has multiple clients; use DISTINCT, GROUP BY, or EXISTS to list each qualifying agency once.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies agencies with clients, but it will return duplicate rows for agencies that have more than one client. Using SELECT DISTINCT would provide a unique list of agencies.

### Item: `2081` (DB: `advertising_agencies`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns duplicate rows if an agency has multiple clients; should use DISTINCT or GROUP BY to list each qualifying agency once.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies agencies with clients, but it will return duplicate rows for an agency if it is associated with multiple clients. Using SELECT DISTINCT would provide a unique list of agencies.

## ❌ Majority INCORRECT

**Found 171 queries where majority of voters said INCORRECT** (showing ALL)

These queries are likely semantically incorrect and need review.

### Item: `35` (DB: `soccer_3`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses INTERSECT, which finds countries that have players in both earnings categories. The question asks for countries of players from either category, which requires a UNION or an OR condition.
  - **gpt-5** (INCORRECT): Uses INTERSECT, which returns countries appearing in both groups. The question asks for countries of players meeting either condition; should use OR or UNION, not INTERSECT.

### Item: `47` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query performs an EXCEPT operation on customer names, which are not unique. If two distinct customers share the same name, and one has placed an order, both will be excluded from the result.
  - **gpt-5** (INCORRECT): Anti-join is done on name fields, not customer_id. If two customers share a name and one has orders, the other wrongly disappears. EXCEPT also deduplicates names, collapsing multiple customers. Use customer_id.

### Item: `50` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts order_items rather than distinct orders and uses inner join, so products with zero orders are omitted. Should count DISTINCT t2.order_id and use LEFT JOIN to include zero-order products.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly counts the number of order items (`COUNT(*)`) instead of the number of distinct orders. It also uses an INNER JOIN, which excludes products that have never been ordered (0 orders).

### Item: `54` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses LIMIT 1, returning only one product; the question asks for all most-frequently ordered products (ties). Should return all products with the maximum order-item count.
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1` which will only return a single product. It fails to return all products if there is a tie for the most frequently ordered product, as requested by the question.

### Item: `66` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses INNER JOIN, so invoices without shipments are excluded. To return statuses and dates for all invoices, use a LEFT JOIN from Invoices to Shipments.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will only return invoices that have a corresponding shipment. To retrieve data for 'all invoices' as requested, a LEFT JOIN from the Invoices table to the Shipments table is necessary.

### Item: `78` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the total price of all items for each order, but it does not verify if the order has been paid. It should use the Invoices table to check the payment status.
  - **gpt-5** (INCORRECT): Ignores payment status. It sums all order items per order without referencing Invoices/Shipments to include only Paid items. Also uses inner joins, omitting orders with no items; not “each order.”

### Item: `108` (DB: `e_commerce`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts customers per gender instead of orders; should join Orders to Customers and compare order counts by gender. May also arbitrarily pick one on ties.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly finds the gender with the fewest customers. It should find the gender that places the fewest orders by joining with the Orders table and counting orders, not customers.

### Item: `136` (DB: `bbc_channels`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): WHERE name != 'Hank Baskett' includes channels that also have Hank as a director (if they have any other director). Use anti-join/NOT EXISTS to exclude channels linked to Hank; DISTINCT may be needed.
  - **gemini-2.5-pro** (INCORRECT): The query returns channels that have at least one director who is not 'Hank Baskett'. It should return channels that are not directed by 'Hank Baskett' at all.

### Item: `142` (DB: `tv_shows`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the `ERP_kW` column, which is of type TEXT, lexicographically. This will not produce the correct numerical order to find the largest value (e.g., '9' would be considered larger than '100').
  - **gpt-5** (INCORRECT): ERP_kW is TEXT; ORDER BY ERP_kW DESC sorts lexicographically, not numerically. Must cast to numeric (e.g., ORDER BY CAST(ERP_kW AS REAL) DESC) to find the true largest ERP_kW.

### Item: `179` (DB: `vehicle_driver`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses EXCEPT on model, so if any vehicle of a model was driven, that model is excluded even if other vehicles of that model were never driven. Should filter by vehicle_id not in vehicle_driver.
  - **gemini-2.5-pro** (INCORRECT): The query finds models for which no vehicle of that model has been driven. It should find the models of specific vehicle instances that are undriven. The use of EXCEPT on model names incorrectly removes a model if at least one vehicle with that model has been driven, even if other vehicles with the same model have not.

### Item: `180` (DB: `vehicle_driver`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes vehicles that have no drivers. This means a vehicle built by 'Ziyang' but never driven will be incorrectly omitted from the results.
  - **gpt-5** (INCORRECT): Uses inner join and groups by vehicle_driver, so vehicles built by 'Ziyang' with no driver records are excluded. Should left join and count driver_ids; also consider >=2 if 'two drivers' means at least two.

### Item: `181` (DB: `vehicle_driver`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which filters out vehicles that have no drivers. This means a vehicle built by 'Ziyang' with zero drivers will be incorrectly excluded from the result set.
  - **gpt-5** (INCORRECT): Inner join and GROUP BY on vehicle_driver exclude vehicles with no drivers. Vehicles built by 'Ziyang' without drivers must be included. Use LEFT JOIN and group by vehicle_id, counting drivers.

### Item: `341` (DB: `region_building`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns region Capital instead of region Name. Should select region.Name alongside building Address.
  - **gemini-2.5-pro** (INCORRECT): The query selects the capital of the region (T2.Capital) instead of the name of the region (T2.Name) as requested by the question.

### Item: `369` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of service interactions per customer using COUNT(*). The question asks for the most *types* of services, which requires counting the distinct services using COUNT(DISTINCT t2.Service_ID).
  - **gpt-5** (INCORRECT): Groups by Customer_Details (not guaranteed unique), potentially merging customers, and counts rows instead of distinct service types. Should group by Customer_ID and use COUNT(DISTINCT t2.Service_ID).

### Item: `372` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The subquery to find the least-used service is incorrect. It counts services in the `Services` table instead of counting service usage in the `Customers_and_Services` table.
  - **gpt-5** (INCORRECT): Least-used should be computed from usage (Customers_and_Services or interactions), not Services; counting in Services yields 1 for all and picks arbitrary service. Also fails to handle ties.

### Item: `373` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The subquery incorrectly identifies the least used service by counting its occurrences in the `services` table. It should count service usage from the `customers_and_services` table instead.
  - **gpt-5** (INCORRECT): Counts are taken from Services instead of Customers_and_Services, so service usage is miscomputed. Should aggregate over Customers_and_Services (and optionally handle ties).

### Item: `378` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses INNER JOINs across all tables, which incorrectly requires a service to be both used by a customer and have an interaction record. This will miss services that meet only one of the two conditions in the question.
  - **gpt-5** (INCORRECT): Inner joins to Customer_Interactions and Customers_and_Services force both paths. Services used by Hardy without interactions are excluded, and services rated ‘good’ may be filtered out if no CAS link exists.

### Item: `379` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly joins all tables together. This structure requires a service to have both a customer and an interaction to be considered, which is wrong for the 'OR' condition in the question.
  - **gpt-5** (INCORRECT): Inner join to customer_interactions forces services to have an interaction, excluding Hardy Kutch’s services without interactions. It also requires a CAS row, excluding services with ‘good’ interactions not in CAS. Use LEFT JOIN/UNION.

### Item: `380` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query correctly identifies services used by 'Hardy Kutch', but it incorrectly checks if those services have a 'bad' rating from *any* customer, not specifically from 'Hardy Kutch'. The join to the `customer_interactions` table is missing a condition to link the interaction back to the customer's ID (`t1.customer_id = t4.customer_id`).
  - **gpt-5** (INCORRECT): The query doesn’t ensure the ‘bad’ rating is from Hardy Kutch’s own interactions. It only matches on service_id; must also filter t4.customer_id = t1.customer_id (same customer).

### Item: `381` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query correctly identifies services used by 'Hardy Kutch' but fails to ensure that the 'bad' interaction belongs to that specific customer. It joins on service_id only, potentially matching a 'bad' interaction from a different customer.
  - **gpt-5** (INCORRECT): The query doesn’t ensure the ‘bad’ interaction is by Hardy Kutch. It joins Customer_Interactions only on service_id; should also filter t4.customer_id = t1.customer_id.

### Item: `388` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query is missing the JOIN condition between the 'customer_interactions' and 'integration_platform' tables. This results in a cross join, failing to correctly link customers to their specific failed interactions.
  - **gpt-5** (INCORRECT): Missing join between Integration_Platform and Customer_Interactions on Customer_Interaction_ID, causing a cross product. Also filter should match value 'Fail' (case-sensitive).

### Item: `389` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Missing join between integration_platform and customer_interactions; causes cartesian product. Should join t3.customer_interaction_id = t2.customer_interaction_id to filter fails per customer.
  - **gemini-2.5-pro** (INCORRECT): The query is missing the join condition between the `customer_interactions` and `integration_platform` tables. It should be `ON t2.customer_interaction_id = t3.customer_interaction_id`.

### Item: `442` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The second part of the UNION uses an INNER JOIN on the Detention table, which incorrectly excludes students with zero detentions. It should use a LEFT JOIN to include all students and correctly count their detentions.
  - **gpt-5** (INCORRECT): The detentions part uses an INNER JOIN, excluding students with 0 detentions. “Less than 2” must include 0. Use a LEFT JOIN on Detention and HAVING COUNT(T2.detention_id) < 2.

### Item: `443` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query fails to find students with zero detentions. The INNER JOIN on the Detention table excludes students who have never had a detention, but the question asks for students with less than two.
  - **gpt-5** (INCORRECT): Students with zero detentions (which satisfy “less than two”) are excluded due to INNER JOIN on Detention. Use LEFT JOIN and count detention rows to include zero-detention students.

### Item: `461` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query correctly identifies the most common detail by ordering by the total count of occurrences (`count(*)`), but it incorrectly returns the count of distinct students (`count(DISTINCT student_id)`).
  - **gpt-5** (INCORRECT): Counts distinct students but orders by total rows, so the returned count may not match the metric used to find the most common detail. Use count(*) consistently, or use DISTINCT in ORDER BY too.

### Item: `465` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly uses an EXCEPT clause. This removes students who have the most common behavior detail but also have other, less common behavior details, which is not what the question asks for.
  - **gpt-5** (INCORRECT): Using EXCEPT on bio_data removes students who also have non‑modal records and can drop correct rows if bio_data isn’t unique. Also LIMIT 1 selects only one mode, missing ties in most common details.

### Item: `468` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts event rows per type, not distinct students. Should use COUNT(DISTINCT T2.student_id) per event_type to find the type with the most students. Join to Students is unnecessary.
  - **gemini-2.5-pro** (INCORRECT): The query correctly finds the most common event type but incorrectly counts the total number of participations (`COUNT(*)`) instead of the number of unique students (`COUNT(DISTINCT student_id)`).

### Item: `500` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): It orders all class-teacher rows by transcript date and returns only one teacher (LIMIT 1). It doesn’t first identify the earliest transcript’s student and list all (DISTINCT) teachers for that student.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly uses `LIMIT 1` on the final joined result. If the student with the earliest transcript had multiple teachers, this query would only return one of them, not all of them as requested.

### Item: `501` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly returns only one teacher. If the student with the earliest transcript had multiple teachers, or if multiple students share the earliest transcript date, this query would fail to return all of them.
  - **gpt-5** (INCORRECT): Orders joined rows by transcript date and LIMIT 1, returning only one teacher. It doesn’t first select the student with the earliest transcript nor return all teachers for that student (missing DISTINCT/tie handling).

### Item: `568` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1`, which will only return one book title. It fails to return all titles if multiple books share the same lowest sale price, as requested by the question.
  - **gpt-5** (INCORRECT): Uses ORDER BY ... LIMIT 1, returning only one title. It should return all titles whose SalePrice equals the global minimum (and avoid selecting NULLs if present).

### Item: `569` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses ORDER BY ... LIMIT 1, returning only one title. The question asks for all books with the lowest sale price; should filter by SalePrice = (SELECT MIN(SalePrice) FROM Book) to include ties.
  - **gemini-2.5-pro** (INCORRECT): The query uses `ORDER BY ... LIMIT 1`, which incorrectly returns only one book title. It fails to retrieve all titles if multiple books share the same lowest sale price.

### Item: `570` (DB: `book_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `ORDER BY ... LIMIT 1`, which will only return one book title. It fails to retrieve all titles if multiple books share the same highest purchase price.
  - **gpt-5** (INCORRECT): Uses ORDER BY ... LIMIT 1, returning only one title. The question requires all titles with the maximum purchase price (including ties). Should filter by PurchasePrice = (SELECT MAX(PurchasePrice) FROM Book).

### Item: `598` (DB: `book_review`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query finds the overall maximum and minimum chapters across all books, but the question asks for the values 'for each book', which requires a GROUP BY clause.
  - **gpt-5** (INCORRECT): Returns overall max/min chapters across all books. The question asks per book; needs grouping by book (e.g., Book_ID/Title) to list each book’s min/max (which would equal its Chapters).

### Item: `632` (DB: `restaurant_bills`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Wrong inequalities. It selects nationalities with customers having Card_Credit < 50 and > 75, but the question requires > 50 and < 75. Should intersect nationalities for >50 and <75.
  - **gemini-2.5-pro** (INCORRECT): The query filters for card credit `< 50` and `> 75`. The question asks for nations with customers having card credit `> 50` and customers having card credit `< 75`.

### Item: `640` (DB: `restaurant_bills`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by Name, which can merge different customers sharing the same name. Should group by Customer_ID (and optionally Name) to aggregate per customer, then return the corresponding Name.
  - **gemini-2.5-pro** (INCORRECT): The query groups by customer name, which is not guaranteed to be unique. If two different customers share the same name, their total order quantities will be incorrectly combined.

### Item: `655` (DB: `club_leader`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause filters for clubs with an overall ranking less than 100 (`< 100`), but the question asks for clubs with a ranking higher than 100.
  - **gpt-5** (INCORRECT): Filter is reversed: uses Overall_Ranking < 100, but “higher than 100” requires > 100. Also returns Club_Name though the question asks only for leader names.

### Item: `673` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects Parent_Document_Object_ID instead of Document_Object_ID for objects owned by Marlin.
  - **gemini-2.5-pro** (INCORRECT): The query selects the Parent_Document_Object_ID, but the question asks for the Document_Object_ID of the objects owned by 'Marlin'.

### Item: `698` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query correctly identifies documents owned by 'Ransom' but then returns the IDs of those same documents. It should return the IDs of the documents that are *related to* them, which are found in the `Related_Document_Object_ID` column.
  - **gpt-5** (INCORRECT): Returns IDs of Ransom-owned documents (t1.document_object_id) instead of the related documents. Should select t1.related_document_object_id (ideally DISTINCT) where the owner of t1.document_object_id is 'Ransom'.

### Item: `699` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns the ID of the document owned by 'Ransom' itself, not the ID of the related document. It should select `t1.Related_Document_Object_ID` to find the related documents.
  - **gpt-5** (INCORRECT): Returns the Ransom-owned document IDs (t1.document_object_id), not the related document IDs. Should select t1.Related_Document_Object_ID (and possibly DISTINCT) to answer the question.

### Item: `703` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query correctly calculates the number of children for each document object, but the `LIMIT 1` clause incorrectly restricts the output to only the single object with the most children, failing to answer the "for each" part of the question.
  - **gpt-5** (INCORRECT): Uses INNER JOIN and LIMIT 1, returning only the top parent and omitting objects with zero children. The question asks counts for each document object id (including zeros), not just the max.

### Item: `704` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts only documents appearing in Document_Subset_Members; documents with zero related documents are excluded. Should LEFT JOIN from Document_Objects and count relateds (including 0) before ordering.
  - **gemini-2.5-pro** (INCORRECT): The query fails to consider documents that have zero related documents. It only queries the `Document_Subset_Members` table, so any document not present in that table will be missed, even though it has the least number (0) of relations.

### Item: `708` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query correctly identifies documents owned by Braeden that are part of a relationship, but it selects the owner of those same documents ('Braeden'). It fails to find the owner of the other document in the relationship, which is what the question asks for.
  - **gpt-5** (INCORRECT): Returns the owner of Braeden's documents (T2.Owner) instead of the owners of the other related documents. Should join to T1.Document_Object_ID to get those owners, and possibly handle both relation directions.

### Item: `709` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects Owner from the Braeden docs (T2.Owner='Braeden'), so it returns only 'Braeden'. Should filter Braeden on Document_Object_ID and return owners of Related_Document_Object_ID (DISTINCT), or handle both directions.
  - **gemini-2.5-pro** (INCORRECT): The query identifies relationships involving a document owned by 'Braeden', but it selects the owner of that same document ('Braeden') instead of the owner of the related document.

### Item: `714` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query orders the results by `count(*)`, which counts the total number of member entries per subset. The question requires ordering by the number of *distinct* documents, which should be `count(distinct t1.document_object_id)`.
  - **gpt-5** (INCORRECT): It counts distinct Document_Object_ID only, ignoring Related_Document_Object_ID. Also orders by count(*) (rows) instead of the distinct document count, ranking by pairs not unique documents.

### Item: `715` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query orders the results by the total count of rows per subset (`count(*)`), but the question asks for the subset with the most *different* documents. The ordering should be based on `count(distinct t1.document_object_id)`.
  - **gpt-5** (INCORRECT): Orders by count(*) of rows, not by distinct documents. This may pick the subset with most pairs, not most different documents. Should ORDER BY count(DISTINCT t1.document_object_id) DESC.

### Item: `718` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Unnecessary self-join misattributes subsets. It selects subset from T2 (the related doc’s own memberships) instead of the subset of the (doc, related_doc) pair. Should join T1.Document_Subset_ID to Document_Subsets.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly self-joins the `Document_Subset_Members` table. It finds subsets that the *related* document belongs to, not the subset governing the relationship itself, which is what the question asks for. A single join to `Document_Subsets` is sufficient.

### Item: `719` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses an unnecessary self-join and takes the subset from the related doc (t2.document_subset_id) instead of the actual relation (t1.document_subset_id). Should join subsets directly to t1.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly joins `document_subset_members` to itself. This logic finds the subsets that a *related* document belongs to, not the subsets that the original document is a member of, which is what the question asks for.

### Item: `727` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns the list of IDs, not the count. Need aggregation, e.g., COUNT(*) (or COUNT(DISTINCT T2.Document_Object_ID)) for collections named 'Best'.
  - **gemini-2.5-pro** (INCORRECT): The user is asking for the 'number of' document object ids, which implies a count. The query selects the list of IDs instead of using COUNT(T2.Document_Object_ID) to return the total number.

### Item: `728` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Adds an unrelated filter WHERE Collection_Name = 'Best', restricting results to one name. The query should consider all collections to find the one with the most documents.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for collections with the name 'Best' using a WHERE clause. The question asks to find the collection with the most documents among all collections, not just a specific one.

### Item: `734` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses INNER JOINs, forcing documents to exist in both a subset and a collection. The OR requires a union of either condition; docs only in one side are wrongly excluded.
  - **gemini-2.5-pro** (INCORRECT): The query uses INNER JOINs across all tables, which requires a document to be in both a document subset and a collection to be considered. The question asks for documents in either, which requires a UNION of two separate queries.

### Item: `735` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses INNER JOINs, which requires a document to be in both a subset and a collection to be considered. The question's 'or' implies finding documents that are in one, the other, or both.
  - **gpt-5** (INCORRECT): Inner joins force docs to exist in both subset and collection, violating the OR. Use UNION of docs from the subset and from the collection (or left joins). Also may miss Related_Document_Object_ID members.

### Item: `736` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Extra self-join filters out related collections that don't appear as a source. Should select T4 by joining Collections to T1.Related_Collection_ID directly.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly self-joins `Collection_Subset_Members`, which unnecessarily constrains the results. It also fails to find all related collections as it only checks for relationships in one direction.

### Item: `737` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly self-joins the `Collection_Subset_Members` table. This wrongly requires that any collection related to 'Best' must also be a source collection in another relationship, a condition not stated in the question.
  - **gpt-5** (INCORRECT): Unnecessary self-join filters out some related collections and only handles rows where 'Best' is Collection_ID. It misses cases where 'Best' is in Related_Collection_ID. Should join to related side or union both directions.

### Item: `749` (DB: `sing_contest`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses an exact match (`= 'English'`) on the `language` column. The schema example shows this column can contain multiple languages, so a `LIKE '%English%'` condition is required to correctly filter.
  - **gpt-5** (INCORRECT): Uses equality on songs.language, but languages are stored as multi-language strings (e.g., 'English , Russian'). Should use containment (e.g., LIKE '%English%') to match songs that include English.

### Item: `758` (DB: `sing_contest`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): language may list multiple languages (e.g., 'English , Russian'); filtering with = 'English' misses those. Should match songs containing 'English' (e.g., WHERE T3.language LIKE '%English%').
  - **gemini-2.5-pro** (INCORRECT): The query filters for songs where the language is exactly 'English'. Based on the schema comments (e.g., 'English , Russian'), the query should use `LIKE '%English%'` to include songs with multiple languages.

### Item: `813` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only checks for the distance in one direction (BAL to CHI). It should also check for the reverse direction (CHI to BAL) as the distance between two cities is symmetric.
  - **gpt-5** (INCORRECT): Only checks BAL→CHI. Distance “between” cities is unordered; should consider both (city1='BAL' AND city2='CHI') OR (city1='CHI' AND city2='BAL').

### Item: `814` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only checks for the distance in one direction (Boston to Newark). It fails to consider the case where the distance is stored in the opposite direction (Newark to Boston).
  - **gpt-5** (INCORRECT): Query enforces Boston as city1 and Newark as city2. The distance is undirected; it should allow either order (Boston–Newark or Newark–Boston). May return no result if only reverse exists.

### Item: `824` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where 'BAL' is the origin city (`city1_code`). It fails to include distances where 'BAL' is the destination city (`city2_code`), resulting in an incomplete total.
  - **gpt-5** (INCORRECT): Misses distances where BAL appears as city2_code; should sum rows with city1='BAL' OR city2='BAL', and exclude BAL-to-BAL if present to match 'all other cities'.

### Item: `825` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where 'BAL' is the origin city (city1_code). To find the total distance 'between' BAL and other cities, it should also include cases where 'BAL' is the destination (city2_code).
  - **gpt-5** (INCORRECT): Filters only city1_code='BAL'. Should include distances where BAL appears in either city1_code or city2_code (and exclude BAL–BAL if present) to sum all distances between BAL and other cities.

### Item: `826` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where Boston is `city1_code`. It fails to account for distances where Boston is `city2_code`, thus calculating an average over an incomplete set of data.
  - **gpt-5** (INCORRECT): Only averages distances where Boston is city1_code, ignoring rows where Boston is city2_code; also doesn’t exclude Boston-to-Boston. Should include either endpoint = Boston and exclude self before averaging.

### Item: `827` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where Boston's city code is in the `city1_code` column. It fails to check for cases where Boston's code is in the `city2_code` column, thus missing relevant data.
  - **gpt-5** (INCORRECT): Only includes distances where Boston is city1_code; ignores rows where Boston is city2_code. Should consider both sides to average all distances between Boston and other cities.

### Item: `830` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers cases where Boston is in the `city1_code` column. It will miss the correct answer if the record for the furthest city has Boston in the `city2_code` column.
  - **gpt-5** (INCORRECT): Only considers rows where Boston is city1_code. If Boston appears as city2_code (or only one row per pair is stored), it misses those distances. Must handle both directions to find the furthest city.

### Item: `832` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query fails to show all city codes as requested. It only includes cities that appear in the `Direct_distance` table, potentially omitting cities from the `City` table that have no recorded distances.
  - **gpt-5** (INCORRECT): Sums only by city1_code, missing cities appearing only as city2_code, and includes self-distances. Should consider both directions (or join City) and exclude city1_code=city2_code.

### Item: `834` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average distance to all cities, but the question asks for the average distance to 'all other cities'. The query should exclude distances where the origin and destination cities are the same.
  - **gpt-5** (INCORRECT): Includes self-distances (no city1_code <> city2_code), contradicting “other cities.” Also starts from Direct_distance with inner join, so cities lacking city1 rows are omitted (not “all” cities).

### Item: `836` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only finds the distance in one direction (Linda's city to Tracy's city). It will fail if the distance is stored in the reverse order in the Direct_distance table.
  - **gpt-5** (INCORRECT): Joins only match when Linda’s city is city1 and Tracy’s is city2. It fails if the distance is stored in reverse order; should handle both (city1,city2) and (city2,city1) pairings.

### Item: `837` (DB: `address_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only finds the distance if Linda Smith's city is `city1_code` and Tracy Kim's city is `city2_code`. It fails to consider the case where the cities are reversed in the `Direct_distance` table.
  - **gpt-5** (INCORRECT): Assumes ordered pair (Linda’s city = city1, Tracy’s = city2). If Direct_distance stores only the reverse, it returns nothing. Should handle both orders (OR/UNION) to get the distance between the cities.

### Item: `854` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The phrase 'older than any sailors' implies finding the sailor(s) with the maximum age. The query incorrectly finds all sailors except for the youngest by comparing age against the minimum age.
  - **gpt-5** (INCORRECT): Misinterprets “older than any” as > MIN(age), returning everyone older than the youngest. It should find those older than all others, e.g., age = (SELECT MAX(age) FROM Sailors).

### Item: `856` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The phrase 'older than any sailors' implies being older than at least one sailor in the group. The query should use `> MIN(age)`. The current query uses `> (SELECT age ...)` which is incorrect as the subquery can return multiple rows.
  - **gpt-5** (INCORRECT): Uses MIN(age) instead of MAX(age); it selects sailors older than the youngest with rating>7, not older than all such sailors. Should use age > (SELECT MAX(age) ...) or a > ALL subquery.

### Item: `878` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses MIN(rating) for Luis; should compare to MAX(rating) (or use > ALL) to ensure ratings are higher than every Luis. Current query returns those only higher than the lowest Luis.
  - **gemini-2.5-pro** (INCORRECT): The phrase 'higher than any sailor named Luis' means the rating must be greater than the rating of at least one sailor named Luis. This is equivalent to being greater than the minimum rating. The query correctly implements this logic.

### Item: `879` (DB: `boat_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Wrong aggregation: compares to MIN(rating) of Luis. For “higher than any Luis,” it should compare to MAX(rating) (or use > ALL). Current query allows ratings below some Luis’ rating.
  - **gemini-2.5-pro** (INCORRECT): The query finds sailors with a rating greater than the minimum rating of a 'Luis'. The phrase 'higher than any sailor named Luis' requires the rating to be greater than the maximum rating among all sailors named 'Luis'.

### Item: `927` (DB: `headphone_store`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): The HAVING clause uses COUNT(*) > 2, which returns classes with more than two headphones. It should use COUNT(*) <= 2 to find classes that do not contain more than two.
  - **gemini-2.5-pro** (INCORRECT): The query's HAVING clause `count(*) > 2` finds classes with *more than* two headphones. The question asks for classes with *not more than* two headphones, which requires the condition `count(*) <= 2`.

### Item: `977` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns distinct pairs of (venue, year), which can result in the same venue appearing multiple times. The question asks for a list of distinct venues.
  - **gpt-5** (INCORRECT): Returns distinct (venue, year) pairs, not distinct venues. To order venues by year you’d need one year per venue (e.g., MIN(year)) and then sort; current query doesn’t match the question.

### Item: `992` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The question asks for the list to be in ascending order of the number of papers, but the query uses `ORDER BY count(*) DESC`, which sorts the results in descending order.
  - **gpt-5** (INCORRECT): Orders by count DESC instead of ASC; counts Author_list rows (duplicates per paper) rather than distinct papers; inner join excludes affiliations with zero papers.

### Item: `993` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of author-paper associations using COUNT(*), not the number of distinct papers for each affiliation as requested. It should use COUNT(DISTINCT T2.paper_id).
  - **gpt-5** (INCORRECT): Counts author-paper rows instead of distinct papers and excludes affiliations with no papers due to INNER JOIN. Should use LEFT JOIN and COUNT(DISTINCT T2.paper_id).

### Item: `1006` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by cited_paper_id but selects paper_id, yielding an arbitrary citing paper id. Should select cited_paper_id with COUNT(*) to return the most cited paper’s id and its citation count.
  - **gemini-2.5-pro** (INCORRECT): The query selects `paper_id`, which is the ID of the paper doing the citing. It should select `cited_paper_id` to return the ID of the paper that was cited, as requested by the question.

### Item: `1007` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects paper_id while grouping by cited_paper_id. Should return cited_paper_id as the most cited paper’s id. Current query may return an arbitrary citing paper, not the cited one.
  - **gemini-2.5-pro** (INCORRECT): The query selects `paper_id` which is the ID of the paper making the citation, but the question asks for the ID of the paper being cited. The query should select `cited_paper_id` instead.

### Item: `1010` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts are per cited_paper_id but the query selects paper_id (the citing paper). Must select cited_paper_id (optionally join to Paper for titles). Current select is mismatched/non-deterministic.
  - **gemini-2.5-pro** (INCORRECT): The query correctly groups by `cited_paper_id` to count citations, but it incorrectly selects `paper_id` (the citing paper) instead of `cited_paper_id` (the paper that was cited).

### Item: `1011` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by cited_paper_id but selects paper_id, yielding arbitrary/non-matching values. Should select cited_paper_id (and optionally join to Paper for titles) with COUNT(*) and ORDER BY count DESC LIMIT 10.
  - **gemini-2.5-pro** (INCORRECT): The query correctly counts citations by grouping by `cited_paper_id`, but it incorrectly selects `paper_id` (the citing paper) instead of `cited_paper_id`. This mismatches the citation counts with the wrong papers.

### Item: `1025` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of authorships per affiliation (`count(*)`) instead of the number of distinct papers. A paper with multiple authors from the same affiliation will be counted multiple times.
  - **gpt-5** (INCORRECT): Counts Author_list rows, overcounting papers with multiple authors from the same affiliation. Should count distinct papers per affiliation (e.g., COUNT(DISTINCT T1.paper_id)).

### Item: `1048` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The subquery groups by paper ID (`T1.cited_paper_id`) but selects the author ID (`T2.author_id`). For a paper with multiple authors, this will only return one arbitrary author, not all of them, leading to an incorrect final count.
  - **gpt-5** (INCORRECT): Subquery groups by cited_paper_id but selects author_id, so it keeps only one arbitrary author per highly cited paper. Co-authors are missed, so some should-be-excluded authors remain, inflating the count.

### Item: `1049` (DB: `aan_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The subquery incorrectly identifies authors of highly-cited papers. It groups by paper ID (`T1.cited_paper_id`) but selects author ID (`T2.author_id`), which means for a paper with multiple authors, only one arbitrary author will be returned, not all of them.
  - **gpt-5** (INCORRECT): Subquery groups by cited_paper_id but selects author_id; SQLite’s permissive GROUP BY returns one arbitrary author per highly cited paper, missing coauthors. Not all such authors are excluded.

### Item: `1080` (DB: `conference`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Missing filter for nationality. Should restrict to staff where Nationality = 'United States' before computing MAX and MIN ages.
  - **gemini-2.5-pro** (INCORRECT): The query calculates the maximum and minimum age for all staff but fails to filter for only those from the 'United States' using a WHERE clause.

### Item: `1096` (DB: `conference`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly returns institutions that have at least one staff member who did not participate in a 2004 conference. The question asks for institutions where *no* staff members participated at all in 2004.
  - **gpt-5** (INCORRECT): Uses staff-level NOT IN, so it returns institutions with any non‑participating staff even if others did participate. Inner join to staff also drops institutions with no staff. Need NOT EXISTS per institution.

### Item: `1097` (DB: `conference`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns institutions that have at least one staff member who did not participate in a 2004 conference. It should return institutions where *no* staff members participated in a 2004 conference.
  - **gpt-5** (INCORRECT): Filters per staff_id; returns institutions with some non-participating staff even if others did participate. Also inner join excludes institutions with no staff. Use NOT EXISTS at institution level.

### Item: `1112` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts skill rows, not unique pilots. Should count DISTINCT pilot_name where age > 40.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of pilot-skill entries, not the number of unique pilots. A pilot with multiple skills would be counted multiple times. It should use COUNT(DISTINCT pilot_name).

### Item: `1113` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of pilot-skill records, not the number of unique pilots. A pilot over 40 with skills for multiple planes will be counted more than once.
  - **gpt-5** (INCORRECT): Counts rows in PilotSkills, not unique pilots. A pilot can have multiple plane skill rows. Use COUNT(DISTINCT pilot_name) WHERE age > 40 to count pilots.

### Item: `1140` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses ORDER BY instead of WHERE, so the condition doesn’t filter rows. Also counts pilot-skill rows, not unique pilots; should use COUNT(DISTINCT pilot_name) with age > 40 OR age < 30.
  - **gemini-2.5-pro** (INCORRECT): The query uses an ORDER BY clause for filtering. The condition on age should be in a WHERE clause to filter the rows before counting them.

### Item: `1141` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses ORDER BY instead of WHERE, so no filtering by age occurs. Also counts rows, not distinct pilots; pilots with multiple plane skills would be double-counted.
  - **gemini-2.5-pro** (INCORRECT): The query uses an ORDER BY clause to apply the condition on age. ORDER BY is used for sorting results, not filtering them. A WHERE clause is needed to filter pilots based on their age.

### Item: `1158` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): pilot_name is neither grouped nor tied to max(age); SQLite may return an arbitrary pilot per plane, not the oldest. Must select pilot(s) where age equals the per-plane maximum.
  - **gemini-2.5-pro** (INCORRECT): The query finds the max age per plane but returns an arbitrary pilot's name from that group, not the pilot corresponding to that max age. This is due to selecting a non-aggregated, non-grouped column.

### Item: `1159` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by plane_name but selects pilot_name with max(age), so pilot_name may not correspond to the oldest (SQLite picks arbitrary). Also fails to return all oldest pilots in case of ties.
  - **gemini-2.5-pro** (INCORRECT): The query selects `pilot_name` which is not in the `GROUP BY` clause. This means the returned `pilot_name` is not guaranteed to be the pilot corresponding to the `max(age)` for each plane.

### Item: `1160` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): pilot_name is not linked to the max(age) per plane; due to GROUP BY it returns an arbitrary pilot for each plane and does not return all names in case of ties.
  - **gemini-2.5-pro** (INCORRECT): The query selects `pilot_name` which is not in the GROUP BY clause. This will return an arbitrary pilot's name for each plane, not necessarily the name of the pilot with the maximum age.

### Item: `1161` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Non-aggregated pilot_name with GROUP BY returns arbitrary pilot, not necessarily the oldest. Also returns only one pilot per plane, failing to include ties for oldest pilots.
  - **gemini-2.5-pro** (INCORRECT): The query correctly finds the maximum age for each plane but returns an arbitrary pilot's name from that group, not necessarily the name of the oldest pilot.

### Item: `1173` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly finds pilots older than the *minimum* age of 'Piper Cub' pilots. The question asks for pilots older than *any* 'Piper Cub' pilot, which requires comparing to the *maximum* age.
  - **gpt-5** (INCORRECT): Compares age to MIN(age) of Piper Cub pilots; should be > MAX(age) or > ALL to mean older than every such pilot. Also missing DISTINCT may return duplicate pilot names.

### Item: `1176` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Queries PilotSkills instead of Hangar, limiting results to planes with skilled pilots. The task is to list all planes; should filter Hangar.plane_name LIKE '%Bomber%'.
  - **gemini-2.5-pro** (INCORRECT): The query uses the `PilotSkills` table, which may not contain all planes. To find *all* planes, it should query the `Hangar` table, which is the definitive source for all plane names.

### Item: `1184` (DB: `district_spokesman`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the sum of the population for all districts first, and then applies the ORDER BY and LIMIT to the single aggregated result. It should first find the top 3 districts by area and then sum their populations.
  - **gpt-5** (INCORRECT): It sums all districts’ populations. ORDER BY/LIMIT apply after aggregation, so top-3 by area_km aren’t selected before SUM. Must first pick 3 largest areas (e.g., subquery) then sum population.

### Item: `1230` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses inner join, so artists with zero paintings are excluded. If the longest-lived artist has no paintings, result is wrong (should be 0). Use LEFT JOIN and order by lifespan across all artists.
  - **gemini-2.5-pro** (INCORRECT): The query finds the painting count for the longest-lived artist who has at least one painting. Due to the INNER JOIN, it will not consider artists who have no paintings, even if they lived the longest.

### Item: `1242` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly adds a filter condition `mediumOn = "canvas"` which is not specified in the natural language question.
  - **gpt-5** (INCORRECT): Adds an unnecessary filter mediumOn='canvas'. The question asks for the artist’s birth year for any painting in 1884, regardless of medium/support.

### Item: `1245` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts mediums only from Paintings; the question asks for numbers of works by medium, which should include Sculptures as well. Combine both tables (UNION ALL) and group by medium.
  - **gemini-2.5-pro** (INCORRECT): The query only counts works from the 'paintings' table. The question asks for all 'works', which should include data from the 'sculptures' table as well.

### Item: `1246` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts only paintings. “Works” should include both paintings and sculptures; need to union mediums from both tables and group by medium.
  - **gemini-2.5-pro** (INCORRECT): The query only counts works from the `Paintings` table. The question asks for all "works", which should also include data from the `Sculptures` table.

### Item: `1287` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selecting max(height_mm) with a non-aggregated paintingID returns an arbitrary id in SQLite. It doesn’t ensure the id corresponds to the maximum-height pre-1900 painting.
  - **gemini-2.5-pro** (INCORRECT): The query is semantically incorrect because it selects a non-aggregated column 'paintingID' alongside an aggregate function 'max(height_mm)'. This structure is logically flawed, as it attempts to retrieve a group-level value and a row-level value simultaneously. While this may produce the intended result in SQLite due to a special feature for min/max, it is not a semantically valid way to express the query's intent.

### Item: `1288` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses MAX(height_mm) with a non-aggregated paintingID, yielding an arbitrary id. It doesn’t ensure the id corresponds to the tallest pre-1900 painting. Should select the row with the max height.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly selects a non-aggregated column `paintingID` alongside an aggregate function `max(height_mm)`. This returns the correct max height but an arbitrary painting ID, not the ID of the tallest painting.

### Item: `1291` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query orders the results by the painting's title (`ORDER BY title`), but the question asks to order by the painter's name. This requires joining with the `Artists` table.
  - **gpt-5** (INCORRECT): Groups by painter but orders by Paintings.title instead of painter name, and doesn’t join Artists to access names. It also returns painterID rather than ordering by (or showing) the painter’s name.

### Item: `1292` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Orders by painting title instead of painter name and doesn’t join Artists to get names. Should group by painter and order by artist name (e.g., lname/fname).
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly orders the results by the painting's title (`title`) instead of the painter's name. It needs to join with the `Artists` table to order by the artist's name.

### Item: `1295` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses INNER JOIN, so artists with zero paintings (who also satisfy “at most 3”) are excluded. Should use LEFT JOIN and count paintings per artist.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will exclude artists with zero paintings. The condition 'at most 3 paintings' should include artists with 0, 1, 2, or 3 paintings.

### Item: `1296` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner join drops artists with 0 paintings; question includes <4 (0–3). Use LEFT JOIN and group by artist, HAVING COUNT(t2.paintingID) < 4 to include zero-painting artists.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes artists who have created zero paintings. The condition 'less than 4 paintings' should include artists with 0, 1, 2, or 3 paintings.

### Item: `1313` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Row-wise filter misses location-level constraint. Need locations with any pre-1885 painting AND no painting at that location with mediumOn='canvas'. Current query may include locations that also have canvas works.
  - **gemini-2.5-pro** (INCORRECT): The query finds locations with a painting that is both pre-1885 and not on canvas. It fails to exclude locations that also contain other paintings that *are* on canvas.

### Item: `1321` (DB: `car_road_race`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Should list constructors per driver ordered by driver age. DISTINCT collapses multiple drivers sharing a constructor and breaks age-based ordering. Use SELECT Constructor FROM driver ORDER BY Age ASC.
  - **gemini-2.5-pro** (INCORRECT): The query selects a distinct list of constructors but orders by driver's age. This is ambiguous because a single constructor can be associated with multiple drivers of different ages. The resulting order is non-deterministic and does not correctly reflect the sorting requested in the question.

### Item: `1425` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Wrong columns. It selects search_seq and omits search_string; grouping by user_id returns an arbitrary search_seq per user. Need user_id with search_string for users having count(*) >= 2.
  - **gemini-2.5-pro** (INCORRECT): The query correctly identifies users who searched at least twice. However, due to the GROUP BY on user_id, it only returns a single, arbitrary search_seq for each user, not all of their searches.

### Item: `1426` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by user_id but selects search_seq, yielding an arbitrary sequence per user. Should list all search_seq for users with >=2 searches (e.g., WHERE user_id IN (subquery) without grouping).
  - **gemini-2.5-pro** (INCORRECT): The query groups by user_id but selects the non-aggregated column search_seq. This returns only one arbitrary search sequence per user, not all search sequences for users with two or more searches.

### Item: `1447` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): It ignores Property_Features. Grouping Properties by property_id gives count=1 per row, so HAVING >=2 returns none. Should group Property_Features by property_id (COUNT DISTINCT feature_id) and then count those properties.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly counts rows from the `Properties` table. To find the number of features per property, it should count rows in the `Property_Features` table grouped by `property_id`.

### Item: `1448` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Must count features per property from Property_Features (e.g., COUNT(DISTINCT feature_id)) and then count those >= 2. Current query groups Properties (1 row per property) and won’t yield the desired count.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly counts rows in the `Properties` table. To count features for each property, it should query the `Property_Features` table, group by `property_id`, and then count the properties that meet the criteria.

### Item: `1467` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): EXCEPT on search_string removes any value used by owners, even if also searched by non-owners. Should filter searches by users with no properties (e.g., WHERE NOT EXISTS on owner_user_id), not by string values.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly uses EXCEPT on the search_string. This will exclude a search term if it was searched by both a property owner and a non-owner, which is wrong. The logic should first identify users who do not own property, and then retrieve all of their searches.

### Item: `1469` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses INNER JOIN to User_Searches, excluding users with 0 searches. “At most twice” should include 0,1,2. Should use LEFT JOIN and count(User_Searches rows) <= 2.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN to count user searches, which incorrectly excludes users with zero searches. The condition 'at most twice' should include users with 0, 1, or 2 searches.

### Item: `1531` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses MAX(price) of Tarts; should compare to MIN(price) (or use < ALL) to get goods priced less than every Tart. Current query returns items below the most expensive Tart, not all Tarts.
  - **gemini-2.5-pro** (INCORRECT): The phrase 'less than any Tart' means the price should be less than the price of at least one Tart. This is equivalent to being less than the maximum price of a Tart. The query incorrectly uses MIN instead of MAX.

### Item: `1550` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Operator precedence makes it return all Cookies regardless of price. Need parentheses or IN: (food IN ('Cookie','Cake')) AND price BETWEEN 3 AND 7.
  - **gemini-2.5-pro** (INCORRECT): Due to SQL operator precedence, the query is interpreted as `WHERE food = 'Cookie' OR (food = 'Cake' AND price BETWEEN 3 AND 7)`. This incorrectly returns all cookies, regardless of their price.

### Item: `1551` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Operator precedence makes it select all Cookies regardless of price. Need parentheses so price filter applies to both: (food='Cookie' OR food='Cake') AND price BETWEEN 3 AND 7.
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause is logically incorrect due to operator precedence. The query returns all cookies regardless of price, plus cakes priced between 3 and 7. The `OR` conditions for food type should be grouped with parentheses.

### Item: `1557` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns only the minimum price, not the good. Should return the good (e.g., Id or Food) with Flavor='Cheese' that has the lowest Price (handling ties if needed).
  - **gemini-2.5-pro** (INCORRECT): The question asks for the 'cheapest good', which implies returning the name or ID of the good. The query returns only the minimum price, not information about the good itself.

### Item: `1574` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Should compare price to twice the average: price > 2 * (SELECT AVG(price) FROM goods). Query compares only to the average, not double.
  - **gemini-2.5-pro** (INCORRECT): The query compares the price to the average price, but the question asks for prices above twice the average. The WHERE clause is missing the multiplication by 2.

### Item: `1575` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Compares price to AVG(price) only. To match “more than twice as expensive,” it should be price > 2 * (SELECT AVG(price) FROM goods).
  - **gemini-2.5-pro** (INCORRECT): The query compares the price to the average price, but the question asks for goods that are more than *twice* the average price. The condition should be `price > 2 * (SELECT avg(price) FROM goods)`.

### Item: `1588` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): It averages prices across all items per customer. The question requires each good bought by the customer to be >5 (e.g., HAVING MIN(T1.Price) > 5 or NOT EXISTS goods with Price <= 5).
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average price of all items a customer purchased. The question asks for the 'average spending for each good', which implies the calculation should be per good, not per customer.

### Item: `1602` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by Team instead of Make; it filters duplicate team names, not makes with multiple teams. Should group by Make and count teams (e.g., COUNT(*) or COUNT(DISTINCT Team_ID)) HAVING > 1.
  - **gemini-2.5-pro** (INCORRECT): The query groups by `team` instead of `make`. To find makes associated with more than one team, the aggregation should be on the `make` column.

### Item: `1603` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by team instead of make. Should group by make to count how many teams each make has: GROUP BY make HAVING COUNT(*) > 1.
  - **gemini-2.5-pro** (INCORRECT): The query groups by `team` instead of `make`. To find makes associated with more than one team, the aggregation should be on the `make` column, not the team name.

### Item: `1612` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Points is TEXT; ORDER BY Points DESC sorts lexicographically, not numerically. Cast to a number (e.g., ORDER BY CAST(Points AS INTEGER) DESC) to correctly order by points.
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. The query will perform a lexicographical (alphabetical) sort, not a numerical sort as intended by the question. This will lead to incorrect ordering (e.g., '9' > '100').

### Item: `1613` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. The query performs a lexicographical sort instead of a numerical sort, which will result in an incorrect order (e.g., '9' > '80').
  - **gpt-5** (INCORRECT): Orders by Points as TEXT, causing lexicographic (not numeric) sorting. Should cast Points to a number, e.g., ORDER BY CAST(Points AS INTEGER) DESC, to match “by points” intent.

### Item: `1622` (DB: `car_racing`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query performs a lexicographical sort on the `Points` column, which is of type TEXT. This will not correctly identify the driver with the highest numerical point value (e.g., '9' would be sorted after '100').
  - **gpt-5** (INCORRECT): Points is TEXT; ORDER BY T2.Points sorts lexicographically, not numerically. Must cast to a number (e.g., ORDER BY CAST(T2.Points AS INTEGER) DESC) to get the true max before returning the capital.

### Item: `1677` (DB: `institution_sports`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses SUM(enrollment) producing a single total, but the question asks to return all individual enrollments. Also filters use lowercase 'vancouver'/'calgary', which may not match case-sensitive values.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly calculates the sum of enrollments. The question asks to return all individual enrollment values for the specified cities, not their total.

### Item: `1696` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Does not aggregate by content. It picks the content of the single highest-value box, not the content with the highest total value across all boxes. Should GROUP BY contents and ORDER BY SUM(value).
  - **gemini-2.5-pro** (INCORRECT): The query finds the content of the single box with the highest value, not the content with the highest *total* value across all boxes. It is missing a GROUP BY Contents and SUM(Value).

### Item: `1704` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns the count of distinct locations, not the list of distinct warehouse locations requested.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of distinct locations, but the question asks to find and list the actual distinct locations.

### Item: `1705` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): The question asks for the distinct warehouse locations, but the query returns the count of distinct locations. It should select DISTINCT Location values, not COUNT.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of distinct warehouse locations, but the question asks for the actual list of locations. The COUNT aggregation is incorrect.

### Item: `1728` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses MIN(value) instead of MAX/ALL. The request is for boxes with value greater than every 'Rocks' box; this query only requires > minimum 'Rocks' value, allowing false positives.
  - **gemini-2.5-pro** (INCORRECT): The phrase 'higher than the value of any boxes' means the value should be greater than the value of ALL boxes with 'Rocks'. The query should use MAX() in the subquery, not MIN().

### Item: `1729` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Should compare against the maximum value of Rocks boxes (or use > ALL). Using MIN returns boxes only greater than the lowest Rocks value, not all.
  - **gemini-2.5-pro** (INCORRECT): The query finds boxes with a value greater than the minimum value of a 'Rocks' box. The phrase 'greater than the value of any box' implies being greater than all of them, which requires using MAX, not MIN.

### Item: `1732` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the value of a single box, not the sum of values for all boxes. The `ORDER BY ... LIMIT 1` reduces the result set to one row before the `SUM` can aggregate all boxes in the target warehouse.
  - **gpt-5** (INCORRECT): Query sums all boxes. ORDER BY/LIMIT on an aggregate single row doesn’t select the max-capacity warehouse. Must first pick warehouse with MAX(capacity) and then sum its boxes’ values.

### Item: `1733` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query orders all individual boxes by their warehouse's capacity and then applies SUM to only the first row due to LIMIT 1. It fails to sum the values of all boxes within the highest capacity warehouse.
  - **gpt-5** (INCORRECT): Sums values across all warehouses; ORDER BY/LIMIT on non-grouped capacity doesn’t restrict to the max-capacity warehouse. Need to filter to warehouse with MAX(capacity) before summing.

### Item: `1747` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts distinct locations, not distinct warehouses. Warehouses sharing the same location would be collapsed; should count DISTINCT warehouse codes (or T2.code).
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of distinct warehouse locations, but the question asks for the number of distinct warehouses. It should count distinct warehouse codes (e.g., COUNT(DISTINCT T2.Code)).

### Item: `1798` (DB: `university_rank`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query filters for universities with an overall rank of 5 or greater (`>= 5`), but the question asks for universities with a rank of 5 or below (`<= 5`).
  - **gpt-5** (INCORRECT): Filter direction is wrong. Query uses rank >= 5, but “rank 5 or below” means rank <= 5. Should be WHERE T2.rank <= 5.

### Item: `1799` (DB: `university_rank`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query filters for universities with a rank of 5 or above (rank >= 5), but the question asks for universities with a rank of 5 or below (rank <= 5).
  - **gpt-5** (INCORRECT): Filter condition is reversed. Query uses rank >= 5, but the question requires universities with rank <= 5 (5 or below).

### Item: `1804` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Should filter with WHERE rating IS NULL; comparing to the string 'null' won’t return movies whose rating is actually NULL.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly compares the rating to the string literal 'null'. To check for missing values (NULLs), the `IS NULL` operator should be used instead of `= 'null'`.

### Item: `1805` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filters for the string 'null' instead of SQL NULL. To find movies without ratings, it should use WHERE rating IS NULL.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for the string literal 'null'. To find movies with no rating (i.e., where the value is NULL), the condition should be `WHERE rating IS NULL`.

### Item: `1822` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns movie titles instead of theater names and lacks join to MovieTheaters. Should join on MovieTheaters.Movie = Movies.Code and select MovieTheaters.Name where rating IN ('G','PG').
  - **gemini-2.5-pro** (INCORRECT): The query selects movie titles from the `Movies` table, but the question asks for the names of the cinemas. The query needs to join with the `MovieTheaters` table and select the `Name` column.

### Item: `1823` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects movie titles and does not join MovieTheaters. Need to join Movies to MovieTheaters and return MovieTheaters.Name for movies with rating 'G' or 'PG'.
  - **gemini-2.5-pro** (INCORRECT): The query selects movie titles from the Movies table, but the question asks for the names of movie theaters, which are in the MovieTheaters table. A JOIN between the two tables is required.

### Item: `1840` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by rating and returns counts per rating, not a single total. Also compares to the string 'null' instead of using IS NOT NULL.
  - **gemini-2.5-pro** (INCORRECT): The query groups the results by rating, providing a count for each rating instead of the single total count requested. Additionally, it incorrectly filters for the string 'null' instead of using `IS NOT NULL`.

### Item: `1841` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by rating and returns multiple counts instead of a single total. Also filters with rating != 'null' rather than IS NOT NULL.
  - **gemini-2.5-pro** (INCORRECT): The query groups by rating, which returns a count for each rating type, not the total count of movies with a rating. The WHERE clause should use `IS NOT NULL` instead of `!= 'null'`.

### Item: `1844` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filters for the string 'null' instead of SQL NULL. Should use WHERE Movie IS NULL to find theaters not showing a movie.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly checks for null values. It compares the 'Movie' column to the string literal 'null' (`= 'null'`) instead of using the correct SQL operator `IS NULL`.

### Item: `1845` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Theaters not showing any movie have Movie = NULL. Query uses Movie = 'null' (a string), which won’t match NULL. Should filter with WHERE Movie IS NULL.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly compares the `Movie` column to the string literal 'null'. To find cinemas not showing any movies, it should check for `NULL` values using `WHERE Movie IS NULL`.

### Item: `1852` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Unrated implies NULL ratings; query compares to string 'null'. Should use WHERE rating IS NULL to return unrated movies.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for the string literal 'null'. To find unrated movies where the rating value is absent, the condition should be `WHERE rating IS NULL`.

### Item: `1853` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Unrated should be rows with Rating IS NULL. The query compares to the literal string 'null' instead of using IS NULL, so it misses actual NULL ratings.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for the string literal 'null'. To check for missing or unknown values (unrated), the `IS NULL` operator should be used instead of `= 'null'`.

### Item: `1854` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly attempts to filter out NULL values by comparing with the string 'null'. The correct SQL syntax is `WHERE Movie IS NOT NULL`. This error can lead to incorrect results if NULLs are present.
  - **gpt-5** (INCORRECT): Subquery uses Movie != 'null' (string) instead of handling NULLs properly. This can mis-handle NULLs and exclude Movie=0, yielding wrong results with NOT IN. Use IS NOT NULL or NOT EXISTS.

### Item: `1855` (DB: `movie_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly attempts to filter NULL values by comparing to the string literal 'null'. The correct SQL syntax to check for non-null values is `IS NOT NULL`.
  - **gpt-5** (INCORRECT): Wrong NULL handling: Movie != 'null' miscompares types and NOT IN can fail with NULLs. Use IS NOT NULL (or NOT EXISTS) to exclude NULLs and correctly find movies with no theater rows.

### Item: `1869` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns package IDs, not the count. Needs aggregation (e.g., COUNT(*)) to get the number of packages sent by Leo Wong.
  - **gemini-2.5-pro** (INCORRECT): The user is asking for the number of packages, which requires a COUNT aggregation. The query returns a list of package numbers instead of the total count.

### Item: `1874` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns package numbers, not a count. INTERSECT on PackageNumber ignores Shipment (PK is Shipment,PackageNumber), causing false matches. Should filter sender and recipient in the same row and COUNT.
  - **gemini-2.5-pro** (INCORRECT): The user asks for the count of packages, but the query returns a list of package numbers. It is missing the required COUNT aggregation.

### Item: `1875` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns the list of package numbers that meet the criteria, but the question asks for 'How many packages', which requires a count of the results (e.g., using COUNT).
  - **gpt-5** (INCORRECT): Returns package numbers, not a count. It intersects only on PackageNumber (ignoring Shipment), so may match different packages across shipments. Should filter sender and recipient on the same row and COUNT(*)

### Item: `1878` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Name filter should use LIKE '%John%' to match names containing John. Also selects PackageNumber with MAX(Weight) without tying them; PackageNumber may not correspond to the max-weight row.
  - **gemini-2.5-pro** (INCORRECT): The query filters for clients with the exact name 'John' (`LIKE "John"`), but the question asks for clients where 'John' is part of the name. The correct condition should be `LIKE '%John%'`.

### Item: `1879` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Name filter uses LIKE 'John' without wildcards, not matching “something similar”. Also selects PackageNumber with max(Weight) without tying them; returns arbitrary PackageNumber, not the heaviest package.
  - **gemini-2.5-pro** (INCORRECT): The query uses an aggregate function MAX() on one column while selecting a non-aggregated column 'PackageNumber' without a GROUP BY clause. This will return the correct maximum weight, but an arbitrary package number from the filtered rows, not necessarily the one corresponding to the heaviest package.

### Item: `1901` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses OR between planet and manager filters. Should use AND to return shipments on Mars that Turanga Leela manages; current query includes Mars shipments by others or Leela’s elsewhere.
  - **gemini-2.5-pro** (INCORRECT): The query uses `OR` in the WHERE clause, but the question requires shipments that are both on planet Mars AND managed by Turanga Leela. The correct logical operator is `AND`.

### Item: `1915` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Selects PackageNumber rows instead of counting them. Should use COUNT(*) with the same joins/filters to return the number of packages.
  - **gemini-2.5-pro** (INCORRECT): The user is asking for the 'number of packages', which requires an aggregation function like COUNT. The query incorrectly selects the individual package numbers instead of counting them.

### Item: `1917` (DB: `planet_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): The question asks for the number (count) of packages, but the query returns PackageNumber rows. It should aggregate, e.g., SELECT COUNT(*) ... with the same joins and WHERE conditions.
  - **gemini-2.5-pro** (INCORRECT): The user is asking for the 'number of packages', which implies an aggregation (COUNT). The query returns a list of package numbers instead of the total count.

### Item: `1936` (DB: `video_game`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `developers != 'Nintendo'`, which only excludes games where the developer string is exactly 'Nintendo'. It will fail to exclude games where Nintendo is a co-developer, such as 'Nintendo / GameFreak'.
  - **gpt-5** (INCORRECT): The WHERE clause only excludes exact 'Nintendo'. Co-developed entries (e.g., 'Nintendo / GameFreak') would be included. Use NOT LIKE '%Nintendo%' (or similar) to exclude any game involving Nintendo.

### Item: `1937` (DB: `video_game`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filter is wrong: developers != 'Nintendo' only excludes exact matches. It will include multi-developer entries like 'Nintendo/GameFreak'. Should exclude any containing 'Nintendo' (e.g., NOT LIKE '%Nintendo%').
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause `developers != 'Nintendo'` only excludes games where the developer is exactly 'Nintendo'. It will incorrectly include games co-developed by Nintendo (e.g., 'Nintendo / GameFreak').

### Item: `1944` (DB: `video_game`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses <= 3, but the question asks for rank smaller than 3, which requires < 3.
  - **gemini-2.5-pro** (INCORRECT): The question asks for players with a rank 'smaller than 3', which translates to the condition `< 3`. The query incorrectly uses `<= 3`, which includes players with a rank of exactly 3.

### Item: `1969` (DB: `video_game`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses INTERSECT, yielding games with both Oklahoma and Auburn players (AND). The question asks for OR; should use UNION or WHERE college IN ('Oklahoma','Auburn') with DISTINCT to avoid duplicates.
  - **gemini-2.5-pro** (INCORRECT): The question asks for games played by players from 'Oklahoma' OR 'Auburn' college. The query uses INTERSECT, which incorrectly finds games played by players from 'Oklahoma' AND 'Auburn'.

### Item: `1979` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query calculates the overall average and maximum profit across all presses, but fails to group the results for 'each press' as requested. A GROUP BY clause is missing.
  - **gpt-5** (INCORRECT): Computes overall average and max across all presses. The question asks per press; needs grouping by press (e.g., GROUP BY Press_ID/Name) and to return one row per press.

### Item: `1994` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Sale_Amount` column is of type TEXT. The query performs a lexicographical (string) sort instead of a numerical sort, which will not correctly identify the books with the highest sales.
  - **gpt-5** (INCORRECT): Orders by sale_amount as TEXT, causing lexicographic sorting instead of numeric. Must cast sale_amount to a numeric type to get the true top 5 best-selling books.

### Item: `1995` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): sale_amount is TEXT; ORDER BY sorts lexicographically, not numerically. Cast to numeric (e.g., ORDER BY CAST(sale_amount AS REAL) DESC) to get true top 5 by amount.
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'sale_amount' column, which is of type TEXT, lexicographically instead of numerically. This will lead to an incorrect ranking (e.g., '9' would be ranked higher than '100').

### Item: `2004` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query is incorrect because it sorts the `Sale_Amount` column, which is of type TEXT, lexicographically. To find the 'best sales', it should cast this column to a numeric type for proper numerical sorting.
  - **gpt-5** (INCORRECT): Orders by Sale_Amount as TEXT, leading to lexicographic (not numeric) ranking. To get the true top 3 by sales, cast Sale_Amount to a numeric type (e.g., CAST(t2.Sale_Amount AS REAL)) before ordering.

### Item: `2005` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'Sale_Amount' column, which is of type TEXT, lexicographically. To find the 'best selling' books, it should be cast to a numeric type for proper numerical sorting.
  - **gpt-5** (INCORRECT): Orders by Sale_Amount as TEXT; lexicographic sort can misrank. Cast to numeric for true top 3.

### Item: `2011` (DB: `book_press`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Orders by Sale_Amount as TEXT, causing lexicographic rather than numeric sorting. Must cast to numeric (e.g., ORDER BY CAST(t2.Sale_Amount AS REAL) DESC) to identify the true best seller.
  - **gemini-2.5-pro** (INCORRECT): The `Sale_Amount` column is of type TEXT. Ordering by this column will result in a lexicographical (alphabetical) sort, not a numerical sort, which is required to find the 'best selling' book.

### Item: `2056` (DB: `cre_Doc_Workflow`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts staff assignments, not document processes. Should count distinct (document_id, process_id) per staff_role_code to get number of document processes for each role.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of staff assignments per role (COUNT(*)). The question asks for the number of document processes, which requires counting the distinct pairs of (document_id, process_id).

### Item: `2114` (DB: `advertising_agencies`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups only Payments; invoices with zero payments are omitted. Use Invoices LEFT JOIN Payments and COUNT(Payments.payment_id) to include all invoice ids.
  - **gemini-2.5-pro** (INCORRECT): The query fails to show invoices that have zero payments. It should query the `Invoices` table and use a LEFT JOIN to include all invoices, not just those present in the `Payments` table.

### Item: `2128` (DB: `advertising_agencies`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups only by meeting_type and omits client identifier. To show counts for each client, include client_id (or client details) and group by client and meeting_type.
  - **gemini-2.5-pro** (INCORRECT): The query groups by meeting type only, but the question asks for the number of meetings for each client. The query should also group by client and select the client identifier.

### Item: `2142` (DB: `advertising_agencies`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Query ignores meeting attendance. It selects staff only by details and uses COUNT(*)>=1 on the Staff table, which is trivial. Needs a join to Staff_in_Meetings to ensure at least one meeting attended.
  - **gemini-2.5-pro** (INCORRECT): The query does not check if the staff attended any meetings. It only filters the `Staff` table. A join with `Staff_in_Meetings` is required to count the meetings for each staff member.

### Item: `2143` (DB: `advertising_agencies`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Missing join to Staff_in_Meetings to enforce attendance. HAVING COUNT(*)>=1 on Staff rows is always true; query returns all staff with 's' in details regardless of meetings.
  - **gemini-2.5-pro** (INCORRECT): The query fails to check if the staff member has attended any meetings. It is missing a join with the `Staff_in_Meetings` table to verify meeting attendance.

## ⚠️ Mixed (No Majority)

**Found 522 queries with mixed voter verdicts (no majority)** (showing ALL)

These queries have no clear majority verdict and require manual review.

### Item: `8` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Excludes clubs with NULL Manufacturer; these should be included as not Nike. Use WHERE Manufacturer IS NULL OR Manufacturer <> 'Nike' (and DISTINCT if duplicate names possible).

### Item: `27` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns one manufacturer with highest count, but in case of ties it arbitrarily picks one; query also counts NULL manufacturers, which may not be intended.

### Item: `28` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL manufacturers, so it could return NULL as most common; also returns an arbitrary value in case of ties. Add WHERE Manufacturer IS NOT NULL and tie-handling if needed.

### Item: `29` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct grouping and HAVING, but it may return NULL as a manufacturer if multiple clubs have NULL. Add WHERE Manufacturer IS NOT NULL to avoid that.

### Item: `30` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right for counting manufacturers across clubs, but it may include NULL as a manufacturer if multiple clubs have NULL. Add WHERE Manufacturer IS NOT NULL to avoid that.

### Item: `34` (DB: `soccer_3`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): NOT IN on subquery can fail if player.Club_ID contains NULLs, causing no rows to match. Use NOT EXISTS or filter NULLs in the subquery.
  - **gemini-2.5-pro** (CORRECT)

### Item: `44` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner JOIN omits orders with no items, violating “for every order.” Use LEFT JOIN and COUNT(T2.order_item_id) to include zero counts. Also consider COUNT(DISTINCT T2.product_id) if distinct products are intended.

### Item: `45` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only the single MIN date instead of dates for all earliest orders, and UNION deduplicates dates so multiple qualifying orders on the same date collapse into one value.

### Item: `46` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): UNION deduplicates dates, collapsing multiple orders that share the same date. The question asks for dates of all such orders. Use UNION ALL or include order_id to avoid deduplication.

### Item: `48` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Subtracts by (first_name, middle_initial, last_name) instead of customer_id. If two customers share the same name and one has orders, the other (with no orders) is wrongly excluded. Use NOT EXISTS/LEFT JOIN on customer_id.

### Item: `52` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts order items, not distinct products. Orders with two items of the same product will qualify. Use COUNT(DISTINCT T2.product_id) to ensure at least two products.

### Item: `53` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts order-item rows, not orders. Use COUNT(DISTINCT T2.order_id) to measure how many orders list each product; duplicates within the same order could be overcounted.

### Item: `57` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per payment method; duplicates per customer-method could skew results. Use COUNT(DISTINCT customer_id) for true popularity by customers. Tie handling not specified.

### Item: `58` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per payment method, not distinct customers. Should use COUNT(DISTINCT customer_id) to avoid duplicate entries inflating counts.
  - **gemini-2.5-pro** (CORRECT)

### Item: `60` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts order-item rows per gender, not products. To answer “how many products,” use COUNT(DISTINCT T3.product_id); current query overcounts when the same product is bought multiple times.

### Item: `64` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so customers without a payment method are excluded. For “all customers,” a LEFT JOIN from Customers to Customer_Payment_Methods is needed to include those with no method (NULL).

### Item: `67` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicates if a shipment has multiple order items of the same product. Use SELECT DISTINCT product_name, shipment_date to list unique product–shipment date pairs.

### Item: `68` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns shipped products with shipment dates, but may produce duplicate product–shipment rows and returns full datetime instead of just the day requested.

### Item: `71` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Joins are appropriate, but it may return duplicates if an order item appears in multiple shipments; lacks DISTINCT/grouping to ensure one row per shipped order item.

### Item: `75` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Orders link to Invoices only through Shipments. For orders not shipped (no Shipment rows), there is no way to associate any invoice to those orders in this schema.

### Item: `76` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Orders and invoices are only linked via Shipments. For unshipped orders there’s no Shipment row, so their associated invoice/status (if any) can’t be determined from this schema.

### Item: `102` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts shipment-item rows, not products. Should join Shipment_Items to Order_Items and count DISTINCT product_id to get how many products have been shipped.
  - **gemini-2.5-pro** (CORRECT)

### Item: `105` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Averages product_price across all order items (duplicating products), not across distinct products that were ordered. Use DISTINCT product_id to average unique ordered products.

### Item: `106` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Averages product_price over order items, weighting products ordered multiple times. To get the average price of products that were ordered at least once, average over distinct product_id (e.g., via GROUP BY).

### Item: `107` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correctly finds customers of a least-common gender, but if multiple genders tie for least-common, it selects only one due to LIMIT 1 instead of returning all tied genders.
  - **gemini-2.5-pro** (CORRECT)

### Item: `109` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows in Customer_Payment_Methods, so duplicates could inflate method count. Should use COUNT(DISTINCT T2.payment_method_code) >= 2. Otherwise logic matches the question.

### Item: `110` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Should count distinct payment methods to avoid duplicates inflating the count. Use COUNT(DISTINCT T2.payment_method_code). Otherwise correct.

### Item: `120` (DB: `e_commerce`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Filters with product_price != max(...) exclude rows where product_price IS NULL. Such products are not at the maximum price but will be omitted.

### Item: `121` (DB: `bbc_channels`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is correct, but may return duplicate names if multiple directors share the same name. Use SELECT DISTINCT name to ensure unique names if required.

### Item: `130` (DB: `bbc_channels`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so channels with zero programs are omitted. A LEFT JOIN from channel to program would include all channels as requested (“for each channel”).
  - **gemini-2.5-pro** (CORRECT)

### Item: `131` (DB: `bbc_channels`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN, which fails if program.channel_id contains NULL (returns no rows). Use NOT EXISTS or filter NULLs in subquery to handle NULL-safe logic.

### Item: `132` (DB: `bbc_channels`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and filter, but may return duplicate names if multiple 'Dracula' program rows share the same director. Use DISTINCT to ensure unique director names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `138` (DB: `tv_shows`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `ERP_kW` column is of type TEXT. The query will perform a lexicographical (alphabetical) sort instead of the required numerical sort, leading to an incorrectly ordered result.
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct table/column but orders ERP_kW as text, yielding lexicographic not numeric order. Should cast to numeric (e.g., ORDER BY CAST(ERP_kW AS REAL)) to match ‘kW’ intent.

### Item: `143` (DB: `tv_shows`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query applies an aggregate function AVG on a TEXT column `ERP_kW`. In SQLite, if a TEXT value cannot be converted to a number, it is treated as 0, which will result in an incorrect average.
  - **gpt-5** (CORRECT)

### Item: `149` (DB: `tv_shows`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the `ERP_kW` column, which is of type TEXT, lexicographically. The question requires a numerical sort based on the ERP value, which will result in an incorrect order (e.g., '9' > '10').
  - **gpt-5** (PARTIALLY_CORRECT): Orders by ERP_kW as TEXT, causing lexicographic (not numeric) sort. Should cast ERP_kW to numeric (e.g., CAST(ERP_kW AS REAL)) for correct descending ERP order. Joins/columns are correct.

### Item: `150` (DB: `tv_shows`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts city channels per transmitter correctly, but INNER JOIN omits radios with no associations. Use LEFT JOIN from radio to include transmitters with zero count.

### Item: `154` (DB: `vehicle_driver`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate names if multiple drivers share the same name; use SELECT DISTINCT name to list unique names.

### Item: `161` (DB: `vehicle_driver`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Excludes vehicles with zero drives. It only counts vehicle_ids present in vehicle_driver. To include vehicles never driven (0 counts), aggregate from vehicle with a LEFT JOIN to vehicle_driver.

### Item: `174` (DB: `vehicle_driver`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing a DISTINCT keyword. The question asks for 'Which car models', which implies a unique list. The current query could return duplicate model names if multiple vehicles of the same model meet the criteria.

### Item: `175` (DB: `vehicle_driver`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query compares the 'total_production' column, which is of type TEXT, with an integer. This comparison will not work as intended in SQL, as it will perform a lexicographical comparison instead of a numerical one.
  - **gpt-5** (CORRECT)

### Item: `190` (DB: `vehicle_driver`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicates if a driver has multiple 'DJ1' vehicle rows; needs DISTINCT or GROUP BY to list unique drivers.
  - **gemini-2.5-pro** (CORRECT)

### Item: `191` (DB: `vehicle_driver`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate drivers if multiple vehicles share model 'DJ1'. Use DISTINCT on name/citizenship to return unique drivers.

### Item: `199` (DB: `online_exams`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses != which filters out NULL Subject_Code rows. If NULLs should count as not 'Database', add OR Subject_Code IS NULL (i.e., WHERE Subject_Code <> 'Database' OR Subject_Code IS NULL).

### Item: `242` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): product_name isn’t unique; the query may return multiple prices if several ‘Monitor’ products exist. Use DISTINCT or ensure uniqueness to return a single price.

### Item: `251` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate product_name values if multiple products share a name; use DISTINCT to return unique names only.

### Item: `256` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly finds a cheapest Hardware product, but may return a NULL-priced item as cheapest and, if multiple share the minimum price, the chosen row is arbitrary due to no tie-break.

### Item: `257` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): If any Hardware products have NULL price, ORDER BY ASC LIMIT 1 may return a NULL-priced item as “cheapest.” Add WHERE product_price IS NOT NULL or use MIN() to avoid this.

### Item: `278` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL payment_method_code; could return NULL as most used if many customers have missing codes.

### Item: `280` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns customers for only one least-used payment_method_code; ties are ignored. Also fails if the least-used code is NULL since '=' won’t match NULL.

### Item: `281` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Finds a least-common payment method but picks only one; ties are not handled (others omitted). Also may return duplicate names since DISTINCT isn’t used.

### Item: `284` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct column/table, but it may include NULL as a distinct value. Add WHERE payment_method_code IS NOT NULL to return only actual payment methods used.

### Item: `285` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Query may include NULL as a method; add WHERE payment_method_code IS NOT NULL to list only actual codes customers use.

### Item: `294` (DB: `customers_and_orders`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, so customers with zero orders are omitted despite “all customer names, ids”. Should LEFT JOIN Customers to Customer_Orders and COUNT(order_id).

### Item: `295` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN on Customer_Orders, so customers with no orders are excluded. For "each customer", use a LEFT JOIN from Customers and count orders grouped by customer_id.

### Item: `304` (DB: `customers_and_orders`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on product_name, not product_id. If product names aren’t unique, names tied to any ordered product are excluded even when another product with the same name has no orders. Filter by product_id.

### Item: `305` (DB: `customers_and_orders`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Compares by product_name instead of product_id. If any product with a given name is ordered, that name is excluded even for unordered products. Should anti-join on product_id to get correct results.

### Item: `314` (DB: `customers_and_orders`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): For the “more than 3 products” condition it counts item rows (COUNT(*)) instead of distinct products. Should use COUNT(DISTINCT T2.product_id). Other logic and UNION are fine.

### Item: `315` (DB: `customers_and_orders`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query performs a string comparison on the `order_quantity` column (`VARCHAR`) instead of a numerical comparison. It should cast `order_quantity` to an integer to correctly filter for quantities greater than 6.
  - **gpt-5** (PARTIALLY_CORRECT): Counts order items with COUNT(*) instead of distinct products. For “more than 3 products,” it should use COUNT(DISTINCT T2.product_id) to avoid overcounting duplicate product lines.

### Item: `327` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate region names; likely expects unique names. Use SELECT DISTINCT Name to ensure uniqueness while ordering alphabetically.

### Item: `335` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN; buildings with NULL or non-matching Region_ID would be excluded. A LEFT JOIN from building to region would ensure all buildings are returned as requested.

### Item: `347` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not handle NULL Completed_Year values; could return NULL as the top “year.” Add WHERE Completed_Year IS NOT NULL or use COUNT(Completed_Year).

### Item: `348` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN, which fails if building.Region_ID contains NULLs (could return no rows). Prefer NOT EXISTS or exclude NULLs in the subquery.

### Item: `349` (DB: `region_building`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if building.Region_ID contains NULL, the predicate fails and may return no rows. Use NOT EXISTS or LEFT JOIN to handle regions with no buildings correctly.

### Item: `357` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate channel details; use DISTINCT if a unique list is intended.

### Item: `360` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts NULLs via COUNT(*); if many NULLs, it may return NULL as the most common “type code.” Filter NULLs or use COUNT(analytical_layer_type_code) to count actual codes.

### Item: `362` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate services if multiple rows exist for the same customer-service pair. Use DISTINCT to ensure a unique list of services used by the customer.

### Item: `363` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and filter, but may return duplicate service_details if multiple links exist. Use DISTINCT to ensure unique services.

### Item: `364` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts customer–service associations, not usage times. Should count rows in Customer_Interactions per Service_ID and join to Services to return service_details where count > 3.

### Item: `365` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): 'More than 3 times' implies counting usage events. Query counts Customers_and_Services links (users), not times. Should count rows in Customer_Interactions per service (HAVING COUNT(*) > 3).

### Item: `366` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts rows in Customers_and_Services and groups by Customer_Details. 'Most times' should be counted from Customer_Interactions, and grouping should be by Customer_ID to avoid merging same-name customers.

### Item: `367` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by Customer_Details instead of Customer_ID, which can merge different customers sharing the same details. Also should use COUNT(DISTINCT t2.Service_ID) to count used services accurately.

### Item: `368` (DB: `government_shift`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of service records for each customer using COUNT(*), not the number of distinct types of services. It should use COUNT(DISTINCT t2.Service_ID) to be correct.
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows instead of distinct service types; use COUNT(DISTINCT t2.service_id). Also groups by customer name rather than ID, which can merge same-named customers.

### Item: `370` (DB: `government_shift`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): NOT IN may fail if Customers_and_Services.Customer_ID contains NULLs (SQLite treats NULL in subquery as unknown, yielding no matches). Use NOT EXISTS, LEFT JOIN IS NULL, or filter out NULLs.
  - **gemini-2.5-pro** (INCORRECT): The query only checks the `Customers_and_Services` table to identify customers who have used a service. It fails to also check the `Customer_Interactions` table, which also links customers to services.

### Item: `371` (DB: `government_shift`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `NOT IN` on a subquery that can return NULL values for `customer_id`. If any NULL is present, the `NOT IN` condition will not evaluate to true, leading to an incorrect empty result set.
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right, but NOT IN fails if Customers_and_Services.customer_id contains NULLs (returns no rows). Use NOT EXISTS or filter NULLs in the subquery.

### Item: `375` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts distinct Customers_and_Services_Details values, not the total available details. Use COUNT(*) or COUNT(Customers_and_Services_Details) to count all entries (column is NOT NULL).

### Item: `385` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic and joins are correct, but it may return duplicate customers if they have multiple qualifying interactions. Use DISTINCT (or GROUP BY) on customer_details to list unique customers.

### Item: `390` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Computes unused services by service_details, not by Service_ID. If two services share the same details, results are wrong. Use anti-join/NOT IN on Service_ID and then return Service_Details.

### Item: `391` (DB: `government_shift`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Compares by Service_Details instead of Service_ID. If two services share the same details and one is used, the unused one’s details are excluded. Should filter by Service_ID (e.g., LEFT JOIN/NOT EXISTS).

### Item: `394` (DB: `government_shift`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic and joins are correct with DISTINCT, but the filter uses "unsatisfied" (lowercase). If values are stored as 'Unsatisfied', the case mismatch may return no rows; use case-insensitive match.

### Item: `418` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one customer. If multiple customers share the maximum membership_credit, others are omitted; should return all with the maximum value.

### Item: `424` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses inner join, so vehicles with no rentals are omitted. For “each vehicle,” a LEFT JOIN from Vehicles to Renting_history (with COALESCE on SUM) is needed to include zero-hour vehicles.

### Item: `425` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits vehicles with no rentals. For “each vehicle,” use LEFT JOIN from Vehicles and COALESCE(SUM(total_hours),0) to include zero-hour vehicles.

### Item: `426` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if renting_history.vehicles_id contains NULL, the predicate evaluates to UNKNOWN for all rows and may return none. Use NOT EXISTS or filter NULLs in subquery.

### Item: `427` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): NOT IN can fail if renting_history.vehicles_id contains NULL, causing all rows to be excluded. Use NOT EXISTS or LEFT JOIN to correctly find vehicles never rented.

### Item: `433` (DB: `vehicle_rent`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN; excludes vehicles never rented. To include all vehicles and sort by total hours (including 0), use LEFT JOIN from Vehicles and COALESCE(SUM(total_hours),0).

### Item: `444` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): EXCEPT is applied on teacher_details, which may not be unique. A teacher with matching details who teaches a 'net%' class could wrongly exclude another. Use teacher_id for exclusion (e.g., NOT EXISTS) and then select details.

### Item: `445` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Filters and EXCEPT operate on teacher_details, which may not be unique. A different teacher with the same details who teaches a 'net%' class would wrongly exclude eligible teachers. Use teacher_id-based filtering.

### Item: `451` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts rows in Classes (including multiple students per class), not courses. Should count DISTINCT class_id per teacher to find who teaches the most courses.

### Item: `454` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOINs, so students without addresses are excluded. For “all the students,” a LEFT JOIN from Students to Students_Addresses (and Ref_Address_Types) is needed to include those with no address.

### Item: `457` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN via Students_Addresses, excluding students with no address. For “each student,” LEFT JOIN from Students is needed. It may also yield duplicates when multiple address records exist.

### Item: `458` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, which omits students without transcripts. To list all students, use LEFT JOIN from Students to Transcripts (showing NULL date where none).

### Item: `459` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Use LEFT JOIN from Students to Transcripts to include all students; the INNER JOIN excludes students without a transcript date.
  - **gemini-2.5-pro** (CORRECT)

### Item: `460` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Ranks results by total rows (count(*)) instead of number of students (count(DISTINCT student_id)). This can select the wrong “most common result among students.” Should order by distinct count.

### Item: `462` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts Behaviour_Monitoring rows instead of distinct students for the “obtained by 3 students” condition; should use COUNT(DISTINCT student_id). Also selects only one mode if there’s a tie.

### Item: `463` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): INTERSECT is on (bio_data, student_details), so different students with identical text can be conflated; it should intersect by student_id. Also counts use COUNT(*) instead of COUNT(DISTINCT student_id) for “3 students.”

### Item: `464` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): EXCEPT operates on bio_data values, not student_id. If multiple students share the same bio_data, results are conflated and wrong. Qualify by student_id first, then select bio_data.

### Item: `469` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts event rows instead of distinct students. To find the event type most students joined, use COUNT(DISTINCT T2.student_id) grouped by event_type_code (and keep the join to Ref_Event_Types).
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of event participations using COUNT(*), but the question asks for the number of unique students. It should use COUNT(DISTINCT T1.student_id).

### Item: `482` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Joins are correct, but without DISTINCT it may return duplicate teacher–student pairs if they share multiple classes. Use DISTINCT or include class_details to disambiguate per class.

### Item: `483` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns teacher-student pairs via Classes, but may include duplicates when a teacher and student share multiple classes. Use DISTINCT to list unique pairs of details.

### Item: `484` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts classes per teacher and returns the maximum, but LIMIT 1 returns only one teacher. If multiple teachers tie for the max, others are omitted. Should return all max-tying teachers or define a tiebreaker.

### Item: `486` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly counts classes per student and returns the max, but LIMIT 1 arbitrarily picks one student in case of ties; does not return all students with the maximum number of courses.

### Item: `492` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate students if a student has multiple loans above average; use DISTINCT or GROUP BY student to list each student once.
  - **gemini-2.5-pro** (CORRECT)

### Item: `493` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Can return duplicate students if a student has multiple above-average loans; use DISTINCT or GROUP BY student to return each student once.
  - **gemini-2.5-pro** (CORRECT)

### Item: `494` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY ... LIMIT 1, which may return NULL if any date_of_loan is NULL. Use MIN(date_of_loan) or add WHERE date_of_loan IS NOT NULL to ensure the earliest actual date.

### Item: `495` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Ordering with LIMIT 1 may return NULL first if any NULL dates exist. Use MIN(date_of_loan) or filter WHERE date_of_loan IS NOT NULL to get the earliest actual date.

### Item: `496` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY ... LIMIT 1, so it picks a single student and ignores ties. Should return all students whose loan equals the global minimum (e.g., WHERE amount_of_loan = (SELECT MIN(...))) and use DISTINCT.

### Item: `497` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL loan amounts; in SQLite, NULLs sort first and could be chosen as “smallest.” Add WHERE T2.amount_of_loan IS NOT NULL to avoid this.

### Item: `498` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Finds the student with the largest loan via ORDER BY, but if that student has multiple transcripts it returns an arbitrary one, and ties on max loan pick an arbitrary student. Needs tie/aggregation logic.

### Item: `499` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Picks a transcript arbitrarily if the student has multiple (no order specified). Also treats “largest amount of loan” as the largest single loan, not highest total per student, which may not match intent.

### Item: `502` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly sums loans per student in Student_Loans, but omits students with no loans. If “each student” is literal, need LEFT JOIN from Students and COALESCE(SUM,0).

### Item: `503` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Excludes students with no loans; 'for each student' suggests including all students from Students with 0 total. Should LEFT JOIN Students and COALESCE SUM to 0.

### Item: `504` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, omitting students with no classes. To cover “each student,” use LEFT JOIN and COUNT(T2.class_id) so students without classes appear with a count of 0.

### Item: `505` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): INNER JOIN drops students with zero courses; question asks for each student. Use LEFT JOIN and COUNT(T2.class_id) (and group by student_id, bio_data) to include students with 0 classes.

### Item: `510` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): EXCEPT is applied on bio_data, not student identity. If two students share the same bio_data and one has a loan, both are excluded. Should compute difference by student_id, then return bio_data.

### Item: `511` (DB: `cre_Students_Information_Systems`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is applied on bio_data, not student_id. If two students share the same bio_data and one has a loan, the other’s value is excluded too. Exclude by student_id, then project bio_data.

### Item: `530` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOINs, so books without an Author_Book link are omitted. To satisfy “all book titles,” use LEFT JOIN from Book to Author_Book and Author.

### Item: `532` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Use LEFT JOIN instead of INNER JOIN to ensure all orders are returned; current join may drop orders lacking a matching client row despite 'all order ids' requirement.

### Item: `534` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so authors with no books are omitted. To include all authors (with zero counts), use LEFT JOIN and count a right-side column, e.g., COUNT(T2.ISBN).

### Item: `535` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, so authors with no books are omitted despite “all the authors.” Should use LEFT JOIN and COUNT(T2.ISBN) to include zero counts.

### Item: `536` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts orders per ISBN only for books appearing in Books_Order. Does not include books with zero orders, despite “all book isbns”. Use LEFT JOIN from Book and COUNT(IdOrder) to include zeros.

### Item: `537` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts orders per ISBN only for those appearing in Books_Order; books never ordered are omitted. For “each book,” left join Book to Books_Order and group to include zero counts.
  - **gemini-2.5-pro** (CORRECT)

### Item: `538` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Sums amounts per ISBN from Books_Order only, so books with no orders are omitted. To show all book ISBNs (including zero), use LEFT JOIN from Book and COALESCE(SUM(amount),0).

### Item: `539` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Excludes books with no orders. It aggregates only from Books_Order, while the question asks for all books’ ISBNs and their total ordered (zero if none). Should LEFT JOIN Book to Books_Order with COALESCE(SUM,0).
  - **gemini-2.5-pro** (CORRECT)

### Item: `545` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query does not filter for orders that occurred 'in the past'. It is missing a join with the 'Orders' table and a WHERE clause to check the 'DateOrder' column.

### Item: `548` (DB: `book_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits clients with zero orders. To include all client names, use LEFT JOIN from Client to Orders and COUNT(T1.IdOrder).
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will only return clients who have placed at least one order. The question asks for "all client names", which implies clients with zero orders should also be included.

### Item: `549` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, so clients with no orders are excluded. To list all clients and their order counts (including zero), use LEFT JOIN from Client to Orders and COUNT(Orders.IdOrder).

### Item: `553` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses inner joins from Orders, so clients without orders are omitted. Question asks for all clients. Should LEFT JOIN from Client and COALESCE(SUM(amount),0) to include zero totals.

### Item: `556` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Operates at title level. If any book with a given title has an order, the title is removed entirely, excluding orderless copies. Should check by ISBN (e.g., NOT EXISTS on Books_Order) and then select titles.

### Item: `557` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Subtracting by title causes false negatives when different books share the same title: if one is ordered, the title is removed for all. The anti-join must be done by ISBN (e.g., WHERE NOT EXISTS on Books_Order).

### Item: `558` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is on Name, not client identity. If two clients share a name and one has orders, the name is removed, wrongly excluding the non-ordering client. EXCEPT also de-duplicates names.

### Item: `559` (DB: `book_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on Name, so clients sharing a name are collapsed. If one homonymous client ordered, all with that name are excluded. Should anti-join by IdClient (e.g., LEFT JOIN/NOT EXISTS).

### Item: `566` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic matches the question, but it may return duplicate titles if multiple rows share the same title. Use SELECT DISTINCT title to ensure unique titles.

### Item: `571` (DB: `book_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY ... LIMIT 1, returning a single title. The question asks for all titles with the maximum purchase price; should return all ties via WHERE purchaseprice = (SELECT MAX(purchaseprice) FROM Book).
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1`, which will only return a single book title. If multiple books share the same highest purchase price, the query will incorrectly omit the other titles.

### Item: `579` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate titles if multiple Author rows named 'Plato' link to the same book. Use DISTINCT to ensure unique titles.

### Item: `580` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Joins and filters are semantically correct, but it may return duplicate author names if multiple ISBNs share the title (e.g., editions). Use DISTINCT to ensure unique authors.

### Item: `582` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate titles if a book has multiple authors whose names contain 'Plato'. Use SELECT DISTINCT to ensure unique titles.

### Item: `583` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Semantically correct joins and filter, but may return duplicate titles if a book has multiple authors whose names contain 'Plato'. Add DISTINCT to ensure unique titles.

### Item: `585` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts line items, not distinct orders. If multiple ISBNs share the title within the same order, it overcounts. Use COUNT(DISTINCT T2.IdOrder) instead.

### Item: `592` (DB: `book_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate client names if a client has multiple orders containing the book. Use DISTINCT to list each client once.
  - **gemini-2.5-pro** (CORRECT)

### Item: `602` (DB: `book_review`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join restricts to books with reviews; if the max-chapters book lacks a review, it picks another book. Also ties (or multiple reviews) make LIMIT 1 non-deterministic. Prefer LEFT JOIN and tie-break.

### Item: `604` (DB: `book_review`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Orders by Rank ascending, returning the lowest (best) rank, not the highest. Should use ORDER BY T2.Rank DESC (and optionally handle ties).

### Item: `609` (DB: `book_review`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and ordering by Rating, but may return duplicate titles if a book has multiple reviews. Use DISTINCT or aggregate to ensure unique titles if that’s intended.

### Item: `610` (DB: `book_review`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so books without reviews are omitted despite asking for all books. May also produce duplicates if a book has multiple reviews. Use LEFT JOIN and deduplicate/aggregate per book.

### Item: `611` (DB: `book_review`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): NOT IN is unsafe if review.Book_ID can be NULL; a NULL in the subquery makes all comparisons UNKNOWN, possibly yielding 0. Use NOT EXISTS or filter NULLs in the subquery.
  - **gemini-2.5-pro** (CORRECT)

### Item: `614` (DB: `book_review`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Anti-join is done on (type,title) instead of Book_ID. If two books share the same type and title, a rated one will remove an unrated one. Should exclude via Book_ID (e.g., NOT EXISTS).

### Item: `625` (DB: `restaurant_bills`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not handle ties: if multiple customers share the highest membership level, ORDER BY ... LIMIT 1 returns an arbitrary card credit. Should filter by MAX level and handle ties explicitly.

### Item: `630` (DB: `restaurant_bills`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Doesn’t handle ties: LIMIT 1 will return an arbitrary nationality if multiple nationalities have the same highest count. Should return all max-tied nationalities or add a deterministic tiebreaker.

### Item: `637` (DB: `restaurant_bills`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by customer Name instead of Customer_ID, so same-name customers get combined; also INNER JOIN excludes customers with no orders. Use LEFT JOIN and GROUP BY T1.Customer_ID, T1.Name.

### Item: `638` (DB: `restaurant_bills`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by name only, which can merge different customers sharing the same name. Should group by customer_id (and name). Also consider LEFT JOIN if customers with zero orders must be included.

### Item: `639` (DB: `restaurant_bills`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Groups by Name, which can merge different customers sharing the same name and miscompute totals. Should group by Customer_ID (and optionally Name) to sum per customer.
  - **gemini-2.5-pro** (CORRECT)

### Item: `648` (DB: `club_leader`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Case-sensitive comparison to "england" may not exclude values stored as "England". Use proper case or a case-insensitive compare (e.g., nationality <> 'England' or COLLATE NOCASE).

### Item: `650` (DB: `club_leader`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one name even if multiple members share the maximum age; LIMIT 1 picks an arbitrary oldest member. Use WHERE Age = (SELECT MAX(Age) FROM member) to include ties.

### Item: `652` (DB: `club_leader`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Finds the most frequent nationality, but includes NULL nationalities and lacks tie-breaking; could return NULL or an arbitrary nationality when counts tie.

### Item: `653` (DB: `club_leader`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May include NULL as a nation if two or more members have NULL nationality. Add a filter (e.g., WHERE Nationality IS NOT NULL) to exclude unknown nations.

### Item: `656` (DB: `club_leader`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns Club_Name in addition to names, while the question asks only for names. Also may need DISTINCT to avoid duplicate names if a member leads multiple clubs.

### Item: `657` (DB: `club_leader`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly assumes the leader is defined in the `club_leader` table. The schema has a dedicated `Team_Leader` column in the `club` table, which should be used to find the leader's name.
  - **gpt-5** (PARTIALLY_CORRECT): Joins club_leader/member to get leader names for Houston, which may return multiple leaders over time. Question implies a single current leader; club.Team_Leader or a year filter would be more precise.

### Item: `660` (DB: `club_leader`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Averages ages per club_leader row, double-counting leaders who lead multiple clubs. Should average unique leaders (e.g., AVG(age) with DISTINCT member_id).
  - **gemini-2.5-pro** (CORRECT)

### Item: `665` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query retrieves 'Collecrtion_Subset_Details' from the 'Collection_Subsets' table. The question asks for 'collection details', which implies it should retrieve 'Collection_Description' from the 'Collections' table by joining through 'Collection_Subset_Members'.

### Item: `674` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses the right table/column and filter, but could return multiple rows if multiple documents share that description; question implies a single owner. Consider DISTINCT or LIMIT 1.

### Item: `675` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Semantically correct but may return duplicate owners if multiple objects have that description; use SELECT DISTINCT OWNER to list unique owners.

### Item: `690` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Join and filter are right, but it may return duplicate names if multiple collections are named 'Nice' (or same parent for several). Use DISTINCT to avoid duplicates.

### Item: `691` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only the immediate parent of 'Nice'. For all parent collections (ancestors), use a recursive CTE; consider DISTINCT if multiple 'Nice' rows exist.

### Item: `693` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Compares and deduplicates by Collection_Name. If names aren’t unique, any name that is a parent removes all collections with that name, including non-parents. Should filter by Collection_ID instead.

### Item: `700` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts member rows (collection pairs) rather than the number of collections per subset; should count distinct collections (union of Collection_ID and Related_Collection_ID). Also excludes subsets with zero members.

### Item: `701` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly counts the number of relationships between collections by using `count(*)` on the `Collection_Subset_Members` table. It should count the number of unique collections within each subset.
  - **gpt-5** (PARTIALLY_CORRECT): Counts membership rows (pairs), not distinct collections per subset; also INNER JOIN excludes subsets with zero members. Use LEFT JOIN and COUNT(DISTINCT ...) to count collections and include empties.

### Item: `705` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query fails to consider document objects that have zero related documents. It only queries the `document_subset_members` table, so any document object not present in that table (with a count of 0) is missed.
  - **gpt-5** (CORRECT)

### Item: `710` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Only matches Braeden’s docs via Document_Subset_Members.Document_Object_ID. If the doc appears as Related_Document_Object_ID, its subsets are missed. Should consider both columns (e.g., UNION).

### Item: `711` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May miss subsets where Braeden’s documents appear as Related_Document_Object_ID in Document_Subset_Members. Should include both columns to capture all relevant subset names.

### Item: `712` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts distinct Document_Object_ID only; documents that appear only as Related_Document_Object_ID are missed. To get unique documents per subset, count the union of both columns.
  - **gemini-2.5-pro** (CORRECT)

### Item: `713` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts only Document_Object_ID, ignoring Related_Document_Object_ID, so it can undercount unique documents. Also uses INNER JOIN, excluding subsets with no members; a LEFT JOIN with unioned IDs is needed.

### Item: `716` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query only selects document IDs from the `Document_Object_ID` column. It fails to also select IDs from the `Related_Document_Object_ID` column, which also represent documents in the subset.

### Item: `717` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Only selects Document_Object_ID. Documents present only in Related_Document_Object_ID for the subset are missed. Union both columns to return all document ids in the subset.

### Item: `720` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate collection names if a single collection contains multiple documents owned by 'Ransom'. Using SELECT DISTINCT would make the result more accurate.
  - **gpt-5** (INCORRECT): WHERE clause mismatches the requested owner ('ransom' vs 'Ransom ' with case and trailing space), leading to wrong/empty results. Also may need DISTINCT to avoid duplicate collection names.

### Item: `721` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Joins and filters are correct, but missing DISTINCT may return duplicate collection names if multiple Ransom-owned documents exist in the same collection.
  - **gemini-2.5-pro** (CORRECT)

### Item: `722` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts collections per document but only for documents present in Documents_in_Collections. Documents with zero collections are omitted; to include all, start from Document_Objects with a LEFT JOIN and COUNT.

### Item: `723` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts collections per document object only for those appearing in Documents_in_Collections. To include document objects with zero collections (implied by “for each”), use LEFT JOIN from Document_Objects.

### Item: `726` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Could return duplicate document IDs if a document belongs to multiple collections named 'Best'. Use SELECT DISTINCT for unique IDs.

### Item: `729` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join drops 'Best' collections with zero documents; should use LEFT JOIN and COUNT(T2.Document_Object_ID) to include zeros and still select the top one.

### Item: `730` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses only Document_Subset_Members.Document_Object_ID. Docs appearing only as Related_Document_Object_ID in the subset would be missed; should include both sides (e.g., UNION) before filtering by collection.

### Item: `731` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only Document_Subset_Members.Document_Object_ID. If subset membership includes Related_Document_Object_ID too, this misses valid docs. Should UNION both sides before filtering and selecting DISTINCT.

### Item: `732` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Excludes only docs where they appear as Document_Object_ID in the subset. Docs that are in the subset only as Related_Document_Object_ID won’t be excluded, yielding wrong results.

### Item: `740` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Joins via Collection_Subset_Members only on Collection_ID. A collection may appear in Related_Collection_ID too. Must check both columns to return all subsets for 'Best'.

### Item: `741` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Misses cases where the collection 'Best' appears under Related_Collection_ID. To get all subsets the collection is in, the filter must consider both Collection_ID and Related_Collection_ID.

### Item: `751` (DB: `sing_contest`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): INNER JOIN excludes participants with zero songs. The question implies listing all participants. Use LEFT JOIN and ORDER BY COUNT(T2.songs_id) to include those with 0 performances.

### Item: `752` (DB: `sing_contest`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate participants if they have multiple songs with score 5. Use DISTINCT or GROUP BY to ensure unique participant id-name pairs.
  - **gemini-2.5-pro** (CORRECT)

### Item: `753` (DB: `sing_contest`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Language filter uses equality. Since songs.language may include multiple languages (e.g., 'English , ...'), this could miss the song. Using LIKE '%English%' would align with the question.

### Item: `757` (DB: `sing_contest`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by the full songs.language string. Songs can contain multiple languages (e.g., 'English , Russian'); this treats them as one category instead of averaging per individual language.

### Item: `759` (DB: `sing_contest`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `WHERE language = '...'` for an exact match. Based on the schema comment for the `language` column (e.g., 'English , Russian'), a substring match like `WHERE language LIKE '%...%'` is required to correctly identify songs in a specific language.
  - **gpt-5** (PARTIALLY_CORRECT): Equality on songs.language misses multi-language values (e.g., 'English , Hebrew'); should use contains/LIKE. Also intersecting on name,popularity can merge distinct participants with identical values.

### Item: `782` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May include NULL as a state if multiple rows have NULL state. Add WHERE state IS NOT NULL to ensure only real states are listed.

### Item: `786` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one country; if multiple countries share the fewest cities, result is non-deterministic due to LIMIT 1. Should return all tied countries.

### Item: `787` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one country due to LIMIT 1; if multiple countries tie for fewest cities, others are omitted. Also may include NULL as a 'country'.

### Item: `796` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so cities with no students are omitted. To include all cities (with zero counts), use LEFT JOIN from City to Student and COALESCE(count).

### Item: `797` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits cities with no students. To include all cities, use LEFT JOIN and COUNT(T2.StuID) so cities with zero students appear with count 0.
  - **gemini-2.5-pro** (CORRECT)

### Item: `800` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will exclude countries that have zero students. A LEFT JOIN from City to Student is needed to correctly find the country with the minimum number of students.

### Item: `806` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses EXCEPT to remove USA residents but will also include students with NULL/missing city_code (unknown country). Should inner join City and filter country <> 'USA'.

### Item: `807` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses EXCEPT, so students with NULL city_code (unknown location) are included as not-USA. Likely intent is only known non-USA via join and country <> 'USA'.

### Item: `812` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only checks for the distance in one direction (from BAL to CHI). The distance 'between' two cities is symmetric and could be stored in the opposite direction (from CHI to BAL), which the query fails to check.
  - **gpt-5** (PARTIALLY_CORRECT): Assumes directed distance BAL->CHI. The question asks for distance between the cities, so it should match either order (BAL-CHI or CHI-BAL). Current query may miss the reverse entry.

### Item: `815` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only finds the distance in one direction (Boston to Newark). It fails to find the distance if the data is stored in the opposite direction (Newark to Boston), which would also be a valid answer.
  - **gpt-5** (PARTIALLY_CORRECT): Assumes Boston->Newark direction only. If the distance is stored only as Newark->Boston, it returns no rows. Should handle either order of the city pair.

### Item: `816` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May double-count reverse city pairs and possibly include same-city rows; average can be skewed. Use DISTINCT or restrict to one direction (e.g., city1_code < city2_code) and exclude city1_code=city2_code.

### Item: `817` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Aggregations are correct, but it may include self-distances. Add WHERE city1_code <> city2_code to restrict to distances between distinct cities.

### Item: `818` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY ... LIMIT 1, so if multiple city pairs share the maximum distance it returns only one pair. Should filter by distance = (SELECT MAX(distance) ...) to return all.
  - **gemini-2.5-pro** (CORRECT)

### Item: `819` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one pair due to ORDER BY ... LIMIT 1. If multiple pairs share the maximum distance, they’re omitted. Use WHERE distance = (SELECT MAX(distance) FROM Direct_distance) to include all.
  - **gemini-2.5-pro** (CORRECT)

### Item: `821` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns city pairs (city1_code, city2_code) rather than a list of city codes. Also lacks DISTINCT/UNION to avoid duplicates. Should return distinct city codes participating in distances > average.
  - **gemini-2.5-pro** (CORRECT)

### Item: `822` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May include self-pairs (same city) and duplicate directional pairs; it doesn’t enforce two distinct cities or deduplicate unordered pairs.

### Item: `828` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only finds distances where Chicago is in the `city1_code` column. It fails to consider cases where Chicago might be in the `city2_code` column, potentially missing the actual closest city.
  - **gpt-5** (CORRECT)

### Item: `829` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query only considers distances where Chicago is the origin city (city1_code). It will miss the correct answer if the shortest path has Chicago as the destination (city2_code) and the table is not symmetric.
  - **gpt-5** (PARTIALLY_CORRECT): Missing self-exclusion; may return 'Chicago' if a 0-distance self row exists. Also considers only city1='Chicago', ignoring distances where Chicago appears as city2.

### Item: `831` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Only checks distances where Boston is city1. To find the farthest city from Boston, it must also consider rows where Boston appears as city2, otherwise the true maximum can be missed.

### Item: `833` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Sums distances only for cities appearing as city1_code. “For each city” implies including all cities (even with zero sum). Should aggregate over City with LEFT JOIN to Direct_distance.

### Item: `838` (DB: `address_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Only considers rows where Linda’s city is in city1_code, ignoring when it’s in city2_code. Must handle both directions to correctly find the farthest student.

### Item: `839` (DB: `address_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query does not exclude 'Linda Smith' from the potential results. It should include a condition to ensure the student returned is not the same as the reference student (e.g., by comparing StuID).
  - **gpt-5** (PARTIALLY_CORRECT): Only uses distances where Linda’s city is city1_code; misses rows where it’s city2_code. Also LIMIT 1 arbitrarily picks among ties/multiple students in the furthest city.

### Item: `840` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return multiple rows and duplicates if multiple students named Linda exist; use DISTINCT to return unique state(s) or handle multiplicity.

### Item: `841` (DB: `address_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and filter, but may return duplicate states if multiple students named Linda exist. Use SELECT DISTINCT state to avoid duplicates.

### Item: `848` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate names if a sailor reserved boat 102 on multiple days; add DISTINCT to return unique sailors.
  - **gemini-2.5-pro** (CORRECT)

### Item: `849` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate names if a sailor reserved boat 102 on multiple days; use DISTINCT (or GROUP BY) to deduplicate.

### Item: `860` (DB: `boat_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts reservations per sailor (COUNT(*)) instead of distinct boats. Sailors with multiple reservations of the same boat would be included. Should use COUNT(DISTINCT T2.bid) > 1.
  - **gemini-2.5-pro** (CORRECT)

### Item: `861` (DB: `boat_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query selects both sailor name and sid, but only groups by sid. While valid in SQLite due to functional dependency, it's non-standard. More importantly, using `DISTINCT` on `(name, sid)` is redundant after `GROUP BY sid`.
  - **gpt-5** (INCORRECT): Counts reservations per sailor, not distinct boats. Should use COUNT(DISTINCT t2.bid) >= 2. Also returns sid though the question asks only for names.

### Item: `880` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct logic via > max(rating), but if no sailor named 'Luis' exists the subquery yields NULL and returns no rows; logically (> ALL empty set) all sailors should qualify.

### Item: `881` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct for cases with at least one 'Luis'. If no 'Luis' (or all ratings NULL), MAX returns NULL and > NULL yields no rows; should return all sailors vacuously.

### Item: `894` (DB: `boat_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts only boats that appear in Reserves. “For each boat” implies including boats with zero reservations; requires LEFT JOIN from Boats to Reserves to include all boats.

### Item: `895` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts reservations per bid from Reserves, but omits boats with zero reservations. For “each boat,” use Boats LEFT JOIN Reserves and GROUP BY boat to include zeros.

### Item: `897` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts only boats that have reservations; boats with id > 50 and zero reservations are omitted. Use LEFT JOIN from Boats and GROUP BY to include zero counts.

### Item: `900` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts reservations per boat where sid>1, but excludes boats with zero qualifying reservations. To cover “for each boat,” use Boats LEFT JOIN Reserves and COUNT with the sid>1 filter.

### Item: `902` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): A sailor’s age is averaged once per reservation, overweighting sailors with multiple red reservations. Should average over distinct sailors per rating (e.g., dedupe by sid before averaging).

### Item: `903` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): A sailor with multiple red reservations is counted multiple times, skewing the average age. Should deduplicate sailors per rating (e.g., aggregate by sid first or use DISTINCT sailor ids).

### Item: `912` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): If no red-boat reservations exist, the MAX subquery returns NULL, so rating > NULL yields no rows. By vacuous truth, all sailors should be returned in that case.

### Item: `913` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right, but MAX-based comparison fails for empty set: if no red-boat reservations exist, MAX returns NULL and no rows match, whereas all sailors should qualify. Use NOT EXISTS to handle this.

### Item: `916` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate sailor names if a sailor reserved 'Melon' multiple times or reserved multiple 'Melon' boats; use SELECT DISTINCT to ensure unique names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `917` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate sailor names if a sailor reserved 'Melon' multiple times (e.g., on different days). Use DISTINCT to ensure unique names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `920` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY ... LIMIT 1, which arbitrarily picks one model if there are ties for highest price. Should return all models with price = MAX(price).

### Item: `921` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one model; if multiple models share the highest price, it arbitrarily picks one (LIMIT 1). Should return all models with the max price.

### Item: `924` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Doesn't handle ties: returns a single class even if multiple classes are equally most common. Otherwise correct aggregation on headphone.Class.

### Item: `934` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one row via LIMIT 1; if multiple headphones share the minimum price, others are omitted. Should filter by MIN(price) to return all cheapest models.

### Item: `935` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one row; if multiple headphones share the lowest price, others are omitted. Should return all with min price (e.g., WHERE price = (SELECT MIN(price) FROM headphone)).

### Item: `940` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Filters only construction = 'Plastic'. It should also exclude any construction that contains plastic (e.g., '... Plastic ...') or different casing to match “use plastic construction.”

### Item: `941` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on earpads, removing any type that appears on a plastic model. The question asks for earpads from non-plastic headphones; should filter rows with construction <> 'Plastic'.

### Item: `944` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Orders by Date_Opened as TEXT, which may sort lexicographically (e.g., month names) instead of chronologically. Should parse/normalize dates before ordering.

### Item: `945` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Date_Opened is TEXT like 'October 29, 2005'; ORDER BY will sort lexicographically, not chronologically. Must parse/cast the date to order by actual open date.

### Item: `953` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Returns only the top store due to ORDER BY/LIMIT 1, while the question implies listing stores with in-stock totals. Also lacks a quantity>0 filter to reflect “in stock.”

### Item: `954` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Returns stores with no stock rows only; misses stores whose stock quantities sum to 0. Should include stores with no entries or total Quantity = 0.

### Item: `955` (DB: `headphone_store`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses absence of stock rows, but ignores Quantity. Stores with only zero quantities won’t be returned even though they have no headphones in stock. Should consider SUM(quantity)=0 or no rows.

### Item: `956` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Ignores Quantity; it only checks absence from stock. Models with stock rows but zero quantity would be excluded. Should return models with total Quantity=0 (e.g., NOT IN with Quantity>0 or HAVING SUM(Quantity)=0).

### Item: `957` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Ignores Quantity. It excludes models with any stock row, even if all quantities are 0. Should return models with no store having Quantity > 0, not just those absent from stock.

### Item: `962` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): It only checks if any stock row exists, ignoring Quantity. Neighborhoods whose stores have only zero-quantity stock will be wrongly treated as having stock. Must filter stock where Quantity > 0.

### Item: `963` (DB: `headphone_store`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Ignores Quantity; stores with only zero-quantity rows are treated as having stock. Also returns neighborhoods of any store lacking stock even if other stores in that neighborhood do have stock.

### Item: `976` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): DISTINCT collapses multiple papers with the same venue and year. The request suggests listing for all papers; removing DISTINCT would return one row per paper ordered by year.

### Item: `980` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate papers if multiple authors with name containing 'Mckeown' are on the same paper. Use SELECT DISTINCT on title, paper_id to ensure unique papers.

### Item: `981` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate rows if multiple authors with name containing 'Mckeown' are on the same paper. Use DISTINCT on (paper_id, title) to avoid duplicates.

### Item: `985` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Filters use name patterns with incorrect spacing around the comma (e.g., "Mckeown ,  Kathleen"), likely failing to match the intended author names. Use correct names or normalize whitespace.

### Item: `988` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): WHERE clause uses name patterns with extra spaces around the comma (e.g., 'Mckeown ,  Kathleen'), likely failing to match actual names like 'Mckeown, Kathleen'/'Rambow, Owen'.

### Item: `989` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): WHERE clause name patterns have extra spaces around the comma (e.g., 'Mckeown ,  Kathleen'), likely failing to match 'Mckeown, Kathleen' or 'Rambow, Owen'. Use correct names without extra spaces.
  - **gemini-2.5-pro** (CORRECT)

### Item: `990` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, excluding authors with zero papers. To list all authors, use LEFT JOIN from Author to Author_list and count T2.paper_id so authors without papers appear with count 0.

### Item: `991` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join excludes authors with zero papers; use LEFT JOIN from Author to Author_list to include all authors as question implies “each author.”

### Item: `998` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one venue-year due to LIMIT 1; if multiple share the max publications, output is arbitrary and incomplete. Should return all ties or specify a deterministic tie-breaker.

### Item: `1000` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct aggregation but LIMIT 1 returns only one venue. If multiple venues tie for the fewest publications, it arbitrarily picks one instead of returning all tied venues.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1001` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts papers per venue correctly but LIMIT 1 returns only one venue. If multiple venues tie for the fewest publications, others are omitted; should return all with the minimum count.

### Item: `1004` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of papers that cite 'D12-1027'. The question asks for the number of papers that 'D12-1027' references (cites), which should be filtered on the `cited_paper_id` column.
  - **gpt-5** (CORRECT)

### Item: `1014` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query counts the total number of citation records. The question 'How many papers' likely asks for the number of unique papers cited, which would require COUNT(DISTINCT T1.cited_paper_id).
  - **gpt-5** (CORRECT)

### Item: `1015` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Should count distinct cited papers. Use COUNT(DISTINCT t1.cited_paper_id). Current COUNT(*) double-counts if she cites the same paper in multiple of her papers.

### Item: `1021` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic and joins are correct, but the WHERE uses lowercase 'columbia university'. SQLite comparisons are case-sensitive; if data is 'Columbia University', it will miss. Use proper case or COLLATE NOCASE.

### Item: `1024` (DB: `aan_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly counts the number of author-paper links (`count(*)`) for each affiliation, not the number of distinct papers. If a paper has multiple authors from the same affiliation, it will be overcounted. The aggregation should be `COUNT(DISTINCT T1.paper_id)`.
  - **gpt-5** (PARTIALLY_CORRECT): Counts author-paper rows rather than distinct papers per affiliation. Multiple authors from the same affiliation on one paper cause overcount. Should use COUNT(DISTINCT T1.paper_id) per affiliation.

### Item: `1035` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Filters on t3.name = 'mckeown ,  kathleen' (lowercase, double space) which may not match 'Mckeown , Kathleen'. Use correct casing/spacing or a case-insensitive comparison.

### Item: `1038` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Doesn’t account for the “by others” nuance. Self-citations would exclude a paper. Add WHERE paper_id <> cited_paper_id in the subquery to ignore self-citations.

### Item: `1040` (DB: `aan_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts author entries per affiliation, not distinct papers. Papers with multiple authors from the same affiliation are overcounted. Use COUNT(DISTINCT T2.paper_id) instead.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly counts the number of authorships (COUNT(*)) rather than the number of distinct papers (COUNT(DISTINCT T2.paper_id)) for each affiliation.

### Item: `1041` (DB: `aan_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of author entries per affiliation (`count(*)`), not the number of distinct papers. It should use `COUNT(DISTINCT T2.paper_id)` to correctly answer the question.
  - **gpt-5** (PARTIALLY_CORRECT): Counts authorships instead of distinct papers. If multiple authors from the same affiliation coauthor a paper, the paper is overcounted. Use COUNT(DISTINCT T2.paper_id) for correct totals.

### Item: `1044` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join excludes affiliations with no papers. To return all affiliations (including zero counts), use LEFT JOIN from Affiliation to Author_list and COALESCE(COUNT(DISTINCT paper_id),0).

### Item: `1045` (DB: `aan_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join drops affiliations with zero papers; the request says “each affiliation.” Use LEFT JOIN from Affiliation to Author_list and COUNT(DISTINCT paper_id), COALESCE to 0.

### Item: `1053` (DB: `aan_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is correct, but it may return duplicate names if multiple authors share the same name. Use SELECT DISTINCT name to return a unique list of author names.

### Item: `1064` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts conferences per year and picks the minimum, but LIMIT 1 returns only one year; if multiple years tie for the least count, others are omitted.

### Item: `1065` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts conferences per year and picks the minimum, but LIMIT 1 returns only one year. If multiple years tie for fewest conferences, others are omitted.

### Item: `1067` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct grouping and count, but may return NULL as a location if multiple conferences have NULL Location. Add WHERE Location IS NOT NULL to match intent.

### Item: `1073` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY founded DESC LIMIT 1, so if multiple institutions share the most recent Founded year, only one is returned arbitrarily instead of all.

### Item: `1075` (DB: `conference`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query returns a count of staff members for each institution, but the question asks for the names of the staff members.
  - **gpt-5** (PARTIALLY_CORRECT): Correctly counts staff per institution founded after 1800, but output doesn’t match request: it omits institution_id and does not return staff names; it only returns institution_name and count.

### Item: `1076` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if staff.Institution_ID contains NULL, result may be empty. Use NOT EXISTS or filter NULLs in subquery to correctly find institutions with no staff.

### Item: `1077` (DB: `conference`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if staff.Institution_ID contains NULL, it yields no rows. Use NOT EXISTS or filter NULLs in subquery to correctly find institutions with no staff.

### Item: `1084` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Does not ensure the speaker and sponsor roles occur in the same conference; it only intersects by staff, allowing roles across different conferences.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1085` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on name, which may not be unique, causing false positives if two staff share a name. Intersect on staff_id (or group by staff_id with both roles) and then return names.

### Item: `1087` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on name, not staff identity. If two different staff share a name (one attended ACL, another NACCL), the name would appear incorrectly. Intersect by staff_ID, then return names.

### Item: `1090` (DB: `conference`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN, so conferences with zero participants are omitted. Should LEFT JOIN conference_participation and COUNT(T2.staff_ID), grouping by the conference to include all conferences.

### Item: `1091` (DB: `conference`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly calculates the number of participants for each conference but fails to return the conference ID, which was explicitly requested in the question.
  - **gpt-5** (INCORRECT): Missing conference_id in SELECT. Also uses INNER JOIN, excluding conferences with zero participants; a LEFT JOIN is needed to cover all conference IDs.

### Item: `1100` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing DISTINCT. If a pilot has skills for multiple planes and their age is below average, their name will be returned multiple times.
  - **gpt-5** (INCORRECT): Averages age over PilotSkills rows (weighted by number of planes) instead of per pilot, and may return duplicate pilot names. Should compute avg per pilot and return distinct names ordered by pilot age.

### Item: `1101` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly filters for pilots younger than the average age but may return duplicate names if a pilot has multiple skills. The question implies a unique list of pilot names, which would require SELECT DISTINCT.
  - **gpt-5** (INCORRECT): Averages age over PilotSkills rows, overweighting pilots with more plane entries; should average per pilot. Also may return duplicate pilot names; needs DISTINCT/aggregation and order by per-pilot age.

### Item: `1114` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Ownership is not represented in the schema. Only pilot skills (pilot-plane proficiency) and hangar info exist, so “planes owned by pilots under 35” cannot be determined.

### Item: `1115` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Ownership info is not in schema. PilotSkills lists skills/ages, not ownership; Hangar lists plane types, not instances or owners. No link to count B-52 Bombers owned by pilots under 35.

### Item: `1116` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct table and filter, but LIMIT 1 ignores ties and may pick a NULL age as 'youngest'. Filter age IS NOT NULL and/or select all with age = (SELECT MIN(age)).
  - **gemini-2.5-pro** (CORRECT)

### Item: `1119` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Schema lacks flight/activity data. PilotSkills shows who can fly which plane, not how often planes are flown. No table records flight counts, so “flown the most often” cannot be determined.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1120` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Aggregates only from PilotSkills, excluding planes with zero pilots. Least popular should consider all planes in Hangar; use LEFT JOIN from Hangar and count pilots, then order ascending.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1121` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts only planes appearing in PilotSkills, excluding planes with zero pilots. “Least often” should include those; use LEFT JOIN from Hangar and order by COUNT(PilotSkills.pilot_name).

### Item: `1125` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Schema lacks ownership data linking pilots to planes. PilotSkills only shows which planes a pilot can fly and age; Hangar has locations. Cannot determine planes owned by Smith, 41.

### Item: `1126` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Ownership by pilots is not represented in the schema. Only skills (PilotSkills) and plane inventory (Hangar) exist, with no link showing which planes a pilot owns.

### Item: `1128` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Schema lacks ownership info. PilotSkills maps pilot-plane skills, not ownership. No table/column indicates which planes a pilot owns, so cannot determine Smith’s owned planes.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1137` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query only selects the location, but the question asks for the locations of the planes. The query should also select the plane name to show which plane is at which location.

### Item: `1138` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Schema lacks any ownership relation between pilots and planes. PilotSkills records flying skills, not ownership, so “planes owned by all pilots” cannot be derived from the given tables.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1139` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses PilotSkills instead of Hangar, so it only returns planes with pilot-skill entries and can miss planes stored in Hangar. Should select plane_name from Hangar ordered alphabetically.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1144` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Schema lacks ownership relation; only PilotSkills (flying skills) exists. Cannot determine which pilots own a Piper Cub but not a B-52 Bomber.

### Item: `1146` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Ownership is not modeled. Schema only records pilot skills (PilotSkills) and plane locations (Hangar); there’s no pilot-to-plane ownership relation to identify owners of those planes.

### Item: `1147` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Ownership is not modeled. Schema has PilotSkills (skills) and Hangar (planes/locations) but no owner info, so pilots who own Piper Cub and B-52 cannot be determined.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1148` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Averages over PilotSkills rows; pilots with multiple plane skills are counted multiple times. Should compute over unique pilots (e.g., per pilot_name) before AVG. MIN is unaffected.
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average age over all pilot-skill records. Since a pilot can appear multiple times, their age is counted for each skill, which incorrectly calculates the average pilot age.

### Item: `1149` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Aggregates over PilotSkills rows, duplicating pilots with multiple plane skills. Need to aggregate per pilot (e.g., on distinct pilot_name) to get avg/min across pilots.

### Item: `1156` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The schema lists plane types in the Hangar table, but does not contain information about the quantity of individual aircraft for each type. Therefore, the number of planes cannot be counted.
  - **gpt-5** (INCORRECT): Counts pilot-skill records per plane_name, not number of planes. Should aggregate from Hangar by plane_name to get planes per type.

### Item: `1164` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Duplicates per city: pilots with multiple planes in the same city are counted multiple times, skewing count and average. Should aggregate per unique pilot-city (e.g., COUNT(DISTINCT) and de-dup for AVG).
  - **gemini-2.5-pro** (INCORRECT): The query counts pilot-plane associations, not unique pilots. This results in an incorrect count and average age if a pilot is skilled for multiple planes in the same city.

### Item: `1165` (DB: `pilot_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts pilot-skill rows instead of unique pilots; AVG(age) is biased by duplicate skills. Also inner join omits hangar locations with zero pilots. Use DISTINCT per location-pilot and a LEFT JOIN.
  - **gemini-2.5-pro** (INCORRECT): The query counts pilot-plane associations, not distinct pilots per location. This also makes the average age incorrect, as a pilot flying multiple planes in one location is counted multiple times.

### Item: `1168` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Ownership is not captured in the schema. PilotSkills shows which planes pilots can fly, not own; thus the plane owned by the youngest pilot cannot be determined.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1169` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate locations if multiple pilots have the minimum age and flew the same plane. Use DISTINCT on location to avoid duplicates.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1170` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilot rows if a pilot has multiple planes in Austin; use DISTINCT or GROUP BY to list each pilot once.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1171` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate pilots if they have multiple Austin-based planes; add DISTINCT (e.g., SELECT DISTINCT pilot_name, age) to list unique pilots.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1174` (DB: `pilot_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per pilot-plane, not unique pilots; should use COUNT(DISTINCT pilot_name). Also MIN subquery returns NULL if no F-14 pilots, making condition false instead of vacuously true.

### Item: `1177` (DB: `pilot_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses PilotSkills instead of Hangar. The question asks for plane names irrespective of pilots; querying PilotSkills may miss Bomber planes with no pilot records.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1186` (DB: `district_spokesman`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Filter uses LIKE "%gov%", which matches any occurrence of "gov" (e.g., in path or "govt"), not specifically .gov domains. Should target the domain/TLD, e.g., LIKE "%.gov%".
  - **gemini-2.5-pro** (CORRECT)

### Item: `1194` (DB: `district_spokesman`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may produce duplicate names if a spokesman served in multiple districts before 2004. Using SELECT DISTINCT would provide a unique list of names.

### Item: `1195` (DB: `district_spokesman`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits districts with zero spokesmen; use LEFT JOIN and COUNT(t2.Spokesman_ID) to include all districts. Group by the district (e.g., t1.District_ID) for clarity.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1196` (DB: `district_spokesman`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on district name instead of District_ID. If names aren’t unique, it can falsely include a name when no single district has both ranks. Intersect by District_ID, then select the names.

### Item: `1198` (DB: `district_spokesman`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if spokesman_district.district_id contains NULL, the NOT IN predicate returns UNKNOWN for all rows, yielding 0. Use NOT EXISTS or LEFT JOIN ... IS NULL to handle NULLs safely.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1201` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY year DESC LIMIT 1, which arbitrarily selects one sculpture. If multiple sculptures share the most recent year, others are omitted. Should return all with year = (SELECT MAX(year)).
  - **gemini-2.5-pro** (CORRECT)

### Item: `1203` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Orders by year but doesn’t exclude NULL years; could return a painting with unknown year instead of the oldest known one. Add WHERE year IS NOT NULL to be precise.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1204` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL years; ORDER BY may select a painting with unknown year as 'oldest'. Add WHERE year IS NOT NULL.

### Item: `1211` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Returns only medium; the question asks for medium types, which should include both medium and mediumOn for paintingID = 80.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1212` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Returns only the medium column. The question asks for mediums used, which should include both medium and mediumOn for paintingID 80.

### Item: `1216` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct columns/table, but WHERE location != 'Gallery 226' excludes NULL locations. To include unknown locations as not in that gallery, use: WHERE location IS NULL OR location <> 'Gallery 226'.

### Item: `1218` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns last name then first name, but the question asks for first name then last name. Otherwise correct joins, filter, and DISTINCT.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1219` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): DISTINCT is applied to birthYear, which can collapse multiple different artists sharing the same birth year. The query should dedupe by artist (e.g., EXISTS or DISTINCT on artistID), not by year.

### Item: `1220` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses DISTINCT on birthYear, collapsing multiple qualified artists who share the same birth year. The question asks per artist; do not dedupe by year (e.g., dedupe by artistID or omit DISTINCT).

### Item: `1223` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL birthYear/deathYear; in SQLite NULLs sort first, so it may return NULL instead of the shortest lifespan. Add WHERE birthYear IS NOT NULL AND deathYear IS NOT NULL.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1224` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Doesn’t exclude artists with NULL deathYear; NULLs sort first in SQLite, so result may be NULL. Add WHERE deathYear IS NOT NULL AND birthYear IS NOT NULL to get the shortest lifespan.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1229` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): INNER JOIN restricts to artists with paintings, so it finds the longest-lived painter among those only. If the longest-lived artist has 0 paintings, result is wrong. Should select max lifespan from Artists then LEFT JOIN to count.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1236` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Selects Paintings.medium instead of the support field. The question asks “on what mediums,” which corresponds to Paintings.mediumOn. Should return location and mediumOn for Pablo’s paintings.

### Item: `1237` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Intersects on lname,fname instead of artistID. Different artists sharing the same name could be incorrectly returned. Should intersect by artistID (or join on IDs) and then project names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1238` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Intersects on (lname,fname) rather than artistID. Artists sharing the same name could be falsely counted as doing both. Intersect by artistID (or join on IDs) and then return names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1239` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic correctly finds artists with both oil and lithograph paintings, but the selected columns are in last-name then first-name order; the question asks for first then last name.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1240` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Intersects on names instead of artistID. Different artists sharing the same name (one oil, one lithograph) could be falsely included. Intersect by artistID, then return fname/lname.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1241` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate birth years if an artist has multiple 1884 canvas paintings. Use DISTINCT to ensure unique birth years.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1259` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Orders by year ascending but doesn’t exclude NULL years; in SQLite NULLs sort first, so it may return an unknown-year painting instead of the oldest. Tie handling is also unspecified.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1260` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Finds an earliest-year painting ID, but ties are not handled (returns arbitrary one). Also may pick rows with NULL year since not excluded. Add WHERE year IS NOT NULL and tie handling if needed.

### Item: `1261` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Selects last name then first name instead of first then last. Also may return duplicates if an artist has multiple matching sculptures; DISTINCT (or GROUP BY) should be used.

### Item: `1262` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate artist names if the artist has multiple matching sculptures. Add DISTINCT (and optionally present as fname,lname/concatenated) to better match the single full-name intent.

### Item: `1266` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses DISTINCT on title, which can drop different paintings sharing a title. The task is to list all paintings ordered by height. Also ORDER BY height_mm with DISTINCT title is inconsistent if titles repeat.

### Item: `1294` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query correctly filters for artists with at least two paintings, but it only counts the number of paintings. The question asks for the total number of "works", which should include sculptures as well.

### Item: `1297` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join restricts to artists with at least one sculpture; the task requires the artist with the fewest sculptures (including zero). Should LEFT JOIN Artists to Sculptures and group by artist.

### Item: `1298` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Breaks ties arbitrarily (LIMIT 1) if multiple artists have the fewest sculptures, and excludes artists with zero sculptures due to inner join.

### Item: `1303` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic matches intent, but if no paintings exist after 1900, subquery returns NULL and no rows are returned; vacuously, all paintings should qualify. A NOT EXISTS approach would handle this.

### Item: `1306` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses LIMIT 3, returning top three artists, not the artist(s) with the maximum number of oil paintings. Should return all artists tied for the maximum count without an arbitrary limit.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1309` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct filter and sorting, but the selected column order is wrong; should output year, location, title (currently title, location, year).
  - **gemini-2.5-pro** (CORRECT)

### Item: `1311` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): EXCEPT compares only lname,fname; artists sharing the same name can be merged/removed incorrectly. Should filter by artistID (e.g., NOT EXISTS). Also returns last,first instead of first,last.

### Item: `1312` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): EXCEPT operates on (lname,fname); homonyms cause wrong results. Must exclude sculptors by artistID (unique) and then project names. Also consider ordering fname,lname if required.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1319` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct but may return duplicate driver names. The question 'Which winning drivers' implies a unique list, so SELECT DISTINCT Winning_driver would be more precise.

### Item: `1322` (DB: `car_road_race`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query orders distinct constructors by driver age. However, a single constructor can be associated with multiple drivers of different ages, making the ordering ambiguous and non-deterministic.
  - **gpt-5** (PARTIALLY_CORRECT): Returns distinct constructors, but ORDER BY Age is ambiguous if multiple drivers share a constructor. Should order by an aggregate age per constructor (e.g., MIN(Age)) to match intent.

### Item: `1333` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so drivers with zero races are omitted. LEFT JOIN with COUNT(T2.Road) would include all drivers; otherwise logic matches the question.

### Item: `1334` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Inner join counts only drivers appearing in race; drivers with zero races are omitted. Use LEFT JOIN and COUNT(T2.Road) or COALESCE to include all drivers.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1342` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Excludes NULL constructors due to !=; such drivers arguably did not have Bugatti. Use WHERE Constructor IS NULL OR Constructor <> 'Bugatti'.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1347` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts all rows; if two or more drivers have NULL Engine, it will return NULL as a type. Should exclude NULLs (WHERE Engine IS NOT NULL or HAVING COUNT(Engine) >= 2).

### Item: `1348` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May include NULL as an engine type if two+ drivers have NULL. Add WHERE Engine IS NOT NULL or use HAVING COUNT(Engine) >= 2 to exclude NULLs.

### Item: `1349` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): NOT IN can misbehave if race.Driver_ID contains NULLs, potentially excluding all drivers. Use NOT EXISTS or filter NULLs in subquery to ensure correct “no participation” logic.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1350` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN; if race.Driver_ID has NULL, predicate becomes UNKNOWN and may return no rows. Use NOT EXISTS or filter NULLs in subquery (WHERE Driver_ID IS NOT NULL).

### Item: `1358` (DB: `car_road_race`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): This excludes drivers who appeared in races where the pole sitter was James Hinchcliffe, not just the pole sitter himself. It should exclude drivers named 'James Hinchcliffe' (or match name to Pole_Position), not join by Driver_ID.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1364` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate names if languages.name isn’t unique. Use SELECT DISTINCT name to ensure unique language names containing "ish".
  - **gemini-2.5-pro** (CORRECT)

### Item: `1370` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Rows with NULL country name are excluded, though they should count as “other than Norway.” Use (name IS NULL OR name <> 'Norway') to include them.

### Item: `1380` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by language name which may not be unique; this can merge different languages with the same name. Group by language_id (and name) to ensure correct per-language counts.

### Item: `1381` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correctly counts countries per language, but LIMIT 1 arbitrarily picks one in case of ties. Should return all languages tied for the maximum count.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1385` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May double-count countries if languages has multiple 'English' rows; should average over unique countries (e.g., AVG from a SELECT DISTINCT country_id, overall_score subquery).

### Item: `1386` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May double-count countries if the join yields multiple rows per country (e.g., multiple 'English' language_ids). Deduplicate countries before averaging (e.g., IN subquery or DISTINCT country_id).

### Item: `1391` (DB: `country_language`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join excludes countries with zero official languages. Use LEFT JOIN and COUNT(T2.language_id) to include all countries when determining the maximum.

### Item: `1401` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Query returns only distinct states across all properties. The question implies per-property locations. It should include a property identifier (e.g., property_id) with county_state_province, not collapse with DISTINCT.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1402` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): It returns only a distinct list of states/provinces. The question asks for the state/province for each property, so it should include the property (e.g., property_id) with its county_state_province, without collapsing rows.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1403` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct table/column and filter, but feature_name isn’t guaranteed unique; could return multiple rows. Consider DISTINCT or ensuring uniqueness if only one description is expected.

### Item: `1405` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows in Property_Features, not distinct properties, and groups by feature_name only while selecting description. Should group by feature_id (or name+desc) and use COUNT(DISTINCT T2.property_id).
  - **gemini-2.5-pro** (CORRECT)

### Item: `1406` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Should count distinct properties per feature and group by feature identity. Use COUNT(DISTINCT T2.property_id) and GROUP BY T1.feature_id (or name+description). Current query groups by name and counts rows, risking duplicates and arbitrary description.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1407` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): room_count is VARCHAR; MIN on text is lexicographic and may return '' or wrong value (e.g., '10' < '2'). Should compute numeric min, e.g., MIN(CAST(room_count AS INTEGER)) and exclude empty strings.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1408` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The `room_count` column is of type VARCHAR. Applying MIN() directly performs a lexicographical comparison (e.g., '10' < '2'), not a numerical one as intended by the question. The column should be cast to a number.

### Item: `1411` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Filter uses LIKE "%Mother" (suffix match) instead of "%Mother%" (contains), misaligning with the question. Also may return duplicates; DISTINCT likely needed for unique age categories.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies the users and their age categories. However, it may return duplicate age category codes. Using SELECT DISTINCT would provide a unique list as implied by the question.

### Item: `1415` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May double-count properties if multiple 'garden' feature rows exist. Deduplicate by property_id (e.g., use WHERE EXISTS or GROUP BY property) before averaging room_count.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1416` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Averages room_count over Property_Features rows; if a property has multiple 'garden' rows, it’s counted multiple times. Should average per distinct property_id (or de-duplicate) to be accurate.

### Item: `1419` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL prices; in SQLite NULLs sort first, so it may return a NULL instead of the true lowest price. Add WHERE vendor_requested_price IS NOT NULL.

### Item: `1420` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return a property with NULL vendor_requested_price since NULLs sort first in SQLite. Add WHERE vendor_requested_price IS NOT NULL to ensure the lowest actual price is returned.

### Item: `1434` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly finds users with exactly one search, but returns only user_category_code. The question likely expects all category codes for each user (e.g., also age_category_code).

### Item: `1435` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Does not exclude NULL search_datetime; SQLite sorts NULLs first, so it might return a NULL-timestamp row instead of the earliest real search. Otherwise the join and ordering are appropriate.

### Item: `1436` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Orders by search_datetime without excluding NULLs, so NULLs could be picked as earliest; also returns arbitrary user on timestamp ties.

### Item: `1445` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate addresses if multiple Senior Citizens share one address. Use DISTINCT to list unique building/street/city combinations.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1446` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and columns, but may return duplicates if multiple senior citizens share the same address. Use DISTINCT (or GROUP BY) on the address fields to get unique addresses.

### Item: `1449` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts photos per property_id but excludes properties with zero photos. A LEFT JOIN from Properties to Property_Photos would include all properties with 0 counts.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1450` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts photos per property_id but only for properties that have photos. To cover “each property,” including those with zero photos, use LEFT JOIN from Properties to Property_Photos.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1451` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts photos per owner correctly for owners with photos, but INNER JOIN omits owners whose properties have zero photos. Use LEFT JOIN and COUNT(T2.photo_seq) to include zero counts.

### Item: `1460` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters on the `age_category_code` column. The value 'Over 60' from the question corresponds to the `age_category_description` column, not the code.

### Item: `1463` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return multiple rows if several users have first_name 'Robbie' or duplicate countries; add DISTINCT or further identify the user to ensure a single, deduped answer.

### Item: `1464` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join/column, but if multiple users have first_name 'Robbie', it may return multiple rows. Consider DISTINCT or disambiguating the user to ensure a single country.

### Item: `1465` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Logic matches intent (owners whose property address equals their user address). However, the query may return duplicate names if a user owns multiple matching properties; use DISTINCT.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1466` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is correct (owner and same address), but may return duplicate names if a user matches multiple properties. Use DISTINCT to return each user only once.

### Item: `1468` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Uses EXCEPT on search_string, removing any string used by any owner. This excludes strings searched by both owners and non-owners. Should filter rows to users with no properties instead.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1470` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): The INNER JOIN to User_Searches excludes users with zero searches, but “two or fewer” includes 0. Use a LEFT JOIN (and count search rows) to include users with no searches.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1484` (DB: `bike_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INTERSECT on product_name and price rather than bike id; could falsely match different bikes sharing the same name/price. Intersect on bike.id and then select name/price.

### Item: `1485` (DB: `bike_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses EXCEPT on non-unique columns (name, nation, result). If two cyclists share these values and one owns a bike, the other is wrongly excluded; also removes duplicates. Should anti-join by cyclist id.

### Item: `1487` (DB: `bike_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts bikes per cyclist only for those appearing in cyclists_own_bikes; cyclists with zero bikes are omitted. Use LEFT JOIN from cyclist and COUNT(bike_id) (COALESCE to 0) to include all.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1501` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct grouping and count, but it may include NULL as a customer id. Should filter out NULLs or join to customers to ensure only real customer ids are returned.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1504` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts all Cake rows (SKUs). “Types” likely means distinct flavors. Use COUNT(DISTINCT Flavor) WHERE Food='Cake' to avoid overcounting multiple SKUs per flavor.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1505` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts cake products, not types. Use COUNT(DISTINCT Flavor) FROM goods WHERE Food='Cake' to count cake types.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1506` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct filter/table, but missing DISTINCT. If multiple croissant goods share the same flavor, duplicates will appear; query should return unique flavors.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1507` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate flavors if multiple croissant goods exist; use SELECT DISTINCT flavor FROM goods WHERE food = 'Croissant'.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1515` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate receipt numbers if multiple croissant items are on the same receipt. Use DISTINCT (or GROUP BY ReceiptNumber) to ensure unique receipt numbers.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1516` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses ORDER BY price DESC LIMIT 1; if multiple receipts contain items with the maximum price, it returns only one arbitrarily instead of all such receipts.

### Item: `1519` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts purchases per item correctly, but LIMIT 1 returns a single arbitrary item if multiple items tie for the fewest purchases; should return all items with the minimum count.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1527` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate flavors; use DISTINCT to list unique cake flavors priced over $10.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1540` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses DISTINCT, which removes duplicate last names. The request is for last names of all customers; duplicates should be preserved. Ordering is otherwise correct.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1547` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Orders the TEXT date 'DD-Mon-YYYY' lexicographically, not chronologically, so latest date may be wrong. Also returns all receipts on that date instead of a single receipt as asked.

### Item: `1548` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Earliest date is derived by ORDER BY on a TEXT field in format 'DD-Mon-YYYY', which sorts lexicographically, not chronologically. Should parse/normalize dates before ordering.

### Item: `1549` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Earliest date is determined by lexicographic ORDER BY on a TEXT 'dd-Mon-yyyy' field, which may not reflect chronological order; could select wrong earliest-date receipts. Otherwise logic aligns.

### Item: `1552` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Orders by TEXT date in 'DD-Mon-YYYY' format, which doesn’t sort chronologically, so the earliest date may not be first. Also LIMIT 1 may exclude other customers on the same earliest date.

### Item: `1553` (DB: `bakery_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'Date' column lexicographically, but its TEXT format ('DD-Mon-YYYY') is not chronologically sortable. This will not reliably find the earliest date.
  - **gpt-5** (PARTIALLY_CORRECT): Sorts by TEXT Date ('DD-Mon-YYYY'), so lexicographic order may not match the true earliest date. Should convert/normalize dates before ordering. Also returns an arbitrary customer if multiple share the earliest date.

### Item: `1555` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Computes one overall average across Blackberry and Blueberry. The question asks for average prices per flavor; needs GROUP BY flavor to return separate averages.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1564` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly counts receipts per customer, but LIMIT 1 arbitrarily picks one in case of ties. Also returns only CustomerId, not the customer’s name as the question implies.

### Item: `1580` (DB: `bakery_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Inner join counts only purchased items; chocolate goods with 0 purchases (still <=10) are excluded. Start from goods with LEFT JOIN to items and count items to include zero-buys.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1589` (DB: `bakery_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): It averages price across all items per customer. The request implies per-good averages (each good > 5). Need per customer–good grouping and to require all such averages > 5.

### Item: `1606` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Applying MIN() and MAX() on a text column performs a lexicographical (alphabetical) comparison, not a numerical one, which will lead to incorrect results.

### Item: `1607` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Applying MAX() and MIN() performs a lexicographical (alphabetical) comparison instead of a numerical one, which will produce the wrong highest and lowest values.

### Item: `1615` (DB: `car_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN; drivers without a matching country (NULL/invalid FK) will be omitted. A LEFT JOIN from driver to country would include all drivers as requested.

### Item: `1616` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. The `MAX()` function will perform a lexicographical comparison (e.g., '9' > '100') instead of a numerical one. The column should be cast to a numeric type to get the correct maximum value.

### Item: `1617` (DB: `car_racing`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Points is TEXT; MAX over TEXT is lexicographic, not numeric. Cast Points to a number (e.g., MAX(CAST(T2.Points AS REAL))) to correctly get the maximum points.
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Applying MAX() directly will perform a lexicographical comparison (e.g., '9' > '185'), not the intended numerical comparison. The column should be cast to a numeric type.

### Item: `1623` (DB: `car_racing`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The `Points` column is of type TEXT. Ordering this column alphabetically (e.g., '9' > '100') will not correctly identify the driver with the highest numerical points. It should be cast to a number.
  - **gpt-5** (PARTIALLY_CORRECT): Points is stored as TEXT; ORDER BY T2.Points sorts lexicographically, which can select the wrong driver. Cast to numeric (e.g., ORDER BY CAST(T2.Points AS REAL) DESC) to ensure correctness.

### Item: `1626` (DB: `car_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Correct aggregation over driver.Make, but LIMIT 1 returns only a single make. If multiple makes tie for most drivers, the query should return all of them.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1634` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query applies numerical aggregate functions (SUM, AVG) to the 'Points' column, which has a TEXT data type. This is semantically incorrect as it relies on implicit type casting which may fail or produce incorrect results if the column contains non-numeric text.

### Item: `1635` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query applies numerical aggregations (SUM, AVG) to the 'Points' column, which has a TEXT data type. This can lead to incorrect results if non-numeric text is present, as it would be coerced to 0, wrongly affecting the average.

### Item: `1636` (DB: `car_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right, but NOT IN fails if driver.Country contains NULLs (may return no rows). Use NOT EXISTS or filter NULLs in subquery.

### Item: `1637` (DB: `car_racing`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN with a subquery that may include NULLs (driver.Country). If any NULL exists, the predicate yields no rows. Prefer NOT EXISTS or filter out NULLs in the subquery.
  - **gemini-2.5-pro** (INCORRECT): The query uses `NOT IN` with a subquery. If the `Country` column in the `driver` table contains any NULL values, the `NOT IN` condition will always evaluate to unknown, causing the query to incorrectly return an empty result set.

### Item: `1638` (DB: `car_racing`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly counts drivers per team. However, ties are resolved arbitrarily (no tiebreaker). Also, teams with zero drivers are excluded due to the inner join.

### Item: `1656` (DB: `institution_sports`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct table/columns, but ORDER BY ... LIMIT 1 returns only one stadium and is non-deterministic on ties. Should return all stadiums with max enrollment (e.g., WHERE Enrollment = (SELECT MAX(...))).

### Item: `1657` (DB: `institution_sports`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns a stadium for the highest enrollment but uses LIMIT 1, which arbitrarily picks one if there are ties. Should return all stadiums with the maximum enrollment.

### Item: `1672` (DB: `institution_sports`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right, but it may return NULL as a “year” if multiple institutions have NULL Founded. Add WHERE Founded IS NOT NULL to align with the question.

### Item: `1673` (DB: `institution_sports`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct grouping/counting, but it may include groups where Founded IS NULL if multiple nulls exist. The question asks for years, so NULL should be excluded (add WHERE Founded IS NOT NULL).

### Item: `1676` (DB: `institution_sports`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): City filter uses lowercase literals; SQLite comparisons are case-sensitive, so it won’t match 'Vancouver' or 'Calgary'. Should use proper case, IN, or case-insensitive comparison (e.g., UPPER).
  - **gemini-2.5-pro** (CORRECT)

### Item: `1710` (DB: `warehouse_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses INTERSECT, which finds contents present in both Chicago and New York warehouses. The question asks for contents from Chicago and New York, which implies a union of contents from either location.
  - **gpt-5** (UNANSWERABLE): Ambiguous intent: could mean union of contents in Chicago and New York warehouses or contents present in both. SQL uses INTERSECT (both), but schema cannot resolve intended meaning.

### Item: `1714` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Compares at location level. EXCEPT on locations excludes any city with any Scissors box, even if a different warehouse there has Rocks and no Scissors. Must test per warehouse (by warehouse code) then return its location.

### Item: `1715` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): EXCEPT is applied on location, conflating multiple warehouses at the same location. If any warehouse there has Scissors, it wrongly excludes other warehouses without Scissors. Filter by warehouse first.

### Item: `1718` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects locations, so different warehouses in the same location can satisfy Rocks and Scissors separately. Must ensure both contents are in the same warehouse (intersect/group by warehouse, then get location).

### Item: `1719` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Intersects by location, not warehouse. Can return a location where different warehouses have Rocks and Scissors. Must ensure the same warehouse contains both before selecting its location.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1730` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct when at least one 'Scissors' box exists. If none, MAX returns NULL and no rows are returned, whereas logically all boxes should qualify (vacuous truth).

### Item: `1731` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct logic via > MAX for non-empty Scissors set, but if no 'Scissors' boxes exist the subquery returns NULL, yielding no rows; logically, all boxes should qualify in that case.

### Item: `1744` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts boxes per warehouse from Boxes only; warehouses with zero boxes are omitted. To include every warehouse code, use a LEFT JOIN from Warehouses and COUNT(Boxes.Code).

### Item: `1745` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts boxes per warehouse only for warehouses present in Boxes; warehouses with zero boxes are omitted. Use LEFT JOIN from Warehouses to include all warehouses.

### Item: `1752` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns counts only for warehouses that contain boxes; warehouses with zero boxes are omitted. Use LEFT JOIN from Warehouses to Boxes and GROUP BY Warehouses.Code to include all warehouses.

### Item: `1753` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts boxes per warehouse only where boxes exist; warehouses with zero boxes are omitted though “each warehouse” implies including them. Use LEFT JOIN Warehouses→Boxes and COALESCE to include zeros.

### Item: `1754` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts distinct contents per warehouse from Boxes only; omits warehouses with zero boxes. Use Warehouses LEFT JOIN Boxes to include all warehouses.

### Item: `1755` (DB: `warehouse_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts distinct contents per warehouse from Boxes, but excludes warehouses with no boxes. To cover “each warehouse,” LEFT JOIN Warehouses and count DISTINCT contents, yielding 0 for empty warehouses.

### Item: `1756` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The HAVING clause compares count(*) with T2.capacity, but T2.capacity is not an aggregate function and is not in the GROUP BY clause. This is not valid in standard SQL and can lead to unpredictable results.
  - **gpt-5** (CORRECT)

### Item: `1757` (DB: `warehouse_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query is almost correct, but it compares the count of boxes to `T2.capacity` in the HAVING clause. `T2.capacity` is not an aggregate function and is not in the GROUP BY clause, which is invalid in standard SQL. While some dialects might allow this, it's semantically ambiguous. The capacity should be aggregated (e.g., using MIN or MAX) or the query restructured.

### Item: `1784` (DB: `university_rank`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by university_name only, which may not be unique. This can merge different universities with the same name and miscount. Should group by university_id (and optionally name).

### Item: `1785` (DB: `university_rank`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Groups by university_name instead of University_ID; if different universities share the same name, counts may be combined. Group by University_ID (and select name) to avoid conflation.

### Item: `1786` (DB: `university_rank`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Filters by University_Name instead of University_ID. If different universities share the same name, a rank-1 major at one will remove the name for all, excluding valid universities. Use IDs for filtering.

### Item: `1787` (DB: `university_rank`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses EXCEPT on University_Name instead of University_ID. If two universities share a name and one has a #1 major, both names are excluded. Use NOT EXISTS/LEFT JOIN filtering by University_ID.

### Item: `1789` (DB: `university_rank`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on University_Name, which isn’t guaranteed unique. If different universities share a name, it can return that name even if no single university has both majors. Intersect by University_ID, then select name.

### Item: `1791` (DB: `university_rank`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, which omits Wisconsin universities lacking an overall_ranking row. For “every university,” use LEFT JOIN to include all with NULL rank where missing.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1796` (DB: `university_rank`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate university names if a university has multiple Accounting entries with ranks <= 3. Use DISTINCT or GROUP BY to ensure unique names.
  - **gemini-2.5-pro** (INCORRECT): The question asks for universities ranked '3 or above', which implies a rank number of 3 or greater (e.g., 3, 4, 5...). The query incorrectly filters for ranks less than or equal to 3.

### Item: `1800` (DB: `university_rank`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses LIMIT 3, which returns exactly 3 rows and may exclude universities tied at the 3rd-highest reputation points. Should include all with Reputation_point >= the third-highest value.
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 3` to find the top 3 universities, which is incorrect because it does not handle ties. If multiple universities share the 3rd highest reputation score, the query will arbitrarily exclude some of them.

### Item: `1814` (DB: `movie_2`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts theater-movie rows; duplicates movies shown in multiple theaters. Use COUNT(DISTINCT T1.code) or COUNT(DISTINCT T2.movie) to count unique movies playing.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1818` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Counts distinct names, not distinct theaters. Theaters are uniquely identified by Code/rows; use COUNT(*) or COUNT(DISTINCT Code) on MovieTheaters.

### Item: `1819` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Counts distinct names, not distinct theaters. Theaters are identified by primary key Code (or rows). Use COUNT(*) or COUNT(DISTINCT Code) from MovieTheaters.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1826` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects by title, not movie identity. If different movies share the same title at the two theaters, it yields a false match. Should intersect/self-join on Movie code and then return the title.

### Item: `1827` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects by title instead of movie ID. If different movies share a title (one at Odeon, another at Imperial), it yields a false match. Should match on movie code and then select the title.

### Item: `1834` (DB: `movie_2`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per theater name, not distinct movies. Use COUNT(DISTINCT Movie) to measure how many movies a theater plays; otherwise duplicates (same movie listed multiple times) inflate counts.

### Item: `1835` (DB: `movie_2`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per theater name; should count distinct movies. Duplicate entries for the same movie would inflate counts. Prefer COUNT(DISTINCT Movie).

### Item: `1836` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by title instead of movie ID. Different movies can share a title, so their theater counts get combined, potentially yielding a wrong result. Group by T1.code (and select its title).

### Item: `1837` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups by title instead of movie ID; duplicate titles would merge different films and miscount theaters. Should group by T1.code (optionally also title) and order by COUNT(*) DESC.

### Item: `1842` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): HAVING COUNT(*)>=1 is always true for any name and doesn’t ensure a movie is playing. It returns all theaters, including those with NULL Movie. Should filter Movie IS NOT NULL or join to Movies.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1843` (DB: `movie_2`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): HAVING COUNT(*)>=1 is always true per group and doesn’t ensure a movie is playing. Must filter by movies, e.g., WHERE Movie IS NOT NULL or HAVING COUNT(Movie)>0 (or join to Movies).

### Item: `1846` (DB: `movie_2`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is logically correct, but it may return duplicate theater names if a single theater is showing multiple movies with a 'G' rating. Using SELECT DISTINCT would provide a unique list of names.

### Item: `1847` (DB: `movie_2`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (CORRECT)
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies theaters showing 'G' rated movies, but it may return duplicate theater names if a theater shows more than one 'G' rated movie. Using SELECT DISTINCT is recommended.

### Item: `1856` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one recipient due to LIMIT 1; if multiple packages share the maximum weight, it arbitrarily selects one instead of all who received the heaviest package.

### Item: `1861` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct table/column, but may return multiple rows if multiple employees share the name 'Amy Wong'. DISTINCT or filtering by a unique key would avoid duplicates.

### Item: `1866` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns clearance levels for all employees with position 'Physician' across all planets; may yield multiple rows. Question implies a single level. Use DISTINCT or specify employee/planet.

### Item: `1867` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 1 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (UNANSWERABLE): Clearance level depends on both employee and planet (Has_Clearance.Employee, Planet). The question doesn’t specify which physician or planet, so a single answer can’t be determined.

### Item: `1871` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): PackageNumber is only unique per shipment; returning only PackageNumber may include duplicates across shipments. Use DISTINCT or include Shipment to avoid ambiguity.

### Item: `1872` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Packages are identified by (Shipment, PackageNumber). Selecting DISTINCT PackageNumber can collapse different packages across shipments, so it may not list all packages sent/received by Leo Wong.

### Item: `1882` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Returns only one top sender; if multiple clients tie for the most packages, LIMIT 1 arbitrarily selects one. Should return all clients with the maximum package count.

### Item: `1884` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Inner join only considers clients with at least one package; clients with zero are omitted. LIMIT 1 arbitrarily breaks ties. Use LEFT JOIN and return all clients with the minimum count.

### Item: `1885` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct grouping and counting, but LIMIT 1 returns only one recipient. If multiple clients tie for the smallest number of packages, they won’t all be returned.

### Item: `1886` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic and joins are correct for identifying senders with >1 package, but the query returns an extra count column. The question asks to list only the client names.

### Item: `1888` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct table/column and filter, but Planet.Name isn’t unique in schema; duplicates could return multiple rows. Consider DISTINCT or enforcing unique planet names.

### Item: `1903` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join omits planets with zero shipments; “each planet” suggests including them. Use LEFT JOIN from Planet to Shipment and GROUP BY PlanetID/Name to include zero counts.

### Item: `1920` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses EXCEPT on Name. If two employees share a name and one has Mars clearance, the other (without clearance) will be excluded. Should compare by EmployeeID and then select names (DISTINCT).

### Item: `1921` (DB: `planet_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is applied on Name. If two employees share a name and one has Mars clearance, the other is wrongly excluded. The anti-join should be per EmployeeID, not by name.

### Item: `1923` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate employee names if multiple planets named 'Omega III' exist; add DISTINCT to ensure unique names.

### Item: `1930` (DB: `planet_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is correct (counts employees without a Mars clearance). However, filtering uses t3.name = "mars"; if names are case-sensitive and stored as "Mars", this will miscount. Use proper case or case-insensitive compare.

### Item: `1951` (DB: `video_game`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct joins and columns, but may return duplicate players if multiple Game_IDs share the title 'Super Mario World'. Use DISTINCT or GROUP BY to deduplicate.

### Item: `1954` (DB: `video_game`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Duplicates possible: if multiple Guard players are linked to the same game, that game's units are averaged multiple times. Should average over distinct games (e.g., dedupe by Game_ID).
  - **gemini-2.5-pro** (CORRECT)

### Item: `1955` (DB: `video_game`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Duplicates possible: games linked to multiple Guard players will be counted multiple times, weighting the average. Should average over distinct games (e.g., AVG on DISTINCT Game_ID via subquery).
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly calculates the average. If a game is played by multiple players with the position 'Guard', its units sold will be counted multiple times, skewing the average. The average should be over unique games.

### Item: `1962` (DB: `video_game`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses GROUP BY and COUNT correctly but LIMIT 1 returns only one franchise. If multiple franchises tie for the most games, they should all be returned.

### Item: `1963` (DB: `video_game`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts games per franchise correctly, but LIMIT 1 returns only one franchise; in case of a tie for most games, other top franchises would be omitted.

### Item: `1968` (DB: `video_game`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Intersects on Title instead of Game_ID. If different games share the same title, it can return that title even though no single game is played by both Oklahoma and Auburn players.

### Item: `1972` (DB: `video_game`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set subtraction is on Title, not Game_ID. If multiple games share the same title and any one has a Guard player, the title is removed for all, incorrectly excluding guard-free games. Use Game_ID-based filter.

### Item: `1973` (DB: `video_game`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right (exclude games with any Guard players), but it subtracts by Title instead of Game_ID. If multiple games share the same title, results can be over-excluded. Use Game_ID for the anti-join.

### Item: `1976` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Logic matches the question, but Name may not be unique; the query can return duplicate publisher names. Use SELECT DISTINCT name ... to ensure unique names.

### Item: `1980` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Uses correct table/column and orders by monthly profit, but LIMIT 1 returns only one row. If multiple publishers tie for highest profit, others are missed. Use WHERE = MAX(...) to include ties.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1998` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Intersects on author name, which may not be unique. This can falsely include a name if different authors share it (one in MM, another in LT). Should intersect/group by author_id and then return the name.
  - **gemini-2.5-pro** (CORRECT)

### Item: `1999` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Intersects on author names, not author IDs. If two different authors share a name (one in MM, another in LT), it returns that name falsely. Intersect by author_id, then select names.
  - **gemini-2.5-pro** (CORRECT)

### Item: `2000` (DB: `book_press`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): NOT IN breaks if book.author_id contains NULLs, potentially excluding all authors. Use NOT EXISTS or filter NULLs in the subquery to handle authors with no books safely.
  - **gemini-2.5-pro** (INCORRECT): The `NOT IN` operator with a subquery will incorrectly return an empty result if any `NULL` values are present in the `book.author_id` column. A `LEFT JOIN` or `NOT EXISTS` should be used instead.

### Item: `2001` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses NOT IN on book.author_id without excluding NULLs. If any NULL exists in the subquery, NOT IN returns no rows. Prefer NOT EXISTS or filter WHERE author_id IS NOT NULL.

### Item: `2006` (DB: `book_press`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, so presses with no books are omitted. For “each press,” use LEFT JOIN from press to book (and optionally COALESCE(SUM(...),0)) and group by press.

### Item: `2007` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (INCORRECT): Inner JOIN omits presses with no books; question asks for each press. Should LEFT JOIN press to book and group by press to include presses with zero sales (using SUM(COALESCE(...,0))).
  - **gemini-2.5-pro** (CORRECT)

### Item: `2008` (DB: `book_press`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query compares the 'sale_amount' column, which is of TEXT type, with a numeric value (1000). This will result in a lexicographical comparison, not a numerical one. For example, '200' > '1000' would be true. The column should be cast to a numeric type for a correct comparison.
  - **gpt-5** (PARTIALLY_CORRECT): Groups by press name, which may not be unique; should group by press_id (and name). Also uses inner join/WHERE, so publishers with zero qualifying books are omitted if “each publisher” was intended.

### Item: `2009` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses INNER JOIN and WHERE, so presses with no qualifying books are omitted; should LEFT JOIN and count conditionally to include zero. Also grouping by name may merge presses sharing a name.

### Item: `2010` (DB: `book_press`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query sorts the 'Sale_Amount' column, which is of type TEXT, lexicographically. This will not correctly identify the best-selling book as it needs to be sorted numerically.
  - **gpt-5** (PARTIALLY_CORRECT): Logic is right (pick author of highest-selling book), but Sale_Amount is TEXT; ORDER BY will sort lexicographically unless CAST to numeric. Also no tie handling; LIMIT 1 returns arbitrary author on ties.

### Item: `2015` (DB: `book_press`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Set difference is done on Name, not Author_ID. If two different authors share the same name, authors who never published with Accor may be wrongly excluded. Use Author_ID for exclusion.

### Item: `2024` (DB: `cre_Doc_Workflow`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate rows if the same author has multiple documents titled 'Travel to Brazil'. Use SELECT DISTINCT to ensure unique author(s).

### Item: `2028` (DB: `cre_Doc_Workflow`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate rows if multiple Documents named 'Travel to China' exist for the same author; lacks DISTINCT/GROUP BY to deduplicate author info.

### Item: `2029` (DB: `cre_Doc_Workflow`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts documents per author in Documents, but omits authors with no documents. To show all author names, left join Authors to Documents and count document_id.

### Item: `2055` (DB: `cre_Doc_Workflow`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses Staff_in_Processes only, so excludes staff with zero document processes despite “all staff ids.” Should LEFT JOIN Staff to include all staff and count joined rows.

### Item: `2066` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts clients per agency from Clients only, so agencies with zero clients are omitted. To cover all agencies, LEFT JOIN Agencies and count Clients.

### Item: `2067` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts clients per agency_id but omits agencies with zero clients. Use LEFT JOIN from Agencies to Clients to include all agencies.

### Item: `2068` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, excluding agencies with zero clients. Should use LEFT JOIN and COUNT(T2.client_id) to include agencies with no clients (e.g., when max count is 0).

### Item: `2069` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Uses INNER JOIN, excluding agencies with zero clients. To include agencies with no clients (and handle all-zero case), use LEFT JOIN and COUNT(T2.client_id).

### Item: `2072` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): May return duplicate agency_details if multiple clients with detail 'Mac' belong to the same agency. Use DISTINCT to avoid duplicates.

### Item: `2073` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correct join and filter, but may return duplicate agency_details if multiple 'Mac' clients share the same agency. Use DISTINCT to avoid duplicates if unique agencies are desired.

### Item: `2088` (DB: `advertising_agencies`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Groups only the Invoices table, so clients with zero invoices are omitted. Use Clients LEFT JOIN Invoices and GROUP BY Clients.client_id to include all client IDs.

### Item: `2089` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Counts invoices per client only for clients present in Invoices, excluding clients with zero invoices. Use LEFT JOIN from Clients to Invoices to include all client_ids with 0 counts.
  - **gemini-2.5-pro** (CORRECT)

### Item: `2096` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Correctly finds the status with the highest count, but ties are not handled—LIMIT 1 will return an arbitrary status if multiple have the same max count.

### Item: `2103` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Returns all rows, but likely needs DISTINCT to list unique meeting outcome–purpose pairs as implied by “all.”
  - **gemini-2.5-pro** (CORRECT)

### Item: `2110` (DB: `advertising_agencies`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): The question asks for payment ids with corresponding invoice ids and invoice details. Query returns payment_details and doesn’t join Invoices to get invoice_details.

### Item: `2115` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts payments per invoice only for invoices that have payments, excluding invoices with zero. Use LEFT JOIN from Invoices to Payments to include all invoices with 0 counts.

### Item: `2117` (DB: `advertising_agencies`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query uses `LIMIT 1`, which incorrectly returns only one invoice in the case of a tie for the most payments. The question asks for 'invoices' (plural), implying all tied invoices should be returned.
  - **gpt-5** (PARTIALLY_CORRECT): Uses LIMIT 1 so returns only one invoice, not all with the maximum payment count (ties). Should filter by count = MAX(count) to return all top invoices.

### Item: `2122` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Inner join ignores agencies with zero staff (could miss correct result if none have staff). Also ties for most staff are broken arbitrarily due to LIMIT 1 without deterministic tie-break.

### Item: `2123` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts from Staff, so agencies with zero staff are excluded; should aggregate from Agencies with LEFT JOIN to include zeros. Also LIMIT 1 arbitrarily picks one on ties.

### Item: `2132` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows per meeting in Staff_in_Meetings, which may overcount if duplicate staff entries exist and excludes meetings with zero staff. Prefer COUNT(DISTINCT staff_id) and LEFT JOIN from Meetings to include all.

### Item: `2133` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): Counts rows in Staff_in_Meetings only; meetings with no staff are omitted, and duplicates per meeting may be double-counted. Should LEFT JOIN Meetings and COUNT(DISTINCT staff_id).

### Item: `2134` (DB: `advertising_agencies`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (INCORRECT): Uses LIMIT 1, so it returns only one staff member. It should return all staff with the lowest attendance (handle ties among those who attended at least one meeting).

### Item: `2135` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5** (PARTIALLY_CORRECT): LIMIT 1 returns only one staff id; if multiple staff tie for the fewest meetings, others are omitted. It also returns the count column, which wasn’t requested.

### Item: `2146` (DB: `advertising_agencies`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (PARTIALLY_CORRECT): Inner joins to Staff_in_Meetings/Staff drop meetings with no staff, conflicting with “each meeting.” Use LEFT JOINs from Meetings to include all meetings (staff_details may be NULL).
  - **gemini-2.5-pro** (CORRECT)

## 🚫 Majority UNANSWERABLE

**Found 2 queries where majority of voters said UNANSWERABLE** (showing ALL)

These queries cannot be answered from the schema (missing data, ambiguous question, etc.).

### Item: `1129` (DB: `pilot_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gpt-5** (UNANSWERABLE): Ownership is not represented in the schema. PilotSkills shows pilots’ skills and Hangar shows locations; no column indicates who owns a plane, so Smith’s owned planes can’t be counted.
  - **gemini-2.5-pro** (UNANSWERABLE): The schema does not contain information about plane ownership. The `PilotSkills` table links pilots to planes they are skilled to fly, not planes they own.

### Item: `1265` (DB: `art_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 0 INCORRECT, 2 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (UNANSWERABLE): The question is ambiguous. The schema for paintings includes 'height_mm' and 'width_mm', but it is unclear what 'length' refers to.
  - **gpt-5** (UNANSWERABLE): Ambiguous term 'length': schema has height_mm and width_mm; unclear whether to order by height, width, or another measure. Cannot determine correct ordering.
