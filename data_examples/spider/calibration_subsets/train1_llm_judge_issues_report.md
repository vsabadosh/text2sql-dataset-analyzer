# LLM Judge Semantic Validation Report

**Generated:** 2026-02-28 19:06:20

## Summary

- **Total Queries Evaluated:** 60
- **Majority CORRECT:** 33 (55.0%)
    *of which Unanimous CORRECT: 19 (31.7%)*
- **Majority PARTIALLY_CORRECT:** 1 (1.7%)
    *of which Unanimous PARTIALLY_CORRECT: 1 (1.7%)*
- **Majority INCORRECT:** 18 (30.0%)
    *of which Unanimous INCORRECT: 14 (23.3%)*
- **Mixed (No Majority):** 8 (13.3%)
    *(Mixed results have no consensus by definition)*

### Mixed Consensus Breakdown

| claude-sonnet-4-5 | gemini-2.5-pro | gemini-3.1-pro-preview | gpt-5.2 | Count |
|-------|-------|-------|-------|-------|
| CORRECT | INCORRECT | CORRECT | PARTIALLY_CORRECT | 2 |
| INCORRECT | INCORRECT | CORRECT | PARTIALLY_CORRECT | 2 |
| CORRECT | CORRECT | PARTIALLY_CORRECT | INCORRECT | 1 |
| INCORRECT | CORRECT | PARTIALLY_CORRECT | INCORRECT | 1 |
| INCORRECT | INCORRECT | PARTIALLY_CORRECT | PARTIALLY_CORRECT | 1 |
| PARTIALLY_CORRECT | CORRECT | CORRECT | PARTIALLY_CORRECT | 1 |
- **Majority UNANSWERABLE:** 0 (0.0%)
    *of which Unanimous UNANSWERABLE: 0 (0.0%)*

---
NOTE: 595 - mark as correct but in original is marked as Partial_correct.
5380 - mark as correct but in original it is mixed
## ✅ Majority CORRECT (Non-Unanimous)

**Found 14 queries where majority (but not all) voters said CORRECT** (showing ALL)

These queries are likely correct but had some voter disagreement.

### Item: `486` (DB: `allergy_1`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (CORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Returns last names of all students tied for minimum age; question implies a single youngest student, so it may return multiple rows without tie-breaking.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `1184` (DB: `election_representative`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Orders names by election.Votes but may repeat representatives if they have multiple election rows; question likely expects unique reps or aggregated votes per representative.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `1492` (DB: `college_2`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Doesn't use DISTINCT so duplicate names possible; if Biology has no instructors, MAX(salary) is NULL and the comparison yields no rows (may need all instructors).
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `1507` (DB: `debate`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Logic matches, but NOT IN can return no rows if debate_people.Affirmative contains NULL; safer to use NOT EXISTS to avoid NULL-related edge case.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `1965` (DB: `products_for_hire`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 3 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **gpt-5.2** (INCORRECT): It counts rows per product (number of booking records), not how many times/units were booked. If “3 times” refers to booked_count, it should use SUM(booked_count)=3 or filter booked_count=3.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `3486` (DB: `hr_1`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN**  (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts job_history rows per employee, not distinct jobs; employees with multiple stints in the same JOB_ID could be incorrectly included. Use COUNT(DISTINCT job_id).
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `3487` (DB: `hr_1`) (FINISH SO FAR)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 3 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN**  (INCORRECT/PARTIALLY_CORRECT/NOT_SURE, but it seems gpt-5.2 and gpt-5 criticizm is right)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5.2** (INCORRECT): job_history stores only past jobs; an employee with 1 job_history row has held 2 jobs (past+current). Query requires >=2 history rows (>=3 jobs) and misses such employees.
  - **claude-sonnet-4-5** (CORRECT)

### Item: `3527` (DB: `hr_1`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN**  (PARTIALLY_CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Uses INNER JOIN so departments with zero employees are omitted; also groups only by department_name, which could merge departments if names aren’t unique. Use LEFT JOIN from departments and group by department_id/name.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `3803` (DB: `e_learning`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Correct join and filter, but may return duplicate login_name values if multiple "advanced database" course rows exist or same author appears multiple times; DISTINCT may be needed.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `4213` (DB: `cre_Doc_Tracking_DB`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Returns role name/description for employees named Ebba, but if multiple employees share that name it may return multiple (possibly duplicate) rows; DISTINCT or Employee_ID filter may be needed.
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `4264` (DB: `club_1`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT/NOT_SURE)
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts rows after joining; if Member_of_club can contain multiple rows per student/club, it may overcount. To count members, COUNT(DISTINCT t2.StuID) is safer.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `4875` (DB: `school_player`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Returns only one team; if multiple players share the highest age, it should return all corresponding teams (e.g., via WHERE Age = (SELECT MAX(Age) ...)).
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)

### Item: `5168` (DB: `cre_Drama_Workshop_Groups`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 3 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query attempts to calculate the average of the `Order_Quantity` column, which has a VARCHAR data type. This will lead to incorrect results as string aggregation is not meaningful for an average.
  - **gpt-5.2** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `5290` (DB: `manufactory_1`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gpt-5.2** (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT; query may return duplicate founders if same person founded multiple companies starting with 'S'

## ⚡ Majority PARTIALLY_CORRECT

**Found 1 queries where majority of voters said PARTIALLY_CORRECT** (showing up to 50)

These queries are mostly correct but may have minor issues.

### Item: `3684` (DB: `baseball_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 4 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Uses UNION, which removes duplicate salary values across/within the two years. If the question expects all salary records (including duplicates), it should use UNION ALL.
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Using UNION removes duplicate salary values. To return all salary values including duplicates, UNION ALL or an OR/IN clause should be used.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query uses UNION, which removes duplicate salary values. The question asks for 'all' salary values, which implies that if multiple players had the same salary, it should be listed multiple times. Using UNION ALL would be more accurate.
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Uses UNION which deduplicates salary amounts; should use UNION ALL to return all salary records from both years as indicated by 'all the salary values'

## ❌ Majority INCORRECT

**Found 18 queries where majority of voters said INCORRECT** (showing ALL)

These queries are likely semantically incorrect and need review.

### Item: `870` (DB: `chinook_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Selects Customer.FirstName (T1) instead of Employee.FirstName (T2). Should return employee first names/ids (e.g., T2.FirstName, T2.EmployeeId) for reps with >=10 customers.
  - **gemini-2.5-pro** (INCORRECT): The query selects the customer's first name (T1.FirstName) instead of the employee's first name (T2.FirstName) as requested by the question.
  - **gemini-3.1-pro-preview** (INCORRECT): The query selects the customer's first name (T1.FirstName) instead of the employee's first name (T2.FirstName).
  - **claude-sonnet-4-5** (INCORRECT): Query selects T1.FirstName (customer first name) instead of T2.FirstName (employee first name). The question asks for employee first names, not customer first names.

### Item: `1223` (DB: `apartment_rentals`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Selects booking_start_date twice; should return booking_start_date and booking_end_date for Duplex apartments.
  - **gemini-3.1-pro-preview** (INCORRECT): The query selects 'booking_start_date' twice instead of selecting both 'booking_start_date' and 'booking_end_date'.
  - **gemini-2.5-pro** (INCORRECT): The query selects the booking_start_date twice, but the question asks for both the booking_start_date and the booking_end_date.
  - **claude-sonnet-4-5** (INCORRECT): Query selects booking_start_date twice instead of selecting both booking_start_date and booking_end_date as requested.

### Item: `1695` (DB: `epinions_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Question asks for the highest rank, but the query uses MIN(rank). It should use MAX(rank) (unless rank=1 is considered highest, which the query doesn’t reflect).
  - **gemini-2.5-pro** (INCORRECT): The query finds the minimum rank, but the question asks for the highest rank. In the context of ranking, a lower number usually means a higher rank (e.g., rank 1 is the highest). However, without this assumption, 'highest' typically implies the maximum value. The query should use MAX(rank) to be unambiguous.
  - **gemini-3.1-pro-preview** (INCORRECT): The query uses min(rank) instead of max(rank) to find the highest rank.
  - **claude-sonnet-4-5** (CORRECT)

### Item: `2357` (DB: `csu_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Question asks overall total degrees 1998-2002, but query groups by campus and returns per-campus sums instead of a single total sum across all campuses.
  - **gemini-2.5-pro** (INCORRECT): The question asks for the single total number of degrees granted. The query incorrectly groups the results by campus, providing a per-campus total instead of the overall total.
  - **gemini-3.1-pro-preview** (INCORRECT): The query groups the results by campus, returning the total per campus instead of the overall total number of degrees granted as requested.
  - **claude-sonnet-4-5** (INCORRECT): Question asks for 'the total number' (singular, overall total), but query groups by campus returning multiple per-campus totals instead of one aggregate sum across all campuses.

### Item: `2379` (DB: `csu_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Filters on Campuses.Year=2004 (campus founding year) instead of faculty.Year=2004, so it won’t return campuses with 600–1000 faculty in year 2004.
  - **gemini-3.1-pro-preview** (INCORRECT): The query filters on T1.year (the year the campus was established) instead of t2.year (the year of the faculty record).
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters on the campus founding year (`T1.year`) instead of the year of the faculty data (`t2.year`). The condition should be `t2.year = 2004`.
  - **claude-sonnet-4-5** (INCORRECT): Query filters on Campuses.Year (campus establishment year) instead of faculty.Year. Should use 't2.year = 2004' to filter faculty data from year 2004.

### Item: `2517` (DB: `movie_1`)

- **Weighted Score:** 0.125
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Uses Rating as base set, so movies with no ratings are omitted. Should start from all Movie.mID and exclude those reviewed by Brittany Harris.
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Uses Rating instead of Movie for the base set, which misses movies that have no reviews at all.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly excludes movies that have never been reviewed at all. The initial set should be all movies from the Movie table, not just the rated movies from the Rating table.
  - **claude-sonnet-4-5** (INCORRECT): Query only considers movies with at least one rating. Should use 'SELECT mID FROM Movie' instead of 'SELECT mID FROM Rating' to include movies with no ratings at all.

### Item: `2732` (DB: `storm_record`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Orders by deaths and LIMIT 1 returns only one region row, not all regions affected by the deadliest storm. Should first select storm(s) with max Number_Deaths then list all related regions.
  - **gemini-3.1-pro-preview** (INCORRECT): LIMIT 1 restricts the output to a single region, even if the storm with the most deaths affected multiple regions. A subquery should be used to find the storm first.
  - **gemini-2.5-pro** (INCORRECT): The query uses `ORDER BY ... LIMIT 1`, which will only return a single region name. This is incorrect if multiple regions were affected by the storm that caused the most deaths.
  - **claude-sonnet-4-5** (INCORRECT): Query returns only one region due to LIMIT 1, but should return all regions affected by the deadliest storm. It arbitrarily picks one region instead of all affected regions.

### Item: `2857` (DB: `customer_deliveries`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **gpt-5.2** (INCORRECT): Counts route locations (Delivery_Route_Locations) per route, not deliveries. Should count rows in Order_Deliveries joined via location_code to route_id to get deliveries per route.
  - **gemini-3.1-pro-preview** (INCORRECT): The query counts the number of locations per route instead of the number of deliveries because it fails to join with the Order_Deliveries table.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of locations per route, not the number of deliveries. It is missing a join with the Order_Deliveries table to correctly count the deliveries for each route.
  - **claude-sonnet-4-5** (INCORRECT): Query counts route locations, not deliveries. Missing join to Order_Deliveries table which contains the actual delivery records.

### Item: `3024` (DB: `loan_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Groups by cust_name, so different customers sharing a name are merged and totals wrong. Should group by customer identifier (cust_ID) and then order by SUM(amount) (often DESC).
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query groups by customer name, which is not guaranteed to be unique. This can incorrectly combine the loan amounts of different customers who happen to share the same name. Grouping should be by cust_ID.
  - **claude-sonnet-4-5** (INCORRECT): Query groups by cust_name instead of cust_ID. If multiple customers share the same name, their loans will be incorrectly aggregated together, violating the intent of 'different customers'.

### Item: `3589` (DB: `music_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Need the top artist per language among songs with resolution>500. Query groups only by languages, returns one overall row (LIMIT 1) and picks arbitrary artist_name per language group.
  - **gemini-3.1-pro-preview** (INCORRECT): The query uses LIMIT 1, returning only one artist overall instead of one per language. It also selects an arbitrary artist per language group rather than the one with the most songs.
  - **gemini-2.5-pro** (INCORRECT): The query finds an arbitrary artist from the language with the most high-resolution songs overall. It does not find the top artist *for each* language as requested by the question.
  - **claude-sonnet-4-5** (INCORRECT): Query groups by languages only without artist_name, making artist_name arbitrary. LIMIT 1 returns only 1 row total instead of one artist per language as required.

### Item: `3638` (DB: `baseball_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Counts all hall_of_fame records per year, including non-inducted entries and possible multiple rows per player/voting body. Should filter inducted='Y' and typically count DISTINCT player_id.
  - **gemini-3.1-pro-preview** (INCORRECT): The query counts all players on the Hall of Fame ballot each year, not just those who were inducted. It needs a filter for inducted = 'Y'.
  - **gemini-2.5-pro** (INCORRECT): The query counts all ballot appearances per year, not the number of players who were actually inducted. It needs a `WHERE inducted = 'Y'` clause to correctly answer the question.
  - **claude-sonnet-4-5** (INCORRECT): Query counts all hall_of_fame records per year, including non-inductees. Should filter WHERE inducted = 'Y' to count only players who actually entered the hall of fame.

### Item: `3642` (DB: `baseball_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Join to team is only on team_id and doesn’t restrict team.year=2014 (or join on year). This can pull an arbitrary rank from other years, so team rank/id may be wrong.
  - **gemini-3.1-pro-preview** (INCORRECT): The query joins 'home_game' and 'team' only on 'team_id' without restricting 'team.year = 2014'. This causes a Cartesian product across all years for the team, returning an arbitrary year's rank.
  - **gemini-2.5-pro** (INCORRECT): The query fails to filter the `team` table by year. It should join on both team_id and year (e.g., `... AND T1.year = T2.year`) to retrieve the correct rank for 2014.
  - **claude-sonnet-4-5** (INCORRECT): JOIN lacks year constraint on team table. Should include AND T1.year = T2.year or add T2.year = 2014 to WHERE clause, otherwise rank may be from wrong year.

### Item: `3663` (DB: `baseball_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gemini-3.1-pro-preview** (INCORRECT): The query is missing the ON clause in the JOIN between player and player_award, resulting in a Cartesian product. It will return all players instead of just those who actually won the awards.
  - **gpt-5.2** (INCORRECT): JOINs to player_award have no ON condition, creating a Cartesian product; filtering only by year returns (distinct) all player names for both years, not just award winners in both 1960 and 1961.
  - **gemini-2.5-pro** (INCORRECT): The query is missing the join condition (`ON T1.player_id = T2.player_id`) in both subqueries. This results in a cross join, failing to correctly link players to their awards for the specified years.
  - **claude-sonnet-4-5** (INCORRECT): JOIN between player and player_award missing ON clause to match player_id, creating Cartesian product instead of properly linking players to their awards

### Item: `3694` (DB: `baseball_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gemini-3.1-pro-preview** (INCORRECT): The JOIN condition T1.team_id = T2.team_id_br is incorrect. According to the schema, home_game.team_id is a foreign key referencing team.team_id, not team.team_id_br.
  - **gpt-5.2** (INCORRECT): JOIN is wrong: home_game.team_id should match team.team_id (and year/league_id), not team_id_br. Missing year/league join can also multiply rows, inflating the SUM.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly joins `home_game.team_id` with `team.team_id_br`. The correct join condition, as indicated by the foreign key relationship, should be `T1.team_id = T2.team_id`.
  - **claude-sonnet-4-5** (INCORRECT): JOIN uses wrong column: home_game.team_id should join with team.team_id (per FK constraint), not team.team_id_br which has different values (e.g., 'BS1' vs 'BOS').

### Item: `3900` (DB: `hospital_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): Counts rows in Department (always 1 per dept), not employees. Need to count physicians per department via Affiliated_With (and possibly include heads) to find dept with most employees.
  - **gemini-2.5-pro** (INCORRECT): The query only counts departments from the `department` table, not the number of employees within each department. It needs to join with the `Affiliated_With` table to count the physicians associated with each department.
  - **gemini-3.1-pro-preview** (INCORRECT): The query fails to join with the Affiliated_With table to count the actual number of employees (physicians) per department. It only counts the primary key of the department table itself, which is always 1.
  - **claude-sonnet-4-5** (INCORRECT): Query doesn't count employees. It only groups departments by ID and counts departmentID (always 1 per group). Missing JOIN with Affiliated_With table to count physicians per department.

### Item: `4456` (DB: `network_2`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **gpt-5.2** (INCORRECT):
  - **gpt-5.2** (INCORRECT): Query returns people who have Bob as their friend (T2.friend='Bob') rather than Bob's friends. Should filter T2.name='Bob' and select T2.friend.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query only finds people who list Bob as a friend (where `friend` = 'Bob'). It misses the other direction: people whom Bob lists as a friend (where `name` = 'Bob').
  - **claude-sonnet-4-5** (INCORRECT): Query finds people who have Bob as a friend (WHERE friend='Bob'), but the question asks for Bob's friends, which requires WHERE name='Bob' to find people that Bob is friends with.

### Item: `5253` (DB: `music_2`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): It returns songs that have vocals but not a 'back' vocal; it misses songs with no vocals records at all. Should start from Songs and exclude those with Vocals.Type='back'.
  - **gemini-2.5-pro** (INCORRECT): The query's first part only selects songs that have at least one vocal performance. This incorrectly excludes songs with no vocals at all, which should be included in the result.
  - **gemini-3.1-pro-preview** (INCORRECT): The query only considers songs present in the vocals table. It misses songs that have no vocals at all, which also do not have a back vocal.
  - **claude-sonnet-4-5** (INCORRECT): Query only returns songs with vocals but not back vocals. It misses songs that have no vocal entries at all, which also do not have back vocals.

### Item: `5440` (DB: `shop_membership`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): Question asks for total purchase amounts for level 6 members (e.g., SUM of purchase.Total_pounds). Query returns COUNT of purchase rows instead of summing amounts.
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of purchases using COUNT(*), but the question asks for the 'total purchases', which implies summing the purchase amounts. The correct aggregation is SUM(T1.Total_pounds).
  - **gemini-3.1-pro-preview** (INCORRECT): The query uses COUNT(*) to find the number of purchase records instead of SUM(Total_pounds) to calculate the total purchase amount.
  - **claude-sonnet-4-5** (INCORRECT): Query uses COUNT(*) to count purchase records, but 'total purchases' should be SUM(Total_pounds) to sum the monetary values of purchases for level 6 members.

## ⚠️ Mixed (No Majority)

**Found 8 queries with mixed voter verdicts (no majority)** (showing ALL)

These queries have no clear majority verdict and require manual review.

### Item: `247` (DB: `musical`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 2 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Returns musical names filtered by Nominee='Bob Fosse', but may output duplicate names if multiple rows exist per musical; DISTINCT may be needed for unique musical names.
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT - could return duplicate musical names if Bob Fosse has multiple nominations for the same musical.

### Item: `859` (DB: `chinook_1`)

- **Weighted Score:** 0.375
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Uses LastName in EXCEPT, so if any customer with a given last name has an invoice total>20, that last name is removed for all customers sharing it. Should filter by CustomerId.
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Using EXCEPT on LastName may incorrectly exclude valid customers if they share a last name with a customer who has an invoice total > 20. EXCEPT should be applied on CustomerId instead.
  - **claude-sonnet-4-5** (INCORRECT): Query uses EXCEPT on LastName. If customers share a name but only one has invoice >20, all are incorrectly excluded. Should filter customers first, then select LastName.

### Item: `1266` (DB: `apartment_rentals`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (CORRECT) 
  - **gpt-5.2** (PARTIALLY_CORRECT): Uses correct grouping and aggregates, but room_count is CHAR; MAX/MIN may compare lexicographically (e.g., '10' vs '2') unless cast to integer.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The `room_count` column is of type CHAR. Applying MIN/MAX functions will result in a lexicographical (text) comparison, not a numerical one, which is semantically incorrect for finding the number of rooms.
  - **claude-sonnet-4-5** (CORRECT)

### Item: `3214` (DB: `college_1`)

- **Weighted Score:** 0.375
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Uses INNER JOIN, so schools with zero professors are excluded; question could require returning such a school (count 0). LEFT JOIN from department (or schools) needed to include them.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which will exclude schools that have zero professors. A LEFT JOIN from department to professor is needed to correctly find the school with the minimum count, which could be zero.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (INCORRECT): INNER JOIN excludes schools with zero professors, potentially missing the correct answer if such schools exist.

### Item: `3292` (DB: `college_1`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): It INTERSECTs by EMP_FNAME, so two different professors sharing a first name (one teaching CIS-220, another QM-261) would be falsely returned. Must match by professor (EMP_NUM) first.
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Intersecting on first name instead of a unique identifier (like employee ID) can return false positives if different professors share the same first name.
  - **claude-sonnet-4-5** (CORRECT)

### Item: `3851` (DB: `insurance_policies`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Max-claim-value branch joins Settlements, so it excludes claims with the maximum Amount_Claimed if they have no settlements. The question doesn’t require a settlement for that condition.
  - **gemini-2.5-pro** (INCORRECT): The second part of the UNION unnecessarily joins to the Settlements table. This will cause a claim with the maximum amount to be listed multiple times if it has more than one settlement, which is incorrect.
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): The second query in the UNION unnecessarily joins with Settlements, which will incorrectly exclude the claim with the maximum value if it has no settlements.
  - **claude-sonnet-4-5** (INCORRECT): The second part of the UNION unnecessarily joins with Settlements, which would exclude claims with maximum Amount_Claimed that have no settlements.

### Item: `4546` (DB: `company_office`)

- **Weighted Score:** 0.375
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Market_Value_billion is TEXT; ORDER BY will sort lexicographically, not numerically. Should CAST(Market_Value_billion AS REAL) to ensure correct descending market value order.
  - **gemini-2.5-pro** (INCORRECT): The `Market_Value_billion` column is of type TEXT. Ordering it directly will result in lexicographical (alphabetical) sorting, not numerical sorting, which is incorrect for this question.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (INCORRECT): Market_Value_billion is TEXT type. Ordering TEXT lexicographically gives incorrect numeric ordering (e.g., '9' > '100'). Should cast to numeric for correct market value sorting.

### Item: `4735` (DB: `department_store`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT):
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Uses DISTINCT on customer_name but orders by customer_id; if multiple customers share a name, DISTINCT collapses them and ordering by id becomes ambiguous/non-deterministic.
  - **gemini-2.5-pro** (INCORRECT): The query selects distinct customer names but orders by customer ID. If multiple customers share the same name, the customer ID used for sorting is ambiguous, leading to a non-deterministic order.
  - **claude-sonnet-4-5** (CORRECT)

## 🚫 Majority UNANSWERABLE

*No majority UNANSWERABLE queries found.*
