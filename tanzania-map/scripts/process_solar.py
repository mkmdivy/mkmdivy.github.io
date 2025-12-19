"""
Process Solar PV Output Data for Tanzania
- Clips global PVOUT raster to Tanzania
- Calculates top 10% threshold
- Creates binary raster (1 = top 10%, 0 = rest)
- Saves original clipped raster for value sampling
"""

import os
import numpy as np
import rasterio
from rasterio.mask import mask
from pathlib import Path
import json
from shapely.geometry import box

# Paths
SOLAR_INPUT = r"G:/Resources/STO GIS Repository/3_Data/1_Raw_data/3_Resources/Solar/PV_Potential/_rawdata/World_PVOUT_GISdata_LTAy_AvgDailyTotals_GlobalSolarAtlas-v2_GEOTIFF/PVOUT.tif"
OUTPUT_DIR = Path(r"U:/mywork/realm/tanzania-map/data")
TILES_DIR = Path(r"U:/mywork/realm/tanzania-map/tiles/solar")

# Tanzania bounding box
TANZANIA_BOUNDS = {
    "minx": 29.0,
    "miny": -11.75,
    "maxx": 40.5,
    "maxy": -0.95
}

def get_tanzania_geometry():
    """Get Tanzania boundary geometry"""
    return [box(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
                TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])]

def process_solar_data():
    """Main processing function for solar data"""
    print("Processing solar PV output data...")
    
    # Create output directories
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Open and clip the solar raster
    with rasterio.open(SOLAR_INPUT) as src:
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
        solar_data = out_image[0]
        
        # Handle nodata values
        nodata = src.nodata if src.nodata is not None else -9999
        valid_data = solar_data[solar_data != nodata]
        valid_data = valid_data[~np.isnan(valid_data)]
        valid_data = valid_data[valid_data > 0]  # Remove zero/negative values
        
        if len(valid_data) == 0:
            print("Error: No valid data found in the clipped region")
            return
        
        # Calculate top 10% threshold
        threshold_90 = np.percentile(valid_data, 90)
        print(f"Solar PV output statistics:")
        print(f"  Min: {valid_data.min():.2f} kWh/kWp/day")
        print(f"  Max: {valid_data.max():.2f} kWh/kWp/day")
        print(f"  Mean: {valid_data.mean():.2f} kWh/kWp/day")
        print(f"  Top 10% threshold (90th percentile): {threshold_90:.2f} kWh/kWp/day")
        
        # Save original clipped raster (for value sampling)
        original_output = OUTPUT_DIR / "pvout_tanzania.tif"
        with rasterio.open(original_output, "w", **out_meta) as dest:
            dest.write(out_image)
        print(f"Saved original clipped raster: {original_output}")
        
        # Create binary raster (1 = top 10%, 0 = rest)
        binary_data = np.zeros_like(solar_data, dtype=np.uint8)
        binary_data[(solar_data >= threshold_90) & (solar_data != nodata) & (~np.isnan(solar_data))] = 1
        
        # Save binary raster
        binary_meta = out_meta.copy()
        binary_meta.update({"dtype": "uint8", "nodata": 255})
        
        binary_output = OUTPUT_DIR / "pvout_top10pct_tanzania.tif"
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
            "units": "kWh/kWp/day",
            "description": "Photovoltaic power output - daily average"
        }
        
        stats_output = OUTPUT_DIR / "solar_stats.json"
        with open(stats_output, "w") as f:
            json.dump(stats, f, indent=2)
        print(f"Saved statistics: {stats_output}")
    
    print("Solar data processing complete!")
    return threshold_90

if __name__ == "__main__":
    process_solar_data()
