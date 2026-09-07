from scripts.summarize_consistency_rule_runs import _is_role_bound


def test_role_bound_requires_target_column_and_supported_binding_kind():
    assert _is_role_bound(
        {
            "column_name": "salary",
            "binding_kind": "QUESTION_ROLE_TO_ROOT_PROJECTION",
        }
    )
    assert _is_role_bound(
        {
            "column_name": "score",
            "binding_kind": "QUESTION_ROLE_TO_ROOT_ORDER_BY",
        }
    )


def test_implementation_exclusions_are_not_counted_as_role_bound():
    for binding_kind in (
        "COMPUTED_AGGREGATE_EQUIVALENCE",
        "COUNT_TARGET_EXCLUDED",
        "MULTI_STAGE_TOPK_EXCLUDED",
        "PRECOMPUTED_COLUMN",
        "RATIO_TARGET_EXCLUDED",
    ):
        assert not _is_role_bound(
            {
                "column_name": "value",
                "binding_kind": binding_kind,
            }
        )


def test_binding_kind_without_target_column_is_not_role_bound():
    assert not _is_role_bound({"binding_kind": "QUESTION_ROLE_TO_ROOT_ORDER_BY"})
