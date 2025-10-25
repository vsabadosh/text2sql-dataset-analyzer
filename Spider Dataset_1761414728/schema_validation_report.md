# Schema Validation Report

**Generated:** 2025-10-25 19:52:59

## Executive Summary

**Databases:** 146 · **Clean:** 131 (89.7%) · **Fatal Errors:** 0 · **Errors:** 9 · **Warnings:** 6

**Tables scanned:** 793 · **Invalid FKs:** 46

**Top issue:** fk_target_not_key (41)

## ❌ Databases with Schema Errors (9)

| Database | Tables | Non-empty | Errors |
|----------|--------|-----------|--------|
| baseball_1 | 26 | 26/26 (100%) | 20 |
| dorm_1 | 5 | 5/5 (100%) | 3 |
| imdb | 16 | 0/16 (0%) | 7 |
| loan_1 | 3 | 3/3 (100%) | 1 |
| restaurants | 3 | 0/3 (0%) | 1 |
| soccer_1 | 6 | 6/6 (100%) | 4 |
| store_product | 5 | 5/5 (100%) | 1 |
| wine_1 | 3 | 3/3 (100%) | 2 |
| yelp | 7 | 0/7 (0%) | 7 |

## ⚠️ Databases with Warnings Only (6)

| Database | Tables | Non-empty | Warnings |
|----------|--------|-----------|----------|
| allergy_1 | 3 | 3/3 (100%) | 1 |
| college_1 | 7 | 7/7 (100%) | 1 |
| flight_4 | 3 | 3/3 (100%) | 1 |
| hospital_1 | 15 | 15/15 (100%) | 1 |
| hr_1 | 7 | 7/7 (100%) | 1 |
| sakila_1 | 16 | 12/16 (75%) | 1 |

## ✅ Clean Databases (131)

| Database | Tables | Non-empty |
|----------|--------|-----------|
| academic | 15 | 0/15 (0%) |
| activity_1 | 5 | 5/5 (100%) |
| aircraft | 5 | 5/5 (100%) |
| … | … | … |

---

## Detailed Database Reports

### Database: baseball_1

**Status:** ❌ 20 errors · **Non-empty:** 26/26 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table all_star FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table appearances FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table appearances FK ['team_id'] references team['team_id'] which is not PK/UNIQUE.
⛔ Table batting FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table batting_postseason FK ['team_id'] references team['team_id'] which is not PK/UNIQUE.
⛔ Table batting_postseason FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table fielding FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table fielding_outfield FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table fielding_postseason has FK referencing non-existing column(s) ['team_id'] on parent 'player'.
⛔ Table fielding_postseason FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table hall_of_fame FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table home_game FK ['park_id'] references park['park_id'] which is not PK/UNIQUE.
⛔ Table home_game FK ['team_id'] references team['team_id'] which is not PK/UNIQUE.
⛔ Table manager FK ['team_id'] references team['team_id'] which is not PK/UNIQUE.
⛔ Table manager_award FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table manager_half FK ['team_id'] references team['team_id'] which is not PK/UNIQUE.
⛔ Table player_award FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table player_award_vote FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.
⛔ Table player_college FK ['college_id'] references college['college_id'] which is not PK/UNIQUE.
⛔ Table player_college FK ['player_id'] references player['player_id'] which is not PK/UNIQUE.

**Tables (summary)**

Total: 26 · Non-empty: 26 · Empty: 0


### Database: dorm_1

**Status:** ❌ 3 errors · **Non-empty:** 5/5 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table Has_amenity FK ['amenid'] references Dorm_amenity['amenid'] which is not PK/UNIQUE.
⛔ Table Has_amenity FK ['dormid'] references Dorm['dormid'] which is not PK/UNIQUE.
⛔ Table Lives_in FK ['dormid'] references Dorm['dormid'] which is not PK/UNIQUE.

**Tables (summary)**

Total: 5 · Non-empty: 5 · Empty: 0


### Database: imdb

**Status:** ❌ 7 errors · **Non-empty:** 0/16 (0%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table cast FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table classification FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table directed_by FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table made_by FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table tags has FK referencing non-existing column(s) ['kid'] on parent 'keyword'.
⛔ Table tags FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table written_by FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.

**Tables (summary)**

Total: 16 · Non-empty: 0 · Empty: 16


### Database: loan_1

**Status:** ❌ 1 error · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table loan has FK referencing non-existing column(s) ['Cust_ID'] on parent 'customer'.

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: restaurants

**Status:** ❌ 1 error · **Non-empty:** 0/3 (0%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table LOCATION has FK referencing non-existing column(s) ['RESTAURANT_ID'] on parent 'RESTAURANT'.

**Tables (summary)**

Total: 3 · Non-empty: 0 · Empty: 3


### Database: soccer_1

**Status:** ❌ 4 errors · **Non-empty:** 6/6 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table Player_Attributes FK ['player_api_id'] references Player['player_api_id'] which is not PK/UNIQUE.
⛔ Table Player_Attributes FK ['player_fifa_api_id'] references Player['player_fifa_api_id'] which is not PK/UNIQUE.
⛔ Table Team_Attributes FK ['team_api_id'] references Team['team_api_id'] which is not PK/UNIQUE.
⛔ Table Team_Attributes FK ['team_fifa_api_id'] references Team['team_fifa_api_id'] which is not PK/UNIQUE.

**Tables (summary)**

Total: 6 · Non-empty: 6 · Empty: 0


### Database: store_product

**Status:** ❌ 1 error · **Non-empty:** 5/5 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table store_product has FK referencing non-existing column(s) ['Product_ID'] on parent 'product'.

**Tables (summary)**

Total: 5 · Non-empty: 5 · Empty: 0


### Database: wine_1

**Status:** ❌ 2 errors · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table wine FK ['Appelation'] references appellations['Appelation'] which is not PK/UNIQUE.
⛔ Table wine FK ['Grape'] references grapes['Grape'] which is not PK/UNIQUE.

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: yelp

**Status:** ❌ 7 errors · **Non-empty:** 0/7 (0%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table category FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.
⛔ Table checkin FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.
⛔ Table neighbourhood FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.
⛔ Table review FK ['user_id'] references user['user_id'] which is not PK/UNIQUE.
⛔ Table review FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.
⛔ Table tip FK ['user_id'] references user['user_id'] which is not PK/UNIQUE.
⛔ Table tip FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.

**Tables (summary)**

Total: 7 · Non-empty: 0 · Empty: 7


### Database: allergy_1

**Status:** ⚠️ 1 warning · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** 1 violations

**Warnings**

⚠️ Found 1 FK data violation(s)

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: college_1

**Status:** ⚠️ 1 warning · **Non-empty:** 7/7 (100%) · **FK:** N/A · **IC:** 2 violations

**Warnings**

⚠️ Found 2 FK data violation(s)

**Tables (summary)**

Total: 7 · Non-empty: 7 · Empty: 0


### Database: flight_4

**Status:** ⚠️ 1 warning · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** 1240 violations

**Warnings**

⚠️ Found 1240 FK data violation(s)

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: hospital_1

**Status:** ⚠️ 1 warning · **Non-empty:** 15/15 (100%) · **FK:** N/A · **IC:** 1 violations

**Warnings**

⚠️ Found 1 FK data violation(s)

**Tables (summary)**

Total: 15 · Non-empty: 15 · Empty: 0


### Database: hr_1

**Status:** ⚠️ 1 warning · **Non-empty:** 7/7 (100%) · **FK:** N/A · **IC:** 6 violations

**Warnings**

⚠️ Found 6 FK data violation(s)

**Tables (summary)**

Total: 7 · Non-empty: 7 · Empty: 0


### Database: sakila_1

**Status:** ⚠️ 1 warning · **Non-empty:** 12/16 (75%) · **FK:** N/A · **IC:** 38273 violations

**Warnings**

⚠️ Found 38273 FK data violation(s)

**Tables (summary)**

Total: 16 · Non-empty: 12 · Empty: 4

