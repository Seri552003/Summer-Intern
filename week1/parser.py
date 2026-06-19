# parser.py
# JSON Input ko validate aur parse karo
# Task 4 — Week 1 | LLM-CAPP Project

from feature_vocab import is_valid_feature
from material_tokens import (
    is_valid_material, get_tolerance_category,
    get_batch_category, TOLERANCE_CATEGORIES, MATERIALS
)

class ParseResult:
    def __init__(self):
        self.valid      = True
        self.errors     = []
        self.warnings   = []
        self.material   = None
        self.features   = []
        self.tolerance  = None
        self.batch_size = None
        self.batch_cat  = None
        self.tol_cat    = None

    def add_error(self, msg):
        self.valid = False
        self.errors.append(msg)

    def __repr__(self):
        status = "✅ VALID" if self.valid else "❌ INVALID"
        return (
            f"\n{status}\n"
            f"Material  : {self.material}\n"
            f"Features  : {self.features}\n"
            f"Tolerance : {self.tolerance} → {self.tol_cat}\n"
            f"Batch     : {self.batch_size} → {self.batch_cat}\n"
            f"Errors    : {self.errors}\n"
            f"Warnings  : {self.warnings}"
        )

def parse_input(part_json: dict) -> ParseResult:
    result = ParseResult()

    # 1. Material check
    material = part_json.get("material")
    if not material:
        result.add_error("'material' field missing hai!")
    elif not is_valid_material(material):
        result.add_error(f"'{material}' invalid material hai. Valid: {list(MATERIALS.keys())}")
    else:
        result.material = material

    # 2. Features check
    features = part_json.get("features", [])
    if not features:
        result.add_error("'features' list empty hai ya missing!")
    else:
        valid_feats = []
        for feat in features:
            if is_valid_feature(feat):
                valid_feats.append(feat)
            else:
                result.warnings.append(f"'{feat}' unknown feature — skip kiya")
        if not valid_feats:
            result.add_error("Koi bhi valid feature nahi mila!")
        else:
            result.features = valid_feats

    # 3. Tolerance check
    tolerance = part_json.get("tolerance")
    if not tolerance:
        result.warnings.append("Tolerance nahi di — default 0.05mm use hoga")
        result.tolerance = "0.05mm"
    elif tolerance not in TOLERANCE_CATEGORIES:
        result.add_error(f"'{tolerance}' invalid tolerance. Valid: {list(TOLERANCE_CATEGORIES.keys())}")
    else:
        result.tolerance = tolerance
        result.tol_cat = get_tolerance_category(tolerance)

    # 4. Batch size check
    batch_size = part_json.get("batch_size")
    if batch_size is None:
        result.warnings.append("batch_size nahi diya — default 1 use hoga")
        result.batch_size = 1
    elif not isinstance(batch_size, int) or batch_size < 1:
        result.add_error("batch_size positive integer hona chahiye!")
    else:
        result.batch_size = batch_size
        result.batch_cat = get_batch_category(batch_size)

    return result

if __name__ == "__main__":
    print("─── Test 1: Valid Input ───")
    good_input = {
        "material":   "Aluminum",
        "features":   ["Hole", "Slot"],
        "tolerance":  "0.02mm",
        "batch_size": 500
    }
    print(parse_input(good_input))

    print("\n─── Test 2: Invalid Input ───")
    bad_input = {
        "material":   "Diamond",
        "features":   [],
        "tolerance":  "1mm",
        "batch_size": -5
    }
    print(parse_input(bad_input))