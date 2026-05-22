"""
LLM client — supports local LLMs (Ollama, LM Studio, llama.cpp) and Anthropic Claude.

Provider is selected by the LLM_PROVIDER env var:
  "local"     → any OpenAI-compatible local LLM server (default for development)
  "anthropic" → Anthropic Claude API (set for production)

All AI calls in the codebase go through stream_text() — no other files need changing
when switching providers.
"""

import logging
from typing import AsyncIterator
from app.core.config import get_settings

logger = logging.getLogger(__name__)


async def stream_text(
    messages: list[dict],
    system: str,
    max_tokens: int = 800,
) -> AsyncIterator[str]:
    """Stream text tokens from the configured LLM provider."""
    settings = get_settings()

    if settings.llm_provider == "anthropic":
        async for chunk in _stream_anthropic(messages, system, max_tokens, settings):
            yield chunk
    else:
        async for chunk in _stream_local(messages, system, max_tokens, settings):
            yield chunk


async def _stream_anthropic(messages, system, max_tokens, settings) -> AsyncIterator[str]:
    """Stream from Anthropic Claude API."""
    import anthropic

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
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
        logger.error("Anthropic API error: %s", e)
        yield f"\n\n[Analysis temporarily unavailable: {type(e).__name__}]"


async def _stream_local(messages, system, max_tokens, settings) -> AsyncIterator[str]:
    """
    Stream from any OpenAI-compatible local LLM server.
    Works with Ollama (localhost:11434/v1), LM Studio (localhost:1234/v1),
    llama.cpp server (localhost:8080/v1), and Jan (localhost:1337/v1).
    """
    from openai import AsyncOpenAI, APIError

    client = AsyncOpenAI(
        base_url=settings.local_llm_base_url,
        api_key="local",   # local servers don't authenticate but the field is required
    )

    # OpenAI-compatible format: system message goes first in the messages array
    full_messages = [{"role": "system", "content": system}] + messages

    try:
        stream = await client.chat.completions.create(
            model=settings.local_llm_model,
            messages=full_messages,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                yield delta
    except APIError as e:
        logger.error("Local LLM error (%s): %s", settings.local_llm_base_url, e)
        yield f"\n\n[Local LLM unavailable — is {settings.local_llm_base_url.split('/')[2]} running? Error: {type(e).__name__}]"
    except Exception as e:
        logger.error("Local LLM connection error: %s", e)
        yield f"\n\n[Cannot reach local LLM at {settings.local_llm_base_url} — start Ollama or LM Studio first]"
