# generate_dataset.py
# Synthetic Manufacturing Parts Dataset Generator — REALISTIC ARCHETYPE-BASED
# Tests Week 1, 2, 3 pipeline pe multiple parts ke saath
#
# UPDATED (v3): Pehle pure-random feature sampling thi (koi bhi 1-4 features
# randomly mil jaate the, chahe woh combination real-world me kabhi saath na
# aati ho). Ab 19 REAL manufacturing part-archetypes (bolt, keyed shaft, gear
# blank, flange plate, etc.) define kiye hain — har archetype ka feature-set
# physically sensible hai (jaise ek gear blank me Gear_Teeth+Hole+Keyway
# realistically saath aate hain, na ki random unrelated features).
#
# Ye guarantee bhi karta hai: (a) saare 19 features kam se kam kuch parts me
# zaroor aayenge (coverage), (b) is session me fix kiye gaye bug-cases
# (jaise Thread+Fillet) explicitly represent honge dataset me.

import json
import random
import csv
import os
import sys

random.seed(42)  # Same dataset har baar generate ho — reproducibility ke liye

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "week1")))
from feature_vocab import get_all_features

# ════════════════════════════════════════════════════
# REAL-WORLD PART ARCHETYPES
# Har archetype: naam, features (jo real me saath aate hain), sensible
# materials, tolerance ka typical range, batch ka typical range
# ════════════════════════════════════════════════════
PART_ARCHETYPES = [
    {"name": "Hex Bolt",
     "features": ["Face", "Thread", "Chamfer"],
     "materials": ["Steel", "Titanium", "Brass"],
     "tolerances": ["0.02mm", "0.05mm", "0.1mm"],
     "batches": [500, 1000, 2500, 5000]},

    {"name": "Keyed Shaft",
     "features": ["Step", "Keyway", "Chamfer", "Face"],
     "materials": ["Steel", "Aluminum", "Cast Iron"],
     "tolerances": ["0.01mm", "0.02mm"],
     "batches": [10, 50, 100]},

    {"name": "Flanged Bushing",
     "features": ["Hole", "Face", "Chamfer", "Counterbore"],
     "materials": ["Brass", "Aluminum", "Copper"],
     "tolerances": ["0.02mm", "0.05mm"],
     "batches": [50, 100, 250]},

    {"name": "Threaded Shaft with Relief Groove",
     "features": ["Thread", "Fillet", "Step"],
     "materials": ["Steel", "Titanium"],
     "tolerances": ["0.01mm", "0.02mm"],
     "batches": [10, 50, 100]},

    {"name": "Gear Blank",
     "features": ["Gear_Teeth", "Hole", "Keyway", "Face"],
     "materials": ["Steel", "Cast Iron"],
     "tolerances": ["0.005mm", "0.01mm"],
     "batches": [10, 50]},

    {"name": "V-Belt Pulley",
     "features": ["Groove", "Hole", "Keyway", "Face"],
     "materials": ["Cast Iron", "Aluminum", "Steel"],
     "tolerances": ["0.02mm", "0.05mm"],
     "batches": [50, 100, 250]},

    {"name": "Flange Plate",
     "features": ["Hole", "Counterbore", "Countersink", "Chamfer", "Face"],
     "materials": ["Steel", "Aluminum", "Cast Iron"],
     "tolerances": ["0.05mm", "0.1mm"],
     "batches": [100, 250, 500]},

    {"name": "Mounting Bracket",
     "features": ["Slot", "Hole", "Chamfer", "Face"],
     "materials": ["Aluminum", "Steel"],
     "tolerances": ["0.05mm", "0.1mm", "0.5mm"],
     "batches": [250, 500, 1000]},

    {"name": "Tapered Sleeve",
     "features": ["Taper", "Hole", "Chamfer"],
     "materials": ["Brass", "Aluminum", "Steel"],
     "tolerances": ["0.02mm", "0.05mm"],
     "batches": [50, 100]},

    {"name": "Knurled Grip Handle",
     "features": ["Knurl", "Step", "Chamfer", "Face"],
     "materials": ["Aluminum", "Steel", "Plastic"],
     "tolerances": ["0.05mm", "0.1mm"],
     "batches": [100, 250, 500]},

    {"name": "Pocketed Housing",
     "features": ["Pocket", "Hole", "Counterbore", "Chamfer"],
     "materials": ["Aluminum", "Steel"],
     "tolerances": ["0.02mm", "0.05mm"],
     "batches": [10, 50, 100]},

    {"name": "Splined Shaft",
     "features": ["Spline", "Step", "Fillet", "Chamfer"],
     "materials": ["Steel", "Titanium"],
     "tolerances": ["0.005mm", "0.01mm"],
     "batches": [10, 50]},

    {"name": "Cam Profile Disc",
     "features": ["Contour_3D", "Hole", "Keyway"],
     "materials": ["Steel", "Cast Iron"],
     "tolerances": ["0.01mm", "0.02mm"],
     "batches": [10, 50]},

    {"name": "Engraved ID Plate",
     "features": ["Engraved_Mark", "Face", "Hole", "Chamfer"],
     "materials": ["Aluminum", "Brass", "Plastic"],
     "tolerances": ["0.1mm", "0.5mm"],
     "batches": [50, 100, 250]},

    {"name": "Precision Dowel Pin",
     "features": ["Chamfer", "Face"],
     "materials": ["Steel", "Titanium"],
     "tolerances": ["0.005mm", "0.01mm"],
     "batches": [500, 1000, 2500]},

    {"name": "Stepped Shaft with Retaining Groove",
     "features": ["Step", "Groove", "Fillet", "Chamfer"],
     "materials": ["Steel", "Aluminum"],
     "tolerances": ["0.01mm", "0.02mm"],
     "batches": [10, 50, 100]},

    {"name": "Internally Threaded Bushing",
     "features": ["Thread", "Hole", "Chamfer", "Face"],
     "materials": ["Brass", "Steel", "Copper"],
     "tolerances": ["0.02mm", "0.05mm"],
     "batches": [100, 250, 500]},

    {"name": "Boss with Spotface",
     "features": ["Boss", "Counterbore", "Hole"],
     "materials": ["Aluminum", "Steel", "Cast Iron"],
     "tolerances": ["0.02mm", "0.05mm"],
     "batches": [50, 100, 250]},

    {"name": "Sealed Housing Cover",
     "features": ["Groove", "Face", "Hole", "Chamfer"],
     "materials": ["Aluminum", "Steel", "Cast Iron"],
     "tolerances": ["0.05mm", "0.1mm"],
     "batches": [100, 250, 500]},
]


def generate_part(part_id: int, archetype: dict) -> dict:
    """Ek archetype se ek real-world-jaisa part banao (material/tolerance/batch me variation ke saath)."""
    return {
        "part_id": f"PART_{part_id:03d}",
        "archetype": archetype["name"],
        "material": random.choice(archetype["materials"]),
        "features": archetype["features"].copy(),
        "tolerance": random.choice(archetype["tolerances"]),
        "batch_size": random.choice(archetype["batches"]),
    }


def generate_dataset(n: int = 200) -> list:
    """
    N parts ka dataset banao — har archetype se roughly barabar count,
    taaki coverage guaranteed rahe (sirf random draw pe depend na ho).
    """
    dataset = []
    part_id = 1
    per_archetype = max(1, n // len(PART_ARCHETYPES))

    for archetype in PART_ARCHETYPES:
        for _ in range(per_archetype):
            dataset.append(generate_part(part_id, archetype))
            part_id += 1

    # Agar n exactly divide nahi hua, baaki parts randomly archetypes se fill karo
    while len(dataset) < n:
        archetype = random.choice(PART_ARCHETYPES)
        dataset.append(generate_part(part_id, archetype))
        part_id += 1

    random.shuffle(dataset)
    # Shuffle ke baad part_id dobara sequential kar do (readability ke liye)
    for i, part in enumerate(dataset, 1):
        part["part_id"] = f"PART_{i:03d}"

    return dataset


def save_as_json(dataset: list, path: str):
    with open(path, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"✅ Saved: {path}")


def save_as_csv(dataset: list, path: str):
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["part_id", "archetype", "material", "features", "tolerance", "batch_size"])
        for part in dataset:
            writer.writerow([
                part["part_id"], part["archetype"], part["material"],
                ";".join(part["features"]), part["tolerance"], part["batch_size"]
            ])
    print(f"✅ Saved: {path}")


if __name__ == "__main__":
    print("=== Generating Realistic Archetype-Based Manufacturing Dataset ===\n")

    dataset = generate_dataset(200)

    print("Preview (first 3 parts):")
    for part in dataset[:3]:
        print(f"  {part}")

    print(f"\nTotal parts generated: {len(dataset)}")
    print(f"Total archetypes used: {len(PART_ARCHETYPES)}")

    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_as_json(dataset, os.path.join(base_dir, "parts_dataset.json"))
    save_as_csv(dataset, os.path.join(base_dir, "parts_dataset.csv"))

    # Coverage check — kya saare 19 features kam se kam ek baar aaye?
    print("\n=== Feature Coverage Check ===")
    all_features = set(get_all_features())
    used_features = set()
    for part in dataset:
        used_features.update(part["features"])
    missing = all_features - used_features
    print(f"Features covered: {len(used_features)}/{len(all_features)}")
    print(f"Missing (should be empty): {missing if missing else 'None -- full coverage'}")

    # Archetype distribution
    print("\n=== Archetype Distribution ===")
    counts = {}
    for part in dataset:
        counts[part["archetype"]] = counts.get(part["archetype"], 0) + 1
    for name, count in sorted(counts.items()):
        print(f"  {name:<38} : {count} parts")