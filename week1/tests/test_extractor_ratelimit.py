# test_extractor_ratelimit.py
# Tests for the vision extractor's handling of Groq rate limits (HTTP 429).
# A fake client replaces the real Groq client, so no API key, network or tokens
# are needed.

import sys
import os
from types import SimpleNamespace
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
ife = pytest.importorskip("image_feature_extractor")   # needs the groq + dotenv packages

RATE_LIMIT_ERROR = ("Error code: 429 - {'error': {'message': 'Request too large for model "
                    "qwen/qwen3.8-27b ... on output tokens per minute (OTPM): Limit 1000, "
                    "Requested 1207', 'type': 'tokens', 'code': 'rate_limit_exceeded'}}")
GOOD_JSON = '{"features": ["Hole", "Thread"], "confidence": "high", "notes": "ok"}'


class FakeClient:
    """Raises the given errors in order, then returns GOOD_JSON. Records every call."""
    def __init__(self, errors):
        self.errors = list(errors)
        self.calls = []
        self.chat = SimpleNamespace(completions=SimpleNamespace(create=self._create))

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        if self.errors:
            raise Exception(self.errors.pop(0))
        msg = SimpleNamespace(content=GOOD_JSON)
        return SimpleNamespace(choices=[SimpleNamespace(message=msg)])


def _run(monkeypatch, errors):
    fake = FakeClient(errors)
    sleeps = []
    monkeypatch.setattr(ife, "client", fake)
    monkeypatch.setattr(ife.time, "sleep", lambda s: sleeps.append(s))
    result = ife._extract_single("AAAA", "png", "- Hole: a circle", "focus")
    return result, fake, sleeps


# Test 1: No error -> one call with the normal (higher-quality) settings
def test_normal_call_uses_default_settings(monkeypatch):
    result, fake, sleeps = _run(monkeypatch, [])
    assert result["success"] and result["features"] == ["Hole", "Thread"]
    assert len(fake.calls) == 1
    assert fake.calls[0]["reasoning_effort"] == ife.REASONING_EFFORT
    assert fake.calls[0]["max_completion_tokens"] == ife.MAX_COMPLETION_TOKENS
    assert sleeps == []


# Test 2: One 429 -> retried immediately with the small token budget, then succeeds
def test_rate_limit_retries_with_small_budget(monkeypatch):
    result, fake, sleeps = _run(monkeypatch, [RATE_LIMIT_ERROR])
    assert result["success"] and result["features"] == ["Hole", "Thread"]
    assert len(fake.calls) == 2
    assert fake.calls[1]["reasoning_effort"] == ife.LOW_QUOTA_REASONING
    assert fake.calls[1]["max_completion_tokens"] == ife.LOW_QUOTA_MAX_TOKENS
    assert ife.LOW_QUOTA_MAX_TOKENS < ife.MAX_COMPLETION_TOKENS
    assert sleeps == []


# Test 3: Two 429s -> third attempt happens after a pause
def test_two_rate_limits_pause_then_succeed(monkeypatch):
    result, fake, sleeps = _run(monkeypatch, [RATE_LIMIT_ERROR, RATE_LIMIT_ERROR])
    assert result["success"]
    assert len(fake.calls) == 3
    assert sleeps == [ife.RATE_LIMIT_PAUSE_S]


# Test 4: Persistent 429 -> clear, friendly failure (no crash)
def test_persistent_rate_limit_gives_clear_error(monkeypatch):
    result, fake, sleeps = _run(monkeypatch, [RATE_LIMIT_ERROR] * 3)
    assert result["success"] is False
    assert "rate limit" in result["error"].lower()
    assert len(fake.calls) == 3


# Test 5: Other errors are NOT retried
def test_other_errors_are_not_retried(monkeypatch):
    result, fake, sleeps = _run(monkeypatch, ["Error code: 401 - invalid api key"])
    assert result["success"] is False
    assert len(fake.calls) == 1
