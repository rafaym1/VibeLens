"""Google Gemini CLI backend.

Invokes ``gemini --prompt --output-format json --yolo`` as a subprocess.
``--prompt`` enables headless non-interactive mode, ``--output-format json``
returns a structured JSON envelope, and ``--yolo`` auto-approves all actions.

The system prompt is passed via the ``GEMINI_SYSTEM_MD`` environment variable
pointing to a temp file, keeping it separate from the user prompt in stdin.

Gemini has no native JSON schema enforcement, so schema instructions are
always included in the user prompt regardless of the JSON output envelope.

Envelope shape (verified 2026-04-16 via ``gemini -p "..." -o json --yolo``)::

    {
        "session_id": "...",
        "response": "<assistant text>",
        "stats": {
            "models": {
                "<model-name>": {
                    "tokens": {
                        "input": <int>, "candidates": <int>,
                        "cached": <int>, "thoughts": <int>, ...
                    },
                    "roles": {"main": {...}, "utility_router": {...}}
                },
                ...
            }
        }
    }

The Gemini CLI may dispatch to several models in one turn (a cheap
"utility_router" plus a "main" model). We report the entry carrying
``roles.main`` when present, so the usage we surface matches the model
that actually produced the response.

References:
    - Headless mode: https://geminicli.com/docs/cli/headless/
    - Headless docs: https://google-gemini.github.io/gemini-cli/docs/cli/headless.html
"""

from pathlib import Path

from vibelens.llm.backends.cli_base import CliBackend
from vibelens.models.llm.inference import BackendType, InferenceRequest, InferenceResult
from vibelens.models.trajectories.metrics import Metrics


def _select_main_model(models: dict) -> tuple[str, dict]:
    """Pick the ``roles.main`` model entry, falling back to first key.

    Gemini CLI may log several models per turn (e.g. a utility router
    plus the main answering model). The one carrying ``roles.main``
    is the one whose output reached the user.

    Args:
        models: ``stats.models`` dict from the Gemini CLI envelope.

    Returns:
        Tuple of (model name, model entry dict).
    """
    for name, entry in models.items():
        if isinstance(entry, dict) and "main" in entry.get("roles", {}):
            return name, entry
    first_name = next(iter(models))
    first_entry = models[first_name]
    if not isinstance(first_entry, dict):
        first_entry = {}
    return first_name, first_entry


class GeminiCliBackend(CliBackend):
    """Run inference via the Gemini CLI."""

    def __init__(self, model: str | None = None, timeout: int = 120):
        """Initialize Gemini CLI backend.

        Args:
            model: Optional model override passed to the CLI.
            timeout: Request timeout in seconds.
        """
        super().__init__(model=model, timeout=timeout)
        self._system_prompt_file: Path | None = None

    @property
    def cli_executable(self) -> str:
        return "gemini"

    @property
    def backend_id(self) -> BackendType:
        return BackendType.GEMINI

    @property
    def supports_native_json(self) -> bool:
        return True

    def _build_command(self, request: InferenceRequest) -> list[str]:
        """Build gemini CLI command.

        Writes the system prompt to a temp file for ``GEMINI_SYSTEM_MD``
        so the system and user prompts remain cleanly separated.

        Args:
            request: Inference request for model and prompt settings.

        Returns:
            Command as a list of strings.
        """
        self._system_prompt_file = self._create_tempfile(
            request.system, suffix=".md", prefix="vibelens_system_"
        )
        cmd = [
            self._cli_path or self.cli_executable,
            "--prompt",
            "--output-format",
            "json",
            "--yolo",
        ]
        if self._model:
            cmd.extend(["--model", self._model])
        return cmd

    def _build_env(self) -> dict[str, str]:
        """Build env with ``GEMINI_SYSTEM_MD`` pointing to the system prompt file.

        Returns:
            Environment dict with system prompt override.
        """
        env = super()._build_env()
        if self._system_prompt_file:
            env["GEMINI_SYSTEM_MD"] = str(self._system_prompt_file)
        return env

    def _build_prompt(self, request: InferenceRequest) -> str:
        """Return only the user prompt, with optional schema augmentation.

        The system prompt is passed via ``GEMINI_SYSTEM_MD`` env var,
        so stdin carries only the user content. Gemini has no native
        schema enforcement, so schema instructions are always appended.

        Args:
            request: Inference request with user prompt and optional schema.

        Returns:
            User prompt text with optional schema instruction.
        """
        prompt = request.user
        if request.json_schema:
            prompt = self._augment_prompt_with_schema(prompt, request.json_schema)
        return prompt

    def _parse_output(self, output: str, duration_ms: int) -> InferenceResult:
        """Parse the Gemini CLI JSON envelope."""
        return self._parse_single_json(output, duration_ms, self._extract)

    def _extract(self, data: dict) -> tuple[str, Metrics | None, str]:
        """Pull text, usage, and model name from Gemini's ``stats.models`` map."""
        text = str(data.get("response", ""))
        model = self.model
        metrics: Metrics | None = None

        models = data.get("stats", {}).get("models")
        if isinstance(models, dict) and models:
            name, entry = _select_main_model(models)
            model = name
            tokens = entry.get("tokens", {}) if isinstance(entry, dict) else {}
            reasoning_tokens = tokens.get("thoughts", 0)
            metrics = Metrics(
                prompt_tokens=tokens.get("prompt", tokens.get("input", 0)),
                completion_tokens=tokens.get("candidates", 0),
                cached_tokens=tokens.get("cached", 0),
                extra={"reasoning_tokens": reasoning_tokens} if reasoning_tokens else None,
            )
        return text, metrics, model
