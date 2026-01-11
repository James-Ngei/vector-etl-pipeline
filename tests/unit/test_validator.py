"""Unit tests for the validator module."""

import pytest
import geopandas as gpd
from shapely.geometry import Point, Polygon
from pathlib import Path


class TestVectorValidator:
    """Test suite for VectorValidator class."""

    def test_import_validator(self):
        """Test that we can import the validator."""
        from src.pipeline.validator import VectorValidator

        assert VectorValidator is not None

    def test_create_validator_instance(self):
        """Test creating a validator instance."""
        from src.pipeline.validator import VectorValidator

        validator = VectorValidator()
        assert validator is not None

    def test_validate_nonexistent_file(self):
        """Test validation fails for non-existent file."""
        from src.pipeline.validator import VectorValidator

        validator = VectorValidator()
        result = validator.validate_file(Path("nonexistent.shp"))

        assert result.is_valid is False
        assert len(result.errors) > 0
        assert "not found" in result.errors[0].lower()

    def test_validate_unsupported_format(self, tmp_path):
        """Test validation fails for unsupported file format."""
        from src.pipeline.validator import VectorValidator

        # Create a dummy .txt file
        test_file = tmp_path / "test.txt"
        test_file.write_text("not a geospatial file")

        validator = VectorValidator()
        result = validator.validate_file(test_file)

        assert result.is_valid is False
        assert any("unsupported" in err.lower() for err in result.errors)

    def test_validate_valid_geodataframe(self, tmp_path):
        """Test validation succeeds for valid GeoJSON."""
        from src.pipeline.validator import VectorValidator

        # Create a simple valid GeoDataFrame
        gdf = gpd.GeoDataFrame(
            {"name": ["Point1", "Point2"]},
            geometry=[Point(0, 0), Point(1, 1)],
            crs="EPSG:4326",
        )

        # Save to GeoJSON
        test_file = tmp_path / "test.geojson"
        gdf.to_file(test_file, driver="GeoJSON")

        validator = VectorValidator()
        result = validator.validate_file(test_file)

        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.metadata["feature_count"] == 2

    def test_check_geometry_validity_all_valid(self):
        """Test geometry validation with all valid geometries."""
        from src.pipeline.validator import VectorValidator

        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B"]}, geometry=[Point(0, 0), Point(1, 1)], crs="EPSG:4326"
        )

        validator = VectorValidator()
        report = validator.check_geometry_validity(gdf)

        assert report["total_features"] == 2
        assert report["invalid_count"] == 0
        assert report["invalid_percentage"] == 0.0

    def test_check_geometry_validity_with_invalid(self):
        """Test geometry validation with invalid geometry."""
        from src.pipeline.validator import VectorValidator
        from shapely import wkt

        # Create a self-intersecting polygon (bowtie shape - invalid)
        invalid_poly = wkt.loads("POLYGON((0 0, 2 2, 2 0, 0 2, 0 0))")
        valid_poly = Polygon([(0, 0), (1, 0), (1, 1), (0, 1)])

        gdf = gpd.GeoDataFrame(
            {"name": ["invalid", "valid"]},
            geometry=[invalid_poly, valid_poly],
            crs="EPSG:4326",
        )

        validator = VectorValidator()
        report = validator.check_geometry_validity(gdf)

        assert report["total_features"] == 2
        assert report["invalid_count"] == 1
        assert report["invalid_percentage"] == 50.0

    def test_detect_crs(self):
        """Test CRS detection."""
        from src.pipeline.validator import VectorValidator

        gdf = gpd.GeoDataFrame({"name": ["A"]}, geometry=[Point(0, 0)], crs="EPSG:4326")

        validator = VectorValidator()
        crs = validator.detect_crs(gdf)

        assert crs == "EPSG:4326"

    def test_detect_crs_missing(self):
        """Test CRS detection when CRS is missing."""
        from src.pipeline.validator import VectorValidator

        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=[Point(0, 0)],
            # No CRS set
        )

        validator = VectorValidator()
        crs = validator.detect_crs(gdf)

        assert crs is None
