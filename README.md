# Vector ETL Pipeline

[![CI Pipeline](https://github.com/James-Ngei/vector-etl-pipeline/actions/workflows/ci.yml/badge.svg)](https://github.com/James-Ngei/vector-etl-pipeline/actions/workflows/ci.yml)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-261230.svg)](https://github.com/astral-sh/ruff)

Production-grade ETL pipeline for cleaning and loading geospatial vector data into PostGIS.

## Features

- ✅ **Automated validation** - File format and geometry validity checking
- ✅ **Geometry repair** - Automatic fixing of invalid geometries using `ST_MakeValid`
- ✅ **CRS normalization** - Reproject to target coordinate system
- ✅ **Duplicate removal** - Automatic deduplication
- ✅ **PostGIS loading** - Optimized batch loading with spatial indexing
- ✅ **96% test coverage** - Comprehensive unit tests
- ✅ **CLI interface** - Beautiful command-line tool with progress bars

## Quick Start

### Installation
```bash
pip install poetry
poetry install
```

### Usage

**Validate a file:**
```bash
poetry run vector-etl validate data.geojson
```

**Process and load to PostGIS:**
```bash
poetry run vector-etl process data.shp --output-table my_table
```

**Test without database (dry-run):**
```bash
poetry run vector-etl process data.geojson --dry-run
```

## Documentation

- [Architecture Overview](docs/architecture.md) - System design and component details
- [Design Decisions](docs/design-decisions.md) - Engineering trade-offs and rationale
- [API Reference](docs/api.md) - Complete API documentation
- [Performance Benchmarks](docs/performance.md) - Performance metrics and optimization

## Project Structure
```
vector-etl-pipeline/
├── src/
│   ├── pipeline/
│   │   ├── validator.py      # Data validation
│   │   ├── cleaner.py         # Geometry repair & normalization
│   │   └── loader.py          # PostGIS loading
│   ├── config/
│   │   └── settings.py        # Configuration
│   └── cli.py                 # Command-line interface
├── tests/
│   ├── unit/                  # Unit tests (96% coverage)
│   ├── integration/           # Integration tests (CI only)
│   └── performance/           # Benchmark tests
├── docs/                      # Documentation
├── benchmarks/                # Performance baselines
└── .github/workflows/         # CI/CD pipelines
```

## Architecture
```
Input File → Validation → Geometry Cleaning → CRS Normalization → 
Deduplication → PostGIS Loading → Spatial Indexing
```

## Development

**Run tests:**
```bash
poetry run pytest tests/ --cov=src
```

**Format code:**
```bash
poetry run black src/ tests/
```

**Lint:**
```bash
poetry run ruff check src/ tests/
```

## Test Coverage

- **Overall:** 96%
- **Validator:** 93%
- **Cleaner:** 96%
- **Loader:** 100%

## Tech Stack

- **Python 3.13**
- **GeoPandas** - Spatial data manipulation
- **PostGIS** - Spatial database
- **SQLAlchemy** - Database ORM
- **Click** - CLI framework
- **Pytest** - Testing framework
- **GitHub Actions** - CI/CD

## License

MIT