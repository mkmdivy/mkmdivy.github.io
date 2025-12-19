"""
Clip wind and solar potential areas to power grid buffer distances
"""
import geopandas as gpd
import os

data_dir = r'U:\mywork\realm\tanzania-map\data'

# Load the base data
print("Loading wind potential...")
wind = gpd.read_file(os.path.join(data_dir, 'wind_potential.geojson'))
print(f"  Wind features: {len(wind)}")

print("Loading solar potential...")
solar = gpd.read_file(os.path.join(data_dir, 'solar_potential.geojson'))
print(f"  Solar features: {len(solar)}")

# Load buffers
buffers = {}
for dist in [20, 50, 100]:
    print(f"Loading {dist}km buffer...")
    buffers[dist] = gpd.read_file(os.path.join(data_dir, f'power_grid_buffer_{dist}km.geojson'))
    print(f"  Buffer features: {len(buffers[dist])}")

# Ensure same CRS
for dist in buffers:
    if buffers[dist].crs != wind.crs:
        buffers[dist] = buffers[dist].to_crs(wind.crs)

# Clip wind and solar to each buffer
for dist in [20, 50, 100]:
    print(f"\nClipping to {dist}km buffer...")
    
    # Dissolve buffer to single polygon
    buffer_dissolved = buffers[dist].dissolve()
    
    # Clip wind
    print(f"  Clipping wind...")
    wind_clipped = gpd.clip(wind, buffer_dissolved)
    wind_clipped = wind_clipped[~wind_clipped.geometry.is_empty]
    out_path = os.path.join(data_dir, f'wind_potential_{dist}km.geojson')
    wind_clipped.to_file(out_path, driver='GeoJSON')
    print(f"  Wind {dist}km: {len(wind_clipped)} features -> {out_path}")
    
    # Clip solar
    print(f"  Clipping solar...")
    solar_clipped = gpd.clip(solar, buffer_dissolved)
    solar_clipped = solar_clipped[~solar_clipped.geometry.is_empty]
    out_path = os.path.join(data_dir, f'solar_potential_{dist}km.geojson')
    solar_clipped.to_file(out_path, driver='GeoJSON')
    print(f"  Solar {dist}km: {len(solar_clipped)} features -> {out_path}")

print("\nDone! Created pre-clipped files for each buffer distance.")
