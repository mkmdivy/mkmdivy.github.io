"""
Create all combinations of percentile + buffer distance files
"""
import geopandas as gpd
import os
import warnings
warnings.filterwarnings('ignore')

data_dir = r'U:\mywork\realm\tanzania-map\data'

# Load buffers
print("Loading buffers...")
buffers = {}
for dist in [20, 50, 100]:
    buffers[dist] = gpd.read_file(os.path.join(data_dir, f'power_grid_buffer_{dist}km.geojson')).dissolve()

# Process all combinations
for source_type in ['wind', 'solar']:
    print(f"\n=== {source_type.upper()} ===")
    
    for pct in [5, 10, 20]:
        # Load base percentile file
        base_file = os.path.join(data_dir, f'{source_type}_top{pct}pct.geojson')
        if not os.path.exists(base_file):
            print(f"  Missing: {base_file}")
            continue
        
        print(f"\n  Top {pct}%:")
        gdf = gpd.read_file(base_file)
        print(f"    Base: {len(gdf)} features")
        
        # Clip to each buffer distance
        for dist in [20, 50, 100]:
            out_file = os.path.join(data_dir, f'{source_type}_top{pct}pct_{dist}km.geojson')
            
            if os.path.exists(out_file):
                existing = gpd.read_file(out_file)
                print(f"    {dist}km: exists ({len(existing)} features)")
                continue
            
            buf = buffers[dist]
            if buf.crs != gdf.crs:
                buf = buf.to_crs(gdf.crs)
            
            clipped = gpd.clip(gdf, buf)
            clipped = clipped[~clipped.geometry.is_empty]
            
            if len(clipped) > 0:
                clipped.to_file(out_file, driver='GeoJSON')
                print(f"    {dist}km: created ({len(clipped)} features)")
            else:
                print(f"    {dist}km: no features after clipping")

print("\n=== Done! ===")
