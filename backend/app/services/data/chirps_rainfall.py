"""
CHIRPS (Climate Hazards Group InfraRed Precipitation with Station Data) integration.
Source: UC Santa Barbara — https://www.chc.ucsb.edu/data/chirps
No authentication required. Monthly GeoTIFF rasters at 0.05° resolution.

We download monthly rasters and compute country-level rainfall statistics.
Historical baseline (1981-2010) is computed from stored values for anomaly calculation.
"""

import httpx
import logging
import tempfile
import os
from datetime import date
from dataclasses import dataclass

logger = logging.getLogger(__name__)

CHIRPS_BASE = "https://data.chc.ucsb.edu/products/CHIRPS-2.0/global_monthly/tifs"


@dataclass
class CountryRainfall:
    iso_code: str
    date: date
    rainfall_mm: float
    anomaly_pct: float | None   # % difference from 1981-2010 climatology


async def download_chirps_month(year: int, month: int) -> bytes | None:
    """Download CHIRPS monthly GeoTIFF for the given year/month."""
    filename = f"chirps-v2.0.{year}.{month:02d}.tif.gz"
    url = f"{CHIRPS_BASE}/{filename}"

    async with httpx.AsyncClient(timeout=120.0, follow_redirects=True) as client:
        try:
            logger.info("Downloading CHIRPS: %s", url)
            response = await client.get(url)
            response.raise_for_status()
            return response.content
        except httpx.HTTPError as e:
            logger.warning("CHIRPS download failed for %d-%02d: %s", year, month, e)
            return None


async def get_country_rainfall_from_api(
    iso_code: str,
    lat: float,
    lon: float,
    year: int,
    month: int,
) -> CountryRainfall | None:
    """
    Get monthly rainfall for a country centroid using Open-Meteo as CHIRPS alternative.
    CHIRPS raster processing requires rasterio; this provides a lighter fallback
    using the centroid coordinate approach via the Open-Meteo archive API.
    """
    from app.services.data.open_meteo import fetch_monthly_rainfall

    start = date(year, month, 1)
    # End of month
    if month == 12:
        end = date(year + 1, 1, 1)
    else:
        end = date(year, month + 1, 1)

    import datetime
    end = end - datetime.timedelta(days=1)

    records = await fetch_monthly_rainfall(lat, lon, start, end)
    if not records:
        return None

    record = records[0]
    return CountryRainfall(
        iso_code=iso_code,
        date=start,
        rainfall_mm=record.total_precipitation_mm,
        anomaly_pct=None,   # computed separately once baseline is available
    )


def compute_anomaly(current_mm: float, baseline_values: list[float]) -> float | None:
    """Compute percentage anomaly vs historical baseline."""
    if not baseline_values:
        return None
    baseline_mean = sum(baseline_values) / len(baseline_values)
    if baseline_mean == 0:
        return None
    return ((current_mm - baseline_mean) / baseline_mean) * 100
