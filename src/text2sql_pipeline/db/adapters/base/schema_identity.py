import hashlib, json, re
from typing import Dict, Any

class SchemaIdentity:
    def good_db_id(self, dialect: str, canonical_ir: Dict[str, Any]) -> str:
        payload = json.dumps(
            {"dialect": dialect, "schema": canonical_ir},
            sort_keys=True, separators=(",", ":")
        ).encode()
        return "t2sql_" + hashlib.sha256(payload).hexdigest()[:16]

    def bad_db_id(self, dialect: str, schema_text: str) -> str:
        norm = re.sub(r"--.*?$", "", schema_text, flags=re.MULTILINE)
        norm = re.sub(r"/\*.*?\*/", "", norm, flags=re.DOTALL)
        norm = re.sub(r"\s+", " ", norm).strip().lower()
        pref = (dialect or "sql")[:3]
        return f"{pref}_err_" + hashlib.sha1(norm.encode()).hexdigest()[:16]