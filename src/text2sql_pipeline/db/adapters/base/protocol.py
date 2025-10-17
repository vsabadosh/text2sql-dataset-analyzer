from typing import Protocol, List, Dict, Any

class SAAdapter(Protocol):
    name: str   # "sqlite" | "postgresql"
    kind: str   # "file"   | "server"

    def identity_from_schema(self, schema: str) -> str:
        """
        Parse schema (dialect-strict) → build canonical IR → compute db_id →
        materialize (create-if-missing + apply DDL) → return db_id.
        May raise AdapterError (InvalidSchemaError / ProvisioningError / DDLApplyError).
        """
        ...

    def db_url_for(self, db_id: str) -> str:
        """Return the deterministic connection URL for this adapter/db_id (no I/O)."""
        ...
    
    def get_sqlglot_dialect(self) -> str:
        """Return the dialect name for sqlglot parsing (e.g., 'sqlite', 'postgres')."""
        ...
    
    def get_tables(self, db_id: str) -> List[str]:
        """Get list of all user tables in the database."""
        ...
    
    def get_table_info(self, db_id: str, table: str) -> Dict[str, Any]:
        """
        Get complete information about a table.
        Returns:
            {
                "columns": [{"name": str, "type": str, "nullable": bool, "pk": bool, "unique": bool}, ...],
                "primary_keys": [str, ...],
                "foreign_keys": [{"local": [str], "parent_table": str, "parent_columns": [str]}, ...]
            }
        """
        ...