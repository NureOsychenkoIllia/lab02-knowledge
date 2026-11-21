import pytest

from agent.errors import DecisionError
from agent.validator import validate_decision


def test_unknown_action_is_rejected():
    with pytest.raises(DecisionError, match="unknown action"):
        validate_decision({"action": "write_note", "arguments": {"path": "Inbox/a.md"}})


def test_missing_and_extra_arguments_are_rejected():
    with pytest.raises(DecisionError, match="missing arguments"):
        validate_decision({"action": "search_knowledge", "arguments": {}})
    with pytest.raises(DecisionError, match="unexpected arguments"):
        validate_decision({"action": "read_note",
                           "arguments": {"path": "a.md", "tag": "cap"}})


def test_empty_argument_is_rejected():
    with pytest.raises(DecisionError, match="non-empty string"):
        validate_decision({"action": "finish", "arguments": {"answer": "   "}})


def test_valid_decisions_pass():
    validate_decision({"action": "search_knowledge",
                       "arguments": {"query": "CAP", "tag": None}})
    validate_decision({"action": "finish", "arguments": {"answer": "Готово"}})
