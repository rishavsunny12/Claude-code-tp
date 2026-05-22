"""
Anthropic Claude API client wrapper.
Uses claude-sonnet-4-6 for risk assessments and chat.
Implements streaming responses for real-time UI updates.
"""

import anthropic
import logging
from typing import AsyncIterator
from app.core.config import get_settings

logger = logging.getLogger(__name__)

_client: anthropic.AsyncAnthropic | None = None


def get_claude_client() -> anthropic.AsyncAnthropic:
    global _client
    if _client is None:
        settings = get_settings()
        _client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    return _client


async def stream_text(
    messages: list[dict],
    system: str,
    max_tokens: int = 800,
) -> AsyncIterator[str]:
    """Stream text tokens from Claude. Yields text chunks as they arrive."""
    client = get_claude_client()
    try:
        async with client.messages.stream(
            model="claude-sonnet-4-6",
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text
    except anthropic.APIError as e:
        logger.error("Claude API error: %s", e)
        yield f"\n\n[Analysis temporarily unavailable: {type(e).__name__}]"
