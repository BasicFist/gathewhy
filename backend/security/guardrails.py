import re
from dataclasses import dataclass


@dataclass
class GuardrailViolation:
    check_name: str
    message: str
    risk_level: str  # "high", "medium", "low"


class GuardrailManager:
    def __init__(self):
        # Regex for common secrets (sk-..., etc.)
        self.secret_patterns = [
            (r"sk-[a-zA-Z0-9]{20,}", "Possible OpenAI API Key"),
            (r"xox[baprs]-([0-9a-zA-Z]{10,48})", "Possible Slack Token"),
            (r"ghp_[0-9a-zA-Z]{36}", "Possible GitHub Personal Access Token"),
            (
                r"-----BEGIN PRIVATE KEY-----",  # pragma: allowlist secret
                "Possible SSH Private Key",
            ),
        ]

    def check_prompt(self, text: str) -> list[GuardrailViolation]:
        """Check prompt for potential security violations."""
        violations = []

        # Secret scanning
        for pattern, desc in self.secret_patterns:
            if re.search(pattern, text):
                violations.append(
                    GuardrailViolation(
                        check_name="secret_scan",
                        message=f"Detected sensitive data pattern: {desc}",
                        risk_level="high",
                    )
                )

        return violations

    def check_request(self, kwargs: dict) -> Exception | None:
        """
        Inspect a LiteLLM request kwargs.
        Returns an Exception if the request should be blocked, else None.
        """
        messages = kwargs.get("messages", [])
        prompt_text = ""

        # Extract text from messages
        if isinstance(messages, list):
            for msg in messages:
                if isinstance(msg, dict):
                    content = msg.get("content", "")
                    if isinstance(content, str):
                        prompt_text += content + "\n"
                    elif isinstance(content, list):
                        # Handle multimodal content structure
                        for part in content:
                            if isinstance(part, dict) and part.get("type") == "text":
                                prompt_text += part.get("text", "") + "\n"

        violations = self.check_prompt(prompt_text)

        if violations:
            # For V1, we only block on HIGH risk
            high_risk = [v for v in violations if v.risk_level == "high"]
            if high_risk:
                violation_msg = "; ".join([v.message for v in high_risk])
                return ValueError(f"Guardrail blocked request: {violation_msg}")

        return None
