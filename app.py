import json
import os
import shutil
import threading
import webbrowser
import zipfile

from flask import Flask, jsonify, render_template, request, send_file

from analyzer import analyze_file
from report import generate_pdf

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
SUMMARY_PATH  = "report_output.json"
ALLOWED_EXTENSIONS = {"geojson", "gpkg", "kml", "json", "zip"}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_shapefile_from_zip(zip_path: str, extract_dir: str) -> str:
    """
    Extract a ZIP and return the path to the .shp file inside.
    Raises ValueError if no .shp is found.
    """
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)

    # Walk extracted tree looking for .shp
    for root, _, files in os.walk(extract_dir):
        for f in files:
            if f.lower().endswith(".shp"):
                return os.path.join(root, f)

    raise ValueError("ZIP does not contain a .shp file. Make sure to include .shp, .shx, .dbf, and .prj.")


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected"}), 400

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""

    if ext not in ALLOWED_EXTENSIONS:
        return jsonify({
            "error": f"Unsupported format '{ext}'. Allowed: GeoJSON, GPKG, KML, ZIP (for Shapefiles)"
        }), 400

    # Save uploaded file
    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    # Resolve actual filepath to analyze
    filepath = save_path

    if ext == "zip":
        extract_dir = os.path.join(UPLOAD_FOLDER, file.filename.rsplit(".", 1)[0])
        os.makedirs(extract_dir, exist_ok=True)
        try:
            filepath = extract_shapefile_from_zip(save_path, extract_dir)
        except (zipfile.BadZipFile, ValueError) as e:
            return jsonify({"error": str(e)}), 400

    try:
        summary = analyze_file(filepath)
    except Exception as e:
        return jsonify({"error": f"Failed to analyze file: {str(e)}"}), 500

    # Persist summary (without large geojson) for PDF export
    save_data = {k: v for k, v in summary.items() if k != "geojson"}
    with open(SUMMARY_PATH, "w", encoding="utf-8") as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)

    return render_template("report.html", data=summary)


@app.route("/export_pdf")
def export_pdf():
    try:
        pdf_path = generate_pdf()
        return send_file(pdf_path, as_attachment=True, download_name="gis_report.pdf")
    except FileNotFoundError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        return jsonify({"error": f"PDF generation failed: {str(e)}"}), 500


def open_browser():
    webbrowser.open("http://127.0.0.1:5000")


if __name__ == "__main__":
    threading.Timer(1.5, open_browser).start()
    app.run(debug=False)