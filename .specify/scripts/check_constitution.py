"""
Constitution guard.
Verifica que imports e padrões da constituição estão sendo seguidos.
Uso: python .specify/scripts/check_constitution.py
"""

import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parents[2]
CONSTITUTION = ROOT / ".specify" / "memory" / "constitution.md"

FORBIDDEN_IMPORTS = {
    "arcgis": "ArcGIS é proibido pela constituição. Use Nominatim + AwesomeAPI.",
    "arcpy": "ArcPy é proibido pela constituição. Use GeoPandas.",
    "mapbox": "Mapbox é proibido pela constituição. Use Leaflet + tiles OSM.",
    "googlemaps": "Google Maps é proibido pela constituição. Use Leaflet + tiles OSM.",
    "@googlemaps": "Google Maps é proibido. Use Leaflet + tiles OSM.",
}

FORBIDDEN_PACKAGE_FRAGMENTS = [
    ("mapbox-gl", "Mapbox GL é proibido pela constituição. Use Leaflet + tiles OSM."),
    ("@react-google-maps", "react-google-maps é proibido. Use react-leaflet."),
]

FORBIDDEN_TOKEN_VARS = [
    "NEXT_PUBLIC_MAPBOX_TOKEN",
    "NEXT_PUBLIC_GOOGLE_MAPS_API_KEY",
    "MAPBOX_TOKEN",
    "GOOGLE_MAPS_API_KEY",
]


def check_python_imports() -> int:
    print("Checking Python imports against constitution...")
    errors = 0
    for py in (ROOT / "backend").rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        try:
            text = py.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for forbidden, reason in FORBIDDEN_IMPORTS.items():
            pattern = rf"(^|\n)\s*(import|from)\s+{forbidden}\b"
            if re.search(pattern, text):
                print(f"  ✗ {py.relative_to(ROOT)}: {reason}")
                errors += 1
    if errors == 0:
        print("  ✓ No forbidden Python imports")
    return errors


def check_frontend_dependencies() -> int:
    print("Checking frontend dependencies against constitution...")
    errors = 0
    pkg_path = ROOT / "frontend" / "package.json"
    if not pkg_path.exists():
        print("  ℹ frontend/package.json not found (skipped)")
        return 0
    import json
    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
    for fragment, reason in FORBIDDEN_PACKAGE_FRAGMENTS:
        for name in deps:
            if fragment in name:
                print(f"  ✗ package.json: {name} — {reason}")
                errors += 1
    if errors == 0:
        print("  ✓ No forbidden frontend dependencies")
    return errors


def check_no_paid_api_tokens() -> int:
    print("Checking for paid API token env vars...")
    errors = 0
    for env_file in (ROOT / "frontend").rglob(".env*"):
        if env_file.is_file():
            text = env_file.read_text(encoding="utf-8", errors="ignore")
            for var in FORBIDDEN_TOKEN_VARS:
                if re.search(rf"^{var}\s*=", text, re.MULTILINE):
                    print(f"  ✗ {env_file.relative_to(ROOT)}: {var} é proibido")
                    errors += 1
    if errors == 0:
        print("  ✓ No paid API tokens")
    return errors


def check_crs_in_clustering() -> int:
    print("Checking CRS handling in clustering pipeline...")
    clustering = ROOT / "backend" / "app" / "services" / "clustering.py"
    geography = ROOT / "backend" / "app" / "services" / "geography.py"
    main = ROOT / "backend" / "app" / "main.py"

    if not clustering.exists():
        print(f"  ℹ clustering.py not found (skipped)")
        return 0

    errors = 0
    geo_text = geography.read_text(encoding="utf-8") if geography.exists() else ""
    main_text = main.read_text(encoding="utf-8") if main.exists() else ""

    if "EPSG:31983" in geo_text or "to_crs" in geo_text:
        print("  ✓ geography.py: handles CRS projection")
    else:
        print("  ✗ geography.py: no CRS projection (to_crs / EPSG)")
        errors += 1

    if "EPSG:31983" in main_text or "to_crs" in main_text or "reproject" in main_text:
        print("  ✓ main.py: applies projection before clustering")
    else:
        print("  ✗ main.py: no reprojection before clustering")
        errors += 1

    cluster_text = clustering.read_text(encoding="utf-8")
    if re.search(r"KMeans\(", cluster_text):
        if "x" in cluster_text and "y" in cluster_text:
            print("  ✓ clustering.py: KMeans operates on (x, y) projected coords")
        else:
            print("  ✗ clustering.py: KMeans sem (x, y) — risco de lat/lon")
            errors += 1

    return errors


def main() -> int:
    if not CONSTITUTION.exists():
        print(f"Constitution not found: {CONSTITUTION}")
        return 1
    errors = (
        check_python_imports()
        + check_frontend_dependencies()
        + check_no_paid_api_tokens()
        + check_crs_in_clustering()
    )
    if errors == 0:
        print("\n✓ Constitution is satisfied")
        return 0
    print(f"\n✗ {errors} violation(s)")
    return 1


if __name__ == "__main__":
    sys.exit(main())
