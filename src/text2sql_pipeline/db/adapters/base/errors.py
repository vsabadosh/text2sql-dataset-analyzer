class AdapterError(Exception):
    def __init__(self, bad_db_id: str, message: str):
        super().__init__(message)
        self.bad_db_id = bad_db_id

class InvalidSchemaError(AdapterError):
    """Schema cannot be parsed/understood for this dialect."""

class ProvisioningError(AdapterError):
    """Could not create/prepare the target database/container."""

class DDLApplyError(AdapterError):
    """Failed while executing DDL against the target database."""