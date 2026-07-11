# route_builder.py
# Dynamic Route Builder — Core Algorithm
# Feature_vocab.py (Step 1) + precedence_graph.py (Step 2) use karke,
# kisi bhi feature-combination ke liye khud COMPLETE + VALID routes banata hai.
#
# Guarantee: Route "incomplete" ho hi nahi sakta — completeness
# CONSTRUCTION se aati hai, filtering se nahi. Isi wajah se purana
# Thread+Fillet wala bug (Fillet ka operation missing) yahan
# structurally impossible hai.

import random
from itertools import product

import feature_vocab as fv
import precedence_graph as pg


# ════════════════════════════════════════════════════
# STEP 1+: Features se operation-combinations nikalo
# ════════════════════════════════════════════════════

def get_operation_combinations(features: list) -> list:
    """
    Har feature ke alternative chains ka cartesian product banao,
    phir har combination ka UNION nikaalo (overlap wale operations
    ek hi baar count honge, jaise Hole+Counterbore dono "Drilling" maangte hain).

    Returns: list of sets — har set ek possible "required operations" combination hai.
    """
    if not features:
        return [set()]

    per_feature_alternatives = [fv.get_operations_for_feature(f) for f in features]

    combos = []
    seen = set()
    for combo in product(*per_feature_alternatives):
        merged = set()
        for chain in combo:
            merged.update(chain)
        key = frozenset(merged)
        if key not in seen:
            seen.add(key)
            combos.append(merged)

    return combos


# ════════════════════════════════════════════════════
# STEP 2+: Precedence rules se valid ordering(s) nikalo
# ════════════════════════════════════════════════════

def _topological_orderings(operations: set, num_variants: int = 3, max_attempts: int = 20) -> list:
    """
    Randomized Kahn's algorithm — operations ke liye multiple DIFFERENT
    valid topological orderings nikalta hai (precedence_graph.py ke rules follow karte hue).

    Returns: list of lists — har list ek valid ordering hai.
    """
    relevant_edges = [
        (a, b) for a, b in pg.PRECEDENCE_EDGES
        if a in operations and b in operations
    ]

    results = []
    attempts = 0
    while len(results) < num_variants and attempts < max_attempts:
        attempts += 1

        in_degree = {op: 0 for op in operations}
        graph = {op: [] for op in operations}
        for a, b in relevant_edges:
            graph[a].append(b)
            in_degree[b] += 1

        available = [op for op in operations if in_degree[op] == 0]
        in_degree_copy = in_degree.copy()
        order = []

        while available:
            random.shuffle(available)
            node = available.pop()
            order.append(node)
            for neighbor in graph[node]:
                in_degree_copy[neighbor] -= 1
                if in_degree_copy[neighbor] == 0:
                    available.append(neighbor)

        if len(order) == len(operations) and order not in results:
            results.append(order)

    return results


# ════════════════════════════════════════════════════
# STEP 3: Poora route construct karo (Facing + ordering + Inspection)
# ════════════════════════════════════════════════════

def build_routes(features: list, max_routes: int = 5) -> list:
    """
    Diye gaye features ke liye multiple candidate COMPLETE routes banao.
    Har route: [Facing, ...ordered operations..., Inspection]
    """
    combos = get_operation_combinations(features)

    all_routes = []
    seen_routes = set()

    for combo in combos:
        # ALWAYS_FIRST/ALWAYS_LAST (Facing/Inspection) explicitly prepend/append
        # hote hain (neeche). Agar koi feature (jaise "Face") khud apne chain me
        # "Facing" maangta hai, toh use yahan se nikaal do — warna route me
        # "Facing" do baar aa jaayega (ek combo se, ek universal-rule se).
        sortable_combo = combo - {pg.ALWAYS_FIRST, pg.ALWAYS_LAST}
        orderings = _topological_orderings(sortable_combo, num_variants=2)
        for order in orderings:
            route = [pg.ALWAYS_FIRST] + order + [pg.ALWAYS_LAST]
            key = tuple(route)
            if key not in seen_routes:
                seen_routes.add(key)
                all_routes.append(route)
        if len(all_routes) >= max_routes:
            break

    return all_routes[:max_routes]


# ════════════════════════════════════════════════════
# COMPLETENESS CHECK — hard constraint, koi bhi route isse fail nahi hona chahiye
# ════════════════════════════════════════════════════

def is_complete(route: list, features: list) -> bool:
    """
    Har feature ke liye check karo — uska KAM SE KAM EK alternative chain
    poori tarah route me maujood hai. Agar koi feature resolve nahi hua,
    route incomplete hai.
    """
    route_set = set(route)
    for feature in features:
        alternatives = fv.get_operations_for_feature(feature)
        if not any(set(alt).issubset(route_set) for alt in alternatives):
            return False
    return True


# ════════════════════════════════════════════════════
# MAIN ENTRY POINT — ye function baaki system (NSGA-II, Self-Correction) use karega
# ════════════════════════════════════════════════════

def generate_valid_routes(features: list, max_routes: int = 5) -> list:
    """
    Route Builder ka main entry point.
    Guarantee: return hone wala har route (a) COMPLETE hai (b) precedence-VALID hai.
    """
    candidates = build_routes(features, max_routes=max_routes * 3)

    final_routes = []
    for route in candidates:
        if is_complete(route, features):
            valid, _ = pg.validate_order(route)
            if valid:
                final_routes.append(route)
        if len(final_routes) >= max_routes:
            break

    return final_routes


if __name__ == "__main__":
    print("=== Test 1: Simple single feature ===")
    routes1 = generate_valid_routes(["Hole"])
    for r in routes1:
        print(" ", " -> ".join(r))

    print("\n=== Test 2: THE ORIGINAL BUG CASE — Thread + Fillet ===")
    print("(Purane system me ye Fillet-less incomplete route deta tha)")
    routes2 = generate_valid_routes(["Thread", "Fillet"])
    for r in routes2:
        complete = is_complete(r, ["Thread", "Fillet"])
        print(f"  Complete={complete} | {' -> '.join(r)}")

    print("\n=== Test 3: Multiple features, multiple valid routes ===")
    routes3 = generate_valid_routes(["Hole", "Counterbore", "Chamfer"], max_routes=4)
    for r in routes3:
        print(" ", " -> ".join(r))
    print(f"Total distinct routes generated: {len(routes3)}")

    print("\n=== Test 4: Naya feature (Taper + Knurl) jo legacy 77 me kabhi tha hi nahi ===")
    routes4 = generate_valid_routes(["Taper", "Knurl"])
    for r in routes4:
        print(" ", " -> ".join(r))