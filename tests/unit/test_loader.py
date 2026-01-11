"""Unit tests for the PostGIS loader module."""

import geopandas as gpd
from shapely.geometry import Point
from unittest.mock import Mock, MagicMock, patch


class TestPostGISLoader:
    """Test suite for PostGISLoader class."""

    def test_import_loader(self):
        """Test that we can import the loader."""
        from src.pipeline.loader import PostGISLoader

        assert PostGISLoader is not None

    def test_create_loader_instance(self):
        """Test creating a loader instance."""
        from src.pipeline.loader import PostGISLoader

        # Create a mock engine
        mock_engine = Mock()
        loader = PostGISLoader(mock_engine)

        assert loader is not None
        assert loader.batch_size == 5000
        assert loader.engine == mock_engine

    def test_create_loader_custom_batch_size(self):
        """Test creating loader with custom batch size."""
        from src.pipeline.loader import PostGISLoader

        mock_engine = Mock()
        loader = PostGISLoader(mock_engine, batch_size=1000)

        assert loader.batch_size == 1000

    @patch("geopandas.GeoDataFrame.to_postgis")
    def test_load_dataframe_success(self, mock_to_postgis):
        """Test successful dataframe loading."""
        from src.pipeline.loader import PostGISLoader

        # Create test data
        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B"]}, geometry=[Point(0, 0), Point(1, 1)], crs="EPSG:4326"
        )

        # Mock the engine
        mock_engine = Mock()
        loader = PostGISLoader(mock_engine)

        # Load data
        result = loader.load_dataframe(gdf, "test_table")

        # Verify to_postgis was called
        mock_to_postgis.assert_called_once()

        # Check result
        assert result.table_name == "test_table"
        assert result.rows_loaded == 2
        assert result.errors == []
        assert result.load_time_seconds >= 0

    @patch("geopandas.GeoDataFrame.to_postgis")
    def test_load_dataframe_with_error(self, mock_to_postgis):
        """Test loading with database error."""
        from src.pipeline.loader import PostGISLoader

        # Mock to_postgis to raise an exception
        mock_to_postgis.side_effect = Exception("Database connection failed")

        gdf = gpd.GeoDataFrame({"name": ["A"]}, geometry=[Point(0, 0)], crs="EPSG:4326")

        mock_engine = Mock()
        loader = PostGISLoader(mock_engine)

        result = loader.load_dataframe(gdf, "test_table")

        # Should handle error gracefully
        assert result.rows_loaded == 0
        assert len(result.errors) > 0
        assert "Failed to load data" in result.errors[0]

    def test_create_spatial_index_success(self):
        """Test creating spatial index."""
        from src.pipeline.loader import PostGISLoader

        # Mock the database connection with context manager
        mock_conn = MagicMock()
        mock_context = MagicMock()
        mock_context.__enter__ = Mock(return_value=mock_conn)
        mock_context.__exit__ = Mock(return_value=False)

        mock_engine = Mock()
        mock_engine.connect.return_value = mock_context

        loader = PostGISLoader(mock_engine)
        result = loader.create_spatial_index("test_table")

        # Should succeed
        assert result is True

        # Verify SQL was executed
        mock_conn.execute.assert_called_once()
        mock_conn.commit.assert_called_once()

    def test_create_spatial_index_failure(self):
        """Test spatial index creation with error."""
        from src.pipeline.loader import PostGISLoader

        # Mock the connection to raise an exception
        mock_engine = Mock()
        mock_engine.connect.side_effect = Exception("Database error")

        loader = PostGISLoader(mock_engine)
        result = loader.create_spatial_index("test_table")

        # Should handle error gracefully
        assert result is False
