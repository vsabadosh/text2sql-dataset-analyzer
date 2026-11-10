"""Normalized schema metadata shared by the antipattern rules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Dict, List, Optional, Set, Tuple

from sqlglot import exp


@dataclass(frozen=True)
class SchemaContext:
    """Schema catalogs the rules read, already normalized.

    ``None`` means the caller did not supply that catalog. An empty mapping
    or set means it was supplied and contains nothing. Several rules
    distinguish the two, so normalization must not collapse one into the other.
    """

    primary_keys: Optional[Dict[str, List[str]]]
    unique_keys: Optional[Dict[str, List[List[str]]]]
    nullable_keys: Optional[Dict[str, List[List[str]]]]
    mismatched_collation_keys: Optional[Dict[str, List[List[str]]]]
    unmodeled_key_tables: Optional[Set[str]]
    table_columns: Optional[Dict[str, List[str]]]
    star_expanded_columns: Optional[Dict[str, List[str]]]
    column_nullability: Optional[Dict[str, Dict[str, bool]]]
    column_comparators: Optional[Dict[str, Dict[str, Tuple[str, str]]]]
    column_types: Optional[Dict[str, Dict[str, str]]]
    foreign_keys: Optional[Dict[str, List[List[str]]]]
    check_columns: Optional[Dict[str, List[str]]]
    triggered_tables: Optional[Set[str]]
    unknown_constraint_tables: Optional[Set[str]]
    date_value_probe: Optional[Callable[[str, str, str], Optional[bool]]]
    dialect: str
    quoted_identifier_proofs_safe: bool

    @classmethod
    def build(
        cls,
        ast: exp.Expression,
        *,
        dialect: Optional[str] = "sqlite",
        primary_keys: Optional[Dict[str, List[str]]] = None,
        table_columns: Optional[Dict[str, List[str]]] = None,
        column_comparators: Optional[
            Dict[str, Dict[str, Tuple[str, str]]]
        ] = None,
        column_nullability: Optional[Dict[str, Dict[str, bool]]] = None,
        star_expanded_columns: Optional[Dict[str, List[str]]] = None,
        column_types: Optional[Dict[str, Dict[str, str]]] = None,
        date_value_probe: Optional[
            Callable[[str, str, str], Optional[bool]]
        ] = None,
        unique_keys: Optional[Dict[str, List[List[str]]]] = None,
        unmodeled_key_tables: Optional[Set[str]] = None,
        foreign_keys: Optional[Dict[str, List[List[str]]]] = None,
        check_columns: Optional[Dict[str, List[str]]] = None,
        triggered_tables: Optional[Set[str]] = None,
        unknown_constraint_tables: Optional[Set[str]] = None,
        nullable_keys: Optional[Dict[str, List[List[str]]]] = None,
        mismatched_collation_keys: Optional[Dict[str, List[List[str]]]] = None,
    ) -> SchemaContext:
        """Normalize the schema keyword arguments of ``detect_antipatterns``.

        A missing dialect still parses as SQLite, but the quoted-identifier
        proof flag treats only an explicit PostgreSQL dialect as unsafe:
        ``(dialect or "")`` rather than ``(dialect or "sqlite")``.
        """
        normalized_primary_keys = None
        if primary_keys is not None:
            normalized_primary_keys = {
                str(table).lower(): [str(column).lower() for column in columns]
                for table, columns in primary_keys.items()
            }
        normalized_unique_keys = None
        if unique_keys is not None:
            normalized_unique_keys = {
                str(table).lower(): [
                    [str(column).lower() for column in key] for key in keys
                ]
                for table, keys in unique_keys.items()
            }
        normalized_unmodeled = (
            {str(table).lower() for table in unmodeled_key_tables}
            if unmodeled_key_tables is not None
            else None
        )
        normalized_nullable_keys = None
        if nullable_keys is not None:
            normalized_nullable_keys = {
                str(table).lower(): [
                    [str(column).lower() for column in key] for key in keys
                ]
                for table, keys in nullable_keys.items()
            }
        normalized_mismatched_keys = None
        if mismatched_collation_keys is not None:
            normalized_mismatched_keys = {
                str(table).lower(): [
                    [str(column).lower() for column in key] for key in keys
                ]
                for table, keys in mismatched_collation_keys.items()
            }
        normalized_foreign_keys = None
        if foreign_keys is not None:
            normalized_foreign_keys = {
                str(table).lower(): [
                    [str(column).lower() for column in columns]
                    for columns in column_sets
                ]
                for table, column_sets in foreign_keys.items()
            }
        normalized_check_columns = None
        if check_columns is not None:
            normalized_check_columns = {
                str(table).lower(): [str(column).lower() for column in columns]
                for table, columns in check_columns.items()
            }
        normalized_triggered = (
            {str(table).lower() for table in triggered_tables}
            if triggered_tables is not None
            else None
        )
        normalized_unknown_constraints = (
            {str(table).lower() for table in unknown_constraint_tables}
            if unknown_constraint_tables is not None
            else None
        )
        normalized_table_columns = None
        if table_columns is not None:
            normalized_table_columns = {
                str(table).lower(): [str(column).lower() for column in columns]
                for table, columns in table_columns.items()
            }
        normalized_star_columns = None
        if star_expanded_columns is not None:
            normalized_star_columns = {
                str(table).lower(): [str(column).lower() for column in columns]
                for table, columns in star_expanded_columns.items()
            }
        normalized_nullability = None
        if column_nullability is not None:
            normalized_nullability = {
                str(table).lower(): {
                    str(column).lower(): bool(nullable)
                    for column, nullable in columns.items()
                }
                for table, columns in column_nullability.items()
            }
        normalized_comparators = None
        if column_comparators is not None:
            normalized_comparators = {
                str(table).lower(): {
                    str(column).lower(): (
                        str(signature[0]).upper(),
                        str(signature[1]).upper(),
                    )
                    for column, signature in columns.items()
                }
                for table, columns in column_comparators.items()
            }
        normalized_column_types = None
        if column_types is not None:
            normalized_column_types = {
                str(table).lower(): {
                    str(column).lower(): str(sql_type).upper()
                    for column, sql_type in columns.items()
                }
                for table, columns in column_types.items()
            }

        # PostgreSQL quoted identifiers are case-sensitive, while several schema
        # catalogs are normalized case-insensitively. Disable guarantees that
        # depend on those lossy catalogs; projection/grouping binders separately
        # reject quoted column references before making an FD proof.
        if (dialect or "").lower() in {"postgres", "postgresql"}:
            query_has_quoted_name = any(
                isinstance(identifier, exp.Identifier)
                and bool(identifier.args.get("quoted"))
                for identifier in ast.find_all(exp.Identifier)
            )
            catalog_names = [
                name
                for metadata in (primary_keys, column_nullability)
                if metadata
                for table, columns in metadata.items()
                for name in (table, *columns)
            ]
            catalog_has_case_sensitive_name = any(
                str(name) != str(name).lower() for name in catalog_names
            )
            if query_has_quoted_name or catalog_has_case_sensitive_name:
                normalized_primary_keys = None
                normalized_unique_keys = None
                normalized_nullable_keys = None
                normalized_mismatched_keys = None
                normalized_nullability = None
                normalized_comparators = None
                normalized_column_types = None

        return cls(
            primary_keys=normalized_primary_keys,
            unique_keys=normalized_unique_keys,
            nullable_keys=normalized_nullable_keys,
            mismatched_collation_keys=normalized_mismatched_keys,
            unmodeled_key_tables=normalized_unmodeled,
            table_columns=normalized_table_columns,
            star_expanded_columns=normalized_star_columns,
            column_nullability=normalized_nullability,
            column_comparators=normalized_comparators,
            column_types=normalized_column_types,
            foreign_keys=normalized_foreign_keys,
            check_columns=normalized_check_columns,
            triggered_tables=normalized_triggered,
            unknown_constraint_tables=normalized_unknown_constraints,
            date_value_probe=date_value_probe,
            dialect=(dialect or "sqlite").lower(),
            quoted_identifier_proofs_safe=(
                (dialect or "").lower() not in {"postgres", "postgresql"}
            ),
        )
