"""
Core antipattern detection logic using sqlglot AST analysis.

This module detects common SQL antipatterns and code smells:
- Unsafe UPDATE/DELETE (no WHERE) - data safety
- = NULL comparison (correctness)
- Non-mathematical chained comparisons (silent boolean coercion or execution failure)
- Conditional COUNT with a non-NULL ELSE branch (condition is not counted selectively)
- Unquoted date-shaped subtraction in temporal predicates
- Division by a static numeric zero
- Inconsistent row filters that are never true
- Disjunctive conditions that are always true
- Unexpanded zero-suffixed template placeholders in predicate values
- Scalar subqueries without a static at-most-one-row proof
- Cartesian product (missing JOIN) - correctness
- Missing GROUP BY (correctness)
- Functions in WHERE clause (index prevention)
- NOT IN with nullable columns (correctness)
- Leading wildcard LIKE (index prevention)
- DISTINCT proven redundant by grouping or schema keys (performance)
- Correlated subqueries (performance)
- SELECT * (maintainability, performance)
- SELECT columns in EXISTS (cosmetic)
"""

from __future__ import annotations

from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Set,
    Tuple,
)

import sqlglot
from sqlglot import exp

from .metrics import (
    AntipatternInstance,
    DECISION_CORRECT,
    DECISION_DEFECT,
    DECISION_REMARK,
    DECISION_UNRESOLVED,
    QueryAntipatternFeatures,
)
from .antipattern_registry import (
    AntipatternPattern,
    DEFAULT_CUSTOM_PENALTY,
    PATTERN_TO_BOOLEAN_FIELD,
    get_impact_class,
    get_severity_penalties,
)
from .context import SchemaContext
from .rules import RULES

# Default antipattern configuration (enables all antipatterns for backwards compatibility)
# In production, use dialect-specific configs from pipeline.yaml
DEFAULT_CONFIG = {
    "critical": [
        AntipatternPattern.UNSAFE_UPDATE_DELETE,  # Combined pattern for both UPDATE and DELETE
        AntipatternPattern.NULL_COMPARISON_EQUALS,
        AntipatternPattern.CARTESIAN_PRODUCT,
        AntipatternPattern.MISSING_GROUP_BY,
        AntipatternPattern.CHAINED_COMPARISON_SEMANTICS,
        AntipatternPattern.CONDITIONAL_COUNT_NON_NULL_ELSE,
        AntipatternPattern.UNQUOTED_DATE_ARITHMETIC,
        AntipatternPattern.LITERAL_DIVISION_BY_ZERO,
        AntipatternPattern.INCONSISTENT_CONDITION,
        AntipatternPattern.TAUTOLOGICAL_CONDITION,
    ],
    "high": [
        AntipatternPattern.TEMPLATE_PLACEHOLDER_LITERAL,
        AntipatternPattern.FUNCTION_IN_WHERE,
        AntipatternPattern.NOT_IN_NULLABLE,
        AntipatternPattern.LEADING_WILDCARD_LIKE,
        AntipatternPattern.LIMIT_WITHOUT_ORDER_BY,
        AntipatternPattern.OFFSET_WITHOUT_ORDER_BY,
        AntipatternPattern.SCALAR_SUBQUERY_CARDINALITY,
    ],
    "medium": [
        AntipatternPattern.REDUNDANT_DISTINCT,
        AntipatternPattern.CORRELATED_SUBQUERY,
        AntipatternPattern.SELECT_STAR,
        AntipatternPattern.SELECT_IN_EXISTS,
    ]
}

def detect_antipatterns(
    sql: str, 
    dialect: Optional[str] = "sqlite",
    config: Optional[Dict[str, List[str]]] = None,
    penalties: Optional[Dict[str, int]] = None,
    primary_keys: Optional[Dict[str, List[str]]] = None,
    table_columns: Optional[Dict[str, List[str]]] = None,
    column_comparators: Optional[
        Dict[str, Dict[str, Tuple[str, str]]]
    ] = None,
    column_nullability: Optional[Dict[str, Dict[str, bool]]] = None,
    star_expanded_columns: Optional[Dict[str, List[str]]] = None,
    column_types: Optional[Dict[str, Dict[str, str]]] = None,
    date_value_probe: Optional[
        Callable[[str, str, str], Optional[bool]]
    ] = None,
    unique_keys: Optional[Dict[str, List[List[str]]]] = None,
    unmodeled_key_tables: Optional[Set[str]] = None,
    foreign_keys: Optional[Dict[str, List[List[str]]]] = None,
    check_columns: Optional[Dict[str, List[str]]] = None,
    triggered_tables: Optional[Set[str]] = None,
    unknown_constraint_tables: Optional[Set[str]] = None,
    nullable_keys: Optional[Dict[str, List[List[str]]]] = None,
    mismatched_collation_keys: Optional[Dict[str, List[List[str]]]] = None,
) -> QueryAntipatternFeatures:
    """
    Pure public API for antipattern detection.
    
    Args:
        sql: SQL query string to analyze
        dialect: SQL dialect for parsing (default: sqlite)
        config: Antipattern configuration dict with keys: critical, high, medium, optional, disabled
                If None, uses DEFAULT_CONFIG
        penalties: Optional dict mapping severity levels to penalty points for scoring.
                   If None, uses DEFAULT_SEVERITY_PENALTIES from registry.
                   Example: {"critical": 30, "high": 15, "medium": 5, "low": 2}
        primary_keys: Optional table name -> primary key columns. Grouping by a
                   whole primary key determines every other column of that table,
                   so ungrouped columns are then legal and deterministic rather
                   than an antipattern. Without this map the check stays purely
                   syntactic and reports those cases too. Callers must include
                   only effective non-null keys; the pipeline integration
                   verifies this against SQLite's current snapshot.
        table_columns: Optional table name -> all column names. This lets
                   unqualified references and GROUP BY alias/input-name
                   collisions be bound without guessing.
        column_comparators: Optional table -> column -> (affinity, collation).
                   Equality-based key propagation is enabled only when both
                   operands have the same verified comparison semantics.
        column_nullability: Optional table -> column -> nullable boolean.
                   This must describe semantic schema nullability, including
                   dialect guarantees such as SQLite's INTEGER PRIMARY KEY
                   rowid alias. The NOT IN rule never treats a current-row
                   scan as a static non-null proof.
        star_expanded_columns: Optional table name -> the columns SELECT *
                   projects. This is narrower than table_columns for a virtual
                   table, whose hidden columns bind normally but are never
                   expanded. Defaults to table_columns, which is exact for
                   every ordinary table.
        column_types: Optional table -> column -> declared SQL type. Temporal
                   types strengthen unquoted-date detection.
        date_value_probe: Optional exact-value existence probe accepting
                   (physical table, column, date-shaped text). It enriches
                   TEXT/unknown columns with snapshot evidence.
        unique_keys: Optional table -> UNIQUE column sets other than the
                   primary key, under the same non-null guarantee as
                   primary_keys. SQLite treats a grouped unique set like a
                   key; PostgreSQL does not.
        unmodeled_key_tables: Optional tables with a uniqueness constraint
                   that neither key map describes, such as a partial unique
                   index. A GROUP BY defect needs two rows that agree on the
                   grouping, and such a constraint may forbid them, so a
                   column of these tables is never reported as a defect.
        foreign_keys: Optional table -> local column lists of foreign keys.
                   A scalar-subquery witness that invents a fresh key value
                   is refused when that key column is also a foreign key.
                   ``None`` means foreign keys were not supplied.
        check_columns: Optional table -> columns named by a CHECK constraint.
                   ``None`` means CHECK constraints were not supplied.
        triggered_tables: Optional tables that have a trigger. ``None`` means
                   triggers were not supplied.
        unknown_constraint_tables: Optional tables whose CHECK or trigger
                   status could not be read. A witness is refused for them.
        nullable_keys: Optional table -> PRIMARY KEY or UNIQUE column sets
                   that may contain NULL and whose index compares like the
                   columns. SQLite treats those NULLs as distinct, so GROUP BY
                   does not use them, but a copied non-null value would still
                   collide. A literal pin may use them: equality never matches
                   NULL, so one literal still identifies at most one row.
        mismatched_collation_keys: Optional table -> PRIMARY KEY or UNIQUE
                   column sets whose index collation differs from the column
                   collation. They never prove a pin, because one compared
                   value can match two index keys, but a witness must still
                   change them and a filter on them is ``key_column_condition``.
        
    Returns:
        QueryAntipatternFeatures with detected antipatterns
    """
    if not sql or not sql.strip():
        return QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
    
    try:
        ast = sqlglot.parse_one(sql, read=dialect or "sqlite")
    except Exception:
        return QueryAntipatternFeatures(parseable=False, quality_score=0, quality_level="poor")
    
    # Use default config if none provided
    if config is None:
        config = DEFAULT_CONFIG
    
    # Get penalties (merge with defaults if provided)
    effective_penalties = get_severity_penalties(penalties)
    
    # Build set of enabled antipatterns and pattern→severity mapping
    # Iterate through all severity levels in config (don't hardcode them)
    enabled_patterns = set()
    pattern_severity_map = {}
    
    for severity_level, patterns in config.items():
        # Each key in config is a severity level, value is list of patterns
        if isinstance(patterns, list):
            for pattern in patterns:
                enabled_patterns.add(pattern)
                pattern_severity_map[pattern] = severity_level
    
    schema = SchemaContext.build(
        ast,
        dialect=dialect,
        primary_keys=primary_keys,
        table_columns=table_columns,
        column_comparators=column_comparators,
        column_nullability=column_nullability,
        star_expanded_columns=star_expanded_columns,
        column_types=column_types,
        date_value_probe=date_value_probe,
        unique_keys=unique_keys,
        unmodeled_key_tables=unmodeled_key_tables,
        foreign_keys=foreign_keys,
        check_columns=check_columns,
        triggered_tables=triggered_tables,
        unknown_constraint_tables=unknown_constraint_tables,
        nullable_keys=nullable_keys,
        mismatched_collation_keys=mismatched_collation_keys,
    )

    return _analyze_ast(
        ast,
        enabled_patterns,
        pattern_severity_map,
        effective_penalties,
        schema,
    )

def _analyze_ast(
    ast: exp.Expression,
    enabled_patterns: Set[str],
    pattern_severity_map: Dict[str, str],
    penalties: Dict[str, int],
    schema: SchemaContext,
) -> QueryAntipatternFeatures:
    """Analyze a parsed AST and detect antipatterns.

    Args:
        ast: Parsed SQL AST
        enabled_patterns: Set of enabled pattern names
        pattern_severity_map: Mapping of pattern name to severity level
        penalties: Mapping of severity level to penalty points for scoring
        schema: Normalized schema metadata used by the rules
    """
    features = QueryAntipatternFeatures(parseable=True)
    antipatterns: List[AntipatternInstance] = []

    for rule in RULES:
        if rule.pattern in enabled_patterns:
            antipatterns.extend(
                rule.detect(
                    ast,
                    schema,
                    pattern_severity_map.get(
                        rule.pattern, rule.default_severity
                    ),
                )
            )

    _store_decisions(features, antipatterns)

    # Calculate quality score and level using config-provided penalties
    features.quality_score = _calculate_quality_score(features, penalties)
    features.quality_level = _classify_quality(features.quality_score)

    return features

def _store_decisions(
    features: QueryAntipatternFeatures,
    records: List[AntipatternInstance],
) -> None:
    """Split rule records by decision and derive flags and counters.

    Class D forms do not change the query result, so their records are remarks
    rather than defects. Boolean flags, ``antipatterns`` and the quality score
    reflect only defects and remarks; unresolved and proved-safe forms are kept
    in their own lists.
    """
    for record in records:
        if (
            record.status == DECISION_DEFECT
            and get_impact_class(record.pattern) == "D"
        ):
            record.status = DECISION_REMARK

    features.antipatterns = [
        record
        for record in records
        if record.status in (DECISION_DEFECT, DECISION_REMARK)
    ]
    features.unresolved = [
        record for record in records if record.status == DECISION_UNRESOLVED
    ]
    features.proved_safe = [
        record for record in records if record.status == DECISION_CORRECT
    ]

    features.defect_count = sum(
        record.status == DECISION_DEFECT for record in features.antipatterns
    )
    features.remark_count = len(features.antipatterns) - features.defect_count
    features.unresolved_count = len(features.unresolved)
    features.proved_safe_count = len(features.proved_safe)
    features.total_antipatterns = len(features.antipatterns)

    for field_name in set(PATTERN_TO_BOOLEAN_FIELD.values()):
        setattr(features, field_name, False)
    for record in features.antipatterns:
        field_name = PATTERN_TO_BOOLEAN_FIELD.get(record.pattern)
        if field_name is not None:
            setattr(features, field_name, True)

# ============================================================================
# Scoring and Classification
# ============================================================================

def _calculate_quality_score(features: QueryAntipatternFeatures, penalties: Dict[str, int]) -> int:
    """
    Calculate query quality score (0-100).
    
    100 = perfect (no antipatterns)
    0 = very poor (many serious issues)
    
    Args:
        features: QueryAntipatternFeatures with detected antipatterns
        penalties: Dict mapping severity level to penalty points.
                   Loaded from config, with defaults from DEFAULT_SEVERITY_PENALTIES.
                   Example: {"critical": 30, "high": 15, "medium": 5, "low": 2}
    
    Returns:
        Quality score from 0 to 100
    """
    score = 100
    
    # Deduct points based on antipatterns' severity using config-provided penalties
    for ap in features.antipatterns:
        penalty = penalties.get(ap.severity, DEFAULT_CUSTOM_PENALTY)
        score -= penalty
    
    # Ensure score stays in valid range
    return max(0, min(100, score))

def _classify_quality(score: int) -> str:
    """
    Classify query quality based on score.
    
    Returns: excellent | good | fair | poor
    """
    if score >= 90:
        return "excellent"
    elif score >= 70:
        return "good"
    elif score >= 50:
        return "fair"
    else:
        return "poor"
