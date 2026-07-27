"""
vision_parser.py

Bridges the VLM's extracted-features JSON (from vision_extractor.py) into
the exact input shape parser.py already expects -- so the rest of the
pipeline (tokenizer.py onward) does not need to change at all. Reuses
parser.py's own validation (parse_input) rather than duplicating it.

batch_size is intentionally NOT read from the VLM output -- it is not
normally printed on a drawing, so it is supplied separately (from the
confirmation screen where the user enters it manually).
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "week1")))

from parser import parse_input, ParseResult
from material_tokens import MATERIALS, TOLERANCE_CATEGORIES


def normalize_material(vlm_material):
    """Case-insensitive match against the project's known material names."""
    if not vlm_material:
        return None
    cleaned = vlm_material.strip()
    for valid_name in MATERIALS:
        if valid_name.lower() == cleaned.lower():
            return valid_name
    return vlm_material  # let parse_input's own validation report it as invalid


def normalize_tolerance(vlm_tolerance):
    """
    Matches the VLM's tolerance reading against the project's known
    tolerance buckets, tolerating minor formatting differences such as
    spaces or a +/- sign (e.g. "± 0.02 mm" -> "0.02mm").
    """
    if not vlm_tolerance:
        return None
    cleaned = (
        vlm_tolerance.strip()
        .replace(" ", "")
        .replace("±", "")
        .replace("+/-", "")
        .replace("+-", "")
    )
    for valid_name in TOLERANCE_CATEGORIES:
        if valid_name.lower() == cleaned.lower():
            return valid_name
    return vlm_tolerance  # let parse_input's own validation report it as invalid


def vlm_output_to_part_json(vlm_output: dict, batch_size: int) -> dict:
    """
    Converts vision_extractor.py's output shape:
        {"features": [{"name": "Hole", "confidence": "high"}, ...],
         "material": "Steel", "tolerance": "0.02mm"}
    into parser.py's expected input shape:
        {"material": "Steel", "features": ["Hole", ...],
         "tolerance": "0.02mm", "batch_size": 500}
    """
    feature_names = [f["name"] for f in vlm_output.get("features", []) if f.get("name")]

    return {
        "material": normalize_material(vlm_output.get("material")),
        "features": feature_names,
        "tolerance": normalize_tolerance(vlm_output.get("tolerance")),
        "batch_size": batch_size,
    }


def parse_vlm_output(vlm_output: dict, batch_size: int) -> ParseResult:
    """
    End-to-end: takes the raw vision_extractor.py output plus the
    user-supplied batch_size, converts it, and runs it through parser.py's
    existing parse_input() -- so validation stays in exactly one place.
    """
    part_json = vlm_output_to_part_json(vlm_output, batch_size)
    return parse_input(part_json)


if __name__ == "__main__":
    sample_vlm_output = {
        "features": [
            {"name": "Hole", "confidence": "high"},
            {"name": "Counterbore", "confidence": "medium"},
            {"name": "Chamfer", "confidence": "high"},
        ],
        "material": "steel",
        "tolerance": "± 0.02 mm",
    }
    result = parse_vlm_output(sample_vlm_output, batch_size=500)
    print(result)