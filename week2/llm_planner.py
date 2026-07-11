# llm_planner.py
# LLM Process Planner — Week 2 | LLM-CAPP Project
# UPDATED: Falcon-RW-1B (local, basic text-gen) → Groq API (Llama-3.1-8B,
# cloud-based, instruction-tuned). Fayda:
#   1. Instruction-following capability kaafi better — structured output de
#      sakta hai (sirf raw prose nahi)
#   2. Laptop pe GPU ki zarurat nahi (cloud pe run hota hai)
#   3. Free tier available (rate-limited, but project ke liye kaafi)
#   4. Response time ~1-2 sec (local CPU inference se kaafi faster)
#
# IMPORTANT: .env file me GROQ_API_KEY rakhna (code me hardcode mat karo!)
#            Pehle EchoSense me bhi ye galti hui thi — is baar se avoid.

import os
import json
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week1")))

from dotenv import load_dotenv
from groq import Groq
from feature_vocab import FEATURE_TO_OPERATIONS

load_dotenv()

# ── Groq Client Setup ────────────────────────────
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    print("⚠️  GROQ_API_KEY not found in .env file!")
    print("   Create a .env file in project root with:")
    print("   GROQ_API_KEY=gsk_your_key_here")

client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

MODEL = "llama-3.1-8b-instant"  # Free tier pe available


# ── Valid Operations (Route Builder ke saath consistent) ──────
def _get_valid_operations_list() -> str:
    """Feature_vocab.py se saari valid operations ka list banao — LLM ko
    context dene ke liye, taaki wo hallucinated operation-names na de."""
    all_ops = set()
    for feat_data in FEATURE_TO_OPERATIONS.values():
        for alt in feat_data["alternatives"]:
            all_ops.update(alt)
    return ", ".join(sorted(all_ops))


# ── Prompt Template ──────────────────────────────
SYSTEM_PROMPT = """You are a manufacturing process planning expert. Your job is to generate a step-by-step machining process plan for a given part.

RULES:
1. Every plan MUST start with "Facing" and end with "Inspection"
2. Use ONLY these valid operations: {valid_ops}
3. Respect machining precedence (e.g., Drilling must come before Tapping/Reaming)
4. Output ONLY a JSON array of operation names, nothing else
5. Do NOT include any explanation, just the JSON array

EXAMPLE:
Input: Material=Aluminum, Features=Hole,Thread, Tolerance=0.02mm, Batch=500
Output: ["Facing", "Center Drilling", "Drilling", "Tapping", "Inspection"]"""


def generate_process_plan(material: str, features: list,
                          tolerance: str = "0.05mm",
                          batch_size: int = 100) -> dict:
    """
    Groq API (Llama-3.1-8B) se manufacturing process plan generate karo.

    Returns:
    {
      "success": True/False,
      "steps": [...] ya [],
      "raw_response": "...",
      "model": "llama-3.1-8b-instant"
    }
    """
    if client is None:
        return {
            "success": False,
            "steps": [],
            "raw_response": "GROQ_API_KEY not configured",
            "model": MODEL
        }

    valid_ops = _get_valid_operations_list()
    feature_str = ", ".join(features)

    user_prompt = (
        f"Generate a machining process plan for:\n"
        f"Material: {material}\n"
        f"Features: {feature_str}\n"
        f"Tolerance: {tolerance}\n"
        f"Batch Size: {batch_size}\n\n"
        f"Output ONLY a JSON array of operation names."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT.format(valid_ops=valid_ops)},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=200
        )

        raw = response.choices[0].message.content.strip()

        # Parse JSON array from response
        steps = _parse_steps(raw)

        return {
            "success": len(steps) > 0,
            "steps": steps,
            "raw_response": raw,
            "model": MODEL
        }

    except Exception as e:
        return {
            "success": False,
            "steps": [],
            "raw_response": f"API Error: {str(e)}",
            "model": MODEL
        }


def _parse_steps(raw_response: str) -> list:
    """
    LLM ka raw response parse karke clean operation-list nikalo.
    Multiple strategies try karta hai (LLM ka output 100% predictable nahi hota).
    """
    text = raw_response.strip()

    # Strategy 1: Direct JSON parse
    try:
        steps = json.loads(text)
        if isinstance(steps, list) and all(isinstance(s, str) for s in steps):
            return steps
    except json.JSONDecodeError:
        pass

    # Strategy 2: JSON array extract karo agar extra text ke saath aaya ho
    import re
    match = re.search(r'\[.*?\]', text, re.DOTALL)
    if match:
        try:
            steps = json.loads(match.group())
            if isinstance(steps, list) and all(isinstance(s, str) for s in steps):
                return steps
        except json.JSONDecodeError:
            pass

    # Strategy 3: Numbered list parse karo (jaise "1. Facing\n2. Drilling...")
    lines = text.strip().split('\n')
    steps = []
    for line in lines:
        cleaned = re.sub(r'^\d+[\.\)]\s*', '', line.strip())
        cleaned = cleaned.strip('- ').strip()
        if cleaned and not cleaned.startswith('{') and not cleaned.startswith('['):
            steps.append(cleaned)
    if steps:
        return steps

    return []


if __name__ == "__main__":
    print("=== LLM Process Planner (Groq — Llama-3.1-8B) ===\n")

    if not GROQ_API_KEY:
        print("❌ GROQ_API_KEY not set. Ek .env file banao project root me:")
        print("   GROQ_API_KEY=gsk_your_key_here")
        print("\n   Groq key free me milta hai: https://console.groq.com/keys")
        exit(1)

    # Test 1: Basic part
    print("─── Test 1: Aluminum Hole+Slot ───")
    result1 = generate_process_plan("Aluminum", ["Hole", "Slot"], "0.02mm", 500)
    print(f"  Success : {result1['success']}")
    print(f"  Steps   : {result1['steps']}")
    print(f"  Raw     : {result1['raw_response']}")

    # Test 2: Asli bug case
    print("\n─── Test 2: Thread+Fillet (asli bug case) ───")
    result2 = generate_process_plan("Steel", ["Thread", "Fillet"], "0.01mm", 50)
    print(f"  Success : {result2['success']}")
    print(f"  Steps   : {result2['steps']}")

    # Test 3: Naye features jo Falcon kabhi nahi samjhta
    print("\n─── Test 3: Taper+Spline+Keyway (complex) ───")
    result3 = generate_process_plan("Titanium", ["Taper", "Spline", "Keyway"], "0.005mm", 10)
    print(f"  Success : {result3['success']}")
    print(f"  Steps   : {result3['steps']}")

    # Test 4: FSM validate karo LLM ka output
    print("\n─── Test 4: LLM output ko FSM se validate karo ───")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))
    from fsm_validator import validate_sequence
    if result1['success']:
        fsm = validate_sequence(result1['steps'])
        print(f"  FSM Valid: {fsm['valid']}")
        if not fsm['valid']:
            print(f"  Errors  : {fsm['errors']}")