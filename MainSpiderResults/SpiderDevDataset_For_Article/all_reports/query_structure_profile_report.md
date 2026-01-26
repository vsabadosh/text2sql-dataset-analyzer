# Query Structure Profile Report

**Generated:** 2025-11-10 18:21:06

**Total Queries Analyzed:** 1,034

## A) Joins Analysis

### A1) Joins per Query Distribution

| Joins per query | Count | Share |
|----------------|-------|-------|
| 0 (single-table) | 626 | 60.54% |
| 1 join | 320 | 30.95% |
| 2 joins | 72 | 6.96% |
| 3 joins | 10 | 0.97% |
| 4 joins | 6 | 0.58% |
| **Total** | **1,034** | **100%** |

### A2) Join Type Distribution

*(for queries with ≥1 join)*

| Join type | Queries using | Share of joined queries | Share of all queries |
|-----------|--------------|------------------------|---------------------|
| INNER (implicit/explicit) | 518 | 127.0% | 50.1% |

## B) Subqueries & CTEs

### B1) Subquery Presence & Depth

| Feature | Count | Share | Notes |
|---------|-------|-------|-------|
| Has ≥1 subquery | 83 | 8.03% | At least one subquery |
| Has correlated subquery | 83 | 8.03% | Uses outer reference (EXISTS/IN) |
| Has nested subquery (depth ≥2) | 0 | 0.0% | Subquery within subquery |
| Max depth = 1 | 83 | 8.03% | Simple subqueries only |

### B3) Common Table Expressions (WITH)

| Feature | Count | Share | Median CTEs when present |
|---------|-------|-------|-------------------------|
| Has ≥1 CTE | 0 | 0.0% | 0 |
| Has multiple CTEs (≥2) | 0 | 0.0% | 0 |
| Has 3+ CTEs | 0 | 0.0% | 0 |
| Has recursive CTE | 0 | 0.0% | — |

## D) Aggregation & Grouping

### D2) Aggregate Function Usage

| Function | Count | Share of all queries | Share of agg queries |
|----------|-------|---------------------|---------------------|
| COUNT | 412 | 39.8% | 74.8% |
| SUM | 35 | 3.4% | 6.4% |
| AVG | 67 | 6.5% | 12.2% |
| MAX | 42 | 4.1% | 7.6% |
| MIN | 27 | 2.6% | 4.9% |

### D3) Aggregation Complexity

| Pattern | Count | Share | Description |
|---------|-------|-------|-------------|
| Single aggregate | 503 | 48.6% | One aggregate function |
| Multiple aggregates | 48 | 4.6% | 2+ aggregate functions |
| Nested aggregation | 56 | 5.4% | Aggregate of aggregate (subquery) |
| HAVING without GROUP BY | 0 | 0.0% | Rare pattern |
| DISTINCT with GROUP BY | 0 | 0.0% | Redundant pattern |

## I) Query Complexity Distribution

### I1) Difficulty Levels

| Difficulty | Count | Share | Complexity Score Range |
|------------|-------|-------|----------------------|
| Easy | 250 | 24.2% | 10-29 |
| Medium | 612 | 59.2% | 30-59 |
| Hard | 172 | 16.6% | 60-79 |

### I2) Feature Density

*(avg features per query by difficulty)*

| Difficulty | Avg Tables | Avg Joins | Avg Subqueries | Avg Aggregates | Avg Complexity |
|------------|-----------|-----------|----------------|----------------|----------------|
| Easy | 1.0 | 0.0 | 0.0 | 0.0 | 10.0 |
| Medium | 1.6 | 0.6 | 0.0 | 0.7 | 41.4 |
| Hard | 1.9 | 0.8 | 0.5 | 0.9 | 72.6 |

## J) Cross-Feature Analysis

### J1) Feature Combinations

*(top 10 most common)*

| Rank | Combination | Count | Share |
|------|-------------|-------|-------|
| 1 | JOIN + WHERE + AGGREGATE | 86 | 8.3% |
| 2 | JOIN + GROUP BY + ORDER BY | 71 | 6.9% |
| 3 | Subquery + WHERE + IN | 50 | 4.8% |
| 4 | WHERE + ORDER BY + LIMIT | 26 | 2.5% |
| 5 | Multiple JOINs + AGGREGATE | 23 | 2.2% |
| 6 | HAVING + GROUP BY + Subquery | 2 | 0.2% |

## L) Dataset Health Summary

### Overall Metrics

- **Total Queries:** 1,034
- **Parseable:** 1,034 (100.0%)
- **Avg Complexity:** 39.0/100
- **Median Complexity:** 41
- **Std Dev:** 19.9

### Balance Indicators

| Metric | Status | Notes |
|--------|--------|-------|
| Difficulty distribution | ✅ Good | Reasonable spread across levels |
| Single vs multi-table | ⚠️ Fair | 44.4% use joins |
| Simple vs advanced features | ⚠️ Fair | Window functions: 0.0% |
| Split consistency | ✅ Good | <5% variance across splits |

### Recommendations

1. ⚠️ **Review** join distribution (55.6% single-table)
2. ⚠️ **Underrepresented**: Window functions (0.0%), Recursive CTEs (0.0%)
3. ✅ **Good**: Set operations coverage (7.7%)
4. ✅ **Good coverage**: Subqueries (8.0%), Aggregations (53.3%)
