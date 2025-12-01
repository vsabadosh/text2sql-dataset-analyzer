# Schema Validation Report

**Generated:** 2025-11-11 17:10:50

## Executive Summary

**Databases:** 40 · **Clean:** 36 (90.0%) · **Fatal Errors:** 0 · **Errors:** 3 · **Warnings:** 1

**Tables scanned:** 180 · **Empty tables:** 0 · **Invalid FKs:** 4

**Total warnings:** 1 · **DBs with FK data violations:** 1

**Empty Table Analysis:** 0 used in queries · 0 unused

**Top issue:** fk_missing_column (3)

## ❌ Databases with Errors (3)

| Database | Tables | Non-empty | Errors | Warnings | FK Violations |
|----------|--------|-----------|--------|----------|---------------|
| book_1 | 6 | 6/6 (100%) | 2 | 0 | 0 |
| car_racing | 4 | 4/4 (100%) | 1 | 0 | 0 |
| government_shift | 7 | 7/7 (100%) | 1 | 0 | 0 |

## ⚠️ Databases with Warnings Only (1)

| Database | Tables | Non-empty | Warnings | FK Violations |
|----------|--------|-----------|----------|---------------|
| pilot_1 | 2 | 2/2 (100%) | 1 | 1 |

## ✅ Clean Databases (36)

| Database | Tables | Non-empty | FK Violations |
|----------|--------|-----------|---------------|
| aan_1 | 5 | 5/5 (100%) | 0 |
| address_1 | 3 | 3/3 (100%) | 0 |
| advertising_agencies | 7 | 7/7 (100%) | 0 |
| … | … | … | … |

---

## Detailed Database Reports

### Database: book_1

**Status:** ❌ 2 errors · **Non-empty:** 6/6 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table Author_Book has FK referencing non-existing column(s) ['idAuthorA'] on parent 'Author'.
⛔ Table Orders has FK referencing non-existing column(s) [None] on parent 'Client'.

**Tables (summary)**

Total: 6 · Non-empty: 6 · Empty: 0


### Database: car_racing

**Status:** ❌ 1 error · **Non-empty:** 4/4 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Table driver has FK referencing non-existing column(s) ['Country_ID'] on parent 'country'.

**Tables (summary)**

Total: 4 · Non-empty: 4 · Empty: 0


### Database: government_shift

**Status:** ❌ 1 error · **Non-empty:** 7/7 (100%) · **FK:** N/A · **IC:** ok

**Errors**

⛔ Foreign key column types differ: Analytical_Layer.Customers_and_Services_ID (VARCHAR(40)→TEXT) vs Customers_and_Services.Customers_and_Services_ID (INTEGER→INTEGER)

**Tables (summary)**

Total: 7 · Non-empty: 7 · Empty: 0


### Database: pilot_1

**Status:** ⚠️ 1 warning · **Non-empty:** 2/2 (100%) · **FK:** N/A · **IC:** 1 violations

**Warnings**

⚠️ Found 1 FK data violation(s)

**Tables (summary)**

Total: 2 · Non-empty: 2 · Empty: 0

