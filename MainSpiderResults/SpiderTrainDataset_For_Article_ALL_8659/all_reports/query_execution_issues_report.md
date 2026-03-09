# Query Execution Detailed Report

**Generated:** 2026-03-09 11:51:53

## Summary

- **Total Executions:** 8,659 · **Analyzed:** 8,659 · **Skipped:** 0
- **Failures:** 3 (0.0%)

## Failed Items (3)

| Item ID | DB | Error |
|---------|----|-------|
| 3154 | assets_maintenance | Execution error: (sqlite3.OperationalError) no such table: Ref_Company_Types
[SQL: SELECT T1.company_name FROM Third_Party_Companies AS T1 JOIN Maintenance_Contracts AS T2 ON T1.company_id  =  T2.maintenance_contract_company_id JOIN Ref_Company_Types AS T3 ON T1.company_type_code  =  T3.company_type_code ORDER BY T2.contract_end_date DESC LIMIT 1]
(Background on this error at: https://sqlalche.me/... |
| 4514 | document_management | Execution error: (sqlite3.OperationalError) ORDER BY clause should come after INTERSECT not before
[SQL: SELECT document_name FROM documents GROUP BY document_type_code ORDER BY count(*) DESC LIMIT 3 INTERSECT SELECT document_name FROM documents GROUP BY document_structure_code ORDER BY count(*) DESC LIMIT 3]
(Background on this error at: https://sqlalche.me/e/20/e3q8) |
| 4515 | document_management | Execution error: (sqlite3.OperationalError) ORDER BY clause should come after INTERSECT not before
[SQL: SELECT document_name FROM documents GROUP BY document_type_code ORDER BY count(*) DESC LIMIT 3 INTERSECT SELECT document_name FROM documents GROUP BY document_structure_code ORDER BY count(*) DESC LIMIT 3]
(Background on this error at: https://sqlalche.me/e/20/e3q8) |

## Error Patterns

| Pattern | Count |
|---------|-------|
| execution error | 3 |
