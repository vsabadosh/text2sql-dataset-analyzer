"""Cartesian-product decisions for AND/OR/NOT conditions, USING/NATURAL joins
and key-pinned sources.

The partition-based check must decide exactly as an explicit DNF expansion
would: a scope is a Cartesian product iff some satisfiable DNF branch leaves
the sources disconnected.
"""
import itertools
import random
import sqlite3

import pytest

from text2sql_pipeline.analyzers.query_antipattern.antipattern_detector import (
    detect_antipatterns,
)

TABLES = ["a", "b", "c", "d"]
TABLE_COLUMNS = {table: ["id", "x", "y", "k"] for table in TABLES}


def _cartesian_records(result):
    return [
        (record.status, record.reason)
        for record in result.antipatterns + result.unresolved
        if record.pattern == "cartesian_product"
    ]


def _row_count(ddl_and_data, sql):
    conn = sqlite3.connect(":memory:")
    try:
        conn.executescript(ddl_and_data)
        return len(conn.execute(sql).fetchall())
    finally:
        conn.close()


# --------------------------------------------------------------------------
# Explicit DNF oracle
# --------------------------------------------------------------------------


def _random_atom(rng, tables):
    kind = rng.choice(["edge", "edge", "filter", "true", "false"])
    if kind == "edge":
        left, right = rng.sample(tables, 2)
        operator = rng.choice(["=", "<", "<>"])
        return ("edge", frozenset({left, right}), f"{left}.x {operator} {right}.y")
    if kind == "filter":
        table = rng.choice(tables)
        return ("filter", None, f"{table}.k = {rng.randint(0, 9)}")
    if kind == "true":
        return ("true", None, "1 = 1")
    return ("false", None, "1 = 0")


def _random_formula(rng, tables, depth):
    if depth == 0 or rng.random() < 0.25:
        return _random_atom(rng, tables)
    operator = rng.choice(["and", "or", "or", "not"])
    if operator == "not":
        return ("not", _random_formula(rng, tables, depth - 1))
    return (
        operator,
        _random_formula(rng, tables, depth - 1),
        _random_formula(rng, tables, depth - 1),
    )


def _render(formula):
    if formula[0] == "not":
        return f"NOT ({_render(formula[1])})"
    if formula[0] in ("and", "or"):
        return (
            f"({_render(formula[1])}) {formula[0].upper()} "
            f"({_render(formula[2])})"
        )
    return formula[2]


def _dnf(formula, negated=False):
    """Branches as (edges, satisfiable) pairs."""
    kind = formula[0]
    if kind == "not":
        return _dnf(formula[1], not negated)
    if kind in ("and", "or"):
        left = _dnf(formula[1], negated)
        right = _dnf(formula[2], negated)
        if (kind == "and") != negated:
            return [
                (l_edges | r_edges, l_ok and r_ok)
                for (l_edges, l_ok), (r_edges, r_ok) in itertools.product(left, right)
            ]
        return left + right
    if kind == "edge":
        return [(frozenset({formula[1]}), True)]
    if kind == "filter":
        return [(frozenset(), True)]
    truth = (kind == "true") != negated
    return [(frozenset(), truth)]


def _connected(tables, edges):
    parent = {table: table for table in tables}

    def find(table):
        while parent[table] != table:
            table = parent[table]
        return table

    for edge in edges:
        first, *others = edge
        for other in others:
            parent[find(other)] = find(first)
    return len({find(table) for table in tables}) == 1


def _oracle_is_cartesian(tables, formula):
    return any(
        ok and not _connected(tables, edges) for edges, ok in _dnf(formula)
    )


@pytest.mark.parametrize("table_count", [2, 3, 4])
@pytest.mark.parametrize("placement", ["where", "on"])
def test_partition_check_matches_explicit_dnf(table_count, placement):
    rng = random.Random(f"{table_count}-{placement}")
    tables = TABLES[:table_count]
    disagreements = []
    cartesian_seen = connected_seen = 0
    for _ in range(250):
        formula = _random_formula(rng, tables, depth=4)
        condition = _render(formula)
        if placement == "where":
            sql = f"SELECT 1 FROM {', '.join(tables)} WHERE {condition}"
        else:
            rest = "".join(f" JOIN {table} ON TRUE" for table in tables[2:])
            sql = (
                f"SELECT 1 FROM {tables[0]} JOIN {tables[1]} ON {condition}"
                f"{rest}"
            )
        expected = _oracle_is_cartesian(tables, formula)
        result = detect_antipatterns(sql, table_columns=TABLE_COLUMNS)
        records = _cartesian_records(result)
        if expected:
            cartesian_seen += 1
        else:
            connected_seen += 1
        if result.has_cartesian_product is not expected or (
            not expected and records
        ):
            disagreements.append((sql, expected, records))

    assert disagreements == []
    # Both outcomes must actually be exercised.
    assert cartesian_seen > 20 and connected_seen > 20


# --------------------------------------------------------------------------
# OR branches
# --------------------------------------------------------------------------


TWO_BY_TWO = """
    CREATE TABLE a(id, x, y, k); CREATE TABLE b(id, x, y, k);
    INSERT INTO a VALUES (1, 1, 1, 1), (2, 2, 2, 2);
    INSERT INTO b VALUES (1, 1, 1, 1), (2, 2, 2, 2);
"""


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT a.id, b.id FROM a JOIN b ON a.id = b.id OR 1 = 1",
        "SELECT a.id, b.id FROM a, b WHERE a.id = b.id OR 1 = 1",
        "SELECT a.id, b.id FROM a LEFT JOIN b ON a.id = b.id OR 1 = 1",
        "SELECT a.id, b.id FROM a, b WHERE a.id = b.id OR a.k = 1",
    ],
)
def test_or_branch_without_link_is_cartesian(sql):
    # Each case returns more rows than the joined pairs.
    assert _row_count(TWO_BY_TWO, sql) > 2
    result = detect_antipatterns(sql, table_columns=TABLE_COLUMNS)
    assert _cartesian_records(result) == [("defect", "disconnected_sources")]


def test_every_branch_linking_through_different_edges_is_not_cartesian():
    # Neither OR has an edge common to both branches, yet every DNF branch
    # (a-b or a-c, plus b-c) connects all three sources.
    sql = (
        "SELECT 1 FROM a, b, c "
        "WHERE (a.id = b.id OR a.id = c.id) AND b.k = c.k"
    )
    result = detect_antipatterns(sql, table_columns=TABLE_COLUMNS)
    assert _cartesian_records(result) == []


def test_false_branch_cannot_be_the_cartesian_one():
    sql = "SELECT 1 FROM a, b WHERE a.id = b.id OR 1 = 0"
    result = detect_antipatterns(sql, table_columns=TABLE_COLUMNS)
    assert _cartesian_records(result) == []


def test_negated_disjunction_keeps_both_links():
    # NOT (p OR q) is (NOT p) AND (NOT q): both inter-table predicates hold.
    sql = (
        "SELECT 1 FROM a, b, c "
        "WHERE NOT (a.x <> b.x OR b.y <> c.y)"
    )
    result = detect_antipatterns(sql, table_columns=TABLE_COLUMNS)
    assert _cartesian_records(result) == []


def test_negated_conjunction_exposes_an_unlinked_branch():
    # NOT (p AND q) is (NOT p) OR (NOT q); the branch NOT q has no link.
    sql = "SELECT 1 FROM a, b WHERE NOT (a.x = b.x AND a.k = 1)"
    result = detect_antipatterns(sql, table_columns=TABLE_COLUMNS)
    assert _cartesian_records(result) == [("defect", "disconnected_sources")]


def test_or_over_unbound_columns_is_unresolved():
    # Without a schema, x may belong to either source in the second branch.
    sql = "SELECT 1 FROM a, b WHERE a.id = b.id OR x = y"
    result = detect_antipatterns(sql)
    assert _cartesian_records(result) == [
        ("unresolved", "unbound_column_source")
    ]


def test_or_branch_without_link_wins_over_unbound_branch():
    sql = "SELECT 1 FROM a, b WHERE x = y OR a.k = 1"
    result = detect_antipatterns(sql)
    assert _cartesian_records(result) == [("defect", "disconnected_sources")]


# --------------------------------------------------------------------------
# Possible edges next to definite ones
# --------------------------------------------------------------------------


def test_possible_source_of_a_joining_predicate_is_kept():
    # z binds to c (unknown columns) or to nothing else, so the predicate may
    # link c as well as a and b.
    sql = (
        "SELECT 1 FROM a, b, (SELECT * FROM t) AS c "
        "WHERE a.x = b.y + z"
    )
    result = detect_antipatterns(
        sql,
        table_columns={"a": ["x"], "b": ["y"], "t": ["z"]},
    )
    assert _cartesian_records(result) == [
        ("unresolved", "unbound_column_source")
    ]


# --------------------------------------------------------------------------
# USING and NATURAL JOIN
# --------------------------------------------------------------------------


NATURAL_SCHEMA = """
    CREATE TABLE a(x, p); CREATE TABLE d(y, s); CREATE TABLE e(x, y, t);
    INSERT INTO a VALUES (1, 'a1'), (2, 'a2');
    INSERT INTO d VALUES (5, 'd5'), (6, 'd6');
    INSERT INTO e VALUES (1, 5, 'e');
"""
NATURAL_COLUMNS = {"a": ["x", "p"], "d": ["y", "s"], "e": ["x", "y", "t"]}


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM a, d NATURAL JOIN e",
        "SELECT * FROM a, d JOIN e ON a.x = e.x AND d.y = e.y",
        "SELECT * FROM a, d JOIN e USING (x, y)",
    ],
)
def test_natural_join_links_each_shared_column_to_its_owner(sql):
    assert _row_count(NATURAL_SCHEMA, sql) == 1
    result = detect_antipatterns(sql, table_columns=NATURAL_COLUMNS)
    assert _cartesian_records(result) == []


def test_natural_join_sharing_with_one_earlier_source_is_cartesian():
    ddl = """
        CREATE TABLE a(x, p); CREATE TABLE d(q, s); CREATE TABLE e(x, t);
        INSERT INTO a VALUES (1, 'a1'); INSERT INTO e VALUES (1, 'e');
        INSERT INTO d VALUES (5, 'd5'), (6, 'd6');
    """
    sql = "SELECT * FROM a, d NATURAL JOIN e"
    assert _row_count(ddl, sql) == 2
    result = detect_antipatterns(
        sql,
        table_columns={"a": ["x", "p"], "d": ["q", "s"], "e": ["x", "t"]},
    )
    assert _cartesian_records(result) == [("defect", "disconnected_sources")]


def test_using_binds_to_the_left_most_owner_even_when_later_sources_have_it():
    # SQLite equates c.x with a.x, leaving b combined with every row.
    ddl = """
        CREATE TABLE a(x, p); CREATE TABLE b(x, q); CREATE TABLE c(x, r);
        INSERT INTO a VALUES (1, 'a1'), (2, 'a2');
        INSERT INTO b VALUES (1, 'b1'), (3, 'b3');
        INSERT INTO c VALUES (1, 'c1'), (3, 'c3');
    """
    sql = "SELECT * FROM a, b JOIN c USING (x)"
    assert _row_count(ddl, sql) == 2
    result = detect_antipatterns(
        sql,
        table_columns={"a": ["x", "p"], "b": ["x", "q"], "c": ["x", "r"]},
    )
    assert _cartesian_records(result) == [("defect", "disconnected_sources")]


def test_using_chain_links_through_the_left_most_owner():
    sql = "SELECT * FROM a JOIN b USING (x) JOIN c USING (x)"
    result = detect_antipatterns(
        sql,
        table_columns={"a": ["x"], "b": ["x"], "c": ["x"]},
    )
    assert _cartesian_records(result) == []


# --------------------------------------------------------------------------
# Sources pinned by a key
# --------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sql, keys, unique",
    [
        ("SELECT a.x FROM a, b WHERE b.id = 5", {"b": ["id"]}, None),
        ("SELECT a.x FROM a JOIN b ON b.id = 5", {"b": ["id"]}, None),
        ("SELECT a.x FROM a LEFT JOIN b ON b.id = 5", {"b": ["id"]}, None),
        ("SELECT a.x FROM a, b WHERE b.k = 'z'", {}, {"b": [["k"]]}),
        (
            "SELECT a.x FROM a, c WHERE c.k = 1 AND c.id = 2",
            {"c": ["k", "id"]},
            None,
        ),
    ],
)
def test_source_pinned_by_a_whole_key_is_not_cartesian(sql, keys, unique):
    result = detect_antipatterns(
        sql,
        table_columns=TABLE_COLUMNS,
        primary_keys=keys,
        unique_keys=unique,
    )
    assert _cartesian_records(result) == []


def test_pinned_source_still_connects_the_others():
    # b and c each join the single a row; a must not be removed with its edges.
    sql = (
        "SELECT * FROM a JOIN b ON a.id = b.k JOIN c ON a.x = c.id "
        "WHERE a.id = 'BU2075'"
    )
    result = detect_antipatterns(
        sql, table_columns=TABLE_COLUMNS, primary_keys={"a": ["id"]}
    )
    assert _cartesian_records(result) == []


def test_sources_meeting_only_at_a_pinned_source_are_not_reported():
    """Same exemption as Brass & Goldberg: b and c are connected through a.

    Both are filtered to the single a row's value, so the result is b_a x c_a.
    The published test does not report this, and neither do we.
    """
    sql = "SELECT * FROM a, b, c WHERE a.id = 5 AND b.k = a.id AND c.k = a.id"
    result = detect_antipatterns(
        sql, table_columns=TABLE_COLUMNS, primary_keys={"a": ["id"]}
    )
    assert _cartesian_records(result) == []


def test_pinned_source_does_not_hide_a_product_of_the_others():
    sql = "SELECT * FROM a, b, c WHERE c.id = 5"
    result = detect_antipatterns(
        sql, table_columns=TABLE_COLUMNS, primary_keys={"c": ["id"]}
    )
    assert _cartesian_records(result) == [("defect", "no_join_condition")]


@pytest.mark.parametrize(
    "sql, keys",
    [
        # Two possible key values leave up to two rows.
        ("SELECT a.x FROM a, b WHERE b.id = 5 OR b.id = 6", {"b": ["id"]}),
        # Half of a composite key leaves many rows.
        ("SELECT a.x FROM a, c WHERE c.k = 1", {"c": ["k", "id"]}),
        # A non-key column.
        ("SELECT a.x FROM a, b WHERE b.x = 5", {"b": ["id"]}),
        # The LEFT JOIN condition restricts b, not the preserved a.
        ("SELECT a.x FROM a LEFT JOIN b ON a.id = 5", {"a": ["id"]}),
    ],
)
def test_partially_pinned_source_is_still_cartesian(sql, keys):
    result = detect_antipatterns(
        sql, table_columns=TABLE_COLUMNS, primary_keys=keys
    )
    assert result.has_cartesian_product is True


# --------------------------------------------------------------------------
# Scopes beyond the partition limit
# --------------------------------------------------------------------------


def _wide_scope(count, missing_link=False, with_or=False):
    tables = [f"t{index}" for index in range(count)]
    links = [
        f"t{index}.x = t{index + 1}.x"
        for index in range(count - 1)
        if not (missing_link and index == count // 2)
    ]
    if with_or:
        links[0] = f"({links[0]} OR t0.k = 1)"
    sql = f"SELECT 1 FROM {', '.join(tables)} WHERE {' AND '.join(links)}"
    return sql, {table: ["x", "k"] for table in tables}


def test_wide_conjunctive_scope_is_decided_by_connectivity():
    sql, columns = _wide_scope(14)
    assert _cartesian_records(
        detect_antipatterns(sql, table_columns=columns)
    ) == []

    sql, columns = _wide_scope(14, missing_link=True)
    assert _cartesian_records(
        detect_antipatterns(sql, table_columns=columns)
    ) == [("defect", "disconnected_sources")]


def test_wide_scope_with_or_is_unresolved():
    sql, columns = _wide_scope(14, with_or=True)
    assert _cartesian_records(
        detect_antipatterns(sql, table_columns=columns)
    ) == [("unresolved", "too_many_sources")]
