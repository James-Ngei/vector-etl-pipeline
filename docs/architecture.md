# System Architecture

## Overview

The Vector ETL Pipeline is a modular, production-grade system for processing geospatial vector data. It follows a pipeline architecture with clear separation of concerns.

## High-Level Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                     Vector ETL Pipeline                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐   ┌──────────────┐   ┌──────────────┐    │
│  │              │   │              │   │              │    │
│  │  Validator   │──▶│   Cleaner    │──▶│    Loader    │    │
│  │              │   │              │   │              │    │
│  └──────────────┘   └──────────────┘   └──────────────┘    │
│         │                   │                   │            │
│         ▼                   ▼                   ▼            │
│    Validation           Geometry           PostGIS          │
│      Report              Repair            Database         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │   CLI (Click)  │
                    └────────────────┘
```

## Component Architecture

### 1. Validator Module (`src/pipeline/validator.py`)

**Responsibility:** Validate input data quality and structure

**Key Functions:**
- `validate_file()` - Check file format and readability
- `check_geometry_validity()` - Identify invalid geometries
- `detect_crs()` - Detect coordinate reference system

**Input:** File path or GeoDataFrame
**Output:** ValidationResult with errors, warnings, metadata

**Performance:** ~2,000 features/second
```python
┌─────────────────────────────────────┐
│        VectorValidator              │
├─────────────────────────────────────┤
│ + validate_file()                   │
│ + check_geometry_validity()         │
│ + detect_crs()                      │
└─────────────────────────────────────┘
              │
              ▼
     ┌────────────────────┐
     │ ValidationResult   │
     │ - is_valid: bool   │
     │ - errors: list     │
     │ - metadata: dict   │
     └────────────────────┘
```

### 2. Cleaner Module (`src/pipeline/cleaner.py`)

**Responsibility:** Repair and normalize geospatial data

**Key Functions:**
- `fix_invalid_geometries()` - Repair using ST_MakeValid algorithm
- `normalize_crs()` - Reproject to target CRS
- `remove_duplicates()` - Deduplicate based on geometry

**Input:** GeoDataFrame
**Output:** CleaningResult with cleaned GeoDataFrame and statistics

**Performance:** 
- Validation: ~2,000 features/sec
- Repair: ~70 features/sec
- CRS normalization: ~400 ops/sec
```python
┌─────────────────────────────────────┐
│        GeometryCleaner              │
├─────────────────────────────────────┤
│ + fix_invalid_geometries()          │
│ + normalize_crs()                   │
│ + remove_duplicates()               │
└─────────────────────────────────────┘
              │
              ▼
     ┌────────────────────┐
     │  CleaningResult    │
     │ - cleaned_gdf      │
     │ - fixed_count      │
     │ - cleaning_log     │
     └────────────────────┘
```

### 3. Loader Module (`src/pipeline/loader.py`)

**Responsibility:** Load data into PostGIS with optimization

**Key Functions:**
- `load_dataframe()` - Batch insert with transactions
- `create_spatial_index()` - Create GiST spatial index

**Input:** GeoDataFrame, table name
**Output:** LoadResult with timing and row counts

**Performance:** 5,000 rows/batch, configurable
```python
┌─────────────────────────────────────┐
│         PostGISLoader               │
├─────────────────────────────────────┤
│ - engine: Engine                    │
│ - batch_size: int                   │
│ + load_dataframe()                  │
│ + create_spatial_index()            │
└─────────────────────────────────────┘
              │
              ▼
     ┌────────────────────┐
     │    LoadResult      │
     │ - rows_loaded      │
     │ - load_time        │
     │ - errors           │
     └────────────────────┘
```

### 4. CLI Module (`src/cli.py`)

**Responsibility:** User interface and orchestration

**Commands:**
- `vector-etl validate` - Validation only
- `vector-etl process` - Full pipeline

**Features:**
- Progress bars
- Colored output
- Error handling
- Dry-run mode

## Data Flow
```
┌──────────────┐
│ Input File   │ (Shapefile, GeoJSON, GeoPackage)
│ (.shp, .json)│
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Step 1: Validation                   │
│ - Check file format                  │
│ - Verify readability                 │
│ - Count features                     │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Step 2: Load to GeoDataFrame         │
│ - Parse geometries                   │
│ - Load attributes                    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Step 3: Geometry Validity Check      │
│ - Identify invalid geometries        │
│ - Report statistics                  │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Step 4: Geometry Cleaning            │
│ - Fix invalid geometries             │
│ - Apply ST_MakeValid                 │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Step 5: CRS Normalization            │
│ - Detect current CRS                 │
│ - Reproject to EPSG:4326             │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Step 6: Deduplication                │
│ - Remove duplicate geometries        │
│ - Keep first occurrence              │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Step 7: PostGIS Loading              │
│ - Batch insert (5000 rows)           │
│ - Transaction safety                 │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│ Step 8: Spatial Indexing             │
│ - Create GiST index                  │
│ - Optimize queries                   │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────┐
│ PostGIS DB   │
│ (Queryable)  │
└──────────────┘
```

## Technology Stack

### Core Dependencies
- **Python 3.13** - Modern Python with type hints
- **GeoPandas 1.1+** - Spatial data manipulation
- **Shapely 2.1+** - Geometry objects and operations
- **SQLAlchemy 2.0+** - Database ORM
- **psycopg2** - PostgreSQL driver
- **Click 8.x** - CLI framework

### Database
- **PostgreSQL 15** - Relational database
- **PostGIS 3.4** - Spatial extensions

### Development Tools
- **pytest** - Testing framework
- **pytest-cov** - Coverage reporting
- **pytest-benchmark** - Performance testing
- **black** - Code formatter
- **ruff** - Linter
- **mypy** - Type checker

## Design Decisions

### 1. Why GeoPandas over pure Shapely?

**Decision:** Use GeoPandas as primary data structure

**Rationale:**
- Integrates with pandas (familiar API)
- Built-in I/O for multiple formats
- Direct PostGIS integration via `to_postgis()`
- CRS management built-in

**Trade-off:** Slightly higher memory usage vs pure Shapely

### 2. Why ST_MakeValid for geometry repair?

**Decision:** Use Shapely's `make_valid()` (implements ST_MakeValid)

**Rationale:**
- OGC-compliant algorithm
- Predictable, deterministic results
- Preserves topology where possible
- Industry standard

**Alternative considered:** `buffer(0)` - rejected due to unpredictable behavior

### 3. Why batch loading with 5000 rows?

**Decision:** Default batch size of 5000

**Rationale:**
- Tested optimal balance between:
  - Memory usage
  - Transaction overhead
  - Network latency
- Performance benchmarks showed 5000 is sweet spot

**Trade-off:** Larger batches (10K+) caused memory pressure

### 4. Why separate Validator, Cleaner, Loader?

**Decision:** Three separate modules vs monolithic pipeline

**Rationale:**
- **Single Responsibility Principle**
- Independent testing
- Flexible composition
- Reusable components

**Trade-off:** More files to manage, but better maintainability

## Error Handling Strategy

### 1. Validation Errors
- **Strategy:** Fail fast
- **Behavior:** Return ValidationResult with errors
- **User Action:** Fix input data before processing

### 2. Cleaning Errors
- **Strategy:** Best effort repair
- **Behavior:** Log warnings, continue processing
- **User Action:** Review cleaning log

### 3. Loading Errors
- **Strategy:** Transaction rollback
- **Behavior:** Rollback entire batch on error
- **User Action:** Check database connectivity, schema

## Testing Strategy

### Unit Tests (96% coverage)
- Mock database connections
- Test individual functions
- Fast execution (< 5 seconds)

### Integration Tests
- Real PostGIS database in CI/CD
- End-to-end pipeline testing
- Run on Linux (GitHub Actions)

### Performance Tests
- Benchmark key operations
- Track regression over time
- Document expected throughput

## Deployment Architecture
```
┌─────────────────────────────────────────┐
│         Development (Local)             │
│  - Windows/Mac/Linux                    │
│  - Unit tests with mocks                │
│  - Manual testing with --dry-run        │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│         CI/CD (GitHub Actions)          │
│  - Ubuntu Linux                         │
│  - Full integration tests               │
│  - PostGIS in Docker                    │
│  - Performance benchmarks               │
└─────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────┐
│      Production (Future)                │
│  - Containerized deployment             │
│  - Managed PostGIS (AWS RDS, etc.)      │
│  - Horizontal scaling possible          │
└─────────────────────────────────────────┘
```

## Scalability Considerations

### Current Limitations
- Single-threaded processing
- Limited to available memory
- Sequential batch processing

### Future Enhancements
- **Parallel processing** - Multiprocessing for large datasets
- **Streaming** - Process files larger than memory
- **Distributed** - Celery/Dask for multi-node processing
- **Caching** - Cache validation results