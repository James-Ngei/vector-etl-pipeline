"""Vector data validation module."""
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass
import geopandas as gpd
from shapely.geometry import Point, Polygon, LineString, MultiPolygon


@dataclass
class ValidationResult:
    """Result of validation operations."""
    is_valid: bool
    errors: list[str]
    warnings: list[str]
    metadata: Dict[str, Any]


class VectorValidator:
    """Validates vector geospatial data."""
    
    def __init__(self):
        """Initialize the validator."""
        self.supported_formats = ['.shp', '.geojson', '.gpkg']
    
    def validate_file(self, filepath: Path) -> ValidationResult:
        """
        Validate input file format and readability.
        
        Args:
            filepath: Path to the vector data file
            
        Returns:
            ValidationResult with validation status
        """
        errors = []
        warnings = []
        metadata = {}
        
        # Check file exists
        if not filepath.exists():
            errors.append(f"File not found: {filepath}")
            return ValidationResult(False, errors, warnings, metadata)
        
        # Check file format
        if filepath.suffix.lower() not in self.supported_formats:
            errors.append(f"Unsupported format: {filepath.suffix}")
            return ValidationResult(False, errors, warnings, metadata)
        
        # Try to read the file
        try:
            gdf = gpd.read_file(filepath)
            metadata['feature_count'] = len(gdf)
            metadata['geometry_type'] = gdf.geom_type.unique().tolist()
        except Exception as e:
            errors.append(f"Cannot read file: {str(e)}")
            return ValidationResult(False, errors, warnings, metadata)
        
        is_valid = len(errors) == 0
        return ValidationResult(is_valid, errors, warnings, metadata)
    def check_geometry_validity(self, gdf: gpd.GeoDataFrame) -> Dict[str, Any]:
        """
        Check for invalid geometries in the GeoDataFrame.
        
        Args:
            gdf: GeoDataFrame to validate
            
        Returns:
            Dictionary with validation statistics
        """
        total_features = len(gdf)
        invalid_geometries = ~gdf.geometry.is_valid
        invalid_count = invalid_geometries.sum()
        
        report = {
            'total_features': total_features,
            'invalid_count': invalid_count,
            'invalid_percentage': (invalid_count / total_features * 100) if total_features > 0 else 0,
            'invalid_indices': gdf[invalid_geometries].index.tolist()
        }
        
        return report
    
    def detect_crs(self, gdf: gpd.GeoDataFrame) -> Optional[str]:
        """
        Detect or infer CRS from GeoDataFrame.
        
        Args:
            gdf: GeoDataFrame to check
            
        Returns:
            CRS string (e.g., 'EPSG:4326') or None
        """
        if gdf.crs is None:
            return None
        return gdf.crs.to_string()