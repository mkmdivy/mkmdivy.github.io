"""
Create filtered wind/solar images for all buffer distances (20km, 50km, 100km)
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

def create_filtered_image(input_tif, buffer_gdf, output_png, colormap_type):
    """Create filtered PNG using buffer mask"""
    
    with rasterio.open(input_tif) as src:
        height, width = src.shape
        scale = min(1.0, MAX_SIZE / max(height, width))
        new_height = int(height * scale)
        new_width = int(width * scale)
        
        # Read with resampling
        data = src.read(1, out_shape=(new_height, new_width), resampling=Resampling.bilinear)
        bounds = src.bounds
        nodata = src.nodata
        
        # Create transform for resampled data
        new_transform = from_bounds(bounds.left, bounds.bottom, bounds.right, bounds.top, new_width, new_height)
        
        # Create buffer mask (True = inside buffer)
        buffer_mask = geometry_mask(
            buffer_gdf.geometry,
            out_shape=(new_height, new_width),
            transform=new_transform,
            invert=True
        )
        
        # Create nodata mask
        if nodata is not None:
            nodata_mask = np.isclose(data, nodata) | np.isnan(data)
        else:
            nodata_mask = np.isnan(data)
        
        # Combined mask: valid data inside buffer
        valid_mask = buffer_mask & ~nodata_mask
        
        valid_data = data[valid_mask]
        if len(valid_data) == 0:
            print(f"    No valid data!")
            return
        
        # Create RGBA image
        rgba = np.zeros((new_height, new_width, 4), dtype=np.uint8)
        
        if colormap_type == 'wind':
            vmin, vmax = np.percentile(valid_data, [5, 95])
            normalized = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
            
            r = np.clip(normalized * 2, 0, 1) * 255
            g = np.clip(2 - np.abs(normalized * 2 - 1) * 2, 0, 1) * 255
            b = np.clip((1 - normalized) * 2, 0, 1) * 255
            
            rgba[:,:,0] = r.astype(np.uint8)
            rgba[:,:,1] = g.astype(np.uint8)
            rgba[:,:,2] = b.astype(np.uint8)
            rgba[valid_mask, 3] = 180
            
        elif colormap_type == 'solar':
            vmin, vmax = np.percentile(valid_data, [5, 95])
            normalized = np.clip((data - vmin) / (vmax - vmin + 1e-10), 0, 1)
            
            rgba[:,:,0] = (normalized * 255).astype(np.uint8)
            rgba[:,:,1] = (normalized * 220).astype(np.uint8)
            rgba[:,:,2] = ((1 - normalized) * 180).astype(np.uint8)
            rgba[valid_mask, 3] = 180
            
        elif colormap_type == 'wind_binary':
            valid = (data == 1) & valid_mask
            rgba[valid, 0] = 30
            rgba[valid, 1] = 100
            rgba[valid, 2] = 255
            rgba[valid, 3] = 200
            
        elif colormap_type == 'solar_binary':
            valid = (data == 1) & valid_mask
            rgba[valid, 0] = 255
            rgba[valid, 1] = 140
            rgba[valid, 2] = 0
            rgba[valid, 3] = 200
        
        # Save
        img = Image.fromarray(rgba, 'RGBA')
        img.save(output_png, 'PNG', optimize=True)

def main():
    print("=" * 60)
    print("Creating filtered images for all buffer distances")
    print("=" * 60)
    
    # Rasters to process
    rasters = [
        ('wind_speed_tanzania.tif', 'wind_speed', 'wind'),
        ('wind_top10pct_tanzania.tif', 'wind_top10', 'wind_binary'),
        ('pvout_tanzania.tif', 'solar_pvout', 'solar'),
        ('pvout_top10pct_tanzania.tif', 'solar_top10', 'solar_binary'),
    ]
    
    # Buffer distances
    buffer_distances = [20, 50, 100]
    
    for distance in buffer_distances:
        buffer_path = os.path.join(DATA_DIR, f'power_grid_buffer_{distance}km.geojson')
        if not os.path.exists(buffer_path):
            print(f"Buffer {distance}km not found, skipping...")
            continue
        
        buffer_gdf = gpd.read_file(buffer_path)
        print(f"\nProcessing {distance}km buffer...")
        
        for tif_name, png_base, cmap in rasters:
            tif_path = os.path.join(DATA_DIR, tif_name)
            png_path = os.path.join(DATA_DIR, f'{png_base}_{distance}km.png')
            
            if os.path.exists(tif_path):
                print(f"  {png_base}_{distance}km.png")
                create_filtered_image(tif_path, buffer_gdf, png_path, cmap)
    
    print("\n" + "=" * 60)
    print("All filtered images created!")

if __name__ == '__main__':
    main()
