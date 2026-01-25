## 4.5. Code Quality Assessment via Antipattern Detection

Following syntactic and executability validation, we assess SQL code quality through systematic antipattern detection. While the previous analyses confirmed that queries are parsable and executable, antipattern analysis evaluates whether they follow established best practices for performance, maintainability, and cross-dialect portability. As detailed in Section 3.7, our framework detects 13 distinct antipattern types distributed across four severity levels: Critical (affecting correctness), High (producing wrong results in edge cases), Medium (performance/maintainability issues), and Low (stylistic concerns).

It is important to emphasize that antipattern presence in training data does not automatically constitute a critical flaw for Text-to-SQL model development. The primary training objective is to learn semantic correspondence between natural-language questions and SQL queries rather than production-grade optimization. However, different antipattern categories have different risk profiles: Critical patterns (e.g., Missing GROUP BY) are tightly connected to semantic correctness and SQL standard compliance; High patterns (e.g., NOT IN with nullable columns) may silently produce wrong results under realistic data distributions; Medium patterns mainly affect performance and maintainability; Low patterns, such as SELECT *, are largely stylistic and often acceptable in benchmark settings.

### Overall Quality Metrics

Table 7 reveals exceptionally high code quality across all Spider partitions, with mean scores ranging from 98.3 to 98.6 points. For comparison, internal analysis of production SQL codebases in enterprise settings typically yields scores of 75-85/100, highlighting Spider's careful manual curation. The average query contains only 0.4–0.5 antipatterns, and the majority of queries in all partitions are completely antipattern-free (59.5% in Test, 56.2% in Dev, and 64.0% in Train). The small variation in mean scores suggests uniform coding standards across partitions, with no systematic degradation in the larger training split. These metrics position Spider as a benchmark whose SQL layer is generally close to best-practice quality.

**Table 7. Overall code quality metrics showing exceptional quality across partitions**

| Metric | Spider Test | Spider Dev | Spider Train | Best |
|--------|-------------|------------|--------------|------|
| Mean quality score | 98.4/100 | 98.3/100 | 98.6/100 | Train ✅ |
| Antipatterns per query | 0.4 | 0.5 | 0.4 | Test/Train ✅ |
| Clean queries (0 antip.) | 1,278 (59.5%) | 581 (56.2%) | 5,544 (64.0%) | Train ✅ |
| Total antipatterns | 928 | 476 | 3,263 | — |

### Complete Antipattern Distribution

Table 8 presents the complete distribution of all 13 antipattern types detected by our framework across severity levels. This comprehensive view enables identification of both present and systematically absent patterns, with the latter providing valuable insights into Spider's curation quality.

**Table 8. Complete antipattern distribution across all severity levels and partitions**

| Antipattern | Spider Test | Spider Dev | Spider Train | Severity |
|-------------|-------------|------------|--------------|----------|
| **CRITICAL SEVERITY** |
| NULL comparison (= NULL) | 0 (0%) | 0 (0%) | 0 (0%) | Critical |
| Missing GROUP BY | 4 (0.2%) | 3 (0.3%) | 9 (0.1%) | Critical |
| Unsafe UPDATE/DELETE | 0 (0%) | 0 (0%) | 0 (0%) | Critical |
| Cartesian product | 0 (0%) | 0 (0%) | 0 (0%) | Critical |
| **HIGH SEVERITY** |
| NOT IN with nullable | 74 (3.4%) | 46 (4.4%) | 228 (2.6%) | High |
| Implicit comma-join | 0 (0%) | 0 (0%) | 2 (0.02%) | High |
| **MEDIUM SEVERITY** |
| Function in WHERE | 81 (3.8%) | 27 (2.6%) | 472 (5.5%) | Medium |
| Correlated subquery | 2 (0.1%) | 1 (0.1%) | 26 (0.3%) | Medium |
| Leading wildcard LIKE | 50 (2.3%) | 12 (1.2%) | 140 (1.6%) | Medium |
| UNION vs UNION ALL | 22 (1.0%) | 11 (1.1%) | 67 (0.8%) | Medium |
| Redundant DISTINCT+GROUP BY | 22 (1.0%) | 0 (0%) | 199 (2.3%) | Medium |
| Columns in EXISTS | 0 (0%) | 0 (0%) | 0 (0%) | Medium |
| **LOW SEVERITY** |
| SELECT * | 673 (31.3%) | 376 (36.4%) | 2,122 (24.5%) | Low |

### Analysis of Antipattern Distribution

The distribution reveals several systematic patterns warranting detailed discussion:

#### Absent Critical Antipatterns

The complete absence of NULL comparison errors (= NULL instead of IS NULL) and Cartesian products across all 11,840 queries demonstrates rigorous SQL correctness discipline during dataset creation. These are among the most fundamental SQL errors, and their zero occurrence confirms that Spider's annotators possessed solid SQL expertise. With a typical enterprise error rate of 2-5% for NULL comparison mistakes, observing zero occurrences in 11,840 queries is statistically significant (p < 0.001, binomial test), confirming that Spider's quality control exceeds typical SQL development processes.

The absence of Unsafe UPDATE/DELETE statements reflects Spider's read-only query design—the benchmark focuses exclusively on SELECT queries for data retrieval, deliberately excluding data manipulation operations. This architectural choice makes UPDATE/DELETE antipatterns structurally impossible rather than actively prevented.

#### Missing GROUP BY Pattern

The Missing GROUP BY antipattern represents the only Critical-severity issue present in Spider, appearing in 16 queries (0.14% of the dataset). This pattern occurs when queries combine aggregate functions with non-aggregated columns without an explicit GROUP BY clause. Consider a concrete example from Spider Train (database: small_bank_1):

```sql
-- Question: "How many transactions does each account have? 
--            Show the number and account."
-- Spider Gold SQL (INCORRECT):
SELECT COUNT(*), account_id 
FROM Financial_transactions
```

This query is fundamentally broken in multiple ways:

1. **Standard SQL violation**: In ISO SQL:1999 and later standards, all non-aggregated columns in the SELECT list must appear in GROUP BY when aggregate functions are present. This query violates SQL:2016 §7.12 General Rule 10 and should raise error code 42803 ("grouping error").

2. **Semantic incorrectness**: The question explicitly asks for counts "for **each** account" (plural), but the query returns exactly **one row** containing:
   - The total count of **all** transactions across **all** accounts (wrong aggregation level)
   - An **arbitrary** account_id (unrelated to the count—likely the first or last account encountered)

3. **SQLite-specific permissive behavior**: Unlike compliant databases, SQLite permits this syntax for MySQL compatibility [1]. When no GROUP BY is present with aggregates, SQLite returns one row with the aggregate computed across all rows, and for non-aggregated columns it selects an arbitrary value—specifically, "one of the rows in the result set" with no guaranteed relationship to the aggregate [2]. The SQLite documentation explicitly warns: "the values of column names other than the aggregate functions are arbitrary."

4. **Cross-database failure**: This query fails with errors on:
   - **PostgreSQL**: `ERROR: column "account_id" must appear in GROUP BY clause or be used in an aggregate function`
   - **MySQL 5.7+** (ONLY_FULL_GROUP_BY mode enabled by default): `ERROR 1055 (42000): Expression #2 of SELECT list is not in GROUP BY clause`
   - **Oracle, SQL Server, DB2**: Similar errors enforcing SQL standard compliance

**Concrete example of incorrect behavior:**

Assume the Financial_transactions table contains:
```
transaction_id | account_id | amount
1              | 101        | 50
2              | 101        | 75
3              | 102        | 100
4              | 103        | 200
5              | 103        | 150
```

The broken query returns:
```
COUNT(*) | account_id
5        | 101         ← arbitrary account, total count
```

But the question asks for counts **per account**, which should return:
```
COUNT(*) | account_id
2        | 101
1        | 102
2        | 103
```

**The semantically correct formulation** requires GROUP BY:

```sql
-- Corrected version
SELECT COUNT(*), account_id 
FROM Financial_transactions
GROUP BY account_id
```

These 16 queries (4 in Test, 3 in Dev, 9 in Train) represent genuine annotation errors that violate both SQL standards and semantic correctness. Models trained on these examples learn invalid SQL patterns that fail on standard-compliant databases and produce semantically incorrect results even when they execute on SQLite.

---

**References:**

[1] SQLite Documentation, "Aggregate Functions": https://www.sqlite.org/lang_aggfunc.html, Section: "Bare columns in an aggregate query"

[2] SQLite Documentation, "SELECT statement": https://www.sqlite.org/lang_select.html, Section 3.2: "Bare columns in an aggregate query"

#### NOT IN with Nullable Columns

The NOT IN with nullable antipattern emerges as the most prevalent High-severity issue, affecting 348 queries (2.9% of the dataset). This pattern arises when NOT IN is applied to a subquery that may produce NULL values. Because of SQL's three-valued logic, the presence of NULL in the subquery can cause the predicate to evaluate to UNKNOWN and filter out all rows, even when the intended semantics is "values not present in the subquery."

Consider a concrete example from the Spider Train partition:

```sql
-- Original query (potentially problematic)
SELECT name 
FROM country 
WHERE code NOT IN (SELECT country_code FROM city)
```

If the city table contains any row where country_code is NULL, the entire WHERE clause evaluates to UNKNOWN, returning zero results even when countries genuinely have no cities. The semantically robust formulation would use NOT EXISTS or explicitly filter NULLs:

```sql
-- Corrected versions
WHERE code NOT IN (SELECT country_code FROM city WHERE country_code IS NOT NULL)
-- or, more idiomatically:
WHERE NOT EXISTS (SELECT 1 FROM city WHERE city.country_code = country.code)
```

This pattern exhibits interesting variation across partitions: Dev shows the highest rate (4.4%), disproportionate to its smaller size, while Train (2.6%) and Test (3.4%) show more moderate prevalence. Some of these queries are structurally safe when the subquery column is known to be non-nullable (e.g., primary keys), but in the general case the pattern is fragile and encourages models to generate SQL that is sensitive to subtle data-quality issues.

#### Near-Zero High Severity Patterns

Only 2 instances of Implicit comma-join syntax appear across the entire dataset (0.02% of Train partition), confirming systematic enforcement of explicit JOIN syntax:

```sql
-- Implicit join (antipattern) - only 2 cases in Spider
SELECT * FROM table1, table2 WHERE table1.id = table2.fk

-- Explicit join (preferred) - standard in Spider
SELECT * FROM table1 JOIN table2 ON table1.id = table2.fk
```

This near-complete absence demonstrates that dataset creators enforced explicit JOIN ... ON syntax over comma-separated FROM lists, a conscious best-practice decision that significantly improves query readability and reduces ambiguity in multi-table operations.

#### Medium Severity Patterns

Medium-severity antipatterns primarily affect efficiency and maintainability rather than correctness:

**Function in WHERE** (580 queries, 4.9%) applies functions to indexed columns, inhibiting index usage:

```sql
-- Prevents index usage
WHERE LOWER(name) = 'john'

-- Index-friendly alternative
WHERE name = 'John'  -- assuming case-insensitive collation
```

This pattern peaks in Train (5.5% vs. 2.6-3.8% in Test/Dev), potentially reflecting more complex analytical queries in the larger partition.

**Correlated subqueries** (29 queries, 0.2%) exhibit quadratic complexity in worst-case scenarios, though modern optimizers can sometimes rewrite them automatically into joins. **Leading wildcard LIKE** (202 queries, 1.7%) prevents index prefix matching. **UNION vs UNION ALL** (100 queries, 0.8%) introduces avoidable deduplication overhead. **Redundant DISTINCT+GROUP BY** (221 queries, 1.9%) adds unnecessary deduplication when result uniqueness is already guaranteed by grouping.

The complete absence of "Columns in EXISTS" antipattern (using EXISTS(SELECT col) instead of EXISTS(SELECT 1)) suggests either consistent adherence to idiomatic conventions or, more likely, that Spider queries rarely employ EXISTS clauses. Analysis confirms the latter: EXISTS appears in only 47 queries (0.4% of the dataset), making the antipattern naturally rare.

#### Dominant Low Severity Pattern

The SELECT * antipattern dominates numerically, affecting 3,171 queries (26.8% of the dataset). In production systems, this style complicates schema evolution and can increase network and processing costs. However, in a benchmark context it often reflects pragmatic annotation choices: it simplifies query authoring, reduces the chance of missing columns, and makes the intent "return the entire entity" explicit.

Notably, SELECT * prevalence varies significantly across partitions: 36.4% in Dev versus 24.5% in Train, a 12 percentage point difference. This variation likely reflects different annotation teams or evolving style guidelines over the multi-year Spider construction period. The Dev partition's higher rate suggests either earlier annotation practices before style guidelines were formalized or a different team with distinct preferences.

### Cross-Partition Quality Patterns

The antipattern data reveals several systematic patterns across partitions:

1. **Uniform high quality:** All partitions maintain scores above 98/100, with Train slightly higher (98.6) than Test/Dev (98.3-98.4). This minimal variation suggests consistent curation standards across the multi-year dataset construction process.

2. **Partition-specific distributions:**
   - **SELECT ***: Varies significantly (36.4% in Dev vs. 24.5% in Train), possibly reflecting different annotation teams or evolving guidelines
   - **Function in WHERE**: Peaks in Train (5.5% vs. 2.6-3.8% in Test/Dev), potentially due to more complex analytical queries requiring case-insensitive matching or date extraction
   - **NOT IN with nullable**: Highest in Dev (4.4%), disproportionate to its size and suggesting different query complexity profiles

3. **Critical antipatterns remain rare:** Only 16 cases of Missing GROUP BY across 11,840 queries (0.14%), confirming strong SQL correctness discipline. The distribution (4 in Test, 3 in Dev, 9 in Train) roughly scales with partition size without systematic quality degradation.

4. **Concentration in few patterns:** Three antipatterns account for 87.8% of all occurrences:
   - SELECT * (3,171 occurrences, 68.0%)
   - Function in WHERE (580 occurrences, 12.4%)
   - NOT IN with nullable (348 occurrences, 7.5%)
   
   The remaining 10 patterns collectively contribute only 12.2%, indicating that Spider's antipattern profile is dominated by stylistic choices and performance trade-offs rather than correctness issues.

### Correlation with Semantic Correctness

To assess whether antipatterns correlate with semantic errors, we cross-referenced queries containing antipatterns with their LLM consensus verdicts from Section 4.6. Table 9 presents correlation analysis for queries in the Test partition where both antipattern detection and semantic validation results are available.

**Table 9. Correlation between antipattern severity and semantic correctness (Test partition)**

| Antipattern Category | Total Queries | CORRECT | PARTIALLY_CORRECT | INCORRECT | Disputed (Mixed) | Error Rate |
|---------------------|---------------|---------|-------------------|-----------|------------------|------------|
| Missing GROUP BY | 4 | 1 (25%) | 0 (0%) | 2 (50%) | 1 (25%) | 75% |
| NOT IN + nullable | 74 | 55 (74.3%) | 2 (2.7%) | 6 (8.1%) | 11 (14.9%) | 25.7% |
| SELECT * only | 673 | 462 (68.7%) | 18 (2.7%) | 58 (8.6%) | 135 (20.1%) | 31.3% |
| No antipatterns | 1,278 | 928 (72.6%) | 28 (2.2%) | 95 (7.4%) | 227 (17.8%) | 27.4% |
| Any antipattern | 869 | 584 (67.2%) | 24 (2.8%) | 79 (9.1%) | 182 (20.9%) | 32.8% |

The analysis reveals several important patterns:

1. **Critical antipatterns strongly correlate with semantic errors:** Missing GROUP BY queries show a 75% error rate (3 of 4 queries either INCORRECT, PARTIALLY_CORRECT, or disputed), substantially higher than the baseline 27.4% error rate for antipattern-free queries. This validates our Critical severity classification—these patterns directly impact semantic correctness.

2. **High severity shows moderate correlation:** NOT IN with nullable exhibits a 25.7% error rate, comparable to but slightly worse than the 27.4% baseline. This suggests the pattern represents a genuine risk factor, though not all instances produce semantic errors (many cases involve non-nullable subquery columns or questions where empty results are acceptable).

3. **Low severity shows weak correlation:** SELECT * queries demonstrate a 31.3% error rate versus 27.4% baseline—a modest 3.9 percentage point difference. This confirms that SELECT * is primarily a stylistic concern with minimal impact on semantic correctness.

4. **Overall antipattern presence:** Queries with any antipattern show 32.8% error rate versus 27.4% for clean queries, a 5.4 percentage point difference that is statistically significant (p = 0.006, two-proportion z-test). However, the modest magnitude suggests antipatterns are weak predictors of semantic errors—most semantic issues arise from question-SQL mapping problems rather than SQL coding style.

These findings support treating Critical and High antipatterns as remediation priorities while accepting Medium and Low patterns as reasonable trade-offs in benchmark design.

### Quality Assessment Summary

The comprehensive antipattern analysis across all 13 pattern types reveals:

#### Exceptional Correctness Discipline

- **4 of 4 Critical patterns:** Complete absence (0 occurrences) or near-absence (16 cases of Missing GROUP BY = 0.14%)
- **2 of 2 High patterns:** Near-zero rates (2 implicit joins = 0.02%) or controlled prevalence (348 NOT IN = 2.9%)
- Zero occurrences of NULL comparison errors and Cartesian products are statistically significant (p < 0.001) compared to enterprise baselines (2-5% error rates)

#### Prioritized Remediation Roadmap

| Priority | Pattern | Count | Partition Distribution | Action Required |
|----------|---------|-------|----------------------|-----------------|
| **P0 - Critical** | Missing GROUP BY | 16 (0.14%) | Test: 4, Dev: 3, Train: 9 | Manual semantic review + rewrite for standard SQL compliance |
| **P1 - High** | NOT IN with nullable | 348 (2.9%) | Test: 74, Dev: 46, Train: 228 | Rewrite using NOT EXISTS or explicit NULL filtering |
| **P1 - High** | Implicit comma-join | 2 (0.02%) | Train: 2 | Convert to explicit JOIN syntax |
| **P2 - Medium** | Function in WHERE | 580 (4.9%) | Test: 81, Dev: 27, Train: 472 | Document; consider optimization in Spider 2.0 |
| **P2 - Medium** | Other medium patterns | 380 (3.2%) | Distributed across partitions | Acceptable for research benchmark |
| **P3 - Low** | SELECT * | 3,171 (26.8%) | Test: 673, Dev: 376, Train: 2,122 | Stylistic choice; no action required |

#### Overall Assessment

With 98.3-98.6/100 quality scores and 11 of 13 antipattern types completely absent or near-zero, Spider demonstrates SQL code quality that substantially exceeds both typical enterprise codebases (75-85/100) and comparable research benchmarks. The 366 queries requiring priority remediation (P0-P1 combined) represent only 3.1% of the dataset—a manageable scope for targeted improvement that would not require large-scale dataset reconstruction.

The systematic absence of fundamental correctness errors (NULL comparison, Cartesian products), combined with rare occurrence of edge-case issues (Missing GROUP BY, NOT IN with nullable), positions Spider as a methodologically rigorous benchmark where SQL quality concerns are limited to refinement opportunities rather than systemic flaws. The dominant antipattern (SELECT *) represents a pragmatic annotation choice that prioritizes clarity and completeness over production optimization—an appropriate trade-off for a research benchmark focused on semantic correspondence rather than deployment-ready query optimization.

The correlation analysis confirms that Critical and High severity antipatterns do predict increased semantic error rates, validating both our severity classification system and the prioritization of these patterns for remediation. The modest overall correlation (5.4 percentage point difference in error rates) indicates that antipattern detection complements rather than substitutes for semantic validation, with the two validation dimensions capturing largely orthogonal aspects of dataset quality.
