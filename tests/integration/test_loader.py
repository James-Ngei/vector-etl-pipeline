"""Integration tests for PostGIS loader."""

import pytest
import geopandas as gpd
from shapely.geometry import Point, Polygon


class TestPostGISLoader:
    """Integration tests for PostGISLoader class."""

    def test_import_loader(self):
        """Test that we can import the loader."""
        from src.pipeline.loader import PostGISLoader

        assert PostGISLoader is not None

    def test_create_loader_instance(self, db_engine):
        """Test creating a loader instance."""
        from src.pipeline.loader import PostGISLoader

        loader = PostGISLoader(db_engine)
        assert loader is not None
        assert loader.batch_size == 5000  # Default batch size
