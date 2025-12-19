"""
Create binary colored wind/solar images for all buffer distances
Blue for wind, Orange for solar - solid colors, not gradients
"""
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from rasterio.transform import from_bounds
from rasterio.enums import Resampling
import numpy as np
from PIL import Image
import os

DATA_DIR = r"U:\mywork\realm\tanzania-map\data"
MAX_SIZE = 1000

def create_binary_image(input_tif, buffer_gdf, output_png, color_rgb, is_top10=False):
    """Create binary colored PNG using buffer mask"""
    
    with rasterio.open(input_tif) as src:
        h, w = src.shape
        scale = min(1.0, MAX_SIZE / max(h, w))
        nh, nw = int(h * scale), int(w * scale)
        
        data = src.read(1, out_shape=(nh, nw), resampling=Resampling.bilinear)
        bounds = src.bounds
        nodata = src.nodata
        
        new_transform = from_bounds(bounds.left, bounds.bottom, bounds.right, bounds.top, nw, nh)
        
        # Create buffer mask
        buffer_mask = geometry_mask(
            buffer_gdf.geometry,
            out_shape=(nh, nw),
            transform=new_transform,
            invert=True
        )
        
        # Create nodata mask
        if nodata is not None:
            nodata_mask = np.isclose(data, nodata) | np.isnan(data)
        else:
            nodata_mask = np.isnan(data)
        
        if is_top10:
            # For top 10% files, data == 1 means it's in top 10%
            valid_mask = buffer_mask & ~nodata_mask & (data == 1)
        else:
            # For regular files, any valid data
            valid_mask = buffer_mask & ~nodata_mask & (data > 0)
        
        # Create RGBA with solid color
        rgba = np.zeros((nh, nw, 4), dtype=np.uint8)
        rgba[valid_mask, 0] = color_rgb[0]
        rgba[valid_mask, 1] = color_rgb[1]
        rgba[valid_mask, 2] = color_rgb[2]
        rgba[valid_mask, 3] = 180
        
        Image.fromarray(rgba, 'RGBA').save(output_png, 'PNG', optimize=True)

def main():
    print("=" * 60)
    print("Creating binary colored images for all buffer distances")
    print("=" * 60)
    
    # Colors
    WIND_COLOR = (30, 120, 255)      # Blue
    WIND_TOP10_COLOR = (0, 80, 200)  # Darker blue for top 10%
    SOLAR_COLOR = (255, 180, 50)     # Orange
    SOLAR_TOP10_COLOR = (255, 120, 0) # Darker orange for top 10%
    
    buffer_distances = [20, 50, 100]
    
    for d in buffer_distances:
        buffer_path = os.path.join(DATA_DIR, f'power_grid_buffer_{d}km.geojson')
        if not os.path.exists(buffer_path):
            print(f"Buffer {d}km not found, skipping...")
            continue
        
        buffer_gdf = gpd.read_file(buffer_path)
        print(f"\n{d}km buffer:")
        
        # Wind speed (binary)
        tif = os.path.join(DATA_DIR, 'wind_speed_tanzania.tif')
        if os.path.exists(tif):
            print(f"  wind_speed_{d}km.png (binary blue)")
            create_binary_image(tif, buffer_gdf, 
                              os.path.join(DATA_DIR, f'wind_speed_{d}km.png'),
                              WIND_COLOR, is_top10=False)
        
        # Wind top 10%
        tif = os.path.join(DATA_DIR, 'wind_top10pct_tanzania.tif')
        if os.path.exists(tif):
            print(f"  wind_top10_{d}km.png (binary dark blue)")
            create_binary_image(tif, buffer_gdf,
                              os.path.join(DATA_DIR, f'wind_top10_{d}km.png'),
                              WIND_TOP10_COLOR, is_top10=True)
        
        # Solar PV (binary)
        tif = os.path.join(DATA_DIR, 'pvout_tanzania.tif')
        if os.path.exists(tif):
            print(f"  solar_pvout_{d}km.png (binary orange)")
            create_binary_image(tif, buffer_gdf,
                              os.path.join(DATA_DIR, f'solar_pvout_{d}km.png'),
                              SOLAR_COLOR, is_top10=False)
        
        # Solar top 10%
        tif = os.path.join(DATA_DIR, 'pvout_top10pct_tanzania.tif')
        if os.path.exists(tif):
            print(f"  solar_top10_{d}km.png (binary dark orange)")
            create_binary_image(tif, buffer_gdf,
                              os.path.join(DATA_DIR, f'solar_top10_{d}km.png'),
                              SOLAR_TOP10_COLOR, is_top10=True)
    
    print("\n" + "=" * 60)
    print("All binary images created!")

if __name__ == '__main__':
    main()
