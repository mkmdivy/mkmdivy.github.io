"""
Process Wind Turbines Data for Tanzania
- Extracts wind turbines from Africa GPKG
- Clips to Tanzania
- Samples wind speed values at each turbine location
- Saves as GeoJSON for web display
"""

import geopandas as gpd
import rasterio
from shapely.geometry import box, Point
from pathlib import Path
import json
import numpy as np

# Paths
TURBINES_INPUT = r"G:/Resources/STO GIS Repository/3_Data/1_Raw_data/2_Infrastructure/Supply/Power/Power_Plants/Wind/Wind_GEM_Africa_052025.gpkg"
WIND_RASTER = Path(r"U:/mywork/realm/tanzania-map/data/wind_speed_tanzania.tif")
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

def sample_wind_speed(gdf, wind_raster_path):
    """Sample wind speed values at turbine locations"""
    if not wind_raster_path.exists():
        print(f"Warning: Wind raster not found at {wind_raster_path}")
        print("Run process_wind.py first to generate the wind raster")
        gdf['wind_speed'] = None
        return gdf
    
    wind_speeds = []
    
    with rasterio.open(wind_raster_path) as src:
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
                        wind_speeds.append(float(value))
                    else:
                        wind_speeds.append(None)
                else:
                    wind_speeds.append(None)
            except Exception as e:
                wind_speeds.append(None)
    
    gdf['wind_speed'] = wind_speeds
    return gdf

def process_wind_turbines():
    """Main processing function for wind turbines"""
    print("Processing wind turbines data...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read the GPKG file
    print("Reading wind turbines data...")
    
    try:
        # Try to read with bbox filter
        gdf = gpd.read_file(
            TURBINES_INPUT,
            bbox=(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
                  TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])
        )
    except Exception as e:
        print(f"Error reading with bbox: {e}")
        print("Reading full file and filtering...")
        gdf = gpd.read_file(TURBINES_INPUT)
        tanzania_box = get_tanzania_bbox()
        gdf = gdf[gdf.geometry.intersects(tanzania_box)]
    
    print(f"Found {len(gdf)} wind turbines in Tanzania region")
    
    if len(gdf) == 0:
        print("Warning: No wind turbines found in Tanzania region")
        # Create empty GeoJSON
        empty_geojson = {"type": "FeatureCollection", "features": []}
        with open(OUTPUT_DIR / "wind_turbines_tanzania.geojson", "w") as f:
            json.dump(empty_geojson, f)
        
        metadata = {
            "feature_count": 0,
            "bounds": TANZANIA_BOUNDS,
            "columns": []
        }
        with open(OUTPUT_DIR / "wind_turbines_metadata.json", "w") as f:
            json.dump(metadata, f, indent=2)
        return
    
    # Ensure CRS is WGS84
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    
    print("Columns in turbines data:", list(gdf.columns))
    
    # Sample wind speed at each turbine location
    print("Sampling wind speed values at turbine locations...")
    gdf = sample_wind_speed(gdf, WIND_RASTER)
    
    # Count successful samples
    valid_samples = gdf['wind_speed'].notna().sum()
    print(f"Successfully sampled wind speed for {valid_samples} out of {len(gdf)} turbines")
    
    # Save as GeoJSON
    output_file = OUTPUT_DIR / "wind_turbines_tanzania.geojson"
    gdf.to_file(output_file, driver="GeoJSON")
    print(f"Saved wind turbines: {output_file}")
    
    # Save metadata
    metadata = {
        "feature_count": len(gdf),
        "valid_wind_samples": int(valid_samples),
        "bounds": TANZANIA_BOUNDS,
        "columns": list(gdf.columns),
        "wind_speed_stats": {
            "min": float(gdf['wind_speed'].min()) if valid_samples > 0 else None,
            "max": float(gdf['wind_speed'].max()) if valid_samples > 0 else None,
            "mean": float(gdf['wind_speed'].mean()) if valid_samples > 0 else None
        }
    }
    
    with open(OUTPUT_DIR / "wind_turbines_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("Wind turbines processing complete!")

if __name__ == "__main__":
    process_wind_turbines()
