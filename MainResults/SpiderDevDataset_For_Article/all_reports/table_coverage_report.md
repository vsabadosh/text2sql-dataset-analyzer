# Table Coverage Report

**Generated:** 2025-11-10 18:21:06

## A) Overall Coverage Summary

### Database-Level Stats

| Metric | Value | Notes |
|--------|-------|-------|
| Total databases | 20 | Unique databases in dataset |
| Total tables across all DBs | 80 | Sum of all tables |
| Tables used ≥1 time | 78 | 97.5% coverage |
| Tables never used | 2 | 2.5% unused |
| Avg tables per DB | 4.0 | — |
| Avg coverage per DB | 98.4% | Median: 100.0% |

## B) Table Usage Distribution

### B1) Usage Frequency

| Usage count | Tables | Share | Description |
|-------------|--------|-------|-------------|
| 0 (unused) | 2 | 2.5% | Never referenced |
| 1-2 times | 6 | 7.5% | Rarely used |
| 3-5 times | 4 | 5.0% | Occasionally used |
| 6-10 times | 23 | 28.8% | Regularly used |
| 11-20 times | 12 | 15.0% | Frequently used |
| 21-50 times | 29 | 36.2% | Very popular |
| 51+ times | 4 | 5.0% | Core tables |

## C) Per-Database Coverage

### C1) Coverage Ranking

**Best Coverage (Top 5):**

| Rank | Database | Tables | Used | Coverage | Queries |
|------|----------|--------|------|----------|---------|
| 1 | pets_1 | 3 | 3 | 100.0% | 42 |
| 2 | orchestra | 4 | 4 | 100.0% | 40 |
| 3 | employee_hire_evaluation | 4 | 4 | 100.0% | 38 |
| 4 | concert_singer | 4 | 4 | 100.0% | 45 |
| 5 | world_1 | 3 | 3 | 100.0% | 120 |

**Worst Coverage (Bottom 5):**

| Rank | Database | Tables | Used | Coverage | Queries | Unused Tables |
|------|----------|--------|------|----------|---------|---------------|
| 1 | real_estate_properties | 5 | 4 | 80.0% | 4 | 1 |
| 2 | dog_kennels | 8 | 7 | 87.5% | 82 | 1 |
| 3 | student_transcripts_tracking | 11 | 11 | 100.0% | 78 | 0 |
| 4 | tvshow | 3 | 3 | 100.0% | 62 | 0 |
| 5 | wta_1 | 3 | 3 | 100.0% | 62 | 0 |

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
| real_estate_properties | 1 | 80.0% | Medium | Add queries using: [other_property_features] |
| dog_kennels | 1 | 87.5% | Medium | Add queries using: [sizes] |

### H2) Quick Wins

*(Databases needing coverage improvement)*

| Database | Current Coverage | Tables Used | Potential Improvement | Suggestion |
|----------|------------------|-------------|----------------------|------------|
| real_estate_properties | 80.0% | 4/5 | 15.0% | Add queries for 1 unused tables |
| dog_kennels | 87.5% | 7/8 | 7.5% | Add queries for 1 unused tables |

### H3) Overall Recommendations

1. **🎯 Priority 1** (High Impact):
   - Analyze 20 databases for comprehensive table coverage
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
pets_1             100% ████████████████████████ Perfect coverage
orchestra          100% ████████████████████████ Perfect coverage
employee_hire_eval 100% ████████████████████████ Perfect coverage
concert_singer     100% ████████████████████████ Perfect coverage
world_1            100% ████████████████████████ Perfect coverage
poker_player       100% ████████████████████████ Perfect coverage
network_1          100% ████████████████████████ Perfect coverage
battle_death       100% ████████████████████████ Perfect coverage
car_1              100% ████████████████████████ Perfect coverage
flight_2           100% ████████████████████████ Perfect coverage
course_teach       100% ████████████████████████ Perfect coverage
voter_1            100% ████████████████████████ Perfect coverage
singer             100% ████████████████████████ Perfect coverage
cre_Doc_Template_M 100% ████████████████████████ Perfect coverage
museum_visit       100% ████████████████████████ Perfect coverage
wta_1              100% ████████████████████████ Perfect coverage
tvshow             100% ████████████████████████ Perfect coverage
student_transcript 100% ████████████████████████ Perfect coverage
dog_kennels         87% █████████████████████    Good coverage
real_estate_proper  80% ███████████████████      Good coverage
```
