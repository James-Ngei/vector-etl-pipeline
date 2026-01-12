# Usage Examples

## Basic Validation
```bash
# Validate a shapefile
vector-etl validate data/boundaries.shp

# Expected output:
# 🔍 Validating: data/boundaries.shp
# ✅ File is valid
# Metadata:
#   - feature_count: 250
#   - geometry_type: ['Polygon']
```

## Full ETL Pipeline
```bash
# Process with default settings
vector-etl process data/parcels.geojson -o clean_parcels

# Custom CRS
vector-etl process data/roads.shp --target-crs EPSG:32636 -o roads_utm

# Dry run (test without database)
vector-etl process data/test.geojson --dry-run
```

## Python API

### Basic Usage
```python
from pathlib import Path
from src.pipeline.validator import VectorValidator
from src.pipeline.cleaner import GeometryCleaner
import geopandas as gpd

# Validate
validator = VectorValidator()
result = validator.validate_file(Path("data.shp"))

if result.is_valid:
    # Load and clean
    gdf = gpd.read_file("data.shp")
    
    cleaner = GeometryCleaner()
    clean_result = cleaner.fix_invalid_geometries(gdf)
    
    print(f"Fixed {clean_result.fixed_count} geometries")
```

### Advanced: Custom Pipeline
```python
from sqlalchemy import create_engine
from src.pipeline.loader import PostGISLoader

# Custom batch size for large datasets
engine = create_engine("postgresql://user:pass@localhost/db")
loader = PostGISLoader(engine, batch_size=10000)

result = loader.load_dataframe(gdf, "my_table")
print(f"Loaded {result.rows_loaded} rows in {result.load_time_seconds:.2f}s")

# Create spatial index
loader.create_spatial_index("my_table")
```

## Common Scenarios

### Scenario 1: Mixed CRS Dataset
```bash
# Input: Shapefiles in various projections
# Output: Unified EPSG:4326 in PostGIS

vector-etl process county_nad83.shp -o counties
vector-etl process state_wgs84.shp -o states
# Both now in EPSG:4326
```

### Scenario 2: Invalid Geometries
```bash
# Input: Dataset with self-intersecting polygons
# Output: Automatically repaired

vector-etl process messy_boundaries.shp -o clean_boundaries
# ⚠️  Found 342 invalid geometries (3.4%)
# 🔧 Fixed 342 geometries
# ✅ Complete
```

### Scenario 3: Large Dataset
```bash
# For datasets > 1M features, process in chunks
# (Future enhancement - not yet implemented)
```