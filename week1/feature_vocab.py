# ============================================================
# 1. GEOMETRY FEATURES
# ============================================================
GEOMETRY_FEATURES = [
    # --- Original 10 (unchanged) ---
    "Hole",              # Round chhed — drilling se banta hai
    "Slot",               # Lambi cut — milling se
    "Pocket",             # Andar ki khudai — end mill se
    "Boss",               # Utha hua hissa
    "Thread",             # Pech wali cutting (external ya internal)
    "Chamfer",            # Edge pe angle cutting
    "Fillet",             # Curved/rounded edge
    "Groove",             # Nali
    "Step",               # Step down surface
    "Face",               # Flat surface
    "Taper",              # Conical surface
    "Knurl",               # Grip pattern surface
    "Counterbore",         # Bolt head seating
    "Countersink",         # Screw head seating
    "Keyway",              # Shaft keyway slot
    "Spline",              # Splined shaft feature
    "Gear_Teeth",          # Gear tooth profile
    "Contour_3D",          # Free-form 3D surface
    "Engraved_Mark",       # Text/marking (feature) — "Engraving" operation se naam clash na ho isliye alag rakha
]

ALL_FEATURES = set(GEOMETRY_FEATURES)

# ============================================================
# 2. FEATURE -> OPERATIONS MAPPING (Dynamic Route Builder — Step 1)
# ============================================================
FEATURE_TO_OPERATIONS = {
    "Hole": {
        "machine": "Both",
        "alternatives": [
            ["Center Drilling", "Drilling"],
            ["Center Drilling", "Drilling", "Reaming"],
            ["Center Drilling", "Drilling", "Boring"],
        ],
    },
    "Slot": {
        "machine": "Milling",
        "alternatives": [
            ["Slot Milling"],
        ],
    },
    "Pocket": {
        "machine": "Milling",
        "alternatives": [
            ["Pocket Milling"],
        ],
    },
    "Boss": {
        "machine": "Both",
        "alternatives": [
            ["Profile Milling"],
            ["Step Turning"],
        ],
    },
    "Thread": {
        "machine": "Both",
        "alternatives": [
            ["External Threading"],
            ["Center Drilling", "Drilling", "Tapping"],
            ["Center Drilling", "Drilling", "Thread Milling"],
        ],
    },
    "Chamfer": {
        "machine": "Both",
        "alternatives": [
            ["Chamfering"],
        ],
    },
    "Fillet": {
        "machine": "Milling",
        "alternatives": [
            ["Corner Rounding/Filleting"],
        ],
    },
    "Groove": {
        "machine": "Lathe",
        "alternatives": [
            ["Grooving/Necking"],
            ["Internal Grooving"],
        ],
    },
    "Step": {
        "machine": "Lathe",
        "alternatives": [
            ["Step Turning"],
        ],
    },
    "Face": {
        "machine": "Both",
        "alternatives": [
            ["Facing"],
            ["Face Milling"],
        ],
    },
    "Taper": {
        "machine": "Lathe",
        "alternatives": [
            ["Taper Turning"],
        ],
    },
    "Knurl": {
        "machine": "Lathe",
        "alternatives": [
            ["Knurling"],
        ],
    },
    "Counterbore": {
        "machine": "Both",
        "alternatives": [
            ["Center Drilling", "Drilling", "Counterboring"],
        ],
    },
    "Countersink": {
        "machine": "Both",
        "alternatives": [
            ["Center Drilling", "Drilling", "Countersinking"],
        ],
    },
    "Keyway": {
        "machine": "Milling",
        "alternatives": [
            ["Woodruff Keyway Milling"],
            ["Slot Milling"],
        ],
    },
    "Spline": {
        "machine": "Milling",
        "alternatives": [
            ["Gear/Spline Milling"],
        ],
    },
    "Gear_Teeth": {
        "machine": "Milling",
        "alternatives": [
            ["Gear/Spline Milling"],
        ],
    },
    "Contour_3D": {
        "machine": "Milling",
        "alternatives": [
            ["Surface Contouring"],
            ["Profile Milling"],
        ],
    },
    "Engraved_Mark": {
        "machine": "Milling",
        "alternatives": [
            ["Engraving"],
        ],
    },
}

# ============================================================
# 3. HELPER FUNCTIONS
# ============================================================

def is_valid_feature(feature: str) -> bool:
    """Check karta hai ki feature vocabulary me exist karta hai ya nahi."""
    return feature in ALL_FEATURES


def get_all_features() -> list:
    """Saari features ki list return karta hai."""
    return GEOMETRY_FEATURES.copy()


def get_operations_for_feature(feature: str) -> list:
    """
    Diye gaye feature ke liye saare alternative operation-sequences return karta hai.
    Route Builder isi function ko call karega (Step 1: Feature -> Operation Mapping).
    Returns: list of lists — har inner list ek valid alternative operation-chain hai.
    """
    if not is_valid_feature(feature):
        raise ValueError(
            f"'{feature}' vocabulary me nahi hai. Valid features: {get_all_features()}"
        )
    return FEATURE_TO_OPERATIONS[feature]["alternatives"]


def get_machine_type(feature: str) -> str:
    """Feature konsi machine (Lathe / Milling / Both) pe banta hai, ye batata hai."""
    if not is_valid_feature(feature):
        raise ValueError(f"'{feature}' vocabulary me nahi hai.")
    return FEATURE_TO_OPERATIONS[feature]["machine"]


def get_required_operations_set(features: list) -> set:
    """
    Diye gaye features ki list ke liye — default (pehla) alternative use karke
    saare zaroori operations ka UNION set nikalta hai. Completeness check
    (koi operation skip na ho) ke liye Route Builder isse use karega.
    """
    required = set()
    for feature in features:
        alternatives = get_operations_for_feature(feature)
        required.update(alternatives[0])  # default: pehla alternative
    return required


if __name__ == "__main__":
    print("=== Feature Vocabulary ===")
    for i, feat in enumerate(GEOMETRY_FEATURES, 1):
        default_ops = FEATURE_TO_OPERATIONS[feat]["alternatives"][0]
        machine = FEATURE_TO_OPERATIONS[feat]["machine"]
        print(f"  {i:2}. {feat:<14} [{machine:<7}] -> {default_ops}")
    print(f"\nTotal features: {len(GEOMETRY_FEATURES)}")