# llm_planner.py
# LLM Process Planner — Week 2 | LLM-CAPP Project

from transformers import pipeline

# HuggingFace token yahan daalo
HF_TOKEN = "your_token_here"

# Model load karo
print("Model load ho raha hai... thoda wait karo")
generator = pipeline(
    "text-generation",
    model="tiiuae/falcon-rw-1b",
    token=HF_TOKEN
)
print("Model ready!")

def generate_process_plan(tokens: list, labels: list) -> str:
    """
    Token sequence lekar manufacturing process plan generate karo.
    """
    # Tokens ko readable format mein convert karo
    token_str = ", ".join(labels)
    
    prompt = f"""You are a manufacturing process planning expert.
Given these part features: {token_str}
Generate a step-by-step machining process plan.
Process Plan:
1."""

    result = generator(
        prompt,
        max_new_tokens=100,
        num_return_sequences=1,
        temperature=0.7,
        do_sample=True
    )
    
    return result[0]["generated_text"]

if __name__ == "__main__":
    # Week 1 ka output use karo
    tokens = [201, 101, 102, 303, 403]
    labels = ["Aluminum", "Hole", "Slot", "±0.02mm", "batch:medium_batch"]
    
    print("\n=== Input Tokens ===")
    print(f"Tokens : {tokens}")
    print(f"Labels : {labels}")
    
    print("\n=== Generated Process Plan ===")
    plan = generate_process_plan(tokens, labels)
    print(plan)