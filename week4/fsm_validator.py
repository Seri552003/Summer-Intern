# fsm_validator.py
# Finite State Machine — Manufacturing Sequence Validator
# Week 4 | LLM-CAPP Project
# UPDATED: Core validation ab precedence_graph.py ke comprehensive rules
# use karta hai (41 operations, 32 precedence edges) — purana rigid
# 8-operation VALID_TRANSITIONS state-machine ab sirf LEGACY REFERENCE
# ke roop me neeche rakha gaya hai, live validation me use nahi hota.

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week2")))

import precedence_graph as pg
from routes import ALL_OPERATIONS  # 41 canonical operations — single source of truth


# ════════════════════════════════════════════════════
# LEGACY REFERENCE — ab live validation me use nahi hota
# ════════════════════════════════════════════════════
# Ye purana 8-operation-only rigid state-machine tha. precedence_graph.py
# isse zyada comprehensive hai (41 ops, non-adjacent pairs bhi check karta
# hai), isliye validate_sequence() ab isse use nahi karta. Reference ke
# liye rakha gaya hai.
_LEGACY_VALID_TRANSITIONS = {
    "START":           ["Facing"],
    "Facing":          ["Center Drilling", "Drilling", "Boring", "Threading"],
    "Center Drilling": ["Drilling"],
    "Drilling":        ["Reaming", "Boring", "Threading", "Chamfering", "Inspection"],
    "Reaming":         ["Inspection", "Chamfering"],
    "Boring":          ["Inspection", "Reaming"],
    "Threading":       ["Chamfering", "Inspection"],
    "Chamfering":      ["Inspection"],
    "Inspection":      ["END"],
}


# ════════════════════════════════════════════════════
# LIVE VALIDATION — precedence_graph.py ke rules use karta hai
# ════════════════════════════════════════════════════

def validate_sequence(steps: list) -> dict:
    """
    Operation sequence validate karo precedence_graph.py ke rules ke against.
    Ye ek GENERIC checkpoint hai — route Route Builder se aaya ho ya LLM
    Planner se, farak nahi padta, same rules lagte hain.

    Returns:
    {
      "valid": True/False,
      "errors": [...],
      "checked_transitions": [...]
    }
    """
    if not steps:
        return {"valid": False, "errors": ["Empty sequence!"], "checked_transitions": []}

    valid, violations = pg.validate_order(steps)

    # Transparency log — har applicable rule ka pass/fail dikhate hain
    checked = []

    first_ok = steps[0] == pg.ALWAYS_FIRST
    first_line = f"First step = '{pg.ALWAYS_FIRST}'"
    if not first_ok:
        first_line += f" (mila: '{steps[0]}')"
    checked.append(f"{'✅' if first_ok else '❌'} {first_line}")

    last_ok = steps[-1] == pg.ALWAYS_LAST
    last_line = f"Last step = '{pg.ALWAYS_LAST}'"
    if not last_ok:
        last_line += f" (mila: '{steps[-1]}')"
    checked.append(f"{'✅' if last_ok else '❌'} {last_line}")

    for a, b in pg.PRECEDENCE_EDGES:
        if a in steps and b in steps:
            ok = steps.index(a) < steps.index(b)
            checked.append(f"{'✅' if ok else '❌'} {a} → {b}")

    return {
        "valid": valid,
        "errors": violations,
        "checked_transitions": checked
    }


# ════════════════════════════════════════════════════
# CORRECTION — 2 tarike
# ════════════════════════════════════════════════════

def fix_sequence(steps: list) -> list:
    """
    BASIC/FALLBACK correction — sirf structural cheezein (Facing/Inspection
    missing) theek karta hai. Order-violations FIX NAHI karta (jaise 'Tapping
    before Drilling') kyunki 32 rules ke against ad-hoc patching unreliable hai.

    Agar original FEATURES pata hain, iski jagah fix_sequence_with_builder()
    use karo — wo guaranteed complete+valid naya route degi.
    """
    fixed = list(steps)

    if not fixed or fixed[0] != pg.ALWAYS_FIRST:
        fixed.insert(0, pg.ALWAYS_FIRST)

    if fixed[-1] != pg.ALWAYS_LAST:
        fixed.append(pg.ALWAYS_LAST)

    return fixed


def fix_sequence_with_builder(features: list, max_routes: int = 1) -> list:
    """
    RECOMMENDED correction — Self-Correction Loop ka primary mechanism.
    Agar original features pata hain (jo aksar pata hote hain, kyunki
    LLM Planner ko bhi wahi features diye gaye the), seedha Route Builder
    se guaranteed-valid replacement route mangao — ad-hoc guessing nahi.

    NOTE: generate_valid_routes() ab list of DICTS return karta hai
    ({"steps": [...], "type": ..., "changeovers": ...}) — machine-aware
    Route Builder ke saath sync karne ke liye ["steps"] explicitly nikala
    jaata hai (pehle plain list assume ho raha tha, jo crash karta tha).
    """
    from route_builder import generate_valid_routes
    routes = generate_valid_routes(features, max_routes=max_routes)
    return routes[0]["steps"] if routes else fix_sequence([])


def print_validation(result: dict, title: str = ""):
    """Pretty print validation result."""
    print(f"\n{'─'*50}")
    if title:
        print(f"  {title}")
    print(f"{'─'*50}")
    status = "✅ VALID" if result["valid"] else "❌ INVALID"
    print(f"  Status: {status}")
    print(f"\n  Checks:")
    for t in result["checked_transitions"]:
        print(f"    {t}")
    if result["errors"]:
        print(f"\n  Errors:")
        for e in result["errors"]:
            print(f"    ⚠️  {e}")


if __name__ == "__main__":
    # Test 1: Valid sequence (route_builder.py se aaya jaisa)
    seq1 = ["Facing", "Center Drilling", "Drilling", "Reaming", "Inspection"]
    print_validation(validate_sequence(seq1), "Valid Sequence Test")

    # Test 2: Invalid sequence (Reaming before Drilling — asli precedence violation)
    seq2 = ["Facing", "Reaming", "Drilling", "Inspection"]
    print_validation(validate_sequence(seq2), "Invalid Sequence Test")

    # Test 3: Naya operation jo purani FSM ke paas exist hi nahi karta tha
    seq3 = ["Facing", "Center Drilling", "Drilling", "Tapping", "Inspection"]
    print_validation(validate_sequence(seq3), "New Operation Test (Tapping)")

    # Test 4: Basic fix_sequence() — sirf structural
    print(f"\n{'─'*50}")
    print("  fix_sequence() Test (basic/fallback)")
    print(f"{'─'*50}")
    bad_seq = ["Drilling", "Reaming"]
    fixed = fix_sequence(bad_seq)
    print(f"  Original : {bad_seq}")
    print(f"  Fixed    : {fixed}")

    # Test 5: fix_sequence_with_builder() — recommended, features se
    print(f"\n{'─'*50}")
    print("  fix_sequence_with_builder() Test (recommended)")
    print(f"{'─'*50}")
    fixed2 = fix_sequence_with_builder(["Thread", "Fillet"])
    print(f"  Features : ['Thread', 'Fillet']")
    print(f"  Route    : {fixed2}")
    result5 = validate_sequence(fixed2)
    print(f"  Status   : {'✅ VALID' if result5['valid'] else '❌ INVALID'}")