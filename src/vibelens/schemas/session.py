"""Session-related request and response models."""

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
