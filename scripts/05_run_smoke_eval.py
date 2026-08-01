import argparse
import json
import re
import time

import torch
from jsonschema import ValidationError, validate
from transformers import AutoModelForCausalLM, AutoTokenizer


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

SCHEMA = {
    "type": "object",
    "properties": {
        "reasoning": {"type": "string"},
        "answer": {"type": "string"},
    },
    "required": ["reasoning", "answer"],
    "additionalProperties": False,
}

EXAMPLES = [
    {
        "id": "gsm8k_manual_1",
        "question": "Natalia sold clips to 48 of her friends in April, and then she sold half as many clips in May. How many clips did Natalia sell altogether in April and May?",
        "gold": "72",
    },
    {
        "id": "gsm8k_manual_2",
        "question": "A restaurant has 23 tables. Each table seats 4 people. How many people can sit in the restaurant when all tables are full?",
        "gold": "92",
    },
    {
        "id": "gsm8k_manual_3",
        "question": "James earns $20 an hour for 30 hours. How much does he earn?",
        "gold": "600",
    },
]


def make_free_prompt(question: str) -> str:
    return f"""Solve this grade-school math problem.

Show brief reasoning and end with the final numeric answer.

Question:
{question}

Answer:
"""


def make_json_prompt(question: str) -> str:
    return f"""Solve the math problem.

Return ONLY valid JSON. No markdown. No extra text.

The JSON must have this shape:
{{
  "reasoning": "your reasoning here",
  "answer": "final numeric answer here"
}}

Question:
{question}

JSON:
"""


def extract_number_from_text(text: str):
    numbers = re.findall(r"-?\d+(?:\.\d+)?", text)
    return numbers[-1] if numbers else None


def extract_json_object(text: str):
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None, "no_json_braces_found"

    candidate = text[start : end + 1]

    try:
        return json.loads(candidate), None
    except Exception as exc:
        return None, f"json_parse_error: {type(exc).__name__}: {exc}"


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--condition", choices=["free", "json"], required=True)
    return parser.parse_args()


def load_model():
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto",
    )
    return tokenizer, model


def generate(model, tokenizer, prompt):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    start_time = time.time()
    output_ids = model.generate(
        **inputs,
        max_new_tokens=192,
        do_sample=False,
        pad_token_id=tokenizer.eos_token_id,
    )
    latency = time.time() - start_time

    prompt_len = inputs["input_ids"].shape[1]
    generated_ids = output_ids[0][prompt_len:]
    raw_output = tokenizer.decode(generated_ids, skip_special_tokens=True)

    return raw_output, latency, prompt_len, len(generated_ids)


def score_free(raw_output):
    return {
        "parsed": None,
        "valid_json": None,
        "valid_schema": None,
        "predicted_answer": extract_number_from_text(raw_output),
        "error": None,
    }


def score_json(raw_output):
    parsed, error = extract_json_object(raw_output)
    valid_schema = False
    predicted_answer = None

    if parsed is not None:
        try:
            validate(instance=parsed, schema=SCHEMA)
            valid_schema = True
            predicted_answer = parsed["answer"]
        except (ValidationError, KeyError, TypeError) as exc:
            error = f"schema_error: {type(exc).__name__}: {exc}"

    return {
        "parsed": parsed,
        "valid_json": parsed is not None,
        "valid_schema": valid_schema,
        "predicted_answer": predicted_answer,
        "error": error,
    }


def main():
    args = parse_args()
    condition = args.condition
    torch.manual_seed(0)

    tokenizer, model = load_model()
    out_path = f"results/day0/smoke_eval_{condition}.jsonl"

    with open(out_path, "w", encoding="utf-8") as output_file:
        for ex in EXAMPLES:
            if condition == "free":
                prompt = make_free_prompt(ex["question"])
            else:
                prompt = make_json_prompt(ex["question"])

            raw_output, latency, prompt_len, generated_tokens = generate(
                model, tokenizer, prompt
            )

            scored = score_free(raw_output) if condition == "free" else score_json(raw_output)
            predicted_answer = scored["predicted_answer"]

            row = {
                "model": MODEL_NAME,
                "condition": condition,
                "seed": 0,
                "example_id": ex["id"],
                "question": ex["question"],
                "gold": ex["gold"],
                "prompt": prompt,
                "raw_output": raw_output,
                "parsed": scored["parsed"],
                "valid_json": scored["valid_json"],
                "valid_schema": scored["valid_schema"],
                "predicted_answer": predicted_answer,
                "correct_exact": str(predicted_answer).strip() == ex["gold"]
                if predicted_answer
                else False,
                "latency_seconds": round(latency, 3),
                "prompt_tokens": int(prompt_len),
                "generated_tokens": int(generated_tokens),
                "error": scored["error"],
            }

            output_file.write(json.dumps(row, ensure_ascii=False) + "\n")

            print("=" * 80)
            print(ex["id"])
            print("predicted:", predicted_answer)
            print("gold:", ex["gold"])
            print("correct:", row["correct_exact"])
            print("valid_json:", row["valid_json"])
            print("valid_schema:", row["valid_schema"])

    print("wrote", out_path)


if __name__ == "__main__":
    main()
