"""Tests for donation history schemas."""

from datetime import datetime, timezone

from vibelens.schemas.session import DonationHistoryEntry, DonationHistoryResponse


def test_donation_history_entry_roundtrip():
    """DonationHistoryEntry serializes and deserializes cleanly."""
    entry = DonationHistoryEntry(
        donation_id="20260416154211_3b4d",
        session_count=3,
        donated_at=datetime(2026, 4, 16, 15, 42, 11, tzinfo=timezone.utc),
    )
    dumped = entry.model_dump(mode="json")
    print(f"dumped = {dumped}")
    assert dumped["donation_id"] == "20260416154211_3b4d"
    assert dumped["session_count"] == 3
    assert "2026-04-16" in dumped["donated_at"]

    restored = DonationHistoryEntry.model_validate(dumped)
    assert restored == entry


def test_donation_history_response_default_empty():
    """DonationHistoryResponse can be constructed with an empty list."""
    resp = DonationHistoryResponse(entries=[])
    print(f"resp = {resp}")
    assert resp.entries == []
