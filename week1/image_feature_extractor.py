# image_feature_extractor.py
# Week 1 (extension) | LLM-CAPP Project
#
# 2D image (engineering sketch / drawing / photo) leke, Groq ke vision-capable
# model (qwen/qwen3.6-27b) se manufacturing features extract karta hai.
#
# Design principle (existing llm_planner.py se consistent):
#   - Model ko sirf EXISTING 19-feature vocabulary di jaati hai — koi naya
#     naam invent nahi kar sakta.
#   - Output feature_vocab.is_valid_feature() se validate hota hai — agar
#     model kuch galat de, wo silently reject hota hai (drop, warning nahi crash).
#   - "AI is verified, not trusted" — extraction ka result UI mein user ko
#     confirm/edit karne ke liye dikhaya jaata hai, blindly pipeline mein
#     aage nahi bhej diya jaata.

import os
import json
import base64
import re

from dotenv import load_dotenv
from groq import Groq
from feature_vocab import GEOMETRY_FEATURES, is_valid_feature

# .env dhoondne ke liye bare load_dotenv() bharosemand nahi tha -- wo current
# working directory se search karta hai, aur agar Streamlit kisi aur folder
# se start ho (ya kabhi CWD change ho), ye silently .env miss kar deta tha,
# jisse "GROQ_API_KEY not configured" error baar baar wapas aata tha. Ab
# explicitly dono jagah check karte hain jahan .env ho sakti hai.
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
_CANDIDATE_ENV_PATHS = [
    os.path.join(_THIS_DIR, ".env"),                      # week1/.env
    os.path.join(_THIS_DIR, "..", "week6", ".env"),        # week6/.env (app.py isi se load karta hai)
    os.path.join(_THIS_DIR, "..", ".env"),                 # project root .env
]
for _env_path in _CANDIDATE_ENV_PATHS:
    if os.path.exists(_env_path):
        load_dotenv(_env_path)
        break
else:
    load_dotenv()   # last resort -- purana CWD-based default behaviour

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

VISION_MODEL = "qwen/qwen3.6-27b"   # same model family as llm_planner.py,
                                     # this one also accepts image input

# NOTE: qwen/qwen3.6-27b is a dual-mode (thinking/non-thinking) model. By
# default it can spend completion tokens on internal reasoning before
# producing the final answer -- with a small token budget this consumes the
# whole budget and leaves nothing for the actual JSON, which is the likely
# cause of earlier "could not parse model response" failures. The
# reasoning_effort="none" + reasoning_format="hidden" params below disable
# that, response_format={"type": "json_object"} forces valid JSON, and the
# larger max_completion_tokens gives room even if reasoning can't be fully
# disabled. See https://console.groq.com/docs/reasoning for details.

MAX_IMAGE_MB = 20   # Groq's documented per-image limit


VISION_SYSTEM_PROMPT = """You are a manufacturing engineer analyzing a 2D
engineering drawing or sketch of a mechanical part.

TASK: Identify which of the following manufacturing features are visibly
present in the image. Use ONLY these exact feature names — do not invent
any other name:
{feature_list}

RULES:
1. Only include a feature if there is clear visual evidence for it in the image
   (e.g. a circle with a centerline = Hole, a helical/angled line pattern on
   a cylindrical surface = Thread, a rectangular cut = Slot or Pocket).
2. If the image is unclear, low-resolution, or ambiguous, still return your
   best guess but set "confidence" to "low".
3. Output ONLY a JSON object in this exact format, nothing else:
   {{"features": ["Hole", "Thread", ...], "confidence": "high/medium/low",
     "notes": "brief explanation of what was seen"}}
"""


def _encode_image(image_bytes: bytes) -> str:
    """Image bytes ko base64 string mein convert karo (Groq API ke liye)."""
    return base64.b64encode(image_bytes).decode("utf-8")


def extract_features_from_image(image_bytes: bytes, image_format: str = "png") -> dict:
    """
    Main entry point. 2D image (raw bytes) leke Groq vision model se
    manufacturing features extract karta hai.

    Returns:
        {
            "success": bool,
            "features": [...],       # validated, only known-vocabulary features
            "rejected_features": [...],  # model ne diya but vocabulary mein nahi tha
            "confidence": "high"/"medium"/"low",
            "notes": "...",
            "raw_response": "..."
        }
    """
    if client is None:
        return {
            "success": False, "features": [], "rejected_features": [],
            "confidence": None, "notes": "",
            "error": "GROQ_API_KEY not configured.",
        }

    size_mb = len(image_bytes) / (1024 * 1024)
    if size_mb > MAX_IMAGE_MB:
        return {
            "success": False, "features": [], "rejected_features": [],
            "confidence": None, "notes": "",
            "error": f"Image too large ({size_mb:.1f}MB) — Groq limit is {MAX_IMAGE_MB}MB.",
        }

    b64_image = _encode_image(image_bytes)
    feature_list_str = ", ".join(GEOMETRY_FEATURES)

    try:
        response = client.chat.completions.create(
            model=VISION_MODEL,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": VISION_SYSTEM_PROMPT.format(feature_list=feature_list_str)},
                        {"type": "image_url", "image_url": {
                            "url": f"data:image/{image_format};base64,{b64_image}"
                        }},
                    ],
                }
            ],
            temperature=0.2,   # low — consistency zaroori hai, creativity nahi
            max_completion_tokens=1500,   # 400 was too tight — qwen3.6-27b is a
                                           # dual-mode reasoning model and can burn
                                           # the whole budget on hidden reasoning,
                                           # leaving nothing for the actual JSON
                                           # (this is the likely cause of the old
                                           # "could not parse model response" error)
            response_format={"type": "json_object"},   # forces valid JSON output,
                                                         # instead of just asking nicely
                                                         # in the prompt
            reasoning_effort="none",     # disables qwen3.6-27b's internal reasoning
            reasoning_format="hidden",   # Groq's recommended pairing with JSON mode
        )
        raw = response.choices[0].message.content.strip()
        parsed = _parse_response(raw)

        # ── Validation Layer — sirf known vocabulary allow hoti hai ──
        valid_features = []
        rejected = []
        for f in parsed.get("features", []):
            if is_valid_feature(f):
                if f not in valid_features:   # duplicate na ho
                    valid_features.append(f)
            else:
                rejected.append(f)

        return {
            "success": True,
            "features": valid_features,
            "rejected_features": rejected,   # transparency ke liye — user dekh sake
            "confidence": parsed.get("confidence", "medium"),
            "notes": parsed.get("notes", ""),
            "raw_response": raw,
        }

    except Exception as e:
        return {
            "success": False, "features": [], "rejected_features": [],
            "confidence": None, "notes": "",
            "error": f"Vision API error: {str(e)}",
        }


def _parse_response(raw_response: str) -> dict:
    """LLM ka JSON output parse karo — fallback strategies ke saath
    (llm_planner.py ke _parse_steps() jaisa hi pattern)."""
    text = raw_response.strip()

    # Strategy 1: Direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Strip markdown code fences (```json ... ``` or ``` ... ```)
    # Bahut common — vision models often wrap JSON in fences even when told not to
    fence_stripped = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.MULTILINE).strip()
    try:
        return json.loads(fence_stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 3: Find the {...} substring anywhere in the (fence-stripped) text
    match = re.search(r'\{.*\}', fence_stripped, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    # Strategy 4: Fix common JSON issues — single quotes instead of double quotes
    if match:
        try:
            fixed = match.group().replace("'", '"')
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    # Strategy 5 (last resort): keyword-match known feature names directly in the
    # raw text, even if it's not valid JSON at all. Better to recover SOMETHING
    # than to return empty when the model clearly did describe the image.
    found = [f for f in GEOMETRY_FEATURES if re.search(rf'\b{re.escape(f)}\b', text, re.IGNORECASE)]
    if found:
        return {"features": found, "confidence": "low",
                "notes": "Recovered via keyword match — model response was not valid JSON"}

    # Total fallback — genuinely kuch nahi mila
    return {"features": [], "confidence": "low", "notes": "Could not parse model response",
            "_debug_raw": text[:300]}


# ═══════════════════════════════════════════════════
# SELF-TEST
# ═══════════════════════════════════════════════════
if __name__ == "__main__":
    print("=== Image Feature Extractor — Self Test ===\n")

    if not GROQ_API_KEY:
        print("⚠️  GROQ_API_KEY not set — cannot run live test.")
        print("    (Module structure and validation logic can still be reviewed.)")
    else:
        test_image_path = "test_part_sketch.png"
        if os.path.exists(test_image_path):
            with open(test_image_path, "rb") as f:
                img_bytes = f.read()
            result = extract_features_from_image(img_bytes)
            print(f"Success     : {result['success']}")
            print(f"Features    : {result['features']}")
            print(f"Rejected    : {result['rejected_features']}")
            print(f"Confidence  : {result['confidence']}")
            print(f"Notes       : {result['notes']}")
        else:
            print(f"No test image found at '{test_image_path}' — place one there to test live.")

    # Validation logic can be tested without the API using a mock response:
    print("\n=== Validation Layer Test (no API needed) ===")
    mock_parsed = {"features": ["Hole", "Thread", "FakeFeatureXYZ", "Slot"], "confidence": "high"}
    valid = [f for f in mock_parsed["features"] if is_valid_feature(f)]
    rejected = [f for f in mock_parsed["features"] if not is_valid_feature(f)]
    print(f"Input       : {mock_parsed['features']}")
    print(f"Valid       : {valid}")
    print(f"Rejected    : {rejected}  (correctly filtered out)")