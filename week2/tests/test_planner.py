# test_planner.py
# pytest unit tests for planner
# Week 2 | LLM-CAPP Project

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../week1")))

from planner import plan, select_route

# Test 1: Aluminum Hole+Slot → Route A
def test_aluminum_route_a():
    result = plan({
        "material":   "Aluminum",
        "features":   ["Hole", "Slot"],
        "tolerance":  "0.02mm",
        "batch_size": 500
    })
    assert result["success"] == True
    assert result["selected_route"] == "Route_A"

# Test 2: Steel Thread → Route C
def test_steel_route_c():
    result = plan({
        "material":   "Steel",
        "features":   ["Thread", "Pocket"],
        "tolerance":  "0.01mm",
        "batch_size": 50
    })
    assert result["success"] == True
    assert result["selected_route"] == "Route_C"

# Test 3: Process steps exist
def test_process_steps_exist():
    result = plan({
        "material":   "Brass",
        "features":   ["Groove"],
        "tolerance":  "0.05mm",
        "batch_size": 10
    })
    assert result["success"] == True
    assert len(result["process_steps"]) > 0

# Test 4: Invalid input → failure
def test_invalid_input():
    result = plan({
        "material":   "Kryptonite",
        "features":   ["Hole"],
        "tolerance":  "0.02mm",
        "batch_size": 100
    })
    assert result["success"] == False

# Test 5: Tokens exist in result
def test_tokens_in_result():
    result = plan({
        "material":   "Aluminum",
        "features":   ["Hole"],
        "tolerance":  "0.02mm",
        "batch_size": 200
    })
    assert result["success"] == True
    assert len(result["tokens"]) > 0