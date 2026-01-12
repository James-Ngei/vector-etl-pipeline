# API Reference

## VectorValidator

### Class: `VectorValidator`

Validates vector geospatial data for quality and correctness.

#### Methods

##### `validate_file(filepath: Path) -> ValidationResult`

Validate input file format and readability.

**Parameters:**
- `filepath` (Path): Path to the vector data file

**Returns:**
- `ValidationResult`: Validation status with errors and metadata

**Example:**
```python
from pathlib import Path
from src.pipeline.validator import VectorValidator

validator = VectorValidator()
result = validator.validate_file(Path("data.geojson"))

if result.is_valid:
    print(f"Valid! Features: {result.metadata['feature_count']}")
else:
    print(f"Errors: {result.errors}")
```

##### `check_geometry_validity(gdf: GeoDataFrame) -> Dict[str, Any]`

Check for invalid geometries in the GeoDataFrame.

**Parameters:**
- `gdf` (GeoDataFrame): GeoDataFrame to validate

**Returns:**
- `Dict`: Statistics about geometry validity

**Example:**
```python
import geopandas as gpd

gdf = gpd.read_file("data.shp")
report = validator.check_geometry_validity(gdf)

print(f"Invalid: {report['invalid_count']} ({report['invalid_percentage']:.1f}%)")
```

##### `detect_crs(gdf: GeoDataFrame) -> Optional[str]`

Detect coordinate reference system.

**Parameters:**
- `gdf` (GeoDataFrame): GeoDataFrame to check

**Returns:**
- `str | None`: CRS string (e.g., 'EPSG:4326') or None

---

## GeometryCleaner

### Class: `GeometryCleaner`

Cleans and normalizes vector geometries.

#### Methods

##### `fix_invalid_geometries(gdf: GeoDataFrame) -> CleaningResult`

Fix invalid geometries using ST_MakeValid algorithm.

**Parameters:**
- `gdf` (GeoDataFrame): GeoDataFrame with potentially invalid geometries

**Returns:**
- `CleaningResult`: Cleaned data with statistics

**Example:**
```python
from src.pipeline.cleaner import GeometryCleaner

cleaner = GeometryCleaner()
result = cleaner.fix_invalid_geometries(gdf)

print(f"Fixed {result.fixed_count} geometries")
cleaned_gdf = result.cleaned_gdf
```

##### `normalize_crs(gdf: GeoDataFrame, target_crs: str = "EPSG:4326") -> CleaningResult`

Reproject GeoDataFrame to target CRS.

**Parameters:**
- `gdf` (GeoDataFrame): GeoDataFrame to reproject
- `target_crs` (str): Target CRS (default: EPSG:4326)

**Returns:**
- `CleaningResult`: Reprojected data

**Example:**
```python
result = cleaner.normalize_crs(gdf, target_crs="EPSG:32636")
print(f"Reprojected: {result.reprojected}")
```

##### `remove_duplicates(gdf: GeoDataFrame) -> CleaningResult`

Remove duplicate geometries.

**Parameters:**
- `gdf` (GeoDataFrame): GeoDataFrame with potential duplicates

**Returns:**
- `CleaningResult`: Deduplicated data

---

## PostGISLoader

### Class: `PostGISLoader`

Loads vector data into PostGIS database.

#### Constructor
```python
PostGISLoader(engine: Engine, batch_size: int = 5000)
```

**Parameters:**
- `engine` (Engine): SQLAlchemy database engine
- `batch_size` (int): Number of rows per batch (default: 5000)

#### Methods

##### `load_dataframe(gdf: GeoDataFrame, table_name: str, if_exists: str = "replace") -> LoadResult`

Load GeoDataFrame into PostGIS table.

**Parameters:**
- `gdf` (GeoDataFrame): Data to load
- `table_name` (str): Target table name
- `if_exists` (str): 'fail', 'replace', or 'append' (default: 'replace')

**Returns:**
- `LoadResult`: Loading statistics

**Example:**
```python
from sqlalchemy import create_engine
from src.pipeline.loader import PostGISLoader

engine = create_engine("postgresql://user:pass@localhost/db")
loader = PostGISLoader(engine)

result = loader.load_dataframe(gdf, "my_table")
print(f"Loaded {result.rows_loaded} rows in {result.load_time_seconds:.2f}s")
```

##### `create_spatial_index(table_name: str, geometry_column: str = "geometry") -> bool`

Create GiST spatial index on geometry column.

**Parameters:**
- `table_name` (str): Table name
- `geometry_column` (str): Geometry column name (default: 'geometry')

**Returns:**
- `bool`: True if successful

---

## Data Classes

### `ValidationResult`
```python
@dataclass
class ValidationResult:
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    metadata: Dict[str, Any]
```

### `CleaningResult`
```python
@dataclass
class CleaningResult:
    cleaned_gdf: GeoDataFrame
    fixed_count: int
    removed_count: int
    reprojected: bool
    cleaning_log: list[str]
```

### `LoadResult`
```python
@dataclass
class LoadResult:
    table_name: str
    rows_loaded: int
    indexes_created: bool
    load_time_seconds: float
    errors: list[str]
```

---

## CLI Reference

### `vector-etl validate`

Validate a vector data file.
```bash
vector-etl validate INPUT_FILE
```

**Arguments:**
- `INPUT_FILE`: Path to file to validate

**Example:**
```bash
vector-etl validate data/boundaries.shp
```

### `vector-etl process`

Process vector data through the ETL pipeline.
```bash
vector-etl process INPUT_FILE [OPTIONS]
```

**Arguments:**
- `INPUT_FILE`: Path to file to process

**Options:**
- `--output-table`, `-o`: Output table name (default: processed_data)
- `--validate-only`: Only validate, do not process
- `--skip-cleaning`: Skip geometry cleaning
- `--target-crs`: Target CRS (default: EPSG:4326)
- `--dry-run`: Run without database loading

**Examples:**
```bash
# Basic usage
vector-etl process data.geojson

# Custom table name
vector-etl process data.shp -o parcels

# Dry run (no database)
vector-etl process data.geojson --dry-run

# Custom CRS
vector-etl process data.shp --target-crs EPSG:32636
```