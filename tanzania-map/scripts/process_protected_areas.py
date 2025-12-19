"""
Process Protected Areas Data for Tanzania
- Reads protected areas from GPKG
- Preserves IUCN_CAT field for filtering
- Saves as GeoJSON for web display
"""

import geopandas as gpd
from shapely.geometry import box
from pathlib import Path
import json

# Paths
PROTECTED_INPUT = r"U:/mywork/realm/protected_area.gpkg"
OUTPUT_DIR = Path(r"U:/mywork/realm/tanzania-map/data")

# Tanzania bounding box
TANZANIA_BOUNDS = {
    "minx": 29.0,
    "miny": -11.75,
    "maxx": 40.5,
    "maxy": -0.95
}

def get_tanzania_bbox():
    """Get Tanzania bounding box as geometry"""
    return box(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
               TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])

def process_protected_areas():
    """Main processing function for protected areas"""
    print("Processing protected areas data...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Read the GPKG file
    print("Reading protected areas data...")
    
    try:
        # Try to read with bbox filter
        gdf = gpd.read_file(
            PROTECTED_INPUT,
            bbox=(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["miny"], 
                  TANZANIA_BOUNDS["maxx"], TANZANIA_BOUNDS["maxy"])
        )
    except Exception as e:
        print(f"Error reading with bbox: {e}")
        print("Reading full file and filtering...")
        gdf = gpd.read_file(PROTECTED_INPUT)
        tanzania_box = get_tanzania_bbox()
        gdf = gdf[gdf.geometry.intersects(tanzania_box)]
    
    print(f"Found {len(gdf)} protected areas in Tanzania region")
    
    if len(gdf) == 0:
        print("Warning: No protected areas found in Tanzania region")
        empty_geojson = {"type": "FeatureCollection", "features": []}
        with open(OUTPUT_DIR / "protected_areas_tanzania.geojson", "w") as f:
            json.dump(empty_geojson, f)
        return
    
    # Ensure CRS is WGS84
    if gdf.crs is None:
        gdf = gdf.set_crs("EPSG:4326")
    elif gdf.crs.to_epsg() != 4326:
        gdf = gdf.to_crs("EPSG:4326")
    
    # Check for IUCN_CAT column
    iucn_column = None
    for col in gdf.columns:
        if 'iucn' in col.lower():
            iucn_column = col
            break
    
    if iucn_column:
        print(f"Found IUCN category column: {iucn_column}")
        # Get unique categories
        categories = gdf[iucn_column].unique().tolist()
        print(f"IUCN Categories found: {categories}")
        
        # Rename to standard name if needed
        if iucn_column != 'IUCN_CAT':
            gdf = gdf.rename(columns={iucn_column: 'IUCN_CAT'})
    else:
        print("Warning: IUCN_CAT column not found. Available columns:", list(gdf.columns))
        categories = []
    
    # Select relevant columns (keep geometry and IUCN category)
    columns_to_keep = ['geometry']
    if 'IUCN_CAT' in gdf.columns:
        columns_to_keep.append('IUCN_CAT')
    if 'NAME' in gdf.columns:
        columns_to_keep.append('NAME')
    elif 'name' in gdf.columns:
        columns_to_keep.append('name')
    
    # Add any other useful columns
    for col in ['DESIG', 'DESIG_ENG', 'STATUS', 'GOV_TYPE', 'OWN_TYPE', 'MARINE']:
        if col in gdf.columns:
            columns_to_keep.append(col)
    
    gdf_export = gdf[[c for c in columns_to_keep if c in gdf.columns]].copy()
    
    # Save as GeoJSON
    output_file = OUTPUT_DIR / "protected_areas_tanzania.geojson"
    gdf_export.to_file(output_file, driver="GeoJSON")
    print(f"Saved protected areas: {output_file}")
    
    # Save metadata including IUCN categories for the web app
    metadata = {
        "feature_count": len(gdf),
        "iucn_categories": [str(c) for c in categories if c is not None],
        "bounds": TANZANIA_BOUNDS,
        "columns": list(gdf_export.columns)
    }
    
    with open(OUTPUT_DIR / "protected_areas_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Saved metadata with {len(categories)} IUCN categories")
    
    print("Protected areas processing complete!")

if __name__ == "__main__":
    process_protected_areas()
