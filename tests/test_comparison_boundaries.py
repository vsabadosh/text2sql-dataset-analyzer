from __future__ import annotations

import pytest

from text2sql_pipeline.analyzers.question_sql_consistency import (
    ConsistencyStatus,
    detect_consistency,
)
from text2sql_pipeline.analyzers.question_sql_consistency.consistency_registry import (
    describe_reason_code,
)


def _finding(features, reason_code):
    return next(
        finding
        for finding in features.findings
        if finding.reason_code == reason_code
    )


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show customers older than 30.",
            "SELECT * FROM customer WHERE age > 30",
        ),
        (
            "Show departments with at least 10 employees.",
            "SELECT * FROM department WHERE employee_count >= 10",
        ),
        (
            "Show papers published in or before 2009.",
            "SELECT * FROM paper WHERE year <= 2009",
        ),
        (
            "Show orders with amount 100 or more.",
            "SELECT * FROM orders WHERE amount >= 100",
        ),
        (
            "Show products with a price larger than or equal to 180.",
            "SELECT * FROM product WHERE price >= 180",
        ),
        (
            "Show employees whose pay rate is equal or below 30.",
            "SELECT * FROM employee WHERE pay_rate <= 30",
        ),
        (
            "Show employees earning a salary on and above 12000.",
            "SELECT * FROM employee WHERE salary >= 12000",
        ),
        (
            "Show users no older than 18.",
            "SELECT * FROM users WHERE age <= 18",
        ),
    ],
)
def test_explicit_single_boundaries_are_supported(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "COMPARISON_BOUNDARY_MATCH")
    assert finding.status == ConsistencyStatus.SUPPORTED
    assert finding.question_spans
    assert finding.sql_locations


@pytest.mark.parametrize(
    "question,sql,expected,actual",
    [
        (
            "Show customers older than 30.",
            "SELECT * FROM customer WHERE age >= 30",
            "GT",
            "GTE",
        ),
        (
            "Show departments with at most 10 employees.",
            "SELECT * FROM department WHERE employee_count < 10",
            "LTE",
            "LT",
        ),
        (
            "Show papers since 2011.",
            "SELECT * FROM paper WHERE year > 2011",
            "GTE",
            "GT",
        ),
    ],
)
def test_explicit_single_boundary_conflicts_are_contradicted(
    question,
    sql,
    expected,
    actual,
):
    features = detect_consistency(
        question,
        sql,
        rules=["comparison_boundary_alignment"],
    )

    finding = _finding(features, "COMPARISON_BOUNDARY_CONFLICT")
    assert finding.status == ConsistencyStatus.CONTRADICTED
    assert finding.details["expected_operator"] == expected
    assert finding.details["actual_operator"] == actual


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show measure values between 10 and 20.",
            "SELECT * FROM measure WHERE value BETWEEN 10 AND 20",
        ),
        (
            "Show measure values from 10 through 20.",
            "SELECT * FROM measure WHERE value >= 10 AND value <= 20",
        ),
    ],
)
def test_inclusive_ranges_are_supported(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert _finding(features, "COMPARISON_RANGE_MATCH")


def test_strict_sql_range_conflicts_with_natural_language_between():
    features = detect_consistency(
        "Show measure values between 10 and 20.",
        "SELECT * FROM measure WHERE value > 10 AND value < 20",
        rules=["comparison_boundary_alignment"],
    )

    finding = _finding(features, "COMPARISON_RANGE_CONFLICT")
    assert finding.status == ConsistencyStatus.CONTRADICTED
    assert finding.details["actual_operators"] == ["GT", "LT"]


def test_negated_boundary_abstains_without_sql_negation_scope_analysis():
    features = detect_consistency(
        "Show items not bought more than 10 times.",
        "SELECT item_id FROM sale WHERE purchase_count <= 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "COMPARISON_BOUNDARY_NEGATION_UNRESOLVED")
    assert finding.status == ConsistencyStatus.UNRESOLVED


def test_clause_bounded_negation_is_not_limited_to_four_tokens():
    features = detect_consistency(
        "Show items that have not ever been purchased by more than 10 customers.",
        "SELECT item_id FROM sale WHERE purchase_count <= 10",
        rules=["comparison_boundary_alignment"],
    )

    assert _finding(features, "COMPARISON_BOUNDARY_NEGATION_UNRESOLVED")


def test_commas_do_not_terminate_negation_scope():
    features = detect_consistency(
        "Show people who do not, under any circumstances, have age greater than 10.",
        "SELECT * FROM person WHERE age > 10",
        rules=["comparison_boundary_alignment"],
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_BOUNDARY_NEGATION_UNRESOLVED")


@pytest.mark.parametrize("verb", ["Exclude", "Excluding"])
def test_exclusion_cues_abstain_instead_of_inverting_the_boundary(verb):
    features = detect_consistency(
        f"{verb} people older than 10.",
        "SELECT * FROM person WHERE age <= 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert _finding(
        features, "COMPARISON_BOUNDARY_NEGATION_UNRESOLVED"
    ).status == ConsistencyStatus.UNRESOLVED


def test_ambiguous_same_value_roles_remain_unresolved():
    features = detect_consistency(
        "Show rows with more than 10.",
        "SELECT * FROM record WHERE age > 10 AND salary > 10",
        rules=["comparison_boundary_alignment"],
    )

    finding = _finding(features, "COMPARISON_BOUNDARY_ROLE_UNRESOLVED")
    assert finding.status == ConsistencyStatus.UNRESOLVED


def test_role_binding_precedes_operator_compatibility():
    features = detect_consistency(
        "Show people with age greater than 10 and salary less than 10.",
        "SELECT * FROM person WHERE age < 10 AND salary > 10",
        rules=["comparison_boundary_alignment"],
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 2
    assert features.unresolved_count == 0


def test_single_sql_candidate_still_requires_question_role_binding():
    features = detect_consistency(
        "Show people with salary greater than 10.",
        "SELECT * FROM person WHERE age > 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_BOUNDARY_ROLE_UNRESOLVED")


def test_nearest_question_role_wins_over_earlier_role_mention():
    features = detect_consistency(
        "Show salary with age greater than 10.",
        "SELECT * FROM person WHERE salary > 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_BOUNDARY_ROLE_UNRESOLVED")


def test_generic_named_column_does_not_bypass_role_binding():
    features = detect_consistency(
        "Show people with salary greater than 10.",
        "SELECT * FROM person WHERE count > 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_BOUNDARY_ROLE_UNRESOLVED")


def test_count_noun_does_not_bind_to_an_identifier_boundary():
    features = detect_consistency(
        "Show departments with more than 10 employees.",
        "SELECT * FROM employee WHERE employee_id > 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert _finding(
        features, "COMPARISON_BOUNDARY_ROLE_UNRESOLVED"
    ).status == ConsistencyStatus.UNRESOLVED


def test_explicit_identifier_word_allows_an_identifier_boundary():
    features = detect_consistency(
        "Show employees with an employee ID greater than 10.",
        "SELECT * FROM employee WHERE employee_id > 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert _finding(
        features, "COMPARISON_BOUNDARY_MATCH"
    ).status == ConsistencyStatus.SUPPORTED


@pytest.mark.parametrize("operator", [">", "<"])
def test_roleless_constant_predicate_does_not_bind_boundary(operator):
    features = detect_consistency(
        "Show rows with item count more than 10.",
        f"SELECT * FROM record WHERE 1 {operator} 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert features.findings == []


def test_range_binding_prefers_the_question_role_not_first_sql_pair():
    features = detect_consistency(
        "Show people with age between 10 and 20.",
        (
            "SELECT * FROM person WHERE salary >= 10 AND salary <= 20 "
            "AND age >= 10 AND age <= 20"
        ),
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "COMPARISON_RANGE_MATCH")
    assert finding.details["column_name"] == "age"


def test_multiple_matching_ranges_are_resolved_by_question_role():
    features = detect_consistency(
        "Show people with age between 10 and 20.",
        (
            "SELECT * FROM person WHERE salary BETWEEN 10 AND 20 "
            "AND age BETWEEN 10 AND 20"
        ),
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "COMPARISON_RANGE_MATCH")
    assert finding.details["column_name"] == "age"


def test_range_on_wrong_sql_role_remains_unresolved():
    features = detect_consistency(
        "Show people with age between 10 and 20.",
        "SELECT * FROM person WHERE salary >= 10 AND salary <= 20",
        rules=["comparison_boundary_alignment"],
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_ROLE_UNRESOLVED")


def test_competing_cues_for_same_sql_value_remain_unresolved():
    features = detect_consistency(
        "List at least 5 users with less than 5 compliments.",
        (
            "SELECT user_id FROM compliment GROUP BY user_id "
            "HAVING COUNT(number_of_compliments) > 5"
        ),
        rules=["comparison_boundary_alignment"],
    )

    assert features.contradicted_count == 0
    assert all(
        finding.status == ConsistencyStatus.UNRESOLVED
        for finding in features.findings
    )


def test_conjunction_and_above_is_not_misread_as_postfix_boundary():
    features = detect_consistency(
        "Show themes with attendance below 100 and above 500.",
        (
            "SELECT theme FROM exhibition WHERE attendance < 100 "
            "INTERSECT SELECT theme FROM exhibition WHERE attendance > 500"
        ),
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 0
    assert features.findings == []


def test_hidden_threshold_without_an_explicit_value_is_out_of_scope():
    features = detect_consistency(
        "Show major cities.",
        "SELECT * FROM city WHERE population > 150000",
        rules=["comparison_boundary_alignment"],
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_discrete_boundary_rewrite_abstains_without_column_type_evidence():
    features = detect_consistency(
        "Show rows with more than 3 children.",
        "SELECT * FROM family WHERE child_count >= 4",
        rules=["comparison_boundary_alignment"],
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 0


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "What is the difference between players 6 and 23?",
            "SELECT score FROM player WHERE id IN (6, 23)",
        ),
        (
            "How many students are under advisor 415?",
            "SELECT count(*) FROM student WHERE advisor_id = 415",
        ),
    ],
)
def test_entity_comparison_language_does_not_become_boundary_conflict(
    question,
    sql,
):
    features = detect_consistency(
        question,
        sql,
        rules=["comparison_boundary_alignment"],
    )

    assert features.contradicted_count == 0


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show people older than 10.",
            "SELECT * FROM person WHERE NOT age > 10",
        ),
        (
            "Show measure values between 10 and 20.",
            "SELECT * FROM measure WHERE NOT value BETWEEN 10 AND 20",
        ),
    ],
)
def test_sql_negation_forces_boundary_abstention(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert _finding(features, "COMPARISON_SQL_NEGATION_UNRESOLVED")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM person WHERE (age > 10) IS FALSE",
        (
            "SELECT * FROM person p WHERE NOT EXISTS "
            "(SELECT 1 FROM qualification q WHERE q.person_id = p.id "
            "AND q.age > 10)"
        ),
    ],
)
def test_indirect_sql_negation_forces_boundary_abstention(sql):
    features = detect_consistency(
        "Show people older than 10.",
        sql,
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert all(
        finding.status == ConsistencyStatus.UNRESOLVED
        for finding in features.findings
    )


def test_boolean_equality_false_forces_boundary_abstention():
    features = detect_consistency(
        "Show people older than 10.",
        "SELECT * FROM person WHERE (age > 10) = FALSE",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_SQL_NEGATION_UNRESOLVED")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM person WHERE (age > 10) <> TRUE",
        (
            "SELECT * FROM person WHERE "
            "CASE WHEN active = 1 THEN age > 10 ELSE TRUE END"
        ),
    ],
)
def test_unsupported_sql_boolean_context_forces_abstention(sql):
    features = detect_consistency(
        "Show people older than 10.",
        sql,
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert _finding(features, "COMPARISON_SQL_NEGATION_UNRESOLVED")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM person WHERE (age > 10) = active",
        "SELECT * FROM person WHERE COALESCE(age > 10, FALSE)",
    ],
)
def test_other_sql_boolean_wrappers_force_abstention(sql):
    features = detect_consistency(
        "Show people older than 10.",
        sql,
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert _finding(features, "COMPARISON_SQL_NEGATION_UNRESOLVED")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT age > 10 AS is_old FROM person",
        "SELECT * FROM person ORDER BY age > 10",
        (
            "SELECT * FROM person p LEFT JOIN audit a "
            "ON a.person_id = p.id AND p.age > 10"
        ),
    ],
)
def test_non_filter_sql_comparisons_are_not_boundary_obligations(sql):
    features = detect_consistency(
        "Show people older than 10.",
        sql,
        rules=["comparison_boundary_alignment"],
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_disjunctive_bounds_do_not_form_a_supported_range():
    features = detect_consistency(
        "Show people with age between 10 and 20.",
        "SELECT * FROM person WHERE age >= 10 OR age <= 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_BOOLEAN_UNRESOLVED")


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM person WHERE age > 10 OR active = 1",
        "SELECT * FROM person WHERE age < 10 OR active = 1",
    ],
)
def test_single_disjunctive_boundary_abstains(sql):
    features = detect_consistency(
        "Show people older than 10.",
        sql,
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert _finding(features, "COMPARISON_BOOLEAN_CONTEXT_UNRESOLVED")


def test_long_natural_language_negation_does_not_support_positive_range():
    features = detect_consistency(
        "Show rows that do not under any circumstances have ages between 10 and 20.",
        "SELECT * FROM person WHERE age BETWEEN 10 AND 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_NEGATION_UNRESOLVED")


def test_comma_delimited_range_negation_remains_unresolved():
    features = detect_consistency(
        "Show rows that do not, under any circumstances, have ages between 10 and 20.",
        "SELECT * FROM person WHERE age BETWEEN 10 AND 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_NEGATION_UNRESOLVED")


def test_degenerate_between_does_not_collapse_endpoint_operators():
    features = detect_consistency(
        "Show measure values between 10 and 10.",
        "SELECT * FROM measure WHERE value BETWEEN 10 AND 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show rows with more than five hundred items.",
            "SELECT * FROM record WHERE items > 5",
        ),
        (
            "Show rows with one hundred or more items.",
            "SELECT * FROM record WHERE items >= 1",
        ),
        (
            "Show rows with more than 5,000 items.",
            "SELECT * FROM record WHERE items > 5",
        ),
        (
            "Show rows with more than 5k items.",
            "SELECT * FROM record WHERE items > 5",
        ),
        (
            "Show rows with more than minus five items.",
            "SELECT * FROM record WHERE items > 5",
        ),
    ],
)
def test_number_word_subspans_do_not_bind_smaller_sql_values(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["comparison_boundary_alignment"],
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT age FROM person GROUP BY age HAVING COUNT(*) > 10",
        "SELECT age FROM person GROUP BY age HAVING COUNT(age) > 10",
    ],
)
def test_count_aggregate_does_not_answer_average_age_boundary(sql):
    features = detect_consistency(
        "Show average age greater than 10.",
        sql,
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0


@pytest.mark.parametrize("operator", [">", "<"])
def test_sum_does_not_answer_maximum_boundary(operator):
    features = detect_consistency(
        "Show maximum salary greater than 10.",
        (
            "SELECT department_id FROM employee GROUP BY department_id "
            f"HAVING SUM(salary) {operator} 10"
        ),
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0


def test_exact_value_does_not_treat_multi_value_in_as_equality():
    features = detect_consistency(
        "Show record rows with exactly 10 items.",
        "SELECT * FROM record WHERE items IN (10, 20)",
        rules=["comparison_boundary_alignment"],
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_BOUNDARY_REALIZATION_UNRESOLVED")


def test_higher_ordinal_rank_has_ambiguous_numeric_polarity():
    features = detect_consistency(
        "Show clubs with overall ranking higher than 100.",
        "SELECT * FROM club WHERE overall_ranking < 100",
        rules=["comparison_boundary_alignment"],
    )

    assert features.contradicted_count == 0
    assert _finding(features, "COMPARISON_ORDINAL_POLARITY_UNRESOLVED")


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show clubs with ranking above 100.",
            "SELECT * FROM club WHERE ranking < 100",
        ),
        (
            "Show clubs with ranking higher than or equal to 100.",
            "SELECT * FROM club WHERE ranking <= 100",
        ),
    ],
)
def test_all_higher_lower_ordinal_cues_abstain(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["comparison_boundary_alignment"],
    )

    assert features.contradicted_count == 0
    assert _finding(features, "COMPARISON_ORDINAL_POLARITY_UNRESOLVED")


@pytest.mark.parametrize("column", ["place", "placement", "seed"])
def test_other_ordinal_role_names_also_abstain(column):
    features = detect_consistency(
        f"Show runners with {column} higher than 10.",
        f"SELECT * FROM runner WHERE {column} < 10",
        rules=["comparison_boundary_alignment"],
    )

    assert features.contradicted_count == 0
    assert _finding(features, "COMPARISON_ORDINAL_POLARITY_UNRESOLVED")


def test_until_range_allows_exclusive_upper_boundary():
    features = detect_consistency(
        "Show result scores from 10 until 20.",
        "SELECT * FROM result WHERE score >= 10 AND score < 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert _finding(features, "COMPARISON_RANGE_MATCH")


def test_until_inclusive_marker_remains_unresolved_in_v1():
    features = detect_consistency(
        "Show result scores from 10 until 20 inclusive.",
        "SELECT * FROM result WHERE score >= 10 AND score <= 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_MODIFIER_UNRESOLVED")


def test_until_and_including_remains_unresolved_in_v1():
    features = detect_consistency(
        "Show result scores from 10 until and including 20.",
        "SELECT * FROM result WHERE score >= 10 AND score <= 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_MODIFIER_UNRESOLVED")


def test_until_not_inclusive_remains_unresolved_in_v1():
    features = detect_consistency(
        "Show result scores from 10 until 20 not inclusive.",
        "SELECT * FROM result WHERE score >= 10 AND score < 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_MODIFIER_UNRESOLVED")


def test_explicit_lower_modifier_remains_unresolved_in_v1():
    features = detect_consistency(
        "Show result scores from 10 exclusive until 20.",
        "SELECT * FROM result WHERE score > 10 AND score < 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_MODIFIER_UNRESOLVED")


def test_explicitly_exclusive_between_range_remains_unresolved():
    features = detect_consistency(
        "Show result scores between 10 and 20 exclusive.",
        "SELECT * FROM result WHERE score > 10 AND score < 20",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_MODIFIER_UNRESOLVED")


def test_mixed_lower_inclusive_until_range_remains_unresolved():
    features = detect_consistency(
        "Show result scores from 10 inclusive until 20.",
        "SELECT * FROM result WHERE score >= 10 AND score < 20",
        rules=["comparison_boundary_alignment"],
    )

    assert features.supported_count == 0
    assert _finding(features, "COMPARISON_RANGE_MODIFIER_UNRESOLVED")


def test_duplicate_equivalent_cues_emit_one_boundary_finding():
    features = detect_consistency(
        "Show record rows with at least 10 or more items.",
        "SELECT * FROM record WHERE items >= 10",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    matches = [
        finding
        for finding in features.findings
        if finding.reason_code == "COMPARISON_BOUNDARY_MATCH"
    ]
    assert len(matches) == 1


def test_unreliable_sql_scope_makes_boundary_rule_abstain():
    features = detect_consistency(
        "Show records with more than 10.",
        (
            "SELECT * FROM users AS T2 JOIN audit AS T2 ON T2.id = T2.id "
            "WHERE T2.score < 10"
        ),
        rules=["comparison_boundary_alignment"],
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_uncorrelated_inner_scope_does_not_answer_outer_boundary_question():
    features = detect_consistency(
        "Show people older than 10.",
        (
            "SELECT * FROM person p WHERE EXISTS "
            "(SELECT 1 FROM qualification q WHERE q.age > 10)"
        ),
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.findings == []


@pytest.mark.parametrize("set_operator", ["UNION", "EXCEPT"])
def test_set_operation_branch_does_not_prove_global_boundary(set_operator):
    features = detect_consistency(
        "Show people older than 10.",
        (
            "SELECT * FROM person WHERE age > 10 "
            f"{set_operator} SELECT * FROM person WHERE active = 1"
        ),
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0


def test_correlated_child_entity_does_not_answer_parent_boundary_question():
    features = detect_consistency(
        "Show parents older than 10.",
        (
            "SELECT * FROM parent p WHERE EXISTS "
            "(SELECT 1 FROM child c WHERE c.parent_id = p.id AND c.age > 10)"
        ),
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.findings == []


def test_correlated_roleless_aggregate_is_outside_v1_scope():
    features = detect_consistency(
        "Show parents with more than 10 awards.",
        (
            "SELECT * FROM parent p WHERE EXISTS "
            "(SELECT 1 FROM child c WHERE c.parent_id = p.id "
            "GROUP BY c.parent_id HAVING COUNT(*) > 10)"
        ),
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.findings == []


@pytest.mark.parametrize(
    "reason_code",
    [
        "COMPARISON_BOOLEAN_CONTEXT_UNRESOLVED",
        "COMPARISON_RANGE_BOOLEAN_UNRESOLVED",
        "COMPARISON_RANGE_MODIFIER_UNRESOLVED",
        "COMPARISON_RANGE_NEGATION_UNRESOLVED",
        "COMPARISON_SQL_NEGATION_UNRESOLVED",
    ],
)
def test_all_boundary_abstention_reasons_have_report_text(reason_code):
    assert describe_reason_code(reason_code)


def test_temporal_year_word_between_cue_and_value_is_supported():
    features = detect_consistency(
        "Show bikes purchased after year 2015.",
        "SELECT * FROM bike WHERE purchase_year > 2015",
        rules=["comparison_boundary_alignment"],
        emit_supported=True,
    )

    assert _finding(features, "COMPARISON_BOUNDARY_MATCH")


def test_temporal_evidence_is_not_dropped_when_boundary_rule_is_enabled():
    features = detect_consistency(
        "Show bikes purchased after year 2015.",
        "SELECT * FROM bike WHERE purchase_year > 2015",
        rules=[
            "comparison_boundary_alignment",
            "temporal_anchor_provenance",
        ],
        emit_supported=True,
    )

    assert _finding(features, "COMPARISON_BOUNDARY_MATCH")
    assert any(
        finding.reason_code == "TEMPORAL_OPERATOR_ALIGNMENT_DEFERRED"
        for finding in features.findings
    )


def test_boundary_rule_does_not_hide_a_temporal_value_conflict():
    features = detect_consistency(
        "Show races after 2004.",
        "SELECT * FROM race WHERE year > 2014",
        rules=[
            "comparison_boundary_alignment",
            "temporal_anchor_provenance",
        ],
    )

    assert _finding(features, "EXPLICIT_TEMPORAL_VALUE_CONFLICT")
