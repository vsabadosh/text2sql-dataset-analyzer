"""
Tests for result-set canonicalisation, fingerprinting and determinism labelling.
"""
import sqlglot
import pytest

from text2sql_pipeline.analyzers.query_execution.query_execution_analyzer import \
    QueryExecutionAnalyzer
from text2sql_pipeline.analyzers.query_execution.result_canon import (
    Determinism,
    build_tie_probe,
    canonical_cell,
    classify_determinism,
    cut_position,
    extract_limit,
    fingerprint_rows,
    has_nondeterministic_call,
    has_order_by,
)
from text2sql_pipeline.core.contracts import MetricsSink
from text2sql_pipeline.core.metric import MetricEvent
from text2sql_pipeline.core.models import DataItem

DB_ID = "student_assessment"
PEOPLE_ROWS = 8


class RecordingSink(MetricsSink):
    def __init__(self):
        self.metrics = []

    def write(self, event: MetricEvent) -> None:
        self.metrics.append(event)

    def flush(self) -> None:
        pass

    def close(self) -> None:
        pass


def run(analyzer, sql):
    sink = RecordingSink()
    item = DataItem(id="i1", dbId=DB_ID, sql=sql)
    list(analyzer.analyze([item], sink=sink, dataset_id="test"))
    return sink.metrics[0].model_dump()


def parse(sql):
    return sqlglot.parse_one(sql, read="sqlite")


# --- Cell canonicalisation ---------------------------------------------------


def test_int_and_float_of_equal_value_canonicalise_alike():
    # The same expression may yield either, depending on which rows it touches.
    assert canonical_cell(10) == canonical_cell(10.0)


def test_negative_zero_folds_into_zero():
    assert canonical_cell(-0.0) == canonical_cell(0.0)


def test_null_is_distinct_from_empty_string_and_zero():
    assert canonical_cell(None) != canonical_cell("")
    assert canonical_cell(None) != canonical_cell(0)


def test_unicode_forms_of_the_same_text_canonicalise_alike():
    assert canonical_cell("é") == canonical_cell("é")  # NFC vs NFD


def test_float_noise_below_precision_is_folded():
    assert canonical_cell(1.0000000000001) == canonical_cell(1.0)


def test_difference_above_precision_survives():
    assert canonical_cell(1.01) != canonical_cell(1.0)


# --- Fingerprints ------------------------------------------------------------


def test_bag_fingerprint_ignores_row_order():
    _, bag_a = fingerprint_rows([(1, "a"), (2, "b")])
    _, bag_b = fingerprint_rows([(2, "b"), (1, "a")])
    assert bag_a == bag_b


def test_sequence_fingerprint_respects_row_order():
    seq_a, _ = fingerprint_rows([(1, "a"), (2, "b")])
    seq_b, _ = fingerprint_rows([(2, "b"), (1, "a")])
    assert seq_a != seq_b


def test_field_boundaries_are_not_ambiguous():
    # Without length prefixes these two would hash alike.
    _, bag_a = fingerprint_rows([("ab", "c")])
    _, bag_b = fingerprint_rows([("a", "bc")])
    assert bag_a != bag_b


def test_differing_values_change_the_fingerprint():
    _, bag_a = fingerprint_rows([(1, "a")])
    _, bag_b = fingerprint_rows([(1, "b")])
    assert bag_a != bag_b


def test_equal_row_count_with_different_values_is_still_detected():
    # This is what row_count alone cannot catch.
    _, bag_a = fingerprint_rows([(1,), (2,)])
    _, bag_b = fingerprint_rows([(3,), (4,)])
    assert bag_a != bag_b


# --- AST helpers -------------------------------------------------------------


@pytest.mark.parametrize("sql,expected", [
    ("SELECT a FROM t", None),
    ("SELECT a FROM t LIMIT 5", 5),
    ("SELECT a FROM t UNION SELECT b FROM u LIMIT 3", 3),
])
def test_extract_limit(sql, expected):
    assert extract_limit(parse(sql)) == expected


def test_order_by_inside_a_subquery_does_not_count():
    assert has_order_by(parse("SELECT a FROM (SELECT a FROM t ORDER BY a)")) is False
    assert has_order_by(parse("SELECT a FROM t ORDER BY a")) is True


@pytest.mark.parametrize("sql", [
    "SELECT random() FROM t",
    "SELECT date('now') FROM t",
    "SELECT CURRENT_TIMESTAMP FROM t",
])
def test_nondeterministic_calls_are_detected(sql):
    assert has_nondeterministic_call(parse(sql)) is True


def test_ordinary_query_has_no_nondeterministic_call():
    assert has_nondeterministic_call(parse("SELECT count(*) FROM t")) is False


# --- Determinism classification ---------------------------------------------


def test_plain_query_is_deterministic():
    label = classify_determinism(parse("SELECT a FROM t"), row_count=5,
                                 truncated=False, effective_limit=None)
    assert label is Determinism.DETERMINISTIC


def test_binding_limit_without_order_leaves_the_row_set_undefined():
    label = classify_determinism(parse("SELECT a FROM t LIMIT 5"), row_count=5,
                                 truncated=False, effective_limit=5)
    assert label is Determinism.SET_UNDEFINED


def test_binding_limit_with_order_is_unresolved_without_probe_verdict():
    label = classify_determinism(parse("SELECT a FROM t ORDER BY b LIMIT 5"), row_count=5,
                                 truncated=False, effective_limit=5)
    assert label is Determinism.UNRESOLVED


def test_limit_that_never_binds_constrains_nothing():
    label = classify_determinism(parse("SELECT a FROM t LIMIT 10"), row_count=3,
                                 truncated=False, effective_limit=10)
    assert label is Determinism.DETERMINISTIC


def test_truncation_outranks_every_other_label():
    label = classify_determinism(parse("SELECT random() FROM t LIMIT 5"), row_count=5,
                                 truncated=True, effective_limit=5)
    assert label is Determinism.TRUNCATED


def test_nondeterministic_function_is_reported():
    label = classify_determinism(parse("SELECT random() FROM t"), row_count=5,
                                 truncated=False, effective_limit=None)
    assert label is Determinism.NONDETERMINISTIC_FN


def test_confirmed_tie_is_ambiguous():
    label = classify_determinism(parse("SELECT a FROM t ORDER BY b LIMIT 5"), row_count=5,
                                 truncated=False, effective_limit=5, tie_at_cut=True)
    assert label is Determinism.SET_AMBIGUOUS


def test_probe_finding_no_tie_is_deterministic_on_the_snapshot():
    label = classify_determinism(parse("SELECT a FROM t ORDER BY b LIMIT 5"), row_count=5,
                                 truncated=False, effective_limit=5, tie_at_cut=False)
    assert label is Determinism.DETERMINISTIC


def test_a_tie_cannot_rescue_a_query_with_no_order_at_all():
    label = classify_determinism(parse("SELECT a FROM t LIMIT 5"), row_count=5,
                                 truncated=False, effective_limit=5, tie_at_cut=True)
    assert label is Determinism.SET_UNDEFINED


# --- Boundary probe construction ---------------------------------------------


def test_probe_returns_the_sort_keys_rather_than_the_payload():
    probe = build_tie_probe(parse("SELECT name FROM t WHERE x > 1 ORDER BY score DESC LIMIT 3"))
    rendered = probe.sql(dialect="sqlite")
    assert "score" in rendered
    assert "name" not in rendered
    assert "WHERE" in rendered
    assert "LIMIT" not in rendered


def test_probe_keeps_grouping_so_the_ranking_is_unchanged():
    probe = build_tie_probe(
        parse("SELECT id, count(*) FROM t GROUP BY cat ORDER BY count(*) DESC LIMIT 1")
    )
    rendered = probe.sql(dialect="sqlite")
    assert "GROUP BY" in rendered
    assert "COUNT(*)" in rendered.upper()


def test_probe_resolves_a_positional_sort_key():
    probe = build_tie_probe(parse("SELECT a, b FROM t ORDER BY 2 LIMIT 1"))
    assert probe.expressions[0].sql() == "b"


def test_probe_resolves_a_sort_key_named_by_output_alias():
    probe = build_tie_probe(parse("SELECT count(*) AS c FROM t GROUP BY x ORDER BY c LIMIT 1"))
    assert "COUNT(*)" in probe.expressions[0].sql().upper()


def test_probe_declines_distinct_because_it_would_shift_the_cut():
    assert build_tie_probe(parse("SELECT DISTINCT a FROM t ORDER BY a LIMIT 1")) is None


def test_probe_declines_set_operations():
    assert build_tie_probe(
        parse("SELECT a FROM t UNION SELECT a FROM u ORDER BY a LIMIT 1")
    ) is None


def test_probe_declines_a_query_with_no_ordering():
    assert build_tie_probe(parse("SELECT a FROM t LIMIT 1")) is None


def test_offset_moves_the_cut_further_down():
    assert cut_position(parse("SELECT a FROM t ORDER BY a LIMIT 5"), 5) == 5
    assert cut_position(parse("SELECT a FROM t ORDER BY a LIMIT 5 OFFSET 10"), 5) == 15


# --- Analyzer integration ----------------------------------------------------


def test_row_count_reflects_the_real_result(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    features = run(analyzer, "SELECT * FROM People")["features"]
    assert features["row_count"] == PEOPLE_ROWS
    assert features["executed"] is True
    assert features["column_count"] == 8
    assert features["truncated"] is False
    assert features["determinism"] == Determinism.DETERMINISTIC.value


def test_fingerprint_is_stable_across_runs(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    sql = "SELECT person_id, first_name FROM People"
    first = run(analyzer, sql)["features"]["result_fingerprint"]
    second = run(analyzer, sql)["features"]["result_fingerprint"]
    assert first is not None
    assert first == second


def test_different_projections_yield_different_fingerprints(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    first = run(analyzer, "SELECT first_name FROM People")["features"]["result_fingerprint"]
    second = run(analyzer, "SELECT last_name FROM People")["features"]["result_fingerprint"]
    assert first != second


def test_reordering_rows_keeps_the_bag_fingerprint(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    ascending = run(analyzer, "SELECT person_id FROM People ORDER BY person_id")["features"]
    descending = run(analyzer, "SELECT person_id FROM People ORDER BY person_id DESC")["features"]
    assert ascending["result_fingerprint"] == descending["result_fingerprint"]
    assert ascending["order_fingerprint"] != descending["order_fingerprint"]
    assert ascending["ordered"] is True


def test_read_cap_truncates_and_withholds_the_fingerprint(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None, read_cap=5)
    features = run(analyzer, "SELECT * FROM People")["features"]
    assert features["truncated"] is True
    assert features["row_count"] == 5
    assert features["determinism"] == Determinism.TRUNCATED.value
    # A prefix of an arbitrary order must not masquerade as an authoritative digest.
    assert features["result_fingerprint"] is None


def test_read_cap_equal_to_result_size_does_not_truncate(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None, read_cap=PEOPLE_ROWS)
    features = run(analyzer, "SELECT * FROM People")["features"]
    assert features["truncated"] is False
    assert features["row_count"] == PEOPLE_ROWS


def test_injected_safety_limit_marks_the_row_set_undefined(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=1)
    features = run(analyzer, "SELECT * FROM People")["features"]
    assert features["row_count"] == 1
    assert features["determinism"] == Determinism.SET_UNDEFINED.value


def test_invalid_read_cap_is_rejected(student_assessment_db):
    with pytest.raises(ValueError, match="read_cap"):
        QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True, read_cap=0)


def test_execution_policy_is_recorded_in_tags(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None, read_cap=500)
    tags = run(analyzer, "SELECT * FROM People")["tags"]
    assert tags == {"dialect": "sqlite", "mode": "select_only",
                    "safety_limit": "null", "read_cap": "500"}


@pytest.mark.parametrize("sql,kind", [
    ("SELECT * FROM NoSuchTable", "missing_table"),
    ("SELECT no_such_column FROM People", "missing_column"),
    ("SELECT FROM", "syntax_error"),
    ("DROP TABLE People", "blocked"),
])
def test_execution_errors_are_classified(student_assessment_db, sql, kind):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True)
    errors = run(analyzer, sql)["stats"]["errors"]
    assert [e["kind"] for e in errors] == [kind]


def test_successful_run_records_no_error(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True)
    assert run(analyzer, "SELECT * FROM People")["stats"]["errors"] == []


def test_tie_at_the_cut_is_measured_and_reported(student_assessment_db):
    # Two people share the surname Hartmann, which lands on ranks 5 and 6.
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    features = run(analyzer, "SELECT first_name FROM People ORDER BY last_name LIMIT 5")["features"]
    assert features["tie_at_cut"] is True
    assert features["determinism"] == Determinism.SET_AMBIGUOUS.value


def test_a_separated_boundary_is_deterministic(student_assessment_db):
    # Rank 4 is Grant and rank 5 is Hartmann, so the boundary keys differ.
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    features = run(analyzer, "SELECT first_name FROM People ORDER BY last_name LIMIT 4")["features"]
    assert features["tie_at_cut"] is False
    assert features["determinism"] == Determinism.DETERMINISTIC.value


def test_no_probe_runs_when_the_limit_never_binds(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    features = run(analyzer, "SELECT first_name FROM People ORDER BY last_name LIMIT 99")["features"]
    assert features["tie_at_cut"] is None
    assert features["determinism"] == Determinism.DETERMINISTIC.value


def test_no_probe_runs_without_an_order_by(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    features = run(analyzer, "SELECT first_name FROM People LIMIT 2")["features"]
    assert features["tie_at_cut"] is None
    assert features["determinism"] == Determinism.SET_UNDEFINED.value


def test_a_query_the_probe_cannot_rewrite_is_unresolved(student_assessment_db):
    # DISTINCT is declined by the probe, and declining must not read as safety.
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True,
                                      safety_limit=None)
    features = run(
        analyzer, "SELECT DISTINCT last_name FROM People ORDER BY last_name LIMIT 3"
    )["features"]
    assert features["tie_at_cut"] is None
    assert features["determinism"] == Determinism.UNRESOLVED.value


def test_mutation_reports_no_result_set(student_assessment_db):
    analyzer = QueryExecutionAnalyzer(db_manager=student_assessment_db, enabled=True, mode="all")
    features = run(analyzer, "UPDATE People SET first_name = 'x'")["features"]
    assert features["executed"] is True
    assert features["row_count"] is None
    assert features["result_fingerprint"] is None
