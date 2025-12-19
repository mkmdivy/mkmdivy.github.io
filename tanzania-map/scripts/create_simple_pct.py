"""
Simple percentile layer generator - no distance clipping
Just generate top 5%, 10%, 20% for wind and solar
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

# Load Tanzania boundary
print("Loading Tanzania boundary...")
tz_boundary = gpd.read_file(os.path.join(data_dir, 'tanzania_boundary.geojson'))
tz_geom = [tz_boundary.geometry.values[0]]

def create_percentile_layer(raster_path, pct, output_path):
    """Create a simplified layer for a percentile threshold"""
    if os.path.exists(output_path):
        print(f"  Skipping (exists): {os.path.basename(output_path)}")
        return
    
    print(f"  Creating: {os.path.basename(output_path)}")
    
    with rasterio.open(raster_path) as src:
        out_image, out_transform = mask(src, tz_geom, crop=True)
        data = out_image[0]
        
        valid_mask = ~np.isnan(data)
        if src.nodata is not None:
            valid_mask &= (data != src.nodata)
        
        valid_data = data[valid_mask]
        if len(valid_data) == 0:
            print("    No valid data")
            return
        
        threshold = np.percentile(valid_data, 100 - pct)
        print(f"    Threshold: {threshold:.2f}")
        
        binary_mask = (data >= threshold) & valid_mask
        
        shapes_gen = features.shapes(
            binary_mask.astype(np.uint8),
            mask=binary_mask,
            transform=out_transform
        )
        
        polygons = [shape(geom) for geom, val in shapes_gen if val == 1]
        if not polygons:
            print("    No polygons")
            return
        
        gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=src.crs)
        gdf = gdf.to_crs('EPSG:4326')
        
        # Very aggressive simplification (0.02 deg ~ 2km)
        gdf['geometry'] = gdf['geometry'].simplify(0.02)
        gdf = gdf[~gdf.geometry.is_empty]
        gdf['geometry'] = gdf['geometry'].buffer(0)
        gdf = gdf[gdf.geometry.is_valid & ~gdf.geometry.is_empty]
        
        print(f"    Polygons: {len(gdf)}")
        gdf.to_file(output_path, driver='GeoJSON')
        print(f"    Saved: {output_path}")

# Generate layers
print("\n=== WIND ===")
wind_raster = os.path.join(data_dir, 'wind_speed_tanzania.tif')
for pct in [5, 10, 20]:
    create_percentile_layer(wind_raster, pct, os.path.join(data_dir, f'wind_top{pct}pct.geojson'))

print("\n=== SOLAR ===")
solar_raster = os.path.join(data_dir, 'pvout_tanzania.tif')
for pct in [5, 10, 20]:
    create_percentile_layer(solar_raster, pct, os.path.join(data_dir, f'solar_top{pct}pct.geojson'))

print("\n=== Done! ===")
