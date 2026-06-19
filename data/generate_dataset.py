# generate_dataset.py
# Synthetic Manufacturing Parts Dataset Generator
# Tests Week 1, 2, 3 pipeline pe multiple parts ke saath

import json
import random
import csv
import os

random.seed(42)  # Same dataset har baar generate ho — reproducibility ke liye

# ── Possible values (Week 1 ke feature_vocab.py se match karte hain) ──
MATERIALS = ["Aluminum", "Steel", "Brass", "Copper", "Titanium", "Plastic", "Cast Iron"]
FEATURES = ["Hole", "Slot", "Pocket", "Boss", "Thread", "Chamfer", "Fillet", "Groove", "Step", "Face"]
TOLERANCES = ["0.005mm", "0.01mm", "0.02mm", "0.05mm", "0.1mm", "0.5mm"]
BATCH_SIZES = [5, 10, 25, 50, 100, 250, 500, 750, 1000, 2500, 5000]


def generate_part(part_id: int) -> dict:
    """Ek random manufacturing part banao."""
    material = random.choice(MATERIALS)
    
    # 1 se 4 features randomly select karo (no duplicates)
    num_features = random.randint(1, 4)
    features = random.sample(FEATURES, num_features)
    
    tolerance = random.choice(TOLERANCES)
    batch_size = random.choice(BATCH_SIZES)
    
    return {
        "part_id": f"PART_{part_id:03d}",
        "material": material,
        "features": features,
        "tolerance": tolerance,
        "batch_size": batch_size
    }


def generate_dataset(n: int = 50) -> list:
    """N parts ka dataset banao."""
    return [generate_part(i + 1) for i in range(n)]


def save_as_json(dataset: list, path: str):
    """Dataset ko JSON file mein save karo."""
    with open(path, "w") as f:
        json.dump(dataset, f, indent=2)
    print(f"✅ Saved: {path}")


def save_as_csv(dataset: list, path: str):
    """Dataset ko CSV file mein save karo (features ko semicolon se join karke)."""
    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["part_id", "material", "features", "tolerance", "batch_size"])
        for part in dataset:
            writer.writerow([
                part["part_id"],
                part["material"],
                ";".join(part["features"]),
                part["tolerance"],
                part["batch_size"]
            ])
    print(f"✅ Saved: {path}")


if __name__ == "__main__":
    print("=== Generating Synthetic Manufacturing Dataset ===\n")
    
    dataset = generate_dataset(50)
    
    # Preview pehle 3 parts
    print("Preview (first 3 parts):")
    for part in dataset[:3]:
        print(f"  {part}")
    
    print(f"\nTotal parts generated: {len(dataset)}")
    
    # Save both formats
    base_dir = os.path.dirname(os.path.abspath(__file__))
    save_as_json(dataset, os.path.join(base_dir, "parts_dataset.json"))
    save_as_csv(dataset, os.path.join(base_dir, "parts_dataset.csv"))
    
    # Quick stats
    print("\n=== Dataset Stats ===")
    material_counts = {}
    for part in dataset:
        material_counts[part["material"]] = material_counts.get(part["material"], 0) + 1
    print("Material distribution:")
    for mat, count in sorted(material_counts.items()):
        print(f"  {mat:12} : {count} parts")