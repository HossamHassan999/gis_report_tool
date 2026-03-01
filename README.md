# 🗺️ GIS Report Tool

A professional desktop web application for analyzing and visualizing GIS vector data. Upload any spatial file and instantly get an interactive map, smart analytics charts, field statistics, and a PDF report — all running locally with no internet required.

---

## ✨ Features

### 🗺 Interactive Map
- Dark / Satellite / OpenStreetMap basemaps
- Hover popups showing all feature attributes
- **Choropleth mode** — color any numeric field on the map with an automatic blue→purple→pink gradient
- Auto-fits to layer bounding box on load

### 📊 Smart Analytics Dashboard
Click any field in the sidebar and get instant charts based on its data type:

| Field Type | Charts Generated |
|------------|-----------------|
| `integer` / `float` | Histogram (auto log-scale for skewed data) + Box Plot + CDF curve + 6 KPI stats |
| `string` | Horizontal bar chart + Pie chart + Ranked list |
| `boolean` | True/False donut chart |

**Smart features:**
- Automatic **NoData sentinel detection** — removes values like `-99`, `-999`, `-9999` that corrupt statistics
- Auto **log-scale histogram** when data spans more than 3 orders of magnitude (e.g. area in m²)
- Visual warning badge when NoData values are removed

### 📋 Fields Table
Full statistics for every field: Min / Max / Mean / Median / Std Dev / Null % / Unique count

### ⬇️ PDF Export
Professional A4 report including:
- Cover page with KPI summary strip
- Layer overview (CRS, geometry type, bounding box)
- Data completeness quality table
- Full numeric statistics table
- Categorical field overview
- Spatial extent section
- NoData warnings section

---

## 📁 Supported File Formats

| Format | Extension | Notes |
|--------|-----------|-------|
| GeoJSON | `.geojson` / `.json` | Single file upload |
| GeoPackage | `.gpkg` | Single file upload |
| KML | `.kml` | Single file upload |
| **Shapefile** | `.zip` | ZIP must contain `.shp` + `.shx` + `.dbf` + `.prj` |

> **Shapefile tip:** Compress all 4 components into one ZIP before uploading.

---

## 🚀 Quick Start

### Option 1 — Run directly (requires Python)

```bash
# 1. Clone or download the project
cd gis_report_tool

# 2. Create a virtual environment
python -m venv env
env\Scripts\activate        # Windows
source env/bin/activate     # Mac/Linux

# 3. Install dependencies
pip install flask geopandas reportlab shapely numpy pyogrio

# 4. Run
python app.py
```

Browser opens automatically at `http://127.0.0.1:5000`

---

### Option 2 — Zero Install (distribute to any Windows PC)

Build a self-contained package on your machine once, then distribute it anywhere:

```
1. Make sure your virtual env is active and working
2. Run:  setup\build_standalone.bat
3. Wait ~10 minutes
4. Output: GIS-Report-Tool-Standalone\ folder
5. ZIP it and send to anyone — no installation needed on their end
```

Recipients just unzip and double-click `GIS_Tool.bat`.

---

## 🗂️ Project Structure

```
gis_report_tool/
│
├── app.py              # Flask server — routes & file handling
├── analyzer.py         # GIS analysis engine (geopandas + numpy)
├── report.py           # PDF generator (ReportLab)
│
├── templates/
│   ├── index.html      # Upload page (drag & drop)
│   └── report.html     # Full dashboard (map + charts + table)
│
├── uploads/            # Uploaded files (auto-created)
└── requirements.txt    # Python dependencies
```

---

## 🔧 Requirements

### Python packages
```
flask>=3.0
geopandas>=0.14
reportlab>=4.0
shapely>=2.0
numpy>=1.26
pyogrio>=0.7       # fast GDAL-based file reader
```

### Install all at once
```bash
pip install -r requirements.txt
```

### System requirements
| | Minimum | Recommended |
|-|---------|-------------|
| OS | Windows 10 / macOS 12 / Ubuntu 20 | Windows 11 / macOS 14 |
| Python | 3.10 | 3.11 |
| RAM | 4 GB | 8 GB |
| Disk | 500 MB | 1 GB |
| Browser | Chrome / Edge / Firefox | Chrome |

---

## ⚠️ Known Issues & Solutions

### GDAL DLL not found (Windows)
If you get `GDAL DLL could not be found` when running as `.exe`:

```bash
# Download the correct GDAL wheel for your Python version from:
# https://github.com/cgohlke/geospatial-wheels/releases
# Then install it:
pip install GDAL-3.4.3-cp311-cp311-win_amd64.whl
```

### Shapefile not loading
Make sure all 4 files are inside the ZIP:
```
my_layer.zip
├── my_layer.shp   ✅
├── my_layer.shx   ✅
├── my_layer.dbf   ✅
└── my_layer.prj   ✅
```

### Histogram looks wrong (one giant bar)
This usually means the field contains NoData sentinel values (`-99`, `-9999`).
The tool detects and removes these automatically — check for the yellow warning badge in the field header.

### PDF opens but has no formatting
Make sure `reportlab>=4.0` is installed:
```bash
pip install --upgrade reportlab
```

---

## 🏗️ Architecture

```
Browser (Leaflet + Chart.js)
        ↕  HTTP
Flask Server (app.py)
        ↕
    analyzer.py          →  GeoPandas reads file
        ↓                    NumPy computes stats
    chart_data{}             Histogram / percentiles / top-N
    fields[]                 Per-field metadata
    geojson (WGS84)          Reprojected for Leaflet
        ↓
    report.py            →  ReportLab builds PDF
```

**Key design decisions:**
- All processing is local — no data leaves your machine
- GeoJSON is reprojected to WGS84 (EPSG:4326) for web map compatibility
- Map display is capped at 5,000 features for performance; stats use full dataset
- NoData sentinels are stripped before statistics but flagged in the UI and PDF

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

*Built with Python · Flask · GeoPandas · Leaflet.js · Chart.js · ReportLab*
