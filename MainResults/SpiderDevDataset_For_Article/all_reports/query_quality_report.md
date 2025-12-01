# Query Quality Report

**Generated:** 2025-11-10 18:21:06

## Summary

- **Total Queries:** 1,034 · **Analyzed:** 1,034 · **Skipped:** 0
- **Avg Quality Score:** 92.7/100 · **Avg Antipatterns:** 1.3

## K) Quality Indicators

### K1) Antipatterns Detected

| Antipattern | Count | Share | Severity |
|-------------|-------|-------|----------|
| SELECT * | 376 | 36.4% | ⚠️ Medium |
| Implicit JOIN | 0 | 0.0% | ⚠️ Medium |
| Functions in WHERE | 27 | 2.6% | ⚠️ Medium |
| Correlated subquery | 21 | 2.0% | ⚠️ Medium |
| Unbounded SELECT (no LIMIT) | 845 | 81.7% | 🔴 High |

**Summary:** Avg quality score: 92.7/100 · Avg antipatterns per query: 1.3

### K2) Unparseable Queries

✅ **All queries are parseable!**
