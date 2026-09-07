from __future__ import annotations

from text2sql_pipeline.analyzers.question_sql_consistency import (
    ContextManifest,
    detect_consistency,
)


def _single_finding(question: str, sql: str):
    features = detect_consistency(
        question,
        sql,
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )
    assert len(features.findings) == 1
    return features, features.findings[0]


def test_top_three_matches_descending_order_and_limit():
    features, finding = _single_finding(
        "Show the top 3 products by price.",
        "SELECT name FROM product ORDER BY price DESC LIMIT 3",
    )

    assert features.supported_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"
    assert finding.details["requested_n"] == 3
    assert finding.details["column_name"] == "price"


def test_bottom_five_matches_number_word_and_ascending_order():
    features, finding = _single_finding(
        "Show the bottom five products by price.",
        "SELECT name FROM product ORDER BY price ASC LIMIT 5",
    )

    assert features.supported_count == 1
    assert finding.details["requested_n"] == 5
    assert finding.details["requested_direction"] == "ASC"


def test_top_three_lowest_uses_lowest_as_direction_and_single_owner():
    features, finding = _single_finding(
        "Show the top three lowest aircraft distances.",
        "SELECT name FROM aircraft ORDER BY distance ASC LIMIT 3",
    )

    assert features.supported_count == 1
    assert finding.details["requested_direction"] == "ASC"
    assert finding.details["direction_basis"] == "lowest"


def test_alphabetical_order_overrides_bare_top_direction():
    features, finding = _single_finding(
        "List the top three elements in alphabetical order.",
        "SELECT element FROM atom ORDER BY element ASC LIMIT 3",
    )

    assert features.supported_count == 1
    assert finding.details["requested_direction"] == "ASC"


def test_weak_cue_takes_direction_from_an_adjacent_quality_adjective():
    for question, sql in (
        (
            "Show the top 3 worst products by rating.",
            "SELECT name FROM product ORDER BY rating ASC LIMIT 3",
        ),
        (
            "Show the bottom 3 best products by rating.",
            "SELECT name FROM product ORDER BY rating DESC LIMIT 3",
        ),
    ):
        features, finding = _single_finding(question, sql)

        assert features.contradicted_count == 0
        assert features.supported_count == 1
        assert finding.reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"


def test_polarity_word_outside_the_cue_phrase_does_not_set_direction():
    features, finding = _single_finding(
        "List the top 3 cities by population in the smallest state.",
        "SELECT city FROM city ORDER BY population DESC LIMIT 3",
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 1
    assert finding.details["requested_direction"] == "DESC"


def test_polarity_word_after_a_comma_does_not_set_direction():
    features, finding = _single_finding(
        "What are the top 3 salaries, and which is the least?",
        "SELECT salary FROM employees ORDER BY salary DESC LIMIT 3",
    )

    assert features.contradicted_count == 0
    assert finding.details["requested_direction"] == "DESC"


def test_polar_cue_is_not_inverted_by_a_distant_opposing_cue():
    features = detect_consistency(
        "Which country has the highest population in the region with the lowest area?",
        (
            "SELECT name FROM country "
            "WHERE region = (SELECT region FROM country ORDER BY area ASC LIMIT 1) "
            "ORDER BY population DESC LIMIT 1"
        ),
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.not_assessed_count == 1
    assert features.findings[0].details["binding_kind"] == "MULTI_STAGE_TOPK_EXCLUDED"


def test_polar_cue_with_opposing_non_cue_signal_is_ambiguous():
    features, finding = _single_finding(
        "Which country has the highest population with the smallest area?",
        "SELECT name FROM country ORDER BY population DESC LIMIT 1",
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"
    assert finding.details["direction_ambiguous"] is True
    assert finding.details["direction_basis"] == "highest+smallest"


def test_multi_stage_topk_abstains_before_root_limit_comparison():
    features = detect_consistency(
        "Which of the top 3 economies by GDP has the lowest agriculture share?",
        ("SELECT name FROM economy " "ORDER BY GDP DESC, agriculture ASC LIMIT 1"),
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.not_assessed_count == 1
    assert len(features.findings) == 1
    finding = features.findings[0]
    assert finding.reason_code == "ORDERING_TOPK_REALIZATION_UNSUPPORTED"
    assert finding.details["binding_kind"] == "MULTI_STAGE_TOPK_EXCLUDED"
    assert [cue["normalized"] for cue in finding.details["cues"]] == [
        "top 3",
        "lowest",
    ]
    assert set(finding.sql_locations) == {
        "ORDER BY GDP DESC, agriculture ASC",
        "LIMIT 1",
    }


def test_explicit_then_phrase_is_also_multi_stage():
    features = detect_consistency(
        (
            "Select the top 3 economies by GDP, then choose the one with "
            "the lowest agriculture share."
        ),
        (
            "SELECT name FROM ("
            "SELECT name, agriculture FROM economy ORDER BY GDP DESC LIMIT 3"
            ") top3 ORDER BY agriculture ASC LIMIT 1"
        ),
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.not_assessed_count == 1
    assert len(features.findings) == 1
    assert features.findings[0].details["binding_kind"] == "MULTI_STAGE_TOPK_EXCLUDED"


def test_wrong_limit_is_contradicted():
    features, finding = _single_finding(
        "Show the top 3 products by price.",
        "SELECT name FROM product ORDER BY price DESC LIMIT 5",
    )

    assert features.contradicted_count == 1
    assert finding.reason_code == "ORDERING_TOPK_LIMIT_CONFLICT"
    assert finding.details["actual_limit"] == 5


def test_wrong_direction_is_contradicted():
    features, finding = _single_finding(
        "Show the top 3 products by price.",
        "SELECT name FROM product ORDER BY price ASC LIMIT 3",
    )

    assert features.contradicted_count == 1
    assert finding.reason_code == "ORDERING_TOPK_DIRECTION_CONFLICT"


def test_explicit_inverse_metric_context_forces_abstention():
    features = detect_consistency(
        "Which year has the lowest speed of lap time?",
        "SELECT year FROM lap_time ORDER BY time DESC LIMIT 1",
        context=ContextManifest(
            evidence_texts=["lowest speed of lap time refers to MAX(time);"]
        ),
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert (
        features.findings[0].reason_code
        == "ORDERING_TOPK_CONTEXT_CONVENTION_UNRESOLVED"
    )
    assert "DATASET_EVIDENCE" in {
        source.value for source in features.findings[0].evidence_sources
    }


def test_explicit_top_k_without_order_by_is_contradicted():
    features, finding = _single_finding(
        "Show the top 3 products with the highest price.",
        "SELECT name FROM product LIMIT 3",
    )

    assert features.contradicted_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ORDER_MISSING"


def test_attributive_by_without_order_is_unresolved():
    features, finding = _single_finding(
        "Show the top 3 songs by the Beatles.",
        "SELECT name FROM song LIMIT 3",
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_bare_top_k_without_ranking_target_is_unresolved():
    features, finding = _single_finding(
        "Show the top 3 products.",
        "SELECT name FROM product LIMIT 3",
    )

    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_rank_predicate_alternative_is_not_assessed():
    features, finding = _single_finding(
        "Show the top 10 drivers by rank.",
        "SELECT name FROM driver WHERE rank <= 10",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "ORDERING_TOPK_REALIZATION_UNSUPPORTED"


def test_nested_max_selection_without_order_is_not_assessed():
    features, finding = _single_finding(
        "Show the top 3 films with the highest replacement cost.",
        (
            "SELECT title FROM film WHERE replacement_cost = "
            "(SELECT MAX(replacement_cost) FROM film) LIMIT 3"
        ),
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "ORDERING_TOPK_REALIZATION_UNSUPPORTED"


def test_wrong_order_column_is_unresolved_not_supported():
    features, finding = _single_finding(
        "Show the top 3 products by price.",
        "SELECT name FROM product ORDER BY rating DESC LIMIT 3",
    )

    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_computed_order_target_is_not_assessed():
    features, finding = _single_finding(
        "Show the top 3 products by price.",
        "SELECT name FROM product ORDER BY price + tax DESC LIMIT 3",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "ORDERING_TOPK_REALIZATION_UNSUPPORTED"


def test_nested_top_k_does_not_satisfy_root_request():
    features, finding = _single_finding(
        "Show the top 3 products by price.",
        (
            "SELECT name FROM ("
            "SELECT name, price FROM product ORDER BY price DESC LIMIT 3"
            ") ranked"
        ),
    )

    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_SCOPE_UNRESOLVED"


def test_first_and_last_n_do_not_create_candidates():
    for question in (
        "Show the first 3 products.",
        "Show the last five products.",
    ):
        features = detect_consistency(
            question,
            "SELECT name FROM product LIMIT 3",
            rules=["ordering_topk_alignment"],
            emit_supported=True,
        )
        assert features.applicable_rules == 0
        assert features.rule_records == []


def test_offset_is_not_assessed():
    features, finding = _single_finding(
        "Show the top 3 products by price.",
        "SELECT name FROM product ORDER BY price DESC LIMIT 3 OFFSET 1",
    )

    assert features.not_assessed_count == 1
    assert finding.reason_code == "ORDERING_TOPK_REALIZATION_UNSUPPORTED"


def test_no_topk_cue_is_not_applicable():
    features = detect_consistency(
        "Show products by price.",
        "SELECT name FROM product ORDER BY price DESC",
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.rule_records == []


def test_entity_highest_is_implicit_top_one_only():
    features, finding = _single_finding(
        "Which employee has the highest salary?",
        "SELECT name FROM employee ORDER BY salary DESC LIMIT 1",
    )

    assert features.supported_count == 1
    assert finding.details["implicit_one"] is True
    assert finding.details["requested_n"] == 1


def test_scalar_maximum_and_entity_highest_have_distinct_rule_owners():
    scalar = detect_consistency(
        "What is the maximum salary?",
        "SELECT MAX(salary) FROM employee",
        rules=["aggregation_alignment", "ordering_topk_alignment"],
        emit_supported=True,
    )
    entity = detect_consistency(
        "Which employee has the highest salary?",
        "SELECT name FROM employee ORDER BY salary DESC LIMIT 1",
        rules=["aggregation_alignment", "ordering_topk_alignment"],
        emit_supported=True,
    )

    assert [record.rule_id for record in scalar.rule_records] == [
        "aggregation_alignment"
    ]
    assert [record.rule_id for record in entity.rule_records] == [
        "ordering_topk_alignment"
    ]


def test_ambiguous_superlative_never_emits_two_contradictions():
    features = detect_consistency(
        "What is the highest salary?",
        "SELECT salary FROM employee",
        rules=["aggregation_alignment", "ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert [record.rule_id for record in features.rule_records] == [
        "ordering_topk_alignment"
    ]
