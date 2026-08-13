# Schema Validation Report

**Generated:** 2026-08-13 13:25:32

## Executive Summary

**Databases:** 146 · **Clean:** 110 (75.3%) · **Fatal Errors:** 0 · **Errors:** 15 · **Warnings:** 21

**Tables scanned:** 793 · **Empty tables:** 71 · **Total FKs:** 717 · **Invalid FKs:** 46

**Total warnings:** 41 · **DBs with FK data violations:** 6

**Top issue:** fk_target_not_key (41)

## ❌ Databases with Errors (15)

| Database | Tables | Non-empty | Errors | Warnings | FK Violations |
|----------|--------|-----------|--------|----------|---------------|
| allergy_1 | 3 | 3/3 (100%) | 0 | 0 | 1 |
| baseball_1 | 26 | 26/26 (100%) | 20 | 0 | 0 |
| college_1 | 7 | 7/7 (100%) | 0 | 0 | 2 |
| dorm_1 | 5 | 5/5 (100%) | 3 | 0 | 0 |
| flight_4 | 3 | 3/3 (100%) | 0 | 0 | 1240 |
| hospital_1 | 15 | 15/15 (100%) | 0 | 0 | 1 |
| hr_1 | 7 | 7/7 (100%) | 0 | 0 | 6 |
| imdb | 16 | 0/16 (0%) | 7 | 1 | 0 |
| loan_1 | 3 | 3/3 (100%) | 1 | 1 | 0 |
| restaurants | 3 | 0/3 (0%) | 1 | 1 | 0 |
| sakila_1 | 16 | 12/16 (75%) | 0 | 1 | 38273 |
| soccer_1 | 6 | 6/6 (100%) | 4 | 0 | 0 |
| store_product | 5 | 5/5 (100%) | 1 | 0 | 0 |
| wine_1 | 3 | 3/3 (100%) | 2 | 0 | 0 |
| yelp | 7 | 0/7 (0%) | 7 | 1 | 0 |

## ⚠️ Databases with Warnings Only (21)

| Database | Tables | Non-empty | Warnings | FK Violations |
|----------|--------|-----------|----------|---------------|
| academic | 15 | 0/15 (0%) | 2 | 0 |
| aircraft | 5 | 5/5 (100%) | 2 | 0 |
| architecture | 3 | 3/3 (100%) | 2 | 0 |
| city_record | 4 | 4/4 (100%) | 1 | 0 |
| company_employee | 3 | 3/3 (100%) | 1 | 0 |
| cre_Drama_Workshop_Groups | 18 | 18/18 (100%) | 9 | 0 |
| culture_company | 3 | 3/3 (100%) | 2 | 0 |
| formula_1 | 13 | 11/13 (85%) | 1 | 0 |
| geo | 7 | 0/7 (0%) | 1 | 0 |
| machine_repair | 4 | 4/4 (100%) | 1 | 0 |
| music_2 | 7 | 0/7 (0%) | 1 | 0 |
| party_people | 4 | 4/4 (100%) | 1 | 0 |
| performance_attendance | 3 | 3/3 (100%) | 2 | 0 |
| phone_1 | 3 | 3/3 (100%) | 1 | 0 |
| phone_market | 3 | 3/3 (100%) | 1 | 0 |
| race_track | 2 | 2/2 (100%) | 1 | 0 |
| scholar | 10 | 0/10 (0%) | 1 | 0 |
| school_finance | 3 | 3/3 (100%) | 2 | 0 |
| shop_membership | 4 | 4/4 (100%) | 2 | 0 |
| student_assessment | 9 | 9/9 (100%) | 1 | 0 |
| wrestler | 2 | 2/2 (100%) | 1 | 0 |

## ✅ Clean Databases (110)

| Database | Tables | Non-empty | FK Violations |
|----------|--------|-----------|---------------|
| activity_1 | 5 | 5/5 (100%) | 0 |
| apartment_rentals | 6 | 6/6 (100%) | 0 |
| assets_maintenance | 14 | 14/14 (100%) | 0 |
| … | … | … | … |

---

## Detailed Database Reports

### Database: allergy_1

**Status:** ❌ 1 error · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** 1 violations

**Errors**

⛔ Found 1 FK data violation(s)

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


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


### Database: college_1

**Status:** ❌ 1 error · **Non-empty:** 7/7 (100%) · **FK:** N/A · **IC:** 2 violations

**Errors**

⛔ Found 2 FK data violation(s)

**Tables (summary)**

Total: 7 · Non-empty: 7 · Empty: 0


### Database: dorm_1

**Status:** ❌ 3 errors · **Non-empty:** 5/5 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table Has_amenity FK ['amenid'] references Dorm_amenity['amenid'] which is not PK/UNIQUE.
⛔ Table Has_amenity FK ['dormid'] references Dorm['dormid'] which is not PK/UNIQUE.
⛔ Table Lives_in FK ['dormid'] references Dorm['dormid'] which is not PK/UNIQUE.

**Tables (summary)**

Total: 5 · Non-empty: 5 · Empty: 0


### Database: flight_4

**Status:** ❌ 1 error · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** 1240 violations

**Errors**

⛔ Found 1240 FK data violation(s)

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: hospital_1

**Status:** ❌ 1 error · **Non-empty:** 15/15 (100%) · **FK:** N/A · **IC:** 1 violations

**Errors**

⛔ Found 1 FK data violation(s)

**Tables (summary)**

Total: 15 · Non-empty: 15 · Empty: 0


### Database: hr_1

**Status:** ❌ 1 error · **Non-empty:** 7/7 (100%) · **FK:** N/A · **IC:** 6 violations

**Errors**

⛔ Found 6 FK data violation(s)

**Tables (summary)**

Total: 7 · Non-empty: 7 · Empty: 0


### Database: imdb

**Status:** ❌ 7 errors, 1 warning · **Non-empty:** 0/16 (0%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table cast FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table classification FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table directed_by FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table made_by FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table tags has FK referencing non-existing column(s) ['kid'] on parent 'keyword'.
⛔ Table tags FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.
⛔ Table written_by FK ['msid'] references copyright['msid'] which is not PK/UNIQUE.

**Warnings**

⚠️ Found 16 empty table(s): "actor", "cast", "classification", "company", "copyright", "directed_by", "director", "genre", "keyword", "made_by", "movie", "producer", "tags", "tv_series", "writer", "written_by"

**Tables (summary)**

Total: 16 · Non-empty: 0 · Empty: 16


### Database: loan_1

**Status:** ❌ 1 error, 1 warning · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table loan has FK referencing non-existing column(s) ['Cust_ID'] on parent 'customer'.

**Warnings**

⚠️ Foreign key declared type families differ: loan.branch_ID (varchar(3)→TEXT) vs bank.branch_ID (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: restaurants

**Status:** ❌ 1 error, 1 warning · **Non-empty:** 0/3 (0%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table LOCATION has FK referencing non-existing column(s) ['RESTAURANT_ID'] on parent 'RESTAURANT'.

**Warnings**

⚠️ Found 3 empty table(s): "GEOGRAPHIC", "LOCATION", "RESTAURANT"

**Tables (summary)**

Total: 3 · Non-empty: 0 · Empty: 3


### Database: sakila_1

**Status:** ❌ 1 error, 1 warning · **Non-empty:** 12/16 (75%) · **FK:** N/A · **IC:** 38273 violations

**Errors**

⛔ Found 38273 FK data violation(s)

**Warnings**

⚠️ Found 4 empty table(s): "film_text", "language", "staff", "store"

**Tables (summary)**

Total: 16 · Non-empty: 12 · Empty: 4


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

**Status:** ❌ 7 errors, 1 warning · **Non-empty:** 0/7 (0%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table category FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.
⛔ Table checkin FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.
⛔ Table neighbourhood FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.
⛔ Table review FK ['user_id'] references user['user_id'] which is not PK/UNIQUE.
⛔ Table review FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.
⛔ Table tip FK ['user_id'] references user['user_id'] which is not PK/UNIQUE.
⛔ Table tip FK ['business_id'] references business['business_id'] which is not PK/UNIQUE.

**Warnings**

⚠️ Found 7 empty table(s): "business", "category", "checkin", "neighbourhood", "review", "tip", "user"

**Tables (summary)**

Total: 7 · Non-empty: 0 · Empty: 7


### Database: academic

**Status:** ⚠️ 2 warnings · **Non-empty:** 0/15 (0%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Found 15 empty table(s): "author", "cite", "conference", "domain", "domain_author", "domain_conference", "domain_journal", "domain_keyword", "domain_publication", "journal", "keyword", "organization", "publication", "publication_keyword", "writes"
⚠️ Foreign key declared type families differ: publication.cid (TEXT→TEXT) vs conference.cid (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 15 · Non-empty: 0 · Empty: 15


### Database: aircraft

**Status:** ⚠️ 2 warnings · **Non-empty:** 5/5 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: match.Winning_Pilot (TEXT→TEXT) vs pilot.Pilot_Id (int(11)→INTEGER); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: match.Winning_Aircraft (TEXT→TEXT) vs aircraft.Aircraft_ID (int(11)→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 5 · Non-empty: 5 · Empty: 0


### Database: architecture

**Status:** ⚠️ 2 warnings · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: bridge.architect_id (INT→INTEGER) vs architect.id (TEXT→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: mill.architect_id (INT→INTEGER) vs architect.id (TEXT→TEXT); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: city_record

**Status:** ⚠️ 1 warning · **Non-empty:** 4/4 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: hosting_city.Host_City (TEXT→TEXT) vs city.City_ID (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 4 · Non-empty: 4 · Empty: 0


### Database: company_employee

**Status:** ⚠️ 1 warning · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: employment.Company_ID (INT→INTEGER) vs company.Company_ID (REAL→REAL); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: cre_Drama_Workshop_Groups

**Status:** ⚠️ 9 warnings · **Non-empty:** 18/18 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: Bookings.Workshop_Group_ID (VARCHAR(100)→TEXT) vs Drama_Workshop_Groups.Workshop_Group_ID (INTEGER→INTEGER); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: Clients.Address_ID (INTEGER→INTEGER) vs Addresses.Address_ID (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: Customer_Orders.Store_ID (INTEGER→INTEGER) vs Stores.Store_ID (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: Customer_Orders.Customer_ID (INTEGER→INTEGER) vs Customers.Customer_ID (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: Customers.Address_ID (INTEGER→INTEGER) vs Addresses.Address_ID (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: Drama_Workshop_Groups.Address_ID (INTEGER→INTEGER) vs Addresses.Address_ID (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: Order_Items.Product_ID (INTEGER→INTEGER) vs Products.Product_ID (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: Performers.Address_ID (INTEGER→INTEGER) vs Addresses.Address_ID (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: Stores.Address_ID (INTEGER→INTEGER) vs Addresses.Address_ID (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 18 · Non-empty: 18 · Empty: 0


### Database: culture_company

**Status:** ⚠️ 2 warnings · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: culture_company.movie_id (TEXT→TEXT) vs movie.movie_id (INT→INTEGER); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: culture_company.book_club_id (TEXT→TEXT) vs book_club.book_club_id (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: formula_1

**Status:** ⚠️ 1 warning · **Non-empty:** 11/13 (85%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Found 2 empty table(s): "lapTimes", "pitStops"

**Tables (summary)**

Total: 13 · Non-empty: 11 · Empty: 2


### Database: geo

**Status:** ⚠️ 1 warning · **Non-empty:** 0/7 (0%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Found 7 empty table(s): "border_info", "city", "highlow", "lake", "mountain", "river", "state"

**Tables (summary)**

Total: 7 · Non-empty: 0 · Empty: 7


### Database: machine_repair

**Status:** ⚠️ 1 warning · **Non-empty:** 4/4 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: repair_assignment.technician_id (INT→INTEGER) vs technician.technician_id (REAL→REAL); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 4 · Non-empty: 4 · Empty: 0


### Database: music_2

**Status:** ⚠️ 1 warning · **Non-empty:** 0/7 (0%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Found 7 empty table(s): "Albums", "Band", "Instruments", "Performance", "Songs", "Tracklists", "Vocals"

**Tables (summary)**

Total: 7 · Non-empty: 0 · Empty: 7


### Database: party_people

**Status:** ⚠️ 1 warning · **Non-empty:** 4/4 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: member.Party_ID (TEXT→TEXT) vs party.Party_ID (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 4 · Non-empty: 4 · Empty: 0


### Database: performance_attendance

**Status:** ⚠️ 2 warnings · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: member_attendance.Performance_ID (INT→INTEGER) vs performance.Performance_ID (REAL→REAL); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: member_attendance.Member_ID (INT→INTEGER) vs member.Member_ID (TEXT→TEXT); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: phone_1

**Status:** ⚠️ 1 warning · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: phone.screen_mode (TEXT→TEXT) vs screen_mode.Graphics_mode (REAL→REAL); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: phone_market

**Status:** ⚠️ 1 warning · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: phone_market.Phone_ID (TEXT→TEXT) vs phone.Phone_ID (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: race_track

**Status:** ⚠️ 1 warning · **Non-empty:** 2/2 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: race.Track_ID (TEXT→TEXT) vs track.Track_ID (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 2 · Non-empty: 2 · Empty: 0


### Database: scholar

**Status:** ⚠️ 1 warning · **Non-empty:** 0/10 (0%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Found 10 empty table(s): "author", "cite", "dataset", "journal", "keyphrase", "paper", "paperDataset", "paperKeyphrase", "venue", "writes"

**Tables (summary)**

Total: 10 · Non-empty: 0 · Empty: 10


### Database: school_finance

**Status:** ⚠️ 2 warnings · **Non-empty:** 3/3 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: budget.School_id (INT→INTEGER) vs School.School_id (TEXT→TEXT); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: endowment.School_id (INT→INTEGER) vs School.School_id (TEXT→TEXT); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 3 · Non-empty: 3 · Empty: 0


### Database: shop_membership

**Status:** ⚠️ 2 warnings · **Non-empty:** 4/4 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: membership_register_branch.Branch_ID (TEXT→TEXT) vs branch.Branch_ID (INT→INTEGER); review coercion behavior and cross-dialect portability
⚠️ Foreign key declared type families differ: purchase.Branch_ID (TEXT→TEXT) vs branch.Branch_ID (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 4 · Non-empty: 4 · Empty: 0


### Database: student_assessment

**Status:** ⚠️ 1 warning · **Non-empty:** 9/9 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: Student_Course_Registrations.course_id (INTEGER→INTEGER) vs Courses.course_id (VARCHAR(100)→TEXT); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 9 · Non-empty: 9 · Empty: 0


### Database: wrestler

**Status:** ⚠️ 1 warning · **Non-empty:** 2/2 (100%) · **FK:** N/A · **IC:** ok

**Warnings**

⚠️ Foreign key declared type families differ: Elimination.Wrestler_ID (TEXT→TEXT) vs wrestler.Wrestler_ID (INT→INTEGER); review coercion behavior and cross-dialect portability

**Tables (summary)**

Total: 2 · Non-empty: 2 · Empty: 0

