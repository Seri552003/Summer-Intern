# nsga2.py
# NSGA-II Multi-Objective Optimization
# Week 4 | LLM-CAPP Project
# UPDATED: "feature-based filtering" (fixed 77-route bank ko filter karna)
# poori tarah HATA diya gaya hai. Population ab route_builder.py (Dynamic
# Route Builder) se aata hai — jo khud completeness guarantee karta hai,
# isliye alag se filtering/duplicate FEATURE_TO_OPS dict ki zarurat nahi rahi.
#
# Core algorithm (dominance check, non-dominated sort, crowding distance)
# BILKUL UNCHANGED hai — inhe route kaha se aaya, farak nahi padta.

import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week3")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))

from agents import time_agent, cost_agent, energy_agent
from route_builder import generate_valid_routes

random.seed(42)


# ── Individual (ek solution) ────────────────────── (UNCHANGED)
class Individual:
    def __init__(self, route_name: str, steps: list, material: str, batch_size: int):
        self.route_name  = route_name
        self.steps       = steps
        self.material    = material
        self.batch_size  = batch_size
        self.objectives  = self._evaluate()
        self.rank        = 0
        self.crowding    = 0.0

    def _evaluate(self) -> tuple:
        t = time_agent(self.steps, self.material)
        c = cost_agent(self.steps, self.material, self.batch_size)
        e = energy_agent(self.steps, self.material)
        return (t, c, e)


# ── Dominance check ─────────────────────────────── (UNCHANGED)
def dominates(a: Individual, b: Individual) -> bool:
    a_obj = a.objectives
    b_obj = b.objectives
    not_worse = all(a_obj[i] <= b_obj[i] for i in range(3))
    strictly_better = any(a_obj[i] < b_obj[i] for i in range(3))
    return not_worse and strictly_better


# ── Non-Dominated Sorting ───────────────────────── (UNCHANGED)
def non_dominated_sort(population: list) -> list:
    fronts = [[]]
    dominated_by = {i: [] for i in range(len(population))}
    domination_count = {i: 0 for i in range(len(population))}

    for i, p in enumerate(population):
        for j, q in enumerate(population):
            if i == j:
                continue
            if dominates(p, q):
                dominated_by[i].append(j)
            elif dominates(q, p):
                domination_count[i] += 1

        if domination_count[i] == 0:
            population[i].rank = 0
            fronts[0].append(i)

    current_front = 0
    while fronts[current_front]:
        next_front = []
        for i in fronts[current_front]:
            for j in dominated_by[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    population[j].rank = current_front + 1
                    next_front.append(j)
        current_front += 1
        fronts.append(next_front)

    return fronts[:-1]


# ── Crowding Distance ───────────────────────────── (UNCHANGED)
def crowding_distance(population: list, front: list) -> None:
    n = len(front)
    if n <= 2:
        for i in front:
            population[i].crowding = float('inf')
        return

    for i in front:
        population[i].crowding = 0.0

    for obj_idx in range(3):
        sorted_front = sorted(front, key=lambda i: population[i].objectives[obj_idx])
        population[sorted_front[0]].crowding = float('inf')
        population[sorted_front[-1]].crowding = float('inf')

        obj_min = population[sorted_front[0]].objectives[obj_idx]
        obj_max = population[sorted_front[-1]].objectives[obj_idx]
        obj_range = obj_max - obj_min if obj_max != obj_min else 1e-9

        for k in range(1, n - 1):
            prev_val = population[sorted_front[k-1]].objectives[obj_idx]
            next_val = population[sorted_front[k+1]].objectives[obj_idx]
            population[sorted_front[k]].crowding += (next_val - prev_val) / obj_range


# ── Main NSGA-II Function ─────────────────────────
def run_nsga2(material: str, batch_size: int, features: list = None, max_routes: int = 15) -> list:
    """
    NSGA-II run karo aur Pareto-optimal routes return karo.

    Population ab route_builder.generate_valid_routes() se aata hai —
    Dynamic Route Builder khud completeness guarantee karta hai
    (Feature -> Operations mapping + Precedence rules se), isliye
    alag "relevant routes filter karo" step ki zarurat nahi rahi.
    """
    features = features or []
    candidate_routes = generate_valid_routes(features, max_routes=max_routes)

    # Safety net — agar kabhi khaali aaye (bahut rare case), trivial route use karo
    if not candidate_routes:
        candidate_routes = [["Facing", "Inspection"]]

    population = [
        Individual(f"Route_{i+1}", steps, material, batch_size)
        for i, steps in enumerate(candidate_routes)
    ]

    fronts = non_dominated_sort(population)

    for front in fronts:
        crowding_distance(population, front)

    pareto_front = [population[i] for i in fronts[0]]
    return pareto_front


def print_pareto(pareto: list, material: str, batch_size: int):
    print(f"\n{'='*65}")
    print(f"  NSGA-II Results — {material}, Batch: {batch_size}")
    print(f"{'='*65}")
    print(f"  {'Route':<12} {'Time(min)':<12} {'Cost($)':<10} {'Energy(kWh)':<14} {'Steps'}")
    print(f"  {'─'*60}")
    for ind in sorted(pareto, key=lambda x: x.objectives[0]):
        t, c, e = ind.objectives
        print(f"  {ind.route_name:<12} {t:<12} {c:<10} {e:<14} {' → '.join(ind.steps)}")
    print(f"{'='*65}")
    print(f"  Pareto-optimal routes: {len(pareto)}")


if __name__ == "__main__":
    print("=== NSGA-II Multi-Objective Optimization ===")

    print("\nTest 1: Thread + Fillet (asli bug case)")
    pareto1 = run_nsga2("Aluminum", 500, ["Thread", "Fillet"])
    print_pareto(pareto1, "Aluminum", 500)

    print("\nTest 2: Hole + Slot")
    pareto2 = run_nsga2("Steel", 50, ["Hole", "Slot"])
    print_pareto(pareto2, "Steel", 50)

    print("\nTest 3: Pocket + Chamfer")
    pareto3 = run_nsga2("Brass", 100, ["Pocket", "Chamfer"])
    print_pareto(pareto3, "Brass", 100)