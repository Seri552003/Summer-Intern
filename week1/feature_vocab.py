# feature_vocab.py
# Manufacturing Features ki vocabulary
# Task 1 — Week 1 | LLM-CAPP Project

GEOMETRY_FEATURES = [
    "Hole",      # Round chhed — drilling se banta hai
    "Slot",      # Lambi cut — milling se
    "Pocket",    # Andar ki khudai — end mill se
    "Boss",      # Utha hua hissa
    "Thread",    # Pech wali cutting
    "Chamfer",   # Edge pe angle cutting
    "Fillet",    # Curved/rounded edge
    "Groove",    # Nali
    "Step",      # Step down surface
    "Face",      # Flat surface
]

ALL_FEATURES = set(GEOMETRY_FEATURES)

def is_valid_feature(feature: str) -> bool:
    return feature in ALL_FEATURES

def get_all_features() -> list:
    return GEOMETRY_FEATURES.copy()

if __name__ == "__main__":
    print("=== Feature Vocabulary ===")
    for i, feat in enumerate(GEOMETRY_FEATURES, 1):
        print(f"  {i:2}. {feat}")
    print(f"\nTotal features: {len(GEOMETRY_FEATURES)}")