"""
Create power grid buffer zones and filter wind/solar rasters by buffer
"""
import geopandas as gpd
import rasterio
from rasterio.mask import mask
import numpy as np
from PIL import Image
from shapely.ops import unary_union
import json
import os

DATA_DIR = r"U:\mywork\realm\tanzania-map\data"
MAX_SIZE = 1000

def create_grid_buffers():
    """Create buffer zones around power grid lines"""
    print("Creating power grid buffer zones...")
    
    grid_path = os.path.join(DATA_DIR, 'power_grid_tanzania.geojson')
    grid = gpd.read_file(grid_path)
    
    # Reproject to UTM for accurate buffering (meters)
    grid_utm = grid.to_crs('EPSG:32736')  # UTM Zone 36S for Tanzania
    
    buffers = {}
    for distance_km in [20, 50, 100]:
        print(f"  Creating {distance_km}km buffer...")
        buffer_m = distance_km * 1000
        buffered = grid_utm.buffer(buffer_m)
        # Union all buffers into one polygon
        union_buffer = unary_union(buffered)
        # Create GeoDataFrame
        buffer_gdf = gpd.GeoDataFrame({'geometry': [union_buffer]}, crs='EPSG:32736')
        # Reproject back to WGS84
        buffer_gdf = buffer_gdf.to_crs('EPSG:4326')
        buffers[distance_km] = buffer_gdf
        
        # Save as GeoJSON
        output_path = os.path.join(DATA_DIR, f'power_grid_buffer_{distance_km}km.geojson')
        buffer_gdf.to_file(output_path, driver='GeoJSON')
        print(f"  Saved: {output_path}")
    
    return buffers

def filter_raster_by_buffer(input_tif, buffer_gdf, output_png, colormap_type):
    """Filter raster to only show values within buffer zone"""
    print(f"Filtering {os.path.basename(input_tif)} by power grid buffer...")
    
    with rasterio.open(input_tif) as src:
        # Get shapes for masking
        shapes = [geom for geom in buffer_gdf.geometry]
        
        # Mask raster with buffer
        out_image, out_transform = mask(src, shapes, crop=False, nodata=src.nodata)
        data = out_image[0]
        
        height, width = data.shape
        scale = min(1.0, MAX_SIZE / max(height, width))
        new_height = int(height * scale)
        new_width = int(width * scale)
        
        # Read with resampling
        data_resampled = src.read(
            1,
            out_shape=(new_height, new_width),
            resampling=rasterio.enums.Resampling.bilinear
        )
        
        # Re-mask the resampled data
        from rasterio.warp import reproject, Resampling
        from rasterio.transform import from_bounds
        
        # Create new transform for resampled data
        bounds = src.bounds
        new_transform = from_bounds(bounds.left, bounds.bottom, bounds.right, bounds.top, new_width, new_height)
        
        # Create mask at new resolution
        from rasterio.features import geometry_mask
        mask_arr = geometry_mask(shapes, out_shape=(new_height, new_width), transform=new_transform, invert=True)
        
        nodata = src.nodata
        if nodata is not None:
            data_mask = np.isclose(data_resampled, nodata) | np.isnan(data_resampled) | ~mask_arr
        else:
            data_mask = np.isnan(data_resampled) | ~mask_arr
        
        valid_data = data_resampled[~data_mask]
        if len(valid_data) == 0:
            print(f"  No valid data after filtering!")
            return None
        
        # Create RGBA image
        rgba = np.zeros((new_height, new_width, 4), dtype=np.uint8)
        
        if colormap_type == 'wind':
            vmin, vmax = np.percentile(valid_data, [5, 95])
            normalized = np.clip((data_resampled - vmin) / (vmax - vmin + 1e-10), 0, 1)
            normalized[data_mask] = 0
            
            r = np.clip(normalized * 2, 0, 1) * 255
            g = np.clip(2 - np.abs(normalized * 2 - 1) * 2, 0, 1) * 255
            b = np.clip((1 - normalized) * 2, 0, 1) * 255
            
            rgba[:,:,0] = r.astype(np.uint8)
            rgba[:,:,1] = g.astype(np.uint8)
            rgba[:,:,2] = b.astype(np.uint8)
            rgba[~data_mask, 3] = 180
            
        elif colormap_type == 'solar':
            vmin, vmax = np.percentile(valid_data, [5, 95])
            normalized = np.clip((data_resampled - vmin) / (vmax - vmin + 1e-10), 0, 1)
            normalized[data_mask] = 0
            
            r = (normalized * 255).astype(np.uint8)
            g = (normalized * 220).astype(np.uint8)
            b = ((1 - normalized) * 180).astype(np.uint8)
            
            rgba[:,:,0] = r
            rgba[:,:,1] = g
            rgba[:,:,2] = b
            rgba[~data_mask, 3] = 180
            
        elif colormap_type == 'wind_binary':
            valid = (data_resampled == 1) & ~data_mask
            rgba[valid, 0] = 30
            rgba[valid, 1] = 100
            rgba[valid, 2] = 255
            rgba[valid, 3] = 200
            
        elif colormap_type == 'solar_binary':
            valid = (data_resampled == 1) & ~data_mask
            rgba[valid, 0] = 255
            rgba[valid, 1] = 140
            rgba[valid, 2] = 0
            rgba[valid, 3] = 200
        
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
    print("=" * 60)
    print("Creating power grid buffers and filtered raster images")
    print("=" * 60)
    
    # Create buffer zones
    buffers = create_grid_buffers()
    
    # Use the largest buffer (100km) for filtering
    buffer_100km = buffers[100]
    
    print("\nFiltering rasters by 100km power grid buffer...")
    
    # Filter wind speed
    filter_raster_by_buffer(
        os.path.join(DATA_DIR, 'wind_speed_tanzania.tif'),
        buffer_100km,
        os.path.join(DATA_DIR, 'wind_speed_filtered.png'),
        'wind'
    )
    
    # Filter wind top 10%
    filter_raster_by_buffer(
        os.path.join(DATA_DIR, 'wind_top10pct_tanzania.tif'),
        buffer_100km,
        os.path.join(DATA_DIR, 'wind_top10_filtered.png'),
        'wind_binary'
    )
    
    # Filter solar
    filter_raster_by_buffer(
        os.path.join(DATA_DIR, 'pvout_tanzania.tif'),
        buffer_100km,
        os.path.join(DATA_DIR, 'solar_pvout_filtered.png'),
        'solar'
    )
    
    # Filter solar top 10%
    filter_raster_by_buffer(
        os.path.join(DATA_DIR, 'pvout_top10pct_tanzania.tif'),
        buffer_100km,
        os.path.join(DATA_DIR, 'solar_top10_filtered.png'),
        'solar_binary'
    )
    
    print("\n" + "=" * 60)
    print("All filtered images created!")

if __name__ == '__main__':
    main()
