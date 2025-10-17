from .sqlite_sa import SQLiteSAAdapter
from .postgres_sa import PostgresSAAdapter
from .base.schema_identity import SchemaIdentity

def make_adapter(*, dialect: str, kind: str, endpoint: str, identity: SchemaIdentity | None = None):
    d = (dialect or "sqlite").lower()
    k = (kind or ("file" if d == "sqlite" else "server")).lower()
    ident = identity or SchemaIdentity()

    if d == "sqlite":
        return SQLiteSAAdapter(file_root=endpoint if k == "file" else None, identity=ident)

    if d in ("postgres", "postgresql"):
        return PostgresSAAdapter(base_url=endpoint if k == "server" else None, identity=ident)

    raise ValueError(f"Unsupported dialect: {dialect}")
