"""
Process Solar Panels Data for Tanzania
- Extracts solar installations from Africa GPKG
- Clips to Tanzania
- Samples solar PV output values at each installation location
- Saves as GeoJSON for web display
"""

import geopandas as gpd
import rasterio
from shapely.geometry import box
from pathlib import Path
import json
import numpy as np

# Paths
SOLAR_INPUT = r"G:/Resources/STO GIS Repository/3_Data/1_Raw_data/2_Infrastructure/Supply/Power/Power_Plants/Solar/Solar_GEM_Africa_052025.gpkg"
SOLAR_RASTER = Path(r"U:/mywork/realm/tanzania-map/data/pvout_tanzania.tif")
OUTPUT_DIR = Path(r"U:/mywork/realm/tanzania-map/data")

# Tanzania bounding box
TANZANIA_BOUNDS = {
    "minx": 29.0,
    "miny": -11.75,
    "maxx": 40.5,
    "maxy": -0.95
}

def get_tanzania_bbox():
    """Get Tanzania bounding box as geometry"""
    return box(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
               TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])

def sample_solar_output(gdf, solar_raster_path):
    """Sample solar PV output values at installation locations"""
    if not solar_raster_path.exists():
        print(f"Warning: Solar raster not found at {solar_raster_path}")
        print("Run process_solar.py first to generate the solar raster")
        gdf['pvout'] = None
        return gdf
    
    pvout_values = []
    
    with rasterio.open(solar_raster_path) as src:
        for idx, row in gdf.iterrows():
            try:
                # Get point coordinates
                if row.geometry.geom_type == 'Point':
                    lon, lat = row.geometry.x, row.geometry.y
                else:
                    # Use centroid for non-point geometries
                    centroid = row.geometry.centroid
                    lon, lat = centroid.x, centroid.y
                
                # Sample the raster at this location
                row_idx, col_idx = src.index(lon, lat)
                
                # Check if within bounds
                if 0 <= row_idx < src.height and 0 <= col_idx < src.width:
                    value = src.read(1)[row_idx, col_idx]
                    if value != src.nodata and not np.isnan(value):
                        pvout_values.append(float(value))
                    else:
                        pvout_values.append(None)
                else:
                    pvout_values.append(None)
            except Exception as e:
                pvout_values.append(None)
    
    gdf['pvout'] = pvout_values
    return gdf

def process_solar_panels():
    """Main processing function for solar panels"""
    print("Processing solar panels data...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read the GPKG file
    print("Reading solar panels data...")
    
    try:
        # Try to read with bbox filter
        gdf = gpd.read_file(
            SOLAR_INPUT,
            bbox=(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
                  TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])
        )
    except Exception as e:
        print(f"Error reading with bbox: {e}")
        print("Reading full file and filtering...")
        gdf = gpd.read_file(SOLAR_INPUT)
        tanzania_box = get_tanzania_bbox()
        gdf = gdf[gdf.geometry.intersects(tanzania_box)]
    
    print(f"Found {len(gdf)} solar installations in Tanzania region")
    
    if len(gdf) == 0:
        print("Warning: No solar installations found in Tanzania region")
        # Create empty GeoJSON
        empty_geojson = {"type": "FeatureCollection", "features": []}
        with open(OUTPUT_DIR / "solar_panels_tanzania.geojson", "w") as f:
            json.dump(empty_geojson, f)
        
        metadata = {
            "feature_count": 0,
            "bounds": TANZANIA_BOUNDS,
            "columns": []
        }
        with open(OUTPUT_DIR / "solar_panels_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        return
    
    # Ensure CRS is WGS84
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    
    print("Columns in solar data:", list(gdf.columns))
    
    # Sample solar PV output at each installation location
    print("Sampling solar PV output values at installation locations...")
    gdf = sample_solar_output(gdf, SOLAR_RASTER)
    
    # Count successful samples
    valid_samples = gdf['pvout'].notna().sum()
    print(f"Successfully sampled PV output for {valid_samples} out of {len(gdf)} installations")
    
    # Save as GeoJSON
    output_file = OUTPUT_DIR / "solar_panels_tanzania.geojson"
    gdf.to_file(output_file, driver="GeoJSON")
    print(f"Saved solar panels: {output_file}")
    
    # Save metadata
    metadata = {
        "feature_count": len(gdf),
        "valid_pvout_samples": int(valid_samples),
        "bounds": TANZANIA_BOUNDS,
        "columns": list(gdf.columns),
        "pvout_stats": {
            "min": float(gdf['pvout'].min()) if valid_samples > 0 else None,
            "max": float(gdf['pvout'].max()) if valid_samples > 0 else None,
            "mean": float(gdf['pvout'].mean()) if valid_samples > 0 else None
        }
    }
    
    with open(OUTPUT_DIR / "solar_panels_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("Solar panels processing complete!")

if __name__ == "__main__":
    process_solar_panels()
