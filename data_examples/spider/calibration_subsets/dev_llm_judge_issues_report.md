# LLM Judge Semantic Validation Report

**Generated:** 2026-02-28 17:10:07

## Summary

- **Total Queries Evaluated:** 10
- **Majority CORRECT:** 5 (50.0%)
    *of which Unanimous CORRECT: 5 (50.0%)*
- **Majority PARTIALLY_CORRECT:** 1 (10.0%)
    *of which Unanimous PARTIALLY_CORRECT: 0 (0.0%)*
- **Majority INCORRECT:** 4 (40.0%)
    *of which Unanimous INCORRECT: 1 (10.0%)*
- **Mixed (No Majority):** 0 (0.0%)
    *(Mixed results have no consensus by definition)*
- **Majority UNANSWERABLE:** 0 (0.0%)
    *of which Unanimous UNANSWERABLE: 0 (0.0%)*

---

## ✅ Majority CORRECT (Non-Unanimous)

*No non-unanimous majority CORRECT queries found.*

## ⚡ Majority PARTIALLY_CORRECT

**Found 1 queries where majority of voters said PARTIALLY_CORRECT** (showing up to 50)

These queries are mostly correct but may have minor issues.

### Item: `847` (DB: `orchestra`)

- **Weighted Score:** 0.600
- **Voter Breakdown:** 1 CORRECT, 4 PARTIALLY_CORRECT, 0 INCORRECT, 0 UNANSWERABLE (out of 5 voters)
- **Voter Details:**
  - **HUMAN** (PARTIALLY_CORRECT) 
  - **gpt-5.2** (PARTIALLY_CORRECT): Query finds conductors linked to orchestras founded after 2008, but may return duplicate names if a conductor has multiple qualifying orchestras; DISTINCT may be needed.
  - **claude-opus-4-6** (PARTIALLY_CORRECT): Missing DISTINCT: if a conductor conducted multiple orchestras founded after 2008, their name would appear multiple times.
  - **gemini-2.5-pro** (CORRECT)
  - **gemini-3.1-pro-preview** (PARTIALLY_CORRECT): Missing DISTINCT in the SELECT clause. A conductor could have conducted multiple orchestras founded after 2008, which would result in duplicate names in the output.
  - **claude-sonnet-4-5** (PARTIALLY_CORRECT): Missing DISTINCT - conductor names may duplicate if they conducted multiple orchestras founded after 2008

## ❌ Majority INCORRECT

**Found 4 queries where majority of voters said INCORRECT** (showing ALL)

These queries are likely semantically incorrect and need review.

### Item: `176` (DB: `car_1`)

- **Weighted Score:** 0.400
- **Voter Breakdown:** 2 CORRECT, 0 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 5 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **claude-opus-4-6** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query incorrectly interprets the condition 'more than 3 car makers' as 'more than 3 cars'. It counts records from the `car_names` table, which represents cars, not car makers.
  - **gpt-5.2** (INCORRECT): SQL finds makers with >=2 entries in model_list AND >3 rows in car_names (cars). The question’s second condition is about 'more than 3 car makers', not number of cars/car_names.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (INCORRECT): The question is contradictory: 'more than 3 car makers' makes no logical sense when asking 'which car makers'. Even interpreting it as 'cars', the SQL counts car_names, which may not match intended meaning.

### Item: `817` (DB: `world_1`)

- **Weighted Score:** 0.400
- **Voter Breakdown:** 2 CORRECT, 0 PARTIALLY_CORRECT, 3 INCORRECT, 0 UNANSWERABLE (out of 5 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT). Even Sqlite allow it but it result is not reliable. if we have multiple. 
  - **gpt-5.2** (INCORRECT): Query groups by CountryCode but selects Language without ensuring it corresponds to the max Percentage; SQLite may return an arbitrary language per country, not the top one.
  - **claude-opus-4-6** (CORRECT)
  - **gemini-2.5-pro** (INCORRECT): The query groups by CountryCode and finds the maximum percentage, but the selected 'LANGUAGE' is not guaranteed to be from the same row as the maximum percentage. It will return an arbitrary language from each group.
  - **gemini-3.1-pro-preview** (CORRECT)
  - **claude-sonnet-4-5** (INCORRECT): LANGUAGE is non-grouped and not correlated with max(Percentage). SQLite returns arbitrary language per country, not necessarily the one with maximum percentage.

### Item: `943` (DB: `dog_kennels`)

- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 5 INCORRECT, 0 UNANSWERABLE (out of 5 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT)
  - **gpt-5.2** (INCORRECT): Counts total treatments per professional (count(*)) instead of distinct treatment types. Should use COUNT(DISTINCT T2.treatment_type_code) >= 2 to match “at least two types”.
  - **claude-opus-4-6** (INCORRECT): The query uses COUNT(*) >= 2 which counts total treatments, not distinct treatment types. It should use COUNT(DISTINCT treatment_type_code) >= 2 to match 'at least two types of treatments'.
  - **gemini-2.5-pro** (INCORRECT): The query counts the total number of treatments per professional using COUNT(*). The question asks for professionals who have performed at least two distinct *types* of treatments, which requires COUNT(DISTINCT T2.treatment_type_code).
  - **claude-sonnet-4-5** (INCORRECT): Query counts total treatments (count(*)) instead of distinct treatment types. Should use COUNT(DISTINCT treatment_type_code) to count different types of treatments performed.
  - **gemini-3.1-pro-preview** (INCORRECT): The query counts the total number of treatments (count(*)) instead of the number of distinct treatment types (count(DISTINCT treatment_type_code)).

### Item: `989` (DB: `dog_kennels`)

- **Weighted Score:** 0.100
- **Voter Breakdown:** 0 CORRECT, 1 PARTIALLY_CORRECT, 4 INCORRECT, 0 UNANSWERABLE (out of 5 voters)
- **Voter Details:**
  - **HUMAN** (INCORRECT) 
  - **gpt-5.2** (INCORRECT): Dogs.age is stored as VARCHAR, so MAX(age) compares lexicographically (e.g., '9' > '10'), which may not return the true oldest age. Should cast to numeric or compute from date_of_birth.
  - **gemini-2.5-pro** (INCORRECT): The `age` column is of type VARCHAR. Applying MAX() on a text column will result in a lexicographical comparison (e.g., '9' > '10'), not a numerical one, leading to an incorrect answer.
  - **claude-opus-4-6** (PARTIALLY_CORRECT): The `age` column is VARCHAR(20), so MAX performs lexicographic comparison, not numeric. For example, '9' > '12' in string order. Should use CAST(age AS INTEGER) or age+0 for correct numeric maximum.
  - **gemini-3.1-pro-preview** (INCORRECT): The 'age' column is VARCHAR, so MAX(age) performs lexicographical string comparison (e.g., '9' > '10'). It must be cast to a numeric type to correctly find the oldest dog.
  - **claude-sonnet-4-5** (INCORRECT): MAX on VARCHAR column performs lexicographic comparison (e.g., '9' > '10'), not numeric comparison needed to find the oldest dog. Should cast age to numeric type.

## ⚠️ Mixed (No Majority)

*No mixed verdict queries found.*

## 🚫 Majority UNANSWERABLE

*No majority UNANSWERABLE queries found.*
