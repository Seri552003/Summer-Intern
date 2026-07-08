# fsm_validator.py
# Finite State Machine — Manufacturing Sequence Validator
# Week 4 | LLM-CAPP Project

# ── Valid Transitions ──────────────────────────────
# Yeh rules define karte hain ki kaun sa operation
# kis operation ke baad aa sakta hai
VALID_TRANSITIONS = {
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

ALL_OPERATIONS = set(VALID_TRANSITIONS.keys()) - {"START"}


def validate_sequence(steps: list) -> dict:
    """
    Operation sequence validate karo FSM rules ke against.
    Returns:
    {
      "valid": True/False,
      "errors": [...],
      "checked_transitions": [...]
    }
    """
    errors = []
    checked = []

    if not steps:
        return {"valid": False, "errors": ["Empty sequence!"], "checked_transitions": []}

    # First step Facing se start hona chahiye
    if steps[0] != "Facing":
        errors.append(f"Sequence 'Facing' se start honi chahiye, '{steps[0]}' se nahi!")

    # Har transition check karo
    current = "START"
    for step in steps:
        allowed = VALID_TRANSITIONS.get(current, [])
        transition = f"{current} → {step}"
        if step in allowed:
            checked.append(f"✅ {transition}")
            current = step
        else:
            checked.append(f"❌ {transition} (INVALID)")
            errors.append(f"Invalid: '{current}' ke baad '{step}' nahi aa sakta!")
            current = step  # Continue checking rest

    # Last step Inspection hona chahiye
    if steps and steps[-1] != "Inspection":
        errors.append(f"Sequence 'Inspection' pe khatam honi chahiye, '{steps[-1]}' pe nahi!")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "checked_transitions": checked
    }


def fix_sequence(steps: list) -> list:
    """
    Invalid sequence ko fix karo — basic corrections apply karo.
    """
    fixed = list(steps)

    # Facing nahi hai toh start mein add karo
    if not fixed or fixed[0] != "Facing":
        fixed.insert(0, "Facing")

    # Inspection nahi hai toh end mein add karo
    if fixed[-1] != "Inspection":
        fixed.append("Inspection")

    # Center Drilling ke baad Drilling hona chahiye
    for i in range(len(fixed) - 1):
        if fixed[i] == "Center Drilling" and fixed[i+1] != "Drilling":
            fixed.insert(i+1, "Drilling")
            break

    return fixed


def print_validation(result: dict, title: str = ""):
    """Pretty print validation result."""
    print(f"\n{'─'*50}")
    if title:
        print(f"  {title}")
    print(f"{'─'*50}")
    status = "✅ VALID" if result["valid"] else "❌ INVALID"
    print(f"  Status: {status}")
    print(f"\n  Transitions Checked:")
    for t in result["checked_transitions"]:
        print(f"    {t}")
    if result["errors"]:
        print(f"\n  Errors:")
        for e in result["errors"]:
            print(f"    ⚠️  {e}")


if __name__ == "__main__":
    # Test 1: Valid sequence
    seq1 = ["Facing", "Center Drilling", "Drilling", "Reaming", "Inspection"]
    print_validation(validate_sequence(seq1), "Valid Sequence Test")

    # Test 2: Invalid sequence (Reaming before Drilling)
    seq2 = ["Facing", "Reaming", "Drilling", "Inspection"]
    result2 = validate_sequence(seq2)
    print_validation(result2, "Invalid Sequence Test")

    # Test 3: Auto-fix karo
    print(f"\n{'─'*50}")
    print("  Auto-Fix Test")
    print(f"{'─'*50}")
    bad_seq = ["Drilling", "Reaming"]  # Facing aur Inspection missing
    fixed = fix_sequence(bad_seq)
    print(f"  Original : {bad_seq}")
    print(f"  Fixed    : {fixed}")
    result3 = validate_sequence(fixed)
    print(f"  Status   : {'✅ VALID' if result3['valid'] else '❌ STILL INVALID'}")