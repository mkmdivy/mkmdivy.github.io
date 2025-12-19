"""
Convert GeoTIFF rasters to PNG images for Mapbox display (optimized version)
Downsamples large rasters for faster web loading
"""
import rasterio
from rasterio.enums import Resampling
import numpy as np
from PIL import Image
import os
import json

DATA_DIR = r"U:\mywork\realm\tanzania-map\data"
MAX_SIZE = 1000  # Max dimension for web display

def convert_to_png(input_tif, output_png, colormap_type, max_size=MAX_SIZE):
    """Convert GeoTIFF to colored PNG with optional downsampling"""
    print(f"Processing: {os.path.basename(input_tif)}")
    
    with rasterio.open(input_tif) as src:
        # Calculate downsample factor
        height, width = src.shape
        scale = min(1.0, max_size / max(height, width))
        new_height = int(height * scale)
        new_width = int(width * scale)
        
        print(f"  Original: {width}x{height}, Resampled: {new_width}x{new_height}")
        
        # Read with resampling
        data = src.read(
            1,
            out_shape=(new_height, new_width),
            resampling=Resampling.bilinear
        )
        
        bounds = src.bounds
        nodata = src.nodata
        
        # Create mask
        if nodata is not None:
            mask = np.isclose(data, nodata) | np.isnan(data)
        else:
            mask = np.isnan(data)
        
        valid_data = data[~mask]
        if len(valid_data) == 0:
            print(f"  No valid data!")
            return None
        
        # Create RGBA image
        rgba = np.zeros((new_height, new_width, 4), dtype=np.uint8)
        
        if colormap_type == 'wind':
            # Blue (low) to Red (high)
            vmin, vmax = np.percentile(valid_data, [5, 95])
            normalized = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
            normalized[mask] = 0
            
            # Blue -> Cyan -> Green -> Yellow -> Red
            r = np.clip(normalized * 2, 0, 1) * 255
            g = np.clip(2 - np.abs(normalized * 2 - 1) * 2, 0, 1) * 255
            b = np.clip((1 - normalized) * 2, 0, 1) * 255
            
            rgba[:,:,0] = r.astype(np.uint8)
            rgba[:,:,1] = g.astype(np.uint8)
            rgba[:,:,2] = b.astype(np.uint8)
            rgba[~mask, 3] = 180
            
        elif colormap_type == 'solar':
            # Purple (low) to Yellow (high)
            vmin, vmax = np.percentile(valid_data, [5, 95])
            normalized = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
            normalized[mask] = 0
            
            r = (normalized * 255).astype(np.uint8)
            g = (normalized * 220).astype(np.uint8)
            b = ((1 - normalized) * 180).astype(np.uint8)
            
            rgba[:,:,0] = r
            rgba[:,:,1] = g
            rgba[:,:,2] = b
            rgba[~mask, 3] = 180
            
        elif colormap_type == 'wind_binary':
            # Blue for top 10% wind
            valid = (data == 1)
            rgba[valid, 0] = 30
            rgba[valid, 1] = 100
            rgba[valid, 2] = 255
            rgba[valid, 3] = 200
            
        elif colormap_type == 'solar_binary':
            # Orange for top 10% solar
            valid = (data == 1)
            rgba[valid, 0] = 255
            rgba[valid, 1] = 140
            rgba[valid, 2] = 0
            rgba[valid, 3] = 200
            
        elif colormap_type == 'agriculture':
            # Green for agriculture
            valid = ~mask & (data > 0)
            rgba[valid, 0] = 50
            rgba[valid, 1] = 160
            rgba[valid, 2] = 50
            rgba[valid, 3] = 180
        
        # Save PNG
        img = Image.fromarray(rgba, 'RGBA')
        img.save(output_png, 'PNG', optimize=True)
        print(f"  Saved: {output_png}")
        
        return {
            'coordinates': [
                [bounds.left, bounds.top],
                [bounds.right, bounds.top],
                [bounds.right, bounds.bottom],
                [bounds.left, bounds.bottom]
            ]
        }

def main():
    print("=" * 50)
    print("Creating PNG images for web display")
    print("=" * 50)
    
    bounds_info = {}
    
    # Define conversions
    conversions = [
        ('wind_speed_tanzania.tif', 'wind_speed.png', 'wind'),
        ('wind_top10pct_tanzania.tif', 'wind_top10.png', 'wind_binary'),
        ('pvout_tanzania.tif', 'solar_pvout.png', 'solar'),
        ('pvout_top10pct_tanzania.tif', 'solar_top10.png', 'solar_binary'),
        ('agriculture_tanzania.tif', 'agriculture.png', 'agriculture'),
    ]
    
    for tif_name, png_name, cmap in conversions:
        tif_path = os.path.join(DATA_DIR, tif_name)
        png_path = os.path.join(DATA_DIR, png_name)
        
        if os.path.exists(tif_path):
            result = convert_to_png(tif_path, png_path, cmap)
            if result:
                key = png_name.replace('.png', '')
                bounds_info[key] = result
        else:
            print(f"  Skipped: {tif_name} (not found)")
    
    # Save bounds info
    bounds_path = os.path.join(DATA_DIR, 'raster_bounds.json')
    with open(bounds_path, 'w') as f:
        json.dump(bounds_info, f, indent=2)
    
    print("\n" + "=" * 50)
    print("All PNG images created successfully!")
    print(f"Bounds saved to: {bounds_path}")

if __name__ == '__main__':
    main()
