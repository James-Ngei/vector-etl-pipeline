"""Geometry cleaning and normalization module."""
from typing import Optional
from dataclasses import dataclass
import geopandas as gpd
from shapely.validation import make_valid
from shapely.geometry import MultiPolygon, Polygon


@dataclass
class CleaningResult:
    """Result of cleaning operations."""
    cleaned_gdf: gpd.GeoDataFrame
    fixed_count: int
    removed_count: int
    reprojected: bool
    cleaning_log: list[str]


class GeometryCleaner:
    """Cleans and normalizes vector geometries."""
    
    def __init__(self):
        """Initialize the cleaner."""
        self.cleaning_log = []
    
    def fix_invalid_geometries(self, gdf: gpd.GeoDataFrame) -> CleaningResult:
        """
        Fix invalid geometries using make_valid.
        
        Args:
            gdf: GeoDataFrame with potentially invalid geometries
            
        Returns:
            CleaningResult with fixed geometries
        """
        self.cleaning_log = []
        fixed_count = 0
        
        # Create a copy to avoid modifying original
        cleaned_gdf = gdf.copy()
        
        # Find invalid geometries
        invalid_mask = ~cleaned_gdf.geometry.is_valid
        invalid_count = invalid_mask.sum()
        
        if invalid_count > 0:
            self.cleaning_log.append(f"Found {invalid_count} invalid geometries")
            
            # Fix invalid geometries
            cleaned_gdf.loc[invalid_mask, 'geometry'] = (
                cleaned_gdf.loc[invalid_mask, 'geometry'].apply(make_valid)
            )
            
            fixed_count = invalid_count
            self.cleaning_log.append(f"Fixed {fixed_count} geometries using make_valid")
        
        return CleaningResult(
            cleaned_gdf=cleaned_gdf,
            fixed_count=fixed_count,
            removed_count=0,
            reprojected=False,
            cleaning_log=self.cleaning_log.copy()
        )
    
    def normalize_crs(
        self, 
        gdf: gpd.GeoDataFrame, 
        target_crs: str = "EPSG:4326"
    ) -> CleaningResult:
        """
        Reproject GeoDataFrame to target CRS.
        
        Args:
            gdf: GeoDataFrame to reproject
            target_crs: Target CRS (default: EPSG:4326)
            
        Returns:
            CleaningResult with reprojected data
        """
        self.cleaning_log = []
        reprojected = False
        
        cleaned_gdf = gdf.copy()
        
        # Check if reprojection is needed
        if cleaned_gdf.crs is None:
            self.cleaning_log.append("Warning: No CRS set, assuming EPSG:4326")
            cleaned_gdf.set_crs("EPSG:4326", inplace=True)
        elif cleaned_gdf.crs.to_string() != target_crs:
            original_crs = cleaned_gdf.crs.to_string()
            cleaned_gdf = cleaned_gdf.to_crs(target_crs)
            reprojected = True
            self.cleaning_log.append(f"Reprojected from {original_crs} to {target_crs}")
        else:
            self.cleaning_log.append(f"Already in target CRS: {target_crs}")
        
        return CleaningResult(
            cleaned_gdf=cleaned_gdf,
            fixed_count=0,
            removed_count=0,
            reprojected=reprojected,
            cleaning_log=self.cleaning_log.copy()
        )
    
    def remove_duplicates(self, gdf: gpd.GeoDataFrame) -> CleaningResult:
        """
        Remove duplicate geometries.
        
        Args:
            gdf: GeoDataFrame with potential duplicates
            
        Returns:
            CleaningResult with duplicates removed
        """
        self.cleaning_log = []
        
        original_count = len(gdf)
        
        # Remove duplicates based on geometry
        cleaned_gdf = gdf.drop_duplicates(subset=['geometry'])
        
        removed_count = original_count - len(cleaned_gdf)
        
        if removed_count > 0:
            self.cleaning_log.append(f"Removed {removed_count} duplicate geometries")
        else:
            self.cleaning_log.append("No duplicates found")
        
        return CleaningResult(
            cleaned_gdf=cleaned_gdf,
            fixed_count=0,
            removed_count=removed_count,
            reprojected=False,
            cleaning_log=self.cleaning_log.copy()
        )