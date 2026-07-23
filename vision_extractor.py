"""
vision_extractor.py

Day 1 deliverable: sends an uploaded 2D engineering drawing to Groq's
vision-capable model and returns a structured JSON dict of extracted
machining features, material, and tolerance -- ready to hand off to
parser.py / tokenizer.py exactly like the dropdown-based input did.

Model choice note: Llama 4 Scout/Maverick (originally the obvious pick for
vision) were deprecated on GroqCloud during 2026. qwen/qwen3.6-27b is the
current Groq vision model -- multimodal, JSON mode, 131K context. If Groq's
lineup changes again, swap MODEL_NAME below and check
https://console.groq.com/docs/vision for the current model.

Reasoning note: qwen/qwen3.6-27b is a dual-mode (thinking/non-thinking)
model. By default it spends completion tokens on internal reasoning before
producing the final answer -- with a modest max_completion_tokens this can
consume the whole budget and leave nothing for the actual JSON, causing a
400 json_validate_failed error with an empty failed_generation. Passing
reasoning_effort="none" disables reasoning for this model (per Groq's
Reasoning docs), and reasoning_format="hidden" is Groq's recommended
setting when combining reasoning models with JSON mode.
"""

import os
import json
import base64
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL_NAME = "qwen/qwen3.6-27b"
TOKEN_MAP_PATH = Path(__file__).parent / "week1" / "token_map.json"

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))


def load_feature_vocabulary(token_map_path: Path = TOKEN_MAP_PATH) -> list[str]:
    """
    Reads the existing token_map.json (a nested, categorized dict -- e.g.
    {"geometry": {...}, "material": {...}, "tolerance": {...}, ...}) and
    recursively collects every name whose token ID falls in the 100-199
    (geometry/feature) range, regardless of which category key it sits
    under. This avoids hard-coding the exact section name.
    """
    with open(token_map_path, "r") as f:
        token_map = json.load(f)

    features = []

    def walk(node):
        if isinstance(node, dict):
            for key, value in node.items():
                if isinstance(value, int):
                    if 100 <= value < 200:
                        features.append(key)
                elif isinstance(value, dict):
                    walk(value)

    walk(token_map)

    if not features:
        raise ValueError(
            f"No geometry-range (100-199) tokens found in {token_map_path}. "
            "Check the file path or the token ID ranges."
        )
    return features


def get_mime_type(image_path: str) -> str:
    ext = Path(image_path).suffix.lower()
    if ext in (".jpg", ".jpeg"):
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    raise ValueError(f"Unsupported image format: {ext}. Use PNG or JPG.")


def encode_image(image_path: str) -> str:
    """Base64-encodes a local image file for the Groq vision API."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def build_prompt(feature_vocabulary: list[str]) -> str:
    vocab_list = ", ".join(feature_vocabulary)
    return (
        "You are inspecting a 2D engineering/manufacturing drawing "
        "(orthographic views, dimension lines, and a title block).\n\n"
        "Identify every machining feature visible in the drawing. "
        f"You must choose ONLY from this exact vocabulary: [{vocab_list}]. "
        "Do not invent feature names outside this list. If a feature you "
        "see does not match any name in the list, omit it rather than "
        "guessing a new name.\n\n"
        "Also read the title block (if present) for material and "
        "tolerance. If a value is not visible, use null.\n\n"
        "Respond with ONLY a JSON object in exactly this shape:\n"
        "{\n"
        '  "features": [\n'
        '    {"name": "<one of the vocabulary names>", "confidence": "high|medium|low"}\n'
        "  ],\n"
        '  "material": "<material name or null>",\n'
        '  "tolerance": "<tolerance value or null>"\n'
        "}"
    )


def extract_features_from_image(image_path: str) -> dict:
    """
    Sends the drawing to the vision model and returns the parsed JSON dict.
    Raises ValueError if the model does not return valid JSON matching the
    expected shape -- the caller (Day 2's parser integration) decides how
    to handle that (re-prompt once, or fall back to manual dropdown entry).
    """
    feature_vocabulary = load_feature_vocabulary()
    prompt = build_prompt(feature_vocabulary)
    mime_type = get_mime_type(image_path)
    base64_image = encode_image(image_path)

    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{base64_image}"
                        },
                    },
                ],
            }
        ],
        temperature=0.2,
        max_completion_tokens=2048,
        top_p=1,
        stream=False,
        response_format={"type": "json_object"},
        reasoning_effort="none",
        reasoning_format="hidden",
        stop=None,
    )

    raw_output = completion.choices[0].message.content

    try:
        result = json.loads(raw_output)
    except json.JSONDecodeError as e:
        raise ValueError(
            f"Model did not return valid JSON: {e}\nRaw output: {raw_output}"
        )

    if "features" not in result:
        raise ValueError(f"JSON missing 'features' key. Got: {result}")

    valid_names = set(feature_vocabulary)
    for feature in result["features"]:
        if feature.get("name") not in valid_names:
            raise ValueError(
                f"Model returned an out-of-vocabulary feature: {feature}"
            )

    return result


if __name__ == "__main__":
    test_image = "sample_drawings/flange_plate.png"
    output = extract_features_from_image(test_image)
    print(json.dumps(output, indent=2))