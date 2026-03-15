# Spider/Dev: missing group intersect (mixed or incorrect)

- **Total intersected item_id:** 59
- **Source:** `llm_judge_full_mode_mixed_detailed.md`
- **Filter:** only `mixed` or `incorrect` that intersect with provided missing group

## Mixed (39)
23, 24, 35, 36, 37, 82, 83, 90, 91, 94, 95, 111, 176, 177, 232, 233, 278, 284, 337, 370, 371, 375, 420, 421, 464, 517, 530, 531, 540, 541, 563, 574, 575, 643, 862, 905, 906, 909, 939

## Incorrect (20)
17, 34, 336, 465, 501, 526, 527, 534, 535, 642, 817, 818, 885, 886, 907, 908, 910, 938, 943, 944

## Union (59)
17, 23, 24, 34, 35, 36, 37, 82, 83, 90, 91, 94, 95, 111, 176, 177, 232, 233, 278, 284, 336, 337, 370, 371, 375, 420, 421, 464, 465, 501, 517, 526, 527, 530, 531, 534, 535, 540, 541, 563, 574, 575, 642, 643, 817, 818, 862, 885, 886, 905, 906, 907, 908, 909, 910, 938, 939, 943, 944

---
===============================
===============================
===============================

MISSING GROUP Antipatterns in SPIDER/DEV
===============================
===============================
===============================

Id: 336 (Here we select random query)
## Previous content
{"question":"What the smallest version number and its template type code?","db_id":"cre_Doc_Template_Mgt","query":"SELECT min(Version_Number) ,  template_type_code FROM Templates"}
what is wrong
==
In SQLite this query is valid because bare columns are allowed in aggregate queries. When a query contains a single MIN() or MAX(), SQLite returns the values of bare columns from the row that contains the minimum or maximum value. However, if multiple rows share the same minimum value, the value of template_type_code is chosen arbitrarily from one of those rows, so the result is not deterministic.
==============================================================================================================================
Id: 17. This is completly wrong
{"question":"What is the maximum capacity and the average of all stadiums ?","db_id":"concert_singer","query":"select max(capacity), average from stadium"}
================================================================================================================================
Id: 34. It seems this completly correct query.
SELECT T2.concert_name, T2.theme, COUNT(*)
FROM singer_in_concert AS T1
JOIN concert AS T2 ON T1.concert_id = T2.concert_id
GROUP BY T2.concert_id
=============================================================================================================================

Id: 465 (wrong query, random column is selected)
{"question":"What is the name of the winner who has won the most matches, and how many rank points does this player have?","db_id":"wta_1","query":"SELECT winner_name ,  winner_rank_points FROM matches GROUP BY winner_name ORDER BY count(*) DESC LIMIT 1"}
LLM:
- **Weighted Score:** 0.000
- **Voter Breakdown:** 0 CORRECT, 0 PARTIALLY_CORRECT, 2 INCORRECT, 0 UNANSWERABLE (out of 2 voters)
- **Voter Details:**
  - **gemini-2.5-pro** (INCORRECT): The query correctly finds the winner with the most wins, but it returns the `winner_rank_points` from an arbitrary match. A player's rank points can change, so this non-deterministic result does not accurately answer how many points the player has.
  - **gpt-5** (INCORRECT): Counts wins by winner_name and selects a non-aggregated winner_rank_points arbitrarily. Should group by winner_id and get a consistent points value (e.g., from rankings latest date or aggregate).

Problem with the Query
SELECT winner_name, winner_rank_points
FROM matches
GROUP BY winner_name
ORDER BY COUNT(*) DESC
LIMIT 1;

The query groups rows by winner_name but also selects winner_rank_points, which is not aggregated and not included in GROUP BY. This makes winner_rank_points a bare column.

In SQLite, this is allowed, but the value of winner_rank_points is taken from an arbitrary row in the group.

Example

If the table contains:

winner_name	winner_rank_points
Serena	5000
Serena	5200
Serena	5100

After grouping:

Serena → {5000, 5200, 5100}

SQLite may return any of these values, so the result is not deterministic.

When the Query Works

The query works correctly only if winner_rank_points is the same for every row of a player, meaning:

winner_name → winner_rank_points

Otherwise, the returned rank points may be incorrect.
SAFER Alternative:

SELECT winner_name, winner_rank_points
FROM matches
WHERE winner_name = (
    SELECT winner_name
    FROM matches
    GROUP BY winner_name
    ORDER BY COUNT(*) DESC
    LIMIT 1
)
ORDER BY tourney_date DESC
LIMIT 1;==============================================================================================================================
Id: 534 (I don't know it inlcude in article this example. I think no....)
{"question":"Who are enrolled in 2 degree programs in one semester? List the first name, middle name and last name and the id.","db_id":"student_transcripts_tracking","query":"SELECT T1.first_name ,  T1.middle_name ,  T1.last_name ,  T1.student_id FROM Students AS T1 JOIN Student_Enrolment AS T2 ON T1.student_id  =  T2.student_id GROUP BY T1.student_id HAVING count(*)  =  2"}

Correct query should be
SELECT s.first_name, s.middle_name, s.last_name, s.student_id
FROM Students s
JOIN Student_Enrolment se ON s.student_id = se.student_id
GROUP BY s.student_id, s.first_name, s.middle_name, s.last_name, se.semester_id
HAVING COUNT(DISTINCT se.degree_program_id) = 2
=======================================================================================
Id 642 (Incorrect - here it expect to select all ids of channel but instead select just one from the channel)
{"question":"find id of the tv channels that from the countries where have more than two tv channels.","db_id":"tvshow","query":"SELECT id FROM tv_channel GROUP BY country HAVING count(*)  >  2"}

Same problem as before — id is not aggregated and not in the GROUP BY. So it returns an arbitrary single id per qualifying country, not all channel ids from those countries.

query_correct = """
SELECT id
FROM TV_Channel
WHERE Country IN (
    SELECT Country
    FROM TV_Channel
    GROUP BY Country
    HAVING COUNT(*) > 2
)
"""

==========================================================
==========================================================
==========================================================
BIRD TRAIN NULL comparison:
Id 8443:
{"db_id": "mondial_geo", "question": "How many businesses were founded after 1960 in a nation that wasn't independent?", "evidence": "Established means founded; Country means nation; Organization means businesses", "SQL": "SELECT COUNT(T3.Name) FROM country AS T1 INNER JOIN politics AS T2 ON T1.Code = T2.Country INNER JOIN organization AS T3 ON T3.Country = T2.Country WHERE T2.Independence = NULL AND STRFTIME('%Y', T3.Established) > '1960'"}
==========================================
==========================================
==========================================

SPIDER TRAIN Cartesian Product:
{"question":"Which engineer has visited the most times? Show the engineer id, first name and last name.","db_id":"assets_maintenance","query":"SELECT T1.engineer_id ,  T1.first_name ,  T1.last_name FROM Maintenance_Engineers AS T1 JOIN Engineer_Visits AS T2 GROUP BY T1.engineer_id ORDER BY count(*) DESC LIMIT 1"}

Because there is no ON condition, SQL joins every row from:
Maintenance_Engineers
with every row from Engineer_Visits
This creates a Cartesian product, so the counts will be incorrect.

==========================================
==========================================
==========================================
==========================================