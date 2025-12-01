# Table Coverage Report

**Generated:** 2025-11-03 02:41:34

## A) Overall Coverage Summary

### Database-Level Stats

| Metric | Value | Notes |
|--------|-------|-------|
| Total databases | 40 | Unique databases in dataset |
| Total tables across all DBs | 180 | Sum of all tables |
| Tables used ≥1 time | 177 | 98.3% coverage |
| Tables never used | 3 | 1.7% unused |
| Avg tables per DB | 4.5 | — |
| Avg coverage per DB | 99.0% | Median: 100.0% |

## B) Table Usage Distribution

### B1) Usage Frequency

| Usage count | Tables | Share | Description |
|-------------|--------|-------|-------------|
| 0 (unused) | 3 | 1.7% | Never referenced |
| 1-2 times | 11 | 6.1% | Rarely used |
| 3-5 times | 20 | 11.1% | Occasionally used |
| 6-10 times | 39 | 21.7% | Regularly used |
| 11-20 times | 43 | 23.9% | Frequently used |
| 21-50 times | 56 | 31.1% | Very popular |
| 51+ times | 8 | 4.4% | Core tables |

## C) Per-Database Coverage

### C1) Coverage Ranking

**Best Coverage (Top 5):**

| Rank | Database | Tables | Used | Coverage | Queries |
|------|----------|--------|------|----------|---------|
| 1 | region_building | 2 | 2 | 100.0% | 40 |
| 2 | soccer_3 | 2 | 2 | 100.0% | 40 |
| 3 | car_racing | 4 | 4 | 100.0% | 50 |
| 4 | sing_contest | 3 | 3 | 100.0% | 20 |
| 5 | video_game | 4 | 4 | 100.0% | 42 |

**Worst Coverage (Bottom 5):**

| Rank | Database | Tables | Used | Coverage | Queries | Unused Tables |
|------|----------|--------|------|----------|---------|---------------|
| 1 | tv_shows | 5 | 4 | 80.0% | 15 | 1 |
| 2 | online_exams | 7 | 6 | 85.7% | 40 | 1 |
| 3 | real_estate_rentals | 13 | 12 | 92.3% | 72 | 1 |
| 4 | pilot_1 | 2 | 2 | 100.0% | 82 | 0 |
| 5 | book_review | 2 | 2 | 100.0% | 21 | 0 |

## D) Unused Tables Analysis

### D1) Unused Tables by Database

*(showing databases with ≥3 unused tables)*

| Database | Unused Count | Examples | Possible Reasons |
|----------|-------------|----------|------------------|
| *Analysis requires schema introspection* | — | — | — |

*Note: Full unused table analysis requires schema introspection to identify all available tables.*

## H) Coverage Gaps & Recommendations

### H1) Critical Gaps

*(Databases with significant unused tables)*

| Database | Unused Count | Coverage | Impact | Recommendation |
|----------|-------------|----------|--------|----------------|
| tv_shows | 1 | 80.0% | Medium | Add queries using: [city_channel_tv_show] |
| online_exams | 1 | 85.7% | Medium | Add queries using: [questions_in_exams] |
| real_estate_rentals | 1 | 92.3% | Medium | Add queries using: [ref_room_types] |

### H2) Quick Wins

*(Databases needing coverage improvement)*

| Database | Current Coverage | Tables Used | Potential Improvement | Suggestion |
|----------|------------------|-------------|----------------------|------------|
| tv_shows | 80.0% | 4/5 | 15.0% | Add queries for 1 unused tables |
| online_exams | 85.7% | 6/7 | 9.3% | Add queries for 1 unused tables |
| real_estate_rentals | 92.3% | 12/13 | 2.7% | Add queries for 1 unused tables |

### H3) Overall Recommendations

1. **🎯 Priority 1** (High Impact):
   - Analyze 40 databases for comprehensive table coverage
   - Identify unused tables across all databases
   - Focus on underused foreign key relationships

2. **🎯 Priority 2** (Medium Impact):
   - Balance query distribution across databases
   - Create queries using many-to-many join tables
   - Add temporal/historical queries for underused tables

3. **📊 Coverage Goals**:
   - Target: ≥90% table usage per database
   - Enable schema introspection for detailed analysis
   - Regular monitoring of table coverage metrics

## I) Table Coverage Heatmap

### Visual Summary

```
Database          Coverage  |████████████████████| Usage Pattern
──────────────────────────────────────────────────────────────────
region_building    100% ████████████████████████ Perfect coverage
soccer_3           100% ████████████████████████ Perfect coverage
car_racing         100% ████████████████████████ Perfect coverage
sing_contest       100% ████████████████████████ Perfect coverage
video_game         100% ████████████████████████ Perfect coverage
aan_1              100% ████████████████████████ Perfect coverage
country_language   100% ████████████████████████ Perfect coverage
movie_2            100% ████████████████████████ Perfect coverage
club_leader        100% ████████████████████████ Perfect coverage
warehouse_1        100% ████████████████████████ Perfect coverage
bike_racing        100% ████████████████████████ Perfect coverage
boat_1             100% ████████████████████████ Perfect coverage
restaurant_bills   100% ████████████████████████ Perfect coverage
e_commerce         100% ████████████████████████ Perfect coverage
cre_Doc_and_collec 100% ████████████████████████ Perfect coverage
government_shift   100% ████████████████████████ Perfect coverage
book_1             100% ████████████████████████ Perfect coverage
vehicle_rent       100% ████████████████████████ Perfect coverage
car_road_race      100% ████████████████████████ Perfect coverage
art_1              100% ████████████████████████ Perfect coverage
conference         100% ████████████████████████ Perfect coverage
university_rank    100% ████████████████████████ Perfect coverage
address_1          100% ████████████████████████ Perfect coverage
book_press         100% ████████████████████████ Perfect coverage
institution_sports 100% ████████████████████████ Perfect coverage
bakery_1           100% ████████████████████████ Perfect coverage
advertising_agenci 100% ████████████████████████ Perfect coverage
vehicle_driver     100% ████████████████████████ Perfect coverage
bbc_channels       100% ████████████████████████ Perfect coverage
headphone_store    100% ████████████████████████ Perfect coverage
cre_Doc_Workflow   100% ████████████████████████ Perfect coverage
cre_Students_Infor 100% ████████████████████████ Perfect coverage
district_spokesman 100% ████████████████████████ Perfect coverage
customers_and_orde 100% ████████████████████████ Perfect coverage
planet_1           100% ████████████████████████ Perfect coverage
book_review        100% ████████████████████████ Perfect coverage
pilot_1            100% ████████████████████████ Perfect coverage
real_estate_rental  92% ██████████████████████   Excellent
online_exams        85% ████████████████████     Good coverage
tv_shows            80% ███████████████████      Good coverage
```
