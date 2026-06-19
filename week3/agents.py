# agents.py
# Multi-Agent Evaluation System — 4 agents score each route
# Week 3 | LLM-CAPP Project

# ── Time Agent ⏱ ──────────────────────────────────
def time_agent(route_steps: list, material: str) -> float:
    """
    Har operation ka time estimate karo (minutes mein).
    Material ke hisaab se speed change hoti hai.
    """
    base_time = {
        "Facing": 5, "Center Drilling": 3, "Drilling": 8,
        "Reaming": 4, "Inspection": 5, "Boring": 10,
        "Threading": 7, "Chamfering": 3
    }
    
    # Material multiplier — hard material = zyada time
    material_factor = {
        "Aluminum": 1.0, "Steel": 1.4, "Brass": 1.1,
        "Copper": 0.9, "Titanium": 1.8, "Plastic": 0.7,
        "Cast Iron": 1.3
    }
    
    factor = material_factor.get(material, 1.0)
    total_time = sum(base_time.get(step, 5) for step in route_steps) * factor
    return round(total_time, 2)


# ── Cost Agent 💰 ──────────────────────────────────
def cost_agent(route_steps: list, material: str, batch_size: int) -> float:
    """
    Tool aur machine cost calculate karo ($ mein).
    """
    base_cost = {
        "Facing": 10, "Center Drilling": 8, "Drilling": 15,
        "Reaming": 12, "Inspection": 5, "Boring": 20,
        "Threading": 18, "Chamfering": 7
    }
    
    material_cost_factor = {
        "Aluminum": 1.0, "Steel": 1.5, "Brass": 1.2,
        "Copper": 1.3, "Titanium": 2.5, "Plastic": 0.6,
        "Cast Iron": 1.4
    }
    
    factor = material_cost_factor.get(material, 1.0)
    per_unit_cost = sum(base_cost.get(step, 10) for step in route_steps) * factor
    
    # Batch discount — zyada batch = thoda kam per-unit cost
    if batch_size > 500:
        per_unit_cost *= 0.85
    elif batch_size > 100:
        per_unit_cost *= 0.92
    
    return round(per_unit_cost, 2)


# ── Energy Agent ⚡ ─────────────────────────────────
def energy_agent(route_steps: list, material: str) -> float:
    """
    Power consumption calculate karo (kWh mein).
    """
    base_energy = {
        "Facing": 0.3, "Center Drilling": 0.2, "Drilling": 0.5,
        "Reaming": 0.25, "Inspection": 0.05, "Boring": 0.6,
        "Threading": 0.4, "Chamfering": 0.15
    }
    
    material_energy_factor = {
        "Aluminum": 1.0, "Steel": 1.6, "Brass": 1.1,
        "Copper": 0.95, "Titanium": 2.2, "Plastic": 0.5,
        "Cast Iron": 1.5
    }
    
    factor = material_energy_factor.get(material, 1.0)
    total_energy = sum(base_energy.get(step, 0.3) for step in route_steps) * factor
    return round(total_energy, 2)


# ── Efficiency Agent 📊 ────────────────────────────
def efficiency_agent(time_val: float, cost_val: float, energy_val: float) -> float:
    """
    Overall efficiency score (0-100). Kam time/cost/energy = zyada efficiency.
    """
    # Normalize karo — lower better, so inverse relationship
    time_score = max(0, 100 - time_val * 1.2)
    cost_score = max(0, 100 - cost_val * 0.8)
    energy_score = max(0, 100 - energy_val * 15)
    
    efficiency = (time_score + cost_score + energy_score) / 3
    return round(efficiency, 2)


# ── Master Evaluation Function ────────────────────
def evaluate_route(route_name: str, route_steps: list, material: str, batch_size: int) -> dict:
    """
    Ek route ko saare 4 agents se evaluate karo.
    """
    t = time_agent(route_steps, material)
    c = cost_agent(route_steps, material, batch_size)
    e = energy_agent(route_steps, material)
    eff = efficiency_agent(t, c, e)
    
    return {
        "route_name": route_name,
        "steps": route_steps,
        "time_min": t,
        "cost_usd": c,
        "energy_kwh": e,
        "efficiency_score": eff
    }


if __name__ == "__main__":
    test_route = ["Facing", "Drilling", "Reaming", "Inspection"]
    result = evaluate_route("Route_A", test_route, "Aluminum", 500)
    
    print("=== Route Evaluation Test ===")
    print(f"Route   : {result['route_name']}")
    print(f"Steps   : {result['steps']}")
    print(f"Time    : {result['time_min']} min")
    print(f"Cost    : ${result['cost_usd']}")
    print(f"Energy  : {result['energy_kwh']} kWh")
    print(f"Efficiency: {result['efficiency_score']}/100")