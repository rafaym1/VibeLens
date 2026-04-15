"""Personalization API schemas — unified request models and catalog response."""

from pydantic import BaseModel, Field


class PersonalizationRequest(BaseModel):
    """Unified request body for all personalization analyses."""

    session_ids: list[str] = Field(description="Session IDs to analyze.")
    skill_names: list[str] | None = Field(
        default=None,
        description="Skill names to target for evolution. None means all installed skills.",
    )


class CatalogStatusResponse(BaseModel):
    """Response for catalog status check."""

    version: str = Field(description="Catalog version date.")
    item_count: int = Field(description="Number of items in the catalog.")
    schema_version: int = Field(description="Catalog schema version.")
