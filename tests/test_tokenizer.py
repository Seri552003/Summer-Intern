# test_tokenizer.py
# pytest unit tests for tokenizer
# Task 6 — Week 1 | LLM-CAPP Project

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tokenizer import tokenize

# Test 1: PPT ka exact example
def test_aluminum_hole_slot():
    result = tokenize({
        "material":   "Aluminum",
        "features":   ["Hole", "Slot"],
        "tolerance":  "0.02mm",
        "batch_size": 500
    })
    assert result["success"] == True
    assert 201 in result["tokens"]  # Aluminum
    assert 101 in result["tokens"]  # Hole
    assert 102 in result["tokens"]  # Slot
    assert 303 in result["tokens"]  # 0.02mm
    assert 403 in result["tokens"]  # medium_batch

# Test 2: Steel part
def test_steel_thread_pocket():
    result = tokenize({
        "material":   "Steel",
        "features":   ["Thread", "Pocket"],
        "tolerance":  "0.01mm",
        "batch_size": 50
    })
    assert result["success"] == True
    assert result["tokens"][0] == 202  # Steel sabse pehle
    assert 105 in result["tokens"]     # Thread
    assert 103 in result["tokens"]     # Pocket
    assert 302 in result["tokens"]     # 0.01mm
    assert 402 in result["tokens"]     # small_batch

# Test 3: Token order sahi hai
def test_token_order():
    result = tokenize({
        "material":   "Brass",
        "features":   ["Groove"],
        "tolerance":  "0.05mm",
        "batch_size": 10
    })
    tokens = result["tokens"]
    assert tokens[0] == 203  # Brass
    assert tokens[1] == 108  # Groove
    assert tokens[2] == 304  # 0.05mm
    assert tokens[3] == 401  # prototype

# Test 4: Invalid material
def test_invalid_material():
    result = tokenize({
        "material":   "Kryptonite",
        "features":   ["Hole"],
        "tolerance":  "0.02mm",
        "batch_size": 100
    })
    assert result["success"] == False
    assert len(result["errors"]) > 0
    assert result["tokens"] == []

# Test 5: Unknown feature warning
def test_unknown_feature_warning():
    result = tokenize({
        "material":   "Aluminum",
        "features":   ["Hole", "LaserCut"],
        "tolerance":  "0.02mm",
        "batch_size": 200
    })
    assert result["success"] == True
    assert 101 in result["tokens"]
    assert len(result["warnings"]) > 0

# Test 6: Mass production batch
def test_mass_production_batch():
    result = tokenize({
        "material":   "Steel",
        "features":   ["Face"],
        "tolerance":  "0.5mm",
        "batch_size": 5000
    })
    assert result["success"] == True
    assert 404 in result["tokens"]  # mass_production

# Test 7: Naya feature (vocab expansion ke baad) sahi tokenize ho raha hai
def test_new_feature_taper():
    result = tokenize({
        "material":   "Titanium",
        "features":   ["Taper", "Knurl"],
        "tolerance":  "0.005mm",
        "batch_size": 1
    })
    assert result["success"] == True
    assert 205 in result["tokens"]  # Titanium
    assert 111 in result["tokens"]  # Taper (naya)
    assert 112 in result["tokens"]  # Knurl (naya)
    assert 301 in result["tokens"]  # 0.005mm
    assert 401 in result["tokens"]  # prototype (batch=1)