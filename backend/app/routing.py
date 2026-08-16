"""Route geometry for the route-plan corridor: try the free OSRM demo server,
fall back to a straight line between the two points if it's unavailable.

The OSRM demo server (router.project-osrm.org) is a free, no-key public
instance OSRM itself asks users not to hammer in production - fine for an
internal sales-team tool's occasional route-plan lookups, but flagged here and
in docs/04-deployment.md as the first thing to swap for a self-hosted OSRM (or
a paid routing API) if usage grows.
"""

import logging

import httpx

from app.config import get_settings

logger = logging.getLogger(__name__)


def get_route_points(from_lat: float, from_lon: float, to_lat: float, to_lon: float) -> list[tuple[float, float]]:
    settings = get_settings()
    url = f"{settings.osrm_base_url}/route/v1/driving/{from_lon},{from_lat};{to_lon},{to_lat}"
    try:
        resp = httpx.get(url, params={"overview": "full", "geometries": "geojson"}, timeout=5.0)
        resp.raise_for_status()
        data = resp.json()
        coords = data["routes"][0]["geometry"]["coordinates"]  # [[lon, lat], ...]
        return [(lat, lon) for lon, lat in coords]
    except Exception as exc:  # noqa: BLE001
        logger.warning("OSRM routing failed (%s) - falling back to straight line.", exc)
        return [(from_lat, from_lon), (to_lat, to_lon)]
