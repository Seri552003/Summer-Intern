# test_agents.py
# pytest unit tests for multi-agent evaluation
# Week 3 | LLM-CAPP Project

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import agents
from agents import time_agent, cost_agent, energy_agent, efficiency_agent, evaluate_route
from multi_agent_eval import evaluate_all_routes, find_best_route
from routes import ALL_ROUTES   # week2 is put on sys.path by multi_agent_eval


# Test 1: Time agent positive value deta hai
def test_time_agent_positive():
    steps = ["Facing", "Drilling", "Inspection"]
    result = time_agent(steps, "Aluminum")
    assert result > 0


# Test 2: Steel zyada time leta hai Aluminum se (hard material)
def test_steel_slower_than_aluminum():
    steps = ["Facing", "Drilling"]
    al_time = time_agent(steps, "Aluminum")
    steel_time = time_agent(steps, "Steel")
    assert steel_time > al_time


# Test 3: Cost agent positive value deta hai
def test_cost_agent_positive():
    steps = ["Facing", "Drilling", "Inspection"]
    result = cost_agent(steps, "Aluminum", 100)
    assert result > 0


# Test 4: Bulk batch discount lagta hai
def test_bulk_discount():
    steps = ["Facing", "Drilling"]
    small_batch_cost = cost_agent(steps, "Aluminum", 10)
    large_batch_cost = cost_agent(steps, "Aluminum", 600)
    assert large_batch_cost < small_batch_cost


# Test 5: Energy agent positive value deta hai
def test_energy_agent_positive():
    steps = ["Facing", "Drilling", "Inspection"]
    result = energy_agent(steps, "Aluminum")
    assert result > 0


# Test 6: Efficiency score 0-100 ke beech hai
def test_efficiency_score_range():
    score = efficiency_agent(20, 40, 1.0)
    assert 0 <= score <= 100


# Test 7: evaluate_route complete dict deta hai
def test_evaluate_route_complete():
    steps = ["Facing", "Drilling", "Inspection"]
    result = evaluate_route("Route_A", steps, "Aluminum", 500)
    assert "time_min" in result
    assert "cost_inr" in result   # costs are reported in INR (key was cost_usd before the INR migration)
    assert "energy_kwh" in result
    assert "efficiency_score" in result


# Test 8: Legacy mode (no features) evaluates every fixed route in the registry
def test_evaluate_all_routes():
    results = evaluate_all_routes("Aluminum", 500)
    assert len(results) == len(ALL_ROUTES) > 0
    assert all("cost_inr" in r and "steps" in r for r in results)


# Test 9: Best route by efficiency milta hai
def test_find_best_route_efficiency():
    results = evaluate_all_routes("Aluminum", 500)
    best = find_best_route(results, "efficiency")
    assert best is not None
    assert "route_name" in best


# Test 10: Best route by cost sabse sasta hota hai
def test_find_best_route_cost():
    results = evaluate_all_routes("Steel", 50)
    best = find_best_route(results, "cost")
    min_cost = min(r["cost_inr"] for r in results)
    assert best["cost_inr"] == min_cost


# Test 11: Feature-aware mode (the RECOMMENDED path) works. generate_valid_routes()
# returns dicts, and evaluate_all_routes() must unwrap them to plain step lists.
def test_evaluate_all_routes_with_features():
    results = evaluate_all_routes("Aluminum", 500, features=["Hole", "Slot"])
    assert len(results) > 0
    for r in results:
        assert isinstance(r["steps"], list)
        assert r["steps"][0] == "Facing" and r["steps"][-1] == "Inspection"
        assert r["time_min"] > 0 and r["cost_inr"] > 0


# Test 12: Exchange rate is defined once; penalties derive from it
def test_exchange_rate_single_source_of_truth():
    assert agents.USD_TO_INR > 0
    assert agents.CHANGEOVER_COST_INR == round(15 * agents.USD_TO_INR)
    assert agents.TOOL_CHANGE_COST_INR == round(2 * agents.USD_TO_INR)
    assert agents.POSITION_CHANGE_COST_INR == round(1 * agents.USD_TO_INR)


# Test 13: Cost tables are derived from the same constant (no stale literals)
def test_cost_tables_follow_exchange_rate():
    assert agents._BASE_COST["Facing"] == round(agents._BASE_COST_USD["Facing"] * agents.USD_TO_INR)
    assert agents._COST_PER_MIN["Facing"] == agents._inr(160)
    # every operation with a base cost also has a per-minute rate
    assert set(agents._BASE_COST) == set(agents._COST_PER_MIN)

