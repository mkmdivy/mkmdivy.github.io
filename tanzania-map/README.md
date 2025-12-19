# 🇹🇿 Tanzania Energy Resources Interactive Map

An interactive web map for visualizing renewable energy resources and infrastructure in Tanzania.

## Features

### 1. 💨 Wind Power Layer
- Shows wind speed at 100m height from Global Wind Atlas
- Toggle to show only **top 10% wind speed areas** (binary view)
- Adjustable opacity
- Source: `G:/Resources/STO GIS Repository/.../wind-speed_100.tif`

### 2. ☀️ Solar Power Layer
- Shows photovoltaic output potential from Global Solar Atlas
- Toggle to show only **top 10% PV output areas** (binary view)
- Adjustable opacity
- Source: `G:/Resources/STO GIS Repository/.../PVOUT.tif`

### 3. ⚡ Power Grid Layer
- Existing power lines and cables from OpenStreetMap
- Selectable buffer zones: **20km, 50km, 100km**
- Option to filter other layers by proximity to grid
- Source: `G:/Resources/STO GIS Repository/.../global_power_grid_2025-09-03.gpkg`

### 4. 🌿 Protected Areas Layer
- Protected areas with IUCN category filtering
- Filter by category: Ia, Ib, II, III, IV, V, VI, or Not Reported
- Source: `U:/mywork/realm/protected_area.gpkg`

### 5. 🌾 Agriculture Land Layer
- Cropland areas from ESA CCI Land Cover
- Classes: 10, 11, 12 (Rainfed cropland), 20 (Irrigated), 30, 40 (Mosaic)
- Adjustable opacity
- Source: `G:/Resources/STO GIS Repository/.../C3S-LC-L4-LCCS-Map-300m-P1Y-2022-v2.1.1.nc`

### 6. 🌬️ Existing Wind Turbines
- Wind turbine locations from GEM Africa database
- Click to see **sampled wind speed** at each location
- Source: `G:/Resources/STO GIS Repository/.../Wind_GEM_Africa_052025.gpkg`

### 7. ☀️ Existing Solar Installations
- Solar panel locations from GEM Africa database
- Click to see **sampled PV output** at each location
- Source: `G:/Resources/STO GIS Repository/.../Solar_GEM_Africa_052025.gpkg`

### 8. 📸 Static Map Export
- Export current map view as PNG image
- Includes title and timestamp

## Installation

### 1. Install Python Dependencies

```bash
cd U:\mywork\realm\tanzania-map
pip install -r requirements.txt
```

### 2. Process the Data

Run the master processing script to generate all data files:

```bash
cd scripts
python process_all.py
```

This will:
- Clip all raster data to Tanzania bounds
- Calculate top 10% thresholds for wind and solar
- Create binary rasters for top resource areas
- Extract and buffer power grid data
- Process protected areas with IUCN categories
- Extract agriculture land cover
- Sample wind/solar values at infrastructure locations
- Generate PNG tiles for web display

### 3. Start a Local Web Server

```bash
cd U:\mywork\realm\tanzania-map
python -m http.server 8000
```

### 4. Open the Map

Navigate to: http://localhost:8000

## Project Structure

```
tanzania-map/
├── index.html              # Main web application
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── scripts/
│   ├── process_all.py     # Master processing script
│   ├── process_wind.py    # Wind speed processor
│   ├── process_solar.py   # Solar PV output processor
│   ├── process_power_grid.py    # Power grid processor
│   ├── process_protected_areas.py  # Protected areas processor
│   ├── process_agriculture.py   # Agriculture land processor
│   ├── process_wind_turbines.py # Wind turbines processor
│   └── process_solar_panels.py  # Solar panels processor
├── data/
│   ├── wind_speed_tanzania.tif      # Clipped wind raster
│   ├── wind_top10pct_tanzania.tif   # Binary top 10% wind
│   ├── wind_stats.json              # Wind statistics
│   ├── pvout_tanzania.tif           # Clipped solar raster
│   ├── pvout_top10pct_tanzania.tif  # Binary top 10% solar
│   ├── solar_stats.json             # Solar statistics
│   ├── power_grid_tanzania.geojson  # Power grid lines
│   ├── power_grid_buffer_20km.geojson
│   ├── power_grid_buffer_50km.geojson
│   ├── power_grid_buffer_100km.geojson
│   ├── protected_areas_tanzania.geojson
│   ├── agriculture_tanzania.tif
│   ├── wind_turbines_tanzania.geojson
│   └── solar_panels_tanzania.geojson
└── tiles/
    ├── wind/{z}/{x}/{y}.png
    ├── wind-top10/{z}/{x}/{y}.png
    ├── solar/{z}/{x}/{y}.png
    ├── solar-top10/{z}/{x}/{y}.png
    └── agriculture/{z}/{x}/{y}.png
```

## Data Sources

| Layer | Source | Format |
|-------|--------|--------|
| Wind Speed | Global Wind Atlas | GeoTIFF |
| Solar PV Output | Global Solar Atlas | GeoTIFF |
| Power Grid | OpenStreetMap | GeoPackage |
| Protected Areas | WDPA | GeoPackage |
| Land Cover | ESA CCI | NetCDF |
| Wind Turbines | GEM Africa | GeoPackage |
| Solar Installations | GEM Africa | GeoPackage |

## Customization

### Changing the Mapbox Token

Edit `index.html` and replace the access token:

```javascript
mapboxgl.accessToken = 'YOUR_MAPBOX_TOKEN';
```

### Adjusting Tanzania Bounds

All scripts use the same bounding box defined in each file:

```python
TANZANIA_BOUNDS = {
    "minx": 29.0,
    "miny": -11.75,
    "maxx": 40.5,
    "maxy": -0.95
}
```

### Modifying Top Percentile Threshold

To change from top 10% to another threshold, edit the processors:

```python
# In process_wind.py and process_solar.py
threshold_90 = np.percentile(valid_data, 90)  # Change 90 to desired percentile
```

## Troubleshooting

### "No valid data found"
- Check that the source file paths are correct
- Verify the raster covers Tanzania region

### Tiles not displaying
- Ensure you're running a local web server
- Check browser console for CORS errors
- Verify tile files exist in the tiles directory

### GeoPackage read errors
- Install GDAL with GeoPackage support
- Try: `pip install gdal` or use conda

## License

This project uses data from various sources. Please refer to individual data providers for licensing terms.
