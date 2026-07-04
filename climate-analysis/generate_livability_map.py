#!/usr/bin/env python3
"""
Global livability heat map: 65-74°F climate + low mosquitoes.

Interpolates monthly climate normals from reference stations worldwide,
then scores temperature comfort and mosquito habitat suitability.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path

import cartopy.crs as ccrs
import cartopy.feature as cfeature
import numpy as np
import plotly.graph_objects as go
from shapely.geometry import Point
from shapely.ops import unary_union

OUTPUT_DIR = Path(__file__).parent / "output"
DATA_DIR = Path(__file__).parent / "data"

TEMP_MIN_F = 65.0
TEMP_MAX_F = 74.0
TEMP_IDEAL_F = (TEMP_MIN_F + TEMP_MAX_F) / 2.0
GRID_STEP = 2.0
MAX_STATION_DIST_KM = 900.0
IDW_POWER = 3.5

_LAND_GEOM = None


def land_geometry():
    global _LAND_GEOM
    if _LAND_GEOM is None:
        land = cfeature.NaturalEarthFeature("physical", "land", "110m")
        _LAND_GEOM = unary_union(list(land.geometries()))
    return _LAND_GEOM


def is_land(lat: float, lon: float) -> bool:
    point = Point(lon, lat)
    if land_geometry().contains(point):
        return True
    # 110m Natural Earth omits many islands; keep station vicinities
    return any(haversine_km(lat, lon, s.lat, s.lon) < 60 for s in STATIONS)


@dataclass(frozen=True)
class ClimateStation:
    name: str
    lat: float
    lon: float
    # Monthly averages: Jan..Dec (°C, % RH, mm precip)
    temp_c: tuple[float, ...]
    humidity: tuple[float, ...]
    precip_mm: tuple[float, ...]


# Reference monthly normals (approx. 1991-2020) from WMO/NCEI/public climatologies
STATIONS: tuple[ClimateStation, ...] = (
    ClimateStation("San Diego, USA", 32.72, -117.16, (14.2, 14.7, 15.7, 16.7, 17.8, 19.0, 20.6, 21.0, 20.5, 18.9, 16.5, 14.5), (63, 65, 67, 68, 72, 75, 76, 77, 75, 70, 65, 63), (46, 42, 42, 18, 5, 2, 1, 3, 6, 12, 28, 42)),
    ClimateStation("Santa Barbara, USA", 34.42, -119.70, (13.0, 13.5, 14.5, 15.5, 16.5, 17.5, 18.5, 18.8, 18.5, 17.0, 15.0, 13.5), (65, 68, 70, 72, 75, 78, 80, 80, 78, 72, 68, 65), (79, 64, 48, 20, 5, 2, 1, 1, 5, 12, 35, 55)),
    ClimateStation("Los Angeles, USA", 34.05, -118.24, (14.0, 14.5, 15.5, 16.5, 18.0, 19.5, 21.5, 22.0, 21.5, 19.5, 16.5, 14.0), (55, 58, 60, 62, 65, 68, 68, 68, 65, 60, 55, 55), (79, 73, 56, 25, 8, 2, 1, 1, 5, 13, 28, 58)),
    ClimateStation("San Francisco, USA", 37.77, -122.42, (10.5, 11.5, 12.5, 13.0, 14.0, 15.0, 15.5, 16.0, 16.5, 15.5, 13.0, 10.5), (75, 75, 75, 75, 78, 80, 82, 82, 80, 78, 75, 75), (112, 97, 79, 37, 18, 4, 1, 2, 5, 31, 58, 112)),
    ClimateStation("Las Palmas, Canary Islands", 28.10, -15.43, (18.1, 18.4, 19.0, 19.6, 20.5, 21.6, 22.9, 23.6, 23.4, 22.2, 20.2, 18.5), (65, 64, 63, 62, 63, 65, 66, 67, 68, 68, 67, 66), (25, 22, 18, 12, 4, 1, 0, 1, 8, 18, 28, 30)),
    ClimateStation("Funchal, Madeira", 32.65, -16.91, (16.5, 16.5, 17.0, 17.5, 18.5, 20.0, 21.5, 22.5, 22.5, 21.5, 19.5, 17.5), (68, 68, 67, 66, 67, 70, 72, 73, 73, 72, 70, 69), (80, 60, 50, 35, 20, 8, 2, 2, 25, 55, 80, 90)),
    ClimateStation("Lisbon, Portugal", 38.72, -9.14, (11.4, 12.5, 14.2, 15.4, 17.5, 20.1, 22.1, 22.4, 21.0, 18.2, 14.5, 12.2), (78, 76, 74, 72, 70, 68, 65, 65, 70, 75, 78, 80), (100, 85, 55, 65, 55, 20, 5, 5, 30, 95, 110, 115)),
    ClimateStation("Valencia, Spain", 39.47, -0.38, (11.5, 12.8, 14.5, 16.0, 18.5, 22.0, 25.0, 25.5, 23.0, 19.0, 15.0, 12.5), (65, 63, 60, 58, 55, 52, 50, 52, 58, 65, 68, 67), (35, 30, 28, 35, 35, 15, 8, 15, 45, 65, 45, 40)),
    ClimateStation("Nice, France", 43.70, 7.27, (8.5, 9.0, 11.0, 13.0, 16.5, 20.0, 23.0, 23.5, 20.5, 16.5, 12.0, 9.5), (68, 67, 65, 65, 65, 62, 58, 60, 65, 70, 70, 69), (65, 50, 55, 65, 50, 35, 15, 20, 75, 130, 95, 70)),
    ClimateStation("Sydney, Australia", -33.87, 151.21, (22.3, 22.1, 21.0, 18.5, 16.0, 14.0, 13.0, 14.0, 16.0, 17.5, 19.0, 21.0), (65, 67, 68, 70, 72, 75, 74, 72, 68, 65, 63, 64), (102, 118, 130, 127, 100, 132, 78, 81, 69, 77, 84, 78)),
    ClimateStation("Perth, Australia", -31.95, 115.86, (24.5, 24.5, 22.5, 20.0, 17.5, 15.5, 14.5, 15.0, 16.0, 17.5, 19.5, 22.0), (50, 52, 55, 58, 62, 68, 70, 68, 62, 55, 50, 48), (18, 15, 20, 45, 90, 130, 170, 135, 85, 52, 28, 15)),
    ClimateStation("Auckland, New Zealand", -36.85, 174.76, (19.5, 19.8, 18.8, 16.8, 14.8, 12.8, 11.8, 12.5, 13.5, 14.8, 16.2, 18.2), (78, 78, 77, 78, 80, 82, 83, 82, 80, 78, 77, 77), (74, 65, 86, 93, 100, 117, 126, 112, 92, 80, 86, 91)),
    ClimateStation("Wellington, New Zealand", -41.29, 174.78, (16.5, 16.8, 15.8, 14.0, 12.0, 10.5, 9.5, 10.0, 11.0, 12.0, 13.5, 15.5), (78, 78, 78, 80, 82, 84, 84, 83, 80, 78, 77, 77), (79, 65, 82, 82, 100, 113, 98, 88, 82, 84, 76, 86)),
    ClimateStation("Medellín, Colombia", 6.25, -75.56, (21.8, 22.0, 22.2, 22.0, 21.8, 21.6, 21.8, 21.8, 21.4, 21.0, 21.0, 21.4), (72, 72, 73, 75, 76, 76, 74, 73, 75, 76, 76, 74), (55, 68, 98, 145, 165, 120, 95, 105, 145, 165, 120, 80)),
    ClimateStation("Quito, Ecuador", -0.18, -78.47, (14.0, 14.0, 14.2, 14.5, 14.5, 14.5, 14.8, 15.0, 15.0, 14.8, 14.5, 14.0), (75, 77, 78, 78, 77, 75, 74, 73, 74, 75, 76, 76), (85, 110, 145, 175, 130, 55, 30, 35, 75, 110, 95, 80)),
    ClimateStation("Cuenca, Ecuador", -2.90, -79.00, (15.0, 15.0, 15.2, 15.0, 14.8, 14.5, 14.5, 14.8, 15.0, 15.2, 15.0, 15.0), (78, 80, 82, 82, 80, 78, 76, 75, 76, 78, 80, 79), (55, 75, 90, 65, 35, 18, 12, 15, 25, 45, 55, 60)),
    ClimateStation("Pretoria, South Africa", -25.75, 28.19, (22.0, 21.5, 20.5, 17.5, 14.5, 11.5, 11.0, 13.5, 17.0, 19.5, 20.5, 21.5), (55, 58, 60, 62, 58, 52, 48, 45, 48, 52, 55, 55), (135, 80, 75, 55, 15, 8, 5, 5, 15, 75, 110, 120)),
    ClimateStation("Cape Town, South Africa", -33.92, 18.42, (21.0, 21.5, 20.0, 17.5, 15.0, 13.5, 12.5, 13.0, 14.5, 16.5, 18.5, 20.0), (68, 68, 70, 72, 75, 78, 78, 76, 72, 70, 68, 68), (15, 18, 22, 52, 82, 93, 82, 72, 58, 42, 22, 18)),
    ClimateStation("Viña del Mar, Chile", -33.02, -71.55, (17.0, 17.5, 16.5, 14.5, 12.5, 11.0, 10.5, 11.0, 12.0, 13.5, 14.5, 16.0), (72, 74, 76, 78, 80, 82, 82, 80, 78, 76, 74, 72), (1, 2, 5, 20, 55, 85, 80, 55, 30, 15, 8, 3)),
    ClimateStation("Santiago, Chile", -33.45, -70.67, (20.0, 19.0, 17.5, 14.5, 11.5, 9.0, 8.5, 9.5, 11.5, 14.0, 16.5, 18.5), (55, 58, 62, 65, 68, 70, 68, 65, 60, 55, 52, 52), (1, 2, 8, 18, 42, 68, 58, 38, 22, 12, 8, 3)),
    ClimateStation("Honolulu, USA", 21.31, -157.86, (23.0, 23.0, 23.5, 24.0, 24.8, 25.5, 26.0, 26.5, 26.5, 26.0, 25.0, 23.5), (73, 72, 71, 70, 68, 65, 64, 64, 66, 68, 70, 72), (58, 42, 52, 28, 38, 12, 18, 22, 28, 58, 68, 72)),
    ClimateStation("Miami, USA", 25.76, -80.19, (20.5, 21.0, 22.5, 24.5, 26.5, 28.0, 28.5, 28.5, 28.0, 26.5, 24.0, 21.5), (72, 72, 70, 68, 70, 75, 75, 76, 77, 76, 75, 73), (52, 58, 68, 82, 158, 238, 165, 178, 198, 144, 72, 48)),
    ClimateStation("Phoenix, USA", 33.45, -112.07, (12.5, 14.5, 17.5, 21.0, 25.5, 30.0, 33.5, 32.5, 29.5, 23.5, 17.0, 12.5), (45, 40, 32, 22, 18, 15, 22, 28, 28, 30, 38, 45), (22, 22, 18, 8, 5, 2, 22, 28, 22, 18, 18, 28)),
    ClimateStation("Seattle, USA", 47.61, -122.33, (5.5, 6.5, 8.0, 10.0, 13.5, 16.0, 18.5, 18.5, 16.5, 12.0, 8.0, 5.5), (78, 78, 76, 74, 72, 70, 68, 68, 72, 78, 80, 80), (148, 108, 98, 68, 52, 38, 18, 22, 42, 82, 148, 138)),
    ClimateStation("London, UK", 51.51, -0.13, (5.5, 5.5, 7.5, 9.5, 12.5, 15.5, 17.5, 17.5, 15.0, 12.0, 8.5, 6.5), (82, 80, 76, 72, 70, 70, 70, 72, 75, 80, 84, 84), (55, 42, 42, 42, 48, 45, 48, 52, 48, 58, 58, 58)),
    ClimateStation("Paris, France", 48.86, 2.35, (4.5, 5.5, 8.0, 10.5, 14.0, 17.0, 19.5, 19.5, 16.5, 12.5, 8.0, 5.5), (85, 82, 78, 74, 72, 70, 68, 70, 75, 82, 88, 88), (52, 42, 48, 52, 62, 52, 58, 52, 52, 62, 52, 58)),
    ClimateStation("Rome, Italy", 41.90, 12.50, (8.0, 8.5, 10.5, 13.0, 16.5, 20.0, 23.0, 23.5, 20.5, 16.5, 12.0, 9.0), (75, 72, 70, 68, 65, 62, 58, 60, 65, 70, 75, 77), (70, 58, 52, 52, 38, 22, 12, 18, 62, 98, 105, 82)),
    ClimateStation("Athens, Greece", 37.98, 23.73, (10.0, 10.5, 12.5, 15.5, 19.5, 24.0, 27.0, 27.0, 23.5, 19.0, 15.0, 11.5), (68, 65, 62, 58, 52, 45, 42, 45, 52, 60, 68, 70), (58, 48, 42, 28, 22, 8, 5, 5, 15, 52, 58, 68)),
    ClimateStation("Marrakech, Morocco", 31.63, -8.00, (12.5, 14.0, 16.0, 18.0, 21.0, 24.5, 28.0, 28.0, 25.0, 21.0, 16.5, 13.5), (58, 55, 52, 50, 48, 45, 42, 45, 50, 55, 58, 60), (28, 32, 28, 28, 18, 5, 2, 2, 8, 22, 28, 32)),
    ClimateStation("Nairobi, Kenya", -1.29, 36.82, (18.5, 19.5, 20.0, 19.5, 18.5, 17.5, 16.5, 17.0, 18.5, 19.5, 18.5, 18.0), (65, 62, 65, 70, 72, 72, 70, 68, 68, 70, 72, 68), (48, 42, 68, 145, 108, 42, 18, 28, 32, 58, 108, 72)),
    ClimateStation("Bangkok, Thailand", 13.76, 100.50, (27.0, 28.5, 29.5, 30.5, 30.0, 29.5, 29.0, 29.0, 28.5, 28.0, 27.5, 26.5), (68, 65, 68, 72, 75, 78, 78, 78, 80, 78, 75, 70), (12, 18, 32, 62, 178, 158, 168, 188, 298, 228, 48, 12)),
    ClimateStation("Singapore", 1.35, 103.82, (26.5, 27.0, 27.5, 28.0, 28.5, 28.5, 28.0, 28.0, 28.0, 27.5, 27.0, 26.5), (82, 80, 82, 84, 84, 82, 82, 82, 82, 83, 84, 84), (198, 108, 165, 178, 168, 152, 158, 148, 158, 168, 258, 318)),
    ClimateStation("Tokyo, Japan", 35.68, 139.69, (5.5, 6.0, 9.0, 14.0, 18.5, 21.5, 25.0, 26.5, 23.0, 17.5, 12.0, 7.5), (52, 52, 55, 60, 65, 75, 78, 75, 72, 68, 62, 55), (52, 58, 98, 118, 132, 168, 128, 148, 208, 198, 88, 48)),
    ClimateStation("Seoul, South Korea", 37.57, 126.98, (-2.0, 0.5, 6.0, 12.5, 18.0, 22.5, 25.5, 26.0, 21.5, 14.5, 7.0, 0.0), (58, 55, 55, 58, 62, 68, 78, 75, 68, 62, 58, 58), (22, 28, 42, 82, 82, 138, 318, 278, 138, 52, 52, 22)),
    ClimateStation("Reykjavik, Iceland", 64.15, -21.94, (1.0, 1.5, 2.5, 4.5, 7.5, 10.5, 12.5, 11.5, 9.0, 5.5, 3.0, 1.5), (78, 78, 78, 76, 74, 76, 78, 80, 80, 80, 78, 78), (88, 72, 82, 58, 48, 52, 52, 62, 68, 82, 78, 88)),
    ClimateStation("Bogotá, Colombia", 4.71, -74.07, (13.5, 14.0, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.5, 14.0), (75, 76, 77, 78, 77, 75, 74, 73, 74, 76, 77, 76), (58, 68, 95, 125, 118, 58, 38, 48, 68, 118, 105, 72)),
    ClimateStation("Tenerife, Spain", 28.29, -16.63, (17.5, 17.8, 18.5, 19.0, 20.0, 21.5, 23.0, 24.0, 24.0, 22.5, 20.5, 18.5), (62, 61, 60, 59, 60, 62, 63, 64, 65, 65, 64, 63), (28, 25, 20, 15, 8, 2, 0, 1, 8, 20, 30, 32)),
    ClimateStation("Malaga, Spain", 36.72, -4.42, (12.5, 13.5, 15.0, 16.5, 19.0, 22.5, 25.0, 25.5, 23.5, 19.5, 16.0, 13.5), (68, 65, 62, 60, 58, 55, 52, 55, 60, 65, 68, 70), (58, 48, 42, 38, 25, 8, 2, 5, 22, 58, 68, 72)),
    ClimateStation("Adelaide, Australia", -34.93, 138.60, (22.5, 22.5, 20.5, 18.0, 15.5, 13.5, 12.5, 13.5, 15.0, 16.5, 18.5, 20.5), (55, 55, 58, 62, 68, 72, 72, 68, 62, 58, 55, 52), (20, 18, 28, 42, 58, 78, 68, 58, 42, 38, 28, 22)),
    ClimateStation("La Paz, Bolivia", -16.50, -68.15, (9.5, 10.0, 10.5, 10.5, 10.0, 9.0, 8.5, 9.5, 11.0, 11.5, 11.0, 10.0), (55, 58, 55, 48, 42, 40, 38, 38, 42, 45, 48, 52), (108, 98, 58, 28, 12, 8, 8, 12, 22, 28, 42, 88)),
    ClimateStation("Oaxaca, Mexico", 17.07, -96.72, (18.0, 19.5, 21.0, 22.5, 22.5, 21.0, 20.0, 20.0, 19.5, 19.0, 18.5, 17.5), (58, 55, 52, 48, 52, 58, 62, 62, 62, 60, 58, 58), (5, 5, 8, 18, 58, 138, 118, 98, 98, 48, 12, 5)),
    ClimateStation("Mexico City, Mexico", 19.43, -99.13, (13.5, 15.0, 17.0, 18.5, 18.5, 17.5, 16.5, 16.5, 16.5, 16.0, 15.0, 13.5), (55, 52, 48, 45, 48, 55, 58, 58, 58, 55, 52, 55), (8, 8, 12, 28, 58, 138, 158, 138, 108, 48, 12, 8)),
    ClimateStation("Dubai, UAE", 25.20, 55.27, (19.0, 20.0, 23.0, 27.0, 31.5, 33.5, 35.5, 35.5, 32.5, 29.0, 24.5, 20.5), (58, 55, 52, 45, 42, 45, 48, 52, 55, 58, 60, 58), (12, 18, 22, 8, 2, 0, 0, 0, 0, 2, 5, 12)),
    ClimateStation("Mumbai, India", 19.08, 72.88, (24.0, 24.5, 26.5, 28.5, 30.0, 28.5, 27.0, 27.0, 27.0, 28.5, 27.5, 25.5), (68, 65, 65, 68, 72, 78, 82, 82, 80, 72, 65, 65), (1, 1, 1, 1, 18, 508, 612, 368, 312, 48, 12, 5)),
    ClimateStation("Dar es Salaam, Tanzania", -6.79, 39.24, (27.5, 28.0, 27.5, 26.5, 25.5, 24.0, 23.5, 24.0, 24.5, 25.5, 26.5, 27.0), (78, 76, 78, 80, 78, 76, 74, 72, 72, 74, 76, 78), (58, 48, 148, 228, 178, 48, 28, 28, 28, 68, 128, 98)),
    ClimateStation("Antananarivo, Madagascar", -18.88, 47.51, (20.5, 20.5, 20.0, 19.0, 17.0, 15.0, 14.5, 15.5, 17.5, 19.0, 20.0, 20.5), (78, 78, 77, 77, 76, 75, 74, 73, 74, 75, 76, 77), (278, 198, 148, 58, 28, 28, 28, 18, 18, 38, 98, 178)),
    ClimateStation("Faro, Portugal", 37.02, -7.93, (12.0, 13.0, 15.0, 16.0, 18.5, 21.5, 24.0, 24.5, 22.5, 19.0, 15.5, 13.0), (75, 73, 70, 68, 65, 62, 58, 60, 65, 70, 74, 76), (58, 48, 38, 42, 28, 8, 2, 2, 22, 58, 68, 72)),
    ClimateStation("Cascais, Portugal", 38.70, -9.42, (11.5, 12.5, 14.0, 15.0, 17.0, 19.5, 21.5, 22.0, 20.5, 18.0, 14.5, 12.5), (76, 74, 72, 70, 68, 66, 64, 65, 68, 72, 76, 77), (95, 85, 55, 58, 48, 18, 5, 5, 28, 95, 105, 110)),
)


def c_to_f(c: float | np.ndarray) -> float | np.ndarray:
    return c * 9.0 / 5.0 + 32.0


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlamb = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlamb / 2) ** 2
    return 2 * r * math.asin(min(1.0, math.sqrt(a)))


def interpolate_climate(lat: float, lon: float) -> dict[str, np.ndarray] | None:
    weights: list[float] = []
    temp_acc = np.zeros(12)
    hum_acc = np.zeros(12)
    prec_acc = np.zeros(12)

    for station in STATIONS:
        dist = max(1.0, haversine_km(lat, lon, station.lat, station.lon))
        if dist > MAX_STATION_DIST_KM:
            continue
        weight = ((1.0 - dist / MAX_STATION_DIST_KM) ** 2) / (dist ** IDW_POWER)
        weights.append(weight)
        temp_acc += weight * np.array(station.temp_c)
        hum_acc += weight * np.array(station.humidity)
        prec_acc += weight * np.array(station.precip_mm)

    if not weights:
        return None

    total = sum(weights)
    return {
        "monthly_temp_c": temp_acc / total,
        "monthly_humidity": hum_acc / total,
        "monthly_precip_mm": prec_acc / total,
    }


def temperature_comfort_score(monthly_temp_c: np.ndarray) -> float:
    temps_f = c_to_f(monthly_temp_c)
    in_range = np.sum((temps_f >= TEMP_MIN_F) & (temps_f <= TEMP_MAX_F))
    proximity = np.exp(-0.5 * ((temps_f - TEMP_IDEAL_F) / 4.0) ** 2)
    proximity *= (temps_f >= TEMP_MIN_F) & (temps_f <= TEMP_MAX_F)
    return 0.7 * (in_range / 12.0) + 0.3 * float(np.mean(proximity))


def mosquito_suitability(
    monthly_temp_c: np.ndarray,
    monthly_humidity: np.ndarray,
    monthly_precip_mm: np.ndarray,
) -> float:
    suitabilities: list[float] = []
    for temp_c, rh, precip in zip(monthly_temp_c, monthly_humidity, monthly_precip_mm):
        temp_factor = math.exp(-((temp_c - 27.0) ** 2) / (2.0 * 7.0**2))
        if temp_c < 5.0:
            temp_factor *= 0.05
        elif temp_c < 12.0:
            temp_factor *= 0.25
        humidity_factor = max(0.0, min(1.0, (rh - 40.0) / 45.0))
        precip_factor = min(1.0, precip / 120.0)
        suitabilities.append(temp_factor * (0.45 * humidity_factor + 0.55 * precip_factor))
    if not suitabilities:
        return 0.5
    return 0.6 * max(suitabilities) + 0.4 * (sum(suitabilities) / len(suitabilities))


def score_point(lat: float, lon: float) -> dict | None:
    if not is_land(lat, lon):
        return None
    climate = interpolate_climate(lat, lon)
    if climate is None:
        return None
    temp_score = temperature_comfort_score(climate["monthly_temp_c"])
    mosquito = mosquito_suitability(
        climate["monthly_temp_c"],
        climate["monthly_humidity"],
        climate["monthly_precip_mm"],
    )
    return {
        "latitude": lat,
        "longitude": lon,
        "livability": round(temp_score * max(0.0, 1.0 - mosquito), 4),
        "temp_score": round(temp_score, 4),
        "mosquito_suitability": round(mosquito, 4),
        "avg_temp_f": round(float(np.mean(c_to_f(climate["monthly_temp_c"]))), 1),
    }


def build_grid() -> tuple[np.ndarray, np.ndarray]:
    lats = np.arange(-60, 61, GRID_STEP, dtype=np.float64)
    lons = np.arange(-180, 180, GRID_STEP, dtype=np.float64)
    return lats, lons


def collect_grid_data() -> dict:
    cache_path = DATA_DIR / "grid_scores.json"
    if cache_path.exists():
        return json.loads(cache_path.read_text())

    lats, lons = build_grid()
    lat_grid, lon_grid = np.meshgrid(lats, lons, indexing="ij")
    print(f"Scoring {lat_grid.size}-point global grid ({GRID_STEP}°)...")
    points = [
        scored
        for lat, lon in zip(lat_grid.ravel(), lon_grid.ravel())
        if (scored := score_point(float(lat), float(lon))) is not None
    ]

    payload = {
        "metadata": {
            "temp_range_f": [TEMP_MIN_F, TEMP_MAX_F],
            "grid_step_deg": GRID_STEP,
            "source": f"IDW interpolation from {len(STATIONS)} reference climate stations",
        },
        "points": points,
    }
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(json.dumps(payload, indent=2))
    return payload


def nearest_station_name(lat: float, lon: float) -> str:
    nearest = min(STATIONS, key=lambda s: haversine_km(lat, lon, s.lat, s.lon))
    dist = haversine_km(lat, lon, nearest.lat, nearest.lon)
    return f"~{nearest.name} ({dist:.0f} km)"


def top_locations(points: list[dict], n: int = 25) -> list[dict]:
    ranked = sorted(points, key=lambda p: p["livability"], reverse=True)[:n]
    for row in ranked:
        row["nearest_reference"] = nearest_station_name(row["latitude"], row["longitude"])
    return ranked


def create_globe_heatmap(points: list[dict], output_html: Path) -> None:
    scores = [p["livability"] for p in points]
    hover = [
        (
            f"Lat {p['latitude']:.1f}, Lon {p['longitude']:.1f}<br>"
            f"Livability: {p['livability']:.2f}<br>"
            f"Temp score (65-74°F): {p['temp_score']:.2f}<br>"
            f"Mosquito burden: {p['mosquito_suitability']:.2f}<br>"
            f"Avg monthly temp: {p['avg_temp_f']:.1f}°F"
        )
        for p in points
    ]

    fig = go.Figure(
        data=[
            go.Scattergeo(
                lon=[p["longitude"] for p in points],
                lat=[p["latitude"] for p in points],
                mode="markers",
                marker={
                    "size": 5,
                    "color": scores,
                    "colorscale": [
                        [0.0, "#2c003e"],
                        [0.15, "#450a5c"],
                        [0.3, "#1e4d6b"],
                        [0.45, "#2d7a4f"],
                        [0.6, "#5cb85c"],
                        [0.75, "#c9e265"],
                        [0.9, "#ffe566"],
                        [1.0, "#ff6b00"],
                    ],
                    "cmin": 0,
                    "cmax": 0.55,
                    "colorbar": {
                        "title": "Livability score<br>(65-74°F × low mosquitoes)",
                        "tickformat": ".2f",
                        "len": 0.75,
                    },
                    "opacity": 0.88,
                    "line": {"width": 0},
                },
                text=hover,
                hoverinfo="text",
            )
        ]
    )

    fig.update_layout(
        title={
            "text": (
                "Optimal Places to Live: 65–74°F Climate + Low Mosquitoes<br>"
                f"<sup>{GRID_STEP}° global grid · purple = poor · yellow/orange = best</sup>"
            ),
            "x": 0.5,
            "xanchor": "center",
        },
        geo={
            "projection_type": "orthographic",
            "projection_rotation": {"lon": -15, "lat": 25},
            "showland": True,
            "landcolor": "#1a1a2e",
            "showocean": True,
            "oceancolor": "#0f0f23",
            "showcountries": True,
            "countrycolor": "#444466",
            "coastlinecolor": "#666688",
            "bgcolor": "#0a0a18",
        },
        paper_bgcolor="#0a0a18",
        plot_bgcolor="#0a0a18",
        font={"color": "#e8e8f0"},
        height=820,
        margin={"l": 0, "r": 0, "t": 90, "b": 0},
    )
    fig.write_html(str(output_html), include_plotlyjs="cdn")
    print(f"Saved interactive globe map to {output_html}")


def create_flat_heatmap(points: list[dict], output_png: Path) -> None:
    fig = go.Figure(
        data=[
            go.Scattergeo(
                lon=[p["longitude"] for p in points],
                lat=[p["latitude"] for p in points],
                mode="markers",
                marker={
                    "size": 3,
                    "color": [p["livability"] for p in points],
                    "colorscale": [
                        [0.0, "#2c003e"],
                        [0.2, "#1e4d6b"],
                        [0.4, "#2d7a4f"],
                        [0.6, "#5cb85c"],
                        [0.8, "#ffe566"],
                        [1.0, "#ff6b00"],
                    ],
                    "cmin": 0,
                    "cmax": 0.55,
                    "colorbar": {"title": "Livability"},
                    "opacity": 0.92,
                },
            )
        ]
    )
    fig.update_layout(
        title="Global Livability Heat Map (65–74°F + Low Mosquitoes)",
        geo={"projection_type": "equirectangular", "showland": True, "landcolor": "#222233"},
        height=500,
    )
    fig.write_image(str(output_png), width=1800, height=900, scale=2)
    print(f"Saved static map to {output_png}")


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = collect_grid_data()
    points = payload["points"]
    best = top_locations(points, 40)

    create_globe_heatmap(points, OUTPUT_DIR / "livability_globe.html")
    try:
        create_flat_heatmap(points, OUTPUT_DIR / "livability_map.png")
    except Exception as exc:
        print(f"Static PNG export skipped: {exc}")

    print("\n=== TOP 20 PLACES TO LIVE (65-74°F + low mosquitoes) ===")
    for rank, p in enumerate(best[:20], 1):
        print(
            f"{rank:2d}. {p['nearest_reference']}\n"
            f"    coords ({p['latitude']:.1f}, {p['longitude']:.1f})  "
            f"score={p['livability']:.3f}  temp={p['temp_score']:.2f}  "
            f"mosquitoes={p['mosquito_suitability']:.2f}  avg={p['avg_temp_f']:.0f}°F"
        )

    (OUTPUT_DIR / "top_locations.json").write_text(json.dumps(best, indent=2))


if __name__ == "__main__":
    main()
