"""
DEPRECATED: This test is for the old QueryExecutionSqliteAnnot class which has been replaced.
See test_query_execution_safe.py for current tests using QueryExecutionAnnot with DbManager.
"""
from __future__ import annotations

import os
import sqlite3
import pytest

# Skipping this entire test file as it tests deprecated functionality
pytestmark = pytest.mark.skip(reason="Tests deprecated QueryExecutionSqliteAnnot class - see test_query_execution_safe.py instead")
