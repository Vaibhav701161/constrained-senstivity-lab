from transformers import AutoTokenizer

MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

samples = [
    "0.46",
    " 0.46",
    '"0.46"',
    '{"amount":0.46}',
    '{"amount": 0.46}',
    '{"answer":72}',
    '{"reasoning":"Natalia sold 48 clips."}',
    "answer",
    '"answer"',
    "reasoning",
    '"reasoning"',
    "{",
    '{"',
    '":',
    '": ',
]

for text in samples:
    ids = tokenizer.encode(text, add_special_tokens=False)
    pieces = [tokenizer.decode([token_id]) for token_id in ids]

    print("=" * 80)
    print("TEXT:", repr(text))
    print("TOKEN COUNT:", len(ids))
    print("TOKEN IDS:", ids)
    print("PIECES:", [repr(piece) for piece in pieces])
