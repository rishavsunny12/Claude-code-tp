"""
Alert generation engine.
Detects countries where food security is deteriorating rapidly and generates
actionable alerts for NGO/government responders.
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone

logger = logging.getLogger(__name__)


@dataclass
class GeneratedAlert:
    iso_code: str
    severity: str       # watch | warning | emergency
    message: str


SEVERITY_THRESHOLDS = {
    "watch":     (0.05, 0.35),    # (min_delta, min_score) — score rising but not critical
    "warning":   (0.08, 0.50),
    "emergency": (0.10, 0.65),
}


def evaluate_alerts(
    iso_code: str,
    country_name: str,
    current_score: float,
    prev_score: float | None,
    ipc_phase: int | None,
    ndvi_anomaly: float | None,
    rainfall_anomaly_pct: float | None,
    affected_pop: int | None,
) -> list[GeneratedAlert]:
    """
    Evaluate whether a country warrants a new alert based on score change and severity.
    Returns a list of alerts (may be empty).
    """
    alerts = []

    delta = (current_score - prev_score) if prev_score is not None else 0.0

    for severity, (min_delta, min_score) in SEVERITY_THRESHOLDS.items():
        if delta >= min_delta and current_score >= min_score:
            message = _build_alert_message(
                country_name, severity, current_score, delta,
                ipc_phase, ndvi_anomaly, rainfall_anomaly_pct, affected_pop,
            )
            alerts.append(GeneratedAlert(iso_code=iso_code, severity=severity, message=message))
            break   # only generate the highest applicable severity

    # Also alert if IPC phase 4+ even without delta
    if ipc_phase and ipc_phase >= 4 and not alerts:
        alerts.append(GeneratedAlert(
            iso_code=iso_code,
            severity="emergency",
            message=_build_phase_alert(country_name, ipc_phase, affected_pop),
        ))

    return alerts


def _build_alert_message(
    country_name: str,
    severity: str,
    score: float,
    delta: float,
    ipc_phase: int | None,
    ndvi_anomaly: float | None,
    rainfall_anomaly_pct: float | None,
    affected_pop: int | None,
) -> str:
    parts = [f"{country_name}: food security {severity.upper()}"]

    if delta > 0:
        parts.append(f"risk score increased by {delta:.0%}")

    indicators = []
    if ndvi_anomaly is not None and ndvi_anomaly < -1.0:
        indicators.append(f"vegetation {abs(ndvi_anomaly):.1f}σ below normal")
    if rainfall_anomaly_pct is not None and rainfall_anomaly_pct < -20:
        indicators.append(f"rainfall {abs(rainfall_anomaly_pct):.0f}% below baseline")
    if ipc_phase:
        phase_labels = {1: "Minimal", 2: "Stressed", 3: "Crisis", 4: "Emergency", 5: "Catastrophe"}
        indicators.append(f"IPC Phase {ipc_phase} ({phase_labels.get(ipc_phase, '')})")

    if indicators:
        parts.append("— " + ", ".join(indicators))
    if affected_pop:
        parts.append(f"— {affected_pop:,} people affected")

    return ". ".join(parts) + "."


def _build_phase_alert(country_name: str, ipc_phase: int, affected_pop: int | None) -> str:
    label = "Emergency" if ipc_phase == 4 else "Catastrophe/Famine"
    msg = f"{country_name}: IPC Phase {ipc_phase} ({label}) — immediate humanitarian response required"
    if affected_pop:
        msg += f". {affected_pop:,} people affected"
    return msg + "."
