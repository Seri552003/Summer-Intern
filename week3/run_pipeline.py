# run_pipeline.py
# End-to-End Pipeline: Week 1 (Tokenizer) -> Week 2 (Route Builder) -> Week 3 (Multi-Agent Eval)
# Dataset ke saare parts ko process karta hai
# FIXED: process_part() features tokenize karne ke baad evaluate_all_routes() ko
# PASS hi nahi karta tha — isliye har part, uske actual features se independent,
# legacy (feature-blind, saare 77 routes) mode me evaluate ho raha tha. Yehi wo
# root cause hai jiski wajah se pipeline ka route-distribution hamesha same
# route pe converge karta tha ("100% Route_A" jaisa symptom).

import sys
import os
import json
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "")))

from tokenizer import tokenize                                      # Week 1
from multi_agent_eval import evaluate_all_routes, find_best_route   # Week 3 (route_builder.py internally use karta hai)


def load_dataset(path: str) -> list:
    """Synthetic dataset load karo JSON se."""
    with open(path, "r") as f:
        return json.load(f)


def process_part(part: dict) -> dict:
    """
    Ek part ko pure pipeline se guzaro:
    Tokenize -> Feature-aware Route Evaluation -> Best Route Select
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

    # Step 2 & 3: features ab explicitly pass ho rahe hain -> route_builder.py
    # sirf is part ke liye RELEVANT + COMPLETE routes evaluate karega
    eval_results = evaluate_all_routes(
        part["material"], part["batch_size"], features=part["features"]
    )

    if not eval_results:
        return {
            "part_id": part["part_id"],
            "success": False,
            "errors": [f"Koi valid route nahi ban paya features ke liye: {part['features']}"]
        }

    best = find_best_route(eval_results, "efficiency")

    return {
        "part_id": part["part_id"],
        "success": True,
        "material": part["material"],
        "features": part["features"],
        "tokens": token_result["tokens"],
        "best_route": best["route_name"],
        "route_steps": best["steps"],
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

        # Route distribution — route_name (jaise "Route_1") har part ke apne
        # candidate-list me sirf ek POSITION hai, part-to-part unique identifier
        # nahi. Isliye distribution ACTUAL route steps se banate hain, taaki
        # genuinely pata chale kitne parts same/alag operation-sequence share
        # kar rahe hain (naam ke label se confuse na ho).
        route_counts = {}
        for r in results:
            if r["success"]:
                route_key = " -> ".join(r["route_steps"])
                route_counts[route_key] = route_counts.get(route_key, 0) + 1

        print(f"\n  Best Route Distribution (by actual operation-sequence):")
        for route_key, count in sorted(route_counts.items(), key=lambda x: -x[1]):
            print(f"    {count/success_count*100:5.1f}% ({count} parts) : {route_key}")

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

    output_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/pipeline_results.json")
    )
    save_results(results, output_path)

    print(f"\n📋 Sample Results (first 3):")
    for r in results[:3]:
        if r["success"]:
            print(f"  {r['part_id']} ({r['material']}, {r['features']}) → {r['best_route']} | "
                  f"Time:{r['time_min']}min Cost:${r['cost_usd']} Eff:{r['efficiency_score']}")
        else:
            print(f"  {r['part_id']} → FAILED: {r['errors']}")