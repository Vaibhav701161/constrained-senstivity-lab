import json
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


def extract_json_object(text: str):
    """
    Return (obj, error).
    Try to find the first {...} region and parse it.
    This is intentionally simple and imperfect.
    """
    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        return None, "no_json_braces_found"

    candidate = text[start : end + 1]

    try:
        return json.loads(candidate), None
    except json.JSONDecodeError as e:
        return None, f"json_parse_error: {type(e).__name__}: {e}"


def make_prompt(question: str):
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


def main():
    torch.manual_seed(0)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto",
    )

    out_path = "results/diagnostics/foundational-probes/prompted_json.jsonl"

    with open(out_path, "w", encoding="utf-8") as f:
        for ex in EXAMPLES:
            prompt = make_prompt(ex["question"])
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

            parsed, parse_error = extract_json_object(raw_output)

            valid_schema = False
            schema_error = None

            if parsed is not None:
                try:
                    validate(instance=parsed, schema=SCHEMA)
                    valid_schema = True
                except ValidationError as e:
                    schema_error = str(e)

            predicted = None
            if isinstance(parsed, dict):
                predicted = parsed.get("answer")

            row = {
                "model": MODEL_NAME,
                "condition": "prompted_json",
                "example_id": ex["id"],
                "question": ex["question"],
                "gold": ex["gold"],
                "raw_output": raw_output,
                "parsed": parsed,
                "parse_error": parse_error,
                "valid_schema": valid_schema,
                "schema_error": schema_error,
                "predicted_answer": predicted,
                "correct_exact": str(predicted).strip() == ex["gold"]
                if predicted is not None
                else False,
                "latency_seconds": round(latency, 3),
                "prompt_tokens": int(prompt_len),
                "generated_tokens": len(generated_ids),
            }

            f.write(json.dumps(row, ensure_ascii=False) + "\n")

            print("=" * 80)
            print(ex["id"])
            print("RAW OUTPUT:")
            print(raw_output)
            print("PARSED:", parsed)
            print("VALID_SCHEMA:", valid_schema)
            print("CORRECT:", row["correct_exact"])

    print("wrote", out_path)


if __name__ == "__main__":
    main()
