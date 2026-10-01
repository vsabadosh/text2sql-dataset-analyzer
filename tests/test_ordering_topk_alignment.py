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


def _single_finding_with_context(
    question: str,
    sql: str,
    evidence_texts: list[str],
):
    features = detect_consistency(
        question,
        sql,
        context=ContextManifest(evidence_texts=evidence_texts),
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


def test_relative_clause_makes_imperative_extremum_entity_returning():
    features, finding = _single_finding(
        "Give the account name of the customer with the lowest balance.",
        "SELECT account_name FROM customer ORDER BY balance ASC LIMIT 1",
    )

    assert features.supported_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"
    assert finding.details["column_name"] == "balance"


def test_camel_case_order_target_preserves_question_word_boundaries():
    features, finding = _single_finding(
        "Show the top 4 teams with the highest build up play speed.",
        "SELECT team_name FROM team ORDER BY buildUpPlaySpeed ASC LIMIT 4",
    )

    assert features.contradicted_count == 1
    assert finding.reason_code == "ORDERING_TOPK_DIRECTION_CONFLICT"
    assert finding.details["column_name"] == "buildupplayspeed"


def test_amount_is_a_meaningful_ordering_role():
    features, finding = _single_finding(
        "Which payment has the highest amount?",
        "SELECT payment_id FROM payment ORDER BY amount DESC LIMIT 1",
    )

    assert features.supported_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"


def test_leading_result_count_applies_to_relative_superlative():
    features, finding = _single_finding(
        "List out 3 customers who have the highest payment amount.",
        "SELECT customer_id FROM payment ORDER BY amount DESC LIMIT 3",
    )

    assert features.supported_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"
    assert finding.details["requested_n"] == 3
    assert finding.details["implicit_one"] is False


def test_count_before_extremum_sets_requested_result_size():
    features, finding = _single_finding(
        "Show the 3 accounts with the lowest balance.",
        "SELECT name FROM account ORDER BY balance ASC LIMIT 3",
    )

    assert features.supported_count == 1
    assert finding.details["requested_n"] == 3
    assert finding.details["implicit_one"] is False


def test_count_before_relative_clause_sets_requested_result_size():
    features, finding = _single_finding(
        "Provide 5 donors who gave the highest amount.",
        "SELECT donor_id FROM donor ORDER BY amount DESC LIMIT 5",
    )

    assert features.supported_count == 1
    assert finding.details["requested_n"] == 5


def test_filter_numbers_do_not_become_requested_result_size():
    cases = [
        (
            "List the customers in district 5 who have the highest balance.",
            "SELECT name FROM customer WHERE district = 5 "
            "ORDER BY balance DESC LIMIT 1",
        ),
        (
            "Among the students aged 20 or older, which one has the highest GPA?",
            "SELECT name FROM student WHERE age >= 20 ORDER BY gpa DESC LIMIT 1",
        ),
        (
            "Among the 5 products, which has the highest price?",
            "SELECT name FROM product ORDER BY price DESC LIMIT 1",
        ),
        (
            "List customers who placed at least 5 orders with the highest total.",
            "SELECT customer FROM orders GROUP BY customer HAVING COUNT(*) >= 5 "
            "ORDER BY SUM(total) DESC LIMIT 1",
        ),
        (
            "State the title of episode 12 which has the highest rating.",
            "SELECT title FROM episode WHERE episode_no = 12 "
            "ORDER BY rating DESC LIMIT 1",
        ),
        (
            "Consider the 3 regions. Which region has the highest sales?",
            "SELECT region FROM sales GROUP BY region "
            "ORDER BY SUM(amount) DESC LIMIT 1",
        ),
        (
            "Which of the two employees has the highest salary?",
            "SELECT name FROM employee ORDER BY salary DESC LIMIT 1",
        ),
        (
            "Show the store in the 3 cities that has the highest revenue.",
            "SELECT store FROM sales ORDER BY revenue DESC LIMIT 1",
        ),
        (
            "Name the player on the 2 teams who has the highest score.",
            "SELECT player FROM result ORDER BY score DESC LIMIT 1",
        ),
        (
            "List the name of the team with the 2 players who have the highest score.",
            "SELECT team FROM result ORDER BY score DESC LIMIT 1",
        ),
        (
            "List the 5 star businesses with the highest review count.",
            "SELECT business FROM review ORDER BY review_count DESC LIMIT 1",
        ),
        (
            "Show the 3 bedroom apartments with the lowest price.",
            "SELECT apartment FROM listing ORDER BY price ASC LIMIT 1",
        ),
        (
            "Name two of the 3 products with the highest price.",
            "SELECT name FROM product ORDER BY price DESC LIMIT 2",
        ),
        (
            "List 2 of the 5 products that have the lowest price.",
            "SELECT name FROM product ORDER BY price ASC LIMIT 2",
        ),
        (
            "Which 2 door cars have the highest horsepower?",
            "SELECT name FROM car ORDER BY horsepower DESC LIMIT 1",
        ),
        (
            "List the 3 letter codes with the highest usage.",
            "SELECT code FROM codes ORDER BY usage DESC LIMIT 1",
        ),
        (
            "Show some of the 5 products with the highest price.",
            "SELECT name FROM product ORDER BY price DESC LIMIT 2",
        ),
        (
            "Name two of the 3 highest priced products by price.",
            "SELECT name FROM product ORDER BY price DESC LIMIT 2",
        ),
    ]
    for question, sql in cases:
        features, _ = _single_finding(question, sql)
        assert features.contradicted_count == 0


def test_which_count_before_entity_is_requested_result_size():
    features, finding = _single_finding(
        "Which 5 customers have the highest balance?",
        "SELECT name FROM customer ORDER BY balance DESC LIMIT 5",
    )

    assert features.supported_count == 1
    assert finding.details["requested_n"] == 5


def test_highest_ordinal_rank_without_domain_convention_abstains():
    features, finding = _single_finding(
        "Which book has the highest rank?",
        "SELECT title FROM review ORDER BY rank ASC LIMIT 1",
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_camel_case_ordinal_rank_also_abstains():
    features, finding = _single_finding(
        "Which university has the highest world rank?",
        "SELECT name FROM university ORDER BY WorldRank ASC LIMIT 1",
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_full_sorted_list_is_not_assessed_by_topk_rule():
    for question in (
        "List all products sorted with the highest price first.",
        "List the employees with the highest salary first.",
        "List employees starting with the highest salary.",
        "List employees from highest to lowest salary.",
        (
            "Which product has the highest price? "
            "List these products in descending order of price."
        ),
    ):
        features = detect_consistency(
            question,
            "SELECT name FROM product ORDER BY price DESC",
            rules=["ordering_topk_alignment"],
            emit_supported=True,
        )

        assert features.not_assessed_count == 1
        assert (
            features.findings[0].reason_code == "ORDERING_TOPK_REALIZATION_UNSUPPORTED"
        )


def test_order_and_all_as_unrelated_words_do_not_suppress_rule():
    for question, sql in (
        (
            "Which customer placed the order with the highest price among all customers?",
            "SELECT customer FROM orders ORDER BY price DESC LIMIT 1",
        ),
        (
            "Show the sort code of the bank with the highest balance.",
            "SELECT sort_code FROM bank ORDER BY balance DESC LIMIT 1",
        ),
    ):
        features, finding = _single_finding(question, sql)
        assert features.supported_count == 1
        assert finding.reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"


def test_earlier_filter_relative_clause_does_not_turn_scalar_into_entity():
    features, finding = _single_finding(
        "For employees who work in Sales, what is the highest salary?",
        "SELECT MAX(salary) FROM employee WHERE department = 'Sales'",
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_complementizer_that_does_not_create_entity_request():
    features, finding = _single_finding(
        "Is it true that the highest salary is paid in Sales?",
        "SELECT MAX(salary) FROM employee WHERE department = 'Sales'",
    )

    assert features.contradicted_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_per_group_extremum_is_not_assessed_as_global_top_one():
    for question in (
        "Show the employee with the highest salary in each department.",
        "For each department, show the employee with the highest salary.",
        "Show the employee with the highest salary per department.",
        "Show the employee with the highest salary by department.",
        "Show the employee with the highest salary within their department.",
        "Show the employee with the highest salary across departments.",
        "For all departments, show the employee with the highest salary.",
    ):
        features, finding = _single_finding(
            question,
            (
                "SELECT department, name, MAX(salary) FROM employee "
                "GROUP BY department ORDER BY salary DESC"
            ),
        )

        assert features.contradicted_count == 0
        assert features.supported_count == 0
        assert features.not_assessed_count == 1
        assert finding.reason_code == "ORDERING_TOPK_REALIZATION_UNSUPPORTED"


def test_plural_entity_without_count_does_not_imply_top_one():
    for question, limit in (
        ("List the products that have the highest ratings.", 5),
        ("Name the players with the highest scores.", 3),
    ):
        features, finding = _single_finding(
            question,
            f"SELECT name FROM result ORDER BY score DESC LIMIT {limit}",
        )

        assert features.contradicted_count == 0
        assert features.unresolved_count == 1
        assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_topk_subset_inside_ungrouped_aggregate_is_not_assessed():
    features, finding = _single_finding(
        "Among the top 5 heaviest shipments, how many were transported via Mack?",
        (
            "SELECT COUNT(*) FROM shipment WHERE make = 'Mack' "
            "ORDER BY weight DESC LIMIT 5"
        ),
    )

    assert features.contradicted_count == 0
    assert features.supported_count == 0
    assert features.not_assessed_count == 1
    assert finding.reason_code == "ORDERING_TOPK_REALIZATION_UNSUPPORTED"


def test_context_can_license_direct_camel_case_order_target():
    features = detect_consistency(
        "List the top five products in descending order of inventory.",
        "SELECT ProductID FROM Products ORDER BY UnitsInStock DESC LIMIT 5",
        context=ContextManifest(
            evidence_texts=["inventory refers to MAX(UnitsInStock)"]
        ),
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 1
    assert features.findings[0].reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"
    assert "DATASET_EVIDENCE" in {
        source.value for source in features.findings[0].evidence_sources
    }
    assert (
        features.findings[0].details["binding_kind"]
        == "DATASET_EVIDENCE_TO_ROOT_ORDER_BY"
    )


def test_context_can_license_count_order_expression():
    features = detect_consistency(
        "Identify the attribute with the highest number of objects.",
        (
            "SELECT attribute_id FROM image_object "
            "GROUP BY attribute_id ORDER BY COUNT(attribute_id) DESC LIMIT 1"
        ),
        context=ContextManifest(
            evidence_texts=[
                "highest number of objects refers to MAX(COUNT(attribute_id))"
            ]
        ),
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 1
    assert features.findings[0].reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"


def test_context_can_license_division_order_expression():
    features = detect_consistency(
        "Which film has the highest rental price per day?",
        (
            "SELECT title FROM film "
            "ORDER BY rental_rate / rental_duration DESC LIMIT 1"
        ),
        context=ContextManifest(
            evidence_texts=[
                "highest rental price per day refers to "
                "MAX(DIVIDE(rental_rate, rental_duration))"
            ]
        ),
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    assert features.supported_count == 1
    assert features.findings[0].reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"


def test_unrelated_evidence_cannot_license_order_target():
    features, finding = _single_finding_with_context(
        "Which player has the lowest weight?",
        "SELECT name FROM player ORDER BY birthday ASC LIMIT 1",
        ["oldest player refers to MIN(birthday)"],
    )

    assert features.supported_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_later_comma_separated_evidence_mapping_cannot_leak():
    features, finding = _single_finding_with_context(
        "Which player has the lowest weight?",
        "SELECT name FROM player ORDER BY birthday ASC LIMIT 1",
        ["lowest weight refers to MIN(weight_kg), " "oldest refers to MIN(birthday)"],
    )

    assert features.supported_count == 0
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_trailing_clause_evidence_cannot_license_cue():
    cases = [
        (
            "Which player has the highest weight among the tallest players?",
            ["tallest refers to MAX(height)"],
        ),
        (
            "Which player has the highest weight, and what is the player's height?",
            ["height refers to MAX(height)"],
        ),
    ]
    for question, evidence in cases:
        features, finding = _single_finding_with_context(
            question,
            "SELECT name FROM player ORDER BY height DESC LIMIT 1",
            evidence,
        )
        assert features.supported_count == 0
        assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_opposite_evidence_polarity_cannot_license_cue():
    features, finding = _single_finding_with_context(
        "Which year has the highest speed?",
        "SELECT year FROM lap ORDER BY lap_ms DESC LIMIT 1",
        ["lowest speed refers to MAX(lap_ms)"],
    )

    assert features.supported_count == 0
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_measure_word_overlap_does_not_link_different_evidence_role():
    features, finding = _single_finding_with_context(
        "Which category has the highest number of images?",
        (
            "SELECT category FROM image GROUP BY category "
            "ORDER BY COUNT(category) DESC LIMIT 1"
        ),
        ["highest number of objects refers to MAX(COUNT(category))"],
    )

    assert features.supported_count == 0
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_context_expression_mismatch_abstains():
    features, finding = _single_finding_with_context(
        "Which film has the highest rental price per day?",
        "SELECT title FROM film ORDER BY rental_rate DESC LIMIT 1",
        [
            "highest rental price per day refers to "
            "MAX(DIVIDE(rental_rate, rental_duration))"
        ],
    )

    assert features.supported_count == 0
    assert features.unresolved_count == 1
    assert finding.reason_code == "ORDERING_TOPK_CONTEXT_CONVENTION_UNRESOLVED"


def test_unsupported_context_function_cannot_license_division():
    features, finding = _single_finding_with_context(
        "Which film has the highest rental price per day?",
        "SELECT title FROM film ORDER BY rental_rate / rental_duration DESC LIMIT 1",
        [
            "highest rental price per day refers to "
            "MAX(SUBTRACT(rental_rate, rental_duration))"
        ],
    )

    assert features.supported_count == 0
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_number_of_table_rows_can_bind_count_star_ordering():
    features, finding = _single_finding(
        "Show the top 3 investors by number of transactions.",
        (
            "SELECT investor_id FROM transactions GROUP BY investor_id "
            "ORDER BY COUNT(*) DESC LIMIT 3"
        ),
    )

    assert features.supported_count == 1
    assert finding.reason_code == "ORDERING_TOPK_ALIGNMENT_MATCH"
    assert finding.details["column_name"] == "count(transactions)"
    assert finding.details["binding_kind"] == "QUESTION_COUNT_ROLE_TO_ROOT_ORDER_BY"


def test_agreeing_context_is_recorded_on_direction_conflict():
    features = detect_consistency(
        "Show the top 3 products with the highest price.",
        "SELECT name FROM product ORDER BY price ASC LIMIT 3",
        context=ContextManifest(evidence_texts=["highest price refers to MAX(price)"]),
        rules=["ordering_topk_alignment"],
        emit_supported=True,
    )

    finding = features.findings[0]
    assert features.contradicted_count == 1
    assert finding.reason_code == "ORDERING_TOPK_DIRECTION_CONFLICT"
    assert "DATASET_EVIDENCE" in {source.value for source in finding.evidence_sources}
    assert finding.details["evidence_text"] == "highest price refers to MAX(price)"


def test_count_star_does_not_bind_nested_or_joined_table_name():
    cases = [
        (
            "Show the top 3 investors by number of transactions.",
            (
                "SELECT investor_id FROM investors "
                "WHERE investor_id IN (SELECT investor_id FROM transactions) "
                "GROUP BY investor_id ORDER BY COUNT(*) DESC LIMIT 3"
            ),
        ),
        (
            "Show the top 3 orders by number of order items.",
            (
                "SELECT orders.id FROM orders JOIN order_items "
                "ON orders.id = order_items.order_id GROUP BY orders.id "
                "ORDER BY COUNT(*) DESC LIMIT 3"
            ),
        ),
        (
            "Show the top 3 investors by number of transactions.",
            (
                "SELECT t.investor_id FROM transactions AS t "
                "JOIN (SELECT investor_id FROM audit) AS a "
                "ON t.investor_id = a.investor_id GROUP BY t.investor_id "
                "ORDER BY COUNT(*) DESC LIMIT 3"
            ),
        ),
    ]
    for question, sql in cases:
        features, finding = _single_finding(question, sql)
        assert features.supported_count == 0
        assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


def test_count_star_does_not_bind_compound_noun_extension():
    features, finding = _single_finding(
        "Which investor has the highest number of transaction types?",
        (
            "SELECT investor_id FROM transactions GROUP BY investor_id "
            "ORDER BY COUNT(*) DESC LIMIT 1"
        ),
    )

    assert features.supported_count == 0
    assert finding.reason_code == "ORDERING_TOPK_ROLE_UNRESOLVED"


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
