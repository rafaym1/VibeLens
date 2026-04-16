"""Session-related request and response models."""

from datetime import datetime

from pydantic import BaseModel, Field


class DownloadRequest(BaseModel):
    """Batch download request payload."""

    session_ids: list[str] = Field(description="Session IDs to export as a zip archive.")


class DonateRequest(BaseModel):
    """Donation request payload."""

    session_ids: list[str] = Field(description="Session IDs to donate.")


class DonateResult(BaseModel):
    """Donation operation result."""

    total: int = Field(description="Total number of sessions in the request.")
    donated: int = Field(description="Number of sessions successfully donated.")
    donation_id: str | None = Field(
        default=None, description="Donation ID, present on successful donation."
    )
    errors: list[dict] = Field(
        default_factory=list, description="Per-session error details for failed donations."
    )


class DonationHistoryEntry(BaseModel):
    """Single donation history entry returned to the client."""

    donation_id: str = Field(description="Unique donation identifier.")
    session_count: int = Field(description="Number of sessions donated in this operation.")
    donated_at: datetime = Field(description="UTC timestamp of the donation.")


class DonationHistoryResponse(BaseModel):
    """Response payload for GET /api/sessions/donations/history."""

    entries: list[DonationHistoryEntry] = Field(
        description="Donations for this browser, newest first."
    )
