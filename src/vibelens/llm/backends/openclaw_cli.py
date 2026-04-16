"""OpenClaw CLI backend.

Invokes ``openclaw --message -`` as a subprocess. Prompt is piped via stdin.
Uses the ACP protocol for communication. Supports model override via
``--model``.

Does not support native JSON output — uses prompt-level schema augmentation.

System prompt: OpenClaw has no CLI flag for system prompts. It uses a
bootstrap file system (``SOUL.md``, ``AGENTS.md``, ``IDENTITY.md``, etc.)
that is live-reloaded from the workspace directory before each API call.
These require persistent project files unsuitable for per-invocation
overrides. System and user prompts are combined in stdin.

References:
    - System prompt docs: https://docs.openclaw.ai/concepts/system-prompt
"""

from vibelens.llm.backends.cli_base import CliBackend
from vibelens.models.llm.inference import BackendType, InferenceRequest, InferenceResult


class OpenClawCliBackend(CliBackend):
    """Run inference via the OpenClaw CLI."""

    @property
    def cli_executable(self) -> str:
        return "openclaw"

    @property
    def backend_id(self) -> BackendType:
        return BackendType.OPENCLAW

    @property
    def supports_freeform_model(self) -> bool:
        return True

    def _build_command(self, request: InferenceRequest) -> list[str]:
        """Build openclaw CLI command.

        Args:
            request: Inference request for model settings.

        Returns:
            Command as a list of strings.
        """
        cmd = [self._cli_path or self.cli_executable, "--message", "-"]
        if self._model:
            cmd.extend(["--model", self._model])
        return cmd

    def _parse_output(self, output: str, duration_ms: int) -> InferenceResult:
        """Return raw stdout as plain text (OpenClaw emits no JSON envelope)."""
        return self._parse_plain_text(output, duration_ms)
