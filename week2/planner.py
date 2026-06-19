# planner.py
# Main Planner — Week 2 | LLM-CAPP Project

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))

from tokenizer import tokenize
from routes import ALL_ROUTES, print_all_routes

def select_route(labels: list) -> str:
    """
    Features dekhkar best route select karo.
    """
    features = [l.lower() for l in labels]
    
    if "thread" in features:
        return "Route_C"
    elif "slot" in features or "hole" in features:
        return "Route_A"
    else:
        return "Route_B"

def plan(part_json: dict) -> dict:
    """
    Part JSON lekar complete process plan banao.
    """
    # Step 1: Tokenize karo
    token_result = tokenize(part_json)
    
    if not token_result["success"]:
        return {
            "success": False,
            "errors": token_result["errors"]
        }
    
    # Step 2: Route select karo
    selected_route = select_route(token_result["token_labels"])
    route_steps = ALL_ROUTES[selected_route]
    
    return {
        "success": True,
        "tokens": token_result["tokens"],
        "token_labels": token_result["token_labels"],
        "selected_route": selected_route,
        "process_steps": route_steps
    }

def print_plan(result: dict):
    if not result["success"]:
        print("❌ FAILED:", result["errors"])
        return
    
    print(f"\n{'='*50}")
    print(f"  ✅ Process Plan Generated!")
    print(f"{'='*50}")
    print(f"  Tokens  : {result['tokens']}")
    print(f"  Labels  : {result['token_labels']}")
    print(f"  Route   : {result['selected_route']}")
    print(f"\n  Process Steps:")
    for i, step in enumerate(result["process_steps"], 1):
        print(f"    {i}. {step}")

if __name__ == "__main__":
    # PPT wala example
    part1 = {
        "material":   "Aluminum",
        "features":   ["Hole", "Slot"],
        "tolerance":  "0.02mm",
        "batch_size": 500
    }
    print("─── Part 1: Aluminum Hole+Slot ───")
    print_plan(plan(part1))

    # Steel Thread part
    part2 = {
        "material":   "Steel",
        "features":   ["Thread", "Pocket"],
        "tolerance":  "0.01mm",
        "batch_size": 50
    }
    print("\n─── Part 2: Steel Thread+Pocket ───")
    print_plan(plan(part2))