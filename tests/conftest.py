"""Pytest configuration and fixtures."""
import pytest
import sqlalchemy as sa
from sqlalchemy import create_engine, text
from src.config.settings import DATABASE_CONFIG


@pytest.fixture(scope="session")
def db_engine():
    """Create database engine for testing."""
    connection_string = (
        f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
        f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
    )
    engine = create_engine(connection_string)
    
    # Verify PostGIS is available
    with engine.connect() as conn:
        result = conn.execute(text("SELECT PostGIS_version();"))
        version = result.fetchone()
        print(f"PostGIS version: {version[0]}")
    
    yield engine
    engine.dispose()


@pytest.fixture
def clean_test_table(db_engine):
    """Clean up test table before and after each test."""
    table_name = "test_vectors"
    
    # Drop table if exists before test
    with db_engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
        conn.commit()
    
    yield table_name
    
    # Clean up after test
    with db_engine.connect() as conn:
        conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE;"))
        conn.commit()