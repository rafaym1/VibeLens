"""Unit tests for vibelens.ingest.parsers.shared.content_blocks."""

from vibelens.ingest.parsers.shared.content_blocks import (
    ContentPiece,
    iter_text_and_tool_uses,
)


def test_yields_text_block() -> None:
    blocks = [{"type": "text", "text": "hello"}]
    pieces = list(iter_text_and_tool_uses(blocks))
    assert len(pieces) == 1
    assert pieces[0].kind == "text"
    assert pieces[0].text == "hello"


def test_yields_thinking_block() -> None:
    blocks = [{"type": "thinking", "thinking": "reasoning..."}]
    pieces = list(iter_text_and_tool_uses(blocks))
    assert pieces[0].kind == "thinking"
    assert pieces[0].text == "reasoning..."


def test_yields_tool_use_block() -> None:
    blocks = [
        {
            "type": "tool_use",
            "id": "tu_1",
            "name": "Read",
            "input": {"file_path": "/x"},
        }
    ]
    pieces = list(iter_text_and_tool_uses(blocks))
    assert pieces[0].kind == "tool_use"
    assert pieces[0].tool_use_id == "tu_1"
    assert pieces[0].tool_name == "Read"
    assert pieces[0].tool_input == {"file_path": "/x"}


def test_yields_tool_result_block_with_error_flag() -> None:
    blocks = [
        {
            "type": "tool_result",
            "tool_use_id": "tu_1",
            "content": "failed",
            "is_error": True,
        }
    ]
    pieces = list(iter_text_and_tool_uses(blocks))
    assert pieces[0].kind == "tool_result"
    assert pieces[0].tool_use_id == "tu_1"
    assert pieces[0].text == "failed"
    assert pieces[0].is_error is True


def test_skips_unknown_block_types() -> None:
    blocks = [
        {"type": "text", "text": "a"},
        {"type": "image", "source": {}},
        {"type": "text", "text": "b"},
    ]
    pieces = list(iter_text_and_tool_uses(blocks))
    assert [p.text for p in pieces] == ["a", "b"]


def test_coerces_list_content_on_tool_result() -> None:
    blocks = [
        {
            "type": "tool_result",
            "tool_use_id": "tu_1",
            "content": [
                {"type": "text", "text": "part-a"},
                {"type": "text", "text": "part-b"},
            ],
        }
    ]
    pieces = list(iter_text_and_tool_uses(blocks))
    assert pieces[0].text == "part-apart-b"


def test_content_piece_is_instantiable() -> None:
    piece = ContentPiece(kind="text", text="x")
    assert piece.kind == "text"
    assert piece.tool_use_id is None
