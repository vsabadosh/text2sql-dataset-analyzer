# Query Quality Report

**Generated:** 2025-11-03 02:41:34

## Summary

- **Total Queries:** 2,147 · **Analyzed:** 2,147 · **Skipped:** 0
- **Avg Quality Score:** 92.7/100 · **Avg Antipatterns:** 1.3

## K) Quality Indicators

### K1) Antipatterns Detected

| Antipattern | Count | Share | Severity |
|-------------|-------|-------|----------|
| SELECT * | 673 | 31.3% | ⚠️ Medium |
| Implicit JOIN | 0 | 0.0% | ⚠️ Medium |
| Functions in WHERE | 81 | 3.8% | ⚠️ Medium |
| Correlated subquery | 46 | 2.1% | ⚠️ Medium |
| Unbounded SELECT (no LIMIT) | 1,816 | 84.6% | 🔴 High |

**Summary:** Avg quality score: 92.7/100 · Avg antipatterns per query: 1.3

### K2) Unparseable Queries

✅ **All queries are parseable!**
