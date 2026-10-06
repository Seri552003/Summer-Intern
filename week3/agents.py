# agents.py
# Multi-Agent Evaluation System
# Week 3 | LLM-CAPP Project
#
# Time = Dimension-based machining time + Tool Change + Position Change + Changeover
# Cost = INR (rate defined ONCE below as USD_TO_INR)
# Energy = kWh

import math

# ── USD to INR conversion rate ─────────────────────
# SINGLE SOURCE OF TRUTH. Every INR figure in the cost tables below is derived
# from this constant (directly, or via _inr()), and the dashboard imports it
# for display, so changing it here updates every reported cost.
USD_TO_INR = 95.595   # 1 USD = Rs.95.595

# The per-minute machine-rate table (_COST_PER_MIN) was calibrated in INR at
# this older rate; _inr() rescales it to the current USD_TO_INR.
_RATE_BASIS = 95.33


def _inr(value_at_rate_basis: float) -> int:
    """Rescale an INR figure calibrated at _RATE_BASIS to the current USD_TO_INR."""
    return round(value_at_rate_basis * USD_TO_INR / _RATE_BASIS)

# ═══════════════════════════════════════════════════
# PENALTY CONSTANTS
# ═══════════════════════════════════════════════════
CHANGEOVER_TIME_MIN    = 15
CHANGEOVER_COST_INR    = round(15 * USD_TO_INR)   # $15 reference value
CHANGEOVER_ENERGY_KWH  = 0.30

TOOL_CHANGE_TIME_MIN   = 2
TOOL_CHANGE_COST_INR   = round(2 * USD_TO_INR)    # $2  reference value
TOOL_CHANGE_ENERGY_KWH = 0.05

POSITION_CHANGE_TIME_MIN   = 1
POSITION_CHANGE_COST_INR   = round(1 * USD_TO_INR) # $1  reference value
POSITION_CHANGE_ENERGY_KWH = 0.02

# Operations that share same tool family
SAME_TOOL_GROUPS = [
    {"Center Drilling", "Drilling"},
    {"Counterboring", "Countersinking"},
    {"Facing", "Plain/Cylindrical Turning", "Step Turning", "Taper Turning"},
    {"Chamfering", "Corner Rounding/Filleting"},
]

# ═══════════════════════════════════════════════════
# CUTTING PARAMETERS (per material)
# Vc = cutting speed (m/min), f = feed (mm/rev)
# ═══════════════════════════════════════════════════
_CUTTING_PARAMS = {
    #            Vc_turn  f_turn  Vc_drill  f_drill  Vc_mill  fz_mill
    "Aluminum":  (300,    0.25,   120,      0.20,    250,     0.10),
    "Steel":     (120,    0.15,   40,       0.10,    80,      0.06),
    "Brass":     (200,    0.20,   80,       0.15,    150,     0.08),
    "Copper":    (180,    0.20,   70,       0.15,    120,     0.08),
    "Titanium":  (60,     0.10,   20,       0.06,    40,      0.04),
    "Plastic":   (400,    0.30,   150,      0.25,    300,     0.12),
    "Cast Iron": (100,    0.20,   35,       0.12,    70,      0.06),
}

# Thread pitch (mm) per operation type
_THREAD_PITCH = {
    "External Threading": 1.5,
    "Tapping": 1.25,
    "Thread Milling": 1.5,
}

# Cutter diameters (mm) for milling ops
_CUTTER_DIA = {
    "Face Milling": 80, "Slab/Peripheral Milling": 63,
    "Slot Milling": 12, "T-Slot Milling": 16,
    "Dovetail Milling": 16, "Woodruff Keyway Milling": 10,
    "Pocket Milling": 16, "Profile Milling": 12,
    "Surface Contouring": 10, "Spotfacing": 25,
    "Corner Rounding/Filleting": 8, "Gear/Spline Milling": 50,
    "Thread Milling": 12, "Angular Milling": 25,
    "Gang Milling": 63, "Form Milling": 25,
    "Helical Milling": 12, "Engraving": 3,
}

# Number of teeth for milling cutters
_CUTTER_TEETH = {
    "Face Milling": 8, "Slab/Peripheral Milling": 6,
    "Slot Milling": 4, "T-Slot Milling": 4,
    "Dovetail Milling": 4, "Woodruff Keyway Milling": 4,
    "Pocket Milling": 4, "Profile Milling": 4,
    "Surface Contouring": 2, "Spotfacing": 4,
    "Corner Rounding/Filleting": 2, "Gear/Spline Milling": 12,
    "Thread Milling": 4, "Angular Milling": 6,
    "Gang Milling": 6, "Form Milling": 4,
    "Helical Milling": 4, "Engraving": 1,
}

# ═══════════════════════════════════════════════════
# MAX DEPTH PER PASS (mm) — per operation type
# Real machining me ek pass me itni hi depth cut hoti hai
# ═══════════════════════════════════════════════════
_MAX_DEPTH_PER_PASS = {
    # Turning
    "Plain/Cylindrical Turning": 3.0,   # 3mm radial depth per pass
    "Step Turning": 3.0,
    "Taper Turning": 2.5,
    "Contour Turning": 1.5,             # Finishing pass — shallow
    "Grooving/Necking": 1.0,            # Narrow grooving tool
    "Internal Grooving": 0.8,
    "Undercutting": 1.0,
    "Eccentric Turning": 2.0,
    "Forming": 1.5,
    "Knurling": 0.5,                    # Forming, not cutting
    # Drilling
    "Drilling": 40.0,                   # Peck drilling — full depth per peck cycle
    "Center Drilling": 5.0,             # Short depth
    "Boring": 2.0,                      # Fine boring — light passes
    "Reaming": 50.0,                    # Reaming — single pass (pre-drilled)
    "Tapping": 50.0,                    # Single pass
    "Counterboring": 5.0,
    "Countersinking": 5.0,
    "Spotfacing": 2.0,
    "External Threading": 50.0,         # Single pass (lathe threading)
    # Milling
    "Face Milling": 3.0,                # 3mm axial depth per pass
    "Slab/Peripheral Milling": 4.0,
    "Slot Milling": 5.0,                # End mill — 5mm per pass
    "T-Slot Milling": 8.0,              # T-slot cutter — full depth
    "Dovetail Milling": 5.0,
    "Woodruff Keyway Milling": 8.0,     # Woodruff — single plunge
    "Pocket Milling": 4.0,              # 4mm axial depth per pass
    "Profile Milling": 5.0,
    "Surface Contouring": 1.0,          # Finishing — very shallow
    "Gear/Spline Milling": 3.0,
    "Thread Milling": 1.5,
    "Angular Milling": 4.0,
    "Gang Milling": 5.0,
    "Form Milling": 3.0,
    "Helical Milling": 3.0,
    "Corner Rounding/Filleting": 3.0,
    "Engraving": 0.3,                   # Very shallow
}


def _num_passes(op: str, depth: float) -> int:
    """
    Depth ko max_depth_per_pass se divide karke passes nikalo.
    """
    max_dp = _MAX_DEPTH_PER_PASS.get(op, 5.0)
    return max(1, math.ceil(depth / max_dp))


# ═══════════════════════════════════════════════════
# DIMENSION-BASED MACHINING TIME (min) PER OPERATION
# ═══════════════════════════════════════════════════

def _op_time(op: str, material: str, dims: dict) -> float:
    """
    Calculate machining time for one operation using standard formulas
    WITH multi-pass depth calculation.

    dims = {
        "diameter": mm,   # workpiece/hole diameter
        "length": mm,     # turning length / milling length
        "depth": mm,      # total depth to achieve (split into multiple passes)
        "width": mm,      # milling width of cut
    }
    """
    p = _CUTTING_PARAMS.get(material, _CUTTING_PARAMS["Steel"])
    Vc_t, f_t, Vc_d, f_d, Vc_m, fz_m = p

    D  = dims.get("diameter", 25.0)   # mm
    L  = dims.get("length", 50.0)     # mm
    dp = dims.get("depth", 20.0)      # mm — TOTAL depth
    W  = dims.get("width", D * 0.8)   # mm

    passes = _num_passes(op, dp)      # how many passes needed

    # ── TURNING GROUP ──────────────────────────────
    if op in ("Facing",):
        N = (Vc_t * 1000) / (math.pi * max(D, 1))
        t = (D / 2) / (f_t * max(N, 1))
        return round(t * passes, 2)

    if op in ("Plain/Cylindrical Turning", "Step Turning", "Contour Turning",
              "Eccentric Turning", "Polishing/Burnishing"):
        N = (Vc_t * 1000) / (math.pi * max(D, 1))
        t = L / (f_t * max(N, 1))
        return round(t * passes, 2)

    if op in ("Taper Turning",):
        taper_length = L * 1.15
        N = (Vc_t * 1000) / (math.pi * max(D, 1))
        t = taper_length / (f_t * max(N, 1))
        return round(t * passes, 2)

    if op in ("Grooving/Necking", "Internal Grooving", "Undercutting"):
        N = (Vc_t * 1000) / (math.pi * max(D, 1))
        t = dp / (f_t * max(N, 1))
        return round(t, 2)   # depth already in formula, no extra × passes

    if op in ("Knurling",):
        N = (Vc_t * 1000) / (math.pi * max(D, 1))
        t = L / (f_t * max(N, 1)) * 1.5
        return round(t * passes, 2)

    if op in ("Parting-off",):
        N = (Vc_t * 1000) / (math.pi * max(D, 1))
        t = (D / 2) / (f_t * max(N, 1))
        return round(t, 2)   # single pass radial plunge

    if op in ("Forming",):
        N = (Vc_t * 1000) / (math.pi * max(D, 1))
        t = dp / (f_t * max(N, 1))
        return round(t * passes, 2)

    # ── DRILLING GROUP ────────────────────────────
    if op in ("Center Drilling",):
        N = (Vc_d * 1000) / (math.pi * max(3, 1))
        t = 5 / (f_d * max(N, 1))
        return round(t, 2)   # fixed short depth, single pass

    if op in ("Drilling", "Boring", "Reaming"):
        N = (Vc_d * 1000) / (math.pi * max(D, 1))
        # Peck drilling — each peck = max_depth_per_pass, retract & re-enter
        peck_depth = _MAX_DEPTH_PER_PASS.get(op, 40.0)
        pecks = max(1, math.ceil(dp / peck_depth))
        t_per_peck = peck_depth / (f_d * max(N, 1))
        retract_time = 0.1 * pecks  # 0.1 min retract per peck
        return round(t_per_peck * pecks + retract_time, 2)

    if op in ("Tapping", "External Threading"):
        pitch = _THREAD_PITCH.get(op, 1.5)
        N = (Vc_d * 1000) / (math.pi * max(D, 1))
        t = (L / pitch) / max(N, 1)
        return round(t, 2)   # single pass

    if op in ("Counterboring", "Countersinking", "Spotfacing"):
        N = (Vc_d * 1000) / (math.pi * max(D, 1))
        t = dp / (f_d * max(N, 1))
        return round(t * passes, 2)

    # ── MILLING GROUP ─────────────────────────────
    if op in _CUTTER_DIA:
        D_c = _CUTTER_DIA[op]
        z   = _CUTTER_TEETH[op]
        N   = (Vc_m * 1000) / (math.pi * max(D_c, 1))
        Vf  = fz_m * z * N  # table feed (mm/min)

        if op in ("Pocket Milling",):
            area = L * W
            step_over = D_c * 0.6
            t_per_pass = area / (Vf * max(step_over, 1))
            return round(t_per_pass * passes, 2)
        elif op in ("Face Milling", "Slab/Peripheral Milling", "Gang Milling"):
            t = (L + D_c) / max(Vf, 1)
            return round(t * passes, 2)
        elif op in ("Surface Contouring", "Profile Milling"):
            t = (L * 2 + W * 2) / max(Vf, 1)
            return round(t * passes, 2)
        elif op in ("Slot Milling", "T-Slot Milling", "Dovetail Milling",
                    "Woodruff Keyway Milling", "Angular Milling"):
            t = L / max(Vf, 1)
            return round(t * passes, 2)
        elif op in ("Thread Milling",):
            pitch = _THREAD_PITCH.get(op, 1.5)
            t = (L / pitch) * (math.pi * D / max(Vf, 1))
            return round(t, 2)   # single helical pass
        elif op in ("Helical Milling",):
            helix_length = math.sqrt((math.pi * D)**2 + dp**2)
            t = helix_length / max(Vf, 1)
            return round(t * passes, 2)
        elif op in ("Gear/Spline Milling",):
            t = (L / max(Vf, 1)) * passes  # each tooth = one pass
            return round(max(t, 0.5), 2)
        else:
            t = L / max(Vf, 1)
            return round(max(t * passes, 0.5), 2)

    # ── FIXED (non-geometric operations) ─────────
    fixed = {
        "Inspection": 5.0,
        "Chamfering": 1.0,
        "Corner Rounding/Filleting": 1.0,
        "Engraving": 3.0,
    }
    return fixed.get(op, 2.0)


# ═══════════════════════════════════════════════════
# BASE COST + ENERGY
# ═══════════════════════════════════════════════════
# USD reference value per operation; INR value is derived from USD_TO_INR.
_BASE_COST_USD = {
    "Facing": 10,
    "Center Drilling": 8,
    "Drilling": 15,
    "Reaming": 12,
    "Inspection": 5,
    "Boring": 20,
    "Chamfering": 7,
    "External Threading": 18,
    "Plain/Cylindrical Turning": 16,
    "Taper Turning": 17,
    "Step Turning": 16,
    "Grooving/Necking": 13,
    "Parting-off": 9,
    "Knurling": 8,
    "Forming": 14,
    "Internal Grooving": 15,
    "Tapping": 12,
    "Counterboring": 10,
    "Countersinking": 9,
    "Contour Turning": 22,
    "Undercutting": 10,
    "Eccentric Turning": 20,
    "Polishing/Burnishing": 11,
    "Face Milling": 12,
    "Slab/Peripheral Milling": 18,
    "Surface Contouring": 28,
    "Slot Milling": 14,
    "T-Slot Milling": 17,
    "Dovetail Milling": 16,
    "Woodruff Keyway Milling": 11,
    "Pocket Milling": 16,
    "Profile Milling": 15,
    "Spotfacing": 8,
    "Corner Rounding/Filleting": 9,
    "Gear/Spline Milling": 26,
    "Thread Milling": 17,
    "Angular Milling": 14,
    "Gang Milling": 13,
    "Form Milling": 17,
    "Helical Milling": 20,
    "Engraving": 10,
}
_BASE_COST = {op: round(usd * USD_TO_INR) for op, usd in _BASE_COST_USD.items()}

_BASE_ENERGY = {
    "Facing": 0.30, "Center Drilling": 0.20, "Drilling": 0.50, "Reaming": 0.25,
    "Inspection": 0.05, "Boring": 0.60, "Chamfering": 0.15, "External Threading": 0.40,
    "Plain/Cylindrical Turning": 0.45, "Taper Turning": 0.48, "Step Turning": 0.45,
    "Grooving/Necking": 0.30, "Parting-off": 0.20, "Knurling": 0.15, "Forming": 0.30,
    "Internal Grooving": 0.35, "Tapping": 0.25, "Counterboring": 0.20,
    "Countersinking": 0.18, "Contour Turning": 0.55, "Undercutting": 0.20,
    "Eccentric Turning": 0.50, "Polishing/Burnishing": 0.20,
    "Face Milling": 0.35, "Slab/Peripheral Milling": 0.55, "Surface Contouring": 0.70,
    "Slot Milling": 0.35, "T-Slot Milling": 0.40, "Dovetail Milling": 0.38,
    "Woodruff Keyway Milling": 0.25, "Pocket Milling": 0.45, "Profile Milling": 0.40,
    "Spotfacing": 0.15, "Corner Rounding/Filleting": 0.18, "Gear/Spline Milling": 0.65,
    "Thread Milling": 0.40, "Angular Milling": 0.32, "Gang Milling": 0.50,
    "Form Milling": 0.42, "Helical Milling": 0.50, "Engraving": 0.15,
}

_MATERIAL_COST_FACTOR = {
    "Aluminum": 1.0, "Steel": 1.5, "Brass": 1.2, "Copper": 1.3,
    "Titanium": 2.5, "Plastic": 0.6, "Cast Iron": 1.4,
}
_MATERIAL_ENERGY_FACTOR = {
    "Aluminum": 1.0, "Steel": 1.6, "Brass": 1.1, "Copper": 0.95,
    "Titanium": 2.2, "Plastic": 0.5, "Cast Iron": 1.5,
}


# ═══════════════════════════════════════════════════
# HELPER — setup events
# ═══════════════════════════════════════════════════
def _same_tool(a: str, b: str) -> bool:
    return any(a in g and b in g for g in SAME_TOOL_GROUPS)


def _count_setup_events(route_steps: list):
    tool_changes = 0
    position_changes = 0
    for i, step in enumerate(route_steps):
        if i == 0:
            continue
        prev = route_steps[i - 1]
        if step == "Inspection":
            pass
        elif prev == "--- Machine Changeover ---":
            pass
        elif _same_tool(prev, step):
            pass
        else:
            tool_changes += 1
        if step in ("Inspection", "--- Machine Changeover ---"):
            pass
        elif prev == "--- Machine Changeover ---":
            pass
        else:
            position_changes += 1
    return tool_changes, position_changes


# ═══════════════════════════════════════════════════
# TIME AGENT (dimension-based)
# ═══════════════════════════════════════════════════
def time_agent(route_steps: list, material: str,
               dims: dict = None) -> float:
    """
    Total time = Σ op_machining_time(dims) + setup penalties.
    dims = {"diameter": mm, "length": mm, "depth": mm, "width": mm}
    If dims is None, uses default reference dimensions (25mm dia, 50mm L, 20mm depth).
    """
    if dims is None:
        dims = {"diameter": 25.0, "length": 50.0, "depth": 20.0, "width": 20.0}

    machining = sum(
        _op_time(s, material, dims)
        for s in route_steps if s != "--- Machine Changeover ---"
    )
    changeovers = route_steps.count("--- Machine Changeover ---")
    tc, pc = _count_setup_events(route_steps)

    total = (machining
             + changeovers * CHANGEOVER_TIME_MIN
             + tc          * TOOL_CHANGE_TIME_MIN
             + pc          * POSITION_CHANGE_TIME_MIN)
    return round(total, 2)


# ═══════════════════════════════════════════════════
# MACHINE COST RATES (₹ per minute)
# = base_cost / base_time for each operation
# This gives cost proportional to actual machining time
# ═══════════════════════════════════════════════════
_COST_PER_MIN = {
    # Lathe operations (₹/min)
    "Facing": _inr(160),      "Center Drilling": _inr(220),
    "Drilling": _inr(179),    "Reaming": _inr(286),
    "Boring": _inr(191),      "Chamfering": _inr(222),
    "External Threading": _inr(245), "Plain/Cylindrical Turning": _inr(169),
    "Taper Turning": _inr(162), "Step Turning": _inr(169),
    "Grooving/Necking": _inr(207), "Parting-off": _inr(215),
    "Knurling": _inr(254),    "Forming": _inr(223),
    "Internal Grooving": _inr(204), "Tapping": _inr(229),
    "Counterboring": _inr(238), "Countersinking": _inr(286),
    "Contour Turning": _inr(175), "Undercutting": _inr(238),
    "Eccentric Turning": _inr(174), "Polishing/Burnishing": _inr(175),
    # Milling operations (₹/min)
    "Face Milling": _inr(191), "Slab/Peripheral Milling": _inr(172),
    "Surface Contouring": _inr(178), "Slot Milling": _inr(191),
    "T-Slot Milling": _inr(180), "Dovetail Milling": _inr(191),
    "Woodruff Keyway Milling": _inr(210), "Pocket Milling": _inr(169),
    "Profile Milling": _inr(179), "Spotfacing": _inr(254),
    "Corner Rounding/Filleting": _inr(215), "Gear/Spline Milling": _inr(177),
    "Thread Milling": _inr(203), "Angular Milling": _inr(191),
    "Gang Milling": _inr(207), "Form Milling": _inr(180),
    "Helical Milling": _inr(173), "Engraving": _inr(159),
    "Inspection": _inr(95),
}

# ═══════════════════════════════════════════════════
# COST AGENT (INR, dimension-based)
# cost = actual_machining_time × cost_per_min × material_factor
# ═══════════════════════════════════════════════════
def cost_agent(route_steps: list, material: str,
               batch_size: int, dims: dict = None) -> float:
    """
    Cost = Σ (op_machining_time × cost_per_min) × material_factor
           + setup costs (tool change, position change, changeover)
    Dimension-aware: bigger part = more time = more cost.
    """
    if dims is None:
        dims = {"diameter": 25.0, "length": 50.0, "depth": 20.0, "width": 20.0}

    factor = _MATERIAL_COST_FACTOR.get(material, 1.0)

    # Machining cost = time × rate per minute
    machining_cost = sum(
        _op_time(s, material, dims) * _COST_PER_MIN.get(s, 180)
        for s in route_steps
        if s != "--- Machine Changeover ---"
    )

    changeovers = route_steps.count("--- Machine Changeover ---")
    tc, pc = _count_setup_events(route_steps)

    total = (machining_cost * factor
             + changeovers * CHANGEOVER_COST_INR
             + tc          * TOOL_CHANGE_COST_INR
             + pc          * POSITION_CHANGE_COST_INR)

    if batch_size > 500:
        total *= 0.85
    elif batch_size > 100:
        total *= 0.92
    return round(total, 2)


# ═══════════════════════════════════════════════════
# ENERGY AGENT
# ═══════════════════════════════════════════════════
def energy_agent(route_steps: list, material: str,
                 dims: dict = None) -> float:
    factor = _MATERIAL_ENERGY_FACTOR.get(material, 1.0)
    machining = sum(
        _BASE_ENERGY.get(s, 0.3) for s in route_steps
        if s != "--- Machine Changeover ---"
    )
    changeovers = route_steps.count("--- Machine Changeover ---")
    tc, pc = _count_setup_events(route_steps)

    total = (machining
             + changeovers * CHANGEOVER_ENERGY_KWH
             + tc          * TOOL_CHANGE_ENERGY_KWH
             + pc          * POSITION_CHANGE_ENERGY_KWH) * factor
    return round(total, 2)


# ═══════════════════════════════════════════════════
# EFFICIENCY AGENT
# ═══════════════════════════════════════════════════
def efficiency_agent(time_val: float, cost_val: float,
                     energy_val: float) -> float:
    ts = max(0, 100 - time_val  * 1.2)
    cs = max(0, 100 - cost_val  * 0.005)
    es = max(0, 100 - energy_val * 15)
    return round((ts + cs + es) / 3, 2)


# ═══════════════════════════════════════════════════
# MASTER EVALUATE
# ═══════════════════════════════════════════════════
def evaluate_route(route_name: str, route_steps: list,
                   material: str, batch_size: int,
                   dims: dict = None) -> dict:
    t   = time_agent(route_steps, material, dims)
    c   = cost_agent(route_steps, material, batch_size, dims)
    e   = energy_agent(route_steps, material, dims)
    eff = efficiency_agent(t, c, e)
    return {
        "route_name": route_name, "steps": route_steps,
        "time_min": t, "cost_inr": c,
        "energy_kwh": e, "efficiency_score": eff,
    }


# ═══════════════════════════════════════════════════
# TIME BREAKDOWN (for UI)
# ═══════════════════════════════════════════════════
def time_breakdown(route_steps: list, material: str,
                   dims: dict = None) -> dict:
    if dims is None:
        dims = {"diameter": 25.0, "length": 50.0, "depth": 20.0, "width": 20.0}

    machining = sum(
        _op_time(s, material, dims)
        for s in route_steps if s != "--- Machine Changeover ---"
    )
    changeovers = route_steps.count("--- Machine Changeover ---")
    tc, pc = _count_setup_events(route_steps)

    return {
        "machining_time":       round(machining, 2),
        "tool_change_time":     round(tc * TOOL_CHANGE_TIME_MIN, 2),
        "position_change_time": round(pc * POSITION_CHANGE_TIME_MIN, 2),
        "changeover_time":      round(changeovers * CHANGEOVER_TIME_MIN, 2),
        "tool_changes":         tc,
        "position_changes":     pc,
        "changeovers":          changeovers,
        "material_factor":      1.0,
        "dims_used":            dims,
    }


# ═══════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== Dimension-Based Time Test ===\n")

    route = ["Facing", "Center Drilling", "Drilling", "Reaming", "Inspection"]

    for mat in ["Aluminum", "Steel", "Titanium"]:
        for D, L, d in [(10, 30, 15), (25, 50, 20), (50, 100, 40)]:
            dims = {"diameter": D, "length": L, "depth": d, "width": D*0.8}
            t = time_agent(route, mat, dims)
            bd = time_breakdown(route, mat, dims)
            print(f"{mat:10} D={D}mm L={L}mm d={d}mm => "
                  f"Total={t}min "
                  f"(Mach={bd['machining_time']} "
                  f"TC={bd['tool_change_time']} "
                  f"PC={bd['position_change_time']})")
    print()
    print("=== Same route, different dimensions — time changes correctly ===")
    route2 = ["Facing", "Plain/Cylindrical Turning", "Grooving/Necking",
              "--- Machine Changeover ---", "Slot Milling", "Inspection"]
    for D, L, d in [(20, 40, 10), (50, 150, 25), (100, 300, 50)]:
        dims = {"diameter": D, "length": L, "depth": d, "width": D*0.5}
        t = time_agent(route2, "Steel", dims)
        print(f"  Steel D={D}mm L={L}mm depth={d}mm => {t} min")