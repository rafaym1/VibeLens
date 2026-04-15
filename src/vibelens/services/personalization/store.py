"""Personalization result persistence.

Thin subclass of AnalysisStore with personalization-specific meta building.
"""

from pathlib import Path

from vibelens.models.personalization.enums import PersonalizationMode
from vibelens.models.personalization.results import PersonalizationMeta, PersonalizationResult
from vibelens.services.analysis_store import AnalysisStore, generate_analysis_id
from vibelens.utils.json import locked_jsonl_append
from vibelens.utils.log import get_logger

logger = get_logger(__name__)

MODE_ITEM_COUNTS = {
    PersonalizationMode.CREATION: "creations",
    PersonalizationMode.EVOLUTION: "evolutions",
    PersonalizationMode.RECOMMENDATION: "ranked_recommendations",
    PersonalizationMode.RETRIEVAL: "recommendations",
}


def _build_meta(analysis_id: str, result: PersonalizationResult) -> PersonalizationMeta:
    """Build lightweight metadata from a full personalization result."""
    attr = MODE_ITEM_COUNTS.get(result.mode, "")
    item_count = len(getattr(result, attr, [])) if attr else 0
    return PersonalizationMeta(
        id=analysis_id,
        mode=result.mode,
        session_count=len(result.session_ids),
        title=result.title,
        item_count=item_count,
        backend=result.backend,
        model=result.model,
        created_at=result.created_at,
        batch_count=result.batch_count,
        final_metrics=result.final_metrics,
        is_example=result.is_example,
    )


class PersonalizationStore(AnalysisStore[PersonalizationResult, PersonalizationMeta]):
    """Manages persisted personalization results on disk."""

    def __init__(self, store_dir: Path):
        super().__init__(store_dir, PersonalizationResult, PersonalizationMeta, _build_meta)

    def save(
        self, result: PersonalizationResult, analysis_id: str | None = None
    ) -> PersonalizationMeta:
        """Persist a result and append metadata to the JSONL index."""
        if analysis_id is None:
            analysis_id = generate_analysis_id()

        self._data_path(analysis_id).write_text(result.model_dump_json(indent=2), encoding="utf-8")

        meta = self._build_meta(analysis_id, result)
        locked_jsonl_append(self._index_path, meta.model_dump(mode="json"))

        logger.info("Saved analysis %s to %s", analysis_id, self._dir.name)
        return meta
