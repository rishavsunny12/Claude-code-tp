"""
Conversational AI handler for food security queries.
Injects real region data into context when a country is selected.
"""

from typing import AsyncIterator, Optional
from app.services.ai.claude_client import stream_text

SYSTEM_PROMPT = """You are HarvestGuard's AI food security analyst. HarvestGuard is a real-time
monitoring platform that fuses NASA MODIS satellite vegetation data, CHIRPS rainfall anomalies,
and WFP food security indicators to provide early warnings of crop failure and food insecurity.

When users ask about specific countries or regions, use the real data provided in the conversation
context. Be specific, data-driven, and actionable. Explain satellite indicators in plain language.

If you don't have data for a region, say so clearly rather than speculating.
Keep responses concise — 3-5 sentences unless more detail is explicitly requested.
Focus on what's most actionable for humanitarian responders, NGOs, and policymakers."""


def build_region_context(
    country_name: str,
    iso_code: str,
    risk_score: Optional[float],
    ipc_phase: Optional[int],
    ndvi_anomaly: Optional[float],
    rainfall_anomaly_pct: Optional[float],
    affected_pop: Optional[int],
    trend: Optional[str],
) -> str:
    """Build a region data context string to inject into chat messages."""
    lines = [f"[Selected region: {country_name} ({iso_code})]"]
    if risk_score is not None:
        lines.append(f"Risk score: {risk_score:.2f}/1.00 (trend: {trend or 'unknown'})")
    if ipc_phase:
        phase_labels = {1: "Minimal", 2: "Stressed", 3: "Crisis", 4: "Emergency", 5: "Catastrophe"}
        lines.append(f"IPC Phase: {ipc_phase} — {phase_labels.get(ipc_phase, '')}")
    if ndvi_anomaly is not None:
        lines.append(f"NDVI anomaly: {ndvi_anomaly:+.2f}σ from 20-year mean")
    if rainfall_anomaly_pct is not None:
        lines.append(f"Rainfall anomaly: {rainfall_anomaly_pct:+.1f}% vs baseline")
    if affected_pop:
        lines.append(f"Affected population: {affected_pop:,}")
    return "\n".join(lines)


async def stream_chat_response(
    messages: list[dict],
    region_context: Optional[str] = None,
) -> AsyncIterator[str]:
    """
    Stream a conversational response. Prepends region context to the last user message
    if a country is currently selected in the UI.
    """
    chat_messages = list(messages)

    if region_context and chat_messages:
        last = chat_messages[-1]
        if last["role"] == "user":
            chat_messages[-1] = {
                "role": "user",
                "content": f"{region_context}\n\nUser question: {last['content']}",
            }

    async for chunk in stream_text(
        messages=chat_messages,
        system=SYSTEM_PROMPT,
        max_tokens=500,
    ):
        yield chunk
