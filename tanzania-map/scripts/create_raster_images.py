"""
Convert GeoTIFF rasters to PNG images for Mapbox display
"""
import rasterio
import numpy as np
from PIL import Image
import os
import json

# Paths
DATA_DIR = r"U:\mywork\realm\tanzania-map\data"

def create_colored_png(input_tif, output_png, colormap='viridis', is_binary=False, color_rgb=None):
    """Convert a GeoTIFF to a colored PNG with transparency"""
    print(f"Converting {os.path.basename(input_tif)} to PNG...")
    
    with rasterio.open(input_tif) as src:
        data = src.read(1)
        bounds = src.bounds
        nodata = src.nodata
        
        # Create mask for nodata
        if nodata is not None:
            mask = (data == nodata) | np.isnan(data)
        else:
            mask = np.isnan(data)
        
        # Get valid data range
        valid_data = data[~mask]
        if len(valid_data) == 0:
            print(f"  Warning: No valid data in {input_tif}")
            return None
            
        vmin, vmax = np.percentile(valid_data, [2, 98])
        print(f"  Data range: {vmin:.2f} to {vmax:.2f}")
        
        if is_binary:
            # Binary layer - use single color with transparency
            rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
            valid = data == 1
            if color_rgb:
                rgba[valid, 0] = color_rgb[0]  # R
                rgba[valid, 1] = color_rgb[1]  # G
                rgba[valid, 2] = color_rgb[2]  # B
                rgba[valid, 3] = 200  # Alpha
            else:
                rgba[valid, 0] = 255  # R
                rgba[valid, 1] = 100  # G
                rgba[valid, 2] = 0    # B
                rgba[valid, 3] = 200  # Alpha
        else:
            # Continuous layer - use colormap
            # Normalize data to 0-1
            normalized = np.clip((data - vmin) / (vmax - vmin), 0, 1)
            
            # Apply colormap based on type
            if colormap == 'wind':
                # Blue to cyan to green to yellow to red
                rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
                # Simple gradient: low=blue, high=red
                rgba[:,:,0] = (normalized * 255).astype(np.uint8)  # R increases
                rgba[:,:,1] = (np.sin(normalized * np.pi) * 200).astype(np.uint8)  # G peaks in middle
                rgba[:,:,2] = ((1 - normalized) * 255).astype(np.uint8)  # B decreases
                rgba[:,:,3] = 180  # Alpha
                rgba[mask, 3] = 0  # Transparent where nodata
                
            elif colormap == 'solar':
                # Purple to yellow (solar theme)
                rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
                rgba[:,:,0] = (normalized * 255).astype(np.uint8)  # R increases
                rgba[:,:,1] = (normalized * 200).astype(np.uint8)  # G increases
                rgba[:,:,2] = ((1 - normalized) * 150).astype(np.uint8)  # B decreases
                rgba[:,:,3] = 180
                rgba[mask, 3] = 0
                
            elif colormap == 'agriculture':
                # Green shades for agriculture
                rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
                valid = ~mask & (data > 0)
                rgba[valid, 0] = 34   # R
                rgba[valid, 1] = 139  # G
                rgba[valid, 2] = 34   # B (forest green)
                rgba[valid, 3] = 180
            else:
                # Default grayscale
                rgba = np.zeros((data.shape[0], data.shape[1], 4), dtype=np.uint8)
                gray = (normalized * 255).astype(np.uint8)
                rgba[:,:,0] = gray
                rgba[:,:,1] = gray
                rgba[:,:,2] = gray
                rgba[:,:,3] = 180
                rgba[mask, 3] = 0
        
        # Ensure nodata is transparent
        rgba[mask, 3] = 0
        
        # Create PIL image and save
        img = Image.fromarray(rgba, 'RGBA')
        img.save(output_png, 'PNG')
        print(f"  Saved: {output_png}")
        
        # Return bounds for Mapbox
        return {
            'bounds': [[bounds.west, bounds.south], [bounds.east, bounds.north]],
            'coordinates': [
                [bounds.west, bounds.north],  # top-left
                [bounds.east, bounds.north],  # top-right
                [bounds.east, bounds.south],  # bottom-right
                [bounds.west, bounds.south]   # bottom-left
            ]
        }

def main():
    print("Creating PNG images from GeoTIFF rasters...")
    
    bounds_info = {}
    
    # Wind speed (continuous)
    wind_tif = os.path.join(DATA_DIR, 'wind_speed_tanzania.tif')
    if os.path.exists(wind_tif):
        result = create_colored_png(
            wind_tif,
            os.path.join(DATA_DIR, 'wind_speed.png'),
            colormap='wind'
        )
        if result:
            bounds_info['wind'] = result
    
    # Wind top 10% (binary)
    wind_top10_tif = os.path.join(DATA_DIR, 'wind_top10pct_tanzania.tif')
    if os.path.exists(wind_top10_tif):
        result = create_colored_png(
            wind_top10_tif,
            os.path.join(DATA_DIR, 'wind_top10.png'),
            is_binary=True,
            color_rgb=(0, 100, 255)  # Blue
        )
        if result:
            bounds_info['wind_top10'] = result
    
    # Solar PV output (continuous)
    solar_tif = os.path.join(DATA_DIR, 'pvout_tanzania.tif')
    if os.path.exists(solar_tif):
        result = create_colored_png(
            solar_tif,
            os.path.join(DATA_DIR, 'solar_pvout.png'),
            colormap='solar'
        )
        if result:
            bounds_info['solar'] = result
    
    # Solar top 10% (binary)
    solar_top10_tif = os.path.join(DATA_DIR, 'pvout_top10pct_tanzania.tif')
    if os.path.exists(solar_top10_tif):
        result = create_colored_png(
            solar_top10_tif,
            os.path.join(DATA_DIR, 'solar_top10.png'),
            is_binary=True,
            color_rgb=(255, 165, 0)  # Orange
        )
        if result:
            bounds_info['solar_top10'] = result
    
    # Agriculture (binary-like)
    agri_tif = os.path.join(DATA_DIR, 'agriculture_tanzania.tif')
    if os.path.exists(agri_tif):
        result = create_colored_png(
            agri_tif,
            os.path.join(DATA_DIR, 'agriculture.png'),
            colormap='agriculture'
        )
        if result:
            bounds_info['agriculture'] = result
    
    # Save bounds info for JavaScript
    with open(os.path.join(DATA_DIR, 'raster_bounds.json'), 'w') as f:
        json.dump(bounds_info, f, indent=2)
    
    print("\nAll PNG images created!")
    print(f"Bounds info saved to: {os.path.join(DATA_DIR, 'raster_bounds.json')}")

if __name__ == '__main__':
    main()
