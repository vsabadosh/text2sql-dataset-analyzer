# LLM Judge Semantic Validation Report

**Generated:** 2026-02-28 18:33:28

## Summary

- **Total Queries Evaluated:** 34
- **Majority CORRECT:** 17 (50.0%)
    *of which Unanimous CORRECT: 14 (41.2%)*
- **Majority PARTIALLY_CORRECT:** 3 (8.8%)
    *of which Unanimous PARTIALLY_CORRECT: 2 (5.9%)*
- **Majority INCORRECT:** 7 (20.6%)
    *of which Unanimous INCORRECT: 5 (14.7%)*
- **Mixed (No Majority):** 7 (20.6%)
    *(Mixed results have no consensus by definition)*

### Mixed Consensus Breakdown

| claude-sonnet-4-5 | gemini-2.5-pro | gemini-3.1-pro-preview | gpt-5.2 | Count |
|-------|-------|-------|-------|-------|
| CORRECT | INCORRECT | CORRECT | INCORRECT | 2 |
| PARTIALLY_CORRECT | CORRECT | CORRECT | PARTIALLY_CORRECT | 2 |
| CORRECT | CORRECT | PARTIALLY_CORRECT | INCORRECT | 1 |
| CORRECT | INCORRECT | CORRECT | PARTIALLY_CORRECT | 1 |
| INCORRECT | INCORRECT | CORRECT | PARTIALLY_CORRECT | 1 |
- **Majority UNANSWERABLE:** 0 (0.0%)
    *of which Unanimous UNANSWERABLE: 0 (0.0%)*

---

## ✅ Majority CORRECT (Non-Unanimous)

**Found 3 queries where majority (but not all) voters said CORRECT** (showing ALL)

These queries are likely correct but had some voter disagreement.

### Item: `833` (DB: `address_1`)

- **Weighted Score:** 0.875
- **Voter Breakdown:** 3 CORRECT, 1 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Groups by city1_code and sums outgoing distances, but doesn’t include all cities (missing those not in Direct_distance as city1) and ignores distances where a city appears only as city2.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `856` (DB: `boat_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 3 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT). There is ambiguity in the English phrasing, so the query writer's interpretation using MIN is defensible, just less likely to be the intended meaning. 
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (INCORRECT): Uses MIN(age) for rating>7, returning sailors older than the youngest high-rated sailor. 'Older than any sailor with rating>7' implies older than all such sailors (use MAX/ALL).
  - **claude-sonnet-4-5** (CORRECT)

### Item: `1236` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 3 CORRECT, 0 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT).
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gpt-5.2** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (INCORRECT): Query selects 'medium' column but question asks 'on what mediums' which refers to the painting surface stored in 'mediumOn' column (canvas, panel, not oil, crayon).

## ⚡ Majority PARTIALLY_CORRECT

**Found 3 queries where majority of voters said PARTIALLY_CORRECT** (showing up to 50)

These queries are mostly correct but may have minor issues.

### Item: `71` (DB: `e_commerce`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 4 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT) 
  - **gpt-5.2** (PARTIALLY_CORRECT): Joins correctly to shipped order items, but may return duplicate product rows if multiple shipped items/shipments share the same product; DISTINCT may be needed for unique names/colors.
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Missing DISTINCT. The query may return duplicate product names and colors if the same product is ordered and shipped multiple times.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query correctly identifies products that have been shipped, but it may return duplicate product name and color pairs if the same product is part of multiple shipments. Using SELECT DISTINCT would provide a unique list.
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT when duplicates possible - same product name/color can appear multiple times if multiple shipped order items have the same product.

### Item: `917` (DB: `boat_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 0 CORRECT, 4 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Query finds sailors who reserved a boat named 'Melon', but may return duplicate sailor names if they reserved it multiple times; DISTINCT may be needed.
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Missing DISTINCT. A sailor could reserve the same boat multiple times on different days, which would result in duplicate names in the output.
  - **gemini-2.5-pro** (PARTIALLY_CORRECT): The query is missing a DISTINCT keyword. If a sailor reserves the boat 'Melon' on multiple occasions, their name will appear multiple times in the result set.
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT when duplicates possible - a sailor who reserved Melon multiple times will appear multiple times in results

### Item: `1466` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 1 CORRECT, 3 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Logic matches owner_user_id=user_id and user address=property address, but may return duplicate name rows if a user owns multiple properties at their address; DISTINCT likely needed.
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Missing DISTINCT. If a user owns multiple properties at their residential address, their name will appear multiple times in the results.
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT; users could appear multiple times if they own multiple properties at their residential address.

## ❌ Majority INCORRECT

**Found 7 queries where majority of voters said INCORRECT** (showing ALL)

These queries are likely semantically incorrect and need review.

### Item: `388` (DB: `government_shift`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT): 
  - **gpt-5.2** (INCORRECT): Missing join condition between Customer_Interactions and Integration_Platform (should join on Customer_Interaction_ID). Current query returns customers with any interaction if any failed integration exists.
  - **gemini-3.1-pro-preview** (INCORRECT): Missing JOIN condition between customer_interactions and integration_platform. This results in a cross join that fails to link the specific customer to the failed integration platform.
  - **gemini-2.5-pro** (INCORRECT): The query is missing a JOIN condition between the `customer_interactions` and `integration_platform` tables. This results in a cross join, which will produce incorrect results.
  - **claude-sonnet-4-5** (INCORRECT): Missing JOIN condition between customer_interactions (t2) and integration_platform (t3). Should specify: ON t2.customer_interaction_id = t3.customer_interaction_id

### Item: `708` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Query returns owners of the related documents owned by Braeden (i.e., 'Braeden'), not owners of documents that are related to Braeden’s documents. Needs joining Document_Objects for Document_Object_ID side.
  - **gemini-2.5-pro** (INCORRECT): The query selects the owner of the document that is already filtered to be 'Braeden'. It should select the owner of the other document in the relationship, which requires another join to the Document_Objects table.
  - **gemini-3.1-pro-preview** (INCORRECT): The query selects the OWNER from the same table alias (T2) used in the WHERE clause (T2.Owner = 'Braeden'), which will only return 'Braeden'. It fails to join Document_Objects a second time.
  - **claude-sonnet-4-5** (INCORRECT): Query filters T2 for Owner='Braeden' and selects T2.OWNER, returning only 'Braeden'. It needs to join Document_Objects again on Document_Object_ID to get owners of the related documents.

### Item: `728` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Query wrongly filters to Collection_Name = "Best", so it cannot find the collection with the most documents overall. It should aggregate all collections and pick the max.
  - **gemini-3.1-pro-preview** (INCORRECT): The query incorrectly filters by Collection_Name = "Best", which is not requested in the natural language question.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly filters for collections named 'Best' with the clause `WHERE T1.Collection_Name = "Best"`, but the question asks to find the collection with the most documents among all collections.
  - **claude-sonnet-4-5** (INCORRECT): WHERE clause incorrectly filters for Collection_Name = 'Best', but question asks for collection with most documents across all collections, not just those named 'Best'.

### Item: `737` (DB: `cre_Doc_and_collections`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Query wrongly self-joins Collection_Subset_Members, requiring the related collection to appear as Collection_ID in another row; it can omit valid related collections. Should join Collections on T1.Related_Collection_ID.
  - **gemini-3.1-pro-preview** (INCORRECT): The query unnecessarily joins Collection_Subset_Members to itself (T2), which incorrectly filters out related collections that do not have their own related collections.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly self-joins `Collection_Subset_Members` on `T1.Related_Collection_ID = T2.Collection_ID`. This wrongly constrains the results to only those collections that are both related to 'Best' and also appear as a primary collection in another relationship, which is not what the question asks for.
  - **claude-sonnet-4-5** (INCORRECT): The T2 join (Collection_Subset_Members) adds an unnecessary filter requiring related collections to also appear as Collection_ID in Collection_Subset_Members, which excludes valid related collections that don't have their own relationships.

### Item: `879` (DB: `boat_1`)

- **Weighted Score:** 0.250
- **Voter Breakdown:** 1 CORRECT, 0 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Uses MIN(rating) for Luis; "higher than any Luis" requires rating > MAX(rating) of all sailors named Luis (greater than all Luis ratings), not just greater than the lowest.
  - **gemini-2.5-pro** (INCORRECT): The phrase 'higher than any sailor named Luis' implies the rating must be greater than the rating of all sailors named Luis. The query incorrectly compares against the minimum rating, not the maximum.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (INCORRECT): Query uses min(rating) but 'higher than any sailor named Luis' means higher than all sailors named Luis, requiring max(rating) or > ALL instead.

### Item: `1230` (DB: `art_1`)

- **Weighted Score:** 0.125
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (PARTIALLY_CORRECT): Finds the longest-lived artist only among artists who have paintings; if the longest-lived artist has 0 paintings, it returns a different artist’s count (and ties are arbitrary).
  - **gemini-3.1-pro-preview** (INCORRECT): The INNER JOIN excludes artists with 0 paintings before determining the longest-lived artist. It should use a LEFT JOIN or subquery to evaluate all artists.
  - **gemini-2.5-pro** (INCORRECT): The query first joins Artists and Paintings, which filters out any artist who does not have a painting. It then finds the longest-lived artist from this reduced set, not from all artists as the question requires.
  - **claude-sonnet-4-5** (INCORRECT): INNER JOIN excludes artists without paintings. If longest-lived artist has no paintings, query returns wrong artist's count. Should identify longest-lived artist first.

### Item: `1551` (DB: `bakery_1`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT):
  - **gpt-5.2** (INCORRECT): WHERE clause precedence makes it return all Cookies regardless of price (food='Cookie' OR (food='Cake' AND price...)). It should apply the price filter to both foods.
  - **gemini-3.1-pro-preview** (INCORRECT): Missing parentheses around the OR condition. AND has higher precedence, so the query returns all Cookies regardless of price, instead of applying the price filter to both Cookies and Cakes.
  - **gemini-2.5-pro** (INCORRECT): The WHERE clause is logically incorrect due to operator precedence. It selects all cookies regardless of price, plus cakes priced between 3 and 7. Parentheses are needed to group the OR condition.
  - **claude-sonnet-4-5** (INCORRECT): Operator precedence error: query returns all Cookies regardless of price. Should be (food='Cookie' OR food='Cake') AND price BETWEEN 3 AND 7 to apply price filter to both.

## ⚠️ Mixed (No Majority)

**Found 7 queries with mixed voter verdicts (no majority)** (showing ALL)

These queries have no clear majority verdict and require manual review.

### Item: `559` (DB: `book_1`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **gpt-5.2** (INCORRECT): Uses EXCEPT on client Name, not IdClient. If two different clients share a name and one ordered, that name is excluded even if the other client never ordered.
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Using EXCEPT on the 'name' column may incorrectly exclude a client who hasn't made an order if they share the same name with a client who has.
  - **claude-sonnet-4-5** (CORRECT)

### Item: `1241` (DB: `art_1`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 2 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Query matches artists with paintings from 1884 on canvas, but may return duplicate birthYear rows (or multiple artists) if multiple qualifying paintings exist; DISTINCT or other disambiguation may be needed.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT on birthYear; if an artist created multiple paintings in 1884 on canvas, their birth year would be returned multiple times

### Item: `1296` (DB: `art_1`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 2 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Returns only deathYear, not each artist (no name/ID). Also inner join omits artists with 0 paintings, though they satisfy “less than 4 paintings”.
  - **gemini-2.5-pro** (INCORRECT): The query uses an INNER JOIN, which excludes artists who have created zero paintings. Artists with zero paintings satisfy the condition 'less than 4 paintings' and should be included in the result.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `1319` (DB: `car_road_race`)

- **Weighted Score:** 0.750
- **Voter Breakdown:** 2 CORRECT, 2 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Query filters races where Pole_Position is not 'Junior Strous' and returns Winning_driver, but may return duplicates if a driver won multiple such races; DISTINCT may be needed.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (CORRECT)
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT when duplicates possible if same driver won multiple races with pole position != 'Junior Strous'

### Item: `1469` (DB: `real_estate_rentals`)

- **Weighted Score:** 0.375
- **Voter Breakdown:** 1 CORRECT, 1 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): The searches part uses an INNER JOIN to User_Searches, so users with 0 searches are excluded, though “at most twice” should include 0–2 searches.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly uses an INNER JOIN on the User_Searches table. This excludes users who have 0 searches, but the condition 'at most twice' should include users with 0, 1, or 2 searches.
  - **claude-sonnet-4-5** (INCORRECT): INNER JOIN with User_Searches excludes users with 0 searches. 'At most twice' should include 0, 1, or 2 searches. Should use LEFT JOIN to include users who never searched.

### Item: `1617` (DB: `car_racing`)

- **Weighted Score:** 0.500
- **Voter Breakdown:** 2 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Points is a TEXT column; MAX(Points) may return the lexicographically largest string, not the highest numeric points. Should CAST Points to INTEGER/REAL before MAX.
  - **gemini-2.5-pro** (INCORRECT): The query applies MAX() to the 'Points' column which is of TEXT type. This will result in a lexicographical comparison (e.g., '9' > '185'), not a numerical one, leading to an incorrect maximum value.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

### Item: `1994` (DB: `book_press`)

- **Weighted Score:** 0.625
- **Voter Breakdown:** 2 CORRECT, 1 PARTIALLY_CORRECT, 1 INCORRECT, 0 UNANSWERABLE (out of 4 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (PARTIALLY_CORRECT): Sale_Amount is a TEXT column; ORDER BY sale_amount DESC may sort lexicographically (e.g., '9' > '100'), so top 5 by numeric sales may be wrong. Should CAST to numeric.
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly sorts the 'sale_amount' column lexicographically because its data type is TEXT. To find the 'best sale books', it should be cast to a numeric type for proper numerical sorting.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (CORRECT)

## 🚫 Majority UNANSWERABLE

*No majority UNANSWERABLE queries found.*
