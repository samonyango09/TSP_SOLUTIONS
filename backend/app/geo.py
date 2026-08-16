"""Distance math for the route-plan corridor filter.

No geospatial library dependency (shapely/geopandas) - at the scale here
(a handful of route segments x tens of thousands of outlets) plain haversine
plus point-to-segment projection in a local equirectangular approximation is
fast enough and keeps the dependency list small.
"""

import math

EARTH_RADIUS_KM = 6371.0088


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _to_local_xy(lat: float, lon: float, origin_lat: float) -> tuple[float, float]:
    """Equirectangular projection around origin_lat, in km. Fine for the short
    segment lengths (tens to low-hundreds of km) a route leg will span."""
    x = math.radians(lon) * math.cos(math.radians(origin_lat)) * EARTH_RADIUS_KM
    y = math.radians(lat) * EARTH_RADIUS_KM
    return x, y


def distance_to_segment_km(
    point_lat: float,
    point_lon: float,
    seg_start_lat: float,
    seg_start_lon: float,
    seg_end_lat: float,
    seg_end_lon: float,
) -> float:
    """Shortest distance from a point to a single route segment (great-circle
    endpoints, projected locally so we can do simple 2D point-to-segment math)."""
    origin_lat = seg_start_lat
    px, py = _to_local_xy(point_lat, point_lon, origin_lat)
    ax, ay = _to_local_xy(seg_start_lat, seg_start_lon, origin_lat)
    bx, by = _to_local_xy(seg_end_lat, seg_end_lon, origin_lat)

    abx, aby = bx - ax, by - ay
    seg_len_sq = abx * abx + aby * aby
    if seg_len_sq == 0:
        return math.hypot(px - ax, py - ay)

    t = ((px - ax) * abx + (py - ay) * aby) / seg_len_sq
    t = max(0.0, min(1.0, t))
    closest_x, closest_y = ax + t * abx, ay + t * aby
    return math.hypot(px - closest_x, py - closest_y)


def distance_to_route_km(point_lat: float, point_lon: float, route_points: list[tuple[float, float]]) -> float:
    """Shortest distance from a point to a polyline route (list of (lat, lon)).
    Falls back gracefully for a single-point or empty route."""
    if not route_points:
        return math.inf
    if len(route_points) == 1:
        lat, lon = route_points[0]
        return haversine_km(point_lat, point_lon, lat, lon)

    best = math.inf
    for (lat1, lon1), (lat2, lon2) in zip(route_points, route_points[1:]):
        d = distance_to_segment_km(point_lat, point_lon, lat1, lon1, lat2, lon2)
        best = min(best, d)
    return best


def within_corridor(
    point_lat: float, point_lon: float, route_points: list[tuple[float, float]], buffer_km: float
) -> bool:
    return distance_to_route_km(point_lat, point_lon, route_points) <= buffer_km
