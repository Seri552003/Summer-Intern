# routes.py
# Week 2 | LLM-CAPP Project
#
# ROLE CHANGE (Dynamic Route Builder architecture ke baad):
# Purana role: "77 complete pre-built routes" — route selection isi se hota tha
# Naya role:   "Atomic Operations ka master registry" — route_builder.py aur
#              agents.py isi list ko reference karenge
#
# Purane 77 ROUTE_*, ALL_ROUTES, FEATURE_ROUTE_MAP, select_best_route() —
# ye sab ab LIVE production path me use NAHI honge. Inhe LEGACY DATA ke
# roop me neeche rakha gaya hai, sirf regression-testing ke liye:
# route_builder.py ka naya output in purani routes se compare karke
# verify kiya ja sakta hai ki naya system kam se kam utna hi achha hai.
#
# Confirmed bug (isi legacy code se reproduce hua): ["Thread","Fillet"] ->
# Route_M29 deta hai jisme Fillet ke liye KOI operation hai hi nahi.
# Dynamic Route Builder is class ke bug ko structurally impossible banata hai.

# ════════════════════════════════════════════════════
# ATOMIC OPERATIONS REGISTRY (naya — Dynamic Route Builder ke liye)
# ════════════════════════════════════════════════════
# Naming feature_vocab.py aur token_map.json ke canonical naamon se match
# karti hai. NOTE: legacy 77-routes neeche chhote naam use karte hain
# (Turning, Threading, Grooving, Parting) — LEGACY_NAME_MAP inhe convert
# karta hai jab legacy routes ko naye system se compare karna ho.

OPERATIONS_LATHE = [
    "Facing", "Plain/Cylindrical Turning", "Taper Turning", "Step Turning",
    "Chamfering", "Grooving/Necking", "Parting-off", "Knurling", "Forming",
    "Center Drilling", "Drilling", "Boring", "Internal Grooving", "Reaming",
    "Tapping", "Counterboring", "Countersinking", "External Threading",
    "Contour Turning", "Undercutting", "Eccentric Turning", "Polishing/Burnishing",
]

OPERATIONS_MILLING = [
    "Face Milling", "Slab/Peripheral Milling", "Surface Contouring", "Slot Milling",
    "T-Slot Milling", "Dovetail Milling", "Woodruff Keyway Milling", "Pocket Milling",
    "Profile Milling", "Spotfacing", "Corner Rounding/Filleting", "Gear/Spline Milling",
    "Thread Milling", "Angular Milling", "Gang Milling", "Form Milling",
    "Helical Milling", "Engraving",
]

# In operations ka Lathe/Milling dono machines pe hona common hai (subset of LATHE)
OPERATIONS_SHARED = [
    "Center Drilling", "Drilling", "Boring", "Reaming", "Tapping",
    "Counterboring", "Countersinking", "Chamfering",
]

# Har route me universal step — legacy 77/77 routes me ye HAMESHA last step hai
OPERATIONS_UNIVERSAL = ["Inspection"]

ALL_OPERATIONS = sorted(set(OPERATIONS_LATHE) | set(OPERATIONS_MILLING) | set(OPERATIONS_UNIVERSAL))


def is_valid_operation(op: str) -> bool:
    """Check karo operation naam registry me valid hai ya nahi."""
    return op in ALL_OPERATIONS


def get_operations_by_machine(machine: str) -> list:
    """machine: 'lathe', 'milling', 'shared', 'universal', 'all'"""
    if machine == "lathe":
        return OPERATIONS_LATHE.copy()
    elif machine == "milling":
        return OPERATIONS_MILLING.copy()
    elif machine == "shared":
        return OPERATIONS_SHARED.copy()
    elif machine == "universal":
        return OPERATIONS_UNIVERSAL.copy()
    else:
        return ALL_OPERATIONS.copy()


# Legacy (purani, choti) naming -> naye canonical naming — sirf legacy
# 77-route validation/comparison ke liye zaroori hai
LEGACY_NAME_MAP = {
    "Turning":   "Plain/Cylindrical Turning",
    "Threading": "External Threading",
    "Grooving":  "Grooving/Necking",
    "Parting":   "Parting-off",
    # Baaki (Facing, Boring, Chamfering, Knurling, Drilling, Center Drilling,
    # Pocket Milling, Slot Milling, Reaming, Inspection) — naam already match
}


def normalize_legacy_route(route: list) -> list:
    """Legacy 77-route operation names ko naye canonical names me convert karo."""
    return [LEGACY_NAME_MAP.get(op, op) for op in route]


# ════════════════════════════════════════════════════
# ═══════════════ LEGACY DATA — validation ke liye ═══════════════
# Neeche wale 77 routes ab LIVE code path me use nahi hote.
# route_builder.py banne ke baad, inhe sirf regression-test
# reference ke roop me rakha gaya hai.
# ════════════════════════════════════════════════════

# ════════════════════════════════════════════════════
# LATHE ROUTES (Turning Operations)
# Lathe pe: Facing, Turning, Boring, Threading, Grooving, Chamfering, Knurling, Parting
# ════════════════════════════════════════════════════

# ── Single Operation Lathe ────────────────────────
ROUTE_L1  = ["Facing", "Inspection"]                                                    # Sirf facing
ROUTE_L2  = ["Facing", "Turning", "Inspection"]                                         # Basic turning
ROUTE_L3  = ["Facing", "Boring", "Inspection"]                                          # Sirf boring
ROUTE_L4  = ["Facing", "Threading", "Inspection"]                                       # Sirf threading
ROUTE_L5  = ["Facing", "Grooving", "Inspection"]                                        # Sirf grooving
ROUTE_L6  = ["Facing", "Chamfering", "Inspection"]                                      # Sirf chamfering
ROUTE_L7  = ["Facing", "Knurling", "Inspection"]                                        # Sirf knurling
ROUTE_L8  = ["Facing", "Parting", "Inspection"]                                         # Sirf parting

# ── Two Operation Lathe ───────────────────────────
ROUTE_L9  = ["Facing", "Turning", "Chamfering", "Inspection"]                           # Turn + Chamfer
ROUTE_L10 = ["Facing", "Turning", "Threading", "Inspection"]                            # Turn + Thread
ROUTE_L11 = ["Facing", "Turning", "Grooving", "Inspection"]                             # Turn + Groove
ROUTE_L12 = ["Facing", "Turning", "Boring", "Inspection"]                               # Turn + Bore
ROUTE_L13 = ["Facing", "Turning", "Knurling", "Inspection"]                             # Turn + Knurl
ROUTE_L14 = ["Facing", "Boring", "Threading", "Inspection"]                             # Bore + Thread
ROUTE_L15 = ["Facing", "Boring", "Chamfering", "Inspection"]                            # Bore + Chamfer
ROUTE_L16 = ["Facing", "Threading", "Chamfering", "Inspection"]                         # Thread + Chamfer
ROUTE_L17 = ["Facing", "Grooving", "Threading", "Inspection"]                           # Groove + Thread
ROUTE_L18 = ["Facing", "Grooving", "Chamfering", "Inspection"]                          # Groove + Chamfer

# ── Three Operation Lathe ─────────────────────────
ROUTE_L19 = ["Facing", "Turning", "Threading", "Chamfering", "Inspection"]              # Turn+Thread+Chamfer
ROUTE_L20 = ["Facing", "Turning", "Boring", "Threading", "Inspection"]                  # Turn+Bore+Thread
ROUTE_L21 = ["Facing", "Turning", "Grooving", "Threading", "Inspection"]                # Turn+Groove+Thread
ROUTE_L22 = ["Facing", "Turning", "Boring", "Chamfering", "Inspection"]                 # Turn+Bore+Chamfer
ROUTE_L23 = ["Facing", "Turning", "Grooving", "Chamfering", "Inspection"]               # Turn+Groove+Chamfer
ROUTE_L24 = ["Facing", "Turning", "Knurling", "Chamfering", "Inspection"]               # Turn+Knurl+Chamfer
ROUTE_L25 = ["Facing", "Boring", "Threading", "Chamfering", "Inspection"]               # Bore+Thread+Chamfer
ROUTE_L26 = ["Facing", "Grooving", "Threading", "Chamfering", "Inspection"]             # Groove+Thread+Chamfer
ROUTE_L27 = ["Facing", "Turning", "Boring", "Grooving", "Inspection"]                   # Turn+Bore+Groove
ROUTE_L28 = ["Facing", "Turning", "Parting", "Chamfering", "Inspection"]                # Turn+Part+Chamfer

# ── Four+ Operation Lathe (Complex) ──────────────
ROUTE_L29 = ["Facing", "Turning", "Boring", "Threading", "Chamfering", "Inspection"]    # Full lathe
ROUTE_L30 = ["Facing", "Turning", "Grooving", "Threading", "Chamfering", "Inspection"]  # Turn+Groove+Thread+Chamfer
ROUTE_L31 = ["Facing", "Turning", "Boring", "Grooving", "Threading", "Inspection"]      # Turn+Bore+Groove+Thread
ROUTE_L32 = ["Facing", "Turning", "Knurling", "Grooving", "Threading", "Chamfering", "Inspection"]  # Full complex lathe

# ════════════════════════════════════════════════════
# MILLING ROUTES (Milling Operations)
# Milling pe: Facing, Center Drilling, Drilling, Reaming, Boring, Threading,
#             Pocket Milling, Slot Milling, Chamfering, Inspection
# ════════════════════════════════════════════════════

# ── Single Operation Milling ──────────────────────
ROUTE_M1  = ["Facing", "Drilling", "Inspection"]                                         # Sirf drilling
ROUTE_M2  = ["Facing", "Center Drilling", "Drilling", "Inspection"]                      # Center drill + drill
ROUTE_M3  = ["Facing", "Pocket Milling", "Inspection"]                                   # Sirf pocket
ROUTE_M4  = ["Facing", "Slot Milling", "Inspection"]                                     # Sirf slot
ROUTE_M5  = ["Facing", "Reaming", "Inspection"]                                          # Sirf reaming (pre-drilled)
ROUTE_M6  = ["Facing", "Boring", "Inspection"]                                           # Sirf boring (milling)
ROUTE_M7  = ["Facing", "Chamfering", "Inspection"]                                       # Sirf chamfer (milling)

# ── Two Operation Milling ─────────────────────────
ROUTE_M8  = ["Facing", "Drilling", "Reaming", "Inspection"]                              # Drill + Ream
ROUTE_M9  = ["Facing", "Drilling", "Boring", "Inspection"]                               # Drill + Bore
ROUTE_M10 = ["Facing", "Drilling", "Threading", "Inspection"]                            # Drill + Thread
ROUTE_M11 = ["Facing", "Drilling", "Chamfering", "Inspection"]                           # Drill + Chamfer
ROUTE_M12 = ["Facing", "Drilling", "Pocket Milling", "Inspection"]                       # Drill + Pocket
ROUTE_M13 = ["Facing", "Drilling", "Slot Milling", "Inspection"]                         # Drill + Slot
ROUTE_M14 = ["Facing", "Pocket Milling", "Slot Milling", "Inspection"]                   # Pocket + Slot
ROUTE_M15 = ["Facing", "Pocket Milling", "Chamfering", "Inspection"]                     # Pocket + Chamfer
ROUTE_M16 = ["Facing", "Slot Milling", "Chamfering", "Inspection"]                       # Slot + Chamfer
ROUTE_M17 = ["Facing", "Pocket Milling", "Drilling", "Inspection"]                       # Pocket + Drill

# ── Three Operation Milling ───────────────────────
ROUTE_M18 = ["Facing", "Center Drilling", "Drilling", "Reaming", "Inspection"]           # Center+Drill+Ream
ROUTE_M19 = ["Facing", "Center Drilling", "Drilling", "Threading", "Inspection"]         # Center+Drill+Thread
ROUTE_M20 = ["Facing", "Center Drilling", "Drilling", "Chamfering", "Inspection"]        # Center+Drill+Chamfer
ROUTE_M21 = ["Facing", "Drilling", "Reaming", "Chamfering", "Inspection"]                # Drill+Ream+Chamfer
ROUTE_M22 = ["Facing", "Drilling", "Threading", "Chamfering", "Inspection"]              # Drill+Thread+Chamfer
ROUTE_M23 = ["Facing", "Drilling", "Boring", "Reaming", "Inspection"]                    # Drill+Bore+Ream
ROUTE_M24 = ["Facing", "Drilling", "Boring", "Chamfering", "Inspection"]                 # Drill+Bore+Chamfer
ROUTE_M25 = ["Facing", "Pocket Milling", "Drilling", "Chamfering", "Inspection"]         # Pocket+Drill+Chamfer
ROUTE_M26 = ["Facing", "Slot Milling", "Drilling", "Chamfering", "Inspection"]           # Slot+Drill+Chamfer
ROUTE_M27 = ["Facing", "Pocket Milling", "Slot Milling", "Chamfering", "Inspection"]     # Pocket+Slot+Chamfer
ROUTE_M28 = ["Facing", "Drilling", "Pocket Milling", "Slot Milling", "Inspection"]       # Drill+Pocket+Slot
ROUTE_M29 = ["Facing", "Drilling", "Reaming", "Threading", "Inspection"]                 # Drill+Ream+Thread
ROUTE_M30 = ["Facing", "Pocket Milling", "Drilling", "Reaming", "Inspection"]            # Pocket+Drill+Ream

# ── Four+ Operation Milling (Complex) ────────────
ROUTE_M31 = ["Facing", "Center Drilling", "Drilling", "Reaming", "Chamfering", "Inspection"]           # Full precision hole
ROUTE_M32 = ["Facing", "Center Drilling", "Drilling", "Threading", "Chamfering", "Inspection"]         # Full thread
ROUTE_M33 = ["Facing", "Drilling", "Boring", "Reaming", "Chamfering", "Inspection"]                    # Full bore
ROUTE_M34 = ["Facing", "Pocket Milling", "Slot Milling", "Drilling", "Chamfering", "Inspection"]       # Pocket+Slot+Drill+Chamfer
ROUTE_M35 = ["Facing", "Center Drilling", "Drilling", "Pocket Milling", "Reaming", "Inspection"]       # Full milling
ROUTE_M36 = ["Facing", "Drilling", "Pocket Milling", "Slot Milling", "Chamfering", "Inspection"]       # Complex milling
ROUTE_M37 = ["Facing", "Center Drilling", "Drilling", "Boring", "Threading", "Chamfering", "Inspection"] # Ultra precise

# ════════════════════════════════════════════════════
# COMBINED LATHE + MILLING ROUTES
# ════════════════════════════════════════════════════
ROUTE_C1 = ["Facing", "Turning", "Drilling", "Threading", "Inspection"]                  # Lathe + Mill basic
ROUTE_C2 = ["Facing", "Turning", "Boring", "Drilling", "Reaming", "Inspection"]          # Lathe bore + Mill ream
ROUTE_C3 = ["Facing", "Turning", "Drilling", "Pocket Milling", "Inspection"]             # Lathe + Pocket
ROUTE_C4 = ["Facing", "Turning", "Drilling", "Slot Milling", "Inspection"]               # Lathe + Slot
ROUTE_C5 = ["Facing", "Turning", "Threading", "Drilling", "Chamfering", "Inspection"]    # Thread lathe + Drill mill
ROUTE_C6 = ["Facing", "Turning", "Boring", "Pocket Milling", "Drilling", "Inspection"]   # Full combined
ROUTE_C7 = ["Facing", "Turning", "Grooving", "Drilling", "Reaming", "Inspection"]        # Groove + Ream
ROUTE_C8 = ["Facing", "Turning", "Threading", "Pocket Milling", "Chamfering", "Inspection"] # Complex combined

# ════════════════════════════════════════════════════
# ALL ROUTES DICTIONARY
# ════════════════════════════════════════════════════
ALL_ROUTES = {}

# Lathe routes
for i in range(1, 33):
    name = f"Route_L{i}"
    ALL_ROUTES[name] = eval(f"ROUTE_L{i}")

# Milling routes
for i in range(1, 38):
    name = f"Route_M{i}"
    ALL_ROUTES[name] = eval(f"ROUTE_M{i}")

# Combined routes
for i in range(1, 9):
    name = f"Route_C{i}"
    ALL_ROUTES[name] = eval(f"ROUTE_C{i}")

# ════════════════════════════════════════════════════
# FEATURE → ROUTE MAPPING
# ════════════════════════════════════════════════════
FEATURE_ROUTE_MAP = {
    # ── Single feature ────────────────────────────
    frozenset(["Hole"]):                                    "Route_M2",
    frozenset(["Slot"]):                                    "Route_M4",
    frozenset(["Pocket"]):                                  "Route_M3",
    frozenset(["Thread"]):                                  "Route_M10",
    frozenset(["Chamfer"]):                                 "Route_M7",
    frozenset(["Fillet"]):                                  "Route_M8",
    frozenset(["Groove"]):                                  "Route_L5",
    frozenset(["Boss"]):                                    "Route_L2",
    frozenset(["Step"]):                                    "Route_L9",
    frozenset(["Face"]):                                    "Route_L1",

    # ── Two features ──────────────────────────────
    frozenset(["Hole", "Slot"]):                            "Route_M13",
    frozenset(["Hole", "Pocket"]):                          "Route_M12",
    frozenset(["Hole", "Thread"]):                          "Route_M19",
    frozenset(["Hole", "Chamfer"]):                         "Route_M20",
    frozenset(["Hole", "Fillet"]):                          "Route_M18",
    frozenset(["Hole", "Groove"]):                          "Route_M8",
    frozenset(["Hole", "Boss"]):                            "Route_M18",
    frozenset(["Slot", "Pocket"]):                          "Route_M14",
    frozenset(["Slot", "Chamfer"]):                         "Route_M16",
    frozenset(["Slot", "Thread"]):                          "Route_M13",
    frozenset(["Pocket", "Chamfer"]):                       "Route_M15",
    frozenset(["Pocket", "Thread"]):                        "Route_M17",
    frozenset(["Thread", "Chamfer"]):                       "Route_M22",
    frozenset(["Thread", "Fillet"]):                        "Route_M29",
    frozenset(["Thread", "Groove"]):                        "Route_L17",
    frozenset(["Chamfer", "Fillet"]):                       "Route_M21",
    frozenset(["Boss", "Thread"]):                          "Route_L19",
    frozenset(["Boss", "Groove"]):                          "Route_L11",
    frozenset(["Step", "Chamfer"]):                         "Route_L9",
    frozenset(["Groove", "Thread"]):                        "Route_L17",
    frozenset(["Groove", "Chamfer"]):                       "Route_L18",

    # ── Three features ────────────────────────────
    frozenset(["Hole", "Slot", "Pocket"]):                  "Route_M28",
    frozenset(["Hole", "Slot", "Chamfer"]):                 "Route_M27",
    frozenset(["Hole", "Slot", "Thread"]):                  "Route_M19",
    frozenset(["Hole", "Pocket", "Chamfer"]):               "Route_M25",
    frozenset(["Hole", "Thread", "Chamfer"]):               "Route_M22",
    frozenset(["Hole", "Thread", "Fillet"]):                "Route_M29",
    frozenset(["Hole", "Fillet", "Chamfer"]):               "Route_M21",
    frozenset(["Pocket", "Slot", "Chamfer"]):               "Route_M27",
    frozenset(["Thread", "Chamfer", "Fillet"]):             "Route_M22",
    frozenset(["Thread", "Groove", "Chamfer"]):             "Route_L26",
    frozenset(["Boss", "Thread", "Chamfer"]):               "Route_L19",
    frozenset(["Boss", "Groove", "Thread"]):                "Route_L21",
    frozenset(["Slot", "Thread", "Chamfer"]):               "Route_M26",
    frozenset(["Hole", "Boring", "Chamfer"]):               "Route_M24",
    frozenset(["Hole", "Slot", "Fillet"]):                  "Route_M28",

    # ── Four features ─────────────────────────────
    frozenset(["Hole", "Slot", "Pocket", "Chamfer"]):       "Route_M36",
    frozenset(["Hole", "Thread", "Chamfer", "Fillet"]):     "Route_M32",
    frozenset(["Hole", "Pocket", "Slot", "Thread"]):        "Route_M34",
    frozenset(["Boss", "Thread", "Groove", "Chamfer"]):     "Route_L30",
    frozenset(["Hole", "Slot", "Thread", "Chamfer"]):       "Route_M36",
    frozenset(["Pocket", "Slot", "Drill", "Chamfer"]):      "Route_M34",
    frozenset(["Hole", "Pocket", "Chamfer", "Fillet"]):     "Route_M35",
    frozenset(["Thread", "Groove", "Boss", "Chamfer"]):     "Route_L30",
}


def get_route(name: str) -> list:
    """Route name se steps return karo."""
    return ALL_ROUTES.get(name, [])


def select_best_route(features: list) -> str:
    """
    Features dekhkar best matching route select karo.
    1. Exact match try karo
    2. Partial match (highest overlap)
    3. Default fallback
    """
    feature_set = frozenset(features)

    # 1. Exact match
    if feature_set in FEATURE_ROUTE_MAP:
        return FEATURE_ROUTE_MAP[feature_set]

    # 2. Partial match — highest overlap
    best_route = "Route_M2"
    best_overlap = 0
    for key, route in FEATURE_ROUTE_MAP.items():
        overlap = len(feature_set & key)
        if overlap > best_overlap:
            best_overlap = overlap
            best_route = route

    return best_route


def get_routes_by_machine(machine: str) -> dict:
    """
    Machine type ke hisaab se routes return karo.
    machine: 'lathe', 'milling', 'combined', 'all'
    """
    if machine == "lathe":
        return {k: v for k, v in ALL_ROUTES.items() if k.startswith("Route_L")}
    elif machine == "milling":
        return {k: v for k, v in ALL_ROUTES.items() if k.startswith("Route_M")}
    elif machine == "combined":
        return {k: v for k, v in ALL_ROUTES.items() if k.startswith("Route_C")}
    else:
        return ALL_ROUTES


def print_all_routes():
    """Saari routes print karo."""
    lathe   = {k: v for k, v in ALL_ROUTES.items() if "L" in k}
    milling = {k: v for k, v in ALL_ROUTES.items() if "M" in k}
    combined = {k: v for k, v in ALL_ROUTES.items() if "C" in k}

    print(f"\n=== LATHE ROUTES ({len(lathe)}) ===")
    for name, steps in lathe.items():
        print(f"  {name:<12}: {' → '.join(steps)}")

    print(f"\n=== MILLING ROUTES ({len(milling)}) ===")
    for name, steps in milling.items():
        print(f"  {name:<12}: {' → '.join(steps)}")

    print(f"\n=== COMBINED ROUTES ({len(combined)}) ===")
    for name, steps in combined.items():
        print(f"  {name:<12}: {' → '.join(steps)}")

    print(f"\nTotal routes: {len(ALL_ROUTES)}")


if __name__ == "__main__":
    print_all_routes()

    print("\n=== Feature → Route Mapping Test ===")
    test_cases = [
        ["Hole"],
        ["Slot"],
        ["Thread"],
        ["Thread", "Chamfer"],
        ["Thread", "Fillet"],
        ["Hole", "Slot"],
        ["Hole", "Pocket"],
        ["Hole", "Thread", "Chamfer"],
        ["Pocket", "Slot", "Chamfer"],
        ["Hole", "Slot", "Pocket", "Chamfer"],
        ["Boss", "Thread", "Groove", "Chamfer"],
    ]
    for feats in test_cases:
        route = select_best_route(feats)
        steps = get_route(route)
        print(f"  {str(feats):<40} → {route} ({' → '.join(steps)})")