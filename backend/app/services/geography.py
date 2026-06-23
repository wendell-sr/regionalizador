from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from zipfile import ZipFile

import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, Polygon, mapping


@dataclass
class CityGeometry:
    name: str
    geom: Polygon
    crs: str


def load_shapefile_zip(zip_path: Path, extract_dir: Path) -> gpd.GeoDataFrame:
    extract_dir.mkdir(parents=True, exist_ok=True)
    with ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_dir)
    shp_files = list(extract_dir.rglob("*.shp"))
    if not shp_files:
        raise FileNotFoundError(f"Nenhum .shp encontrado em {extract_dir}")
    return gpd.read_file(shp_files[0])


def find_city(gdf: gpd.GeoDataFrame, name: str) -> CityGeometry:
    name_col = None
    for candidate in ("NM_MUN", "NOME", "name", "municipio", "MUNICIPIO"):
        if candidate in gdf.columns:
            name_col = candidate
            break
    if name_col is None:
        raise ValueError(f"Coluna de nome do município não encontrada: {gdf.columns.tolist()}")

    match = gdf[gdf[name_col].str.contains(name, case=False, na=False)]
    if match.empty:
        raise ValueError(f"Município '{name}' não encontrado no shapefile")

    if gdf.crs is None or gdf.crs.to_epsg() != 4326:
        match = match.to_crs(4326)

    geom = match.geometry.union_all()
    return CityGeometry(name=name, geom=geom, crs="EPSG:4326")


def filter_points_within_city(
    df: pd.DataFrame, city: CityGeometry
) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    points = gpd.GeoDataFrame(
        df,
        geometry=[Point(lon, lat) for lon, lat in zip(df["lon"], df["lat"])],
        crs="EPSG:4326",
    )
    mask = points.within(city.geom)
    return df.loc[mask].reset_index(drop=True)


def reproject(df: pd.DataFrame, target_crs: str) -> pd.DataFrame:
    if df.empty:
        return df.copy()
    gdf = gpd.GeoDataFrame(
        df, geometry=[Point(lon, lat) for lon, lat in zip(df["lon"], df["lat"])], crs="EPSG:4326"
    )
    gdf = gdf.to_crs(target_crs)
    out = df.copy()
    out["x"] = gdf.geometry.x
    out["y"] = gdf.geometry.y
    return out


def geometry_to_geojson(geom) -> dict:
    return mapping(geom)
