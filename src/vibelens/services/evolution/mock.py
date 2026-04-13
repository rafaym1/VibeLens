"""Mock evolution analysis data for demo/test mode.

Builds realistic EvolutionAnalysisResult instances using real step IDs
from loaded trajectories.
"""

from datetime import datetime, timezone

from vibelens.deps import get_central_skill_store
from vibelens.models.enums import ElementType
from vibelens.models.evolution import ElementEdit, ElementEvolution, EvolutionAnalysisResult
from vibelens.models.llm.inference import BackendType
from vibelens.models.session.patterns import WorkflowPattern
from vibelens.models.step_ref import StepRef
from vibelens.models.trajectories.metrics import Metrics
from vibelens.services.session.store_resolver import load_from_stores

# Cap session loading in mock mode to avoid slow I/O
MAX_MOCK_SESSIONS = 5


def build_mock_evolution_result(session_ids: list[str]) -> EvolutionAnalysisResult:
    """Build a mock EvolutionAnalysisResult for demo/test mode.

    Args:
        session_ids: Session IDs from the request.

    Returns:
        Mock EvolutionAnalysisResult with sample patterns and evolution suggestions.
    """
    step_pool = _collect_step_ids(session_ids)
    loaded_ids = list(step_pool.keys())
    skipped = [sid for sid in session_ids if sid not in step_pool]

    patterns = _build_mock_patterns(step_pool)
    evolutions = _build_mock_evolutions()

    return EvolutionAnalysisResult(
        title="Your Installed Skills Are Missing Linting and Context-Reduction Steps",
        workflow_patterns=patterns,
        evolutions=evolutions,
        session_ids=loaded_ids,
        skipped_session_ids=skipped,
        backend_id=BackendType.MOCK,
        model="mock/test-model",
        metrics=Metrics(cost_usd=0.028),
        created_at=datetime.now(timezone.utc).isoformat(),
    )


def _collect_step_ids(session_ids: list[str]) -> dict[str, list[str]]:
    """Load trajectories and collect step IDs per session.

    Only loads up to MAX_MOCK_SESSIONS to avoid slow I/O in mock mode.
    All remaining session_ids are reported as loaded (with no step refs).
    """
    pool: dict[str, list[str]] = {}
    for sid in session_ids[:MAX_MOCK_SESSIONS]:
        trajectories = load_from_stores(sid)
        if not trajectories:
            continue
        step_ids = [step.step_id for traj in trajectories for step in traj.steps]
        if step_ids:
            pool[sid] = step_ids
    # Mark remaining sessions as "loaded" without step data
    for sid in session_ids[MAX_MOCK_SESSIONS:]:
        if sid not in pool:
            pool[sid] = []
    return pool


def _build_mock_patterns(pool: dict[str, list[str]]) -> list[WorkflowPattern]:
    """Build mock workflow patterns with varying frequencies for edge-case coverage."""
    if not pool:
        return []

    sids = list(pool.keys())

    all_refs: list[StepRef] = []
    for sid in sids[:5]:
        steps = pool[sid]
        for step_id in steps[:3]:
            all_refs.append(StepRef(session_id=sid, start_step_id=step_id))

    return [
        WorkflowPattern(
            title="Search-Read-Edit Cycle",
            description=(
                "Grep for a pattern, read the matching file, then edit it. "
                "This three-step sequence appears whenever code modifications are needed."
            ),
            example_refs=all_refs[:6],
        ),
        WorkflowPattern(
            title="Test-Fix Loop",
            description=(
                "Run tests, read failure output, apply fix, re-run tests. "
                "Iterative debugging cycle until all tests pass."
            ),
            example_refs=all_refs[:3],
        ),
    ]


def _build_mock_evolutions() -> list[ElementEvolution]:
    """Build mock evolution suggestions using installed skills."""
    skill_store = get_central_skill_store()
    skills = skill_store.get_cached()

    evolutions: list[ElementEvolution] = []

    if skills:
        first_skill = skills[0]
        evolutions.append(
            ElementEvolution(
                element_type=ElementType.SKILL,
                element_name=first_skill.name,
                description=first_skill.description or first_skill.name,
                edits=[
                    ElementEdit(
                        old_string="",
                        new_string="5. Run `ruff check` after every edit to catch lint errors.",
                    ),
                    ElementEdit(
                        old_string=first_skill.description or first_skill.name,
                        new_string=f"{first_skill.name} with automatic linting and error checking",
                    ),
                    ElementEdit(
                        old_string="allowed_tools: [Read, Edit]",
                        new_string="allowed_tools: [Read, Edit, Grep]",
                    ),
                ],
                rationale=(
                    f"Skill '{first_skill.name}' needs alignment with observed usage.\n"
                    "- Adding linting catches errors earlier in the workflow\n"
                    "- Search capabilities match your grep-first patterns"
                ),
                addressed_patterns=["Search-Read-Edit Cycle", "Test-Fix Loop"],
            )
        )

    if len(skills) > 1:
        second_skill = skills[1]
        evolutions.append(
            ElementEvolution(
                element_type=ElementType.SKILL,
                element_name=second_skill.name,
                description=second_skill.description or second_skill.name,
                edits=[
                    ElementEdit(
                        old_string="Step 3: Manual verification\n",
                        new_string="",
                    ),
                    ElementEdit(
                        old_string="Step 2: Read all files in directory",
                        new_string="Step 2: Read only modified files (use `git diff --name-only`)",
                    ),
                ],
                rationale=(
                    f"Skill '{second_skill.name}' wastes context on redundant steps.\n"
                    "- Removing manual verification step saves a full turn\n"
                    "- Reading only modified files reduces context usage by ~30%"
                ),
                addressed_patterns=["Search-Read-Edit Cycle"],
            )
        )

    if not evolutions:
        evolutions.append(
            ElementEvolution(
                element_type=ElementType.SKILL,
                element_name="example-skill",
                description="Example skill for demonstrating evolution analysis.",
                edits=[
                    ElementEdit(
                        old_string="",
                        new_string="Always verify changes with the linter before completing.",
                    ),
                ],
                rationale=(
                    "No installed skills found.\n"
                    "- This is an example showing how evolution analysis works"
                ),
                addressed_patterns=["Search-Read-Edit Cycle"],
            )
        )

    return evolutions
