"""
Process Wind Speed Data for Tanzania
- Clips global wind speed raster to Tanzania
- Calculates top 10% threshold
- Creates binary raster (1 = top 10%, 0 = rest)
- Converts to PNG tiles for web display
- Saves original clipped raster for value sampling
"""

import os
import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import geopandas as gpd
from pathlib import Path
import json

# Paths
WIND_INPUT = r"G:/Resources/STO GIS Repository/3_Data/1_Raw_data/3_Resources/Wind/Global_Wind_Atlas/_rawdata/wind-speed_100.tif"
OUTPUT_DIR = Path(r"U:/mywork/realm/tanzania-map/data")
TILES_DIR = Path(r"U:/mywork/realm/tanzania-map/tiles/wind")

# Tanzania bounding box (approximate)
TANZANIA_BOUNDS = {
    "minx": 29.0,
    "miny": -11.75,
    "maxx": 40.5,
    "maxy": -0.95
}

def get_tanzania_geometry():
    """Get Tanzania boundary geometry"""
    # Create a simple bounding box polygon for Tanzania
    from shapely.geometry import box
    return [box(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
                TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])]

def process_wind_data():
    """Main processing function for wind data"""
    print("Processing wind speed data...")
    
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Open and clip the wind raster
    with rasterio.open(WIND_INPUT) as src:
        tanzania_geom = get_tanzania_geometry()
        
        # Clip to Tanzania
        out_image, out_transform = mask(src, tanzania_geom, crop=True)
        out_meta = src.meta.copy()
        
        # Update metadata
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })
        
        # Get the data array
        wind_data = out_image[0]
        
        # Handle nodata values
        nodata = src.nodata if src.nodata is not None else -9999
        valid_data = wind_data[wind_data != nodata]
        valid_data = valid_data[~np.isnan(valid_data)]
        
        if len(valid_data) == 0:
            print("Error: No valid data found in the clipped region")
            return
        
        # Calculate top 10% threshold
        threshold_90 = np.percentile(valid_data, 90)
        print(f"Wind speed statistics:")
        print(f"  Min: {valid_data.min():.2f} m/s")
        print(f"  Max: {valid_data.max():.2f} m/s")
        print(f"  Mean: {valid_data.mean():.2f} m/s")
        print(f"  Top 10% threshold (90th percentile): {threshold_90:.2f} m/s")
        
        # Save original clipped raster (for value sampling)
        original_output = OUTPUT_DIR / "wind_speed_tanzania.tif"
        with rasterio.open(original_output, "w", **out_meta) as dest:
            dest.write(out_image)
        print(f"Saved original clipped raster: {original_output}")
        
        # Create binary raster (1 = top 10%, 0 = rest)
        binary_data = np.zeros_like(wind_data, dtype=np.uint8)
        binary_data[(wind_data >= threshold_90) & (wind_data != nodata) & (~np.isnan(wind_data))] = 1
        
        # Save binary raster
        binary_meta = out_meta.copy()
        binary_meta.update({"dtype": "uint8", "nodata": 255})
        
        binary_output = OUTPUT_DIR / "wind_top10pct_tanzania.tif"
        with rasterio.open(binary_output, "w", **binary_meta) as dest:
            dest.write(binary_data, 1)
        print(f"Saved binary raster: {binary_output}")
        
        # Save statistics as JSON for the web app
        stats = {
            "min": float(valid_data.min()),
            "max": float(valid_data.max()),
            "mean": float(valid_data.mean()),
            "threshold_top10": float(threshold_90),
            "bounds": TANZANIA_BOUNDS,
            "units": "m/s",
            "description": "Wind speed at 100m height"
        }
        
        stats_output = OUTPUT_DIR / "wind_stats.json"
        with open(stats_output, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"Saved statistics: {stats_output}")
    
    print("Wind data processing complete!")
    return threshold_90

if __name__ == "__main__":
    process_wind_data()
