import torch
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    LogitsProcessor,
    LogitsProcessorList,
)

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

class BanDigitTokensProcessor(LogitsProcessor):
    def __init__(self, tokenizer):
        self.tokenizer = tokenizer
        self.banned_token_ids = []

        vocab_size = len(tokenizer)

        for token_id in range(vocab_size):
            piece = tokenizer.decode([token_id], skip_special_tokens=False)

            if any(ch.isdigit() for ch in piece):
                self.banned_token_ids.append(token_id)

        print("BANNED TOKEN COUNT:", len(self.banned_token_ids))

    def __call__(self, input_ids, scores):
        # scores shape: [batch_size, vocab_size]
        scores[:, self.banned_token_ids] = -float("inf")
        return scores

def generate(model, tokenizer, prompt, logits_processor=None):
    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    output_ids = model.generate(
        **inputs,
        max_new_tokens=96,
        do_sample=False,
        logits_processor=logits_processor,
        pad_token_id=tokenizer.eos_token_id,
    )

    prompt_len = inputs["input_ids"].shape[1]
    generated_ids = output_ids[0][prompt_len:]
    return tokenizer.decode(generated_ids, skip_special_tokens=True)

def main():
    torch.manual_seed(0)

    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        torch_dtype="auto",
        device_map="auto",
    )

    prompt = """Answer the question.

Question: What is 48 plus 24?

Answer:"""

    print("=" * 80)
    print("NORMAL GENERATION")
    normal = generate(model, tokenizer, prompt)
    print(normal)

    print("=" * 80)
    print("DIGIT-BANNED GENERATION")
    processor = LogitsProcessorList([BanDigitTokensProcessor(tokenizer)])
    banned = generate(model, tokenizer, prompt, logits_processor=processor)
    print(banned)

    with open("results/day0/banned_digits.txt", "w", encoding="utf-8") as f:
        f.write("NORMAL GENERATION\n")
        f.write(normal)
        f.write("\n\nDIGIT-BANNED GENERATION\n")
        f.write(banned)

if __name__ == "__main__":
    main()