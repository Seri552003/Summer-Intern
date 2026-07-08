# test_week4.py
# pytest unit tests for Week 4 — FSM + NSGA-II
# Week 4 | LLM-CAPP Project

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../week3")))

from fsm_validator import validate_sequence, fix_sequence
from nsga2 import run_nsga2, dominates, Individual, ROUTE_VARIANTS


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

# Test 8: NSGA-II results return karta hai
def test_nsga2_returns_results():
    pareto = run_nsga2("Aluminum", 500)
    assert len(pareto) > 0


# Test 9: Dominance check sahi kaam karta hai
def test_dominance_check():
    mat, batch = "Aluminum", 500
    ind_a = Individual("Route_B2", ROUTE_VARIANTS["Route_B2"], mat, batch)
    ind_b = Individual("Route_A1", ROUTE_VARIANTS["Route_A1"], mat, batch)
    # Route_B2 shorter hai — likely dominates longer route
    # At least ek direction mein dominance check karo
    dom_ab = dominates(ind_a, ind_b)
    dom_ba = dominates(ind_b, ind_a)
    # Dono simultaneously dominate nahi kar sakte
    assert not (dom_ab and dom_ba)


# Test 10: Pareto front mein koi ek dusre ko dominate nahi karta
def test_pareto_front_non_dominated():
    pareto = run_nsga2("Steel", 100)
    for i in range(len(pareto)):
        for j in range(len(pareto)):
            if i != j:
                assert not dominates(pareto[i], pareto[j])