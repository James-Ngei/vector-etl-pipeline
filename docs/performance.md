# Performance Benchmarks

## Test Environment
- Python 3.13
- Windows 11 / Ubuntu Linux
- GeoPandas 1.1.2

## Benchmark Results

### Validation Operations

| Operation | Dataset Size | Throughput | Mean Time |
|-----------|--------------|------------|-----------|
| CRS Detection | N/A | 25,449 ops/sec | 39 μs |
| Geometry Validation | 100 features | 1,966 features/sec | 509 μs |
| Geometry Validation | 1000 features | 1,661 features/sec | 602 μs |

### Cleaning Operations

| Operation | Dataset Size | Throughput | Mean Time |
|-----------|--------------|------------|-----------|
| Fix Invalid Geometries | 100 features (50% invalid) | 70 features/sec | 14.2 ms |
| CRS Normalization | 1000 features | 412 ops/sec | 2.4 ms |
| Duplicate Removal | 1000 features | 211 ops/sec | 4.7 ms |

## Performance Characteristics

### Fast Operations (< 1ms)
- ✅ CRS detection
- ✅ File validation
- ✅ Geometry validity checking (small datasets)

### Medium Operations (1-10ms)
- ⚡ CRS reprojection
- ⚡ Duplicate removal
- ⚡ Geometry validation (large datasets)

### Intensive Operations (10ms+)
- 🔧 Invalid geometry repair (expected - uses ST_MakeValid algorithm)

## Expected Performance

For a typical ETL job with 10,000 features:

- **Validation**: ~5 seconds
- **Cleaning (no invalid geometries)**: ~2-3 seconds
- **Cleaning (with 10% invalid)**: ~15-20 seconds
- **Total pipeline**: 20-30 seconds

## Optimization Recommendations

1. **Batch Processing**: Process large datasets in chunks
2. **Parallel Processing**: Use multiprocessing for independent geometries
3. **Pre-filtering**: Remove obviously invalid data before geometry repair
4. **Database Indexing**: Ensure spatial indexes are created after loading