"""Performance benchmarks for the ETL pipeline."""

import geopandas as gpd
from shapely.geometry import Point, Polygon
from shapely import wkt
import pytest

from src.pipeline.validator import VectorValidator
from src.pipeline.cleaner import GeometryCleaner


@pytest.fixture
def small_dataset():
    """Create a small test dataset (100 features)."""
    points = [Point(i, i) for i in range(100)]
    return gpd.GeoDataFrame(
        {"name": [f"point_{i}" for i in range(100)]},
        geometry=points,
        crs="EPSG:4326",
    )


@pytest.fixture
def medium_dataset():
    """Create a medium test dataset (1000 features)."""
    points = [Point(i % 100, i // 100) for i in range(1000)]
    return gpd.GeoDataFrame(
        {"name": [f"point_{i}" for i in range(1000)]},
        geometry=points,
        crs="EPSG:4326",
    )


@pytest.fixture
def dataset_with_invalid_geometries():
    """Create dataset with invalid geometries."""
    # Mix of valid and invalid polygons
    geometries = []

    # Add 50 valid polygons
    for i in range(50):
        geom = Polygon([(i, i), (i + 1, i), (i + 1, i + 1), (i, i + 1)])
        geometries.append(geom)

    # Add 50 invalid polygons (self-intersecting)
    for i in range(50):
        geom = wkt.loads(
            f"POLYGON(({i} {i}, {i+2} {i+2}, {i+2} {i}, {i} {i+2}, {i} {i}))"
        )
        geometries.append(geom)

    return gpd.GeoDataFrame(
        {"name": [f"poly_{i}" for i in range(100)]},
        geometry=geometries,
        crs="EPSG:4326",
    )


class TestValidatorPerformance:
    """Benchmark tests for validator."""

    def test_check_geometry_validity_small(self, benchmark, small_dataset):
        """Benchmark geometry validation on 100 features."""
        validator = VectorValidator()

        result = benchmark(validator.check_geometry_validity, small_dataset)

        assert result["total_features"] == 100
        assert benchmark.stats.stats.mean < 0.1  # Should complete in < 100ms

    def test_check_geometry_validity_medium(self, benchmark, medium_dataset):
        """Benchmark geometry validation on 1000 features."""
        validator = VectorValidator()

        result = benchmark(validator.check_geometry_validity, medium_dataset)

        assert result["total_features"] == 1000
        assert benchmark.stats.stats.mean < 0.5  # Should complete in < 500ms

    def test_detect_crs(self, benchmark, small_dataset):
        """Benchmark CRS detection."""
        validator = VectorValidator()

        result = benchmark(validator.detect_crs, small_dataset)

        assert result == "EPSG:4326"


class TestCleanerPerformance:
    """Benchmark tests for geometry cleaner."""

    def test_fix_invalid_geometries(self, benchmark, dataset_with_invalid_geometries):
        """Benchmark geometry fixing on 100 features (50% invalid)."""
        cleaner = GeometryCleaner()

        result = benchmark(
            cleaner.fix_invalid_geometries, dataset_with_invalid_geometries
        )

        assert result.fixed_count == 50
        assert result.cleaned_gdf.geometry.is_valid.all()
        # Should fix 50 invalid geometries in reasonable time
        assert benchmark.stats.stats.mean < 1.0  # < 1 second

    def test_normalize_crs(self, benchmark, medium_dataset):
        """Benchmark CRS reprojection on 1000 features."""
        cleaner = GeometryCleaner()

        # Reproject from EPSG:4326 to UTM Zone 36N
        result = benchmark(
            cleaner.normalize_crs, medium_dataset, target_crs="EPSG:32636"
        )

        assert result.reprojected is True
        assert result.cleaned_gdf.crs.to_string() == "EPSG:32636"

    def test_remove_duplicates(self, benchmark):
        """Benchmark duplicate removal."""
        # Create dataset with duplicates
        points = [
            Point(i % 10, i % 10) for i in range(1000)
        ]  # 10 unique points, repeated
        gdf = gpd.GeoDataFrame(
            {"name": [f"point_{i}" for i in range(1000)]},
            geometry=points,
            crs="EPSG:4326",
        )

        cleaner = GeometryCleaner()
        result = benchmark(cleaner.remove_duplicates, gdf)

        assert len(result.cleaned_gdf) == 10  # Only unique points remain
        assert result.removed_count == 990


class TestThroughputMetrics:
    """Test processing throughput (features per second)."""

    def test_validation_throughput(self, medium_dataset):
        """Measure validation throughput."""
        validator = VectorValidator()

        import time

        start = time.time()
        validator.check_geometry_validity(medium_dataset)
        elapsed = time.time() - start

        throughput = len(medium_dataset) / elapsed

        print(f"\n  Validation throughput: {throughput:.0f} features/second")
        assert throughput > 1000  # Should process > 1000 features/sec

    def test_cleaning_throughput(self, dataset_with_invalid_geometries):
        """Measure cleaning throughput."""
        cleaner = GeometryCleaner()

        import time

        start = time.time()
        cleaner.fix_invalid_geometries(dataset_with_invalid_geometries)
        elapsed = time.time() - start

        throughput = len(dataset_with_invalid_geometries) / elapsed

        print(f"\n  Cleaning throughput: {throughput:.0f} features/second")
        assert throughput > 50  # Should clean > 50 features/sec
