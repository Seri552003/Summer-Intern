# multi_agent_eval.py
# Saare Routes ko evaluate karke compare karo
# Week 3 | LLM-CAPP Project (MAIN FILE)

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))

from routes import ALL_ROUTES
from agents import evaluate_route

def evaluate_all_routes(material: str, batch_size: int) -> list:
    """
    Saare available routes ko evaluate karke list return karo.
    """
    results = []
    for route_name, steps in ALL_ROUTES.items():
        result = evaluate_route(route_name, steps, material, batch_size)
        results.append(result)
    return results


def print_comparison(results: list):
    """
    Saare routes ko ek table jaisa format mein print karo.
    """
    print(f"\n{'='*75}")
    print(f"  {'Route':<10} {'Time(min)':<12} {'Cost($)':<10} {'Energy(kWh)':<14} {'Efficiency':<10}")
    print(f"{'='*75}")
    for r in results:
        print(f"  {r['route_name']:<10} {r['time_min']:<12} {r['cost_usd']:<10} {r['energy_kwh']:<14} {r['efficiency_score']:<10}")
    print(f"{'='*75}")


def find_best_route(results: list, priority: str = "efficiency") -> dict:
    """
    Best route nikalo based on priority:
    'time', 'cost', 'energy', ya 'efficiency'
    """
    if priority == "time":
        return min(results, key=lambda r: r["time_min"])
    elif priority == "cost":
        return min(results, key=lambda r: r["cost_usd"])
    elif priority == "energy":
        return min(results, key=lambda r: r["energy_kwh"])
    else:  # efficiency — higher is better
        return max(results, key=lambda r: r["efficiency_score"])


if __name__ == "__main__":
    material = "Aluminum"
    batch_size = 500
    
    print(f"\n📦 Part: {material}, Batch Size: {batch_size}")
    
    results = evaluate_all_routes(material, batch_size)
    print_comparison(results)
    
    print("\n🏆 Best Routes by Priority:")
    print(f"  Fastest        : {find_best_route(results, 'time')['route_name']}")
    print(f"  Cheapest       : {find_best_route(results, 'cost')['route_name']}")
    print(f"  Most Energy-Efficient : {find_best_route(results, 'energy')['route_name']}")
    print(f"  Best Overall   : {find_best_route(results, 'efficiency')['route_name']}")