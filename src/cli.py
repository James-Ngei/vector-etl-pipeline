"""Command-line interface for the vector ETL pipeline."""

import click
from pathlib import Path
import sys
from sqlalchemy import create_engine

from src.config.settings import DATABASE_CONFIG, ETL_CONFIG
from src.pipeline.validator import VectorValidator
from src.pipeline.cleaner import GeometryCleaner
from src.pipeline.loader import PostGISLoader
import geopandas as gpd


def get_db_engine():
    """Create database engine from config."""
    connection_string = (
        f"postgresql://{DATABASE_CONFIG['user']}:{DATABASE_CONFIG['password']}"
        f"@{DATABASE_CONFIG['host']}:{DATABASE_CONFIG['port']}/{DATABASE_CONFIG['database']}"
    )
    return create_engine(connection_string)


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """Vector ETL Pipeline - Clean and load geospatial data into PostGIS."""
    pass


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output-table", "-o", default="processed_data", help="Output table name"
)
@click.option("--validate-only", is_flag=True, help="Only validate, do not process")
@click.option("--skip-cleaning", is_flag=True, help="Skip geometry cleaning")
@click.option("--target-crs", default="EPSG:4326", help="Target CRS for reprojection")
@click.option("--dry-run", is_flag=True, help="Run pipeline without database loading")
def process(
    input_file, output_table, validate_only, skip_cleaning, target_crs, dry_run
):
    """
    Process vector data through the ETL pipeline.

    INPUT_FILE: Path to shapefile or GeoJSON to process
    """
    click.echo(f"🚀 Starting ETL pipeline for: {input_file}")
    click.echo("=" * 60)

    # Step 1: Validation
    click.echo("\n📋 Step 1: Validating input file...")
    validator = VectorValidator()
    validation_result = validator.validate_file(input_file)

    if not validation_result.is_valid:
        click.echo(click.style("❌ Validation failed:", fg="red"))
        for error in validation_result.errors:
            click.echo(f"  - {error}")
        sys.exit(1)

    click.echo(click.style("✅ Validation passed", fg="green"))
    click.echo(
        f"  - Features: {validation_result.metadata.get('feature_count', 'unknown')}"
    )
    click.echo(
        f"  - Geometry types: {validation_result.metadata.get('geometry_type', [])}"
    )

    if validate_only:
        click.echo("\n✅ Validation complete (--validate-only flag set)")
        return

    # Step 2: Load data
    click.echo("\n📂 Step 2: Loading data...")
    gdf = gpd.read_file(input_file)
    click.echo(f"  - Loaded {len(gdf)} features")

    # Step 3: Check geometry validity
    click.echo("\n🔍 Step 3: Checking geometry validity...")
    geometry_report = validator.check_geometry_validity(gdf)

    if geometry_report["invalid_count"] > 0:
        click.echo(
            click.style(
                f"  ⚠️  Found {geometry_report['invalid_count']} invalid geometries "
                f"({geometry_report['invalid_percentage']:.1f}%)",
                fg="yellow",
            )
        )
    else:
        click.echo(click.style("  ✅ All geometries valid", fg="green"))

    # Step 4: Clean geometries
    cleaner = GeometryCleaner()

    if not skip_cleaning and geometry_report["invalid_count"] > 0:
        click.echo("\n🔧 Step 4: Cleaning invalid geometries...")
        clean_result = cleaner.fix_invalid_geometries(gdf)
        gdf = clean_result.cleaned_gdf
        click.echo(
            click.style(f"  ✅ Fixed {clean_result.fixed_count} geometries", fg="green")
        )
    else:
        click.echo("\n⏭️  Step 4: Skipping geometry cleaning")

    # Step 5: Normalize CRS
    click.echo(f"\n🌍 Step 5: Normalizing CRS to {target_crs}...")
    crs_result = cleaner.normalize_crs(gdf, target_crs=target_crs)
    gdf = crs_result.cleaned_gdf

    if crs_result.reprojected:
        click.echo(click.style(f"  ✅ Reprojected to {target_crs}", fg="green"))
    else:
        click.echo(f"  ℹ️  Already in {target_crs}")

    # Step 6: Remove duplicates
    click.echo("\n🔍 Step 6: Removing duplicates...")
    dedup_result = cleaner.remove_duplicates(gdf)
    gdf = dedup_result.cleaned_gdf

    if dedup_result.removed_count > 0:
        click.echo(
            click.style(
                f"  ✅ Removed {dedup_result.removed_count} duplicate geometries",
                fg="green",
            )
        )
    else:
        click.echo("  ℹ️  No duplicates found")

    # Step 7: Load to PostGIS
    # click.echo(f"\n💾 Step 7: Loading to PostGIS table '{output_table}'...")

    if dry_run:
        click.echo("\n💾 Step 7: Skipping database load (--dry-run mode)")
        click.echo(f"  ℹ️  Would have loaded {len(gdf)} rows to table '{output_table}'")

        click.echo("\n" + "=" * 60)
        click.echo(
            click.style("🎉 ETL Pipeline Complete (dry-run)!", fg="green", bold=True)
        )
        click.echo("\n📊 Summary:")
        click.echo(
            f"  - Input features: {validation_result.metadata.get('feature_count')}"
        )
        click.echo(f"  - Output features: {len(gdf)}")
        click.echo(f"  - Target table: {output_table}")
        return

    click.echo(f"\n💾 Step 7: Loading to PostGIS table '{output_table}'...")

    try:
        engine = get_db_engine()
        loader = PostGISLoader(engine, batch_size=ETL_CONFIG["batch_size"])

        with click.progressbar(
            length=len(gdf), label="Loading data", show_pos=True
        ) as bar:
            load_result = loader.load_dataframe(gdf, output_table)
            bar.update(len(gdf))

        if load_result.errors:
            click.echo(click.style("❌ Loading failed:", fg="red"))
            for error in load_result.errors:
                click.echo(f"  - {error}")
            sys.exit(1)

        click.echo(
            click.style(
                f"  ✅ Loaded {load_result.rows_loaded} rows in "
                f"{load_result.load_time_seconds:.2f}s",
                fg="green",
            )
        )

        # Step 8: Create spatial index
        if ETL_CONFIG["create_indexes"]:
            click.echo("\n🗂️  Step 8: Creating spatial index...")
            index_success = loader.create_spatial_index(output_table)

            if index_success:
                click.echo(click.style("  ✅ Spatial index created", fg="green"))
            else:
                click.echo(click.style("  ⚠️  Failed to create index", fg="yellow"))

        click.echo("\n" + "=" * 60)
        click.echo(click.style("🎉 ETL Pipeline Complete!", fg="green", bold=True))
        click.echo("\n📊 Summary:")
        click.echo(
            f"  - Input features: {validation_result.metadata.get('feature_count')}"
        )
        click.echo(f"  - Output features: {load_result.rows_loaded}")
        click.echo(f"  - Table: {output_table}")
        click.echo(f"  - Processing time: {load_result.load_time_seconds:.2f}s")

    except Exception as e:
        click.echo(click.style(f"\n❌ Error: {str(e)}", fg="red"))
        sys.exit(1)


@cli.command()
@click.argument("input_file", type=click.Path(exists=True, path_type=Path))
def validate(input_file):
    """
    Validate a vector data file without processing.

    INPUT_FILE: Path to shapefile or GeoJSON to validate
    """
    click.echo(f"🔍 Validating: {input_file}\n")

    validator = VectorValidator()
    result = validator.validate_file(input_file)

    if result.is_valid:
        click.echo(click.style("✅ File is valid", fg="green"))
        click.echo("\nMetadata:")
        for key, value in result.metadata.items():
            click.echo(f"  - {key}: {value}")

        # Check geometries
        gdf = gpd.read_file(input_file)
        geom_report = validator.check_geometry_validity(gdf)

        click.echo("\nGeometry Validity:")
        click.echo(f"  - Total features: {geom_report['total_features']}")
        click.echo(f"  - Invalid geometries: {geom_report['invalid_count']}")
        click.echo(f"  - Valid: {geom_report['invalid_percentage']:.1f}% invalid")

        # Check CRS
        crs = validator.detect_crs(gdf)
        click.echo(f"\nCRS: {crs if crs else 'Not set'}")

    else:
        click.echo(click.style("❌ Validation failed", fg="red"))
        for error in result.errors:
            click.echo(f"  - {error}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
