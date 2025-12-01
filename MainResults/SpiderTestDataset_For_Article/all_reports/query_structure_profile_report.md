# Query Structure Profile Report

**Generated:** 2025-11-03 02:41:34

**Total Queries Analyzed:** 2,147

## A) Joins Analysis

### A1) Joins per Query Distribution

| Joins per query | Count | Share |
|----------------|-------|-------|
| 0 (single-table) | 1,285 | 59.85% |
| 1 join | 558 | 25.99% |
| 2 joins | 242 | 11.27% |
| 3 joins | 38 | 1.77% |
| 4 joins | 22 | 1.02% |
| 6 joins | 2 | 0.09% |
| **Total** | **2,147** | **100%** |

### A2) Join Type Distribution

*(for queries with ≥1 join)*

| Join type | Queries using | Share of joined queries | Share of all queries |
|-----------|--------------|------------------------|---------------------|
| INNER (implicit/explicit) | 1,256 | 145.7% | 58.5% |

## B) Subqueries & CTEs

### B1) Subquery Presence & Depth

| Feature | Count | Share | Notes |
|---------|-------|-------|-------|
| Has ≥1 subquery | 175 | 8.15% | At least one subquery |
| Has correlated subquery | 175 | 8.15% | Uses outer reference (EXISTS/IN) |
| Has nested subquery (depth ≥2) | 0 | 0.0% | Subquery within subquery |
| Max depth = 1 | 175 | 8.15% | Simple subqueries only |

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
| COUNT | 750 | 34.9% | 70.9% |
| SUM | 80 | 3.7% | 7.6% |
| AVG | 162 | 7.5% | 15.3% |
| MAX | 86 | 4.0% | 8.1% |
| MIN | 63 | 2.9% | 6.0% |

### D3) Aggregation Complexity

| Pattern | Count | Share | Description |
|---------|-------|-------|-------------|
| Single aggregate | 911 | 42.4% | One aggregate function |
| Multiple aggregates | 147 | 6.8% | 2+ aggregate functions |
| Nested aggregation | 119 | 5.5% | Aggregate of aggregate (subquery) |
| HAVING without GROUP BY | 0 | 0.0% | Rare pattern |
| DISTINCT with GROUP BY | 22 | 1.0% | Redundant pattern |

## I) Query Complexity Distribution

### I1) Difficulty Levels

| Difficulty | Count | Share | Complexity Score Range |
|------------|-------|-------|----------------------|
| Easy | 516 | 24.0% | 10-29 |
| Medium | 1,246 | 58.0% | 30-59 |
| Hard | 385 | 17.9% | 60-79 |

### I2) Feature Density

*(avg features per query by difficulty)*

| Difficulty | Avg Tables | Avg Joins | Avg Subqueries | Avg Aggregates | Avg Complexity |
|------------|-----------|-----------|----------------|----------------|----------------|
| Easy | 1.0 | 0.0 | 0.0 | 0.0 | 10.0 |
| Medium | 1.7 | 0.7 | 0.0 | 0.7 | 41.4 |
| Hard | 2.0 | 1.0 | 0.5 | 0.8 | 72.6 |

## J) Cross-Feature Analysis

### J1) Feature Combinations

*(top 10 most common)*

| Rank | Combination | Count | Share |
|------|-------------|-------|-------|
| 1 | JOIN + GROUP BY + ORDER BY | 131 | 6.1% |
| 2 | JOIN + WHERE + AGGREGATE | 121 | 5.6% |
| 3 | Subquery + WHERE + IN | 85 | 4.0% |
| 4 | Multiple JOINs + AGGREGATE | 84 | 3.9% |
| 5 | WHERE + ORDER BY + LIMIT | 56 | 2.6% |
| 6 | HAVING + GROUP BY + Subquery | 12 | 0.6% |
| 7 | UNION + ORDER BY | 6 | 0.3% |

## L) Dataset Health Summary

### Overall Metrics

- **Total Queries:** 2,147
- **Parseable:** 2,147 (100.0%)
- **Avg Complexity:** 39.5/100
- **Median Complexity:** 41
- **Std Dev:** 20.2

### Balance Indicators

| Metric | Status | Notes |
|--------|--------|-------|
| Difficulty distribution | ✅ Good | Reasonable spread across levels |
| Single vs multi-table | ⚠️ Fair | 42.9% use joins |
| Simple vs advanced features | ⚠️ Fair | Window functions: 0.0% |
| Split consistency | ✅ Good | <5% variance across splits |

### Recommendations

1. ⚠️ **Review** join distribution (57.1% single-table)
2. ⚠️ **Underrepresented**: Window functions (0.0%), Recursive CTEs (0.0%)
3. ✅ **Good**: Set operations coverage (8.4%)
4. ✅ **Good coverage**: Subqueries (8.2%), Aggregations (49.3%)
