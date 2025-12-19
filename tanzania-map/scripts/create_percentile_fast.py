"""
Create wind and solar potential layers for different percentile thresholds
Optimized for speed - skips existing files
"""
import rasterio
from rasterio.mask import mask
import geopandas as gpd
import numpy as np
from shapely.geometry import shape
from rasterio import features
import os
import warnings
warnings.filterwarnings('ignore')

data_dir = r'U:\mywork\realm\tanzania-map\data'

# Load Tanzania boundary once
print("Loading Tanzania boundary...")
tz_boundary = gpd.read_file(os.path.join(data_dir, 'tanzania_boundary.geojson'))
tz_geom = [tz_boundary.geometry.values[0]]

# Load power grid buffers once
print("Loading buffers...")
buffers = {}
for dist in [20, 50, 100]:
    buffers[dist] = gpd.read_file(os.path.join(data_dir, f'power_grid_buffer_{dist}km.geojson')).dissolve()

def vectorize_threshold(raster_path, threshold_pct, tz_geom):
    """Vectorize raster at threshold percentile with simplified output"""
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, tz_geom, crop=True)
        data = out_image[0]
        
        valid_mask = ~np.isnan(data)
        if src.nodata is not None:
            valid_mask &= (data != src.nodata)
        
        valid_data = data[valid_mask]
        if len(valid_data) == 0:
            return None
        
        threshold = np.percentile(valid_data, 100 - threshold_pct)
        print(f"    Threshold: {threshold:.2f}")
        
        binary_mask = (data >= threshold) & valid_mask
        
        shapes_gen = features.shapes(
            binary_mask.astype(np.uint8),
            mask=binary_mask,
            transform=out_transform
        )
        
        polygons = [shape(geom) for geom, val in shapes_gen if val == 1]
        if not polygons:
            return None
        
        gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=src.crs)
        gdf = gdf.to_crs('EPSG:4326')
        
        # Simplify heavily
        gdf['geometry'] = gdf['geometry'].simplify(0.01)  # ~1km
        gdf = gdf[~gdf.geometry.is_empty]
        
        # Fix invalid geometries
        gdf['geometry'] = gdf['geometry'].buffer(0)
        gdf = gdf[gdf.geometry.is_valid]
        gdf = gdf[~gdf.geometry.is_empty]
        
        print(f"    {len(gdf)} polygons")
        return gdf

def save_with_buffers(gdf, name, buffers):
    """Save full and buffer-clipped versions"""
    # Save full
    out_path = os.path.join(data_dir, f'{name}.geojson')
    if os.path.exists(out_path):
        print(f"    Skipping {name}.geojson (exists)")
    else:
        gdf.to_file(out_path, driver='GeoJSON')
        print(f"    Saved {name}.geojson ({len(gdf)} features)")
    
    # Clip to buffers
    for dist in [20, 50, 100]:
        out_path = os.path.join(data_dir, f'{name}_{dist}km.geojson')
        if os.path.exists(out_path):
            print(f"    Skipping {name}_{dist}km.geojson (exists)")
            continue
            
        buf = buffers[dist]
        if buf.crs != gdf.crs:
            buf = buf.to_crs(gdf.crs)
        
        clipped = gpd.clip(gdf, buf)
        clipped = clipped[~clipped.geometry.is_empty]
        
        if len(clipped) > 0:
            clipped.to_file(out_path, driver='GeoJSON')
            print(f"    Saved {name}_{dist}km.geojson ({len(clipped)} features)")

# Process
configs = [
    ('wind', os.path.join(data_dir, 'wind_speed_tanzania.tif')),
    ('solar', os.path.join(data_dir, 'pvout_tanzania.tif')),
]

for source_type, raster_path in configs:
    print(f"\n=== {source_type.upper()} ===")
    for pct in [5, 10, 20]:
        name = f'{source_type}_top{pct}pct'
        print(f"\n  Top {pct}%:")
        
        # Check if all files exist
        all_exist = os.path.exists(os.path.join(data_dir, f'{name}.geojson'))
        for dist in [20, 50, 100]:
            all_exist &= os.path.exists(os.path.join(data_dir, f'{name}_{dist}km.geojson'))
        
        if all_exist:
            print(f"    All files exist, skipping")
            continue
        
        gdf = vectorize_threshold(raster_path, pct, tz_geom)
        if gdf is not None:
            save_with_buffers(gdf, name, buffers)

print("\n=== Done! ===")
