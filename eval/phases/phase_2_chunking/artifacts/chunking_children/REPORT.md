# EXT-RQ2-CHILD: Does Parent Expansion Help? (Children-Only Control, Descriptive)

**Protocol:** `reports/revalidation/protocol/ext_rq2_child.json`, registered before the run (protocol record version 5). The script is `rq2ext_children.py`, and its hash matches the record.

**Design:** the same hierarchical children, the same e5 vectors and the same dense ranking feed two context assemblies:
- `hierarchical`: production small-to-big. Children are expanded to their deduplicated parents, with windowing.
- `children_only`: the top children used directly as flat units. Same budget, at most 5 units.

**Primary metric:** CEC@0.5. It stays primary despite the RQ2 fallback, because nDCG is not comparable across these arms. **Caveat:** CEC agreed with the check labels on only 0.667 of cases, and those labels are not an independent human judgment.

## Counts
335 papers, 567 questions, 0 failures. Run time 2 min. Python peak 774 MB.

## Results (paper-cluster bootstrap, B = 10,000, seed 42)

| Arm | CEC@0.3 | CEC@0.5 | CEC@0.7 | Context tokens | Units |
|---|---|---|---|---|---|
| hierarchical | 0.922 | 0.732 | 0.616 | 1,318 | 3.4 |
| children_only | 0.866 | 0.677 | 0.538 | 866 | 5.0 |

**children_only − hierarchical:**

| τ | Diff [95% CI] |
|---|---|
| 0.5 | **−0.055** [−0.082, −0.027] |
| 0.3 | −0.056 [−0.082, −0.032] |
| 0.7 | −0.078 [−0.110, −0.047] |

The CEC@0.5 CI half-width is 0.028, inside the planned ~0.035.

## Interpretation (descriptive; never adopted, per the protocol)
- **Expansion helps.** Expanding the matched children to their parents puts more evidence into the context at every τ.
- **The gain comes with more text.** The context grows from about 870 to about 1,320 tokens. As registered, the difference is the combined effect of expansion and the extra context it supplies, which is what small-to-big means in production.
- **What this adds to RQ2:**
  - Flat 400-token chunking (RQ2-v2) reaches similar coverage by filling the budget with larger chunks.
  - Retrieving small 200-token children without expanding them is clearly worse.
  - So small units help retrieval rank, but they must be expanded before generation.
