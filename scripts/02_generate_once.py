import time
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

prompt = """Solve this grade-school math problem.

Question:
Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May?

Answer:
"""

def main():
    torch.manual_seed(0)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto",
    )

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    start = time.time()
    output_ids = model.generate(
        **inputs,
        max_new_tokens=128,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    latency = time.time() - start

    prompt_len = inputs["input_ids"].shape[1]
    generated_ids = output_ids[0][prompt_len:]

    generated_text = tokenizer.decode(generated_ids, skip_special_tokens=True)

    print("MODEL:", MODEL_NAME)
    print("PROMPT TOKENS:", prompt_len)
    print("GENERATED TOKENS:", len(generated_ids))
    print("LATENCY_SECONDS:", round(latency, 3))
    print("=" * 80)
    print(generated_text)

if __name__ == "__main__":
    main()