"""Guardrail: модель пропонує, програма вирішує."""

from .errors import DecisionError

# Простір дій: обов'язкові й необов'язкові аргументи кожної дії
ALLOWED_ACTIONS: dict[str, dict[str, set[str]]] = {
    "search_knowledge": {"required": {"query"}, "optional": {"tag"}},
    "read_note": {"required": {"path"}, "optional": set()},
    "write_note": {"required": {"title", "body"}, "optional": {"tags"}},
    "finish": {"required": {"answer"}, "optional": set()},
}


def validate_decision(decision: dict) -> None:
    action = decision.get("action")
    if action not in ALLOWED_ACTIONS:
        raise DecisionError(f"unknown action: {action!r}")

    arguments = decision.get("arguments")
    if not isinstance(arguments, dict):
        raise DecisionError("arguments must be a JSON object")

    spec = ALLOWED_ACTIONS[action]
    missing = spec["required"] - arguments.keys()
    if missing:
        raise DecisionError(f"missing arguments for {action}: {sorted(missing)}")
    extra = arguments.keys() - spec["required"] - spec["optional"]
    if extra:
        raise DecisionError(f"unexpected arguments for {action}: {sorted(extra)}")

    for key, value in arguments.items():
        if value is None and key in spec["optional"]:
            continue
        if not isinstance(value, str) or not value.strip():
            raise DecisionError(f"argument {key!r} must be a non-empty string")
