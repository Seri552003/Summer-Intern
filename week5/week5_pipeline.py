# week5_pipeline.py
# Week 5 Main — Error Detection + Self-Correction Loop
# Week 5 | LLM-CAPP Project

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week3")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))

from tokenizer import tokenize
from nsga2 import run_nsga2
from fsm_validator import validate_sequence
from error_detector import detect_errors
from self_corrector import self_correct


def process_part_week5(part: dict) -> dict:
    """
    Complete Week 5 pipeline:
    Tokenize → NSGA-II → FSM Check → Error Detect → Self-Correct
    """
    print(f"\n{'═'*60}")
    print(f"  Part: {part.get('part_id','PART')} | {part['material']}")
    print(f"{'═'*60}")

    # Step 1: Tokenize
    token_result = tokenize(part)
    if not token_result["success"]:
        return {"success": False, "errors": token_result["errors"]}

    # Step 2: NSGA-II — best routes nikalo
    pareto = run_nsga2(part["material"], part["batch_size"])

    final_results = []

    for ind in pareto:
        steps = ind.steps

        # Step 3: FSM Check
        fsm_result = validate_sequence(steps)

        if fsm_result["valid"]:
            print(f"  ✅ {ind.route_name} → FSM Valid (no correction needed)")
            final_results.append({
                "route": ind.route_name,
                "steps": steps,
                "corrected": False,
                "objectives": ind.objectives
            })
        else:
            # Step 4: Error Detection
            error_report = detect_errors(steps)
            print(f"  ❌ {ind.route_name} → {len(error_report['errors'])} error(s) — attempting self-correction...")

            # Step 5: Self-Correction
            correction = self_correct(steps, verbose=False)

            if correction["success"]:
                print(f"  🔧 {ind.route_name} → Corrected: {' → '.join(correction['corrected'])}")
                final_results.append({
                    "route": ind.route_name,
                    "steps": correction["corrected"],
                    "corrected": True,
                    "correction_attempts": correction["attempts"],
                    "changes": correction["changes_made"],
                    "objectives": ind.objectives
                })
            else:
                print(f"  ⚠️  {ind.route_name} → Could not fix — skipped")

    # Best route select karo (lowest time)
    if final_results:
        best = min(final_results, key=lambda x: x["objectives"][0])
        t, c, e = best["objectives"]
        print(f"\n  🏆 Best: {best['route']} | Time:{t}min Cost:${c} Energy:{e}kWh")
        if best["corrected"]:
            print(f"  🔧 Was auto-corrected in {best.get('correction_attempts',0)} attempt(s)")

        return {
            "success": True,
            "part_id": part.get("part_id", "PART"),
            "material": part["material"],
            "best_route": best["route"],
            "steps": best["steps"],
            "time_min": t,
            "cost_usd": c,
            "energy_kwh": e,
            "was_corrected": best["corrected"]
        }

    return {"success": False, "errors": ["No valid routes found"]}


def run_week5_on_dataset(dataset_path: str) -> list:
    """Poore dataset pe Week 5 pipeline chalao."""
    with open(dataset_path, "r") as f:
        dataset = json.load(f)

    results = []
    corrected_count = 0

    print(f"\n🚀 Running Week 5 pipeline on {len(dataset)} parts...\n")

    for part in dataset[:10]:  # Pehle 10 parts pe test karo
        result = process_part_week5(part)
        results.append(result)
        if result.get("was_corrected"):
            corrected_count += 1

    print(f"\n{'='*60}")
    print(f"  WEEK 5 SUMMARY (10 parts)")
    print(f"{'='*60}")
    print(f"  ✅ Successful    : {sum(1 for r in results if r['success'])}")
    print(f"  🔧 Auto-corrected: {corrected_count}")
    print(f"  ❌ Failed        : {sum(1 for r in results if not r['success'])}")
    print(f"{'='*60}")

    return results


if __name__ == "__main__":
    print("=== Week 5 Pipeline: Error Detection + Self-Correction ===")

    # Single part test
    part1 = {
        "part_id": "PART_TEST",
        "material": "Aluminum",
        "features": ["Hole", "Slot"],
        "tolerance": "0.02mm",
        "batch_size": 500
    }
    result = process_part_week5(part1)

    # Dataset pe chalao
    dataset_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/parts_dataset.json")
    )
    if os.path.exists(dataset_path):
        run_week5_on_dataset(dataset_path)