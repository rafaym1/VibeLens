"""Source metadata for skills."""

from pydantic import BaseModel, Field

from vibelens.models.enums import SkillSource


class SkillSourceInfo(BaseModel):
    """One source from which a skill is available or was loaded."""

    source_type: SkillSource = Field(description="Source/store type for this skill.")
    source_path: str = Field(description="Local path or URL for the source.")
