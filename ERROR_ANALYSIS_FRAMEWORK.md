# Day 4: Error Analysis Framework for Scientific Document Retrieval (RAG)

> **Document Purpose:** Defines the formal error taxonomy, diagnostic failure classification methodology, and structured error-logging schema for empirical evaluation of the Scientific Document Retrieval pipeline.

---

## 1. Motivation & Principles of Error Analysis

In academic retrieval systems and RAG pipelines, aggregate performance metrics (such as Hit Rate@k, Recall@k, or MRR) reveal *how often* a system succeeds, but provide **zero visibility into why it fails**. 

A system achieving a 90% Hit Rate might suffer from completely distinct bottlenecks:
* Is the missing 10% caused by two-column PDF reading errors?
* Is it caused by arbitrary chunk cuts that separate a premise from its conclusion?
* Is it caused by lexical mismatch between the user's natural query and academic terminology?
* Or is it caused by the language model hallucinating despite retrieving the correct passage?

By systematically classifying every failure case against a formalized taxonomy, we can prioritize engineering effort on the components that degrade retrieval performance the most.

---

## 2. Six-Tier Error Taxonomy for Academic RAG

```
+───────────────────────────────────────────────────────────────────────────+
│                       Academic Document RAG Pipeline                      │
│                                                                           │
│ [PDF File] ──► [Layout Parsing] ──► [Section Chunking] ──► [Embedding]    │
│                        │                      │                  │        │
│                    Tier E1                Tier E2/E3             │        │
│                                                                  ▼        │
│ [Answer & Citation] ◄── [LLM Generation] ◄── [Top-k Rank] ◄── [Vector DB]│
│         │                       │                  │                      │
│      Tier E6                 Tier E6            Tier E4/E5                │
+───────────────────────────────────────────────────────────────────────────+
```

### Tier E1: Document Layout & Physical Extraction Failures
* **E1.1: Multi-Column Flow Bridging:** In two-column academic layouts (e.g. IEEE, ACM, NeurIPS), reading left-to-right across columns rather than top-to-bottom within each column.
* **E1.2: Header / Footer & Pagination Contamination:** Running headers ("Preprint under review"), page numbers, or conference watermarks mistakenly embedded into the middle of extracted paragraphs.
* **E1.3: Mathematical & Equation Mangling:** Complex LaTeX symbols (e.g. $\mathcal{F}(x, \{W_i\}) + x$, $\frac{1}{\sqrt{d_k}}$) parsed as garbled ASCII artifacts or dropped entirely.
* **E1.4: Table & Figure Caption Detachment:** Numerical tables separated from their explanatory captions, leading to ungrounded numerical data chunks.

### Tier E2: Section Structure Detection Failures
* **E2.1: Missed Subsection Boundaries:** Non-numbered or subtle bold subheadings (e.g. `Bottleneck Architecture:`) treated as regular body text rather than new logical section boundaries.
* **E2.2: Heading-Body Merging:** The section title line concatenated directly to the first paragraph sentence, breaking downstream section metadata filters.
* **E2.3: Spurious Section Detection:** Bold bullet points or emphasized terms mistakenly identified as academic section headings.

### Tier E3: Chunk Granularity & Context Fragmentation Failures
* **E3.1: Boundary Severing (The Split-Sentence Problem):** A critical factoid, theorem, or parameter specification is split across two adjacent chunks (e.g., "The dimensionality is" in Chunk 1; "$d_{model}=512$" in Chunk 2).
* **E3.2: Semantic Dilution in Oversized Chunks:** Chunks exceeding 1000 tokens (common in baseline pure section-based chunking) dilute dense embedding representations, lowering cosine similarity against specific targeted queries.
* **E3.3: Loss of Contextual Anchor:** Sub-chunks generated without their parent section title lose their semantic grounding (e.g. "We used 4000 steps" without the context of "5.3 Optimizer").

### Tier E4: Semantic Retrieval & Vocabulary Mismatch Failures
* **E4.1: Lexical Gap (Synonymy Mismatch):** The user query uses colloquial or high-level phrasing ("How fast is it during inference?") while the paper uses formal terminology ("introduces zero additional inference latency").
* **E4.2: Generic Passage Collision:** Dense or BM25 retriever ranks general introductory survey text higher than the specific technical section because the introduction repeats the query keywords multiple times.

### Tier E5: Ranking & Top-$k$ Truncation Failures
* **E5.1: Top-$k$ Omission ($k > 5$):** The ground-truth evidence chunk is successfully retrieved by the vector index but ranked at position $k=6$ or $k=7$, falling outside the context window fed to the generator.
* **E5.2: Redundancy Clustering:** Top 3 retrieved slots are monopolized by nearly identical overlapping chunks from the same page, crowding out complementary evidence from subsequent pages.

### Tier E6: Generation, Faithfulness & Hallucination Failures
* **E6.1: Parametric Prior Leakage:** The LLM answers the question correctly from its internal pre-training weights, but ignores or contradicts the specific nuances stated in the retrieved chunk.
* **E6.2: Extrapolative Hallucination:** The LLM invents technical details, hyperparameter values, or benchmark rankings not supported by the retrieved evidence.
* **E6.3: Citation Attribution Error:** The LLM generates the correct answer, but attributes the citation badge to the wrong section or page.

---

## 3. Standardized Failure Logging Schema

When running benchmark evaluation scripts, any query that fails to achieve a Hit@1 or produces an ungrounded answer is recorded in a standardized JSON error log:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "RetrievalFailureRecord",
  "type": "object",
  "properties": {
    "query_id": { "type": "string" },
    "paper_arxiv_id": { "type": "string" },
    "question": { "type": "string" },
    "strategy_evaluated": { "type": "string", "enum": ["section", "section_token", "section_overlap"] },
    "failure_category": { 
      "type": "string", 
      "enum": ["E1_LAYOUT", "E2_STRUCTURE", "E3_CHUNKING", "E4_RETRIEVAL", "E5_RANKING", "E6_GENERATION"] 
    },
    "sub_category": { "type": "string" },
    "observed_rank": { "type": ["integer", "null"] },
    "retrieved_chunk_ids": { "type": "array", "items": { "type": "string" } },
    "expected_target_section": { "type": "string" },
    "expected_target_page": { "type": "integer" },
    "root_cause_diagnosis": { "type": "string" },
    "remediation_action": { "type": "string" }
  },
  "required": ["query_id", "failure_category", "root_cause_diagnosis", "remediation_action"]
}
```

---

## 4. Real-World Diagnostic Case Studies

### Case Study 1: The Token Dilution Failure in Baseline Section Chunking
* **Query ID:** `Q_ATTN_01` ("What is the dimensionality ($d_{model}$) across all layers in the base Transformer model?")
* **Strategy:** `section` (Strategy A - Pure Section Baseline)
* **Observed Failure:** The entire Section 3 ("Model Architecture") is 1,480 tokens long. In dense retrieval, averaging token embeddings over 1,480 tokens washes out the specific mention of `$d_{model} = 512$`. A shorter introductory section discussing model dimension ranks higher.
* **Root Cause Category:** `E3.2: Semantic Dilution in Oversized Chunks`.
* **Remediation:** Apply Strategy B/C (`section_token` or `section_overlap`) with `max_tokens=400`. Splitting into sub-sections isolates the encoder stack paragraph, raising cosine similarity and boosting rank to Position 1.

### Case Study 2: The Context Severing Failure in Token-Limited Chunking
* **Query ID:** `Q_LORA_02` ("How are matrices A and B initialized before training begins?")
* **Strategy:** `section_token` (Strategy B - Token Limit without Overlap)
* **Observed Failure:** The sentence "We use a random Gaussian initialization for A" ended at character 1,598, exactly at the 400-token boundary. The subsequent sentence "and zero for B, so Delta W = BA = 0" landed in the next chunk. The retriever only retrieved the first chunk, leaving the model unable to state how matrix B was initialized.
* **Root Cause Category:** `E3.1: Boundary Severing (The Split-Sentence Problem)`.
* **Remediation:** Apply Strategy C (`section_overlap`) with `overlap=80 tokens`. The overlapping sliding window ensures both initialization clauses exist in the same retrieved passage.

### Case Study 3: The Lexical Gap in High-Level Queries
* **Query ID:** `Q_LORA_04` ("Does LoRA introduce any inference latency overhead compared to full fine-tuning?")
* **Strategy:** Lexical Retrieval (BM25)
* **Observed Failure:** Query uses word "overhead", which does not appear in the text. The paper states: "no additional inference latency". BM25 fails to match the query term.
* **Root Cause Category:** `E4.1: Lexical Gap (Synonymy Mismatch)`.
* **Remediation:** In final phase, combine dense semantic embeddings with BM25 (Hybrid Sparse-Dense Retrieval).

---

## 5. Midterm Defense Presentation Guidelines (Slide 9 & 10)

When presenting this framework to the examination committee:
1. **Highlight the Scientific Approach:** Explain that accuracy metrics alone are unscientific; a rigorous engineering project must diagnose root causes.
2. **Showcase the Chunking Evolution:** Demonstrate how moving from **Baseline Section Chunking $\rightarrow$ Section with Token Limit $\rightarrow$ Section with Overlapping Sliding Window** systematically eliminates Tier E3.1 and Tier E3.2 errors.
3. **Set the Stage for the Final Defense:** Conclude that having fixed this error analysis taxonomy, your final phase will introduce Hybrid Search to target Tier E4 (lexical gaps) and Reranking to target Tier E5 (top-$k$ truncation).
