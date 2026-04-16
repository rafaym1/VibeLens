"""OpenCode CLI backend.

Invokes ``opencode -p - -q -f json --system <prompt>`` as a subprocess.
The user prompt is piped via stdin. ``-q`` suppresses the interactive spinner
for scripted usage, and ``-f json`` returns structured JSON output.

The system prompt is passed via ``--system`` to properly separate system
and user prompts, avoiding duplication in stdin.

Envelope shape (per OpenCode CLI docs): a single JSON object whose
assistant text lives under ``result`` (or ``text`` in older versions).
Token usage may appear under ``usage`` when supplied by the upstream
provider; otherwise None.

References:
    - CLI docs: https://opencode.ai/docs/cli/
"""

from vibelens.llm.backends.cli_base import CliBackend
from vibelens.models.llm.inference import BackendType, InferenceRequest, InferenceResult
from vibelens.models.trajectories.metrics import Metrics


class OpenCodeCliBackend(CliBackend):
    """Run inference via the OpenCode CLI."""

    @property
    def cli_executable(self) -> str:
        return "opencode"

    @property
    def backend_id(self) -> BackendType:
        return BackendType.OPENCODE

    @property
    def supports_freeform_model(self) -> bool:
        return True

    @property
    def supports_native_json(self) -> bool:
        return True

    def _build_command(self, request: InferenceRequest) -> list[str]:
        """Build opencode CLI command.

        Passes the system prompt via ``--system`` for clean
        system/user separation. Stdin carries only the user prompt.

        Args:
            request: Inference request for prompt settings.

        Returns:
            Command as a list of strings.
        """
        cmd = [
            self._cli_path or self.cli_executable,
            "-p",
            "-",
            "-q",
            "-f",
            "json",
            "--system",
            request.system,
        ]
        if self._model:
            cmd.extend(["--model", self._model])
        return cmd

    def _build_prompt(self, request: InferenceRequest) -> str:
        """Return only the user prompt.

        The system prompt is passed via ``--system`` in
        ``_build_command``, so stdin carries only the user content.

        Args:
            request: Inference request with system and user prompts.

        Returns:
            User prompt text only.
        """
        return request.user

    def _parse_output(self, output: str, duration_ms: int) -> InferenceResult:
        """Parse OpenCode's single-JSON envelope."""
        return self._parse_single_json(output, duration_ms, self._extract)

    def _extract(self, data: dict) -> tuple[str, Metrics | None, str]:
        """Pull text and optional usage from OpenCode's envelope.

        The exact key for the assistant text has varied across OpenCode
        versions; we try ``result``, ``text``, and ``response`` in order.
        """
        text = data.get("result") or data.get("text") or data.get("response") or ""
        metrics: Metrics | None = None
        usage_data = data.get("usage")
        if isinstance(usage_data, dict):
            metrics = Metrics(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
            )
        model = data.get("model") or self.model
        return str(text), metrics, model
