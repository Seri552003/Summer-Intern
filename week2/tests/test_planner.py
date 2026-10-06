# test_planner.py
# pytest unit tests for planner
# Week 2 | LLM-CAPP Project
#
# plan() now builds routes with the Dynamic Route Builder (week1/route_builder.py)
# instead of choosing between hard-coded Route_A / Route_B / Route_C, so these
# tests check properties every plan must have rather than a fixed route name.

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../week1")))

from planner import plan
from route_builder import is_complete


def _part(material, features, tolerance="0.02mm", batch_size=500):
    return {"material": material, "features": features,
            "tolerance": tolerance, "batch_size": batch_size}


# Test 1: Aluminum Hole+Slot -> complete route that starts with Facing and ends with Inspection
def test_aluminum_hole_slot_route():
    result = plan(_part("Aluminum", ["Hole", "Slot"]))
    assert result["success"] == True
    steps = result["process_steps"]
    assert isinstance(steps, list)               # plain list of operation names, not a dict
    assert steps[0] == "Facing" and steps[-1] == "Inspection"
    assert is_complete(steps, ["Hole", "Slot"])


# Test 2: Steel Thread+Pocket -> complete route
def test_steel_thread_pocket_route():
    result = plan(_part("Steel", ["Thread", "Pocket"], "0.01mm", 50))
    assert result["success"] == True
    assert is_complete(result["process_steps"], ["Thread", "Pocket"])


# Test 3: Process steps exist
def test_process_steps_exist():
    result = plan(_part("Brass", ["Groove"], "0.05mm", 10))
    assert result["success"] == True
    assert len(result["process_steps"]) > 0


# Test 4: Invalid input -> failure
def test_invalid_input():
    result = plan(_part("Kryptonite", ["Hole"], "0.02mm", 100))
    assert result["success"] == False


# Test 5: Tokens exist in result
def test_tokens_in_result():
    result = plan(_part("Aluminum", ["Hole"], "0.02mm", 200))
    assert result["success"] == True
    assert len(result["tokens"]) > 0


# Test 6: Alternative routes are also plain lists and complete
def test_alternative_routes_are_valid_lists():
    features = ["Hole", "Slot", "Thread"]
    result = plan(_part("Aluminum", features))
    assert result["success"] == True
    for alt in result["alternative_routes"]:
        assert isinstance(alt, list)
        assert is_complete(alt, features)
