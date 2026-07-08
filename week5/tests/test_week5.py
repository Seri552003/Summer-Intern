# test_week5.py
# pytest unit tests for Week 5 — Error Detection + Self-Correction
# Week 5 | LLM-CAPP Project

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../week4")))

from error_detector import detect_errors
from self_corrector import self_correct


# ── Error Detection Tests ─────────────────────────

# Test 1: Valid sequence mein koi error nahi
def test_no_errors_in_valid_sequence():
    seq = ["Facing", "Drilling", "Reaming", "Inspection"]
    result = detect_errors(seq)
    assert result["has_errors"] == False


# Test 2: Missing Facing detect hota hai
def test_detects_missing_facing():
    seq = ["Drilling", "Reaming", "Inspection"]
    result = detect_errors(seq)
    assert result["has_errors"] == True
    assert "MISSING_FACING" in result["error_types"]


# Test 3: Missing Inspection detect hota hai
def test_detects_missing_inspection():
    seq = ["Facing", "Drilling", "Reaming"]
    result = detect_errors(seq)
    assert result["has_errors"] == True
    assert "MISSING_INSPECTION" in result["error_types"]


# Test 4: Unknown operation detect hota hai
def test_detects_unknown_operation():
    seq = ["Facing", "LaserCut", "Inspection"]
    result = detect_errors(seq)
    assert result["has_errors"] == True
    assert "UNKNOWN_OPERATION" in result["error_types"]


# Test 5: Unknown operation fixable nahi hai
def test_unknown_operation_not_fixable():
    seq = ["Facing", "LaserCut", "Inspection"]
    result = detect_errors(seq)
    assert result["fixable"] == False


# Test 6: Empty sequence detect hota hai
def test_detects_empty_sequence():
    result = detect_errors([])
    assert result["has_errors"] == True
    assert "EMPTY_SEQUENCE" in result["error_types"]


# ── Self-Correction Tests ─────────────────────────

# Test 7: Missing Facing fix hoti hai
def test_corrects_missing_facing():
    result = self_correct(["Drilling", "Inspection"], verbose=False)
    assert result["success"] == True
    assert result["corrected"][0] == "Facing"


# Test 8: Missing Inspection fix hoti hai
def test_corrects_missing_inspection():
    result = self_correct(["Facing", "Drilling"], verbose=False)
    assert result["success"] == True
    assert result["corrected"][-1] == "Inspection"


# Test 9: Dono missing fix hote hain
def test_corrects_both_missing():
    result = self_correct(["Drilling", "Reaming"], verbose=False)
    assert result["success"] == True
    assert result["corrected"][0] == "Facing"
    assert result["corrected"][-1] == "Inspection"


# Test 10: Unknown operation fix nahi hoti
def test_cannot_fix_unknown_operation():
    result = self_correct(["Facing", "LaserCut", "Inspection"], verbose=False)
    assert result["success"] == False


# Test 11: Corrected sequence valid hoti hai
def test_corrected_sequence_is_valid():
    from fsm_validator import validate_sequence
    result = self_correct(["Drilling", "Reaming"], verbose=False)
    if result["success"]:
        fsm = validate_sequence(result["corrected"])
        assert fsm["valid"] == True


# Test 12: Already valid sequence unchanged rehti hai
def test_valid_sequence_unchanged():
    seq = ["Facing", "Drilling", "Inspection"]
    result = self_correct(seq, verbose=False)
    assert result["success"] == True
    assert result["attempts"] == 0