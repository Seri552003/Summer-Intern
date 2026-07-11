# agents.py
# Multi-Agent Evaluation System — 4 agents score each route
# Week 3 | LLM-CAPP Project
# UPDATED: base_time/base_cost/base_energy ab saare 41 operations cover karte hain
#          (routes.py ke ALL_OPERATIONS registry se match). "Threading" ko
#          "External Threading" kiya gaya (canonical naam se match karne ke liye).
#
# NOTE: Naye 33 operations ke values REALISTIC ESTIMATES hain (domain-knowledge
# based), asli measured data nahi. Agar tumhare paas real machining data/
# Sir se reference values hain, toh unse replace kar dena — abhi ke liye
# ye placeholder ki jagah "sabko same default milna" se kaafi behtar hain.

# ── Time Agent ⏱ ──────────────────────────────────
def time_agent(route_steps: list, material: str) -> float:
    """
    Har operation ka time estimate karo (minutes mein).
    Material ke hisaab se speed change hoti hai.
    """
    base_time = {
        # ── Pehle se the (unchanged) ──
        "Facing": 5, "Center Drilling": 3, "Drilling": 8,
        "Reaming": 4, "Inspection": 5, "Boring": 10,
        "Chamfering": 3,
        # ── Rename: "Threading" -> "External Threading" ──
        "External Threading": 7,
        # ── Naye — Lathe ──
        "Plain/Cylindrical Turning": 9, "Taper Turning": 10, "Step Turning": 9,
        "Grooving/Necking": 6, "Parting-off": 4, "Knurling": 3, "Forming": 6,
        "Internal Grooving": 7, "Tapping": 5, "Counterboring": 4,
        "Countersinking": 3, "Contour Turning": 12, "Undercutting": 4,
        "Eccentric Turning": 11, "Polishing/Burnishing": 6,
        # ── Naye — Milling ──
        "Face Milling": 6, "Slab/Peripheral Milling": 10, "Surface Contouring": 15,
        "Slot Milling": 7, "T-Slot Milling": 9, "Dovetail Milling": 8,
        "Woodruff Keyway Milling": 5, "Pocket Milling": 9, "Profile Milling": 8,
        "Spotfacing": 3, "Corner Rounding/Filleting": 4, "Gear/Spline Milling": 14,
        "Thread Milling": 8, "Angular Milling": 7, "Gang Milling": 6,
        "Form Milling": 9, "Helical Milling": 11, "Engraving": 6,
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
        # ── Pehle se the (unchanged) ──
        "Facing": 10, "Center Drilling": 8, "Drilling": 15,
        "Reaming": 12, "Inspection": 5, "Boring": 20,
        "Chamfering": 7,
        # ── Rename: "Threading" -> "External Threading" ──
        "External Threading": 18,
        # ── Naye — Lathe ──
        "Plain/Cylindrical Turning": 16, "Taper Turning": 17, "Step Turning": 16,
        "Grooving/Necking": 13, "Parting-off": 9, "Knurling": 8, "Forming": 14,
        "Internal Grooving": 15, "Tapping": 12, "Counterboring": 10,
        "Countersinking": 9, "Contour Turning": 22, "Undercutting": 10,
        "Eccentric Turning": 20, "Polishing/Burnishing": 11,
        # ── Naye — Milling ──
        "Face Milling": 12, "Slab/Peripheral Milling": 18, "Surface Contouring": 28,
        "Slot Milling": 14, "T-Slot Milling": 17, "Dovetail Milling": 16,
        "Woodruff Keyway Milling": 11, "Pocket Milling": 16, "Profile Milling": 15,
        "Spotfacing": 8, "Corner Rounding/Filleting": 9, "Gear/Spline Milling": 26,
        "Thread Milling": 17, "Angular Milling": 14, "Gang Milling": 13,
        "Form Milling": 17, "Helical Milling": 20, "Engraving": 10,
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
        # ── Pehle se the (unchanged) ──
        "Facing": 0.3, "Center Drilling": 0.2, "Drilling": 0.5,
        "Reaming": 0.25, "Inspection": 0.05, "Boring": 0.6,
        "Chamfering": 0.15,
        # ── Rename: "Threading" -> "External Threading" ──
        "External Threading": 0.4,
        # ── Naye — Lathe ──
        "Plain/Cylindrical Turning": 0.45, "Taper Turning": 0.48, "Step Turning": 0.45,
        "Grooving/Necking": 0.3, "Parting-off": 0.2, "Knurling": 0.15, "Forming": 0.3,
        "Internal Grooving": 0.35, "Tapping": 0.25, "Counterboring": 0.2,
        "Countersinking": 0.18, "Contour Turning": 0.55, "Undercutting": 0.2,
        "Eccentric Turning": 0.5, "Polishing/Burnishing": 0.2,
        # ── Naye — Milling ──
        "Face Milling": 0.35, "Slab/Peripheral Milling": 0.55, "Surface Contouring": 0.7,
        "Slot Milling": 0.35, "T-Slot Milling": 0.4, "Dovetail Milling": 0.38,
        "Woodruff Keyway Milling": 0.25, "Pocket Milling": 0.45, "Profile Milling": 0.4,
        "Spotfacing": 0.15, "Corner Rounding/Filleting": 0.18, "Gear/Spline Milling": 0.65,
        "Thread Milling": 0.4, "Angular Milling": 0.32, "Gang Milling": 0.5,
        "Form Milling": 0.42, "Helical Milling": 0.5, "Engraving": 0.15,
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