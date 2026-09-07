"""
Canonical result-set fingerprinting.

A fingerprint makes two result sets comparable, and a run reproducible, without
persisting any row data. Canonicalisation is required because raw rows are not
comparable as returned:

- row order is undefined unless the query carries a total ORDER BY;
- the same logical number may arrive as int or float depending on the data;
- text may differ only by Unicode normalisation form.

Two digests are produced. ``bag`` hashes the multiset of rows and is the one
that survives undefined row order. ``seq`` hashes rows as returned and is only
meaningful when the query fixes a total order.

Neither digest says anything on its own: a result whose *content* is undefined
(``LIMIT`` without a total ``ORDER BY``, a call to ``random()``, a read cut off
at the cap) must not be used as evidence. :func:`classify_determinism` labels
that, and the label travels with the fingerprint.
"""

from __future__ import annotations

import hashlib
import math
import unicodedata
from datetime import date, datetime, time
from decimal import Decimal
from enum import Enum
from typing import Any, Iterable, Sequence

from sqlglot import exp

# Enough to keep aggregates stable while folding the last bits of float noise.
FLOAT_SIGNIFICANT_DIGITS = 12

# 128 bits: collisions are not a concern at dataset scale, and short digests
# stay readable in reports.
FINGERPRINT_HEX_LEN = 32

_ROW_SEPARATOR = b"\x1e"
_FIELD_SEPARATOR = b"\x1f"

# Functions whose value depends on the moment of execution or on chance.
_NONDETERMINISTIC_FUNCTIONS = frozenset({
    "rand", "random", "randomblob",
    "current_timestamp", "current_date", "current_time",
    "now", "getdate", "sysdate", "localtime", "localtimestamp",
    "uuid", "newid", "gen_random_uuid",
})

# SQLite spells "right now" as a string argument: date('now'), datetime('now').
_NONDETERMINISTIC_LITERALS = frozenset({"now"})


class Determinism(str, Enum):
    """Whether the result set is reproducible, and if not, why not."""

    #: The multiset of rows is fully determined by the query and the data.
    DETERMINISTIC = "DETERMINISTIC"

    #: LIMIT binds without any ORDER BY, so which rows come back is arbitrary.
    SET_UNDEFINED = "SET_UNDEFINED"

    #: Rows at the cut share the same sort key, so the query admits several
    #: equally ranked answers and the one returned is arbitrary.
    SET_AMBIGUOUS = "SET_AMBIGUOUS"

    #: A binding ordered LIMIT could not be checked by the boundary probe.
    #: This is a coverage status, not a demonstrated defect.
    UNRESOLVED = "UNRESOLVED"

    #: The query calls a time- or chance-dependent function.
    NONDETERMINISTIC_FN = "NONDETERMINISTIC_FN"

    #: Reading stopped at the cap, so the rows seen are an arbitrary prefix.
    TRUNCATED = "TRUNCATED"


def canonical_cell(value: Any) -> tuple[str, str]:
    """Reduce one cell to a (type tag, text) pair.

    Numeric types collapse into a single tag so that ``10`` and ``10.0`` — which
    the same expression may yield depending on the rows it touches — do not read
    as a difference.
    """
    if value is None:
        return ("z", "")
    if isinstance(value, bool):
        return ("n", "1" if value else "0")
    if isinstance(value, int):
        return ("n", str(value))
    if isinstance(value, float):
        return ("n", _canonical_number(value))
    if isinstance(value, Decimal):
        return ("n", _canonical_number(float(value)))
    if isinstance(value, str):
        return ("s", unicodedata.normalize("NFC", value))
    if isinstance(value, (bytes, bytearray, memoryview)):
        return ("x", hashlib.sha256(bytes(value)).hexdigest())
    if isinstance(value, (datetime, date, time)):
        return ("t", value.isoformat())
    return ("o", repr(value))


def _canonical_number(value: float) -> str:
    if math.isnan(value):
        return "nan"
    if math.isinf(value):
        return "inf" if value > 0 else "-inf"
    if value == 0.0:
        return "0"  # folds -0.0 into 0.0
    text = f"{value:.{FLOAT_SIGNIFICANT_DIGITS}g}"
    if "e" not in text and "." in text:
        text = text.rstrip("0").rstrip(".")
    return text or "0"


def canonical_row(row: Sequence[Any]) -> tuple[str, ...]:
    """Flatten a row into alternating type tags and texts, so rows sort totally."""
    tokens: list[str] = []
    for cell in row:
        tag, text = canonical_cell(cell)
        tokens.append(tag)
        tokens.append(text)
    return tuple(tokens)


def _digest(rows: Iterable[Sequence[str]]) -> str:
    digest = hashlib.sha256()
    for row in rows:
        digest.update(_ROW_SEPARATOR)
        for token in row:
            encoded = token.encode("utf-8")
            # Length prefixes keep ("ab", "c") distinct from ("a", "bc").
            digest.update(str(len(encoded)).encode("ascii"))
            digest.update(_FIELD_SEPARATOR)
            digest.update(encoded)
    return digest.hexdigest()[:FINGERPRINT_HEX_LEN]


def fingerprint_rows(rows: Sequence[Sequence[Any]]) -> tuple[str, str]:
    """Return ``(seq_fingerprint, bag_fingerprint)`` for the given rows."""
    canonical = [canonical_row(row) for row in rows]
    return _digest(canonical), _digest(sorted(canonical))


def extract_limit(ast: exp.Expression) -> int | None:
    """Read the top-level LIMIT, or None when absent or not a plain integer."""
    node = ast.args.get("limit")
    if node is None:
        return None
    expression = node.args.get("expression")
    if expression is None:
        return None
    try:
        return int(expression.name)
    except (TypeError, ValueError):
        return None


def has_order_by(ast: exp.Expression) -> bool:
    """Whether the outermost query fixes row order.

    Deliberately ignores ORDER BY inside subqueries: it does not constrain the
    order of the rows the caller receives.
    """
    return ast.args.get("order") is not None


def has_nondeterministic_call(ast: exp.Expression) -> bool:
    for node in ast.find_all(exp.Func):
        if _function_name(node) in _NONDETERMINISTIC_FUNCTIONS:
            return True
    for literal in ast.find_all(exp.Literal):
        if literal.is_string and str(literal.this).strip().lower() in _NONDETERMINISTIC_LITERALS:
            return True
    return False


def _function_name(node: exp.Func) -> str:
    if isinstance(node, exp.Anonymous):
        return str(node.this or "").lower()
    try:
        return node.sql_name().lower()
    except Exception:
        return type(node).__name__.lower()


def limit_binds(ast: exp.Expression, row_count: int, effective_limit: int | None) -> bool:
    """Whether the LIMIT actually cut the result rather than merely capping it."""
    return effective_limit is not None and row_count >= effective_limit


def cut_position(ast: exp.Expression, effective_limit: int) -> int:
    """The 1-based rank of the last row the LIMIT lets through."""
    offset = ast.args.get("offset")
    if offset is not None:
        expression = offset.args.get("expression", offset)
        try:
            return int(expression.name) + effective_limit
        except (TypeError, ValueError):
            pass
    return effective_limit


def build_tie_probe(ast: exp.Expression) -> exp.Expression | None:
    """Rewrite a query so that it returns its sort keys instead of its payload.

    Comparing the keys at the cut against the next one down decides whether the
    LIMIT chose between rows the ORDER BY had already separated, or picked
    arbitrarily among equals. The payload is irrelevant to that question, and
    projecting it instead would hide ties in columns not selected.

    Returns None when the rewrite cannot be trusted. The caller records that as
    unresolved rather than inventing either safety or a defect.
    """
    if not isinstance(ast, exp.Select):
        # Set operations put ORDER BY outside the branches; rewriting the
        # projection would have to be pushed into each of them.
        return None
    if ast.args.get("distinct"):
        # Deduplication happens on the payload, so projecting the sort keys
        # instead would collapse a different set of rows and shift the cut.
        return None

    order = ast.args.get("order")
    if order is None:
        return None

    keys = []
    for ordered in order.expressions:
        key = _resolve_order_key(ast, ordered.this)
        if key is None:
            return None
        keys.append(key.copy())

    probe = ast.copy()
    probe.set("expressions", keys)
    probe.set("limit", None)
    probe.set("offset", None)
    return probe


def _resolve_order_key(select: exp.Select, key: exp.Expression) -> exp.Expression | None:
    """Rewrite a sort key into something valid in the projection.

    ORDER BY may name an output column by position or by alias, neither of
    which is defined once the projection is replaced.
    """
    if isinstance(key, exp.Literal) and not key.is_string:
        try:
            index = int(key.name) - 1
        except (TypeError, ValueError):
            return None
        if not 0 <= index < len(select.expressions):
            return None
        projected = select.expressions[index]
        return projected.this if isinstance(projected, exp.Alias) else projected

    if isinstance(key, exp.Column) and not key.table:
        for projected in select.expressions:
            if isinstance(projected, exp.Alias) and projected.alias.lower() == key.name.lower():
                return projected.this

    return key


def classify_determinism(
    ast: exp.Expression,
    row_count: int,
    truncated: bool,
    effective_limit: int | None,
    tie_at_cut: bool | None = None,
) -> Determinism:
    """Label the reproducibility of a result set.

    ``effective_limit`` is the LIMIT actually in force, which may be one the
    analyzer injected rather than one the dataset wrote.

    ``tie_at_cut`` carries the verdict of :func:`build_tie_probe` when it was
    run. None means the question was not settled, which is reported as risk
    rather than as absence of ambiguity.

    The label describes the multiset of rows. Row *order* is covered separately
    by :func:`has_order_by`, because an undefined order leaves the multiset
    intact.
    """
    if truncated:
        return Determinism.TRUNCATED
    if has_nondeterministic_call(ast):
        return Determinism.NONDETERMINISTIC_FN
    # A limit that never binds constrains nothing.
    if limit_binds(ast, row_count, effective_limit):
        if not has_order_by(ast):
            return Determinism.SET_UNDEFINED
        if tie_at_cut is True:
            return Determinism.SET_AMBIGUOUS
        if tie_at_cut is False:
            return Determinism.DETERMINISTIC
        return Determinism.UNRESOLVED
    return Determinism.DETERMINISTIC
