from __future__ import annotations

import pytest

from text2sql_pipeline.analyzers.question_sql_consistency import (
    ConsistencyStatus,
    ContextManifest,
    detect_consistency,
    detect_paraphrase_twin_typos,
)


def _finding(features, reason_code):
    return next(
        finding for finding in features.findings if finding.reason_code == reason_code
    )


def test_literal_exact_match_is_supported_and_can_be_hidden():
    features = detect_consistency(
        "Show customers from California older than 21.",
        "SELECT * FROM customers WHERE state = 'California' AND age > 21",
        rules=["literal_alignment"],
        emit_supported=False,
    )

    assert features.parseable is True
    assert features.applicable_rules == 1
    assert features.supported_count == 2
    assert features.contradicted_count == 0
    assert features.unresolved_count == 0
    assert features.findings == []


def test_literal_without_question_or_context_source_is_unresolved():
    features = detect_consistency(
        "Show active customers.",
        "SELECT * FROM customers WHERE status = 'ZXQ-17'",
        rules=["literal_alignment"],
    )

    assert features.unresolved_count == 1
    finding = _finding(features, "SQL_LITERAL_UNLICENSED")
    assert finding.status == ConsistencyStatus.UNRESOLVED
    assert finding.details["sql_value"] == "ZXQ-17"


def test_literal_can_be_licensed_by_dataset_evidence():
    features = detect_consistency(
        "Show active customers.",
        "SELECT * FROM customers WHERE status = 'PAID'",
        context=ContextManifest(evidence_texts=["active means status PAID"]),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.status == ConsistencyStatus.SUPPORTED
    assert "DATASET_EVIDENCE" in {source.value for source in finding.evidence_sources}


def test_negated_dataset_evidence_does_not_license_a_literal():
    features = detect_consistency(
        "Show active customers.",
        "SELECT * FROM customers WHERE status = 'PAID'",
        context=ContextManifest(
            evidence_texts=["PAID does not mean active; active means OPEN"]
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert not any(
        finding.reason_code == "LITERAL_EXPLICITLY_LICENSED"
        for finding in features.findings
    )
    assert _finding(features, "SQL_LITERAL_UNLICENSED")


@pytest.mark.parametrize(
    "evidence",
    [
        "active means OPEN rather than PAID",
        "active means OPEN as opposed to PAID",
    ],
)
def test_contrastive_dataset_evidence_does_not_license_rejected_value(evidence):
    features = detect_consistency(
        "Show active customers.",
        "SELECT * FROM customers WHERE status = 'PAID'",
        context=ContextManifest(evidence_texts=[evidence]),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert not any(
        finding.reason_code == "LITERAL_EXPLICITLY_LICENSED"
        for finding in features.findings
    )


def test_negated_aggregate_evidence_is_not_normative():
    features = detect_consistency(
        "Show rows with rating one.",
        "SELECT * FROM review WHERE rating = 1",
        context=ContextManifest(
            evidence_texts=["Do not use MIN(rating); rating 1 is requested"]
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


@pytest.mark.parametrize(
    "evidence",
    [
        "Use rating 1 rather than MIN(rating)",
        "MIN(rating) isn't required; use rating 1",
        "There is no need to use MIN(rating)",
    ],
)
def test_contrastive_aggregate_mentions_are_not_normative(evidence):
    features = detect_consistency(
        "Show rows with rating one.",
        "SELECT * FROM review WHERE rating = 1",
        context=ContextManifest(evidence_texts=[evidence]),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


def test_literal_can_be_licensed_by_explicit_alias_manifest():
    features = detect_consistency(
        "Show customers in the USA.",
        "SELECT * FROM customers WHERE country = 'United States'",
        context=ContextManifest(value_aliases={"United States": ["USA", "US"]}),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.status == ConsistencyStatus.SUPPORTED
    assert "CONTEXT_MANIFEST" in {source.value for source in finding.evidence_sources}


def test_hidden_qualitative_threshold_gets_a_specific_abstention():
    features = detect_consistency(
        "List all major cities.",
        "SELECT name FROM city WHERE population > 150000",
        rules=["literal_alignment"],
    )

    finding = _finding(features, "IMPLICIT_THRESHOLD_UNLICENSED")
    assert finding.status == ConsistencyStatus.UNRESOLVED
    assert finding.target.value == "CONTEXT"
    assert finding.details["qualitative_cue"] == "major"
    assert finding.details["column_name"] == "population"


def test_boolean_flag_requires_a_binary_domain_for_support():
    unresolved = detect_consistency(
        "Count the searches made by buyers.",
        "SELECT count(*) FROM searches WHERE is_buyer = 1",
        rules=["literal_alignment"],
        emit_supported=True,
    )
    supported = detect_consistency(
        "Count the searches made by buyers.",
        "SELECT count(*) FROM searches WHERE is_buyer = 1",
        context=ContextManifest(column_domains={"is_buyer": [0, 1]}),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    unresolved_finding = _finding(unresolved, "BOOLEAN_FLAG_LITERAL")
    supported_finding = _finding(supported, "BOOLEAN_FLAG_LITERAL")
    assert unresolved_finding.status == ConsistencyStatus.UNRESOLVED
    assert unresolved_finding.details["domain_confirmed"] is False
    assert supported_finding.status == ConsistencyStatus.SUPPORTED
    assert supported_finding.details["domain_confirmed"] is True
    assert supported_finding.target.value == "MAPPING"
    assert "CONTEXT_MANIFEST" in {
        source.value for source in supported_finding.evidence_sources
    }


def test_qualified_boolean_domain_does_not_cross_tables():
    features = detect_consistency(
        "Show active audit records.",
        "SELECT * FROM audit WHERE audit.is_active = 1",
        context=ContextManifest(
            column_domains={"users.is_active": [0, 1]}
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "BOOLEAN_FLAG_LITERAL")
    assert finding.status == ConsistencyStatus.UNRESOLVED
    assert finding.details["domain_confirmed"] is False


def test_qualified_boolean_domain_has_priority_over_unqualified_default():
    features = detect_consistency(
        "Show active audit records.",
        "SELECT * FROM audit WHERE audit.is_active = 1",
        context=ContextManifest(
            column_domains={
                "is_active": [0, 1],
                "audit.is_active": [0, 1, 2],
            }
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0


def test_conflicting_alias_and_table_domains_do_not_support_boolean_mapping():
    features = detect_consistency(
        "Show active audit records.",
        "SELECT * FROM audit AS a WHERE a.is_active = 1",
        context=ContextManifest(
            column_domains={
                "a.is_active": [0, 1],
                "audit.is_active": [0, 1, 2],
            }
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0


def test_exclusion_language_does_not_support_positive_boolean_flag():
    features = detect_consistency(
        "Count searches excluding buyers.",
        "SELECT count(*) FROM search WHERE is_buyer = 1",
        context=ContextManifest(
            column_domains={"search.is_buyer": [0, 1]}
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0


def test_ordinary_numeric_column_is_not_guessed_to_be_boolean():
    features = detect_consistency(
        "Show drivers who won.",
        "SELECT name FROM drivers WHERE wins = 1",
        rules=["literal_alignment"],
    )

    assert features.unresolved_count == 1
    assert _finding(features, "SQL_LITERAL_UNLICENSED")


def test_evidence_aggregate_substituted_by_constant_is_contradicted():
    features = detect_consistency(
        "Which brand received the lowest rating?",
        "SELECT brand FROM review WHERE StarRating = 1",
        context=ContextManifest(
            evidence_texts=["lowest rating refers to MIN(StarRating)"]
        ),
        rules=["literal_alignment"],
    )

    finding = _finding(features, "EVIDENCE_AGGREGATE_SUBSTITUTED")
    assert finding.status == ConsistencyStatus.CONTRADICTED
    assert finding.target.value == "SQL"
    assert finding.details["required_aggregate"] == "MIN"


def test_order_by_limit_realizes_the_evidence_aggregate():
    features = detect_consistency(
        "Which brand received the lowest rating?",
        (
            "SELECT brand FROM review WHERE published = 1 "
            "ORDER BY StarRating ASC LIMIT 1"
        ),
        context=ContextManifest(
            evidence_texts=["lowest rating refers to MIN(StarRating)"]
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


def test_non_equality_is_not_an_aggregate_substitution():
    features = detect_consistency(
        "Which brands have a positive rating?",
        "SELECT brand FROM review WHERE StarRating > 0",
        context=ContextManifest(
            evidence_texts=["lowest rating refers to MIN(StarRating)"]
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


def test_max_of_count_evidence_is_not_treated_as_value_aggregate():
    features = detect_consistency(
        "Which group has the most members?",
        "SELECT group_id FROM groups WHERE member_id = 1",
        context=ContextManifest(
            evidence_texts=["most members refers to MAX(COUNT(member_id))"]
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


def test_count_of_max_evidence_is_not_treated_as_direct_value_aggregate():
    features = detect_consistency(
        "How many establishments have the highest risk?",
        "SELECT count(*) FROM establishment WHERE risk_level = 3",
        context=ContextManifest(
            evidence_texts=["total establishments = COUNT(MAX(risk_level))"]
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


def test_rank_one_without_a_domain_invariant_remains_unresolved():
    features = detect_consistency(
        "In which race did the driver rank highest?",
        "SELECT race FROM result WHERE rank = 1",
        context=ContextManifest(
            evidence_texts=["rank highest refers to MIN(rank)"]
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )
    finding = _finding(features, "AGGREGATE_CONSTANT_EQUIVALENCE_UNPROVEN")
    assert finding.status == ConsistencyStatus.UNRESOLVED
    assert finding.target.value == "CONTEXT"


def test_sum_divided_by_count_realizes_average_evidence():
    features = detect_consistency(
        "What is the average answer?",
        (
            "SELECT CAST(SUM(AnswerText) AS REAL) / COUNT(UserID) "
            "FROM Answer WHERE AnswerText = 'United States'"
        ),
        context=ContextManifest(
            evidence_texts=["average answer refers to AVG(AnswerText)"]
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


def test_sum_and_count_without_division_do_not_realize_average():
    features = detect_consistency(
        "Show the relevant rows.",
        "SELECT SUM(score), COUNT(*) FROM result WHERE score = 1",
        context=ContextManifest(
            evidence_texts=["required score refers to AVG(result.score)"]
        ),
        rules=["literal_alignment"],
    )

    assert _finding(features, "EVIDENCE_AGGREGATE_SUBSTITUTED")


def test_unrelated_subquery_aggregate_does_not_suppress_substitution():
    features = detect_consistency(
        "Show the relevant orders.",
        (
            "SELECT * FROM orders AS o WHERE o.amount = 10 "
            "AND EXISTS (SELECT MIN(r.amount) FROM refunds AS r)"
        ),
        context=ContextManifest(
            evidence_texts=["required amount refers to MIN(orders.amount)"]
        ),
        rules=["literal_alignment"],
    )

    finding = _finding(features, "EVIDENCE_AGGREGATE_SUBSTITUTED")
    assert finding.details["table_name"] == "orders"


def test_descendant_same_source_aggregate_does_not_suppress_outer_substitution():
    features = detect_consistency(
        "Show the relevant orders.",
        (
            "SELECT * FROM orders AS o WHERE o.amount = 10 "
            "AND EXISTS (SELECT MIN(x.amount) FROM orders AS x)"
        ),
        context=ContextManifest(
            evidence_texts=["required amount refers to MIN(orders.amount)"]
        ),
        rules=["literal_alignment"],
    )

    assert _finding(features, "EVIDENCE_AGGREGATE_SUBSTITUTED")


def test_evidence_source_table_blocks_same_named_column_on_another_table():
    features = detect_consistency(
        "Show patients with the requested immunization.",
        (
            "SELECT * FROM immunizations AS i "
            "WHERE i.description = 'Influenza vaccine'"
        ),
        context=ContextManifest(
            evidence_texts=[
                "most common condition refers to MAX(description) from conditions"
            ]
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


def test_same_source_average_in_another_scope_is_an_existing_realization():
    features = detect_consistency(
        "Show the average answer for US respondents.",
        (
            "SELECT CAST(SUM(a.answer_text) AS REAL) / COUNT(a.user_id) "
            "FROM answer AS a WHERE a.question_id = 1 "
            "AND a.user_id IN (SELECT b.user_id FROM answer AS b "
            "WHERE b.answer_text = 'United States')"
        ),
        context=ContextManifest(
            evidence_texts=["average answer refers to AVG(answer_text)"]
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EVIDENCE_AGGREGATE_SUBSTITUTED"
        for finding in features.findings
    )


def test_unrequested_common_word_filter_waits_for_corpus_confirmation():
    features = detect_consistency(
        "In what year was the artist who created a painting in 1884 born?",
        "SELECT birthYear FROM artist WHERE mediumOn = 'canvas'",
        rules=["literal_alignment"],
    )

    finding = _finding(features, "UNREQUESTED_FILTER")
    assert finding.status == ConsistencyStatus.UNRESOLVED
    assert finding.target.value == "SQL"
    assert finding.details["corpus_gate"] == "LICENSED_PEER_MAJORITY"


def test_unparsed_dataset_evidence_blocks_unrequested_filter_promotion():
    features = detect_consistency(
        "List directly charter-funded schools.",
        "SELECT name FROM school WHERE funding_type = 'Directly funded'",
        context=ContextManifest(
            evidence_texts=["direct charter-funded describes the funding category"]
        ),
        rules=["literal_alignment"],
    )

    assert _finding(features, "SQL_LITERAL_UNLICENSED")
    assert not any(
        finding.reason_code == "UNREQUESTED_FILTER"
        for finding in features.findings
    )


@pytest.mark.parametrize(
    "question,value",
    [
        (
            "How many courses does Computer Information Systmes offer?",
            "Computer Info. Systems",
        ),
        ("Which students tried out for the position of goal?", "goalie"),
        ("Show all video games that are collectible cards.", "Collectible card game"),
        ("Show papers on keyphrase0 by Brian Curless.", "convolution"),
        ("Show papers on ${entity} by Brian Curless.", "convolution"),
        ("Show parties with delegates on Appropriations and", "Economic Matters"),
        ("Show grants from organisation type described", "Research"),
    ],
)
def test_lexical_ambiguity_and_placeholders_are_not_unrequested_filters(
    question, value
):
    features = detect_consistency(
        question,
        f"SELECT id FROM records WHERE category = '{value}'",
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "UNREQUESTED_FILTER"
        for finding in features.findings
    )


def test_computed_superlative_does_not_hide_an_unrequested_filter_candidate():
    features = detect_consistency(
        "Which collection has the most documents?",
        (
            "SELECT collection_id, count(*) FROM collection "
            "WHERE name = 'Best' GROUP BY collection_id "
            "ORDER BY count(*) DESC LIMIT 1"
        ),
        rules=["literal_alignment"],
    )

    assert _finding(features, "UNREQUESTED_FILTER")


def test_corpus_records_retain_hidden_supported_obligations():
    features = detect_consistency(
        "Show customers from California.",
        "SELECT id FROM customer WHERE state = 'California'",
        rules=["literal_alignment"],
        emit_supported=False,
    )

    assert features.findings == []
    assert len(features.corpus_records) == 1
    assert features.corpus_records[0].status == ConsistencyStatus.SUPPORTED
    assert features.corpus_records[0].column_name == "state"


def test_double_quoted_identifier_is_not_a_postgres_string_literal():
    features = detect_consistency(
        "Match the expected status.",
        'SELECT * FROM customer WHERE status = "expected_status"',
        dialect="postgres",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_number_word_licenses_numeric_sql_literal():
    features = detect_consistency(
        "Show departments with more than five employees.",
        "SELECT * FROM department WHERE employee_count > 5",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 1
    assert (
        _finding(features, "LITERAL_EXPLICITLY_LICENSED").question_spans[0].text
        == "five"
    )


@pytest.mark.parametrize(
    "literal",
    ["1e100", "123456789012345678901234567890123456789012345678901234"],
)
def test_large_numeric_literals_abstain_without_crashing(literal):
    features = detect_consistency(
        "Show requested rows.",
        f"SELECT * FROM t WHERE amount = {literal}",
        rules=["literal_alignment"],
    )

    assert features.parseable is True
    assert features.unresolved_count == 1


def test_question_typo_is_derived_from_identifier_used_by_gold_sql():
    features = detect_consistency(
        "Count the number of coutries.",
        "SELECT count(DISTINCT country) FROM City",
        rules=["question_lexical_integrity"],
    )

    assert features.applicable_rules == 1
    assert features.contradicted_count == 1
    finding = _finding(features, "QUESTION_TOKEN_SQL_IDENTIFIER_NEAR_MISS")
    assert finding.target.value == "QUESTION"
    assert finding.details == {
        "question_token": "coutries",
        "expected_token": "countries",
        "sql_identifier": "country",
        "sql_identifier_kind": "COLUMN",
        "candidate_identifiers": [
            {"identifier": "country", "kind": "COLUMN"},
        ],
        "distance": 1,
        "binding": "SQL_IDENTIFIER",
    }
    assert finding.question_spans[0].text == "coutries"
    assert finding.sql_locations == ["COLUMN country"]
    assert {source.value for source in finding.evidence_sources} == {
        "QUESTION_TEXT",
        "SQL_AST",
    }


def test_regular_question_word_and_inflection_are_not_typos():
    for question in (
        "How many countries do we have?",
        "How many cities are in each country?",
    ):
        features = detect_consistency(
            question,
            "SELECT count(DISTINCT country) FROM City",
            rules=["question_lexical_integrity"],
        )
        assert features.contradicted_count == 0


def test_question_lexical_rule_does_not_take_over_literal_direction():
    features = detect_consistency(
        "List all tracks bought by customer Daan Peeters.",
        'SELECT name FROM customers WHERE first_name = "Daan"',
        rules=["question_lexical_integrity"],
    )

    assert features.contradicted_count == 0


def test_question_lexical_rule_leaves_literal_near_misses_to_literal_alignment():
    features = detect_consistency(
        "Show acounts.",
        "SELECT accounts FROM ledger WHERE category = 'account'",
        rules=["question_lexical_integrity"],
    )
    twin_findings = detect_paraphrase_twin_typos(
        "Find customers with a Mortage loan.",
        "SELECT name FROM loans WHERE loan_type = 'Mortgages'",
        [("clean", "Find customers with a Mortgages loan.")],
    )

    assert features.contradicted_count == 0
    assert twin_findings == []


def test_identical_sql_peer_is_not_a_trusted_paraphrase_by_default():
    peer = detect_paraphrase_twin_typos(
        "Who receieved the package?",
        "SELECT recipient FROM package",
        [("clean", "Who received the package?")],
    )
    trusted = detect_paraphrase_twin_typos(
        "Who receieved the package?",
        "SELECT recipient FROM package",
        [("clean", "Who received the package?")],
        trusted_paraphrases=True,
    )

    assert peer[0].status == ConsistencyStatus.UNRESOLVED
    assert peer[0].reason_code == "QUESTION_TOKEN_IDENTICAL_SQL_PEER_NEAR_MISS"
    assert trusted[0].status == ConsistencyStatus.CONTRADICTED
    assert trusted[0].reason_code == "QUESTION_TOKEN_PARAPHRASE_TWIN_NEAR_MISS"


def test_identifier_suffix_and_derivation_guards_prevent_false_typos():
    features = detect_consistency(
        "Which datasets are used by each high schooler?",
        "SELECT datasetid FROM school",
        rules=["question_lexical_integrity"],
    )

    assert features.contradicted_count == 0


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "List the texts of all messages that were reshared.",
            "SELECT text FROM message WHERE IsReshare = 1",
        ),
        (
            "How many cast members were uncredited?",
            "SELECT count(*) FROM cast_member WHERE credited = 0",
        ),
    ],
)
def test_productive_prefixed_words_are_not_identifier_typos(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["question_lexical_integrity"],
    )

    assert features.contradicted_count == 0


def test_rule_uses_only_identifiers_from_the_current_gold_sql():
    features = detect_consistency(
        "Show the custmers.",
        "SELECT country FROM City",
        rules=["question_lexical_integrity"],
    )

    assert features.contradicted_count == 0


def test_spider_train_641_detects_near_miss_mismatch():
    features = detect_consistency(
        "What are the tracks that Dean Peeters bought?",
        (
            "SELECT T1.name FROM tracks AS T1 "
            "JOIN invoice_lines AS T2 ON T1.id = T2.track_id "
            "JOIN invoices AS T3 ON T3.id = T2.invoice_id "
            "JOIN customers AS T4 ON T4.id = T3.customer_id "
            'WHERE T4.first_name = "Daan" '
            'AND T4.last_name = "Peeters";'
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 1
    assert features.supported_count == 1
    finding = _finding(features, "NEAR_MISS_LITERAL_MISMATCH")
    assert finding.details["question_value"] == "Dean"
    assert finding.details["sql_value"] == "Daan"
    assert finding.details["binding"] == "STRONG_PAIR"
    assert {assumption.code for assumption in finding.assumptions} == {
        "SQLITE_DQS_STRING_FALLBACK",
        "NEAR_MISS_SIBLING_ADJACENCY",
        "LEXICAL_RESOURCE_VERSIONS",
    }


def test_context_alias_prevents_a_near_miss_contradiction():
    features = detect_consistency(
        "What are the tracks that Dean Peeters bought?",
        (
            "SELECT name FROM customers "
            'WHERE first_name = "Daan" AND last_name = "Peeters"'
        ),
        context=ContextManifest(value_aliases={"Daan": ["Dean"]}),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 2


def test_near_miss_is_detected_without_naming_any_column():
    features = detect_consistency(
        "How much surface area do the countires in the Carribean cover together?",
        'SELECT SUM(SurfaceArea) FROM country WHERE Region = "Caribbean"',
        rules=["literal_alignment"],
    )

    finding = _finding(features, "NEAR_MISS_LITERAL_MISMATCH")
    assert finding.status == ConsistencyStatus.CONTRADICTED
    assert finding.details["binding"] == "WEAK_UNIQUE"
    assert finding.details["question_value"] == "Carribean"


def test_strong_pair_survives_a_second_unlicensed_literal():
    features = detect_consistency(
        "How many lessons did the customer Ryan Goodwin complete?",
        (
            "SELECT count(*) FROM lessons AS T1 "
            "JOIN customers AS T2 ON T1.customer_id = T2.customer_id "
            'WHERE T2.first_name = "Rylan" AND T2.last_name = "Goodwin" '
            'AND T1.lesson_status_code = "Completed"'
        ),
        rules=["literal_alignment"],
    )

    finding = _finding(features, "NEAR_MISS_LITERAL_MISMATCH")
    assert finding.details["binding"] == "STRONG_PAIR"
    assert finding.details["question_value"] == "Ryan"
    # The independent status value is now licensed through the guarded
    # complete/completed derivational relation.
    assert features.unresolved_count == 0
    assert features.supported_count == 2


def test_disjunctive_siblings_do_not_vouch_for_each_other():
    """An OR branch describes an alternative row, so it cannot bind a neighbour."""
    conjunctive = detect_consistency(
        "What are the tracks that Dean Peeters bought?",
        'SELECT name FROM customers WHERE first_name = "Daan" AND last_name = "Peeters"',
        rules=["literal_alignment"],
    )
    disjunctive = detect_consistency(
        "What are the tracks that Dean Peeters bought?",
        'SELECT name FROM customers WHERE first_name = "Daan" OR last_name = "Peeters"',
        rules=["literal_alignment"],
    )
    both_unlicensed = detect_consistency(
        "Which tracks did Dean Peeters buy in Amsterdam?",
        'SELECT name FROM customers WHERE first_name = "Daan" OR city = "Amsterdm"',
        rules=["literal_alignment"],
    )

    assert _finding(conjunctive, "NEAR_MISS_LITERAL_MISMATCH").details["binding"] == (
        "STRONG_PAIR"
    )
    assert _finding(disjunctive, "NEAR_MISS_LITERAL_MISMATCH").details["binding"] == (
        "WEAK_UNIQUE"
    )
    assert both_unlicensed.contradicted_count == 0
    assert both_unlicensed.unresolved_count == 2


def test_shadowed_aliases_in_nested_scopes_do_not_form_a_strong_pair():
    features = detect_consistency(
        "Show records for Dean Peeters.",
        (
            "SELECT * FROM customers AS t "
            'WHERE t.first_name = "Daan" AND t.status_code = "QZXQ" '
            "AND EXISTS (SELECT 1 FROM employees AS t "
            'WHERE t.last_name = "Peeters")'
        ),
        rules=["literal_alignment"],
    )

    assert not any(
        finding.details.get("binding") == "STRONG_PAIR"
        for finding in features.findings
    )


def test_optimizer_invalid_duplicate_alias_forces_scoped_checks_to_abstain():
    features = detect_consistency(
        "Show active records.",
        (
            "SELECT * FROM users AS T2 JOIN audit AS T2 ON T2.id = T2.id "
            "WHERE T2.is_active = 1"
        ),
        rules=["literal_alignment"],
    )

    assert features.parseable is True
    assert features.contradicted_count == 0


def test_ambiguous_near_miss_candidates_leave_the_literal_unresolved():
    features = detect_consistency(
        "Was it Peters or Peetrs who bought the track?",
        'SELECT id FROM customers WHERE last_name = "Peeters"',
        rules=["literal_alignment"],
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1


def test_demonym_licenses_its_wordnet_pertainym_without_becoming_a_near_miss():
    features = detect_consistency(
        "What is the average age for all French singers?",
        "SELECT avg(age) FROM singer WHERE country = 'France'",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.details["license_kind"] == "PERTAINYM"
    assert finding.question_spans[0].text == "French"


@pytest.mark.parametrize(
    "question,value,expected_span",
    [
        ("Show papers affiliated with Stanford.", "Stanford University", "Stanford"),
        ("Show tracks stored as MPEG.", "MPEG audio file", "MPEG"),
        ("Show flights arriving at Gatwick.", "London Gatwick", "Gatwick"),
        (
            "Show Computer Information Systems classes.",
            "Computer Info Systems",
            "Computer Information Systems",
        ),
        ("Show customers from the US.", "United States", "US"),
    ],
)
def test_conservative_abbreviations_license_string_values(
    question, value, expected_span
):
    features = detect_consistency(
        question,
        f"SELECT id FROM records WHERE category = '{value}'",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.details["license_kind"] == "ABBREVIATION"
    assert finding.question_spans[0].text == expected_span


def test_abbreviation_prefers_the_distinctive_airport_component():
    features = detect_consistency(
        "Show airports associated with both London Heathrow and Gatwick.",
        "SELECT id FROM airports WHERE name = 'London Gatwick'",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
    assert [span.text for span in finding.question_spans] == ["Gatwick"]


@pytest.mark.parametrize(
    "question,value",
    [
        ("Show papers reviewed by Britanny Harris.", "Brittany Harris"),
        ("Show members from Hiram, Goergia.", "Hiram, Georgia"),
        ("What album has the track Ball to the Wall?", "Balls to the Wall"),
    ],
)
def test_partial_component_does_not_hide_a_full_value_near_miss(
    question, value
):
    features = detect_consistency(
        question,
        f"SELECT id FROM records WHERE category = '{value}'",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert not any(
        finding.details.get("license_kind") == "ABBREVIATION"
        for finding in features.findings
    )


@pytest.mark.parametrize(
    "question,value,span",
    [
        ("Show every successful integration.", "Success", "successful"),
        ("Show paintings in a lithographic medium.", "lithograph", "lithographic"),
        ("Show each failed integration.", "fail", "failed"),
        ("Show staff in a research role.", "researcher", "research"),
    ],
)
def test_derivational_forms_license_string_values(question, value, span):
    features = detect_consistency(
        question,
        f"SELECT id FROM records WHERE category = '{value}'",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.details["license_kind"] == "DERIVATION"
    assert finding.question_spans[0].text == span


def test_multiplicative_number_word_licenses_numeric_value():
    features = detect_consistency(
        "Show customers who ordered more than twice.",
        "SELECT customer_id FROM orders GROUP BY customer_id HAVING COUNT(*) > 2",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.details["license_kind"] == "MULTIPLICATIVE_NUMBER"
    assert finding.question_spans[0].text == "twice"


def test_single_licenses_one_only_for_a_count_role():
    count_features = detect_consistency(
        "Show templates used in more than a single document.",
        (
            "SELECT template_id FROM documents GROUP BY template_id "
            "HAVING COUNT(*) > 1"
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )
    unrelated = detect_consistency(
        "Show each single driver name.",
        "SELECT name FROM drivers WHERE wins = 1",
        rules=["literal_alignment"],
    )

    finding = _finding(count_features, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.details["license_kind"] == "COUNT_QUANTIFIER"
    assert finding.question_spans[0].text == "single"
    assert unrelated.unresolved_count == 1


def test_ordinal_number_requires_adjacent_predicate_role():
    licensed = detect_consistency(
        "Show students in fifth grade.",
        "SELECT name FROM students WHERE grade = 5",
        rules=["literal_alignment"],
        emit_supported=True,
    )
    unrelated = detect_consistency(
        "Show the first name of every winning driver.",
        "SELECT first_name FROM drivers WHERE wins = 1",
        rules=["literal_alignment"],
    )

    finding = _finding(licensed, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.details["license_kind"] == "ORDINAL_ROLE"
    assert finding.question_spans[0].text == "fifth"
    assert unrelated.supported_count == 0
    assert unrelated.unresolved_count == 1


def test_pluralized_question_licenses_the_stored_singular():
    features = detect_consistency(
        "Show all volvos in stock.",
        "SELECT * FROM cars WHERE model = 'volvo'",
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
    assert finding.question_spans[0].text == "volvos"


def test_number_words_license_values_above_the_old_parser_ceiling():
    for question, value in (
        ("Show cities with twenty-five thousand residents.", "25000"),
        ("Show cities with one thousand two hundred thirty-four residents.", "1234"),
    ):
        features = detect_consistency(
            question,
            f"SELECT name FROM city WHERE population = {value}",
            rules=["literal_alignment"],
            emit_supported=True,
        )

        finding = _finding(features, "LITERAL_EXPLICITLY_LICENSED")
        assert finding.details["sql_value"] == value
        assert finding.question_spans[0].normalized == value


def test_possessive_name_is_not_a_near_miss_mismatch():
    features = detect_consistency(
        "What is Nancy Edwards's address?",
        (
            "SELECT address FROM employees "
            'WHERE first_name = "Nancy" AND last_name = "Edwards"'
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 2


def test_singular_question_licenses_a_stored_plural_of_a_common_word():
    features = detect_consistency(
        "Return the unit of measure for 'Herb' products.",
        (
            "SELECT unit_of_measure FROM categories "
            'WHERE product_category_code = "Herbs"'
        ),
        rules=["literal_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "LITERAL_EXPLICITLY_LICENSED").details["sql_value"] == (
        "Herbs"
    )


def test_a_name_typo_is_not_licensed_as_an_inflection():
    """The mirror of the plural case, which is how name typos present.

    'Luca' against a stored 'Lucas' looks like a singular against a plural, so
    licensing inflection in both directions would swallow the near-miss rule.
    Only a stored value that is itself a common English word licenses this way.
    """
    features = detect_consistency(
        "What are the papers of Luca Aceto?",
        (
            "SELECT p.title FROM authors AS a JOIN papers AS p "
            "ON a.paper_id = p.paper_id "
            "WHERE a.fname = 'Lucas' AND a.lname = 'Aceto'"
        ),
        rules=["literal_alignment"],
    )

    finding = _finding(features, "NEAR_MISS_LITERAL_MISMATCH")
    assert finding.details["sql_value"] == "Lucas"
    assert finding.details["binding"] == "STRONG_PAIR"


def test_possessive_apostrophes_do_not_create_a_quoted_question_value():
    features = detect_consistency(
        "List pairs of the owner's first name and the dog's name in Sales.",
        "SELECT owner_name, dog_name FROM dogs WHERE department = 'Marketing'",
        rules=["literal_alignment"],
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1


def test_real_quoted_value_still_conflicts_next_to_a_possessive():
    features = detect_consistency(
        "What is the director's name for the movie 'Sky High'?",
        "SELECT director FROM movies WHERE title = 'Skyfall'",
        rules=["literal_alignment"],
    )

    finding = _finding(features, "EXPLICIT_QUOTED_LITERAL_MISMATCH")
    assert finding.status == ConsistencyStatus.CONTRADICTED
    assert finding.details["question_value"] == "Sky High"


def test_sole_quoted_value_is_not_paired_with_another_predicate_role():
    features = detect_consistency(
        "Show orders for customer 'Alice'.",
        "SELECT * FROM orders WHERE customer_id = 42 AND country = 'US'",
        rules=["literal_alignment"],
    )

    assert not any(
        finding.reason_code == "EXPLICIT_QUOTED_LITERAL_MISMATCH"
        for finding in features.findings
    )


def test_courtesy_title_is_not_bound_to_a_first_name_predicate():
    features = detect_consistency(
        "What is Mr Smith's address?",
        (
            "SELECT address FROM staff "
            'WHERE first_name = "John" AND last_name = "Smith"'
        ),
        rules=["literal_alignment"],
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1


def test_literals_without_lexical_content_carry_no_obligation():
    empty_string = detect_consistency(
        "Show rows with no comment.",
        "SELECT * FROM t WHERE comment = ''",
        rules=["literal_alignment"],
    )
    bare_wildcard = detect_consistency(
        "Show every named row.",
        "SELECT * FROM t WHERE name LIKE '%'",
        rules=["literal_alignment"],
    )

    for features in (empty_string, bare_wildcard):
        assert features.applicable_rules == 0
        assert features.findings == []


def test_transformed_numeric_boundary_is_left_for_boundary_rule():
    features = detect_consistency(
        "Show countries that speak at least 3 languages.",
        "SELECT country FROM languages GROUP BY country HAVING COUNT(*) > 2",
        rules=["literal_alignment"],
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert _finding(features, "SQL_LITERAL_UNLICENSED").details["sql_value"] == "2"


def test_spider_train_7707_requires_stored_temporal_anchor():
    features = detect_consistency(
        "papers on Parsing appeared at acl last year",
        (
            "SELECT DISTINCT paperid FROM paper "
            'WHERE keyphrase = "Parsing" '
            "AND year = 2012 "
            'AND venue = "acl"'
        ),
        rules=["temporal_anchor_provenance"],
    )

    assert features.applicable_rules == 1
    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    finding = _finding(features, "TEMPORAL_ANCHOR_MISSING")
    assert finding.target.value == "CONTEXT"
    assert finding.details["sql_temporal_values"] == ["2012"]


def test_relative_year_matches_dataset_reference_datetime():
    features = detect_consistency(
        "Show papers from last year.",
        "SELECT * FROM paper WHERE publication_year = 2012",
        context=ContextManifest(reference_datetime="2013-06-15T12:00:00Z"),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    finding = _finding(features, "TEMPORAL_ANCHOR_DERIVATION_MATCH")
    assert finding.status == ConsistencyStatus.SUPPORTED
    assert finding.details["derived_interval"] == {
        "start_inclusive": "2012-01-01",
        "end_exclusive": "2013-01-01",
    }


def test_relative_year_conflict_needs_valid_anchor():
    features = detect_consistency(
        "Show papers from last year.",
        "SELECT * FROM paper WHERE publication_year = 2011",
        context=ContextManifest(reference_datetime="2013-06-15"),
        rules=["temporal_anchor_provenance"],
    )

    finding = _finding(features, "TEMPORAL_ANCHOR_DERIVATION_CONFLICT")
    assert finding.status == ConsistencyStatus.CONTRADICTED


def test_explicit_year_conflict_is_contradicted():
    features = detect_consistency(
        "Show papers from 2012.",
        "SELECT * FROM paper WHERE publication_year = 2011",
        rules=["temporal_anchor_provenance"],
    )

    finding = _finding(features, "EXPLICIT_TEMPORAL_VALUE_CONFLICT")
    assert finding.status == ConsistencyStatus.CONTRADICTED


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show schools opened after 2000/1/1.",
            "SELECT * FROM school WHERE open_date > '2000-01-01'",
        ),
        (
            "Show events held on 2010-1-1.",
            "SELECT * FROM event WHERE event_date = '2010/01/01'",
        ),
    ],
)
def test_equivalent_padded_and_unpadded_dates_match(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "EXPLICIT_TEMPORAL_VALUE_MATCH").status == (
        ConsistencyStatus.SUPPORTED
    )


def test_distinct_calendar_dates_still_conflict_after_normalization():
    features = detect_consistency(
        "Show schools opened after 2000/1/1.",
        "SELECT * FROM school WHERE open_date > '2000-01-02'",
        rules=["temporal_anchor_provenance"],
    )

    assert _finding(features, "EXPLICIT_TEMPORAL_VALUE_CONFLICT").status == (
        ConsistencyStatus.CONTRADICTED
    )


def test_unanchored_model_number_is_not_a_year_when_a_full_date_is_present():
    features = detect_consistency(
        "What quantity of Printer 1952 was ordered on 2014/9/10?",
        (
            "SELECT quantity FROM orders "
            "WHERE product_name = 'Printer 1952' "
            "AND order_date = '2014-09-10'"
        ),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 1
    assert _finding(
        features, "EXPLICIT_TEMPORAL_VALUE_MATCH"
    ).details["question_temporal_value"] == "2014/9/10"


def test_unanchored_model_number_is_not_inferred_as_a_year_from_sql():
    features = detect_consistency(
        "Show sales of Printer 1952.",
        "SELECT * FROM sales WHERE order_date = '2014-09-10'",
        rules=["temporal_anchor_provenance"],
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_coordinated_year_endpoint_inherits_explicit_temporal_range():
    features = detect_consistency(
        "Compare events between 1996 and 1997.",
        "SELECT * FROM event WHERE event_year IN (1996, 1997)",
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 0
    assert features.supported_count == 2


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "How many concerts occurred in year 2014 or 2015?",
            "SELECT count(*) FROM concert WHERE year = 2014 OR year = 2015",
        ),
        (
            "Find students who took classes in the years of 2009 and 2010.",
            "SELECT * FROM takes WHERE year = 2009 OR year = 2010",
        ),
        (
            "Compare orders shipped in each month of 1995 and 1996.",
            (
                "SELECT SUM(CASE WHEN year = 1995 THEN 1 ELSE 0 END), "
                "SUM(CASE WHEN year = 1996 THEN 1 ELSE 0 END) FROM orders"
            ),
        ),
        (
            "Show singers whose birth year is either 1948 or 1949.",
            "SELECT * FROM singer WHERE birth_year = 1948 OR birth_year = 1949",
        ),
        (
            "Show directors with a movie in either 1999 or 2000.",
            "SELECT * FROM movie WHERE year = 1999 OR year = 2000",
        ),
        (
            "Show vehicles with model years in either 2013 2014.",
            "SELECT * FROM vehicle WHERE model_year = 2013 OR model_year = 2014",
        ),
    ],
)
def test_coordinated_year_sets_do_not_create_competing_values(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 2


def test_coordinated_dates_compare_normalized_value_keys():
    features = detect_consistency(
        "Which day was windier, 2012/1/1 or 2012/1/2?",
        (
            "SELECT CASE WHEN SUM(CASE WHEN date = '2012-01-01' THEN speed END) "
            "> SUM(CASE WHEN date = '2012-01-02' THEN speed END) "
            "THEN 'first' ELSE 'second' END FROM weather"
        ),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 2


def test_enumerated_interior_year_is_part_of_an_explicit_range():
    features = detect_consistency(
        "Show graduates from 2011 to 2013.",
        "SELECT * FROM graduates WHERE year IN (2011, 2012, 2013)",
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 2


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show cards issued after the year 1996.",
            "SELECT * FROM card WHERE issued >= '1997-01-01'",
        ),
        (
            "Show ratings made after the year 2011.",
            "SELECT * FROM rating WHERE created_at >= '2012-01-01'",
        ),
    ],
)
def test_after_complete_year_matches_successor_date_boundary(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "EXPLICIT_TEMPORAL_VALUE_MATCH")


def test_inclusive_year_range_matches_exclusive_successor_boundary():
    features = detect_consistency(
        "Show indicators from 1968 to 1970.",
        "SELECT * FROM indicator WHERE year >= 1968 AND year < 1971",
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0


def test_within_year_range_matches_exclusive_successor_boundary():
    features = detect_consistency(
        "Show papers within the year of 2001 to 2010.",
        "SELECT * FROM paper WHERE year >= 2001 AND year < 2011",
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0


def test_inclusive_successor_operator_does_not_fake_half_open_equivalence():
    features = detect_consistency(
        "Show users from the year of 2005 to 2014.",
        "SELECT * FROM users WHERE start_year >= 2005 AND start_year <= 2015",
        rules=["temporal_anchor_provenance"],
    )

    assert _finding(features, "EXPLICIT_TEMPORAL_VALUE_CONFLICT").status == (
        ConsistencyStatus.CONTRADICTED
    )


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Which day had more orders: 2005-04-08 or two days later?",
            (
                "SELECT order_date FROM orders "
                "WHERE order_date = '2005-04-08' OR order_date = '2005-04-10'"
            ),
        ),
        (
            "What was the decrease after a player was traded in 2005?",
            (
                "SELECT SUM(CASE WHEN year = 2005 THEN games ELSE 0 END) - "
                "SUM(CASE WHEN year = 2006 THEN games ELSE 0 END) FROM player"
            ),
        ),
    ],
)
def test_unsupported_derived_multi_periods_abstain(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(
        features, "TEMPORAL_REALIZATION_UNSUPPORTED"
    ).status == ConsistencyStatus.UNRESOLVED


def test_wrong_threshold_survives_multi_value_false_positive_guards():
    features = detect_consistency(
        "Show races held after 2004.",
        "SELECT * FROM race WHERE year > 2014",
        rules=["temporal_anchor_provenance"],
    )

    assert _finding(features, "EXPLICIT_TEMPORAL_VALUE_CONFLICT").status == (
        ConsistencyStatus.CONTRADICTED
    )


def test_invalid_calendar_date_is_outside_temporal_rule_scope():
    features = detect_consistency(
        "Show events held on 2024/2/30.",
        "SELECT * FROM event WHERE event_date = '2024-03-01'",
        rules=["temporal_anchor_provenance"],
    )

    assert features.applicable_rules == 0
    assert features.findings == []


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show papers after 2012.",
            "SELECT * FROM paper WHERE publication_year < 2012",
        ),
        (
            "Show papers from 2012.",
            "SELECT * FROM paper WHERE publication_year != 2012",
        ),
        (
            "Show papers from 2012.",
            "SELECT * FROM paper WHERE publication_year < 2012",
        ),
    ],
)
def test_temporal_operator_mismatch_is_deferred_to_boundary_rule(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    finding = _finding(features, "TEMPORAL_OPERATOR_ALIGNMENT_DEFERRED")
    assert finding.status == ConsistencyStatus.UNRESOLVED
    assert not any(
        candidate.reason_code == "EXPLICIT_TEMPORAL_VALUE_MATCH"
        for candidate in features.findings
    )


def test_multiple_temporal_values_bind_to_their_question_roles():
    features = detect_consistency(
        "Show orders from 1990 and births from 2020.",
        (
            "SELECT * FROM event "
            "WHERE order_year = 2020 AND birth_year = 1990"
        ),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 2


def test_single_temporal_cue_does_not_bind_to_wrong_role_when_roles_compete():
    features = detect_consistency(
        "Show orders from 1990.",
        (
            "SELECT * FROM event "
            "WHERE birth_year = 1990 AND order_year = 2020"
        ),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "EXPLICIT_TEMPORAL_VALUE_CONFLICT")


def test_matching_and_competing_temporal_values_are_not_supported():
    features = detect_consistency(
        "Show papers from 2012.",
        (
            "SELECT * FROM paper "
            "WHERE publication_year = 2012 AND publication_year = 2011"
        ),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    finding = _finding(features, "EXPLICIT_TEMPORAL_VALUE_CONFLICT")
    assert finding.status == ConsistencyStatus.CONTRADICTED
    assert features.supported_count == 0


def test_adjacent_explicit_year_can_conflict_with_relative_context():
    features = detect_consistency(
        "Show papers from last year (2011).",
        "SELECT * FROM paper WHERE publication_year = 2011",
        context=ContextManifest(reference_datetime="2013-06-15"),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    finding = _finding(features, "QUESTION_TEMPORAL_CONTEXT_CONFLICT")
    assert finding.status == ConsistencyStatus.CONTRADICTED
    assert finding.target.value == "CONTEXT"
    assert features.supported_count == 0


def test_half_open_date_range_matches_current_month():
    features = detect_consistency(
        "Show orders from this month.",
        (
            "SELECT * FROM orders "
            "WHERE order_date >= '2024-02-01' "
            "AND order_date < '2024-03-01'"
        ),
        context=ContextManifest(reference_datetime="2024-02-15"),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert (
        _finding(features, "TEMPORAL_ANCHOR_DERIVATION_MATCH").status
        == ConsistencyStatus.SUPPORTED
    )


def test_quantity_in_the_year_range_is_not_a_temporal_cue():
    """Spider train 51: a population threshold must not be read as a year.

    Nothing in the question or the SQL is temporal, so the rule has to stay
    silent rather than report an unbound date.
    """
    features = detect_consistency(
        "Show the status shared by cities with population bigger than 1500 "
        "and smaller than 500.",
        (
            "SELECT Status FROM city WHERE Population > 1500 "
            "INTERSECT SELECT Status FROM city WHERE Population < 500"
        ),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_year_on_a_column_without_a_temporal_name_is_supported():
    """Spider train 996: the value match licenses the year, not the column name."""
    features = detect_consistency(
        "What are the average enrollment size of the universities that are "
        "founded before 1850?",
        "SELECT avg(enrollment) FROM university WHERE founded < 1850",
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    finding = _finding(features, "EXPLICIT_TEMPORAL_VALUE_MATCH")
    assert finding.status == ConsistencyStatus.SUPPORTED
    assert features.unresolved_count == 0


@pytest.mark.parametrize(
    "sql_time",
    ["2005-08-23 02:06:01", "2005-08-23 03:00:00", "2005-08-23 99:99:99"],
)
def test_explicit_time_of_day_abstains_at_day_granularity(sql_time):
    features = detect_consistency(
        "What are the first names of customers who have not rented any films "
        "after '2005-08-23 02:06:01'?",
        (
            "SELECT first_name FROM customer WHERE customer_id NOT IN ("
            "SELECT customer_id FROM rental "
            f"WHERE rental_date > '{sql_time}')"
        ),
        rules=["temporal_anchor_provenance"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    finding = _finding(features, "TEMPORAL_TIME_GRANULARITY_UNRESOLVED")
    assert finding.status == ConsistencyStatus.UNRESOLVED
    assert finding.details["supported_granularity"] == "day"


def test_quoted_date_is_not_paired_with_an_unrelated_string_predicate():
    """Spider train 4377: the sole-quoted-value pairing needs matching kinds."""
    features = detect_consistency(
        "What are the distinct grant amounts for documents sent before "
        "'1989-04-24 23:51:54' by a leader?",
        (
            "SELECT grant_amount FROM grants AS T1 "
            "JOIN project_staff AS T2 ON T1.grant_id = T2.project_id "
            "WHERE T2.role_code = 'leader' "
            "AND T1.document_sent_date < '1989-04-24 23:51:54'"
        ),
        rules=["literal_alignment"],
    )

    assert features.contradicted_count == 0


def test_invalid_sql_and_missing_question_are_reported_separately():
    invalid = detect_consistency(
        "Show customers.",
        "SELECT FROM",
        rules=["literal_alignment"],
    )
    missing_question = detect_consistency(
        None,
        "SELECT * FROM customers",
        rules=["literal_alignment"],
    )

    assert invalid.parseable is False
    assert invalid.question_present is True
    assert missing_question.parseable is True
    assert missing_question.question_present is False
