"""AI API client functions for Anthropic and OpenAI-compatible providers."""

import httpx


ANTHROPIC_VERSION = "2023-06-01"


async def call_anthropic(
    api_key: str,
    api_base_url: str,
    model: str,
    messages: list[dict],
) -> str:
    """Call Anthropic Messages API and return the response text."""
    anthropic_messages = [
        {
            "role": m["author_role"] if m["author_role"] != "assistant" else "assistant",
            "content": m["content"],
        }
        for m in messages
        if m["author_role"] in ("user", "assistant")
    ]

    if not anthropic_messages:
        anthropic_messages = [{"role": "user", "content": "Hello"}]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_base_url}/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": ANTHROPIC_VERSION,
                "content-type": "application/json",
            },
            json={
                "model": model,
                "max_tokens": 4096,
                "messages": anthropic_messages,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        # Handle both regular text and thinking/reasoning models
        # Content can be: [{"type":"text","text":"..."}] or [{"type":"thinking","thinking":"..."},{"type":"text","text":"..."}]
        for block in data.get("content", []):
            if block.get("type") == "text":
                return block["text"]
        # Fallback: return thinking content if no text block
        for block in data.get("content", []):
            if block.get("type") == "thinking":
                return block.get("thinking", "")
        return ""


async def call_openai(
    api_key: str,
    api_base_url: str,
    model: str,
    messages: list[dict],
) -> str:
    """Call OpenAI-compatible API (GPT, DeepSeek, Qwen, etc.) and return the response text."""
    openai_messages = [
        {"role": m["author_role"], "content": m["content"]}
        for m in messages
        if m["author_role"] in ("user", "assistant", "system")
    ]

    if not openai_messages:
        openai_messages = [{"role": "user", "content": "Hello"}]

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{api_base_url}/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "content-type": "application/json",
            },
            json={
                "model": model,
                "messages": openai_messages,
                "max_tokens": 4096,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
