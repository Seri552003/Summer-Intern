# image_feature_extractor.py
# Week 1 (extension) | LLM-CAPP Project
#
# 2D image (engineering sketch / drawing / photo) leke, Groq ke vision-capable
# model (qwen/qwen3.6-27b) se manufacturing features extract karta hai.
#
# Design principle (existing llm_planner.py se consistent):
#   - Model ko sirf EXISTING feature vocabulary di jaati hai — koi naya
#     naam invent nahi kar sakta.
#   - Output feature_vocab.is_valid_feature() se validate hota hai — agar
#     model kuch galat de, wo silently reject hota hai (drop, warning nahi crash).
#   - "AI is verified, not trusted" — extraction ka result UI mein user ko
#     confirm/edit karne ke liye dikhaya jaata hai, blindly pipeline mein
#     aage nahi bhej diya jaata.
#   - Run-to-run consistency: same image ko baar baar extract karne pe kabhi
#     1-2 feature miss ho jaate the (LLM sampling variance + hidden
#     reasoning token budget se). Fix: ab har extraction N=2 independent
#     calls karta hai aur unke UNION ko final result maanta hai (self-
#     consistency / ensemble pattern).

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
N_EXTRACTION_SAMPLES = 2   # kitni independent calls union karni hain --
                            # 2 latency/consistency ka accha balance hai;
                            # agar ab bhi feature miss ho to 3 kar dena


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
3. Before finalizing, systematically re-check the image against EVERY name in
   the feature list above, one by one -- do not stop as soon as you notice a
   few features.
4. Output ONLY a JSON object in this exact format, nothing else:
   {{"features": ["Hole", "Thread", ...], "confidence": "high/medium/low",
     "notes": "brief explanation of what was seen"}}
"""


def _encode_image(image_bytes: bytes) -> str:
    """Image bytes ko base64 string mein convert karo (Groq API ke liye)."""
    return base64.b64encode(image_bytes).decode("utf-8")


def _extract_single(b64_image: str, image_format: str, feature_list_str: str) -> dict:
    """Ek single Groq API call karke parse + validate karta hai. Internal
    helper -- extract_features_from_image() isse N baar call karke union
    leta hai consistency ke liye."""
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
            temperature=0,     # was 0.2 -- 0 minimizes run-to-run sampling
                               # variance, jo same image pe har baar alag
                               # result aane ki main wajah thi
            max_completion_tokens=1500,
            response_format={"type": "json_object"},
            reasoning_effort="none",
            reasoning_format="hidden",
        )
        raw = response.choices[0].message.content.strip()
        parsed = _parse_response(raw)

        valid_features = []
        rejected = []
        for f in parsed.get("features", []):
            if is_valid_feature(f):
                if f not in valid_features:
                    valid_features.append(f)
            else:
                rejected.append(f)

        return {
            "success": True,
            "features": valid_features,
            "rejected_features": rejected,
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


def extract_features_from_image(image_bytes: bytes, image_format: str = "png") -> dict:
    """
    Main entry point. 2D image (raw bytes) leke Groq vision model se
    manufacturing features extract karta hai.

    Consistency ke liye N_EXTRACTION_SAMPLES independent calls karta hai aur
    unke valid features ka UNION final result hota hai -- ek call kisi
    feature ko miss kare (sampling variance ya truncation ki wajah se) to
    doosri call usually usse pakad leti hai, isliye same image baar baar
    extract karne pe result stabilize ho jaata hai.

    Returns:
        {
            "success": bool,
            "features": [...],       # validated, union across all samples
            "rejected_features": [...],  # union of out-of-vocabulary terms seen
            "confidence": "high"/"medium"/"low",
            "notes": "...",
            "raw_response": "...",   # from the last successful sample
            "sample_agreement": {feature: count, ...}  # har feature kitne
                                                          # samples mein dikha
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

    samples = [
        _extract_single(b64_image, image_format, feature_list_str)
        for _ in range(N_EXTRACTION_SAMPLES)
    ]

    successful = [s for s in samples if s["success"]]
    if not successful:
        return samples[0]

    union_features = []
    union_rejected = []
    agreement = {}
    confidences = []
    for s in successful:
        for f in s["features"]:
            agreement[f] = agreement.get(f, 0) + 1
            if f not in union_features:
                union_features.append(f)
        for f in s["rejected_features"]:
            if f not in union_rejected:
                union_rejected.append(f)
        confidences.append(s["confidence"])

    conf_rank = {"high": 3, "medium": 2, "low": 1, None: 0}
    best_confidence = max(confidences, key=lambda c: conf_rank.get(c, 0)) if confidences else "low"

    combined_notes = successful[-1]["notes"]
    if len(successful) > 1 and any(agreement[f] < len(successful) for f in union_features):
        combined_notes += f" (combined from {len(successful)} passes; not every feature was seen in every pass)"

    return {
        "success": True,
        "features": union_features,
        "rejected_features": union_rejected,
        "confidence": best_confidence,
        "notes": combined_notes,
        "raw_response": successful[-1]["raw_response"],
        "sample_agreement": agreement,
    }


def _parse_response(raw_response: str) -> dict:
    """LLM ka JSON output parse karo — fallback strategies ke saath
    (llm_planner.py ke _parse_steps() jaisa hi pattern)."""
    text = raw_response.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    fence_stripped = re.sub(r'^```(?:json)?\s*|\s*```$', '', text, flags=re.MULTILINE).strip()
    try:
        return json.loads(fence_stripped)
    except json.JSONDecodeError:
        pass

    match = re.search(r'\{.*\}', fence_stripped, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    if match:
        try:
            fixed = match.group().replace("'", '"')
            return json.loads(fixed)
        except json.JSONDecodeError:
            pass

    found = [f for f in GEOMETRY_FEATURES if re.search(rf'\b{re.escape(f)}\b', text, re.IGNORECASE)]
    if found:
        return {"features": found, "confidence": "low",
                "notes": "Recovered via keyword match — model response was not valid JSON"}

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
            if "sample_agreement" in result:
                print(f"Agreement   : {result['sample_agreement']}")
        else:
            print(f"No test image found at '{test_image_path}' — place one there to test live.")

    print("\n=== Validation Layer Test (no API needed) ===")
    mock_parsed = {"features": ["Hole", "Thread", "FakeFeatureXYZ", "Slot"], "confidence": "high"}
    valid = [f for f in mock_parsed["features"] if is_valid_feature(f)]
    rejected = [f for f in mock_parsed["features"] if not is_valid_feature(f)]
    print(f"Input       : {mock_parsed['features']}")
    print(f"Valid       : {valid}")
    print(f"Rejected    : {rejected}  (correctly filtered out)")