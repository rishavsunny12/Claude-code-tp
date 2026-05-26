"""
AI-powered country risk assessment generation.
Builds prompts from real satellite and field data and streams Claude's analysis.
"""

import re
from datetime import date
from typing import AsyncIterator, Optional
from app.services.ai.claude_client import stream_text

# Labels small local LLMs often echo from the prompt — stripped from streamed output.
_SECTION_LABEL_RE = re.compile(
    r"(\*{0,2}\s*)?"
    r"[Pp]aragraph\s*\d+\s*"
    r"([—–\-]\s*)?"
    r"(Current Situation|Key Drivers|(?:30[- ]?60[- ]?Day\s+)?Outlook)?"
    r"\s*:?\s*"
    r"\*{0,2}",
    re.IGNORECASE,
)
_STANDALONE_HEADING_RE = re.compile(
    r"(\*{0,2}\s*)?(Current Situation|Key Drivers|(?:30[- ]?60[- ]?Day\s+)?Outlook)\s*:?\s*\*{0,2}",
    re.IGNORECASE,
)


def _strip_section_labels(text: str) -> str:
    text = _SECTION_LABEL_RE.sub("", text)
    text = _STANDALONE_HEADING_RE.sub("", text)
    return text

IPC_DESCRIPTIONS = {
    1: "Minimal — most households can meet food needs without resorting to negative coping strategies",
    2: "Stressed — have minimally adequate food but unable to afford non-food expenses",
    3: "Crisis — food consumption gaps exist, or use of crisis coping strategies",
    4: "Emergency — large food consumption gaps; high levels of acute malnutrition",
    5: "Catastrophe/Famine — extreme food deprivation and starvation with widespread mortality",
}

SYSTEM_PROMPT = """You are a senior food security analyst at HarvestGuard, an AI-powered early warning system.
You have access to real-time satellite vegetation data (NASA MODIS NDVI), CHIRPS rainfall anomalies,
and WFP food security indicators. Your assessments are used by NGOs, governments, and humanitarian
organizations to allocate resources and trigger responses.

Write concise, expert-level assessments. Be specific and data-driven — reference the actual numbers.
Do not use generic phrases like "the situation is concerning." Explain what the satellite data means
in practical terms for farmers and communities. Use plain language accessible to non-specialists.

Never include section headings or labels in your output (e.g. do not write "Paragraph 1",
"Current Situation", "Key Drivers", or markdown headings). Write flowing prose only."""


async def stream_risk_assessment(
    country_name: str,
    iso_code: str,
    ndvi_current: Optional[float],
    ndvi_anomaly: Optional[float],
    ndvi_trend_30d: Optional[float],
    rainfall_current_mm: Optional[float],
    rainfall_anomaly_pct: Optional[float],
    ipc_phase: Optional[int],
    affected_pop: Optional[int],
    risk_score: float,
    trend: str,
) -> AsyncIterator[str]:
    """Stream a Claude risk assessment for a country using real data."""

    today = date.today().strftime("%B %d, %Y")
    ipc_desc = IPC_DESCRIPTIONS.get(ipc_phase or 0, "Unknown")

    # Build data context from real values
    data_lines = []
    if ndvi_current is not None:
        anomaly_str = f"{ndvi_anomaly:+.2f} standard deviations from 20-year mean" if ndvi_anomaly is not None else "anomaly unavailable"
        data_lines.append(f"• Vegetation Health (NDVI): {ndvi_current:.3f} — {anomaly_str}")
    if ndvi_trend_30d is not None:
        direction = "declining" if ndvi_trend_30d < 0 else "improving"
        data_lines.append(f"• NDVI 30-day trend: {direction} ({ndvi_trend_30d:+.3f})")
    if rainfall_current_mm is not None:
        anom_str = f"{rainfall_anomaly_pct:+.1f}% vs 1981-2010 baseline" if rainfall_anomaly_pct is not None else "baseline unavailable"
        data_lines.append(f"• Monthly Rainfall: {rainfall_current_mm:.1f}mm — {anom_str}")
    if ipc_phase:
        pop_str = f" ({affected_pop:,} people)" if affected_pop else ""
        data_lines.append(f"• WFP IPC Phase: {ipc_phase}/5 — {ipc_desc}{pop_str}")
    data_lines.append(f"• Composite risk score: {risk_score:.2f}/1.00 (trend: {trend})")

    data_section = "\n".join(data_lines) if data_lines else "Limited data available for this country."

    prompt = f"""Analyze the current food security situation in {country_name} ({iso_code}) as of {today}.

REAL SATELLITE AND FIELD DATA:
{data_section}

Write exactly 3 short paragraphs of plain prose. Separate them with a single blank line only.

Content order:
1) What the numbers mean for farmers and communities right now (NDVI, rainfall).
2) What is driving the risk level — which indicators matter most.
3) Likely trajectory over 30-60 days and recommended actions for NGOs or governments.

Rules: no headings, no numbered sections, no labels, no markdown headers, and never write
the words Paragraph, Current Situation, Key Drivers, or Outlook."""

    async for chunk in stream_text(
        messages=[{"role": "user", "content": prompt}],
        system=SYSTEM_PROMPT,
        max_tokens=700,
    ):
        cleaned = _strip_section_labels(chunk)
        if cleaned:
            yield cleaned
