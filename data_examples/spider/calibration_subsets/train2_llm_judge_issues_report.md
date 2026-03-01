# LLM Judge Semantic Validation Report

**Generated:** 2026-02-28 19:33:55

## Summary

- **Total Queries Evaluated:** 46
- **Majority CORRECT:** 23 (50.0%)
    *of which Unanimous CORRECT: 12 (26.1%)*
- **Majority PARTIALLY_CORRECT:** 1 (2.2%)
    *of which Unanimous PARTIALLY_CORRECT: 0 (0.0%)*
- **Majority INCORRECT:** 11 (23.9%)
    *of which Unanimous INCORRECT: 7 (15.2%)*
- **Mixed (No Majority):** 11 (23.9%)
    *(Mixed results have no consensus by definition)*

### Mixed Consensus Breakdown

| claude-sonnet-4-5 | gemini-2.5-pro | gemini-3.1-pro-preview | gpt-5.2 | Count |
|-------|-------|-------|-------|-------|
| CORRECT | CORRECT | INCORRECT | PARTIALLY_CORRECT | 3 |
| CORRECT | INCORRECT | CORRECT | PARTIALLY_CORRECT | 2 |
| CORRECT | CORRECT | PARTIALLY_CORRECT | PARTIALLY_CORRECT | 1 |
| INCORRECT | CORRECT | CORRECT | PARTIALLY_CORRECT | 1 |
| INCORRECT | CORRECT | INCORRECT | PARTIALLY_CORRECT | 1 |
| INCORRECT | INCORRECT | CORRECT | PARTIALLY_CORRECT | 1 |
| INCORRECT | INCORRECT | PARTIALLY_CORRECT | PARTIALLY_CORRECT | 1 |
| PARTIALLY_CORRECT | CORRECT | CORRECT | PARTIALLY_CORRECT | 1 |
- **Majority UNANSWERABLE:** 0 (0.0%)
    *of which Unanimous UNANSWERABLE: 0 (0.0%)*

---
5539, 5680 - Correct

## ✅ Majority CORRECT (Non-Unanimous)

**Found 11 queries where majority (but not all) voters said CORRECT** (showing ALL)

These queries are likely correct but had some voter disagreement.

### Item: `5998` (DB: `game_1`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts students per advisor correctly, but will also return NULL as an 'advisor' if 2+ students have Advisor IS NULL; should typically filter out NULL advisors.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `6018` (DB: `game_1`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts SportsInfo rows per student, not distinct sports; if multiple rows per sport exist it may overcount. Use COUNT(DISTINCT SportName). Also LIMIT 1 ignores ties.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `6237` (DB: `ship_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 3 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
 - **HUMAN** (CORRECT):
  - **gpt-5.2** (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query applies numeric aggregate functions (AVG, MIN) to the 'age' column, which has a TEXT data type. This will result in incorrect calculations, as MIN will perform a string comparison.
  - **claude-sonnet-4-5** (CORRECT)

### Item: `6342` (DB: `e_government`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
 - **HUMAN** (PARTIALLY_CORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts service usages but groups by party_email instead of party_id; if multiple parties share an email, their counts are combined and could return wrong party/email.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `6855` (DB: `flight_4`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (CORRECT):
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts grouped city values with >3 airports, but will include NULL as a 'city' if there are >3 airports with city IS NULL; question likely intends non-NULL cities.
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `6861` (DB: `flight_4`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Uses INNER JOIN so airports with 0 departing routes are omitted (should be LEFT JOIN for full list). Grouping only by name can also merge different airports sharing a name.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `7133` (DB: `geo`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  -  **HUMAN** (UNANSWERABLE)
  - **gpt-5.2** (PARTIALLY_CORRECT): city has PK (city_name,state_name); filtering only by city_name may return multiple Boulders in different states, so query may not yield a single intended population.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `7135` (DB: `geo`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:** 
  - **HUMAN** (UNANSWERABLE):
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): city_name isn’t unique (PK is city_name,state_name). Filtering only by city_name may return multiple Boulder rows; question implies a single population but state isn’t specified.
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `7748` (DB: `scholar`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Finds papers authored by the given author via writes/author joins, but returns only paperId and year (and includes year not asked); likely should list paper titles/details.
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `8454` (DB: `imdb`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (UNANSWERABLE)
  - **gpt-5.2** (PARTIALLY_CORRECT): Likely returns the actor name, but may output duplicates if multiple cast rows match; DISTINCT may be needed. Also assumes cast.role stores the character name (DDL says INT).
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `8625` (DB: `restaurants`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Finds French restaurants in the specified region and filters by rating, but only returns house_number (no street/city) and the 'good' threshold (rating>2.5) is arbitrary/not clearly implied.
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

## ⚡ Majority PARTIALLY_CORRECT

**Found 1 queries where majority of voters said PARTIALLY_CORRECT** (showing up to 50)

These queries are mostly correct but may have minor issues.

### Item: `6488` (DB: `scientist_1`)

- **Weighted Score:** 0.375
- **Voter Breakdown:** 0 CORRECT, 3 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Sums hours per assignment row; if both scientists are assigned to the same project, that project’s Hours will be counted twice. Should dedupe projects before summing.
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Joins may produce duplicate projects if multiple matching scientists are assigned to the same project, causing hours to be summed multiple times.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly double-counts the hours of projects that are assigned to both 'Michael Rogers' and 'Carol Smith'. It should sum the hours of the unique set of projects assigned to either scientist.
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT on projects; if both scientists are assigned to the same project, its hours will be counted multiple times instead of once.

## ❌ Majority INCORRECT

**Found 11 queries where majority of voters said INCORRECT** (showing ALL)

These queries are likely semantically incorrect and need review.

### Item: `5535` (DB: `products_gen_characteristics`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT): 
  - **gpt-5.2** (INCORRECT): Uses typical_buying_price > 1000, but the question asks for products typically sold above 1000 (should filter on typical_selling_price).
  - **gemini-2.5-pro** (INCORRECT): The query filters on `typical_buying_price`, but the question asks about products 'sold' above 1000, which corresponds to the `typical_selling_price` column.
  - **gemini-3.1-pro-preview** (INCORRECT): The query filters on typical_buying_price instead of typical_selling_price as requested by 'typically sold above 1000'.
  - **claude-sonnet-4-5** (INCORRECT): Query uses 'typical_buying_price' but question asks for 'typically sold above 1000' which should use 'typical_selling_price' instead.

### Item: `5590` (DB: `products_gen_characteristics`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): The WHERE clause filters color_description = 'white' but question asks products that are NOT white. It should use != 'white' (or <>), along with unit_of_measure != 'Handful'.
  - **gemini-3.1-pro-preview** (INCORRECT): The query filters for products that ARE 'white' in color (t3.color_description = "white") instead of products that are NOT 'white', contradicting the question.
  - **gemini-2.5-pro** (INCORRECT): The query filters for products with the color 'white' (`t3.color_description = "white"`), but the question asks for products that are NOT 'white'.
  - **claude-sonnet-4-5** (INCORRECT): WHERE clause uses color_description = 'white' but question asks for products that are NOT white. Should use != or <> instead of =.

### Item: `5740` (DB: `dorm_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): Adds unrelated filter student_capacity>100 and uses INNER JOIN, excluding dorms with 0 amenities. Question asks amenities count for each dorm with no extra filtering.
  - **gemini-3.1-pro-preview** (INCORRECT): The query incorrectly filters for dorms with student capacity > 100, which is not requested in the natural language question.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for dorms with a student capacity greater than 100, but the question asks for the amenity count for all dorms.
  - **claude-sonnet-4-5** (INCORRECT): Query filters dorms with student_capacity > 100, but question asks for 'each dorm' (all dorms). Also INNER JOIN excludes dorms with no amenities.

### Item: `5813` (DB: `customer_complaints`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): Orders by COUNT(*) ascending, so it returns the state with the fewest customers. Should order by COUNT(*) DESC to get the most customers.
  - **gemini-3.1-pro-preview** (INCORRECT): The query uses ORDER BY count(*) ASC (default), which returns the state with the least customers instead of the most. It should use ORDER BY count(*) DESC.
  - **gemini-2.5-pro** (INCORRECT): The query orders the results in ascending order of customer count by default. To find the state with the 'most' customers, it should explicitly order in descending order (DESC).
  - **claude-sonnet-4-5** (INCORRECT): ORDER BY count(*) defaults to ASC, returning the state with the FEWEST customers. Should be ORDER BY count(*) DESC to get the state with the MOST customers.

### Item: `6060` (DB: `customers_and_addresses`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): It averages order_quantity across order item rows, not total items per order. Need SUM(order_quantity) grouped by order_id, then AVG of those per-order sums.
  - **gemini-3.1-pro-preview** (INCORRECT): The query calculates the average quantity per order item, not the average total quantity per order. It should sum the quantities per order first or divide the total sum by the count of distinct orders.
  - **gemini-2.5-pro** (INCORRECT): The query calculates the average quantity per item line, not the average total quantity per order. It should first sum the quantities for each order and then calculate the average of those sums.
  - **claude-sonnet-4-5** (INCORRECT): Query averages individual line item quantities across all rows, but the question asks for the average total amount per order, which requires summing quantities per order_id first, then averaging those totals.

### Item: `6100` (DB: `customers_and_addresses`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): Query takes MAX(active_to_date) over all channels for the customer, not the active_to_date of the latest contact channel record (e.g., the one with greatest active_from_date).
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query finds the maximum 'active_to_date' among all contact channels for the customer. The question asks for the 'active_to_date' of the 'latest' channel, which should be identified by the most recent 'active_from_date'.
  - **claude-sonnet-4-5** (INCORRECT): Query returns max(active_to_date) across all channels instead of the active_to_date of the channel with the most recent active_from_date (the latest channel used).

### Item: `6607` (DB: `train_station`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): Query requires a single station to have both >=15 platforms AND >25 passengers. Question can mean a location has (possibly different) stations meeting each condition; needs grouping/EXISTS per location.
  - **gemini-3.1-pro-preview** (INCORRECT): The query requires a single station to meet both conditions, but the question asks for locations that have stations meeting each condition (potentially different stations), requiring INTERSECT.
  - **gemini-2.5-pro** (INCORRECT): The query finds locations where a single station meets both conditions. The question asks for locations that have at least one station with >=15 platforms AND at least one station with >25 passengers, which could be two different stations.
  - **claude-sonnet-4-5** (INCORRECT): Query requires same station to meet both conditions. Question asks for locations with stations having >=15 platforms AND stations with >25 passengers (potentially different stations).

### Item: `7498` (DB: `geo`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **INCORRECT**
  - **gpt-5.2** (INCORRECT): Query filters only by area>750 and ignores that lakes must be in the United States (country_name). Also 'major' isn’t defined; at minimum it should filter country_name for USA.
  - **gemini-3.1-pro-preview** (INCORRECT): The query is missing a filter for 'United States' (e.g., country_name = 'USA').
  - **gemini-2.5-pro** (INCORRECT): The query fails to filter for lakes located in the 'united states', which is a key constraint in the question. It will return major lakes from all countries in the database.
  - **claude-sonnet-4-5** (INCORRECT): Query missing WHERE clause filter for country_name to restrict results to United States. Currently returns major lakes from any country, not just USA as specified in question.

### Item: `7533` (DB: `geo`)

- **Weighted Score:** 0.125
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): Query takes MAX(area) over all states without restricting to USA; should filter state.country_name to USA to answer the question.
  - **gemini-2.5-pro** (INCORRECT): The query finds the maximum area among all states in the database, but it fails to filter for states that are in the 'usa' as specified in the question.
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): The query is missing a filter for country_name = 'usa' as specified in the natural language question.
  - **claude-sonnet-4-5** (INCORRECT): Query missing WHERE clause to filter for USA states. It returns the largest state from all countries in the database, not specifically from the USA as required by the question.

### Item: `7556` (DB: `geo`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Query finds largest city in any state with a river but ignores “American” requirement (no filter on city/state country_name for USA).
  - **gemini-2.5-pro** (INCORRECT): The query does not filter for 'American' cities as requested by the question. It should include a condition on the `country_name` column from the `city` table.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (INCORRECT): Query doesn't filter for American cities (missing country_name condition) as required by the question.

### Item: `8651` (DB: `restaurants`)

- **Weighted Score:** 0.125
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT) 
  - **gpt-5.2** (PARTIALLY_CORRECT): Returns only house_number (and name) but not the full location/address; likely should include street_name (and possibly city) to answer “where”.
  - **gemini-3.1-pro-preview** (INCORRECT): Filters on restaurant name instead of food_type for 'jamerican cuisine'. Additionally, it only selects house_number, missing street_name which is required to answer 'where'.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters on the restaurant's name (`t1.name`) instead of the food type (`t1.food_type`). The question is asking for a type of cuisine, not a specific restaurant name.
  - **claude-sonnet-4-5** (INCORRECT): Query filters by restaurant NAME='jamerican cuisine' instead of FOOD_TYPE. The question asks for restaurants serving jamerican cuisine (food type), not named 'jamerican cuisine'.

## ⚠️ Mixed (No Majority)

**Found 11 queries with mixed voter verdicts (no majority)** (showing ALL)

These queries have no clear majority verdict and require manual review.

### Item: `5827` (DB: `workshop_paper`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts submissions per college, not necessarily number of (distinct) authors. If an author has multiple submissions, should use COUNT(DISTINCT Author) grouped by College.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (INCORRECT): Query uses COUNT(*) which counts submissions, not distinct authors. Authors with multiple submissions from same college would be counted multiple times.

### Item: `6086` (DB: `customers_and_addresses`)

- **Weighted Score:** 0.375
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts address records per city, not distinct customers. Also doesn’t restrict to residential/current addresses (e.g., address_type='Residential' and date_address_to IS NULL), so may not reflect where customers live.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query counts the number of addresses per city (COUNT(*)) instead of the number of unique customers (COUNT(DISTINCT T1.customer_id)), which is what the question asks for.
  - **claude-sonnet-4-5** (INCORRECT): Query counts customer-address relationships not unique customers. A customer with multiple addresses in same city is counted multiple times. Should use COUNT(DISTINCT customer_id).

### Item: `7588` (DB: `scholar`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts syntactic-parsing papers per author and orders desc, but doesn’t return only the top author (no LIMIT 1) and returns authorId rather than the author name.
  - **gemini-3.1-pro-preview** (INCORRECT): The query fails to return the author's name (returns authorid instead) and is missing LIMIT 1 to isolate the author with the most publications.
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `7614` (DB: `scholar`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** PARTIALLY_CORRECT
  - **gpt-5.2** (PARTIALLY_CORRECT): It counts 2016 papers for that author, but returns a count/authorId (or no row) rather than an explicit yes/no. Also relies on exact authorName match.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The user is asking a yes/no question ('Has mirella lapata written any papers...?'). The query returns a count of papers, which is not what the question asks for. A better query would check for existence.
  - **claude-sonnet-4-5** (CORRECT)

### Item: `8070` (DB: `scholar`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** PARTIALLY_CORRECT
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts papers per author for venue='chi' and orders by count desc, but doesn’t restrict to the single most prolific author (missing LIMIT 1) and returns authorId not authorName.
  - **gemini-3.1-pro-preview** (INCORRECT): The query fails to return the author's name (only returns authorid) and is missing a LIMIT 1 clause to return only the most prolific author.
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `8074` (DB: `scholar`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** PARTIALLY_CORRECT
  - **gpt-5.2** (PARTIALLY_CORRECT): Finds venueIds of papers linked to dataset 'ImageNet', but returns only IDs and doesn’t join venue to output conference (venue) names as asked.
  - **gemini-3.1-pro-preview** (INCORRECT): The query returns venue IDs instead of conference names. It should join with the venue table and select venueName.
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `8082` (DB: `scholar`)

- **Weighted Score:** 0.375
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** PARTIALLY_CORRECT
  - **gpt-5.2** (PARTIALLY_CORRECT): Finds venueId(s) of papers tagged with keyphrase 'Trophic Cascade', but doesn’t return the venue name (no join to venue table), which is likely what 'venue' asks for.
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (INCORRECT): The query returns venueId instead of venueName. Additionally, it searches for 'Trophic Cascade' as a keyphrase rather than a paper title, which may not match the user's intent.
  - **claude-sonnet-4-5** (INCORRECT): Query returns venueId instead of venueName. Missing join to venue table to get the actual venue name that answers the question.

### Item: `8376` (DB: `academic`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 0 CORRECT, 2 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** INCORRECT
  - **gpt-5.2** (PARTIALLY_CORRECT): Query finds coauthors on papers with H. V. Jagadish after 2000, but may include Jagadish himself and can return duplicate author names (missing t2.aid<>t1.aid and DISTINCT).
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Missing DISTINCT to handle authors who cooperated on multiple papers, and fails to exclude 'H. V. Jagadish' himself from the results.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly includes 'H. V. Jagadish' in the list of his own collaborators. It should filter him out from the final result. The query also fails to return distinct authors.
  - **claude-sonnet-4-5** (INCORRECT): Query includes H. V. Jagadish himself in results (needs t2.aid != t1.aid to exclude self) and lacks DISTINCT to prevent duplicate co-authors across multiple papers.

### Item: `8391` (DB: `academic`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** INCORRECT
  - **gpt-5.2** (PARTIALLY_CORRECT): Counts DISTINCT publication titles and groups by conference name; should count distinct papers (pid) and group by conference id. Same-title papers or duplicate conference names could miscount.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly counts the number of distinct paper titles (`COUNT(DISTINCT t3.title)`). To correctly count the number of papers, it should count the distinct publication IDs (`COUNT(DISTINCT t3.pid)`).
  - **claude-sonnet-4-5** (CORRECT)

### Item: `8471` (DB: `imdb`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 2 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** PARTIALLY_CORRECT
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Returns movie titles tagged with keyword exactly 'nuclear weapons', but may output duplicates if multiple tag rows exist per movie; DISTINCT may be needed.
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT - the same movie could be tagged with 'nuclear weapons' multiple times (tags.id is PK, not msid+kid), resulting in duplicate titles.

### Item: `8633` (DB: `restaurants`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 2 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** CORRECT
  - **gpt-5.2** (PARTIALLY_CORRECT): Returns Arabic restaurants in Mountain View with rating>2.5, but 'good' threshold is arbitrary and output isn’t full location (only house_number, missing street/address details).
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): The query selects house_number but misses street_name, which is necessary to provide a complete address for 'where'.
  - **claude-sonnet-4-5** (CORRECT)

## 🚫 Majority UNANSWERABLE

*No majority UNANSWERABLE queries found.*
