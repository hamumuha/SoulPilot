import re
from typing import Literal

ToolMode = Literal["read_only", "confirm", "blocked"]

_SAFE_OPERATION_NAME = re.compile(
    r"^(list|enumerate|count|metadata|describe|status|health|version|get status|check status|health check)(?:\s|$)",
    re.IGNORECASE,
)
_MUTATION_TERMS = re.compile(
    r"\b(write|create|update|edit|delete|remove|move|copy|rename|execute|run|shell|command|"
    r"send|email|message|post|publish|commit|deploy|install|purchase|pay|transfer|"
    r"submit|approve|revoke|grant|chmod|upload|download|save|overwrite|patch|put)\b",
    re.IGNORECASE,
)
_SENSITIVE_TERMS = re.compile(
    r"\b(secret|credential|password|token|private|personal|sensitive|key|database|sql)\b",
    re.IGNORECASE,
)


def default_tool_mode(name: str, description: str = "") -> ToolMode:
    """Default to confirmation unless the tool is clearly described as read-only."""
    combined = f"{name} {description}"
    if _MUTATION_TERMS.search(combined) or _SENSITIVE_TERMS.search(combined):
        return "confirm"
    normalized_name = re.sub(r"[_-]+", " ", name).strip()
    if _SAFE_OPERATION_NAME.search(normalized_name):
        return "read_only"
    return "confirm"
