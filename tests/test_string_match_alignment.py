from __future__ import annotations

import pytest

from text2sql_pipeline.analyzers.question_sql_consistency import (
    ConsistencyStatus,
    detect_consistency,
)
from text2sql_pipeline.analyzers.question_sql_consistency.consistency_registry import (
    describe_reason_code,
    select_rules,
)


def _finding(features, reason_code):
    return next(
        finding
        for finding in features.findings
        if finding.reason_code == reason_code
    )


@pytest.mark.parametrize(
    "question,sql,mode",
    [
        (
            "Show names exactly matching Alpha.",
            "SELECT * FROM person WHERE name LIKE 'Alpha'",
            "EXACT",
        ),
        (
            "Show names starting with Alpha.",
            "SELECT * FROM person WHERE name LIKE 'Alpha%'",
            "PREFIX",
        ),
        (
            "Show names ending with Alpha.",
            "SELECT * FROM person WHERE name LIKE '%Alpha'",
            "SUFFIX",
        ),
        (
            "Show names containing Alpha.",
            "SELECT * FROM person WHERE name LIKE '%Alpha%'",
            "CONTAINS",
        ),
    ],
)
def test_static_like_modes_are_supported(question, sql, mode):
    features = detect_consistency(
        question,
        sql,
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "STRING_MATCH_ALIGNMENT_MATCH")
    assert finding.status == ConsistencyStatus.SUPPORTED
    assert finding.details["expected_mode"] == mode
    assert finding.details["actual_mode"] == mode


def test_explicit_include_the_string_is_contains():
    features = detect_consistency(
        "Show game names that include the string Box.",
        "SELECT * FROM game WHERE game_name LIKE '%Box%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert _finding(features, "STRING_MATCH_ALIGNMENT_MATCH")


def test_generic_including_is_not_a_string_match_cue():
    features = detect_consistency(
        "Return project IDs, including all requested item names.",
        "SELECT * FROM project WHERE school_city LIKE 'Brooklyn'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_generic_negative_including_is_not_a_string_match_cue():
    features = detect_consistency(
        "Return project IDs, not including requested item names.",
        "SELECT * FROM project WHERE school_city LIKE 'Brooklyn'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


@pytest.mark.parametrize(
    "question,pattern,expected,actual",
    [
        ("Show names containing Alpha.", "Alpha%", "CONTAINS", "PREFIX"),
        ("Show names starting with Alpha.", "%Alpha", "PREFIX", "SUFFIX"),
        ("Show names ending with Alpha.", "%Alpha%", "SUFFIX", "CONTAINS"),
        ("Show names exactly matching Alpha.", "%Alpha%", "EXACT", "CONTAINS"),
    ],
)
def test_incompatible_like_shapes_are_contradicted(
    question,
    pattern,
    expected,
    actual,
):
    features = detect_consistency(
        question,
        f"SELECT * FROM person WHERE name LIKE '{pattern}'",
        rules=["string_match_alignment"],
    )

    finding = _finding(features, "STRING_MATCH_MODE_CONFLICT")
    assert finding.status == ConsistencyStatus.CONTRADICTED
    assert finding.details["expected_mode"] == expected
    assert finding.details["actual_mode"] == actual


def test_paragraph_text_contains_cue_binds_through_relative_clause():
    features = detect_consistency(
        "Show details for the paragraph that includes the text Korea.",
        "SELECT details FROM paragraph WHERE paragraph_text LIKE 'Korea'",
        rules=["string_match_alignment"],
    )

    assert _finding(features, "STRING_MATCH_MODE_CONFLICT")


def test_dqs_contains_suffix_conflict_still_abstains():
    features = detect_consistency(
        "Show users whose category description contains the string Mother.",
        'SELECT * FROM category WHERE category_description LIKE "%Mother"',
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "STRING_MATCH_DQS_UNRESOLVED")


@pytest.mark.parametrize(
    "question,operator,expected_polarity",
    [
        ("Show names containing Alpha.", "LIKE", "POSITIVE"),
        ("Show names that do not contain Alpha.", "NOT LIKE", "NEGATIVE"),
        ("Show names without the string Alpha.", "NOT LIKE", "NEGATIVE"),
        (
            "Show names that do not exactly match Alpha.",
            "NOT LIKE",
            "NEGATIVE",
        ),
    ],
)
def test_direct_positive_and_negative_polarity_is_supported(
    question,
    operator,
    expected_polarity,
):
    pattern = "Alpha" if "exactly" in question else "%Alpha%"
    features = detect_consistency(
        question,
        f"SELECT * FROM person WHERE name {operator} '{pattern}'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "STRING_MATCH_ALIGNMENT_MATCH")
    assert finding.details["expected_polarity"] == expected_polarity
    assert finding.details["actual_polarity"] == expected_polarity


@pytest.mark.parametrize(
    "question,pattern",
    [
        ("Show names that must not contain Alpha.", "%Alpha%"),
        ("Show names that do not begin with Alpha.", "Alpha%"),
        ("Show names that do not match exactly Alpha.", "Alpha"),
    ],
)
def test_direct_negative_variants_bind_as_negative(question, pattern):
    features = detect_consistency(
        question,
        f"SELECT * FROM person WHERE name NOT LIKE '{pattern}'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "STRING_MATCH_ALIGNMENT_MATCH")
    assert finding.details["expected_polarity"] == "NEGATIVE"


def test_sentential_exclusion_abstains_instead_of_inverting_locally():
    features = detect_consistency(
        "Exclude names starting with Alpha.",
        "SELECT * FROM person WHERE name NOT LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "STRING_MATCH_QUESTION_NEGATION_UNRESOLVED")


def test_outer_exclusion_of_negative_cue_abstains():
    features = detect_consistency(
        "Exclude names that do not contain Alpha.",
        "SELECT * FROM person WHERE name LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "STRING_MATCH_QUESTION_NEGATION_UNRESOLVED")


@pytest.mark.parametrize(
    "question",
    [
        "Show names that never contain Alpha.",
        "Show names that cannot contain Alpha.",
        "Show names that can't contain Alpha.",
        "Show names that shouldn't contain Alpha.",
        "Avoid names containing Alpha.",
    ],
)
def test_unsupported_question_negation_variants_abstain(question):
    features = detect_consistency(
        question,
        "SELECT * FROM person WHERE name NOT LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "STRING_MATCH_QUESTION_NEGATION_UNRESOLVED")


def test_exact_quantifier_is_not_an_exact_string_cue():
    features = detect_consistency(
        "Show exactly one name containing Alpha.",
        "SELECT * FROM person WHERE name LIKE '%Alpha%' LIMIT 1",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 1
    assert not any(
        finding.reason_code == "STRING_MATCH_MODE_CONFLICT"
        for finding in features.findings
    )


@pytest.mark.parametrize(
    "question,operator",
    [
        ("Show names containing Alpha.", "NOT LIKE"),
        ("Show names that do not contain Alpha.", "LIKE"),
    ],
)
def test_string_match_polarity_conflicts_are_contradicted(question, operator):
    features = detect_consistency(
        question,
        f"SELECT * FROM person WHERE name {operator} '%Alpha%'",
        rules=["string_match_alignment"],
    )

    assert _finding(
        features, "STRING_MATCH_POLARITY_CONFLICT"
    ).status == ConsistencyStatus.CONTRADICTED


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM person WHERE name LIKE 'Alpha_%'",
        "SELECT * FROM person WHERE name LIKE 'Al%pha'",
        "SELECT * FROM person WHERE name LIKE '%%Alpha%%'",
        r"SELECT * FROM person WHERE name LIKE '%Alpha\%%' ESCAPE '\'",
    ],
)
def test_patterns_outside_the_percent_edge_allowlist_abstain(sql):
    features = detect_consistency(
        "Show names containing Alpha.",
        sql,
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(
        features, "STRING_MATCH_PATTERN_UNRESOLVED"
    ).status == ConsistencyStatus.UNRESOLVED


def test_function_wrapped_role_abstains():
    features = detect_consistency(
        "Show names containing Alpha.",
        "SELECT * FROM person WHERE LOWER(name) LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert _finding(features, "STRING_MATCH_WRAPPER_UNRESOLVED")


def test_dynamic_pattern_abstains():
    features = detect_consistency(
        "Show names containing Alpha.",
        "SELECT * FROM person WHERE name LIKE '%' || search_term || '%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert _finding(features, "STRING_MATCH_DYNAMIC_PATTERN_UNRESOLVED")


def test_disjunctive_like_abstains():
    features = detect_consistency(
        "Show names containing Alpha.",
        "SELECT * FROM person WHERE active = 1 OR name LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert _finding(features, "STRING_MATCH_BOOLEAN_UNRESOLVED")


@pytest.mark.parametrize(
    "wrapper",
    [
        "(name LIKE '%Alpha%') IS FALSE",
        "(name LIKE '%Alpha%') = 0",
        "(name LIKE '%Alpha%') IS NULL",
        "(name LIKE '%Alpha%') < 1",
        "(name LIKE '%Alpha%') IN (0)",
        "(name LIKE '%Alpha%') BETWEEN 0 AND 0",
        "1 - (name LIKE '%Alpha%')",
    ],
)
def test_boolean_wrappers_around_like_abstain(wrapper):
    features = detect_consistency(
        "Show names containing Alpha.",
        f"SELECT * FROM person WHERE {wrapper}",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert features.contradicted_count == 0
    assert _finding(features, "STRING_MATCH_SQL_NEGATION_UNRESOLVED")


def test_same_payload_on_multiple_roles_abstains():
    features = detect_consistency(
        "Show people with names containing Alpha.",
        (
            "SELECT * FROM person WHERE first_name LIKE '%Alpha%' "
            "AND last_name LIKE '%Alpha%'"
        ),
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert _finding(features, "STRING_MATCH_ROLE_UNRESOLVED")


def test_local_role_words_disambiguate_same_payload():
    features = detect_consistency(
        "Show people with first names containing Alpha.",
        (
            "SELECT * FROM person WHERE first_name LIKE '%Alpha%' "
            "AND last_name LIKE '%Alpha%'"
        ),
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "STRING_MATCH_ALIGNMENT_MATCH")
    assert finding.details["column_name"] == "first_name"


def test_sole_predicate_requires_question_role_binding():
    features = detect_consistency(
        "Show descriptions containing Alpha.",
        "SELECT * FROM person WHERE name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_value_text_cannot_supply_the_predicate_role():
    features = detect_consistency(
        "Show descriptions containing Name.",
        "SELECT * FROM person WHERE name LIKE '%Name%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_value_binding_does_not_cross_sentence_boundaries():
    features = detect_consistency(
        "Show names containing Beta. Use code Alpha.",
        "SELECT * FROM person WHERE name LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_generic_role_head_requires_the_column_qualifier():
    features = detect_consistency(
        "Show product names containing Alpha.",
        "SELECT * FROM customer WHERE customer_name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_generic_role_head_must_match_the_owning_entity():
    features = detect_consistency(
        "Show books by authors whose names contain Alpha.",
        "SELECT * FROM book WHERE name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


@pytest.mark.parametrize(
    "question,sql",
    [
        (
            "Show authors with names containing Alpha.",
            "SELECT * FROM book WHERE name LIKE 'Alpha%'",
        ),
        (
            "Show authors whose first names contain Alpha.",
            "SELECT * FROM book WHERE first_name LIKE 'Alpha%'",
        ),
    ],
)
def test_all_roles_must_match_the_owning_entity(question, sql):
    features = detect_consistency(
        question,
        sql,
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_all_nested_owner_qualifiers_must_agree():
    features = detect_consistency(
        "Show products whose customer names contain Alpha.",
        "SELECT * FROM product WHERE name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_matching_qualifier_does_not_override_conflicting_role_head():
    features = detect_consistency(
        "Show product descriptions containing Alpha.",
        "SELECT * FROM product WHERE product_name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_role_binding_uses_the_noun_phrase_attached_to_the_cue():
    features = detect_consistency(
        "Show product names with descriptions containing Alpha.",
        "SELECT * FROM product WHERE product_name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_later_unrelated_value_cannot_replace_the_cue_argument():
    features = detect_consistency(
        "Show product names containing Beta from brand Alpha.",
        "SELECT * FROM product WHERE product_name LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


@pytest.mark.parametrize(
    "question",
    [
        "Show names starting with Alpha or Beta.",
        "Show names starting with Alpha and Beta.",
        "Show names starting with Alpha and ending with Beta.",
    ],
)
def test_question_boolean_match_specification_abstains(question):
    features = detect_consistency(
        question,
        "SELECT * FROM person WHERE name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_QUESTION_BOOLEAN_UNRESOLVED")


@pytest.mark.parametrize("pattern", ["the%", "letter%"])
def test_match_markers_cannot_become_the_pattern_payload(pattern):
    features = detect_consistency(
        "Show names starting with the letter A.",
        f"SELECT * FROM person WHERE name LIKE '{pattern}'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_containment_marker_cannot_become_the_pattern_payload():
    features = detect_consistency(
        "Show descriptions containing the text Alpha.",
        "SELECT * FROM category WHERE description LIKE '%text%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_role_words_after_the_value_do_not_rebind_the_cue():
    features = detect_consistency(
        "Show product names containing Alpha for customer Beta.",
        "SELECT * FROM customer WHERE customer_name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_role_binding_uses_the_last_coordinated_noun_phrase():
    features = detect_consistency(
        "Show customer names and product descriptions containing Alpha.",
        "SELECT * FROM customer WHERE customer_name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_relational_containment_does_not_bind_to_nested_entity_name():
    features = detect_consistency(
        "Show boxes containing items named Alpha.",
        "SELECT * FROM item AS i WHERE i.item_name LIKE 'Alpha'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_non_string_containment_does_not_bind_to_date_like():
    features = detect_consistency(
        "Which brand contains cane sugar in 2012?",
        "SELECT * FROM review WHERE review_date LIKE '2012%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_unmatched_question_value_is_out_of_scope():
    features = detect_consistency(
        "Show names containing Mary.",
        "SELECT * FROM person WHERE name LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_sqlite_double_quoted_rhs_abstains_without_schema_resolution():
    features = detect_consistency(
        "Show descriptions containing Mother.",
        'SELECT * FROM category WHERE description LIKE "%Mother%"',
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "STRING_MATCH_DQS_UNRESOLVED")


def test_punctuation_distinct_values_do_not_collapse_to_one_token():
    features = detect_consistency(
        "Show languages containing C#.",
        "SELECT * FROM language WHERE name LIKE '%C++%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_word_boundary_claim_abstains_from_substring_pattern():
    features = detect_consistency(
        "Show descriptions containing the word he.",
        "SELECT * FROM category WHERE description LIKE '%he%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_WORD_BOUNDARY_UNRESOLVED")


def test_post_value_whole_word_claim_abstains():
    features = detect_consistency(
        "Show descriptions containing Alpha as a whole word.",
        "SELECT * FROM category WHERE description LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_WORD_BOUNDARY_UNRESOLVED")


def test_post_value_standalone_word_claim_abstains():
    features = detect_consistency(
        "Show descriptions containing Alpha as a standalone word.",
        "SELECT * FROM category WHERE description LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_WORD_BOUNDARY_UNRESOLVED")


@pytest.mark.parametrize("article,modifier", [("an", "entire"), ("a", "full")])
def test_additional_whole_word_phrasings_abstain(article, modifier):
    features = detect_consistency(
        f"Show descriptions containing Alpha as {article} {modifier} word.",
        "SELECT * FROM category WHERE description LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_WORD_BOUNDARY_UNRESOLVED")


@pytest.mark.parametrize("suffix", ["as a word", "as a single word"])
def test_any_post_value_word_claim_abstains(suffix):
    features = detect_consistency(
        f"Show descriptions containing Alpha {suffix}.",
        "SELECT * FROM category WHERE description LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_WORD_BOUNDARY_UNRESOLVED")


def test_string_match_cue_cannot_cross_sentence_punctuation():
    features = detect_consistency(
        "Show names that start. With Alpha.",
        "SELECT * FROM person WHERE name LIKE 'Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


@pytest.mark.parametrize(
    "question",
    [
        "Don't show person names that do not contain Alpha.",
        "Return no person names containing Alpha.",
    ],
)
def test_additional_outer_negation_abstains(question):
    features = detect_consistency(
        question,
        "SELECT * FROM person WHERE name LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.contradicted_count == 0
    assert _finding(features, "STRING_MATCH_QUESTION_NEGATION_UNRESOLVED")


@pytest.mark.parametrize(
    "dialect,sql",
    [
        ("mysql", 'SELECT * FROM person WHERE name LIKE "Alpha%"'),
        ("tsql", "SELECT * FROM person WHERE name LIKE '%Al[ph]a%'"),
    ],
)
def test_unvalidated_dialect_pattern_semantics_abstain(dialect, sql):
    features = detect_consistency(
        "Show names starting with Alpha.",
        sql,
        dialect=dialect,
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_DIALECT_UNRESOLVED")


@pytest.mark.parametrize(
    "question,pattern",
    [
        ("Show names exactly matching Alpha.", " Alpha "),
        ("Show names exactly matching Alpha Beta.", "Alpha  Beta"),
    ],
)
def test_semantically_significant_pattern_whitespace_abstains(question, pattern):
    features = detect_consistency(
        question,
        f"SELECT * FROM person WHERE name LIKE '{pattern}'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_PATTERN_UNRESOLVED")


@pytest.mark.parametrize("separator", ["\t", "\u00a0"])
def test_non_space_pattern_whitespace_abstains(separator):
    features = detect_consistency(
        "Show names exactly matching Alpha Beta.",
        f"SELECT * FROM person WHERE name LIKE 'Alpha{separator}Beta'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 0
    assert _finding(features, "STRING_MATCH_PATTERN_UNRESOLVED")


def test_postgres_ilike_uses_the_same_shape_semantics():
    features = detect_consistency(
        "Show names starting with Alpha.",
        "SELECT * FROM person WHERE name ILIKE 'Alpha%'",
        dialect="postgres",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    finding = _finding(features, "STRING_MATCH_ALIGNMENT_MATCH")
    assert finding.details["sql_operator"] == "ILIKE"


def test_like_without_an_explicit_shape_cue_is_out_of_scope():
    features = detect_consistency(
        "Show people named Alpha.",
        "SELECT * FROM person WHERE name LIKE '%Alpha%'",
        rules=["string_match_alignment"],
        emit_supported=True,
    )

    assert features.applicable_rules == 0
    assert features.findings == []


def test_string_match_rule_is_registered_and_documented():
    assert [rule.value for rule in select_rules(["string_match_alignment"])] == [
        "string_match_alignment"
    ]
    for reason_code in (
        "STRING_MATCH_ALIGNMENT_MATCH",
        "STRING_MATCH_MODE_CONFLICT",
        "STRING_MATCH_POLARITY_CONFLICT",
        "STRING_MATCH_PATTERN_UNRESOLVED",
        "STRING_MATCH_WRAPPER_UNRESOLVED",
        "STRING_MATCH_DYNAMIC_PATTERN_UNRESOLVED",
        "STRING_MATCH_BOOLEAN_UNRESOLVED",
        "STRING_MATCH_DQS_UNRESOLVED",
        "STRING_MATCH_DIALECT_UNRESOLVED",
        "STRING_MATCH_QUESTION_NEGATION_UNRESOLVED",
        "STRING_MATCH_QUESTION_BOOLEAN_UNRESOLVED",
        "STRING_MATCH_ROLE_UNRESOLVED",
        "STRING_MATCH_SCOPE_UNRESOLVED",
        "STRING_MATCH_SQL_NEGATION_UNRESOLVED",
        "STRING_MATCH_WORD_BOUNDARY_UNRESOLVED",
    ):
        assert describe_reason_code(reason_code)
