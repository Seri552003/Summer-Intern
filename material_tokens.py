# material_tokens.py
# Materials aur Tolerances ki category definitions
# Task 2 — Week 1 | LLM-CAPP Project

MATERIALS = {
    "Aluminum":   "Soft metal, easy to machine, lightweight",
    "Steel":      "Hard metal, strong, needs carbide tools",
    "Brass":      "Medium hardness, good for threads",
    "Copper":     "Soft, electrical parts mein use hota hai",
    "Titanium":   "Very hard, aerospace grade, slow machining",
    "Plastic":    "ABS/POM, low-speed machining",
    "Cast Iron":  "Brittle, abrasive, needs special tools",
}

TOLERANCE_CATEGORIES = {
    "0.005mm": "ultra_tight",
    "0.01mm":  "tight",
    "0.02mm":  "standard",
    "0.05mm":  "medium",
    "0.1mm":   "coarse",
    "0.5mm":   "rough",
}

def get_batch_category(batch_size: int) -> str:
    if batch_size <= 10:
        return "prototype"
    elif batch_size <= 99:
        return "small_batch"
    elif batch_size <= 999:
        return "medium_batch"
    else:
        return "mass_production"

def get_tolerance_category(tol: str) -> str:
    return TOLERANCE_CATEGORIES.get(tol, "unknown")

def is_valid_material(material: str) -> bool:
    return material in MATERIALS

if __name__ == "__main__":
    print("=== Materials ===")
    for mat, desc in MATERIALS.items():
        print(f"  {mat:12} → {desc}")

    print("\n=== Tolerance Categories ===")
    for tol, cat in TOLERANCE_CATEGORIES.items():
        print(f"  ±{tol:8} → {cat}")

    print("\n=== Batch Size Test ===")
    for size in [5, 50, 500, 5000]:
        print(f"  {size:5} units → {get_batch_category(size)}")