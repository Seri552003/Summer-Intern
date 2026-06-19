# tokenizer.py
# Manufacturing Input → Token Sequence
# Task 5 — Week 1 | LLM-CAPP Project (MAIN FILE)

import json
import os
from parser import parse_input
from material_tokens import get_batch_category

# token_map.json load karo
def load_token_map(path=None):
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "token_map.json")
    with open(path, "r") as f:
        return json.load(f)

TOKEN_MAP = load_token_map()

def tokenize(part_json: dict) -> dict:
    # Step 1: Parse karo
    parsed = parse_input(part_json)

    # Step 2: Errors hain toh rok do
    if not parsed.valid:
        return {
            "success": False,
            "tokens": [],
            "token_labels": [],
            "errors": parsed.errors,
            "warnings": parsed.warnings,
        }

    tokens = []
    labels = []

    # Step 3: Material token
    mat_token = TOKEN_MAP["material"].get(parsed.material)
    if mat_token:
        tokens.append(mat_token)
        labels.append(parsed.material)

    # Step 4: Feature tokens
    for feat in parsed.features:
        feat_token = TOKEN_MAP["geometry"].get(feat)
        if feat_token:
            tokens.append(feat_token)
            labels.append(feat)

    # Step 5: Tolerance token
    tol_token = TOKEN_MAP["tolerance"].get(parsed.tolerance)
    if tol_token:
        tokens.append(tol_token)
        labels.append(f"±{parsed.tolerance}")

    # Step 6: Batch size token
    batch_cat = get_batch_category(parsed.batch_size)
    batch_token = TOKEN_MAP["batch_size"].get(batch_cat)
    if batch_token:
        tokens.append(batch_token)
        labels.append(f"batch:{batch_cat}")

    return {
        "success": True,
        "tokens": tokens,
        "token_labels": labels,
        "errors": [],
        "warnings": parsed.warnings,
    }

def print_result(result: dict, title: str = ""):
    print(f"\n{'─'*50}")
    if title:
        print(f"  {title}")
    print(f"{'─'*50}")
    if result["success"]:
        print("  ✅ SUCCESS")
        print(f"  Tokens : {result['tokens']}")
        print("  Mapping:")
        for tok, lab in zip(result["tokens"], result["token_labels"]):
            print(f"    {tok}  →  {lab}")
    else:
        print("  ❌ FAILED")
        for e in result["errors"]:
            print(f"  Error: {e}")
    if result["warnings"]:
        for w in result["warnings"]:
            print(f"  ⚠️  {w}")

if __name__ == "__main__":
    # PPT wala exact example
    part1 = {
        "material":   "Aluminum",
        "features":   ["Hole", "Slot"],
        "tolerance":  "0.02mm",
        "batch_size": 500
    }
    print_result(tokenize(part1), "PPT Example — Aluminum Hole+Slot")

    # Steel part
    part2 = {
        "material":   "Steel",
        "features":   ["Pocket", "Thread", "Chamfer"],
        "tolerance":  "0.01mm",
        "batch_size": 50
    }
    print_result(tokenize(part2), "Steel Pocket+Thread+Chamfer")