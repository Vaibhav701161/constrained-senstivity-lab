## Tokenizer observations

1. Did "0.46" tokenize differently from " 0.46"? -- yes , space was tokenized as a seperate token
2. Did JSON context change tokenization? -- 
3. Are `"answer"` and `answer` different token sequences? -- yes  
4. Are `{`, `{"`, and `":` single tokens or multiple tokens? -- yes
5. If a grammar says the next character must be "0", which tokens could satisfy that? -- only this one : "0.46"
6. What surprised me? -- multiple special char where tokenized as single token , in sentences , tokenization happens as gpt-2 paper describes , while in digits tokenization was different then i expected . this is strange !

## LogitsProcessor observations

1. How many digit-containing tokens did I ban? 28
2. Did the model still produce digits somehow? It avoided normal ASCII digits, but produced digit-like circled symbols such as `①`, `②`, and `③`.
3. Did it spell numbers instead? No; it mostly used non-ASCII digit-like symbols and degraded formatting.
4. Did generation become lower quality? Yes. The answer became awkward and partially broken.
5. What does this teach me about hard masking? A mask can block obvious tokens while leaving weird alternate token paths, and generation quality can collapse even in a tiny arithmetic prompt.

## Smoke eval observations

Free correct: 3 / 3
JSON correct: 0 / 3
JSON valid: 0 / 3
Which condition looked easier for the model? Free-form looked easier for this model and extractor.
Did JSON formatting reduce answer quality? It reduced measured quality because the outputs did not parse, even when the visible answer was often present.
Did JSON condition increase latency? Yes, JSON prompts used more prompt tokens and similar or more generation work.
What did my logs miss? The free extractor only takes the last number, so it can score the wrong thing if the model mentions extra numbers after the answer.

Observed JSON failure modes:
- Markdown fenced JSON followed by another fenced block.
- Valid-looking JSON followed by extra prose.
- Multiple JSON objects in one response.

## Day 2 baseline observations

- The RTX 4050 works with the pinned CUDA 12.4 PyTorch wheel.
- Prompted reasoning-first JSON scored 4/20; answer-first scored 1/20.
- Outlines reasoning-first scored 3/20 versus 4/20 for its matched prompted condition.
- Outlines improved schema validity from 55% to 95%, but validity did not imply semantic correctness.
- One Outlines output was deterministically invalid on rerun despite not hitting the token cap.
- The free condition hit its token cap on 8/20 items and needed a last-number fallback on 13/20.
- These results are suggestive only; see `notes/DAY2.md` for the controlled comparisons and limitations.
