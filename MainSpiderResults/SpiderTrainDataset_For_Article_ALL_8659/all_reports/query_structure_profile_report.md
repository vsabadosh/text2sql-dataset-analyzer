# Query Structure Profile Report

**Generated:** 2026-03-17 11:33:57

**Total Queries Analyzed:** 8,659

## A) Joins Analysis

### A1) Joins per Query Distribution

| Joins per query | Count | Share |
|----------------|-------|-------|
| 0 (single-table) | 4,847 | 55.98% |
| 1 join | 2,233 | 25.79% |
| 2 joins | 1,042 | 12.03% |
| 3 joins | 359 | 4.15% |
| 4 joins | 154 | 1.78% |
| 5 joins | 16 | 0.18% |
| 6 joins | 6 | 0.07% |
| 7+ joins | 2 | 0.02% |
| **Total** | **8,659** | **100%** |

### A2) Join Type Distribution

*(for queries with ≥1 join)*

| Join type | Queries using | Share of joined queries | Share of all queries |
|-----------|--------------|------------------------|---------------------|
| INNER (implicit/explicit) | 6,142 | 161.1% | 70.9% |

## B) Subqueries & CTEs

### B1) Subquery Presence & Depth

| Feature | Count | Share | Notes |
|---------|-------|-------|-------|
| Has ≥1 subquery | 852 | 9.84% | At least one subquery |
| Has correlated subquery | 846 | 9.77% | Uses outer reference (EXISTS/IN) |
| Has nested subquery (depth ≥2) | 66 | 0.76% | Subquery within subquery |
| Max depth = 1 | 786 | 9.08% | Simple subqueries only |
| Max depth = 2 | 54 | 0.62% | Two-level nesting |
| Max depth ≥ 3 | 12 | 0.14% | Deep nesting (complex) |

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
| COUNT | 2,753 | 31.8% | 69.1% |
| SUM | 289 | 3.3% | 7.3% |
| AVG | 504 | 5.8% | 12.6% |
| MAX | 443 | 5.1% | 11.1% |
| MIN | 246 | 2.8% | 6.2% |

### D3) Aggregation Complexity

| Pattern | Count | Share | Description |
|---------|-------|-------|-------------|
| Single aggregate | 3,499 | 40.4% | One aggregate function |
| Multiple aggregates | 487 | 5.6% | 2+ aggregate functions |
| Nested aggregation | 601 | 6.9% | Aggregate of aggregate (subquery) |
| DISTINCT with GROUP BY | 199 | 2.3% | Redundant pattern |

## I) Query Complexity Distribution

### I1) Difficulty Levels

| Difficulty | Count | Share | Complexity Score Range |
|------------|-------|-------|----------------------|
| Easy | 2,039 | 23.5% | 10-29 |
| Medium | 4,827 | 55.7% | 30-59 |
| Hard | 1,727 | 19.9% | 60-79 |
| Expert | 66 | 0.8% | 80-100 |

### I2) Feature Density

*(avg features per query by difficulty)*

| Difficulty | Avg Tables | Avg Joins | Avg Subqueries | Avg Aggregates | Avg Complexity |
|------------|-----------|-----------|----------------|----------------|----------------|
| Easy | 1.0 | 0.0 | 0.0 | 0.0 | 10.0 |
| Medium | 1.8 | 0.8 | 0.0 | 0.7 | 41.4 |
| Hard | 2.3 | 1.3 | 0.5 | 0.8 | 72.7 |
| Expert | 2.1 | 0.2 | 2.8 | 1.3 | 95.3 |

## J) Cross-Feature Analysis

### J1) Feature Combinations

*(top 10 most common)*

| Rank | Combination | Count | Share |
|------|-------------|-------|-------|
| 1 | JOIN + WHERE + AGGREGATE | 887 | 10.2% |
| 2 | Multiple JOINs + AGGREGATE | 525 | 6.1% |
| 3 | JOIN + GROUP BY + ORDER BY | 517 | 6.0% |
| 4 | Subquery + WHERE + IN | 378 | 4.4% |
| 5 | WHERE + ORDER BY + LIMIT | 176 | 2.0% |
| 6 | HAVING + GROUP BY + Subquery | 12 | 0.1% |
| 7 | UNION + ORDER BY | 4 | 0.0% |

## L) Dataset Health Summary

### Overall Metrics

- **Total Queries:** 8,659
- **Parseable:** 8,659 (100.0%)
- **Avg Complexity:** 40.7/100
- **Median Complexity:** 41
- **Std Dev:** 21.2

### Balance Indicators

| Metric | Status | Notes |
|--------|--------|-------|
| Difficulty distribution | ✅ Good | Reasonable spread across levels |
| Single vs multi-table | ⚠️ Fair | 48.8% use joins |
| Simple vs advanced features | ⚠️ Fair | Window functions: 0.0% |
| Split consistency | ✅ Good | <5% variance across splits |

### Recommendations

1. ⚠️ **Review** join distribution (51.2% single-table)
2. ⚠️ **Underrepresented**: Window functions (0.0%), Recursive CTEs (0.0%)
3. ✅ **Good**: Set operations coverage (6.1%)
4. ✅ **Good coverage**: Subqueries (9.8%), Aggregations (46.0%)
