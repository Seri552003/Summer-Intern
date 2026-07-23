# nsga2.py
# NSGA-II Multi-Objective Optimization
# Week 4 | LLM-CAPP Project
# UPDATED:
#   1. generate_valid_routes() ab list of dicts return karta hai
#      ({"steps": [...], "type": "LATHE_FIRST", "changeovers": 1})
#      — isliye population creation me r["steps"] use hota hai
#   2. Cost display INR me (₹)
#   3. Core algorithm (dominance, sorting, crowding) UNCHANGED

import random
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week3")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))

from agents import time_agent, cost_agent, energy_agent
from route_builder import generate_valid_routes

random.seed(42)


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
        t = time_agent(self.steps, self.material)
        c = cost_agent(self.steps, self.material, self.batch_size)
        e = energy_agent(self.steps, self.material)
        return (t, c, e)


# ── Dominance check ───────────────────────────────
def dominates(a: Individual, b: Individual) -> bool:
    a_obj = a.objectives
    b_obj = b.objectives
    not_worse = all(a_obj[i] <= b_obj[i] for i in range(3))
    strictly_better = any(a_obj[i] < b_obj[i] for i in range(3))
    return not_worse and strictly_better


# ── Non-Dominated Sorting ─────────────────────────
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


# ── Crowding Distance ─────────────────────────────
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
def run_nsga2(material: str, batch_size: int, features: list = None, max_routes: int = 15,
              machine_preference: str = "auto", include_llm: bool = True,
              tolerance: str = "0.05mm") -> list:
    """
    NSGA-II run karo aur Pareto-optimal routes return karo.
    machine_preference: "auto", "prefer_lathe", "prefer_milling"

    include_llm=True (default): LLM Planner se bhi ek candidate route generate
    karwaya jaata hai, FSM se validate hota hai (invalid ho toh Route Builder
    se self-correct), aur TABHI population mein add hota hai jab valid ho.
    "AI is verified, not trusted" — LLM ka route kabhi bina check ke population
    mein nahi jaata. Agar valid ho, ye Route Builder ke candidates ke SAATH
    fairly compete karta hai — agar genuinely behtar hai (Pareto-optimal),
    normal non_dominated_sort() ke through apne aap Front 0 mein aa jaayega.
    """
    features = features or []
    candidate_routes = generate_valid_routes(features, max_routes=max_routes, machine_preference=machine_preference)

    # Safety net
    if not candidate_routes:
        candidate_routes = [{"steps": ["Facing", "Inspection"], "type": "FALLBACK", "changeovers": 0}]

    population = [
        Individual(f"Route_{i+1}", r["steps"], material, batch_size)
        for i, r in enumerate(candidate_routes)
    ]

    # ═══════════════════════════════════════════════
    # LLM CANDIDATE — generate, verify, THEN include
    # ═══════════════════════════════════════════════
    llm_status = {"attempted": False, "generated": False, "valid": False,
                  "corrected": False, "included": False, "reason": ""}

    if include_llm and features:
        llm_status["attempted"] = True
        try:
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))
            from llm_planner import generate_process_plan
            from fsm_validator import validate_sequence, fix_sequence_with_builder

            llm_result = generate_process_plan(material, features, tolerance, batch_size)

            if not llm_result["success"]:
                llm_status["reason"] = "LLM generation failed (API/parsing issue)"
            else:
                llm_status["generated"] = True
                llm_steps = llm_result["steps"]
                fsm_check = validate_sequence(llm_steps)

                if fsm_check["valid"]:
                    llm_status["valid"] = True
                    population.append(Individual("Route_LLM", llm_steps, material, batch_size))
                    llm_status["included"] = True
                    llm_status["reason"] = "LLM route valid as-is — added to population"
                else:
                    # LLM route broke a rule — self-correct via Route Builder
                    corrected = fix_sequence_with_builder(features)
                    if corrected and validate_sequence(corrected)["valid"]:
                        llm_status["corrected"] = True
                        population.append(Individual("Route_LLM_corrected", corrected, material, batch_size))
                        llm_status["included"] = True
                        llm_status["reason"] = f"LLM route invalid ({fsm_check['errors'][:1]}) — self-corrected, included"
                    else:
                        llm_status["reason"] = "LLM route invalid and could not be self-corrected — excluded"

        except Exception as e:
            llm_status["reason"] = f"LLM path skipped: {e}"

    fronts = non_dominated_sort(population)

    for front in fronts:
        crowding_distance(population, front)

    pareto_front = [population[i] for i in fronts[0]]
    pareto_front_indices = set(fronts[0])

    # Kisi ko bhi curious ho, LLM ka fate pura transparent hai:
    llm_status["reached_pareto_front"] = any(
        population[i].route_name.startswith("Route_LLM") for i in pareto_front_indices
    )
    run_nsga2.last_llm_status = llm_status   # debug/inspection ke liye accessible

    return pareto_front


def print_pareto(pareto: list, material: str, batch_size: int):
    print(f"\n{'='*70}")
    print(f"  NSGA-II Results — {material}, Batch: {batch_size}")
    print(f"{'='*70}")
    print(f"  {'Route':<20} {'Time(min)':<12} {'Cost(₹)':<12} {'Energy(kWh)':<14} {'Steps'}")
    print(f"  {'─'*65}")
    for ind in sorted(pareto, key=lambda x: x.objectives[0]):
        t, c, e = ind.objectives
        has_co = "⚙" if "--- Machine Changeover ---" in ind.steps else " "
        tag = "🤖" if ind.route_name.startswith("Route_LLM") else "  "
        clean_steps = [s for s in ind.steps if s != "--- Machine Changeover ---"]
        print(f"  {tag}{ind.route_name:<18} {t:<12} ₹{c:<11} {e:<14} {has_co} {' → '.join(clean_steps)}")
    print(f"{'='*70}")
    print(f"  Pareto-optimal routes: {len(pareto)}")

    status = getattr(run_nsga2, "last_llm_status", None)
    if status and status["attempted"]:
        print(f"\n  🤖 LLM Integration Status:")
        print(f"     Generated       : {status['generated']}")
        print(f"     Valid as-is     : {status['valid']}")
        print(f"     Self-corrected  : {status['corrected']}")
        print(f"     Included in pop : {status['included']}")
        print(f"     Reached Pareto front : {status['reached_pareto_front']}")
        print(f"     Detail          : {status['reason']}")


if __name__ == "__main__":
    print("=== NSGA-II Multi-Objective Optimization (₹ INR) ===")

    print("\nTest 1: Thread + Fillet (asli bug case)")
    pareto1 = run_nsga2("Aluminum", 500, ["Thread", "Fillet"])
    print_pareto(pareto1, "Aluminum", 500)

    print("\nTest 2: Hole + Keyway + Taper (mixed machines)")
    pareto2 = run_nsga2("Steel", 50, ["Hole", "Keyway", "Taper"])
    print_pareto(pareto2, "Steel", 50)

    print("\nTest 3: Pocket + Chamfer (milling only)")
    pareto3 = run_nsga2("Brass", 100, ["Pocket", "Chamfer"])
    print_pareto(pareto3, "Brass", 100)