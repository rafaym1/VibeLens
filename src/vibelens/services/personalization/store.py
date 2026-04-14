"""Personalization result persistence.

Thin subclass of AnalysisStore with personalization-specific meta building.
"""

from pathlib import Path

from vibelens.models.personalization.results import PersonalizationResult
from vibelens.schemas.skills import PersonalizationMeta
from vibelens.services.analysis_store import AnalysisStore, generate_analysis_id
from vibelens.utils.json import locked_jsonl_append
from vibelens.utils.log import get_logger

logger = get_logger(__name__)


def _build_meta(analysis_id: str, result: PersonalizationResult) -> PersonalizationMeta:
    """Build lightweight metadata from a full personalization result."""
    return PersonalizationMeta(
        analysis_id=analysis_id,
        mode=result.mode,
        title=result.title,
        session_ids=result.session_ids,
        created_at=result.created_at,
        model=result.model,
        cost_usd=result.final_metrics.total_cost_usd,
    )


class PersonalizationStore(AnalysisStore[PersonalizationResult, PersonalizationMeta]):
    """Manages persisted personalization results on disk."""

    def __init__(self, store_dir: Path):
        super().__init__(store_dir, PersonalizationResult, PersonalizationMeta, _build_meta)

    def save(
        self, result: PersonalizationResult, analysis_id: str | None = None
    ) -> PersonalizationMeta:
        """Persist a result using the model's ``id`` field.

        Overrides the generic store which expects ``analysis_id`` on the result.
        """
        if analysis_id is None:
            analysis_id = generate_analysis_id()

        self._data_path(analysis_id).write_text(
            result.model_dump_json(indent=2), encoding="utf-8"
        )

        meta = self._build_meta(analysis_id, result)
        locked_jsonl_append(self._index_path, meta.model_dump(mode="json"))

        logger.info("Saved analysis %s to %s", analysis_id, self._dir.name)
        return meta
