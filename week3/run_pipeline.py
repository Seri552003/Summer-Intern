# run_pipeline.py
# End-to-End Pipeline: Week 1 (Tokenizer) → Week 2 (LLM Planner) → Week 3 (Multi-Agent Eval)
# Dataset ke saare parts ko process karta hai

import sys
import os
import json
import time

# Week 1, 2, 3 ke modules import karo
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "")))

from tokenizer import tokenize           # Week 1
from routes import ALL_ROUTES            # Week 2
from multi_agent_eval import evaluate_all_routes, find_best_route   # Week 3


def load_dataset(path: str) -> list:
    """Synthetic dataset load karo JSON se."""
    with open(path, "r") as f:
        return json.load(f)


def process_part(part: dict) -> dict:
    """
    Ek part ko pure pipeline se guzaro:
    Tokenize → Routes Evaluate → Best Route Select
    """
    # Step 1: Week 1 — Tokenize
    token_result = tokenize({
        "material": part["material"],
        "features": part["features"],
        "tolerance": part["tolerance"],
        "batch_size": part["batch_size"]
    })

    if not token_result["success"]:
        return {
            "part_id": part["part_id"],
            "success": False,
            "errors": token_result["errors"]
        }

    # Step 2 & 3: Week 2 routes + Week 3 multi-agent evaluation
    eval_results = evaluate_all_routes(part["material"], part["batch_size"])
    best = find_best_route(eval_results, "efficiency")

    return {
        "part_id": part["part_id"],
        "success": True,
        "material": part["material"],
        "tokens": token_result["tokens"],
        "best_route": best["route_name"],
        "time_min": best["time_min"],
        "cost_usd": best["cost_usd"],
        "energy_kwh": best["energy_kwh"],
        "efficiency_score": best["efficiency_score"]
    }


def run_full_pipeline(dataset_path: str) -> list:
    """Saare parts ko process karo aur results list return karo."""
    dataset = load_dataset(dataset_path)
    results = []

    print(f"\n🚀 Processing {len(dataset)} parts through full pipeline...\n")

    for part in dataset:
        result = process_part(part)
        results.append(result)

    return results


def print_summary(results: list):
    """Summary statistics print karo."""
    success_count = sum(1 for r in results if r["success"])
    fail_count = len(results) - success_count

    print(f"{'='*60}")
    print(f"  PIPELINE SUMMARY")
    print(f"{'='*60}")
    print(f"  Total Parts     : {len(results)}")
    print(f"  ✅ Successful   : {success_count}")
    print(f"  ❌ Failed       : {fail_count}")

    if success_count > 0:
        avg_time = sum(r["time_min"] for r in results if r["success"]) / success_count
        avg_cost = sum(r["cost_usd"] for r in results if r["success"]) / success_count
        avg_energy = sum(r["energy_kwh"] for r in results if r["success"]) / success_count
        avg_eff = sum(r["efficiency_score"] for r in results if r["success"]) / success_count

        print(f"\n  Average Time    : {avg_time:.2f} min")
        print(f"  Average Cost    : ${avg_cost:.2f}")
        print(f"  Average Energy  : {avg_energy:.2f} kWh")
        print(f"  Average Efficiency : {avg_eff:.2f}/100")

        # Route distribution
        route_counts = {}
        for r in results:
            if r["success"]:
                route_counts[r["best_route"]] = route_counts.get(r["best_route"], 0) + 1

        print(f"\n  Best Route Distribution:")
        for route, count in sorted(route_counts.items()):
            print(f"    {route} : {count} parts ({count/success_count*100:.1f}%)")

    print(f"{'='*60}")


def save_results(results: list, path: str):
    """Pipeline results ko JSON mein save karo."""
    with open(path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✅ Results saved: {path}")


if __name__ == "__main__":
    start_time = time.time()

    dataset_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/parts_dataset.json")
    )

    results = run_full_pipeline(dataset_path)
    print_summary(results)

    elapsed = time.time() - start_time
    print(f"\n⏱ Total Pipeline Time: {elapsed:.2f} seconds")

    # Save results
    output_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/pipeline_results.json")
    )
    save_results(results, output_path)

    # Show first 3 results as sample
    print(f"\n📋 Sample Results (first 3):")
    for r in results[:3]:
        if r["success"]:
            print(f"  {r['part_id']} ({r['material']}) → {r['best_route']} | "
                  f"Time:{r['time_min']}min Cost:${r['cost_usd']} Eff:{r['efficiency_score']}")
        else:
            print(f"  {r['part_id']} → FAILED: {r['errors']}")