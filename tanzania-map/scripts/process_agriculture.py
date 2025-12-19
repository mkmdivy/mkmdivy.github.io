"""
Process Agriculture Land Cover Data for Tanzania
- Reads ESA CCI Land Cover NetCDF
- Filters for agriculture classes (10, 11, 12, 20, 30, 40)
- Clips to Tanzania
- Saves as GeoTIFF for web display
"""

import numpy as np
import rasterio
from rasterio.mask import mask
from rasterio.transform import from_bounds
from pathlib import Path
import json
from shapely.geometry import box

try:
    import xarray as xr
    HAS_XARRAY = True
except ImportError:
    HAS_XARRAY = False
    print("Warning: xarray not installed. Install with: pip install xarray netcdf4")

try:
    import netCDF4 as nc
    HAS_NETCDF4 = True
except ImportError:
    HAS_NETCDF4 = False

# Paths
LC_INPUT = r"G:/Resources/STO GIS Repository/3_Data/1_Raw_data/5_Planet/Land_Cover/ESA_CCI_LC/C3S-LC-L4-LCCS-Map-300m-P1Y-2022-v2.1.1.nc"
OUTPUT_DIR = Path(r"U:/mywork/realm/tanzania-map/data")

# Tanzania bounding box
TANZANIA_BOUNDS = {
    "minx": 29.0,
    "miny": -11.75,
    "maxx": 40.5,
    "maxy": -0.95
}

# Agriculture land classes from ESA CCI LC
AGRICULTURE_CLASSES = {
    10: "Cropland, rainfed",
    11: "Cropland, rainfed, herbaceous cover",
    12: "Cropland, rainfed, tree or shrub cover",
    20: "Cropland, irrigated or post-flooding",
    30: "Mosaic cropland (>50%) / natural vegetation",
    40: "Mosaic natural vegetation (>50%) / cropland"
}

def process_agriculture_land():
    """Main processing function for agriculture land cover"""
    print("Processing agriculture land cover data...")
    
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    if HAS_XARRAY:
        process_with_xarray()
    elif HAS_NETCDF4:
        process_with_netcdf4()
    else:
        print("Error: Neither xarray nor netCDF4 is installed.")
        print("Install with: pip install xarray netcdf4")
        return

def process_with_xarray():
    """Process using xarray"""
    print("Using xarray to read NetCDF...")
    
    # Open the NetCDF file
    ds = xr.open_dataset(LC_INPUT)
    
    # Get the land cover variable
    if 'lccs_class' in ds:
        lc_data = ds['lccs_class']
    else:
        print("Available variables:", list(ds.data_vars))
        # Try to find the land cover variable
        for var in ds.data_vars:
            if 'lc' in var.lower() or 'class' in var.lower():
                lc_data = ds[var]
                break
        else:
            print("Error: Could not find land cover variable")
            return
    
    print(f"Land cover data shape: {lc_data.shape}")
    print(f"Coordinates: {list(lc_data.coords)}")
    
    # Get coordinate names
    lat_name = 'lat' if 'lat' in lc_data.coords else 'latitude'
    lon_name = 'lon' if 'lon' in lc_data.coords else 'longitude'
    
    # Subset to Tanzania region
    lc_tanzania = lc_data.sel(
        **{
            lat_name: slice(TANZANIA_BOUNDS["maxy"], TANZANIA_BOUNDS["miny"]),
            lon_name: slice(TANZANIA_BOUNDS["minx"], TANZANIA_BOUNDS["maxx"])
        }
    )
    
    # If there's a time dimension, select the first/only time
    if 'time' in lc_tanzania.dims:
        lc_tanzania = lc_tanzania.isel(time=0)
    
    print(f"Tanzania subset shape: {lc_tanzania.shape}")
    
    # Get the data as numpy array
    data = lc_tanzania.values
    
    # Create binary mask for agriculture classes
    agriculture_mask = np.zeros_like(data, dtype=np.uint8)
    for class_code in AGRICULTURE_CLASSES.keys():
        agriculture_mask[data == class_code] = 1
    
    print(f"Agriculture pixels: {np.sum(agriculture_mask)} out of {agriculture_mask.size}")
    
    # Get bounds for transform
    lats = lc_tanzania[lat_name].values
    lons = lc_tanzania[lon_name].values
    
    # Calculate transform
    res_x = (lons[-1] - lons[0]) / (len(lons) - 1) if len(lons) > 1 else 0.00277778
    res_y = (lats[-1] - lats[0]) / (len(lats) - 1) if len(lats) > 1 else -0.00277778
    
    transform = rasterio.transform.from_origin(
        lons[0] - res_x/2,  # west
        lats[0] - res_y/2,  # north (lats usually descending)
        abs(res_x),
        abs(res_y)
    )
    
    # Save agriculture mask as GeoTIFF
    output_file = OUTPUT_DIR / "agriculture_tanzania.tif"
    
    with rasterio.open(
        output_file, 'w',
        driver='GTiff',
        height=agriculture_mask.shape[0],
        width=agriculture_mask.shape[1],
        count=1,
        dtype='uint8',
        crs='EPSG:4326',
        transform=transform,
        nodata=255
    ) as dst:
        dst.write(agriculture_mask, 1)
    
    print(f"Saved agriculture mask: {output_file}")
    
    # Save metadata
    metadata = {
        "agriculture_classes": AGRICULTURE_CLASSES,
        "bounds": TANZANIA_BOUNDS,
        "pixel_count_agriculture": int(np.sum(agriculture_mask)),
        "pixel_count_total": int(agriculture_mask.size),
        "percentage_agriculture": float(np.sum(agriculture_mask) / agriculture_mask.size * 100)
    }
    
    with open(OUTPUT_DIR / "agriculture_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    ds.close()
    print("Agriculture land cover processing complete!")

def process_with_netcdf4():
    """Process using netCDF4 directly"""
    print("Using netCDF4 to read NetCDF...")
    
    dataset = nc.Dataset(LC_INPUT, 'r')
    
    print("Variables:", list(dataset.variables.keys()))
    
    # Get the land cover data
    lc_var = dataset.variables['lccs_class']
    
    # Get coordinates
    lats = dataset.variables['lat'][:]
    lons = dataset.variables['lon'][:]
    
    # Find indices for Tanzania bounds
    lat_idx = np.where((lats >= TANZANIA_BOUNDS["miny"]) & (lats <= TANZANIA_BOUNDS["maxy"]))[0]
    lon_idx = np.where((lons >= TANZANIA_BOUNDS["minx"]) & (lons <= TANZANIA_BOUNDS["maxx"]))[0]
    
    # Subset data
    if len(lc_var.shape) == 3:  # time, lat, lon
        data = lc_var[0, lat_idx[0]:lat_idx[-1]+1, lon_idx[0]:lon_idx[-1]+1]
    else:  # lat, lon
        data = lc_var[lat_idx[0]:lat_idx[-1]+1, lon_idx[0]:lon_idx[-1]+1]
    
    subset_lats = lats[lat_idx]
    subset_lons = lons[lon_idx]
    
    print(f"Tanzania subset shape: {data.shape}")
    
    # Create binary mask for agriculture classes
    agriculture_mask = np.zeros_like(data, dtype=np.uint8)
    for class_code in AGRICULTURE_CLASSES.keys():
        agriculture_mask[data == class_code] = 1
    
    print(f"Agriculture pixels: {np.sum(agriculture_mask)} out of {agriculture_mask.size}")
    
    # Calculate transform
    res_x = abs(subset_lons[1] - subset_lons[0]) if len(subset_lons) > 1 else 0.00277778
    res_y = abs(subset_lats[1] - subset_lats[0]) if len(subset_lats) > 1 else 0.00277778
    
    transform = rasterio.transform.from_origin(
        float(subset_lons[0]) - res_x/2,
        float(subset_lats[0]) + res_y/2,
        res_x,
        res_y
    )
    
    # Save agriculture mask as GeoTIFF
    output_file = OUTPUT_DIR / "agriculture_tanzania.tif"
    
    with rasterio.open(
        output_file, 'w',
        driver='GTiff',
        height=agriculture_mask.shape[0],
        width=agriculture_mask.shape[1],
        count=1,
        dtype='uint8',
        crs='EPSG:4326',
        transform=transform,
        nodata=255
    ) as dst:
        dst.write(agriculture_mask, 1)
    
    print(f"Saved agriculture mask: {output_file}")
    
    # Save metadata
    metadata = {
        "agriculture_classes": {str(k): v for k, v in AGRICULTURE_CLASSES.items()},
        "bounds": TANZANIA_BOUNDS,
        "pixel_count_agriculture": int(np.sum(agriculture_mask)),
        "pixel_count_total": int(agriculture_mask.size),
        "percentage_agriculture": float(np.sum(agriculture_mask) / agriculture_mask.size * 100)
    }
    
    with open(OUTPUT_DIR / "agriculture_metadata.json", "w") as f:
        json.dump(metadata, f, indent=2)
    
    dataset.close()
    print("Agriculture land cover processing complete!")

if __name__ == "__main__":
    process_agriculture_land()
