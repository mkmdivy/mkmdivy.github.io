"""
Vectorize rasters to GeoJSON at ~1km resolution, clipped to Tanzania boundary
"""
import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.features import shapes
from rasterio.warp import calculate_default_transform, reproject, Resampling
from rasterio.io import MemoryFile
import numpy as np
from shapely.geometry import shape, mapping
from shapely.ops import unary_union
import json
import os

# Paths
DATA_DIR = r"U:\mywork\realm\tanzania-map\data"
GPKG_PATH = r"U:\mywork\realm\WEO_OECD-Model-Map.gpkg"

# Target resolution ~1km (0.01 degrees is roughly 1km at equator)
TARGET_RES = 0.01  # degrees

def get_tanzania_boundary():
    """Extract Tanzania boundary from GPKG"""
    print("Loading Tanzania boundary...")
    gdf = gpd.read_file(GPKG_PATH)
    
    # Find Tanzania - try different column names
    tz = None
    for col in ['iso3', 'ISO3', 'iso_a3', 'ISO_A3', 'country_code']:
        if col in gdf.columns:
            tz = gdf[gdf[col] == 'TZA']
            if len(tz) > 0:
                break
    
    if tz is None or len(tz) == 0:
        # Try to find by name
        for col in ['name', 'NAME', 'country', 'COUNTRY']:
            if col in gdf.columns:
                tz = gdf[gdf[col].str.contains('Tanzania', case=False, na=False)]
                if len(tz) > 0:
                    break
    
    if tz is None or len(tz) == 0:
        print(f"Available columns: {gdf.columns.tolist()}")
        print(f"First few rows: {gdf.head()}")
        raise ValueError("Could not find Tanzania in GPKG")
    
    tz = tz.to_crs('EPSG:4326')
    print(f"Found Tanzania boundary with {len(tz)} features")
    
    # Save Tanzania boundary
    tz_boundary = tz.dissolve()
    tz_boundary.to_file(os.path.join(DATA_DIR, 'tanzania_boundary.geojson'), driver='GeoJSON')
    print(f"Saved: tanzania_boundary.geojson")
    
    return tz_boundary

def resample_raster(src, target_res):
    """Resample raster to target resolution"""
    # Calculate new dimensions
    bounds = src.bounds
    new_width = int((bounds.right - bounds.left) / target_res)
    new_height = int((bounds.top - bounds.bottom) / target_res)
    
    # Calculate new transform
    new_transform = rasterio.transform.from_bounds(
        bounds.left, bounds.bottom, bounds.right, bounds.top,
        new_width, new_height
    )
    
    # Resample
    data = src.read(
        1,
        out_shape=(new_height, new_width),
        resampling=Resampling.average
    )
    
    return data, new_transform, src.crs

def vectorize_raster(input_tif, tanzania_geom, output_geojson, value_field='value', 
                     threshold=None, is_binary=False, top_percentile=None):
    """Convert raster to vector polygons clipped to Tanzania"""
    print(f"\nProcessing: {os.path.basename(input_tif)}")
    
    with rasterio.open(input_tif) as src:
        # First clip to Tanzania
        tz_shapes = [mapping(geom) for geom in tanzania_geom.geometry]
        
        try:
            clipped, clipped_transform = mask(src, tz_shapes, crop=True, nodata=src.nodata)
            clipped = clipped[0]  # Get first band
        except Exception as e:
            print(f"  Error clipping: {e}")
            return
        
        nodata = src.nodata if src.nodata is not None else -9999
        
        # Calculate new dimensions for ~1km resolution
        bounds = src.bounds
        current_res = (bounds.right - bounds.left) / src.width
        scale_factor = current_res / TARGET_RES
        
        if scale_factor < 1:
            # Need to downsample (reduce resolution)
            new_height = max(1, int(clipped.shape[0] * scale_factor))
            new_width = max(1, int(clipped.shape[1] * scale_factor))
            
            # Simple block averaging
            from scipy.ndimage import zoom
            clipped_resampled = zoom(clipped, (new_height/clipped.shape[0], new_width/clipped.shape[1]), order=0)
            
            # Update transform
            clipped_transform = rasterio.transform.from_bounds(
                clipped_transform.c, 
                clipped_transform.f + clipped_transform.e * clipped.shape[0],
                clipped_transform.c + clipped_transform.a * clipped.shape[1],
                clipped_transform.f,
                new_width, new_height
            )
            clipped = clipped_resampled
            print(f"  Resampled to: {new_width}x{new_height}")
        
        # Create mask for valid data
        valid_mask = ~np.isclose(clipped, nodata) & ~np.isnan(clipped)
        
        if is_binary:
            # For binary rasters (top 10%), just use value == 1
            binary_data = (clipped == 1).astype(np.uint8)
            binary_data[~valid_mask] = 0
        elif top_percentile is not None:
            # Calculate threshold for top X%
            valid_values = clipped[valid_mask]
            threshold_val = np.percentile(valid_values, 100 - top_percentile)
            binary_data = (clipped >= threshold_val).astype(np.uint8)
            binary_data[~valid_mask] = 0
            print(f"  Top {top_percentile}% threshold: {threshold_val:.2f}")
        elif threshold is not None:
            binary_data = (clipped >= threshold).astype(np.uint8)
            binary_data[~valid_mask] = 0
        else:
            # Just valid data mask
            binary_data = valid_mask.astype(np.uint8)
        
        # Vectorize
        print(f"  Vectorizing...")
        results = list(shapes(binary_data, mask=binary_data==1, transform=clipped_transform))
        
        if len(results) == 0:
            print(f"  No features found!")
            return
        
        print(f"  Found {len(results)} raw polygons")
        
        # Simplify by merging adjacent polygons
        polygons = [shape(geom) for geom, val in results if val == 1]
        
        if len(polygons) == 0:
            print(f"  No valid polygons!")
            return
        
        # Union all polygons and simplify
        merged = unary_union(polygons)
        
        # Create GeoDataFrame
        if merged.geom_type == 'MultiPolygon':
            gdf = gpd.GeoDataFrame({'geometry': list(merged.geoms)}, crs='EPSG:4326')
        else:
            gdf = gpd.GeoDataFrame({'geometry': [merged]}, crs='EPSG:4326')
        
        # Simplify geometries for smaller file size
        gdf['geometry'] = gdf['geometry'].simplify(0.001, preserve_topology=True)
        
        # Remove tiny polygons
        gdf['area'] = gdf.geometry.area
        gdf = gdf[gdf['area'] > 0.0001]  # Remove polygons smaller than ~10 sq km
        gdf = gdf.drop(columns=['area'])
        
        print(f"  Final: {len(gdf)} polygons")
        
        # Save
        gdf.to_file(output_geojson, driver='GeoJSON')
        print(f"  Saved: {os.path.basename(output_geojson)}")
        
        return gdf

def main():
    print("=" * 60)
    print("Vectorizing rasters to GeoJSON (clipped to Tanzania)")
    print("=" * 60)
    
    # Get Tanzania boundary
    tz = get_tanzania_boundary()
    
    # Process wind speed - create "suitable for wind" layer (top 10%)
    vectorize_raster(
        os.path.join(DATA_DIR, 'wind_speed_tanzania.tif'),
        tz,
        os.path.join(DATA_DIR, 'wind_potential.geojson'),
        value_field='wind_speed',
        top_percentile=10
    )
    
    # Process solar PV - create "suitable for solar" layer (top 10%)
    vectorize_raster(
        os.path.join(DATA_DIR, 'pvout_tanzania.tif'),
        tz,
        os.path.join(DATA_DIR, 'solar_potential.geojson'),
        value_field='pvout',
        top_percentile=10
    )
    
    # Process agriculture - areas with cropland
    vectorize_raster(
        os.path.join(DATA_DIR, 'agriculture_tanzania.tif'),
        tz,
        os.path.join(DATA_DIR, 'agriculture_areas.geojson'),
        value_field='cropland',
        threshold=1
    )
    
    print("\n" + "=" * 60)
    print("Vectorization complete!")
    print("=" * 60)

if __name__ == '__main__':
    main()
