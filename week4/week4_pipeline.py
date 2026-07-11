# week4_pipeline.py
# Week 4 Main — NSGA-II + FSM Validation combined
# Week 4 | LLM-CAPP Project
# FIXED: run_nsga2() ko part["features"] pass nahi ho rahe the — matlab
# har part, uske actual features se independent, sirf 1 trivial route
# ("Facing -> Inspection", koi machining nahi) pata tha. Ab features
# properly pass hote hain. Bonus: chunki features ab yahan available hain,
# FSM correction bhi basic fix_sequence() ki jagah fix_sequence_with_builder()
# use karta hai — zyada reliable (order-violations bhi fix kar sakta hai).

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week3")))

from tokenizer import tokenize
from fsm_validator import validate_sequence, fix_sequence_with_builder
from nsga2 import run_nsga2, print_pareto


def process_part_week4(part: dict) -> dict:
    """
    Part ko Week 4 pipeline se guzaro:
    Tokenize -> NSGA-II (feature-aware) -> FSM Validate -> Fix if needed
    """
    print(f"\n{'═'*60}")
    print(f"  Processing: {part.get('part_id', 'PART')} | {part['material']}")
    print(f"{'═'*60}")

    # Step 1: Tokenize (Week 1)
    token_result = tokenize(part)
    if not token_result["success"]:
        return {"success": False, "errors": token_result["errors"]}

    print(f"  Tokens : {token_result['tokens']}")
    print(f"  Labels : {token_result.get('token_labels', part['features'])}")

    # Step 2: NSGA-II Optimization (Week 4) — features ab explicitly pass ho rahe hain
    pareto = run_nsga2(part["material"], part["batch_size"], features=part["features"])
    print(f"\n  NSGA-II Pareto-optimal routes: {len(pareto)}")

    # Step 3: FSM Validate each Pareto route
    valid_routes = []
    invalid_routes = []

    for ind in pareto:
        fsm_result = validate_sequence(ind.steps)
        if fsm_result["valid"]:
            valid_routes.append(ind)
            print(f"  ✅ {ind.route_name} → FSM VALID")
        else:
            print(f"  ❌ {ind.route_name} → FSM INVALID")
            # Ab Route Builder-backed fix use karta hai (features available hain)
            fixed_steps = fix_sequence_with_builder(part["features"])
            fixed_result = validate_sequence(fixed_steps)
            if fixed_result["valid"]:
                ind.steps = fixed_steps
                valid_routes.append(ind)
                print(f"  🔧 {ind.route_name} → Fixed & VALID: {fixed_steps}")
            else:
                invalid_routes.append(ind)
                print(f"  ⚠️  {ind.route_name} → Could not fix")

    # Step 4: Best valid route select karo (lowest time)
    if valid_routes:
        best = min(valid_routes, key=lambda x: x.objectives[0])
        t, c, e = best.objectives
        print(f"\n  🏆 Best Valid Route: {best.route_name}")
        print(f"     Steps   : {' → '.join(best.steps)}")
        print(f"     Time    : {t} min | Cost: ${c} | Energy: {e} kWh")
        return {
            "success": True,
            "part_id": part.get("part_id", "PART"),
            "material": part["material"],
            "features": part["features"],
            "tokens": token_result["tokens"],
            "best_route": best.route_name,
            "steps": best.steps,
            "time_min": t,
            "cost_usd": c,
            "energy_kwh": e,
            "pareto_count": len(pareto),
            "valid_count": len(valid_routes)
        }
    else:
        return {"success": False, "errors": ["No valid routes found after FSM check"]}


if __name__ == "__main__":
    print("=== Week 4 Pipeline: NSGA-II + FSM Validation ===")

    part1 = {
        "part_id": "PART_001",
        "material": "Aluminum",
        "features": ["Hole", "Slot"],
        "tolerance": "0.02mm",
        "batch_size": 500
    }
    result1 = process_part_week4(part1)

    part2 = {
        "part_id": "PART_002",
        "material": "Steel",
        "features": ["Thread", "Pocket"],
        "tolerance": "0.01mm",
        "batch_size": 50
    }
    result2 = process_part_week4(part2)

    part3 = {
        "part_id": "PART_003",
        "material": "Titanium",
        "features": ["Hole", "Chamfer"],
        "tolerance": "0.005mm",
        "batch_size": 10
    }
    result3 = process_part_week4(part3)

    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    for r in [result1, result2, result3]:
        if r["success"]:
            print(f"  ✅ {r['part_id']} ({r['material']}, {r['features']}) → "
                  f"Time:{r['time_min']}min Cost:${r['cost_usd']} Energy:{r['energy_kwh']}kWh")
            print(f"     Steps: {' → '.join(r['steps'])}")
        else:
            print(f"  ❌ Failed: {r['errors']}")