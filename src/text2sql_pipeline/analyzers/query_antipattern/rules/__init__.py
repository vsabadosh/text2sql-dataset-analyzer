"""Antipattern rules, in detection order.

``RULES`` is the order in which records are extended. A new rule is a
class implementing ``AntipatternRule``, in its own module, added here.
"""

from __future__ import annotations

from typing import Tuple

from .base import AntipatternRule
from .unsafe_update_delete import UnsafeUpdateDeleteRule
from .null_comparison_equals import NullComparisonEqualsRule
from .cartesian_product import CartesianProductRule
from .missing_group_by import MissingGroupByRule
from .chained_comparison_semantics import ChainedComparisonSemanticsRule
from .conditional_count_non_null_else import ConditionalCountNonNullElseRule
from .unquoted_date_arithmetic import UnquotedDateArithmeticRule
from .literal_division_by_zero import LiteralDivisionByZeroRule
from .template_placeholder_literal import TemplatePlaceholderLiteralRule
from .inconsistent_condition import InconsistentConditionRule
from .tautological_condition import TautologicalConditionRule
from .scalar_subquery_cardinality import ScalarSubqueryCardinalityRule
from .function_in_where import FunctionInWhereRule
from .not_in_nullable import NotInNullableRule
from .leading_wildcard_like import LeadingWildcardLikeRule
from .limit_without_order_by import LimitWithoutOrderByRule
from .offset_without_order_by import OffsetWithoutOrderByRule
from .redundant_distinct import RedundantDistinctRule
from .correlated_subquery import CorrelatedSubqueryRule
from .select_star import SelectStarRule
from .select_in_exists import SelectInExistsRule

# Detection order is observable: records are extended in this sequence.
RULES: Tuple[AntipatternRule, ...] = (
    UnsafeUpdateDeleteRule(),
    NullComparisonEqualsRule(),
    CartesianProductRule(),
    MissingGroupByRule(),
    ChainedComparisonSemanticsRule(),
    ConditionalCountNonNullElseRule(),
    UnquotedDateArithmeticRule(),
    LiteralDivisionByZeroRule(),
    TemplatePlaceholderLiteralRule(),
    InconsistentConditionRule(),
    TautologicalConditionRule(),
    ScalarSubqueryCardinalityRule(),
    FunctionInWhereRule(),
    NotInNullableRule(),
    LeadingWildcardLikeRule(),
    LimitWithoutOrderByRule(),
    OffsetWithoutOrderByRule(),
    RedundantDistinctRule(),
    CorrelatedSubqueryRule(),
    SelectStarRule(),
    SelectInExistsRule(),
)

__all__ = ["AntipatternRule", "RULES"]
