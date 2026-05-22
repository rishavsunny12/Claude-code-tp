"""
WFP HungerMap LIVE API integration.
Docs: https://api.hungermapdata.org/
No authentication required — public API.
"""

import httpx
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

HUNGER_MAP_BASE = "https://api.hungermapdata.org/v2"

# IPC phase human-readable descriptions
IPC_DESCRIPTIONS = {
    1: "Minimal",
    2: "Stressed",
    3: "Crisis",
    4: "Emergency",
    5: "Catastrophe/Famine",
}


@dataclass
class HungerMapCountry:
    iso_code: str
    name: str
    ipc_phase: Optional[int]
    affected_pop: Optional[int]
    prevalence: Optional[float]   # % food insecure
    latitude: Optional[float]
    longitude: Optional[float]


async def fetch_all_countries() -> list[HungerMapCountry]:
    """Fetch current food security status for all countries from WFP HungerMap API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{HUNGER_MAP_BASE}/info/countrydata",
                headers={"Accept": "application/json"},
            )
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error("HungerMap API request failed: %s", e)
            return []

    countries: list[HungerMapCountry] = []
    for item in data.get("body", {}).get("countries", []):
        props = item.get("properties", {})
        food_security = props.get("foodSecurityData", {}) or {}
        pop = food_security.get("fcsGraph", {})

        # Extract IPC phase from fcs classification if available
        ipc_phase = None
        cs = food_security.get("cs", {})
        if cs:
            ipc_phase = _classify_ipc(cs)

        affected = food_security.get("fcsMalnourished")

        coords = item.get("geometry", {}).get("coordinates", [None, None])

        countries.append(HungerMapCountry(
            iso_code=props.get("iso3", ""),
            name=props.get("country", ""),
            ipc_phase=ipc_phase,
            affected_pop=int(affected) if affected else None,
            prevalence=food_security.get("fcsPrevalence"),
            latitude=coords[1] if len(coords) > 1 else None,
            longitude=coords[0] if coords else None,
        ))

    logger.info("Fetched %d countries from WFP HungerMap", len(countries))
    return [c for c in countries if c.iso_code]


async def fetch_country_detail(iso_code: str) -> Optional[HungerMapCountry]:
    """Fetch detailed food security data for a single country."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            response = await client.get(
                f"{HUNGER_MAP_BASE}/info/countrydata/{iso_code.upper()}",
                headers={"Accept": "application/json"},
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
        except httpx.HTTPError as e:
            logger.error("HungerMap country detail failed for %s: %s", iso_code, e)
            return None

    props = data.get("body", {}).get("country", {}).get("properties", {})
    food_security = props.get("foodSecurityData", {}) or {}
    cs = food_security.get("cs", {})

    return HungerMapCountry(
        iso_code=iso_code.upper(),
        name=props.get("country", ""),
        ipc_phase=_classify_ipc(cs) if cs else None,
        affected_pop=food_security.get("fcsMalnourished"),
        prevalence=food_security.get("fcsPrevalence"),
        latitude=None,
        longitude=None,
    )


def _classify_ipc(cs: dict) -> int:
    """Map WFP consumption score classification to IPC phase (1-5)."""
    very_poor = cs.get("veryPoor", 0) or 0
    poor = cs.get("poor", 0) or 0
    borderline = cs.get("borderline", 0) or 0

    crisis_pct = very_poor + poor + borderline
    if crisis_pct >= 40 or very_poor >= 20:
        return 4
    if crisis_pct >= 25 or very_poor >= 10:
        return 3
    if crisis_pct >= 10:
        return 2
    return 1
