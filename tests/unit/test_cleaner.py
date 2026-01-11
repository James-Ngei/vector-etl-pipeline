"""Unit tests for the geometry cleaner module."""

import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely import wkt


class TestGeometryCleaner:
    """Test suite for GeometryCleaner class."""

    def test_import_cleaner(self):
        """Test that we can import the cleaner."""
        from src.pipeline.cleaner import GeometryCleaner

        assert GeometryCleaner is not None

    def test_create_cleaner_instance(self):
        """Test creating a cleaner instance."""
        from src.pipeline.cleaner import GeometryCleaner

        cleaner = GeometryCleaner()
        assert cleaner is not None

    def test_fix_invalid_geometry(self):
        """Test fixing a self-intersecting polygon."""
        from src.pipeline.cleaner import GeometryCleaner

        # Create a bowtie polygon (self-intersecting - invalid)
        invalid_poly = wkt.loads("POLYGON((0 0, 2 2, 2 0, 0 2, 0 0))")

        gdf = gpd.GeoDataFrame(
            {"name": ["invalid"]}, geometry=[invalid_poly], crs="EPSG:4326"
        )

        cleaner = GeometryCleaner()
        result = cleaner.fix_invalid_geometries(gdf)

        # After fixing, geometry should be valid
        assert result.cleaned_gdf.geometry.is_valid.all()
        assert result.fixed_count > 0

    def test_normalize_crs_reprojection(self):
        """Test CRS reprojection."""
        from src.pipeline.cleaner import GeometryCleaner

        # Create GeoDataFrame in UTM Zone 36N
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=[Point(500000, 0)],  # UTM coordinates
            crs="EPSG:32636",  # UTM Zone 36N
        )

        cleaner = GeometryCleaner()
        result = cleaner.normalize_crs(gdf, target_crs="EPSG:4326")

        assert result.reprojected is True
        assert result.cleaned_gdf.crs.to_string() == "EPSG:4326"
        assert len(result.cleaning_log) > 0

    def test_normalize_crs_no_reprojection_needed(self):
        """Test when already in target CRS."""
        from src.pipeline.cleaner import GeometryCleaner

        gdf = gpd.GeoDataFrame({"name": ["A"]}, geometry=[Point(0, 0)], crs="EPSG:4326")

        cleaner = GeometryCleaner()
        result = cleaner.normalize_crs(gdf, target_crs="EPSG:4326")

        assert result.reprojected is False
        assert result.cleaned_gdf.crs.to_string() == "EPSG:4326"

    def test_remove_duplicates(self):
        """Test duplicate geometry removal."""
        from src.pipeline.cleaner import GeometryCleaner

        # Create GeoDataFrame with duplicate geometries
        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B", "C"]},
            geometry=[
                Point(0, 0),
                Point(0, 0),
                Point(1, 1),
            ],  # First two are duplicates
            crs="EPSG:4326",
        )

        cleaner = GeometryCleaner()
        result = cleaner.remove_duplicates(gdf)

        assert len(result.cleaned_gdf) == 2  # One duplicate removed
        assert result.removed_count == 1

    def test_remove_duplicates_none_found(self):
        """Test when no duplicates exist."""
        from src.pipeline.cleaner import GeometryCleaner

        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B"]}, geometry=[Point(0, 0), Point(1, 1)], crs="EPSG:4326"
        )

        cleaner = GeometryCleaner()
        result = cleaner.remove_duplicates(gdf)

        assert len(result.cleaned_gdf) == 2
        assert result.removed_count == 0

    def test_fix_preserves_valid_geometries(self):
        """Test that fixing doesn't alter valid geometries."""
        from src.pipeline.cleaner import GeometryCleaner

        valid_poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

        gdf = gpd.GeoDataFrame(
            {"name": ["valid"]}, geometry=[valid_poly], crs="EPSG:4326"
        )

        cleaner = GeometryCleaner()
        result = cleaner.fix_invalid_geometries(gdf)

        # Should not modify valid geometries
        assert result.fixed_count == 0
        assert result.cleaned_gdf.geometry.equals(gdf.geometry)
