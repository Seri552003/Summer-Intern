# full_pipeline.py
# Complete End-to-End Pipeline — Week 1 through Week 5
# Week 6 | LLM-CAPP Project
# FIXED:
#   1. run_nsga2() aur self_correct() dono ko part["features"] pass nahi ho
#      rahe the — same class ka bug jo run_pipeline.py, week4_pipeline.py,
#      week5_pipeline.py me mila tha (chautha instance).
#   2. "was_corrected" ek GLOBAL counter (`corrections`) se decide ho raha
#      tha, jo poore pareto-loop ke across accumulate hota tha — isliye agar
#      pareto set me KOI BHI ek route correction maangta, final best_result
#      bhi galti se "was_corrected: True" dikhata, chahe wo khud valid ho.
#      Ab per-individual flag use hota hai.
#   3. Route distribution "Route_1"/"Route_2" jaisे generic labels use karta
#      tha jo part-to-part unique nahi hote (misleading summary) — ab actual
#      operation-sequence se banta hai.

import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week3")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week5")))

from tokenizer import tokenize
from nsga2 import run_nsga2
from fsm_validator import validate_sequence
from error_detector import detect_errors
from self_corrector import self_correct
from agents import time_agent, cost_agent, energy_agent, efficiency_agent


def process_part_full(part: dict) -> dict:
    """
    Complete pipeline — Week 1 -> 2 -> 3 -> 4 -> 5
    """
    # Step 1: Tokenize (Week 1)
    token_result = tokenize(part)
    if not token_result["success"]:
        return {"success": False, "part_id": part.get("part_id"), "errors": token_result["errors"]}

    # Step 2: NSGA-II (Week 4) — features ab explicitly pass ho rahe hain
    pareto = run_nsga2(part["material"], part["batch_size"], features=part["features"])

    best_result = None

    for ind in pareto:
        steps = ind.steps
        individual_was_corrected = False  # PER-INDIVIDUAL flag, global counter nahi

        # Step 3: FSM Validate (Week 4)
        fsm = validate_sequence(steps)

        if not fsm["valid"]:
            # Step 4: Error detect + Self-correct (Week 5) — features pass karke
            correction = self_correct(steps, features=part["features"], verbose=False)
            if correction["success"]:
                steps = correction["corrected"]
                individual_was_corrected = True
            else:
                continue

        # Step 5: Agent scoring (Week 3)
        t = time_agent(steps, part["material"])
        c = cost_agent(steps, part["material"], part["batch_size"])
        e = energy_agent(steps, part["material"])
        eff = efficiency_agent(t, c, e)

        if best_result is None or eff > best_result["efficiency_score"]:
            best_result = {
                "route": ind.route_name,
                "steps": steps,
                "time_min": t,
                "cost_usd": c,
                "energy_kwh": e,
                "efficiency_score": eff,
                "was_corrected": individual_was_corrected
            }

    if best_result:
        return {
            "success": True,
            "part_id": part.get("part_id", "PART"),
            "material": part["material"],
            "features": part["features"],
            "tokens": token_result["tokens"],
            **best_result
        }

    return {"success": False, "part_id": part.get("part_id"), "errors": ["No valid route found"]}


def run_full_pipeline(dataset_path: str) -> dict:
    """
    Poore dataset pe complete pipeline chalao.
    """
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    print(f"\n🚀 Full Pipeline — Processing {len(dataset)} parts (Week 1→2→3→4→5)\n")

    results = []
    start = time.time()

    for part in dataset:
        result = process_part_full(part)
        results.append(result)

    elapsed = time.time() - start

    success = [r for r in results if r["success"]]
    failed  = [r for r in results if not r["success"]]
    corrected = [r for r in success if r.get("was_corrected")]

    avg_time = sum(r["time_min"] for r in success) / len(success) if success else 0
    avg_cost = sum(r["cost_usd"] for r in success) / len(success) if success else 0
    avg_energy = sum(r["energy_kwh"] for r in success) / len(success) if success else 0
    avg_eff = sum(r["efficiency_score"] for r in success) / len(success) if success else 0

    # Route distribution — route_name ("Route_1") part-to-part unique nahi hota,
    # isliye ACTUAL operation-sequence se distribution banate hain
    route_dist = {}
    for r in success:
        route_key = " -> ".join(r["steps"])
        route_dist[route_key] = route_dist.get(route_key, 0) + 1

    print(f"{'='*65}")
    print(f"  FULL PIPELINE SUMMARY — {len(dataset)} Parts")
    print(f"{'='*65}")
    print(f"  ✅ Successful      : {len(success)}")
    print(f"  🔧 Auto-corrected  : {len(corrected)}")
    print(f"  ❌ Failed          : {len(failed)}")
    print(f"\n  Average Time       : {avg_time:.2f} min")
    print(f"  Average Cost       : ${avg_cost:.2f}")
    print(f"  Average Energy     : {avg_energy:.2f} kWh")
    print(f"  Average Efficiency : {avg_eff:.2f}/100")
    print(f"\n  Route Distribution (top 10 by actual operation-sequence):")
    for route_key, count in sorted(route_dist.items(), key=lambda x: -x[1])[:10]:
        pct = count / len(success) * 100
        print(f"    {pct:5.1f}% ({count:3} parts) : {route_key}")
    print(f"\n  ⏱ Total Time       : {elapsed:.2f} seconds")
    print(f"{'='*65}")

    return {
        "results": results,
        "summary": {
            "total": len(dataset),
            "success": len(success),
            "failed": len(failed),
            "corrected": len(corrected),
            "avg_time": round(avg_time, 2),
            "avg_cost": round(avg_cost, 2),
            "avg_energy": round(avg_energy, 2),
            "avg_efficiency": round(avg_eff, 2),
            "route_distribution": route_dist,
            "pipeline_time_sec": round(elapsed, 2)
        }
    }


if __name__ == "__main__":
    dataset_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/parts_dataset.json")
    )

    output = run_full_pipeline(dataset_path)

    out_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/final_results.json")
    )
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n✅ Results saved: {out_path}")