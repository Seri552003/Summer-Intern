# nsga2.py
# NSGA-II Multi-Objective Optimization
# Week 4 | LLM-CAPP Project

import random
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week3")))

from agents import time_agent, cost_agent, energy_agent

random.seed(42)

# ── Route variations define karo ──────────────────
# Yeh NSGA-II ke liye candidate solutions hain
ROUTE_VARIANTS = {
    "Route_A1": ["Facing", "Center Drilling", "Drilling", "Reaming", "Inspection"],
    "Route_A2": ["Facing", "Drilling", "Reaming", "Inspection"],
    "Route_B1": ["Facing", "Drilling", "Boring", "Inspection"],
    "Route_B2": ["Facing", "Drilling", "Inspection"],
    "Route_C1": ["Facing", "Drilling", "Threading", "Chamfering", "Inspection"],
    "Route_C2": ["Facing", "Center Drilling", "Drilling", "Threading", "Inspection"],
}


# ── Individual (ek solution) ──────────────────────
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
        """3 objectives calculate karo — minimize sab."""
        t = time_agent(self.steps, self.material)
        c = cost_agent(self.steps, self.material, self.batch_size)
        e = energy_agent(self.steps, self.material)
        return (t, c, e)  # (time, cost, energy)


# ── Dominance check ───────────────────────────────
def dominates(a: Individual, b: Individual) -> bool:
    """
    'a' dominates 'b' if:
    - a is no worse than b in all objectives
    - a is strictly better in at least one objective
    """
    a_obj = a.objectives
    b_obj = b.objectives
    not_worse = all(a_obj[i] <= b_obj[i] for i in range(3))
    strictly_better = any(a_obj[i] < b_obj[i] for i in range(3))
    return not_worse and strictly_better


# ── Non-Dominated Sorting ─────────────────────────
def non_dominated_sort(population: list) -> list:
    """Population ko Pareto fronts mein sort karo."""
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

    return fronts[:-1]  # last empty front remove karo


# ── Crowding Distance ─────────────────────────────
def crowding_distance(population: list, front: list) -> None:
    """Diversity maintain karne ke liye crowding distance calculate karo."""
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
def run_nsga2(material: str, batch_size: int) -> list:
    """
    NSGA-II run karo aur Pareto-optimal routes return karo.
    Returns list of best Individual objects (Pareto front 0).
    """
    # Population banao
    population = [
        Individual(name, steps, material, batch_size)
        for name, steps in ROUTE_VARIANTS.items()
    ]

    # Non-dominated sort karo
    fronts = non_dominated_sort(population)

    # Crowding distance calculate karo
    for front in fronts:
        crowding_distance(population, front)

    # Pareto front (rank 0) return karo
    pareto_front = [population[i] for i in fronts[0]]
    return pareto_front


def print_pareto(pareto: list, material: str, batch_size: int):
    """Pareto front print karo."""
    print(f"\n{'='*65}")
    print(f"  NSGA-II Results — {material}, Batch: {batch_size}")
    print(f"{'='*65}")
    print(f"  {'Route':<10} {'Time(min)':<12} {'Cost($)':<10} {'Energy(kWh)':<14} {'Steps'}")
    print(f"  {'─'*60}")
    for ind in sorted(pareto, key=lambda x: x.objectives[0]):
        t, c, e = ind.objectives
        print(f"  {ind.route_name:<10} {t:<12} {c:<10} {e:<14} {' → '.join(ind.steps)}")
    print(f"{'='*65}")
    print(f"  Total Pareto-optimal routes: {len(pareto)}")
    print(f"  (These routes cannot be improved in one objective")
    print(f"   without worsening another — trade-off solutions)")


if __name__ == "__main__":
    print("=== NSGA-II Multi-Objective Optimization ===")

    # Test 1: Aluminum, medium batch
    pareto1 = run_nsga2("Aluminum", 500)
    print_pareto(pareto1, "Aluminum", 500)

    # Test 2: Steel, small batch
    pareto2 = run_nsga2("Steel", 50)
    print_pareto(pareto2, "Steel", 50)