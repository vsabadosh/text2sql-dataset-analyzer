# Query Structure & Table Coverage Report - Proposal

## Overview

This document proposes comprehensive reports for analyzing query structure patterns and database table coverage in text-to-SQL datasets. These reports will help identify:
- Query complexity distribution
- Structural patterns and features
- Dataset biases and gaps
- Table coverage and usage patterns

---

## 📊 Report 1: Query Structure Profile Report

### Purpose
Provide a detailed statistical breakdown of SQL query structural patterns to understand dataset composition, identify biases, and assess difficulty distribution.

### Sections

#### A) **Joins Analysis** (Multi-dimensional)

**A1) Joins per Query Distribution**

| Joins per query | Count | Share | Cumulative | (==Don't include Cumulative columns==)
|----------------|-------|-------|------------|
| 0 (single-table) | 412 | 27.5% | 27.5% |
| 1 join | 530 | 35.4% | 62.9% |
| 2 joins | 332 | 22.2% | 85.1% |
| 3 joins | 145 | 9.7% | 94.8% |
| 4 joins | 52 | 3.5% | 98.3% |
| 5+ joins | 25 | 1.7% | 100.0% |
| **Total** | **1,496** | **100%** | — |

**A2) Join Type Distribution** (for queries with ≥1 join)

| Join type | Queries using | Share of joined queries | Share of all queries |
|-----------|--------------|------------------------|---------------------|
| INNER (implicit/explicit) | 962 | 88.7% | 64.3% |
| LEFT (OUTER) | 294 | 27.1% | 19.7% |
| RIGHT (OUTER) | 24 | 2.2% | 1.6% |
| FULL (OUTER) | 8 | 0.7% | 0.5% |
| CROSS | 15 | 1.4% | 1.0% |
| SELF-join detected | 61 | 5.6% | 4.1% |

*Note: A single query may use multiple join types, so percentages may exceed 100%*

**A3) Join Complexity Patterns**

| Pattern | Count | Share | Description |
|---------|-------|-------|-------------|
| Single join type | 890 | 82.1% | Uses only one join type |
| Mixed join types | 194 | 17.9% | Uses 2+ join types |
| Implicit joins | 123 | 11.3% | Uses WHERE for joins (antipattern) |
| Complex join chains | 87 | 8.0% | 3+ tables in join chain |

**A4) By Split** (train/val/test distribution check) (==Don't Include THIS===)

| Split | Avg joins/query | 0 joins | 1-2 joins | 3+ joins | Max joins |
|-------|----------------|---------|-----------|----------|-----------|
| Train | 1.42 | 28.1% | 56.3% | 15.6% | 8 |
| Val | 1.38 | 27.8% | 58.2% | 14.0% | 7 |
| Test | 1.51 | 25.4% | 55.1% | 19.5% | 9 |

*💡 Tip: Check for distribution drift - ideally splits should have similar patterns*

---

#### B) **Subqueries & CTEs**

**B1) Subquery Presence & Depth**

| Feature | Count | Share | Notes |
|---------|-------|-------|-------|
| Has ≥1 subquery | 468 | 31.3% | At least one subquery |
| Has correlated subquery | 132 | 8.8% | Uses outer reference (EXISTS/IN) |
| Has nested subquery (depth ≥2) | 126 | 8.4% | Subquery within subquery |
| Max depth = 1 | 342 | 22.9% | Simple subqueries only |
| Max depth = 2 | 110 | 7.4% | Two-level nesting |
| Max depth ≥ 3 | 16 | 1.1% | Deep nesting (complex) |

**B2) Subquery Location** (==Don't Include THIS===)

| Location | Count | Share | Example Context |
|----------|-------|-------|-----------------|
| SELECT clause | 142 | 9.5% | Scalar subquery in projection |
| FROM clause | 287 | 19.2% | Derived table/inline view |
| WHERE clause | 218 | 14.6% | Filter with subquery |
| HAVING clause | 34 | 2.3% | Aggregate filter with subquery |
| IN/EXISTS predicate | 156 | 10.4% | Set membership test |

**B3) Common Table Expressions (WITH)** 

| Feature | Count | Share | Median CTEs when present |
|---------|-------|-------|-------------------------|
| Has ≥1 CTE | 204 | 13.6% | 1 |
| Has multiple CTEs (≥2) | 67 | 4.5% | 2 |
| Has 3+ CTEs | 18 | 1.2% | 3 |
| Has recursive CTE | 12 | 0.8% | — |

**B4) Subquery vs CTE Usage** (==for now don't inlcude this section==)

| Pattern | Count | Share |
|---------|-------|-------|
| Uses subqueries only | 297 | 19.9% |
| Uses CTEs only | 33 | 2.2% |
| Uses both | 171 | 11.4% |
| Neither | 995 | 66.5% |

---

#### C) **Set Operations** (==for now don't inlcude this section==)

| Set operation | Count | Share | Avg # of sets combined |
|---------------|-------|-------|----------------------|
| UNION ALL | 58 | 3.9% | 2.1 |
| UNION (distinct) | 21 | 1.4% | 2.0 |
| INTERSECT | 7 | 0.5% | 2.0 |
| EXCEPT / MINUS | 5 | 0.3% | 2.0 |
| Multiple set ops (2+) | 8 | 0.5% | 3.2 |
| **Any set operation** | **91** | **6.1%** | **2.1** |

---

#### D) **Aggregation & Grouping**

**D1) Basic Statistics**

| Feature | Count | Share |
|---------|-------|-------|
| Has aggregation (any) | 676 | 45.2% |
| GROUP BY | 545 | 36.4% |
| HAVING | 108 | 7.2% |
| DISTINCT | 239 | 16.0% |

**D2) Aggregate Function Usage**

| Function | Count | Share of all queries | Share of agg queries |
|----------|-------|---------------------|---------------------|
| COUNT | 521 | 34.8% | 77.1% |
| SUM | 234 | 15.6% | 34.6% |
| AVG | 189 | 12.6% | 28.0% |
| MAX | 156 | 10.4% | 23.1% |
| MIN | 143 | 9.6% | 21.2% |
| Other (GROUP_CONCAT, etc.) | 45 | 3.0% | 6.7% |

**D3) Aggregation Complexity**

| Pattern | Count | Share | Description |
|---------|-------|-------|-------------|
| Single aggregate | 378 | 25.3% | One aggregate function |
| Multiple aggregates | 298 | 19.9% | 2+ aggregate functions |
| Nested aggregation | 56 | 3.7% | Aggregate of aggregate (subquery) |
| HAVING without GROUP BY | 8 | 0.5% | Rare pattern |
| DISTINCT with GROUP BY | 67 | 4.5% | Redundant pattern |

---

#### E) **Window Functions** (Advanced Analytics) 

| Feature | Count | Share | Share of all queries |
|---------|-------|-------|---------------------|
| Has ≥1 window function | 72 | 4.8% | — |
| With PARTITION BY | 58 | 3.9% | 80.6% of window queries |
| With ORDER BY | 65 | 4.3% | 90.3% of window queries |
| With frame spec (ROWS/RANGE) | 23 | 1.5% | 31.9% of window queries |

**Window Function Types** (==for now don't inlcude this section==)

| Function | Count | Share of window queries |
|----------|-------|------------------------|
| ROW_NUMBER | 34 | 47.2% |
| RANK | 28 | 38.9% |
| DENSE_RANK | 15 | 20.8% |
| LAG/LEAD | 18 | 25.0% |
| SUM/AVG/COUNT (windowed) | 24 | 33.3% |
| Other | 8 | 11.1% |

---

#### F) **Filtering & Predicates** (==for now don't inlcude this section==)

**F1) WHERE Clause Complexity** 

| Condition count | Queries | Share | Description |
|----------------|---------|-------|-------------|
| No WHERE | 412 | 27.5% | Unfiltered queries |
| 1 condition | 298 | 19.9% | Simple filter |
| 2-3 conditions | 456 | 30.5% | Moderate filtering |
| 4-5 conditions | 234 | 15.6% | Complex filtering |
| 6+ conditions | 96 | 6.4% | Very complex |

**F2) Predicate Types** (==Don't include this==)

| Predicate | Count | Share |
|-----------|-------|-------|
| Comparison (=, <, >, etc.) | 892 | 59.6% |
| LIKE | 187 | 12.5% |
| IN | 234 | 15.6% |
| BETWEEN | 98 | 6.6% |
| IS NULL / IS NOT NULL | 145 | 9.7% |
| EXISTS | 87 | 5.8% |

**F3) Logical Operators** (==Don't include this==)

| Operator | Avg per query (when used) | Queries using |
|----------|---------------------------|---------------|
| AND | 2.3 | 734 (49.1%) |
| OR | 1.8 | 267 (17.8%) |
| NOT | 1.2 | 156 (10.4%) |

---

#### G) **Sorting & Limiting** (==Don't include this==)

| Feature | Count | Share | Avg columns (when used) |
|---------|-------|-------|------------------------|
| ORDER BY | 621 | 41.5% | 1.4 |
| LIMIT / TOP | 504 | 33.7% | — |
| OFFSET | 89 | 6.0% | — |
| ORDER BY without LIMIT | 117 | 7.8% | Potential inefficiency |

---

#### H) **Special Features** (==Don't include this==)

| Feature | Count | Share | Notes |
|---------|-------|-------|-------|
| CASE expressions | 178 | 11.9% | Conditional logic |
| Type casts | 92 | 6.2% | CAST/CONVERT |
| String functions | 234 | 15.6% | CONCAT, SUBSTRING, etc. |
| Date/time functions | 167 | 11.2% | DATE, DATEADD, etc. |
| Math functions | 89 | 6.0% | ROUND, ABS, etc. |
| NULL handling (COALESCE/IFNULL) | 134 | 9.0% | Explicit NULL handling |

---

#### I) **Query Complexity Distribution**

**I1) Difficulty Levels**

| Difficulty | Count | Share | Complexity Score Range |
|------------|-------|-------|----------------------|
| Easy | 542 | 36.2% | 10-29 |
| Medium | 623 | 41.6% | 30-59 |
| Hard | 267 | 17.8% | 60-79 |
| Expert | 64 | 4.3% | 80-100 |

**I2) Feature Density** (avg features per query by difficulty)

| Difficulty | Avg Tables | Avg Joins | Avg Subqueries | Avg Aggregates | Avg Complexity |
|------------|-----------|-----------|----------------|----------------|----------------|
| Easy | 1.2 | 0.1 | 0.0 | 0.3 | 15.4 |
| Medium | 2.1 | 1.3 | 0.2 | 1.1 | 42.7 |
| Hard | 3.4 | 2.6 | 1.2 | 1.8 | 68.3 |
| Expert | 4.8 | 3.9 | 2.4 | 2.1 | 87.6 |

**I3) Complexity Histogram** (==for now don't inlcude this section==)

```
Score  Count  ████████████████████████
0-9    23     ██
10-19  519    ████████████████████████
20-29  234    ███████████
30-39  312    ███████████████
40-49  311    ███████████████
50-59  178    ████████
60-69  156    ███████
70-79  111    █████
80-89  42     ██
90-100 22     █
```

---

#### J) **Cross-Feature Analysis**

**J1) Feature Combinations** (top 10 most common)

| Rank | Combination | Count | Share |
|------|-------------|-------|-------|
| 1 | JOIN + GROUP BY + ORDER BY | 234 | 15.6% |
| 2 | WHERE + ORDER BY + LIMIT | 198 | 13.2% |
| 3 | JOIN + WHERE + AGGREGATE | 187 | 12.5% |
| 4 | Subquery + WHERE + IN | 156 | 10.4% |
| 5 | Multiple JOINs + AGGREGATE | 145 | 9.7% |
| 6 | CTE + JOIN + AGGREGATE | 89 | 6.0% |
| 7 | UNION + ORDER BY | 52 | 3.5% |
| 8 | Window Function + ORDER BY | 48 | 3.2% |
| 9 | HAVING + GROUP BY + Subquery | 34 | 2.3% |
| 10 | Multiple CTEs + JOIN | 28 | 1.9% |

---

---

#### L) **Dataset Health Summary**

**Overall Metrics:**
- **Total Queries:** 1,496
- **Parseable:** 1,487 (99.4%)
- **Avg Complexity:** 38.7/100
- **Median Complexity:** 35
- **Std Dev:** 24.3

**Balance Indicators:**
| Metric | Status | Notes |
|--------|--------|-------|
| Difficulty distribution | ✅ Good | Reasonable spread across levels |
| Single vs multi-table | ✅ Good | 72.5% use joins |
| Simple vs advanced features | ⚠️ Fair | Limited window functions (4.8%) |
| Split consistency | ✅ Good | <5% variance across splits |

**Recommendations:**
1. ✅ **Well-balanced** join distribution (27.5% single-table is healthy)
2. ⚠️ **Underrepresented**: Window functions (4.8%), Recursive CTEs (0.8%)
3. 🔴 **Consider adding**: More INTERSECT/EXCEPT examples (0.8% combined)
4. ✅ **Good coverage**: Subqueries (31.3%), Aggregations (45.2%)

---

## 📊 Report 2: Database Table Coverage Report

### Purpose
Analyze how comprehensively dataset queries utilize available database tables, identify unused tables, and detect coverage gaps.

### Sections

#### A) **Overall Coverage Summary**

**Database-Level Stats:**
| Metric | Value | Notes |
|--------|-------|-------|
| Total databases | 23 | Unique databases in dataset |
| Total tables across all DBs | 487 | Sum of all tables |
| Tables used ≥1 time | 412 | 84.6% coverage |
| Tables never used | 75 | 15.4% unused |
| Avg tables per DB | 21.2 | — |
| Avg coverage per DB | 83.1% | Median: 85.7% |

---

#### B) **Table Usage Distribution**

**B1) Usage Frequency**

| Usage count | Tables | Share | Description |
|-------------|--------|-------|-------------|
| 0 (unused) | 75 | 15.4% | Never referenced |
| 1-2 times | 123 | 25.3% | Rarely used |
| 3-5 times | 98 | 20.1% | Occasionally used |
| 6-10 times | 87 | 17.9% | Regularly used |
| 11-20 times | 64 | 13.1% | Frequently used |
| 21-50 times | 32 | 6.6% | Very popular |
| 51+ times | 8 | 1.6% | Core tables |

**B2) Usage Statistics** ((==for now don't inlcude this section==))

| Statistic | Value |
|-----------|-------|
| Min usage | 0 |
| Median usage | 5 |
| Mean usage | 7.3 |
| Max usage | 127 |
| Std dev | 12.4 |

---

#### C) **Per-Database Coverage**

**C1) Coverage Ranking** (Top 10 & Bottom 10)

**Best Coverage:**
| Rank | Database | Tables | Used | Coverage | Queries |
|------|----------|--------|------|----------|---------|
| 1 | concert_singer | 8 | 8 | 100.0% | 45 |
| 2 | world_1 | 12 | 12 | 100.0% | 67 |
| 3 | car_rental | 15 | 15 | 100.0% | 52 |
| 4 | employee | 18 | 17 | 94.4% | 71 |
| 5 | department | 20 | 19 | 95.0% | 63 |

**Worst Coverage:**
| Rank | Database | Tables | Used | Coverage | Queries | Unused Tables |
|------|----------|--------|------|----------|---------|---------------|
| 19 | insurance | 32 | 18 | 56.3% | 34 | 14 (claim_history, policy_notes, ...) |
| 20 | hospital | 28 | 15 | 53.6% | 28 | 13 (patient_insurance, appointments, ...) |
| 21 | university | 45 | 24 | 53.3% | 41 | 21 (course_materials, office_hours, ...) |
| 22 | retail | 38 | 19 | 50.0% | 36 | 19 (promotions, gift_cards, ...) |
| 23 | city_data | 52 | 23 | 44.2% | 29 | 29 (neighborhoods, landmarks, ...) |

**C2) Coverage Histogram** ((==for now don't inlcude this section==))

```
Coverage   DBs  ████████████
0-20%      1    █
21-40%     2    ██
41-60%     5    █████
61-80%     8    ████████
81-100%    7    ███████
```

---

#### D) **Unused Tables Analysis**

**D1) Unused Tables by Database** (showing databases with ≥3 unused tables)

| Database | Unused Count | Examples | Possible Reasons |
|----------|-------------|----------|------------------|
| city_data | 29 | neighborhoods, landmarks, parks | Incomplete dataset |
| university | 21 | course_materials, office_hours | Focus on core academic data |
| retail | 19 | promotions, gift_cards, loyalty | Limited scope |
| hospital | 13 | patient_insurance, appointments | Privacy/compliance limited |
| insurance | 14 | claim_history, policy_notes | Complexity limitation |

**D2) Table Categories Most Underused** (==for now don't inlcude this section==)

| Category Pattern | Unused Count | Share | Examples |
|-----------------|-------------|-------|----------|
| Metadata/Logs | 18 | 24.0% | audit_log, change_history |
| Many-to-many join tables | 15 | 20.0% | course_enrollment, project_assignment |
| Supplementary info | 12 | 16.0% | notes, comments, descriptions |
| Temporal/Historical | 11 | 14.7% | history, archive, snapshots |
| Complex relationships | 10 | 13.3% | nested hierarchies |
| Other | 9 | 12.0% | miscellaneous |

---

#### E) **High-Usage Tables** (Hot Spots) ((==for now don't inlcude this section==))

**Top 20 Most Referenced Tables:**

| Rank | Table | Database | Usage Count | Share of DB queries | Avg joins with this table |
|------|-------|----------|-------------|--------------------|-----------------------|
| 1 | users | employee | 127 | 89.4% | 2.3 |
| 2 | orders | retail | 98 | 67.6% | 1.8 |
| 3 | students | university | 87 | 71.3% | 2.1 |
| 4 | country | world_1 | 82 | 91.1% | 1.5 |
| 5 | employees | department | 76 | 84.4% | 1.9 |
| ... | ... | ... | ... | ... | ... |

**High-Usage Pattern Analysis:**
- **Entity tables** (users, customers, products): Avg 45.2 references
- **Fact tables** (orders, transactions): Avg 38.7 references
- **Dimension tables** (country, category): Avg 32.1 references
- **Bridge tables** (many-to-many): Avg 12.4 references

---

#### F) **Join Coverage Analysis** (==for now don't inlcude this section==)

**F1) Table Relationships**

| Metric | Value | Description |
|--------|-------|-------------|
| Total foreign keys defined | 312 | Declared relationships |
| FKs used in queries | 267 | 85.6% utilized |
| FKs never used | 45 | 14.4% unused |
| Implicit joins (no FK) | 89 | Ad-hoc relationships |

**F2) Most Common Join Pairs** (Top 15) (==for now don't inlcude this section==)

| Rank | Table 1 | Table 2 | Database | Count | Has FK? |
|------|---------|---------|----------|-------|---------|
| 1 | orders | customers | retail | 76 | ✅ Yes |
| 2 | students | enrollments | university | 67 | ✅ Yes |
| 3 | employees | departments | department | 58 | ✅ Yes |
| 4 | city | country | world_1 | 54 | ✅ Yes |
| 5 | products | orders | retail | 52 | ✅ Yes |
| ... | ... | ... | ... | ... | ... |

**F3) Unused Foreign Keys** (==for now don't inlcude this section==)

| Database | From Table | To Table | FK Name | Reason |
|----------|-----------|----------|---------|--------|
| hospital | appointments | doctors | fk_doctor_id | Appointments table underused |
| retail | promotions | products | fk_product_id | Promotions not in scope |
| university | course_materials | courses | fk_course_id | Materials table unused |

---

#### G) **Coverage by Query Complexity**

**Table Usage by Query Difficulty:**

| Difficulty | Avg Tables/Query | Coverage % | Notes |
|------------|------------------|-----------|-------|
| Easy | 1.2 | 34.2% | Single-table queries |
| Medium | 2.1 | 58.7% | 2-3 table joins |
| Hard | 3.4 | 76.3% | More comprehensive |
| Expert | 4.8 | 82.1% | Widest coverage |

**Insight:** More complex queries naturally use more tables, improving overall coverage.

---

#### H) **Coverage Gaps & Recommendations**

**H1) Critical Gaps** (≥5 unused tables per database)

| Database | Unused Count | Impact | Recommendation |
|----------|-------------|--------|----------------|
| city_data | 29 | 🔴 High | Add 10-15 queries covering geo features |
| university | 21 | 🔴 High | Expand to course materials, schedules |
| retail | 19 | ⚠️ Medium | Add promotion/loyalty queries |
| hospital | 13 | ⚠️ Medium | Include appointment workflows |
| insurance | 14 | ⚠️ Medium | Cover claims processing |

**H2) Quick Wins** (high-value unused tables)

| Table | Database | Potential | Suggestion |
|-------|----------|-----------|------------|
| appointments | hospital | 🔥 High | Add scheduling queries (easy) |
| promotions | retail | 🔥 High | Add discount/offer queries (medium) |
| course_materials | university | 🔥 High | Add resource access queries (easy) |
| claim_history | insurance | 🟡 Medium | Add historical analysis (hard) |

**H3) Overall Recommendations**

1. **🎯 Priority 1** (High Impact):
   - Add 25-30 queries to `city_data` database (current: 44% coverage)
   - Add 15-20 queries to `university` database (current: 53% coverage)
   - Focus on underused foreign key relationships (45 unused FKs)

2. **🎯 Priority 2** (Medium Impact):
   - Balance `retail` and `hospital` databases (+10-15 queries each)
   - Create queries using many-to-many join tables (20% underused)
   - Add temporal/historical queries (history tables underused)

3. **✅ Well-Covered** (Maintain):
   - `concert_singer`, `world_1`, `car_rental` (100% coverage)
   - Core entity tables (users, orders, students) well-represented

4. **📊 Coverage Goals**:
   - Target: ≥90% table usage per database
   - Current: 83.1% average (need +6.9% improvement)
   - Estimated queries needed: ~45-60 additional queries

---

#### I) **Table Coverage Heatmap** (Visual Summary)

```
Database          Coverage  |████████████████████| Usage Pattern
──────────────────────────────────────────────────────────────────
concert_singer    100% ████████████████████████ Even distribution
world_1           100% ████████████████████████ Even distribution  
car_rental        100% ████████████████████████ Even distribution
employee          94%  ███████████████████████  Good coverage
department        95%  ███████████████████████  Good coverage
flight            89%  ██████████████████████   Good, 2 unused
university        53%  █████████████            Uneven - expand
retail            50%  ████████████             Core tables only
hospital          54%  █████████████            Limited scope
city_data         44%  ██████████               Significant gaps
insurance         56%  █████████████            Missing claims data
```

---

#### J) **Cross-Split Coverage Consistency** ((==for now don't inlcude this section==))

**Coverage by Dataset Split:**

| Split | Queries | DBs Used | Avg Tables/Query | Unique Tables Used | Overlap with Other Splits |
|-------|---------|----------|------------------|-------------------|--------------------------|
| Train | 1,047 (70%) | 23 | 2.1 | 398 | 96.6% (with val/test) |
| Val | 224 (15%) | 22 | 2.0 | 387 | 97.2% |
| Test | 225 (15%) | 23 | 2.2 | 392 | 96.9% |

**Tables Unique to Single Split:** 8 tables (1.6%)
- **Train-only:** 4 tables (risk: undertrained in val/test)
- **Val-only:** 2 tables (minor concern)
- **Test-only:** 2 tables (possible data leakage check needed)

**Recommendation:** Ensure all critical tables appear across all splits for fair evaluation.

---

## 📈 Report 3: Combined Structure × Coverage Analysis (==for now don't inlcude this report==)

### Purpose
Cross-analyze query structure patterns with table coverage to identify correlations and optimization opportunities.

### Sections

#### A) **Table Usage by Query Features**

| Feature | Avg Tables Used | Correlation | Insight |
|---------|----------------|-------------|---------|
| Has JOIN | 2.8 | Strong ↗️ | More joins = more tables |
| Has subquery | 2.4 | Moderate ↗️ | Subqueries broaden scope |
| Has CTE | 3.1 | Strong ↗️ | CTEs enable complex multi-table |
| Has window function | 2.6 | Moderate ↗️ | Analytics queries wider scope |
| Has set operation | 2.2 | Weak ↗️ | UNIONs may not add tables |
| Has aggregation | 1.9 | Weak ↗️ | Aggregations can be single-table |

#### B) **Underused Tables by Complexity**

Tables used in ≤5 queries, broken down by query difficulty:

| Difficulty Level | Tables in this category | Avg usage | Opportunity |
|------------------|------------------------|-----------|-------------|
| Easy | 45 | 1.8 | Add simple single-table queries |
| Medium | 32 | 3.2 | Add basic joins involving these |
| Hard | 18 | 4.1 | Create complex multi-join queries |
| Expert | 10 | 4.4 | Advanced analytics opportunities |

#### C) **Coverage Improvement Roadmap**

**Phase 1: Quick Wins** (2-3 weeks)
- Add 20 easy queries using unused core tables
- Target: +10% coverage in 5 databases

**Phase 2: Medium Complexity** (4-6 weeks)
- Add 25 medium queries with joins to underused tables
- Target: +15% coverage overall

**Phase 3: Advanced Features** (8-10 weeks)
- Add 15 hard/expert queries using rare patterns (window functions, recursive CTEs)
- Target: 90%+ coverage across all databases

---

## 📈 Report 3: Query Quility

#### K) **Quality Indicators** 

**K1) Best Practices** (==for now don't inlcude this section==)

| Pattern | Count | Share | Assessment |
|---------|-------|-------|-----------|
| Uses explicit JOINs (vs implicit) | 961 | 64.2% | ✅ Good |
| Avoids SELECT * | 1,189 | 79.5% | ✅ Good |
| Uses aliases for multi-table | 876 | 58.6% | ✅ Good |
| Has WHERE with JOINs | 634 | 42.4% | ✅ Good filtering |

**K2) Antipatterns Detected**

| Antipattern | Count | Share | Severity |
|-------------|-------|-------|----------|
| SELECT * | 307 | 20.5% | ⚠️ Medium |
| Implicit JOIN | 123 | 8.2% | ⚠️ Medium |
| Functions in WHERE | 89 | 6.0% | ⚠️ Medium |
| Correlated subquery | 132 | 8.8% | ⚠️ Medium |
| No LIMIT on large scans | 117 | 7.8% | 🔴 High |
| Cartesian product risk | 34 | 2.3% | 🔴 High |

## 🛠️ Implementation Plan

### Technical Approach

1. **Data Collection** (Already Available)
   - Query features: `metrics_query_syntax` table in DuckDB
   - Table info: Via `DbManager.get_tables()` and schema introspection
   - Usage tracking: Cross-reference `tables` field in metrics

2. **New Analyzer Component** (To Build)
   ```
   src/text2sql_pipeline/analyzers/query_structure/
   ├── __init__.py
   ├── structure_profile_annot.py    # Query structure profiler
   ├── table_coverage_annot.py       # Table coverage tracker
   └── metrics.py                    # New metric models
   ```

3. **Report Generator Extension**
   - Add `generate_query_structure_report()` to `md_generator.py`
   - Add `generate_table_coverage_report()` to `md_generator.py`
   - Add `generate_combined_analysis_report()` to `md_generator.py`

4. **DuckDB Schema Extension**
   ```sql
   -- New tables
   CREATE TABLE metrics_query_structure_profile (...);
   CREATE TABLE metrics_table_coverage (...);
   CREATE TABLE metrics_table_usage_detail (...);
   ```

### CLI Commands

```bash
# Generate all reports (includes new ones)
text2sql report --database metrics.duckdb --output full_report.md

# Generate only query structure report
text2sql report --database metrics.duckdb --output structure.md --type query-structure

# Generate only table coverage report
text2sql report --database metrics.duckdb --output coverage.md --type table-coverage

# Generate combined analysis
text2sql report --database metrics.duckdb --output combined.md --type combined
```

---

## 📋 Report Output Examples

### File Structure After Generation

```
analyses_spider_dataset_20251030/
├── analysis_report.md                        # Main report (existing)
├── schema_validation_report.md               # Schema details (existing)
├── query_execution_issues_report.md          # Execution issues (existing)
├── query_structure_profile_report.md         # ⭐ NEW
├── table_coverage_report.md                  # ⭐ NEW
├── combined_structure_coverage_report.md     # ⭐ NEW
└── metrics.duckdb
```

---

## 🎯 Summary

### What's New

**Report 1: Query Structure Profile**
- ✅ Comprehensive join analysis (distribution, types, patterns)
- ✅ Detailed subquery/CTE breakdown (depth, location, complexity)
- ✅ Set operations coverage
- ✅ Aggregation patterns and function usage
- ✅ Window function analysis (rare feature spotlight)
- ✅ Filtering and predicate analysis
- ✅ Cross-feature correlations
- ✅ Quality indicators and antipatterns
- ✅ Dataset health summary with recommendations

**Report 2: Table Coverage**
- ✅ Database-level coverage metrics
- ✅ Per-table usage frequency distribution
- ✅ Per-database coverage ranking
- ✅ Unused table identification and categorization
- ✅ High-usage table analysis (hot spots)
- ✅ Foreign key relationship coverage
- ✅ Coverage by query complexity correlation
- ✅ Coverage gaps and actionable recommendations
- ✅ Cross-split consistency checks

**Report 3: Combined Analysis**
- ✅ Structure × coverage correlations
- ✅ Optimization roadmap
- ✅ Phased improvement plan

### Key Improvements Over Original Example

1. **More Granular Breakdowns**: Added subcategories (e.g., A1, A2, A3, A4 for joins)
2. **Cross-Split Analysis**: Distribution consistency checks across train/val/test
3. **Actionable Insights**: Specific recommendations with priority levels
4. **Visual Elements**: ASCII histograms and heatmaps for quick scanning
5. **Correlation Analysis**: How features relate to each other and coverage
6. **Quality Indicators**: Best practices vs antipatterns
7. **Comprehensive Coverage**: Table usage from multiple angles (frequency, relationships, complexity)
8. **Roadmap**: Clear next steps for dataset improvement

---

## 📊 Next Steps

**For Review:**
1. ✅ Review proposed report structure
2. ✅ Prioritize which sections are must-haves vs nice-to-haves
3. ✅ Confirm metrics and thresholds
4. ✅ Approve implementation approach

**After Approval:**
1. ⚙️ Implement new analyzer components
2. ⚙️ Extend DuckDB schema
3. ⚙️ Build report generator methods
4. ⚙️ Add CLI commands
5. ✅ Test with sample datasets
6. 📄 Generate sample reports for validation

---

**Questions? Feedback?** Let me know which sections to prioritize or if you'd like any modifications!

