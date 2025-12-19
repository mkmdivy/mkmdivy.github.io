"""
Process Power Grid Data for Tanzania
- Extracts power lines from global GPKG
- Clips to Tanzania area
- Creates buffer zones (20km, 50km, 100km)
- Saves as GeoJSON for web display
"""

import geopandas as gpd
from shapely.geometry import box
from pathlib import Path
import json

# Paths
GRID_INPUT = r"G:/Resources/STO GIS Repository/3_Data/1_Raw_data/2_Infrastructure/Supply/Power/Grids/OSM/OSM_lines-and-cables/global_power_grid_2025-09-03.gpkg"
OUTPUT_DIR = Path(r"U:/mywork/realm/tanzania-map/data")

# Tanzania bounding box with buffer for edge effects
TANZANIA_BOUNDS = {
    "minx": 29.0,
    "miny": -11.75,
    "maxx": 40.5,
    "maxy": -0.95
}

# Buffer distances in kilometers
BUFFER_DISTANCES = [20, 50, 100]

def get_tanzania_bbox():
    """Get Tanzania bounding box as geometry"""
    return box(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
               TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])

def process_power_grid():
    """Main processing function for power grid data"""
    print("Processing power grid data...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read the GPKG file with bounding box filter
    print("Reading power grid data (this may take a while for large files)...")
    
    try:
        # Try to read with bbox filter for efficiency
        gdf = gpd.read_file(
            GRID_INPUT, 
            bbox=(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
                  TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])
        )
    except Exception as e:
        print(f"Error reading with bbox: {e}")
        print("Trying to read full file and filter...")
        gdf = gpd.read_file(GRID_INPUT)
        tanzania_box = get_tanzania_bbox()
        gdf = gdf[gdf.geometry.intersects(tanzania_box)]
    
    print(f"Found {len(gdf)} power grid features in Tanzania region")
    
    if len(gdf) == 0:
        print("Warning: No power grid features found in Tanzania region")
        # Create empty GeoJSON
        empty_geojson = {"type": "FeatureCollection", "features": []}
        with open(OUTPUT_DIR / "power_grid_tanzania.geojson", "w") as f:
            json.dump(empty_geojson, f)
        return
    
    # Ensure CRS is WGS84
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    
    # Save the original grid lines
    grid_output = OUTPUT_DIR / "power_grid_tanzania.geojson"
    gdf.to_file(grid_output, driver="GeoJSON")
    print(f"Saved power grid lines: {grid_output}")
    
    # Create buffer zones
    # Convert to a projected CRS for accurate buffering (UTM zone 36S for Tanzania)
    gdf_projected = gdf.to_crs("EPSG:32736")
    
    # Merge all lines into a single geometry for buffering
    merged_lines = gdf_projected.unary_union
    
    for distance_km in BUFFER_DISTANCES:
        distance_m = distance_km * 1000
        print(f"Creating {distance_km}km buffer zone...")
        
        # Create buffer
        buffer_geom = merged_lines.buffer(distance_m)
        
        # Create GeoDataFrame with buffer
        buffer_gdf = gpd.GeoDataFrame(
            {"distance_km": [distance_km]}, 
            geometry=[buffer_geom], 
            crs="EPSG:32736"
        )
        
        # Convert back to WGS84
        buffer_gdf = buffer_gdf.to_crs("EPSG:4326")
        
        # Clip to Tanzania bounds
        tanzania_box = get_tanzania_bbox()
        buffer_gdf["geometry"] = buffer_gdf.geometry.intersection(tanzania_box)
        
        # Save buffer zone
        buffer_output = OUTPUT_DIR / f"power_grid_buffer_{distance_km}km.geojson"
        buffer_gdf.to_file(buffer_output, driver="GeoJSON")
        print(f"Saved {distance_km}km buffer: {buffer_output}")
    
    # Save metadata
    metadata = {
        "feature_count": len(gdf),
        "buffer_distances_km": BUFFER_DISTANCES,
        "bounds": TANZANIA_BOUNDS,
        "source": "OpenStreetMap",
        "columns": list(gdf.columns)
    }
    
    with open(OUTPUT_DIR / "power_grid_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    print("Power grid processing complete!")

if __name__ == "__main__":
    process_power_grid()
