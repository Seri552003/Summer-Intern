# test_week4.py
# pytest unit tests for Week 4 — FSM + NSGA-II
# Week 4 | LLM-CAPP Project

import sys
import os
import types
import pytest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../week3")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../week1")))

from fsm_validator import validate_sequence, fix_sequence
from nsga2 import run_nsga2, dominates, Individual
from route_builder import is_complete


def _stub_llm(monkeypatch, steps=None):
    """Replace the LLM planner with a stub so tests never call the Groq API
    (offline, deterministic, no API key needed). steps=None simulates an LLM
    failure; otherwise the stub returns that route every time."""
    fake = types.ModuleType("llm_planner")
    if steps is None:
        fake.generate_process_plan = lambda *a, **k: {"success": False, "steps": [], "raw_response": "stub"}
    else:
        fake.generate_process_plan = lambda *a, **k: {"success": True, "steps": list(steps), "raw_response": "stub"}
    monkeypatch.setitem(sys.modules, "llm_planner", fake)


FEATURES = ["Hole", "Slot", "Thread"]


# ── FSM Tests ─────────────────────────────────────

# Test 1: Valid sequence pass hoti hai
def test_valid_sequence():
    seq = ["Facing", "Center Drilling", "Drilling", "Reaming", "Inspection"]
    result = validate_sequence(seq)
    assert result["valid"] == True
    assert len(result["errors"]) == 0


# Test 2: Invalid sequence fail hoti hai
def test_invalid_sequence():
    seq = ["Reaming", "Drilling", "Inspection"]  # Facing missing, wrong order
    result = validate_sequence(seq)
    assert result["valid"] == False
    assert len(result["errors"]) > 0


# Test 3: Sequence Facing se start honi chahiye
def test_must_start_with_facing():
    seq = ["Drilling", "Reaming", "Inspection"]
    result = validate_sequence(seq)
    assert result["valid"] == False


# Test 4: Sequence Inspection pe khatam honi chahiye
def test_must_end_with_inspection():
    seq = ["Facing", "Drilling", "Reaming"]
    result = validate_sequence(seq)
    assert result["valid"] == False


# Test 5: Fix function Facing add karta hai
def test_fix_adds_facing():
    bad_seq = ["Drilling", "Inspection"]
    fixed = fix_sequence(bad_seq)
    assert fixed[0] == "Facing"


# Test 6: Fix function Inspection add karta hai
def test_fix_adds_inspection():
    bad_seq = ["Facing", "Drilling"]
    fixed = fix_sequence(bad_seq)
    assert fixed[-1] == "Inspection"


# Test 7: Fixed sequence valid hoti hai
def test_fixed_sequence_is_valid():
    bad_seq = ["Drilling", "Reaming"]
    fixed = fix_sequence(bad_seq)
    result = validate_sequence(fixed)
    assert result["valid"] == True


# ── NSGA-II Tests ─────────────────────────────────

# Test 8: NSGA-II returns a non-empty Pareto front of complete routes
def test_nsga2_returns_results(monkeypatch):
    _stub_llm(monkeypatch)
    pareto = run_nsga2("Aluminum", 500, features=FEATURES, route_generation_mode="route_builder_first")
    assert len(pareto) > 0
    for ind in pareto:
        assert is_complete(ind.steps, FEATURES)
        assert validate_sequence(ind.steps)["valid"]


# Test 9: Dominance check works (a shorter route beats a longer one on all 3 objectives)
def test_dominance_check():
    mat, batch = "Aluminum", 500
    short = Individual("short", ["Facing", "Inspection"], mat, batch)
    long_ = Individual("long", ["Facing", "Center Drilling", "Drilling", "Reaming", "Inspection"], mat, batch)
    assert dominates(short, long_)
    assert not dominates(long_, short)      # dominance is one-directional
    assert not dominates(short, short)      # a route never dominates itself


# Test 10: No member of the Pareto front dominates another
def test_pareto_front_non_dominated(monkeypatch):
    _stub_llm(monkeypatch)
    pareto = run_nsga2("Steel", 100, features=FEATURES, route_generation_mode="route_builder_first")
    for i in range(len(pareto)):
        for j in range(len(pareto)):
            if i != j:
                assert not dominates(pareto[i], pareto[j])


# Test 11: If the LLM is unavailable, llm_first mode falls back to the Route Builder
def test_llm_first_falls_back_to_route_builder(monkeypatch):
    _stub_llm(monkeypatch)   # every LLM call fails
    pareto = run_nsga2("Aluminum", 500, features=FEATURES, route_generation_mode="llm_first")
    status = run_nsga2.last_llm_status
    assert len(pareto) > 0
    assert status["route_builder_fallback_used"] is True
    assert all(is_complete(ind.steps, FEATURES) for ind in pareto)


# Test 12: An invalid LLM route (Reaming before Drilling) is caught by the FSM and
# replaced by a valid Route-Builder route, never used as-is
def test_invalid_llm_route_is_corrected(monkeypatch):
    bad = ["Facing", "Reaming", "Drilling", "Inspection"]
    assert validate_sequence(bad)["valid"] is False
    _stub_llm(monkeypatch, steps=bad)
    features = ["Reamed_Hole"]
    pareto = run_nsga2("Aluminum", 500, features=features, route_generation_mode="llm_first")
    status = run_nsga2.last_llm_status
    assert status["llm_corrected"] >= 1
    assert status["llm_valid"] == 0
    assert len(pareto) > 0
    for ind in pareto:
        assert ind.steps != bad
        assert validate_sequence(ind.steps)["valid"]
        assert is_complete(ind.steps, features)
