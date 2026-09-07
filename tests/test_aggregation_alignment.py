from __future__ import annotations

from text2sql_pipeline.analyzers.question_sql_consistency import (
    ConsistencyStatus,
    ContextManifest,
    detect_consistency,
)


def _single_finding(question: str, sql: str):
    features = detect_consistency(
        question,
        sql,
        rules=["aggregation_alignment"],
        emit_supported=True,
    )
    assert len(features.findings) == 1
    return features, features.findings[0]


def test_average_age_matches_avg_age():
    features, finding = _single_finding(
        "What is the average age?",
        "SELECT AVG(age) FROM people",
    )

    assert features.supported_count == 1
    assert finding.reason_code == "AGGREGATION_ALIGNMENT_MATCH"
    assert finding.details["requested_aggregate"] == "AVG"
    assert finding.details["column_name"] == "age"
    assert finding.question_spans[0].text == "average"


def test_cue_local_aggregate_target_wins_over_grouping_column():
    features, finding = _single_finding(
        "What is the average value of boxes for each warehouse?",
        "SELECT warehouse, AVG(value) FROM boxes GROUP BY warehouse",
    )

    assert features.supported_count == 1
    assert finding.details["column_name"] == "value"


def test_camel_case_aggregate_target_wins_over_other_named_projection():
    features, finding = _single_finding(
        "Find the average life expectancy and total population for each continent.",
        (
            "SELECT SUM(Population), AVG(LifeExpectancy), Continent "
            "FROM country GROUP BY Continent"
        ),
    )

    assert features.supported_count == 1
    assert finding.details["column_name"] == "lifeexpectancy"


def test_mean_age_matches_avg_age():
    features, finding = _single_finding(
        "What is the mean age?",
        "SELECT AVG(age) FROM people",
    )

    assert features.supported_count == 1
    assert finding.details["requested_aggregate"] == "AVG"


def test_average_age_conflicts_with_sum_age():
    features, finding = _single_finding(
        "What is the average age?",
        "SELECT SUM(age) FROM people",
    )

    assert features.contradicted_count == 1
    assert finding.reason_code == "AGGREGATION_OPERATOR_CONFLICT"
    assert finding.details["actual_aggregates"] == ["SUM"]


def test_average_age_conflicts_with_raw_age_projection():
    features, finding = _single_finding(
        "What is the average age?",
        "SELECT age FROM people",
    )

    assert features.contradicted_count == 1
    assert finding.reason_code == "AGGREGATION_OPERATOR_CONFLICT"


def test_precomputed_aggregate_named_column_is_not_assessed():
    features, finding = _single_finding(
        "What is the average attendance?",
        "SELECT average_attendance FROM stadium",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"


def test_maximum_number_of_events_is_outside_count_free_scope():
    features, finding = _single_finding(
        "What is the maximum number of visits by one customer?",
        "SELECT COUNT(*) FROM visit GROUP BY customer_id ORDER BY COUNT(*) DESC LIMIT 1",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"


def test_sum_count_average_equivalence_is_not_assessed():
    features, finding = _single_finding(
        "What is the average height?",
        "SELECT CAST(SUM(height) AS REAL) / COUNT(id) FROM player",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"


def test_per_unit_average_is_not_assessed_as_ratio():
    features, finding = _single_finding(
        "What is the average population per square kilometer?",
        "SELECT population / area FROM state",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"


def test_average_percentage_is_not_assessed_as_ratio():
    features, finding = _single_finding(
        "What is the average percentage of appearances?",
        "SELECT SUM(words) * 100 / SUM(occurrences) FROM pages",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"


def test_avg_of_wrong_column_does_not_claim_support():
    features, finding = _single_finding(
        "What is the average age?",
        "SELECT AVG(salary) FROM people",
    )

    assert features.supported_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "AGGREGATION_ROLE_UNRESOLVED"


def test_computed_aggregate_operand_is_not_assessed():
    features, finding = _single_finding(
        "What is the average age?",
        "SELECT AVG(age + bonus) FROM people",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"


def test_ambiguous_aggregate_columns_are_unresolved():
    features, finding = _single_finding(
        "What is the average age?",
        (
            "SELECT AVG(p.age), AVG(e.age) "
            "FROM people p JOIN employee e ON p.id = e.id"
        ),
    )

    assert features.unresolved_count == 1
    assert finding.reason_code == "AGGREGATION_ROLE_UNRESOLVED"
    assert finding.details["candidate_count"] == 2


def test_nested_aggregate_does_not_satisfy_root_scalar_request():
    features, finding = _single_finding(
        "What is the maximum salary?",
        (
            "SELECT name FROM employee "
            "WHERE salary = (SELECT MAX(salary) FROM employee)"
        ),
    )

    assert features.supported_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "AGGREGATION_SCOPE_UNRESOLVED"


def test_bound_root_role_does_not_contradict_subquery_extremum():
    features, finding = _single_finding(
        "What is the maximum capacity of the stadiums?",
        "SELECT capacity FROM stadium WHERE capacity = (SELECT MAX(capacity) FROM stadium)",
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "AGGREGATION_SCOPE_UNRESOLVED"


def test_bound_root_role_does_not_contradict_cte_extremum():
    features, finding = _single_finding(
        "What is the maximum enrollment of the schools?",
        (
            "WITH m AS (SELECT MAX(enrollment) AS enrollment FROM school) "
            "SELECT enrollment FROM m"
        ),
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "AGGREGATION_SCOPE_UNRESOLVED"


def test_offset_breaks_the_order_by_limit_one_extremum_equivalence():
    features, finding = _single_finding(
        "What is the maximum salary?",
        "SELECT salary FROM employee ORDER BY salary DESC LIMIT 1 OFFSET 1",
    )

    assert features.supported_count == 0
    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"
    assert finding.details["realization"] == "OFFSET_ORDER_BY_LIMIT_1"


def test_reversed_order_extremum_with_nested_aggregate_abstains():
    features, finding = _single_finding(
        "What is the minimum price of a product?",
        (
            "SELECT price FROM products "
            "WHERE price >= (SELECT MIN(price) FROM products) "
            "ORDER BY price DESC LIMIT 1"
        ),
    )

    assert features.contradicted_count == 0
    assert finding.reason_code == "AGGREGATION_SCOPE_UNRESOLVED"


def test_reversed_order_extremum_still_contradicts_without_nested_aggregate():
    features, finding = _single_finding(
        "What is the maximum salary?",
        "SELECT salary FROM employee ORDER BY salary ASC LIMIT 1",
    )

    assert features.contradicted_count == 1
    assert finding.reason_code == "AGGREGATION_OPERATOR_CONFLICT"


def test_scalar_maximum_accepts_order_by_limit_one_equivalence():
    features, finding = _single_finding(
        "What is the maximum salary?",
        "SELECT salary FROM employee ORDER BY salary DESC LIMIT 1",
    )

    assert features.supported_count == 1
    assert finding.reason_code == "AGGREGATION_ALIGNMENT_MATCH"
    assert finding.details["realization"] == "ORDER_BY_LIMIT_1"


def test_scalar_maximum_accepts_projection_alias_in_order_by():
    features, finding = _single_finding(
        "What is the maximum salary?",
        "SELECT salary AS amount FROM employee ORDER BY amount DESC LIMIT 1",
    )

    assert features.supported_count == 1
    assert finding.reason_code == "AGGREGATION_ALIGNMENT_MATCH"
    assert finding.details["realization"] == "ORDER_BY_LIMIT_1"


def test_computed_order_expression_is_not_assessed_as_scalar_extreme():
    features, finding = _single_finding(
        "What is the maximum salary?",
        ("SELECT salary FROM employee " "ORDER BY salary + bonus DESC LIMIT 1"),
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"
    assert finding.details["realization"] == "COMPUTED_ORDER_BY_LIMIT_1"


def test_computed_projection_alias_is_not_assessed_as_scalar_extreme():
    features, finding = _single_finding(
        "What is the maximum salary?",
        "SELECT -salary AS amount FROM employee ORDER BY amount DESC LIMIT 1",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"
    assert finding.details["realization"] == "COMPUTED_ORDER_BY_LIMIT_1"


def test_derived_sources_with_same_column_name_remain_ambiguous():
    features, finding = _single_finding(
        "What is the average age?",
        (
            "WITH p AS (SELECT age FROM people), "
            "e AS (SELECT age FROM employees) "
            "SELECT AVG(p.age), SUM(e.age) FROM p JOIN e ON 1 = 1"
        ),
    )

    assert features.supported_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "AGGREGATION_ROLE_UNRESOLVED"
    assert finding.details["candidate_count"] == 2


def test_unrelated_computed_aggregate_does_not_block_direct_avg():
    features, finding = _single_finding(
        "What is the average age?",
        "SELECT AVG(age), SUM(salary) / COUNT(*) FROM people",
    )

    assert features.supported_count == 1
    assert finding.reason_code == "AGGREGATION_ALIGNMENT_MATCH"
    assert finding.details["column_name"] == "age"


def test_unrelated_precomputed_column_does_not_preempt_bound_raw_target():
    features, finding = _single_finding(
        "What is the average age?",
        "SELECT age, average_salary FROM people",
    )

    assert features.contradicted_count == 1
    assert finding.reason_code == "AGGREGATION_OPERATOR_CONFLICT"
    assert finding.details["column_name"] == "age"


def test_opaque_precomputed_target_preempts_only_distant_grouping_role():
    features, finding = _single_finding(
        "What is the average writing score of each school?",
        "SELECT School, AvgScrWrite FROM satscores",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "AGGREGATION_REALIZATION_UNSUPPORTED"
    assert finding.details["binding_kind"] == "PRECOMPUTED_COLUMN"


def test_no_aggregation_cue_is_not_applicable():
    features = detect_consistency(
        "What is the employee salary?",
        "SELECT salary FROM employee",
        rules=["aggregation_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.rule_records == []


def test_entity_returning_average_wording_is_outside_scalar_scope():
    features = detect_consistency(
        "Which department has the highest average salary?",
        (
            "SELECT department FROM employee GROUP BY department "
            "ORDER BY AVG(salary) DESC LIMIT 1"
        ),
        rules=["aggregation_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.rule_records == []


def test_evidence_aggregate_substitution_suppresses_new_rule_duplicate():
    features = detect_consistency(
        "What is the maximum salary?",
        "SELECT salary FROM employee WHERE salary = 100",
        context=ContextManifest(evidence_texts=["Use MAX(salary) from employee."]),
        rules=["literal_alignment", "aggregation_alignment"],
        emit_supported=True,
    )

    contradictions = [
        finding
        for finding in features.findings
        if finding.status == ConsistencyStatus.CONTRADICTED
    ]
    assert [finding.reason_code for finding in contradictions] == [
        "EVIDENCE_AGGREGATE_SUBSTITUTED"
    ]
