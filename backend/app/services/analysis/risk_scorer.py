"""
Composite food insecurity risk scoring.
Combines NDVI anomaly, rainfall anomaly, WFP IPC phase, and 30-day trend
into a single 0.0–1.0 risk score mapped to IPC phases.
"""

from dataclasses import dataclass


@dataclass
class RiskScoreResult:
    score: float            # 0.0 (minimal) to 1.0 (catastrophe)
    ipc_equivalent: int     # 1–5 derived from score
    trend: str              # improving | stable | deteriorating
    factors: dict           # breakdown for explainability


def compute_risk_score(
    ndvi_anomaly: float | None,
    rainfall_anomaly_pct: float | None,
    ipc_phase: int | None,
    prev_score: float | None = None,
) -> RiskScoreResult:
    """
    Compute composite risk score from multi-source indicators.

    Weights:
      - NDVI anomaly:       35% (satellite vegetation health — leading indicator)
      - Rainfall anomaly:   30% (precipitation deficit — leading indicator)
      - IPC phase:          35% (WFP ground-truth assessment — lagging but authoritative)

    Each component normalized to 0 (best) → 1 (worst).
    """
    components = {}

    # NDVI component: -3 std deviations = worst (score 1.0), +3 = best (score 0.0)
    if ndvi_anomaly is not None:
        ndvi_component = max(0.0, min(1.0, (-ndvi_anomaly + 1.5) / 4.5))
    else:
        ndvi_component = 0.3   # neutral assumption when data unavailable
    components["ndvi"] = round(ndvi_component, 3)

    # Rainfall component: -50% or worse = worst (score 1.0), +50% = best (score 0.0)
    if rainfall_anomaly_pct is not None:
        rainfall_component = max(0.0, min(1.0, (-rainfall_anomaly_pct + 25) / 75))
    else:
        rainfall_component = 0.3
    components["rainfall"] = round(rainfall_component, 3)

    # IPC phase component: phase 1 = 0.0, phase 5 = 1.0
    if ipc_phase is not None:
        phase_component = (max(1, min(5, ipc_phase)) - 1) / 4.0
    else:
        phase_component = 0.3
    components["ipc_phase"] = round(phase_component, 3)

    composite = (
        ndvi_component     * 0.35 +
        rainfall_component * 0.30 +
        phase_component    * 0.35
    )
    composite = round(composite, 4)

    # Trend from 30-day score delta
    if prev_score is not None:
        delta = composite - prev_score
        if delta > 0.05:
            trend = "deteriorating"
        elif delta < -0.05:
            trend = "improving"
        else:
            trend = "stable"
    else:
        trend = "stable"

    return RiskScoreResult(
        score=composite,
        ipc_equivalent=_score_to_ipc(composite),
        trend=trend,
        factors=components,
    )


def _score_to_ipc(score: float) -> int:
    """Map composite score to IPC phase equivalent."""
    if score >= 0.80:
        return 5
    if score >= 0.60:
        return 4
    if score >= 0.40:
        return 3
    if score >= 0.20:
        return 2
    return 1
