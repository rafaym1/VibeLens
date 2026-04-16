"""OpenAI Codex CLI backend.

Invokes ``codex exec --json --sandbox read-only`` as a subprocess.
Supports native JSON output and schema validation via ``--output-schema``.

Safety flags: ``--ephemeral`` skips session persistence, ``--sandbox read-only``
prevents writes, and ``--skip-git-repo-check`` allows running outside repos.

System prompt: Codex supports ``-c model_instructions_file=<path>`` and
``-c developer_instructions="..."`` as global config overrides, but these
are top-level flags for the interactive ``codex`` command — the ``exec``
subcommand does not accept them. System and user prompts are combined
in stdin as a workaround.

NDJSON event stream (verified 2026-04-16 via ``codex exec --json``)::

    {"type": "thread.started", ...}
    {"type": "turn.started"}
    {"type": "item.completed", "item": {"type": "agent_message", "text": "..."}}
    {"type": "turn.completed", "usage": {
        "input_tokens": <int>,
        "cached_input_tokens": <int>,
        "output_tokens": <int>
    }}

The model name is not echoed per-event; we report the configured
``self._model`` (see https://github.com/openai/codex/issues/14736).

References:
    - Config reference: https://developers.openai.com/codex/config-reference
    - CLI options: https://developers.openai.com/codex/cli/reference
    - Non-interactive mode: https://developers.openai.com/codex/noninteractive
    - Feature request for --system-prompt: https://github.com/openai/codex/issues/11588
    - Model-in-jsonl gap: https://github.com/openai/codex/issues/14736
"""

import json

from vibelens.llm.backend import InferenceError
from vibelens.llm.backends.cli_base import CliBackend
from vibelens.models.llm.inference import BackendType, InferenceRequest, InferenceResult
from vibelens.models.trajectories.metrics import Metrics

# NDJSON event type labels emitted by ``codex exec --json``
EVENT_ITEM_COMPLETED = "item.completed"
EVENT_TURN_COMPLETED = "turn.completed"
# Item type within an ``item.completed`` event that carries assistant text
ITEM_AGENT_MESSAGE = "agent_message"


class CodexCliBackend(CliBackend):
    """Run inference via the OpenAI Codex CLI."""

    @property
    def cli_executable(self) -> str:
        return "codex"

    @property
    def backend_id(self) -> BackendType:
        return BackendType.CODEX

    @property
    def supports_native_json(self) -> bool:
        return True

    def _build_command(self, request: InferenceRequest) -> list[str]:
        """Build codex CLI command.

        Creates a temp schema file for ``--output-schema`` when the
        request includes a JSON schema constraint.

        Args:
            request: Inference request for model and schema settings.

        Returns:
            Command as a list of strings.
        """
        cmd = [
            self._cli_path or self.cli_executable,
            "exec",
            "--json",
            "--sandbox",
            "read-only",
            "--ephemeral",
            "--skip-git-repo-check",
        ]
        if self._model:
            cmd.extend(["--model", self._model])
        if request.json_schema:
            schema_path = self._create_tempfile(
                json.dumps(request.json_schema, indent=2),
                suffix=".json",
                prefix="vibelens_schema_",
            )
            cmd.extend(["--output-schema", str(schema_path)])
        return cmd

    def _parse_output(self, output: str, duration_ms: int) -> InferenceResult:
        """Parse Codex's NDJSON event stream.

        Text comes from every ``item.completed`` event whose item type
        is ``agent_message``. Usage is taken from the final
        ``turn.completed`` event.

        Args:
            output: Raw NDJSON stdout from ``codex exec --json``.
            duration_ms: Elapsed time in milliseconds.

        Returns:
            Parsed InferenceResult.
        """
        text_parts: list[str] = []
        metrics: Metrics | None = None
        for event in self._iter_ndjson_events(output):
            event_type = event.get("type")
            if event_type == EVENT_ITEM_COMPLETED:
                item = event.get("item", {})
                if isinstance(item, dict) and item.get("type") == ITEM_AGENT_MESSAGE:
                    item_text = item.get("text")
                    if isinstance(item_text, str):
                        text_parts.append(item_text)
            elif event_type == EVENT_TURN_COMPLETED:
                usage_data = event.get("usage")
                if isinstance(usage_data, dict):
                    metrics = Metrics(
                        prompt_tokens=usage_data.get("input_tokens", 0),
                        completion_tokens=usage_data.get("output_tokens", 0),
                        cached_tokens=usage_data.get("cached_input_tokens", 0),
                    )
        if not text_parts:
            raise InferenceError("codex NDJSON stream contained no agent_message items")
        if metrics is None:
            metrics = Metrics()
        metrics.duration_ms = duration_ms
        return InferenceResult(text="\n".join(text_parts), model=self.model, metrics=metrics)
