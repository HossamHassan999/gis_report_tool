import geopandas as gpd
import numpy as np
import pandas as pd

# ── Keywords ────────────────────────────────────────────────────────────────
AREA_KEYWORDS    = ["area","مساحة","مساحه","surface","hectare","sqkm","sq_km","shape_area","area_km"]
POP_KEYWORDS     = ["pop","population","سكان","عدد_السكان","inhabitants","residents","total_pop"]
DENSITY_KEYWORDS = ["density","كثافة","كثافه","dens","pop_den","pop_dens"]
NAME_KEYWORDS    = ["name","اسم","nam","label","title","gov","governorate","district","محافظة","مركز"]

# Common NoData sentinel values used in GIS
NODATA_SENTINELS = {-9999, -999, -99, -1, 9999, 99999, -9999.0, -999.0, -99.0}

def _dtype_str(dtype) -> str:
    if pd.api.types.is_bool_dtype(dtype):           return "bool"
    if pd.api.types.is_integer_dtype(dtype):        return "integer"
    if pd.api.types.is_float_dtype(dtype):          return "float"
    if pd.api.types.is_datetime64_any_dtype(dtype): return "datetime"
    if pd.api.types.is_string_dtype(dtype) and not pd.api.types.is_numeric_dtype(dtype):
        return "string"
    return str(dtype)

def _is_numeric(series: pd.Series) -> bool:
    try:   return pd.api.types.is_numeric_dtype(series)
    except TypeError: return False

def _strip_nodata(series: pd.Series) -> tuple[pd.Series, list]:
    """Remove likely NoData sentinels. Returns (clean_series, list_of_removed_values)."""
    clean = series.dropna()
    removed = []
    for sentinel in NODATA_SENTINELS:
        mask = clean == sentinel
        if mask.sum() > 0 and mask.sum() < len(clean) * 0.15:  # remove only if <15% of data
            removed.append(sentinel)
            clean = clean[~mask]
    return clean, removed

def _detect_role(col: str, series: pd.Series, numeric: bool) -> str:
    c = col.lower()
    if any(k in c for k in AREA_KEYWORDS):    return "area"
    if any(k in c for k in POP_KEYWORDS):     return "population"
    if any(k in c for k in DENSITY_KEYWORDS): return "density"
    if any(k in c for k in NAME_KEYWORDS):    return "name"
    if numeric:
        rng = series.max() - series.min() if not series.isnull().all() else 0
        if rng > 1_000_000: return "large_numeric"
        return "numeric"
    return "categorical"

def _percentiles(series: pd.Series) -> dict:
    clean = series.dropna()
    if len(clean) == 0: return {}
    p = np.percentile(clean, [0, 10, 25, 50, 75, 90, 100])
    return {f"p{k}": round(float(v), 4) for k, v in zip([0,10,25,50,75,90,100], p)}

def _top_n(series: pd.Series, n=15) -> dict:
    vc = series.value_counts().head(n)
    return {"labels": [str(k) for k in vc.index.tolist()], "values": vc.values.tolist()}

def _histogram(clean: pd.Series, bins=15) -> dict:
    """Build histogram on already-cleaned series (no nulls, no sentinels)."""
    n_bins = min(bins, max(2, clean.nunique()))
    mn, mx = float(clean.min()), float(clean.max())
    if mn == mx:
        return {"labels": [str(mn)], "edge_end": str(mx), "values": [int(len(clean))], "use_log": False}

    # Use log-spaced bins when range spans >3 orders of magnitude
    use_log = (mx > 0 and mn >= 0 and mx / max(mn, 1e-9) > 1000)

    if use_log:
        edges = np.logspace(np.log10(max(mn, 1e-9)), np.log10(mx), n_bins + 1)
    else:
        edges = np.linspace(mn, mx, n_bins + 1)

    counts, edges = np.histogram(clean, bins=edges)

    def _fmt(v):
        v = float(v)
        if abs(v) >= 1e9: return f"{v/1e9:.2f}B"
        if abs(v) >= 1e6: return f"{v/1e6:.2f}M"
        if abs(v) >= 1e3: return f"{v/1e3:.1f}K"
        return f"{round(v, 2)}"

    return {
        "labels":   [_fmt(e) for e in edges[:-1]],
        "edge_end": _fmt(edges[-1]),
        "values":   counts.tolist(),
        "use_log":  bool(use_log),
    }

def analyze_file(filepath: str) -> dict:
    gdf = gpd.read_file(filepath)

    if gdf.crs and gdf.crs.to_epsg() != 4326:
        gdf_4326 = gdf.to_crs(epsg=4326)
    else:
        gdf_4326 = gdf.copy()

    bounds = gdf_4326.total_bounds

    # GeoJSON for map (cap at 5000)
    sample = gdf_4326.head(5000).copy()
    for col in list(sample.columns):
        if col == sample.geometry.name: continue
        try:    sample[col] = sample[col].astype(str).where(sample[col].notna(), None)
        except: sample = sample.drop(columns=[col])
    geojson_str = sample.to_json()

    geom_counts = gdf.geom_type.value_counts().to_dict()
    fields, chart_data, numeric_fields = [], {}, []

    for col in gdf.columns:
        if col == gdf.geometry.name: continue

        series  = gdf[col]
        numeric = _is_numeric(series)
        role    = _detect_role(col, series, numeric)

        field_info = {
            "name": col, "type": _dtype_str(series.dtype), "role": role,
            "nulls": int(series.isnull().sum()),
            "null_pct": round(series.isnull().mean() * 100, 1),
            "unique": int(series.nunique()),
            "min": None, "max": None, "mean": None, "median": None, "std": None,
            "nodata_removed": [],
        }

        cd = {"role": role}

        if numeric and not series.isnull().all():
            clean_raw = series.dropna()

            # Strip NoData sentinels before stats & histogram
            clean, removed = _strip_nodata(clean_raw)
            field_info["nodata_removed"] = [float(v) for v in removed]

            field_info["min"]    = round(float(clean.min()),    4)
            field_info["max"]    = round(float(clean.max()),    4)
            field_info["mean"]   = round(float(clean.mean()),   4)
            field_info["median"] = round(float(clean.median()), 4)
            field_info["std"]    = round(float(clean.std()),    4)

            cd["histogram"]   = _histogram(clean, bins=15)
            cd["percentiles"] = _percentiles(clean)
            cd["raw_values"]  = [round(float(v), 4) for v in clean.tolist()[:500]]
            numeric_fields.append(col)
        else:
            cd["top_n"] = _top_n(series, n=15)

        chart_data[col] = cd
        fields.append(field_info)

    # ── Scatter pairs ────────────────────────────────────────────────────────
    scatter_pairs = []
    nf_lower = {c.lower(): c for c in numeric_fields}

    def find_col(kws):
        for k in kws:
            for lc, orig in nf_lower.items():
                if k in lc: return orig
        return None

    area_col    = find_col(AREA_KEYWORDS)
    pop_col     = find_col(POP_KEYWORDS)
    density_col = find_col(DENSITY_KEYWORDS)

    def make_scatter(cx, cy, label):
        if cx and cy and cx in gdf.columns and cy in gdf.columns:
            df2 = gdf[[cx, cy]].dropna()
            if len(df2) > 1:
                scatter_pairs.append({
                    "x_field": cx, "y_field": cy, "label": label,
                    "x": [round(float(v), 4) for v in df2[cx].tolist()[:500]],
                    "y": [round(float(v), 4) for v in df2[cy].tolist()[:500]],
                })

    make_scatter(area_col, pop_col,     "Area vs Population")
    make_scatter(area_col, density_col, "Area vs Density")
    make_scatter(pop_col,  density_col, "Population vs Density")

    # ── Rankings ─────────────────────────────────────────────────────────────
    rankings = []
    name_col = find_col(NAME_KEYWORDS)
    if name_col and name_col in gdf.columns:
        for num_col in [pop_col, area_col, density_col]:
            if num_col and num_col in gdf.columns:
                df3 = gdf[[name_col, num_col]].dropna().sort_values(num_col, ascending=False).head(15)
                rankings.append({
                    "name_field": name_col, "value_field": num_col,
                    "labels": df3[name_col].astype(str).tolist(),
                    "values": [round(float(v), 2) for v in df3[num_col].tolist()],
                })

    return {
        "layer_name": filepath.split("/")[-1],
        "crs": str(gdf.crs),
        "crs_epsg": gdf.crs.to_epsg() if gdf.crs else None,
        "geometry_type": gdf.geom_type.unique().tolist(),
        "geom_counts": geom_counts,
        "feature_count": len(gdf),
        "truncated": len(gdf) > 5000,
        "bbox": {
            "minx": round(float(bounds[0]), 6), "miny": round(float(bounds[1]), 6),
            "maxx": round(float(bounds[2]), 6), "maxy": round(float(bounds[3]), 6),
        },
        "fields": fields, "chart_data": chart_data,
        "scatter_pairs": scatter_pairs, "rankings": rankings,
        "geojson": geojson_str,
    }