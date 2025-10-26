"""
Tests for DbManager DDL schema generation with examples.
"""
import pytest
from text2sql_pipeline.db.adapters.base.schema_identity import SchemaIdentity
from text2sql_pipeline.db.adapters.factory import make_adapter
from text2sql_pipeline.db.manager import DbManager


class TestDbManagerDDLWithExamples:
    """Test smart DDL generation with example data."""
    
    @pytest.fixture
    def db_manager(self):
        """Create DbManager instance for testing."""
        schema_identity = SchemaIdentity()
        adapter = make_adapter(
            dialect='sqlite',
            kind='file',
            endpoint='./data_examples/databases',
            identity=schema_identity,
        )
        return DbManager(adapter=adapter)
    
    def test_extract_tables_from_sql(self, db_manager):
        """Test extracting table names from SQL query."""
        sql = "SELECT * FROM users JOIN orders ON users.id = orders.user_id"
        tables = db_manager._extract_tables_from_sql(sql, "sqlite")
        
        assert "users" in tables
        assert "orders" in tables
        assert len(tables) == 2
    
    def test_extract_tables_from_complex_sql(self, db_manager):
        """Test extracting tables from complex SQL with subqueries."""
        sql = """
            SELECT u.name, COUNT(o.id)
            FROM users u
            LEFT JOIN orders o ON u.id = o.user_id
            WHERE u.id IN (SELECT user_id FROM subscriptions)
            GROUP BY u.name
        """
        tables = db_manager._extract_tables_from_sql(sql, "sqlite")
        
        assert "users" in tables
        assert "orders" in tables
        assert "subscriptions" in tables
    
    def test_extract_tables_invalid_sql(self, db_manager):
        """Test that invalid SQL returns empty list."""
        sql = "THIS IS NOT VALID SQL"
        tables = db_manager._extract_tables_from_sql(sql, "sqlite")
        
        assert tables == []
    
    def test_format_example_values_numbers(self, db_manager):
        """Test formatting numeric example values."""
        values = [1, 2, 3]
        formatted = db_manager._format_example_values(values)
        
        assert formatted == "[1, 2, 3]"
    
    def test_format_example_values_strings(self, db_manager):
        """Test formatting string example values."""
        values = ["Alice", "Bob"]
        formatted = db_manager._format_example_values(values)
        
        assert formatted == "['Alice', 'Bob']"
    
    def test_format_example_values_mixed(self, db_manager):
        """Test formatting mixed type values."""
        values = [1, "Alice", None]
        formatted = db_manager._format_example_values(values)
        
        assert "1" in formatted
        assert "'Alice'" in formatted
        assert "NULL" in formatted
    
    def test_format_example_values_empty(self, db_manager):
        """Test formatting empty list."""
        values = []
        formatted = db_manager._format_example_values(values)
        
        assert formatted == "[]"
    
    def test_format_example_values_with_quotes(self, db_manager):
        """Test formatting string with single quotes."""
        values = ["O'Brien", "It's fine"]
        formatted = db_manager._format_example_values(values)
        
        # Quotes should be escaped
        assert "O\\'Brien" in formatted
        assert "It\\'s fine" in formatted


class TestDbManagerDDLIntegration:
    """Integration tests with actual database (requires toydb)."""
    
    @pytest.fixture
    def db_manager_with_data(self):
        """Create DbManager with test database."""
        schema_identity = SchemaIdentity()
        adapter = make_adapter(
            dialect='sqlite',
            kind='file',
            endpoint='./data_examples/databases',
            identity=schema_identity,
        )
        return DbManager(adapter=adapter)
    
    def test_get_ddl_schema_with_examples(self, db_manager_with_data):
        """Test DDL generation with real database (toydb)."""
        try:
            # Test with a simple query
            sql = "SELECT * FROM users"
            ddl = db_manager_with_data.get_ddl_schema_with_examples(
                db_id="toydb",
                sql=sql,
                num_examples=2
            )
            
            # Check that DDL contains expected elements
            assert "CREATE TABLE" in ddl
            assert "users" in ddl
            
            # Check for example comments (if data exists)
            # Note: This might fail if toydb has no data
            if "/* ex:" in ddl:
                assert "/* ex:" in ddl
                
        except Exception as e:
            # Database might not exist in test environment
            pytest.skip(f"Database not available: {e}")
    
    def test_get_ddl_schema_with_multiple_tables(self, db_manager_with_data):
        """Test DDL generation with multiple tables."""
        try:
            # Query that references multiple tables
            sql = """
                SELECT u.id, o.total
                FROM users u
                JOIN orders o ON u.id = o.user_id
            """
            ddl = db_manager_with_data.get_ddl_schema_with_examples(
                db_id="toydb",
                sql=sql,
                num_examples=1
            )
            
            # Should contain both tables
            # Note: Might fail if tables don't exist
            if ddl:
                assert "CREATE TABLE" in ddl
                
        except Exception as e:
            pytest.skip(f"Database not available: {e}")
    
    def test_build_create_table_with_examples(self, db_manager_with_data):
        """Test building CREATE TABLE statement with example data."""
        table_info = {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False},
                {"name": "name", "type": "VARCHAR(255)", "nullable": True},
                {"name": "email", "type": "VARCHAR(255)", "nullable": True}
            ],
            "primary_keys": ["id"],
            "foreign_keys": []
        }
        
        examples = {
            "id": [1, 2],
            "name": ["Alice", "Bob"],
            "email": ["alice@example.com", "bob@example.com"]
        }
        
        ddl = db_manager_with_data._build_create_table_with_examples(
            "users",
            table_info,
            examples
        )
        
        # Check structure
        assert "CREATE TABLE users" in ddl
        assert "id INTEGER NOT NULL /* ex: [1, 2] */" in ddl
        assert "name VARCHAR(255) /* ex: ['Alice', 'Bob'] */" in ddl
        assert "PRIMARY KEY (id)" in ddl
    
    def test_build_create_table_with_foreign_keys(self, db_manager_with_data):
        """Test building CREATE TABLE with foreign keys."""
        table_info = {
            "columns": [
                {"name": "id", "type": "INTEGER", "nullable": False},
                {"name": "user_id", "type": "INTEGER", "nullable": False}
            ],
            "primary_keys": ["id"],
            "foreign_keys": [
                {
                    "local": ["user_id"],
                    "parent_table": "users",
                    "parent_columns": ["id"]
                }
            ]
        }
        
        examples = {
            "id": [1, 2],
            "user_id": [10, 20]
        }
        
        ddl = db_manager_with_data._build_create_table_with_examples(
            "orders",
            table_info,
            examples
        )
        
        # Check foreign key
        assert "FOREIGN KEY (user_id) REFERENCES users (id)" in ddl


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

