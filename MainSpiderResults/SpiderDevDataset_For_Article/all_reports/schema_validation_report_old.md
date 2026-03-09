# Schema Validation Report

**Generated:** 2025-11-11 17:05:19

## Executive Summary

**Databases:** 20 · **Clean:** 13 (65.0%) · **Fatal Errors:** 0 · **Errors:** 5 · **Warnings:** 2

**Tables scanned:** 80 · **Empty tables:** 0 · **Invalid FKs:** 7

**Total warnings:** 3 · **DBs with FK data violations:** 3

**Empty Table Analysis:** 0 used in queries · 0 unused

**Top issue:** fk_type_mismatch (5)

## ❌ Databases with Errors (5)

| Database | Tables | Non-empty | Errors | Warnings | FK Violations |
|----------|--------|-----------|--------|----------|---------------|
| car_1 | 6 | 6/6 (100%) | 2 | 1 | 2 |
| concert_singer | 4 | 4/4 (100%) | 2 | 0 | 0 |
| employee_hire_evaluation | 4 | 4/4 (100%) | 1 | 0 | 0 |
| museum_visit | 3 | 3/3 (100%) | 1 | 0 | 0 |
| voter_1 | 3 | 3/3 (100%) | 1 | 0 | 0 |

## ⚠️ Databases with Warnings Only (2)

| Database | Tables | Non-empty | Warnings | FK Violations |
|----------|--------|-----------|----------|---------------|
| flight_2 | 3 | 3/3 (100%) | 1 | 2400 |
| wta_1 | 3 | 3/3 (100%) | 1 | 1 |

## ✅ Clean Databases (13)

| Database | Tables | Non-empty | FK Violations |
|----------|--------|-----------|---------------|
| battle_death | 3 | 3/3 (100%) | 0 |
| course_teach | 3 | 3/3 (100%) | 0 |
| cre_Doc_Template_Mgt | 4 | 4/4 (100%) | 0 |
| … | … | … | … |

---

## Detailed Database Reports

### Database: car_1

**Status:** ❌ 2 errors, 1 warning · **Non-empty:** 6/6 (100%) · **FK:** N/A · **IC:** 2 violations

**Errors**

⛔ Foreign key column types differ: car_makers.Country (TEXT→TEXT) vs countries.CountryId (INTEGER→INTEGER)
⛔ Table car_names FK ['Model'] references model_list['Model'] which is not PK/UNIQUE.

**Warnings**

⚠️ Found 2 FK data violation(s)

**Tables (summary)**

Total: 6 · Non-empty: 6 · Empty: 0


### Database: concert_singer

**Status:** ❌ 2 errors · **Non-empty:** 4/4 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Foreign key column types differ: concert.Stadium_ID (TEXT→TEXT) vs stadium.Stadium_ID (INT→INTEGER)
⛔ Foreign key column types differ: singer_in_concert.Singer_ID (TEXT→TEXT) vs singer.Singer_ID (INT→INTEGER)

**Tables (summary)**

Total: 4 · Non-empty: 4 · Empty: 0


### Database: employee_hire_evaluation

**Status:** ❌ 1 error · **Non-empty:** 4/4 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Foreign key column types differ: evaluation.Employee_ID (TEXT→TEXT) vs employee.Employee_ID (INT→INTEGER)

**Tables (summary)**

Total: 4 · Non-empty: 4 · Empty: 0


### Database: museum_visit

**Status:** ❌ 1 error · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Foreign key column types differ: visit.visitor_ID (TEXT→TEXT) vs visitor.ID (INT→INTEGER)

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: voter_1

**Status:** ❌ 1 error · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table VOTES FK ['state'] references AREA_CODE_STATE['state'] which is not PK/UNIQUE.

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: flight_2

**Status:** ⚠️ 1 warning · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** 2400 violations

**Warnings**

⚠️ Found 2400 FK data violation(s)

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: wta_1

**Status:** ⚠️ 1 warning · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** 1 violations

**Warnings**

⚠️ Found 1 FK data violation(s)

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0

