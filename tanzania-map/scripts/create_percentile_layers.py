"""
Create wind and solar potential layers for different percentile thresholds (top 5%, 10%, 20%)
and clip to power grid buffer distances
"""
import rasterio
from rasterio.mask import mask
from rasterio.warp import reproject, Resampling, calculate_default_transform
import geopandas as gpd
import numpy as np
from shapely.geometry import shape, mapping
from rasterio import features
import json
import os

data_dir = r'U:\mywork\realm\tanzania-map\data'

# Load Tanzania boundary
print("Loading Tanzania boundary...")
tz_boundary = gpd.read_file(os.path.join(data_dir, 'tanzania_boundary.geojson'))
tz_geom = [tz_boundary.geometry.values[0]]

# Load power grid buffers
buffers = {}
for dist in [20, 50, 100]:
    buffers[dist] = gpd.read_file(os.path.join(data_dir, f'power_grid_buffer_{dist}km.geojson'))

percentiles = [5, 10, 20]

def vectorize_raster_threshold(raster_path, threshold_pct, tz_geom, output_name):
    """Vectorize raster keeping only values above threshold percentile"""
    with rasterio.open(raster_path) as src:
        # Clip to Tanzania
        out_image, out_transform = mask(src, tz_geom, crop=True)
        data = out_image[0]
        
        # Get valid data
        valid_mask = ~np.isnan(data) & (data != src.nodata if src.nodata else True)
        valid_data = data[valid_mask]
        
        if len(valid_data) == 0:
            print(f"  No valid data found")
            return None
        
        # Calculate threshold (top X% means values above (100-X) percentile)
        threshold = np.percentile(valid_data, 100 - threshold_pct)
        print(f"  Top {threshold_pct}% threshold: {threshold:.2f}")
        
        # Create binary mask for values above threshold
        binary_mask = (data >= threshold) & valid_mask
        
        # Vectorize
        shapes_gen = features.shapes(
            binary_mask.astype(np.uint8),
            mask=binary_mask,
            transform=out_transform
        )
        
        polygons = []
        for geom, value in shapes_gen:
            if value == 1:
                polygons.append(shape(geom))
        
        if not polygons:
            print(f"  No polygons generated")
            return None
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame({'geometry': polygons}, crs=src.crs)
        gdf = gdf.to_crs('EPSG:4326')
        
        # Simplify geometries aggressively (0.005 degrees ~ 500m)
        gdf['geometry'] = gdf['geometry'].simplify(0.005)
        gdf = gdf[~gdf.geometry.is_empty]
        
        # Dissolve and explode
        gdf_dissolved = gdf.dissolve()
        gdf_exploded = gdf_dissolved.explode(index_parts=False).reset_index(drop=True)
        
        # Filter small polygons (less than ~1 sq km)
        gdf_exploded['area'] = gdf_exploded.geometry.area
        gdf_exploded = gdf_exploded[gdf_exploded['area'] > 0.0001]
        gdf_exploded = gdf_exploded.drop(columns=['area'])
        
        print(f"  Generated {len(gdf_exploded)} polygons")
        return gdf_exploded

# Process wind data
print("\n=== Processing Wind Data ===")
wind_raster = os.path.join(data_dir, 'wind_speed_tanzania.tif')

for pct in percentiles:
    print(f"\nWind Top {pct}%:")
    gdf = vectorize_raster_threshold(wind_raster, pct, tz_geom, f'wind_top{pct}pct')
    
    if gdf is not None:
        # Save full version
        out_path = os.path.join(data_dir, f'wind_top{pct}pct.geojson')
        gdf.to_file(out_path, driver='GeoJSON')
        print(f"  Saved: {out_path}")
        
        # Clip to each buffer
        for dist in [20, 50, 100]:
            buffer_dissolved = buffers[dist].dissolve()
            if buffer_dissolved.crs != gdf.crs:
                buffer_dissolved = buffer_dissolved.to_crs(gdf.crs)
            
            clipped = gpd.clip(gdf, buffer_dissolved)
            clipped = clipped[~clipped.geometry.is_empty]
            
            if len(clipped) > 0:
                out_path = os.path.join(data_dir, f'wind_top{pct}pct_{dist}km.geojson')
                clipped.to_file(out_path, driver='GeoJSON')
                print(f"  Saved: {out_path} ({len(clipped)} features)")

# Process solar data
print("\n=== Processing Solar Data ===")
solar_raster = os.path.join(data_dir, 'pvout_tanzania.tif')

for pct in percentiles:
    print(f"\nSolar Top {pct}%:")
    gdf = vectorize_raster_threshold(solar_raster, pct, tz_geom, f'solar_top{pct}pct')
    
    if gdf is not None:
        # Save full version
        out_path = os.path.join(data_dir, f'solar_top{pct}pct.geojson')
        gdf.to_file(out_path, driver='GeoJSON')
        print(f"  Saved: {out_path}")
        
        # Clip to each buffer
        for dist in [20, 50, 100]:
            buffer_dissolved = buffers[dist].dissolve()
            if buffer_dissolved.crs != gdf.crs:
                buffer_dissolved = buffer_dissolved.to_crs(gdf.crs)
            
            clipped = gpd.clip(gdf, buffer_dissolved)
            clipped = clipped[~clipped.geometry.is_empty]
            
            if len(clipped) > 0:
                out_path = os.path.join(data_dir, f'solar_top{pct}pct_{dist}km.geojson')
                clipped.to_file(out_path, driver='GeoJSON')
                print(f"  Saved: {out_path} ({len(clipped)} features)")

print("\n=== Done! ===")
