"""Anthropic Messages API content-block normalization.

Claude Code, Claude Web, and Hermes all produce assistant messages
whose ``content`` field is a list of typed blocks:

    {"type": "text", "text": ...}
    {"type": "thinking", "thinking": ...}
    {"type": "tool_use", "id": ..., "name": ..., "input": {...}}
    {"type": "tool_result", "tool_use_id": ..., "content": ..., "is_error": ?}

This helper walks such a list once and yields a uniform ContentPiece
for each supported block, skipping unknown block types (e.g. image).
Per-parser step-building logic can then dispatch on ``piece.kind``
instead of duplicating the type-switch.
"""

from collections.abc import Iterator
from typing import Literal

from pydantic import BaseModel, Field

# The four block types we normalize.  Anything else (e.g. "image",
# "server_tool_use", older format variants) is ignored silently — we
# do not attempt transparent upcasts.
_TEXT_BLOCK = "text"
_THINKING_BLOCK = "thinking"
_TOOL_USE_BLOCK = "tool_use"
_TOOL_RESULT_BLOCK = "tool_result"


class ContentPiece(BaseModel):
    """Normalized view of one Anthropic content block."""

    kind: Literal["text", "thinking", "tool_use", "tool_result"] = Field(
        description="Which block kind this piece represents."
    )
    text: str | None = Field(
        default=None,
        description="For text/thinking/tool_result blocks: the plain text payload.",
    )
    tool_use_id: str | None = Field(
        default=None,
        description="For tool_use: the id; for tool_result: the paired tool_use_id.",
    )
    tool_name: str | None = Field(
        default=None, description="Tool name — tool_use blocks only."
    )
    tool_input: dict | None = Field(
        default=None, description="Tool arguments dict — tool_use blocks only."
    )
    is_error: bool = Field(
        default=False,
        description="True when a tool_result block is flagged as errored.",
    )


def _coerce_tool_result_content(raw: object) -> str:
    """Flatten a tool_result content field into a single string.

    Anthropic encodes tool output as either a plain string or a list
    of ``{"type": "text", "text": ...}`` blocks.  Downstream code only
    wants the text, so we concatenate.
    """
    if isinstance(raw, str):
        return raw
    if isinstance(raw, list):
        parts = []
        for item in raw:
            if isinstance(item, dict) and item.get("type") == _TEXT_BLOCK:
                parts.append(str(item.get("text", "")))
        return "".join(parts)
    return str(raw) if raw is not None else ""


def iter_text_and_tool_uses(blocks: list[dict]) -> Iterator[ContentPiece]:
    """Yield one ContentPiece per supported Anthropic content block.

    Unknown block types are skipped.  The order of emission matches the
    input list so callers can preserve chronological structure.
    """
    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = block.get("type")
        if block_type == _TEXT_BLOCK:
            yield ContentPiece(kind="text", text=str(block.get("text", "")))
        elif block_type == _THINKING_BLOCK:
            yield ContentPiece(
                kind="thinking", text=str(block.get("thinking", ""))
            )
        elif block_type == _TOOL_USE_BLOCK:
            raw_input = block.get("input")
            yield ContentPiece(
                kind="tool_use",
                tool_use_id=block.get("id"),
                tool_name=block.get("name"),
                tool_input=raw_input if isinstance(raw_input, dict) else {},
            )
        elif block_type == _TOOL_RESULT_BLOCK:
            yield ContentPiece(
                kind="tool_result",
                tool_use_id=block.get("tool_use_id"),
                text=_coerce_tool_result_content(block.get("content")),
                is_error=bool(block.get("is_error")),
            )
