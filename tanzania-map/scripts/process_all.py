"""
Master Processing Script for Tanzania Energy Map
Runs all data processors and generates tiles for the web application

Requirements:
    pip install numpy rasterio geopandas shapely xarray netcdf4 rio-cogeo

Usage:
    python process_all.py
"""

import subprocess
import sys
from pathlib import Path
import os

# Project paths
PROJECT_DIR = Path(r"U:/mywork/realm/tanzania-map")
SCRIPTS_DIR = PROJECT_DIR / "scripts"
DATA_DIR = PROJECT_DIR / "data"
TILES_DIR = PROJECT_DIR / "tiles"

def run_script(script_name):
    """Run a Python script and print its output"""
    script_path = SCRIPTS_DIR / script_name
    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print('='*60)
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            capture_output=True,
            text=True,
            cwd=str(SCRIPTS_DIR)
        )
        print(result.stdout)
        if result.stderr:
            print(f"Warnings/Errors:\n{result.stderr}")
        if result.returncode != 0:
            print(f"Script failed with return code: {result.returncode}")
            return False
        return True
    except Exception as e:
        print(f"Error running {script_name}: {e}")
        return False

def generate_tiles():
    """Generate PNG tiles from raster data for web display"""
    print(f"\n{'='*60}")
    print("Generating map tiles...")
    print('='*60)
    
    try:
        import rasterio
        from rasterio.warp import calculate_default_transform, reproject, Resampling
        import numpy as np
        from PIL import Image
        import math
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Install with: pip install rasterio pillow")
        return
    
    # Tile generation parameters
    TILE_SIZE = 256
    MIN_ZOOM = 4
    MAX_ZOOM = 10
    
    def lat_lon_to_tile(lat, lon, zoom):
        """Convert lat/lon to tile coordinates"""
        n = 2 ** zoom
        x = int((lon + 180) / 360 * n)
        y = int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n)
        return x, y
    
    def tile_to_bbox(x, y, zoom):
        """Convert tile coordinates to bounding box"""
        n = 2 ** zoom
        lon1 = x / n * 360 - 180
        lon2 = (x + 1) / n * 360 - 180
        lat1 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * (y + 1) / n))))
        lat2 = math.degrees(math.atan(math.sinh(math.pi * (1 - 2 * y / n))))
        return lon1, lat1, lon2, lat2
    
    def generate_tiles_for_raster(input_path, output_dir, colormap, nodata_value=None):
        """Generate tiles for a single raster"""
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with rasterio.open(input_path) as src:
            bounds = src.bounds
            data = src.read(1)
            transform = src.transform
            
            # Get min/max for normalization
            if nodata_value is not None:
                valid_data = data[data != nodata_value]
            else:
                valid_data = data[~np.isnan(data)]
            
            if len(valid_data) == 0:
                print(f"No valid data in {input_path}")
                return
            
            vmin, vmax = valid_data.min(), valid_data.max()
            print(f"Data range: {vmin:.2f} to {vmax:.2f}")
            
            for zoom in range(MIN_ZOOM, MAX_ZOOM + 1):
                print(f"  Generating zoom level {zoom}...")
                
                # Get tile range for this zoom
                x1, y1 = lat_lon_to_tile(bounds.top, bounds.left, zoom)
                x2, y2 = lat_lon_to_tile(bounds.bottom, bounds.right, zoom)
                
                for tx in range(min(x1, x2), max(x1, x2) + 1):
                    for ty in range(min(y1, y2), max(y1, y2) + 1):
                        tile_dir = output_dir / str(zoom) / str(tx)
                        tile_dir.mkdir(parents=True, exist_ok=True)
                        tile_path = tile_dir / f"{ty}.png"
                        
                        # Get tile bounds
                        tile_bbox = tile_to_bbox(tx, ty, zoom)
                        
                        # Create tile image
                        tile_img = Image.new('RGBA', (TILE_SIZE, TILE_SIZE), (0, 0, 0, 0))
                        
                        # Sample raster for this tile
                        for px in range(TILE_SIZE):
                            for py in range(TILE_SIZE):
                                # Calculate geographic coordinates
                                lon = tile_bbox[0] + (tile_bbox[2] - tile_bbox[0]) * px / TILE_SIZE
                                lat = tile_bbox[3] - (tile_bbox[3] - tile_bbox[1]) * py / TILE_SIZE
                                
                                # Check if within raster bounds
                                if bounds.left <= lon <= bounds.right and bounds.bottom <= lat <= bounds.top:
                                    # Get pixel coordinates in raster
                                    row, col = src.index(lon, lat)
                                    if 0 <= row < data.shape[0] and 0 <= col < data.shape[1]:
                                        val = data[row, col]
                                        if nodata_value is not None and val == nodata_value:
                                            continue
                                        if np.isnan(val):
                                            continue
                                        
                                        # Normalize and apply colormap
                                        norm_val = (val - vmin) / (vmax - vmin) if vmax > vmin else 0
                                        norm_val = max(0, min(1, norm_val))
                                        color = colormap(norm_val)
                                        tile_img.putpixel((px, py), color)
                        
                        tile_img.save(tile_path)
        
        print(f"Tiles saved to {output_dir}")
    
    # Define colormaps
    def wind_colormap(val):
        """Red colormap for wind"""
        r = int(255 * val)
        g = int(100 * (1 - val))
        b = int(100 * (1 - val))
        return (r, g, b, int(200 * val) + 55)
    
    def solar_colormap(val):
        """Orange colormap for solar"""
        r = int(255)
        g = int(255 * (1 - val * 0.7))
        b = int(100 * (1 - val))
        return (r, g, b, int(200 * val) + 55)
    
    def agriculture_colormap(val):
        """Green/yellow colormap for agriculture"""
        if val > 0.5:
            return (243, 156, 18, 180)  # Orange for cropland
        return (0, 0, 0, 0)
    
    def binary_colormap(val):
        """Binary colormap for top 10% areas"""
        if val > 0.5:
            return (231, 76, 60, 200)  # Red for top areas
        return (0, 0, 0, 0)
    
    # Generate tiles for each raster
    rasters = [
        (DATA_DIR / "wind_speed_tanzania.tif", TILES_DIR / "wind", wind_colormap),
        (DATA_DIR / "wind_top10pct_tanzania.tif", TILES_DIR / "wind-top10", binary_colormap),
        (DATA_DIR / "pvout_tanzania.tif", TILES_DIR / "solar", solar_colormap),
        (DATA_DIR / "pvout_top10pct_tanzania.tif", TILES_DIR / "solar-top10", binary_colormap),
        (DATA_DIR / "agriculture_tanzania.tif", TILES_DIR / "agriculture", agriculture_colormap),
    ]
    
    for raster_path, tile_dir, colormap in rasters:
        if raster_path.exists():
            print(f"\nProcessing {raster_path.name}...")
            try:
                generate_tiles_for_raster(raster_path, tile_dir, colormap)
            except Exception as e:
                print(f"Error generating tiles: {e}")
        else:
            print(f"Raster not found: {raster_path}")

def main():
    """Main processing pipeline"""
    print("="*60)
    print("Tanzania Energy Map - Data Processing Pipeline")
    print("="*60)
    
    # Create directories
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TILES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Process scripts in order
    scripts = [
        "process_wind.py",
        "process_solar.py",
        "process_power_grid.py",
        "process_protected_areas.py",
        "process_agriculture.py",
        "process_wind_turbines.py",
        "process_solar_panels.py",
    ]
    
    results = {}
    for script in scripts:
        success = run_script(script)
        results[script] = success
    
    # Generate tiles
    generate_tiles()
    
    # Print summary
    print("\n" + "="*60)
    print("Processing Summary")
    print("="*60)
    
    for script, success in results.items():
        status = "✅ Success" if success else "❌ Failed"
        print(f"  {script}: {status}")
    
    # Check output files
    print("\nOutput Files:")
    for f in DATA_DIR.glob("*"):
        size = f.stat().st_size / 1024  # KB
        print(f"  {f.name}: {size:.1f} KB")
    
    print("\n" + "="*60)
    print("Processing complete!")
    print(f"Open {PROJECT_DIR / 'index.html'} in a browser to view the map.")
    print("Note: You need to serve the files from a local web server.")
    print("Run: python -m http.server 8000")
    print("Then open: http://localhost:8000")
    print("="*60)

if __name__ == "__main__":
    main()
