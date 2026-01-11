"""PostGIS data loading module."""

from dataclasses import dataclass
import geopandas as gpd
from sqlalchemy import text
from sqlalchemy.engine import Engine


@dataclass
class LoadResult:
    """Result of loading operations."""

    table_name: str
    rows_loaded: int
    indexes_created: bool
    load_time_seconds: float
    errors: list[str]


class PostGISLoader:
    """Loads vector data into PostGIS database."""

    def __init__(self, engine: Engine, batch_size: int = 5000):
        """
        Initialize the loader.

        Args:
            engine: SQLAlchemy database engine
            batch_size: Number of rows to insert per batch
        """
        self.engine = engine
        self.batch_size = batch_size

    def load_dataframe(
        self, gdf: gpd.GeoDataFrame, table_name: str, if_exists: str = "replace"
    ) -> LoadResult:
        """
        Load GeoDataFrame into PostGIS table.

        Args:
            gdf: GeoDataFrame to load
            table_name: Name of the target table
            if_exists: How to behave if table exists ('fail', 'replace', 'append')

        Returns:
            LoadResult with loading statistics
        """
        import time

        start_time = time.time()
        errors: list[str] = []

        try:
            # Load data using geopandas to_postgis
            gdf.to_postgis(
                table_name,
                self.engine,
                if_exists=if_exists,
                index=False,
                chunksize=self.batch_size,
            )

            rows_loaded = len(gdf)
            load_time = time.time() - start_time

            return LoadResult(
                table_name=table_name,
                rows_loaded=rows_loaded,
                indexes_created=False,  # Will add index creation separately
                load_time_seconds=load_time,
                errors=errors,
            )

        except Exception as e:
            errors.append(f"Failed to load data: {str(e)}")
            return LoadResult(
                table_name=table_name,
                rows_loaded=0,
                indexes_created=False,
                load_time_seconds=time.time() - start_time,
                errors=errors,
            )

    def create_spatial_index(
        self, table_name: str, geometry_column: str = "geometry"
    ) -> bool:
        """
        Create GiST spatial index on geometry column.

        Args:
            table_name: Table name
            geometry_column: Name of geometry column

        Returns:
            True if successful, False otherwise
        """
        try:
            index_name = f"{table_name}_geom_idx"
            with self.engine.connect() as conn:
                conn.execute(
                    text(
                        f"CREATE INDEX IF NOT EXISTS {index_name} "
                        f"ON {table_name} USING GIST ({geometry_column});"
                    )
                )
                conn.commit()
            return True
        except Exception:
            return False
