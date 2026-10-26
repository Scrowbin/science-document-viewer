# DEC-03: Final End-to-End Evaluation Protocol and Governance (Stage C4 — Pre-Inference Protocol Revision)

*Document Status:* **Final Protocol Specification (Stage C4 Revised / NFR-03 Production Alignment / 250-Paper Main Evaluation Target)**
*Canonical Location:* [`eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md)
*Canonical Experiment Provenance Registry:* [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json)
*Provenance Registry Documentation:* [`eval/EXPERIMENT_PROVENANCE_REGISTRY.md`](file:///c:/DACNTT/eval/EXPERIMENT_PROVENANCE_REGISTRY.md)
*Overlap Audit Utility:* [`eval/scripts/check_experiment_overlap.py`](file:///c:/DACNTT/eval/scripts/check_experiment_overlap.py)
*Prerequisite Exposure Audit:* [`eval/phases/phase_9_generation/artifacts/DEC03_EXPOSURE_AUDIT.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_EXPOSURE_AUDIT.md)
*Machine-Readable Exposure Artifact:* [`eval/phases/phase_9_generation/artifacts/dec03_exposure_overlap_report.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/dec03_exposure_overlap_report.json)
*Canonical Audit Change Log:* [`PROTOCOL_AUDIT_CHANGELOG.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/PROTOCOL_AUDIT_CHANGELOG.md)
*Workspace Root:* `c:\DACNTT`

---

## 1. Governance Context and Objective

The objective of this protocol is to specify a rigorous, reproducible end-to-end evaluation procedure for the Scientific Document Manager RAG system without misrepresenting prior dataset exposure or overstating experimental independence.

### Key Audit Findings Governing This Protocol:
1. **Prior Exposure Boundary:** The official QASPER Test set (408 papers / 1,310 queries) was previously evaluated during RQ4 retrieval benchmarking. It is therefore **not an untouched or unexposed confirmatory set** for the full RAG pipeline. Any full-pipeline evaluation on it represents a *post-retrieval-selection evaluation*.
2. **Experiment-Unexposed Reservoir:** Exactly **777 papers (2,154 total questions)** from the official QASPER Train split are **unexposed to the identified experiments (RQ1–RQ5)** within this project's development history.
3. **Data Provenance Distinction:** Because this reservoir originates from QASPER Train, it shares the same domain distribution and crowdworker collection methodology as Dev and Test. It represents an *experiment-unexposed paper cohort drawn from QASPER Train*, and must **not** be described as an independent or pristine holdout.
4. **Reconciled Split-Wide Count Matrix and Arithmetic Parity:**
   Every category below has been verified by direct programmatic parsing of raw JSON files on disk. Every partition satisfies exact arithmetic equality:

| Partition / Cohort | Papers | Total Questions | Retrieval-Eligible (Text Evidence) | Answer-Gen Eligible (Usable Answer) | Atomic End-to-End Eligible | Float-Only Answerable | Strictly Unanswerable | Decoupled Annotations | Checksum Parity |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **QASPER Train (Total)** | 888 | 2,593 | 2,101 | 2,322 | 2,101 | 221 | 271 | 0 | $2,101 + 221 + 271 = 2,593$ |
| ├── **RQ3 Train Cohort** | 111 | 439 | 372 | 406 | 372 | 34 | 33 | 0 | $372 + 34 + 33 = 439$ |
| └── **Unexposed Reservoir** | 777 | 2,154 | 1,729 | 1,916 | 1,729 | 187 | 238 | 0 | $1,729 + 187 + 238 = 2,154$ |
| **QASPER Dev (Total)** | 281 | 1,005 | 892 | 945 | 892 | 53 | 60 | 0 | $892 + 53 + 60 = 1,005$ |
| **QASPER Test (Total)** | 416 | 1,451 | 1,310 | 1,372 | 1,310 | 62 | 79 | 0 | $1,310 + 62 + 79 = 1,451$ |

5. **Paper Distribution in the 777-Paper Reservoir by End-to-End Eligible Questions ($m \ge 2$):**
   - Papers with $\ge 2$ end-to-end eligible questions: **487 papers** (contains 1,503 eligible questions)
   - Papers with exactly 1 end-to-end eligible question: **226 papers** (`EXCL_FEWER_THAN_2_ELIGIBLE_QUESTIONS`)
   - Papers with 0 end-to-end eligible questions: **64 papers** (`EXCL_ZERO_ELIGIBLE_QUESTIONS`)
   - *Total unexposed papers:* $487 + 226 + 64 = \mathbf{777\text{ papers}}$ (exact arithmetic parity).
   - *Sampling Feasibility for 250 Papers:* Since $487 \ge 250$, targeting $K=250$ papers leaves a **surplus reserve of $+237$ eligible papers**, guaranteeing full feasibility without weakening eligibility rules.

6. **Reconciliation of Historical Exposure Counts (804 vs 802 Unique Papers):**
   - **804 Unique Exposed Papers (Partition-Level Historical Total):** Exactly $111\text{ Train (RQ3)} + 281\text{ Dev (entire Dev split partition)} + 408\text{ Test (evaluated in RQ4 Test)} + 4\text{ Seed (RQ5 Pilot)} = \mathbf{804\text{ papers}}$.
   - **802 Unique Exposed Papers (Active Benchmark Run Total):** Exactly $111\text{ Train} + 279\text{ Dev (active runs)} + 408\text{ Test} + 4\text{ Seed} = \mathbf{802\text{ papers}}$.
   - *Resolution of Arithmetic Discrepancy:* In the official QASPER Dev split (281 papers), exactly 2 papers (`1804.00720` and `1903.07406`) contained exclusively unanswerable questions with zero text evidence paragraphs and were omitted from experimental benchmark runs in RQ1–RQ4 ($281 - 2 = 279$ Dev papers with active runs). The sum $111 + 281 + 408 + 4$ equals strictly **804**, not 802. Writing $111 + 281 + 408 + 4 = 802$ was an arithmetic error that mistakenly substituted the 281 partition count while reporting the 802 active-run total.
   - *Impact on Train Candidate Pool:* **Identically Zero.** Both counting methods confirm that the 777-paper Train reservoir and 487-paper candidate pool have **strictly zero prior exposure** across all repository experiments.

---

## 2. Evaluation Options Assessment

| Option | Description & Feasibility | Annotation & Computational Burden | Justified Claims | Limitations & Unjustified Claims |
| :--- | :--- | :--- | :--- | :--- |
| **Option A: Reused QASPER Test Set** | Frozen end-to-end run across the 408 QASPER Test papers (1,310 queries). | **Low burden:** Ground-truth and chunk caches already exist. High CPU runtime (~10–12 hours for LLM generation). | End-to-end system performance across the published test benchmark; comparability with existing literature. | **Cannot claim independent generalization.** Must be explicitly reported as *post-retrieval-selection evaluation*, not an untouched confirmatory test set. |
| **Option B: Unexposed Train Reservoir Holdout (Target Primary — 250 Papers)** | Paper-clustered sample ($K=250$ papers, $m=2$ questions, $N=500$ questions, $1,500$ model outputs) drawn from the 487 eligible unexposed Train papers. | **Moderate-to-High burden:** ~3.0 hours of claim-level review across 60 sampled outputs (Option A approved). ~2.0–2.5 hours CPU runtime. | **Evaluation on 250 papers and 500 queries with zero prior exposure in the project's history.** Substantial reduction in estimation standard error (55.3% reduction in SE vs $K=50$, $df=249$). Defensible thesis governance. | Paper-clustered design; shares QASPER collection methodology; does not guarantee normality or adequate statistical power for arbitrary effect sizes; does not eliminate potential pre-training exposure in LLM base weights. |
| **Option C: External Dataset (SciFact / BioASQ)** | Benchmarking on an external corpus. | **High burden:** Severe task mismatch. SciFact evaluates abstract claim verification; BioASQ lacks PDF coordinates. | Out-of-domain transfer of dense retrieval representations. | Does **not** evaluate long-form document question answering with PDF citation coordinates. |

### Strategic Recommendation:
- **Primary Thesis Standard: Option B (250 Papers).** A high-precision paper-clustered sample ($K=250$ papers, $m=2$ questions, $N=500$ questions, $1,500$ model responses) drawn from the 487 eligible unexposed Train papers, providing an evaluation free from prior pipeline exposure.
- **Complementary Benchmark: Option A.** Run the frozen pipeline across the full QASPER Test set and report the results in Chapter 5 with explicit disclosure of prior retrieval benchmarking.

### 2.1. Candidate Embedding Shortlist for Downstream Combination Testing (RQ6 Alignment)
While RQ5 evaluates candidate Small Language Models (`qwen2.5:0.5b`, `llama3.2:1b`, `llama3.2:3b`) under fixed gold context to isolate generator faithfulness, the downstream End-to-End Combination Benchmark (RQ6 / Chapter 6) integrates the generator with the multi-stage retrieval pipeline. To avoid an intractable combinatorial explosion ($11\text{ embedders} \times 4\text{ retrieval fusion strategies} \times 3\text{ LLMs} = 132\text{ pipelines}$), **3 representative embedding models** spanning the empirical Pareto frontier established in RQ3 are shortlisted for combination testing:

| Tier / Role | Shortlisted Representative | Parameters / Dims | RQ3 nDCG@10 | Query Latency P50 | Indexing Throughput | Peak Process RAM |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **Efficiency Baseline** | **`all-MiniLM-L6-v2`** | 22.7M (384-d) | 0.5026 | **19.30 ms** | **19.0 chunks/s** | **593.1 MB** |
| **Balanced Champion (System Choice)** | **`intfloat/e5-small-v2`** | 33.4M (384-d) | 0.5522 | **30.26 ms** | **6.5 chunks/s** | **659.8 MB** |
| **Quality Ceiling Champion** | **`modernbert-embed-base`** | 149.0M (768-d) | **0.5872** | **103.39 ms** | **1.8 chunks/s** | **1,161.7 MB** |

#### Why These 3 Models Were Selected
1. **`all-MiniLM-L6-v2` (Efficiency Baseline):** Fastest dense model in the benchmark ($3\times$ faster indexing than E5-Small, sub-20 ms query latency, 593.1 MB RAM). Serves as the minimal-overhead anchor to determine whether higher semantic retrieval accuracy actually yields measurable downstream gains in generated answer quality.
2. **`intfloat/e5-small-v2` (Balanced Production Choice):** Optimal Pareto trade-off point on desktop CPUs. Statistically significant retrieval gain over baseline ($\Delta = +0.0497^*, p = 0.0010^*$), low latency (30.26 ms), and light RAM (659.8 MB). Deployed as the default embedder in the application and tested in RQ4.
3. **`modernbert-embed-base` (Quality Ceiling Champion):** Highest retrieval accuracy in the benchmark (nDCG@10 = 0.5872, $\Delta = +0.0846^*$, nDCG@4 = 0.4937) with native 8,192-token context window. Evaluates whether a $3.4\times$ latency and $3.6\times$ throughput penalty translates to downstream LLM faithfulness and hallucination reduction.

---

## 3. Question Eligibility Rules and Canonical Implementation

### 3.1. Deterministic Eligibility Rules
A question $q$ in candidate paper $p$ is evaluated under three deterministic, documented eligibility categories:

1. **Rule 1: Retrieval Eligibility:**
   - A question $q$ is retrieval-eligible if and only if at least one annotator annotation $a \in q.\text{answers}$ provides $\ge 1$ non-empty, non-float text evidence paragraph:
     $$\exists a \in q.\text{answers} : \text{any}(\text{"FLOAT SELECTED"} \notin e \land e.\text{strip}() \neq \text{""} \text{ for } e \in a.\text{evidence})$$
   - *Count in 777 Unexposed Train:* **1,729 questions**.
2. **Rule 2: Answer-Generation Eligibility:**
   - A question $q$ is answer-generation-eligible under the benchmark policy if and only if at least one annotator annotation $a \in q.\text{answers}$ provides a usable reference answer:
     $$\exists a \in q.\text{answers} : a.\text{unanswerable} == \text{False} \land \Big(\text{any}(s.\text{strip}() \neq \text{""} \text{ for } s \in a.\text{extractive\_spans}) \lor (a.\text{free\_form\_answer} \land a.\text{free_form_answer}.\text{strip}() \neq \text{""}) \lor (a.\text{yes\_no} \neq \text{None})\Big)$$
   - *Note on Boolean Answers:* $a.\text{yes\_no} \neq \text{None}$ correctly captures both $a.\text{yes\_no} == \text{True}$ ("Yes") and $a.\text{yes\_no} == \text{False}$ ("No").
   - *Count in 777 Unexposed Train:* **1,916 questions** (includes 1,729 text-evidenced + 187 float/table-only questions).
3. **Rule 3: End-to-End Eligibility (Atomic Joint Grounding Rule):**
   - A question $q$ is end-to-end eligible if and only if there exists **at least one annotator annotation $a \in q.\text{answers}$** that simultaneously satisfies BOTH conditions in the *same annotation object*:
     - (a) $a.\text{unanswerable} == \text{False}$ with a usable reference answer (Rule 2), AND
     - (b) $a.\text{evidence}$ contains $\ge 1$ valid non-float text evidence paragraph (Rule 1).
   - *Count in 777 Unexposed Train:* **1,729 questions**.

### 3.2. Structural Verification of QASPER Annotations
To address the risk of decoupled annotations (e.g., text evidence in annotator A, but reference answer in annotator B):
- **Verification Across All 5,049 QASPER Questions:** Across Train (2,593), Dev (1,005), and Test (1,451), there are exactly **0 decoupled questions** (`decoupled_count = 0`). Whenever an annotator highlights text evidence, they atomically provide the reference answer in the exact same answer object.
- **Verification of Unanswerable Evidence:** In 100% of cases, no annotator ever marks `unanswerable: true` while providing text evidence (`ev_unans_count = 0`).
- **Identity of Rule 1 and Rule 3 Sets:** In QASPER v0.3, every retrieval-eligible question is atomically end-to-end eligible within the same annotator object ($1,729 = 1,729$).
- **Multi-Annotator Ambiguity Audit:**
  - 48 questions in the 777 reservoir have 2 annotators.
  - 41 have complete agreement with both annotators providing usable answers.
  - 6 have split votes: one annotator found text evidence and answered, while the second marked unanswerable with 0 evidence. All 6 retain a valid atomic text-evidence + answer pair and are evaluated under the standard max-over-annotators SQuAD/QASPER protocol.
  - 1 question has unanimous unanswerable consensus (`f7070b2e258beac9b09514be2bfcc5a528cc3a0e`) and is excluded.

### 3.3. Deterministic Exclusion Logging
Questions failing eligibility are logged in the manifest with explicit exclusion codes:
- `EXCL_FLOAT_ONLY_EVIDENCE` (187 questions): Answer provided, but evidence is exclusively located in tables or figures (`FLOAT SELECTED:`).
- `EXCL_STRICTLY_UNANSWERABLE` (238 questions): Marked unanswerable across all annotators.
- `EXCL_RQ3_EXPOSURE` (111 papers): Papers previously included in RQ3 embedding benchmarking.
- `EXCL_FEWER_THAN_2_ELIGIBLE_QUESTIONS` (226 papers): Papers with exactly 1 eligible question (ineligible for the $m=2$ design).
- `EXCL_ZERO_ELIGIBLE_QUESTIONS` (64 papers): Papers with 0 eligible questions.

### 3.4. Methodological Boundary of Eligibility vs. Evidence Sufficiency
- **What Eligibility Rules Establish:** Rule 3 (Atomic End-to-End Eligibility) proves that for every selected question, at least one annotator provided a usable reference answer and highlighted $\ge 1$ non-empty, non-float text paragraph in the same annotation object.
- **What Eligibility Rules Do NOT Establish:** Passing Rule 3 does **not** prove that the highlighted paragraph(s) provide a complete, self-contained semantic basis to derive the reference answer without external world knowledge, unstated domain assumptions, or adjacent context. In academic question-answering benchmarks, crowdworkers frequently under-highlight or omit prerequisite introductory context.
- **Consequences for Generator Evaluation:** Under an anti-hallucination prompt that explicitly forbids extrapolation and commands refusal when context is insufficient, language models may refuse on questions where evidence is partial or ambiguous, even though a human annotator wrote an answer. Therefore:
  1. The impact of the prompt change on model refusal rates and Answer Token $F_1$ is an empirical outcome to be observed and reported, not assumed to be negligible a priori.
  2. Model refusals must be tracked explicitly (`is_refusal`, `refusal_count`, `refusal_rate_pct`) across all three models to assess whether stricter grounding suppresses valid answers or properly blocks ungrounded speculation.

---

## 4. Finalized Deterministic Sampling Design (250-Paper Main Evaluation)

> [!IMPORTANT]
> **Non-Execution Notice:** In strict adherence to Stage C2.8 stop conditions, **no final sample has been drawn**. The procedure below specifies the deterministic algorithm to be executed only after formal approval.

### 4.1. Design Characterization and Prerequisite Check
- **Design:** High-precision paper-clustered evaluation design ($K=250$ papers, $m=2$ questions per paper, total $N=500$ questions, $1,500$ total model outputs across the 3 candidate models).
- **Prerequisite Validation:** The pool of experiment-unexposed Train papers with $\ge 2$ end-to-end eligible questions contains **487 papers**. Since $487 \ge 250$, the prerequisite condition is fully satisfied with a **surplus reserve margin of $+237$ eligible papers**.
- **Statistical Characterization:** Expanding the target from $K=50$ to $K=250$ papers reduces estimation standard error $\text{SE}(\bar{D}) = s_{\bar{D}} / \sqrt{K}$ by a factor of $\sqrt{5} \approx 2.236$ (a **55.3% reduction in estimation uncertainty**). Degrees of freedom increase from $df = 49$ to $df = 249$ (critical value $t_{0.975, 249} \approx 1.9695$). **Crucial Methodological Caveat:** A sample size of $K=250$ does **NOT** guarantee that the sampling distribution of paper mean differences is strictly normal, nor does it guarantee adequate statistical power for arbitrary effect sizes. Because Answer Token F1 differences are bounded in $[-1, 1]$ and discrete, point-mass spikes at zero (where models achieve identical performance) and empirical skewness can persist. The paired $t$-test is therefore treated strictly as an approximate inferential procedure whose validity depends on independence and distributional assumptions, cross-checked with the pre-registered non-parametric (Wilcoxon), trimmed-mean, and cluster-jackknife sensitivity protocols. A difference threshold of $\Delta = 0.030$ is retained strictly as an unvalidated exploratory practical-effect threshold (heuristic representing a 3 percentage-point shift in Answer Token F1, borrowed from prior retrieval SESOI conventions), not a formal statistical significance cutoff.

### 4.2. Stratification Policy
- **Natural Distribution Preservation:** Paper and question selection will use **uniform random sampling** without artificial post-hoc stratification quotas by answer type (extractive, abstractive, boolean) or answer length.
- *Rationale:* Papers contain varying mixtures of answer types. Enforcing rigid per-paper quotas would reject valid papers and distort the natural paper-level distribution.
- *Distribution Tracking:* The natural distribution in the 487-paper candidate pool is ~62% extractive, ~23% abstractive, ~15% boolean. For every selected question, its answer type, reference length, and evidence length are recorded in the manifest, enabling stratified metric reporting (Answer F1 by type) matching official `qasper_evaluator.py`.

### 4.3. Deterministic Paper and Question Selection Algorithm
```python
import hashlib
import json
import random
from typing import Any, Dict, List

def generate_sample_manifest_250(
    train_data_path: str = "eval/data/qasper_official/qasper-train-v0.3.json",
    rq3_split_path: str = "eval/prepared/expanded_held_out_split.json",
    seed: int = 42,
    target_k: int = 250,
    standby_k: int = 50,
    m: int = 2
) -> Dict[str, Any]:
    # 1. Load data and identify the 777 unexposed Train papers
    with open(train_data_path, "r", encoding="utf-8") as f:
        train_data = json.load(f)
    with open(rq3_split_path, "r", encoding="utf-8") as f:
        rq3_pids = set(json.load(f).get("held_out_papers", []))
    unexposed_train = {pid: p for pid, p in train_data.items() if pid not in rq3_pids}

    # 2. Identify end-to-end eligible questions for each paper (canonical implementation)
    paper_eligible_map: Dict[str, List[Dict[str, Any]]] = {}
    for pid, pdata in unexposed_train.items():
        eligible_qs = []
        for qa in pdata["qas"]:
            # Check atomic joint grounding: same annotator has usable answer and non-float text evidence
            atomic_ann = [
                a["answer"] for a in qa["answers"]
                if not a["answer"].get("unanswerable", False) and
                any("FLOAT SELECTED" not in t and t.strip() for t in a["answer"].get("evidence", [])) and
                (any(s.strip() for s in a["answer"].get("extractive_spans", [])) or
                 (a["answer"].get("free_form_answer") and a["answer"].get("free_form_answer").strip()) or
                 a["answer"].get("yes_no") is not None)
            ]
            if atomic_ann:
                eligible_qs.append(qa)
        if len(eligible_qs) >= m:
            paper_eligible_map[pid] = eligible_qs

    # 3. Stable sorting: Sort candidate paper IDs lexicographically ascending
    candidate_pids = sorted(paper_eligible_map.keys())  # exactly 487 papers

    # 4. Deterministic shuffle and split
    rng = random.Random(seed)
    shuffled_pids = list(candidate_pids)
    rng.shuffle(shuffled_pids)

    primary_pids = sorted(shuffled_pids[:target_k])             # 250 primary papers
    standby_pids = shuffled_pids[target_k:target_k+standby_k]    # 50 pre-registered reserve papers

    # 5. Deterministic question selection per paper
    selected_items: List[Dict[str, Any]] = []
    for pid in primary_pids:
        # Sort questions lexicographically by 40-char question_id hash ascending
        q_pool = sorted(paper_eligible_map[pid], key=lambda x: x["question_id"])
        # Deterministic paper-specific sub-seed
        sub_seed = seed + int(hashlib.sha256(pid.encode()).hexdigest()[:8], 16)
        paper_rng = random.Random(sub_seed)
        chosen_qs = sorted(paper_rng.sample(q_pool, m), key=lambda x: x["question_id"])

        for q in chosen_qs:
            selected_items.append({
                "item_index": len(selected_items) + 1,
                "paper_arxiv_id": pid,
                "question_id": q["question_id"],
                "question_text": q["question"],
                "answers": q["answers"],
            })

    return {
        "manifest_metadata": {
            "seed": seed,
            "target_k": target_k,
            "standby_k": standby_k,
            "m": m,
            "candidate_pool_size": len(candidate_pids),
            "standby_queue": standby_pids,
            "replacement_log": []
        },
        "selected_eval_items": selected_items
    }
```

### 4.4. Approved Standby Replacement Queue and Objective Failure Rules
- **Approved Standby Queue:** Exactly **50 reserve papers** (indices 250..299 of the deterministic shuffle) are pre-registered in `manifest_metadata.standby_queue`.
- **Eligibility Timing:** Question eligibility is established strictly on official QASPER JSON annotations *before* physical PDF ingestion is attempted.
- **Objective Failure Criteria Justifying Standby Replacement:**
  A primary paper may be replaced if and only if it encounters one of the following verifiable technical PDF ingestion failures:
  1. `EXCL_PDF_HTTP_FETCH_FAILED`: Persistent arXiv HTTP 404, 403, or connection failure after 3 automated retries with 5s exponential backoff.
  2. `EXCL_PDF_CORRUPTED_BINARY`: PyMuPDF `fitz.open()` throws `fitz.FileDataError` or file lacks valid `%PDF-` magic bytes.
  3. `EXCL_PDF_ZERO_SECTIONS_EXTRACTED`: PDF layout extraction yields 0 text sections or total extracted body text < 100 characters (e.g. un-OCRed scanned bitmap).
- **Strict Anti-Bias and Anti-Replacement Prohibitions:**
  - **MANDATORY ANTI-BIAS RULE: NEVER replace a paper based on question difficulty, model-output quality, answer correctness, refusal, low retrieval score, or inconvenient results.**
  - Replacement from the standby queue occurs strictly in pre-registered rank order (index 250, then 251, etc.) and must be logged in `manifest_metadata.replacement_log` with timestamp, failed paper ID, error traceback, and replacement paper ID.
- **Reserve Exhaustion Hard Stop Rule:**
  - If all 50 pre-registered reserve papers are exhausted and fewer than 250 valid papers remain, **STOP IMMEDIATELY and request user approval** rather than silently changing the sample size, drawing un-registered papers, or altering the design.

### 4.5. Manifest Schema and Recorded Fields
The frozen manifest artifact (`eval_sample_manifest_500q.json`) must record:
1. `manifest_metadata`: Seed, date, code version, total candidate pool, standby queue, replacement log, checksums.
2. `selected_eval_items` ($N=500$ items):
   - `item_index`: Integer 1..500.
   - `paper_arxiv_id`: Clean arXiv ID.
   - `question_id`: 40-character SHA hash.
   - `question_text`: Verbatim question string.
   - `question_type`: Extractive, abstractive, or boolean.
   - `ground_truth_references`: List of all usable annotator answers with worker ID and answer type.
   - `ground_truth_evidence`: List of paragraph text strings.
   - `eligibility_status`: `ELIGIBLE_E2E`.
3. `exclusion_manifest`: Complete registry of all 777 papers and 2,154 questions, categorizing every non-selected item with its formal exclusion code and count.

### 4.6. Frozen Production-Aligned Prompt Specification (Stage C4 Refinement)
- **Specification Source & Requirement Citation:**
  The evaluation prompt is strictly aligned with the non-functional requirement **NFR-03** documented in the system specification ([`DU_AN_CNTT_TOAN_VAN.md`](file:///c:/DACNTT/DU_AN_CNTT_TOAN_VAN.md) Table 4.2 / [`docs/CHAPTER4_DRAFT.md`](file:///c:/DACNTT/docs/CHAPTER4_DRAFT.md) Table 4.2):
  > *"NFR-03: Ngăn ngừa ảo giác và Tiếp đất học thuật — Mô hình AI chỉ được trả lời dựa trên ngữ cảnh trích xuất từ tài liệu. Khi điểm tương đồng ngữ nghĩa rơi vào vùng bất đối xứng không liên quan (< 0,80), hệ thống bắt buộc kích hoạt cơ chế từ chối (Refusal Guardrail), không được suy diễn ngụy tạo."*
  and the production service implementation in [`backend/apps/documents/services/rag_service.py`](file:///c:/DACNTT/backend/apps/documents/services/rag_service.py#L1276-L1335):
  `REFUSAL_MESSAGE = "The document does not contain sufficient relevant information to answer this question."`
- **Pre-Inference Protocol Refinement:**
  Prior to live model inference, the preliminary pilot prompt instruction (*"If the answer is not contained in the context, synthesize the most relevant details available"*) was identified as methodologically contradictory: it encouraged ungrounded speculation, confounded faithfulness evaluation, and diverged from production behavior. It is permanently replaced by the grounded refusal directive.
- **Exact Frozen Evaluation Prompt Template:**
  ```text
  You are a precise academic research assistant reading "{doc_title}".
  Use ONLY the provided context below to answer the user's question clearly and accurately.
  If the answer is not contained in the context, state clearly: 'The document does not contain sufficient relevant information to answer this question.'
  Do NOT extrapolate, speculate, or fabricate details beyond the provided context.

  Context:
  {context}

  Question: {question}

  Answer:
  ```
- **Controlled Application:** This prompt template is frozen and applied identically across all three candidate models (`llama3.2:3b`, `llama3.2:1b`, `qwen2.5:0.5b`) under greedy decoding (`temperature=0.0`, `num_predict=256`).

---

## 5. Statistical Analysis Specification

All comparative evaluations between candidate language models must follow the paper-cluster paired bootstrap protocol:

### 5.1. Pre-Registered Primary Metric and Pairwise Comparisons
- **Primary Metric:** Answer Token F1 (harmonic mean of normalized precision and recall, max over annotator references).
- **Pre-Registered Model Comparisons:** Defined strictly prior to observing outputs:
  - Comparison 1: `llama3.2:3b` vs. `llama3.2:1b`
  - Comparison 2: `llama3.2:3b` vs. `qwen2.5:0.5b`
  - Comparison 3: `llama3.2:1b` vs. `qwen2.5:0.5b`
- **Secondary Metrics & Measurement Reporting:**
  - `is_refusal` and **Refusal Rate (%):** Frequency and percentage of queries returning `REFUSAL_MESSAGE`. A refusal is not inherently faithful; its validity is evaluated conditionally based on context sufficiency.
  - **Automated Context Containment Proxy (%):** Automated token-level heuristic measuring the proportion of informative non-stopword prediction tokens present verbatim in prompt context (0.0% on refusal). Explicitly characterized as an automated lexical proxy, NOT a complete measure of semantic faithfulness or factual entailment.
  - **Human Claim-Level Faithfulness Review (% Supported):** Qualitative audit across the 60 sampled answers (Option A), evaluating atomic claims into `SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, and answer-level omissions/refusals.
  - **Efficiency & Footprint:** End-to-end latency (P50/P95 in ms), single-query throughput (tokens/s), Peak RAM (RSS in MB: Python, Ollama, Sum).

### 5.2. Observed Effect Size Calculation
For each pairwise model comparison (Candidate vs. Baseline):
$$\Delta_{\text{obs}} = \bar{S}_{\text{cand}} - \bar{S}_{\text{base}} = \frac{1}{N}\sum_{i=1}^N (S_{\text{cand}, i} - S_{\text{base}, i})$$
where $N = 500$ questions across the $K=250$ papers ($m=2$ questions per paper).

### 5.3. Paper-Cluster Paired Bootstrap Algorithm & Confidence Interval (Estimation)
1. **Cluster Unit:** Resample the $K=250$ selected paper IDs with replacement.
2. **Cluster Inclusion:** For each resampled paper ID, include both evaluated questions ($m=2$), maintaining the intra-cluster correlation ($N=500$ total questions per bootstrap replicate).
3. **Shared Cluster Resampling Across Models:** Use the **exact same resampled paper IDs** across candidate models in every replicate $b \in \{1, \dots, B\}$ ($B=2,000$, `seed = 42`) to compute the paired bootstrap difference:
   $$\Delta_b^* = \frac{1}{N}\sum_{p \in \mathcal{P}_b^*} \sum_{q \in \mathcal{Q}_p} (S_{\text{cand}, p, q} - S_{\text{base}, p, q})$$
4. **95% Bootstrap Confidence Interval:** Compute the empirical percentile interval $[\Delta_{2.5\%}^*, \Delta_{97.5\%}^*]$ from the sorted distribution of $\Delta_b^*$.
5. **Methodological Role of Bootstrap Distribution:** The bootstrap distribution approximates sampling uncertainty around the observed point estimate $\Delta_{\text{obs}}$ ($\mathbb{E}_*[\Delta_b^*] = \Delta_{\text{obs}}$). It represents parameter estimation uncertainty, not a null sampling distribution.

### 5.4. Hypothesis Testing: Approved Paper-Level Paired t-Test and Outlier Sensitivity Protocol
1. **Approved Primary Hypothesis Testing Procedure:**
   The formal hypothesis testing procedure across the 3 pre-registered comparisons is the **Paper-Level One-Sample Paired $t$-Test on the 250 Paper Mean Paired Differences ($df = 249$)** with **Holm–Bonferroni step-down multiple-testing correction**.
   - For each paper cluster $p \in \{1, \dots, 250\}$, compute the paper mean paired difference:
     $$\bar{D}_p = \frac{1}{2}\sum_{q=1}^2 (S_{\text{cand}, p, q} - S_{\text{base}, p, q}) \in [-1, 1]$$
   - Sample mean difference: $\bar{D} = \Delta_{\text{obs}} = \frac{1}{250}\sum_{p=1}^{250}\bar{D}_p$.
   - Sample standard deviation of paper means: $s_{\bar{D}} = \sqrt{\frac{1}{249}\sum_{p=1}^{250}(\bar{D}_p - \bar{D})^2}$.
   - Standard error of the cluster mean: $\text{SE}(\bar{D}) = s_{\bar{D}} / \sqrt{250}$.
   - One-sample test statistic: $t = \bar{D} / \text{SE}(\bar{D})$ with degrees of freedom $\nu = K - 1 = 249$.
   - Critical value at $\alpha = 0.05$: $t_{0.975, 249} \approx 1.9695$ (closely approaching standard normal $z = 1.960$).
   - Raw two-sided $p$-value: $p = 2 \cdot (1 - F_{t_{249}}(|t|))$.
2. **Explicit Methodological Caveats & Nature of Approximate Inference:**
   - **Approximate Inference Only:** The paper-level $t$-test is an **approximate inferential procedure**, NOT an exact test. Its finite-sample validity and calibration depend strictly on:
     a. **Cluster Independence:** The assumption that the 250 paper clusters are sampled independently from the target population distribution.
     b. **Asymptotic Normality of the Sample Mean:** While the Central Limit Theorem implies asymptotic convergence to normality as $K \to \infty$ for sums of independent bounded random variables, **a sample size of $K=250$ does NOT guarantee that the distribution of paper-level mean differences is strictly normal**. Because Answer Token F1 scores are bounded in $[0, 1]$ and discrete, finite-sample departures from normality can persist, such as empirical skewness, heavy tails, or point-mass spikes at zero where both models achieve identical scores or where both fail.
     c. **Continuity:** The Student's $t_{249}$ distribution provides a smooth, continuous cumulative distribution function that avoids discrete permutation steps, but continuity alone does not eliminate finite-sample distributional distortion if gross departures from symmetry or normality occur.
3. **Distribution of Paper-Level Differences and Scope of the 16-Question Pilot:**
   - Paper-level mean differences $\bar{D}_p$ are bounded in $[-1, 1]$.
   - In scientific Q&A, differences between two fixed models are often zero or near-zero for factual queries where both succeed or both fail, creating an empirical mass spike at 0.
   - For complex analytical questions, one model may produce substantial gains while the other model fails or hallucinates, introducing potential empirical skewness across paper clusters.
   - **Audit of the 16-Question Pilot Benchmark (`rq5_llm_generation_benchmark.json`):**
     We audited the 16 pilot queries across 4 seminal papers (`ATTN: 1706.03762`, `RES: 1512.03385`, `LORA: 2106.09685`, `RAG: 2005.11401`) from `backend/data/eval_benchmark_seed.json`:
     - Scoring field verified: `f1` (Token F1 in $[0, 1]$).
     - Record alignment verified: Exactly 16 records per model, matched 1-to-1 by question ID (`Q_ATTN_01`..`04`, `Q_RES_01`..`04`, `Q_LORA_01`..`04`, `Q_RAG_01`..`04`).
     - Verified paper mean differences:
       - `llama3.2:3b` vs `qwen2.5:0.5b`: Paper means range from **$-0.1216$** (RAG) to **$+0.1912$** (ATTN) (overall mean: $+0.0460$, std: $0.1588$).
       - `llama3.2:3b` vs `llama3.2:1b`: Paper means range from **$-0.1110$** (RAG) to **$+0.1863$** (ATTN) (overall mean: $+0.0289$, std: $0.1302$).
       - `llama3.2:1b` vs `qwen2.5:0.5b`: Paper means range from **$-0.0209$** (RES) to **$+0.0952$** (LORA) (overall mean: $+0.0171$, std: $0.0531$).
       - Individual query differences span from $-0.3639$ to $+0.4482$.
   - **Strict Methodological Scope of Pilot Evidence:**
     - The pilot benchmark contains **16 questions across four papers only**.
     - Its observed paper-level differences and ranges are **descriptive evidence from those four papers only**.
     - These pilot results serve to motivate robustness checks (such as trimmed means and non-parametric sensitivity checks) but **cannot establish the distribution of differences in the planned 250-paper evaluation**.
     - The pilot does **not, by itself, establish that the primary $t$-test will be well calibrated in the main study**.
     - Pilot findings **must never be presented as results from the planned 250-paper evaluation**.
4. **Pre-Registered Outlier-Sensitivity Protocol (Secondary Checks):**
   To verify that inferential conclusions are robust and not artifacts of isolated extreme paper clusters, post-evaluation reporting must include three companion sensitivity checks alongside the primary $t$-test:
   - **Sensitivity Check 1 (Non-Parametric Location Sensitivity):** The **Wilcoxon Signed-Rank Test** on the 250 paper mean differences $\bar{D}_p$.
     - *Assumptions and Location-Shift Interpretation:* The Wilcoxon signed-rank test is **NOT an assumption-free test**. While continuity of differences was historically assumed in textbook derivations to preclude ties, continuous differences are **not an absolute requirement** for executing the test in modern statistical computing. However, the standard location-shift interpretation (testing whether the median difference is zero, or whether $P(X > Y) = P(Y > X)$) relies strictly on an appropriate **symmetry assumption** (reflection symmetry of the paired difference distribution about the median/zero). If the distribution of paper-level differences is asymmetric or skewed, the test evaluates a complex rank-sum location shift (the Hodges–Lehmann pseudo-median) rather than the pure median or mean. It is therefore pre-registered strictly as a **secondary non-parametric sensitivity analysis**, not as the primary hypothesis test of zero mean difference.
     - *Discrete Values, Ties, and Software Implementation:* Because Answer Token F1 scores are bounded in $[0, 1]$ and discrete (evaluated across $m=2$ questions per paper), paper-level mean differences $\bar{D}_p \in [-1, 1]$ are inherently discrete, so ties in absolute differences and exact zeros ($\bar{D}_p = 0.0$) may and do occur. In the chosen implementation (`scipy.stats.wilcoxon` in SciPy 1.17.1, verified directly from source in `scipy/stats/_wilcoxon.py`):
       1. Non-zero tied absolute differences are assigned **average ranks** (`_rankdata(..., 'average')`).
       2. Ties adjust the standard error of the test statistic via the tie-correction formula $\text{Var}(W) = \frac{1}{24}\left[n(n+1)(2n+1) - \frac{1}{2}\sum (t_i^3 - t_i)\right]$, where $t_i$ is the number of observations tied at rank $i$.
       3. In the presence of ties or zeros, SciPy's `method="auto"` cannot compute an exact permutation distribution for sample sizes $n > 13$ and automatically falls back to the **asymptotic normal approximation** (`method="asymptotic"`). Thus, with $K=250$, $p$-values are computed from the standard normal distribution using the tie-adjusted $z$-statistic, rather than an exact combinatorial distribution.
     - *Zero-Difference Handling (Alternative Sensitivity Analyses):* Exact zero differences ($\bar{D}_p = 0.0$, where both models achieve identical Token F1 on a paper) must be explicitly reported ($K_0$). We pre-register two distinct zero-handling treatments:
       1. **Wilcoxon's zero-dropping method** (`zero_method="wilcox"`): Discards all zero-difference papers, reducing the effective sample size to $K_{\text{eff}} = 250 - K_0$.
       2. **Pratt's zero-ranking method** (`zero_method="pratt"`): Retains zero differences during ranking (assigning them tied lowest ranks) and then drops zero ranks from the rank sum, adjusting the null mean and variance per Cureton (1967) while preserving $K=250$.
       - *Crucial Methodological Distinction:* Pratt's method and Wilcoxon's method are **alternative sensitivity analyses** exploring different rank-handling conventions on the exact same underlying observations. They are **NOT independent confirmations** of each other or of the primary result.
   - **Sensitivity Check 2 (10% Trimmed Mean Difference):** A **10% trimmed mean difference** ($K_{\text{trim}} = 200$) dropping the 25 highest and 25 lowest paper differences ($10\% \times 250 = 25$ per tail) to determine whether the estimated effect direction and significance persist when extreme cluster outliers are excluded.
   - **Sensitivity Check 3 (Cluster Jackknife Influence Diagnostic):** Compute the leave-one-out cluster difference $\Delta_{(-p)} - \Delta_{\text{obs}}$ for each paper $p \in \{1, \dots, 250\}$ to identify whether any single paper cluster disproportionately drives the test statistic or flips significance across $\alpha = 0.05$.
5. **Decoupled Architecture Summary:**
   - **Parameter Estimation:** $\Delta_{\text{obs}}$ with **95% Paper-Cluster Paired Bootstrap Percentile CI** ($B=2,000$, `seed=42`) for non-parametric empirical estimation uncertainty.
   - **Formal Hypothesis Testing:** **Paper-Level Paired $t$-Test on the 250 Paper Means ($df = 249$)** with Holm–Bonferroni step-down across the 3 pre-registered comparisons, supplemented by the pre-registered outlier-sensitivity protocol.

### 5.5. Multiple-Comparison Policy (Holm-Bonferroni)
The 3 pre-registered pairwise tests are adjusted to strongly control the family-wise error rate at $\alpha = 0.05$:
1. Sort raw p-values in ascending order: $p_{(1)} \le p_{(2)} \le p_{(3)}$.
2. Compute step-down adjusted p-values:
   - $p_{\text{adj},(1)} = \min(1.0, 3 \cdot p_{(1)})$
   - $p_{\text{adj},(2)} = \min(1.0, \max(p_{\text{adj},(1)}, 2 \cdot p_{(2)}))$
   - $p_{\text{adj},(3)} = \min(1.0, \max(p_{\text{adj},(2)}, 1 \cdot p_{(3)}))$
3. A comparison is declared statistically significant iff $p_{\text{adj}} < 0.05$.
4. The reported summary table must present: Candidate, Baseline, $\Delta_{\text{obs}}$, 95% Percentile Bootstrap CI $[\Delta_{2.5\%}^*, \Delta_{97.5\%}^*]$ (unadjusted), Raw $p$ ($t$-test), Holm-Bonferroni Adjusted $p_{\text{adj}}$, Formal Decision, and Practical Effect ($\Delta \ge 0.030$).

### 5.6. Missing Data and Error Handling Policy
- If a model throws an HTTP timeout, produces an empty string, or crashes on a query:
  - The prediction is scored as an empty response (`Token F1 = 0.0`).
  - The query is **NEVER dropped or omitted** from the evaluation set to prevent survivorship bias.

### 5.7. Statistical Power, Equivalence, and Inference Boundaries
- **Percentile CI vs. Hypothesis Testing:** The 95% percentile confidence interval describes the range of plausible values for the mean difference, while the Holm-adjusted paper-level $t$-test $p$-value governs the formal hypothesis decision across the family of 3 comparisons.
- **Sample Size Boundaries:** The sample size is strictly fixed at $K=250$ independent paper clusters ($N=500$ questions). Running $B=2,000$ bootstrap replicates improves numerical stability of the CI bounds, but **does NOT increase the number of independent papers ($K=250$) or effective sample size**, and does not generate new data.
- **Calibrated Power & Equivalence Language:**
  - **No Guaranteed Statistical Power:** While expanding to $K=250$ papers reduces estimation standard error by 55.3% relative to $K=50$, a sample size of 250 does **NOT guarantee adequate statistical power** for detecting arbitrary, subtle, or small effect sizes (e.g. $\Delta < 0.020$). Statistical power is inherently a function of the unknown population variance and true effect size, neither of which can be definitively guaranteed a priori from small pilot samples.
  - $\Delta = 0.030$ is **NOT** a statistical significance cutoff. It is an unvalidated heuristic practical-effect threshold (borrowed from earlier retrieval SESOI conventions, representing a 3 percentage-point difference in Answer Token F1).
  - A nonsignificant difference ($p_{\text{adj}} \ge 0.05$) indicates that the observed difference cannot be reliably distinguished from random variation under this sample size, and **must NEVER be claimed to establish equivalence**.

---

## 6. Human Claim-Level Faithfulness Review

Automated lexical overlap rewards verbatim keyword repetition and penalizes valid paraphrasing. A claim-level human evaluation will be conducted on sampled answers:

### 6.1. Approved Review Scope and Deterministic Selection (Option A Approved)
Following provisional user authorization, **Option A** is the approved human review protocol:
- **Review Sample:** Exactly **20 questions** deterministically sampled from the frozen 500-question manifest using a fixed stride of 25 (items 1, 26, 51, 76, ..., 476), evaluated across all 3 candidate models ($20 \times 3 = \mathbf{60\text{ model answers}}$).
- **Review Burden:** Estimated annotation time is ~3.0 hours across the 60 answers.
- **Reviewer Blinding:** The evaluation interface presents the Question, the Retrieved Context Chunks (with section titles), and the Model Answer. Model names are replaced with anonymized labels (`Model_Alpha`, `Model_Beta`, `Model_Gamma` with a permuted mapping per question) to prevent reviewer bias.

### 6.2. Unit of Analysis: Atomic Factual Claims
- **Definition:** An *atomic factual claim* is defined as the smallest self-contained declarative clause or subject-predicate proposition asserting a verifiable empirical fact, relation, measurement, or methodology.
- **Splitting Rules for Compound Claims:**
  - Conjunctions (e.g. "and", "but", "as well as") joining independent assertions must be split into separate atomic claims (e.g., "The model uses AdamW with lr=1e-4 and trains for 10 epochs" $\to$ Claim 1: "The model uses AdamW with learning rate 1e-4"; Claim 2: "The model trains for 10 epochs").
  - Relative and adverbial clauses asserting distinct verifiable facts are split into separate claims.
  - Conversational preamble, formatting boilerplate, and framing phrases (e.g., "Based on the text...", "In conclusion...") do not assert verifiable facts and are excluded from claim scoring.

### 6.3. Evidence Standard (Retrieved Context Bound)
- Every claim is judged strictly and exclusively against the **actual retrieved parent context chunks supplied in the model's prompt**.
- External scientific plausibility, general world knowledge, or facts present in the full original PDF but omitted from the prompt context cannot be used to substantiate a claim. If the claim is not entailed by the prompt context, it is unverified from the model's perspective.

### 6.4. Claim-Level Rubric vs. Answer-Level Omission/Refusal Classification
To ensure rigorous and reproducible auditing, the protocol strictly separates **claim-level evaluation** (assessing factual propositions) from **answer-level defect categorization** (assessing completeness and abstention validity):

#### 1. Claim-Level Labels (Applied to Each Extracted Atomic Claim)
Each extracted atomic claim is assigned exactly one mutually exclusive label:

| Judgment Category | Operational Definition |
| :--- | :--- |
| **SUPPORTED** | The factual assertion is directly entailed by the retrieved prompt context. Semantic paraphrasing is supported if meaning is fully preserved. |
| **UNSUPPORTED** | The claim asserts factual details that are neither stated in nor directly entailed by the retrieved context, but do NOT directly conflict with what is written (extrapolation, unverified external knowledge). **MANDATORY AUDIT RULE:** Any ungrounded, fabricated, or unverifiable factual assertion MUST be classified as `UNSUPPORTED`. It must **never** be labeled `MISSING_INFO`. |
| **CONTRADICTED** | The claim asserts a fact that directly conflicts with or negates explicit statements in the retrieved context (e.g. inverted numerical values, misattributed methods). |

#### 2. Answer-Level Holistic Classifications (Applied to the Complete Response)
Because omissions and refusals do not produce verifiable factual claims, completeness defects and refusal behaviors are categorized at the answer level:

| Answer Classification | Operational Definition & Scope |
| :--- | :--- |
| **Fully Faithful (`SUPPORTED`)** | All extracted atomic claims are `SUPPORTED`, with zero unsupported qualifiers, contradictions, or core omissions. |
| **Appropriate Abstention (`REFUSAL_VALID`)** | The model emitted the standard refusal message, and human audit confirms the prompt context genuinely lacked sufficient factual evidence to answer. (Valid safe abstention; receives credit for caution). |
| **Incomplete Answer (`MISSING_INFO - PARTIAL`)** | The model attempted an answer with generated claims, but omitted crucial qualifiers, parameters, or findings present in the context that were necessary to answer the question. (Receives zero credit for omitted elements). |
| **Unjustified Refusal (`MISSING_INFO - UNJUSTIFIED_REFUSAL`)** | The model emitted the refusal message despite the prompt context actually containing sufficient evidence to answer. (Abstention defect / false negative; receives zero credit as supported). |
| **Extrapolated / Hallucinated (`UNSUPPORTED`)** | The response contains $\ge 1$ `UNSUPPORTED` claim. |
| **Contradicted (`CONTRADICTED`)** | The response contains $\ge 1$ `CONTRADICTED` claim. |

### 6.5. Partial Support and Scoring Denominator
- Compound sentences with mixed evidence are split into atomic claims before scoring so that each claim receives its own label.
- If an atomic claim contains an inseparable unsupported qualifier: scored as `UNSUPPORTED`.
- **Per-Answer Claim Support Ratio:**
  $$\text{Support Ratio} = \frac{N_{\text{SUPPORTED}}}{N_{\text{total atomic claims}}}$$
  where the denominator is the count of verifiable factual claims: $N_{\text{total atomic claims}} = N_{\text{SUPPORTED}} + N_{\text{UNSUPPORTED}} + N_{\text{CONTRADICTED}}$. (If an answer contains zero factual claims, e.g. a refusal, support ratio is recorded as `N/A` and scored under abstention rules).
- **Answer-Level Holistic Classification Priority:** Assigned based on worst-case failure priority: `CONTRADICTED` > `UNSUPPORTED` > `MISSING_INFO - UNJUSTIFIED_REFUSAL` > `MISSING_INFO - PARTIAL` > `REFUSAL_VALID` > `SUPPORTED` (Fully Faithful).

### 6.6. Abstentions, Refusals, and Metric Delineation
- **Strict Distinction Between Answer Correctness and Faithfulness:**
  - **Automated Answer Token F1 (Tier 1):** QASPER-style Answer Token F1 measures lexical precision and recall against the ground-truth human reference answers. A refusal response (`The document does not contain sufficient relevant information to answer this question.`) evaluated against an answerable reference answer yields **Answer Token F1 = 0.0**. Automated token F1 is strictly an answer correctness / reconstruction metric, not a measure of safe abstention or factual faithfulness.
  - **Automated Context Containment Proxy (Automated Tier):** Token overlap against prompt context measures lexical containment (evaluates strictly to 0.0% on refusal). This heuristic does **not** establish semantic faithfulness, logical consistency, or factual truth.
  - **Human Claim-Level Faithfulness Review (Tier 2):** In the claim-level audit (Option A: 60 answers), refusals do **NOT** receive automatic credit as `SUPPORTED`. Refusals are evaluated conditionally:
    1. **Appropriate Abstention (`REFUSAL_VALID`):** If and only if the supplied prompt context genuinely lacks the necessary factual evidence required to answer the question, an explicit refusal is judged as faithful behavior and scored as `SUPPORTED` (or recorded as valid zero-claim abstention).
    2. **Unjustified Refusal (`MISSING_INFO - UNJUSTIFIED_REFUSAL`):** If the supplied prompt context actually contains sufficient evidence to answer the question, but the model refuses, the response must **NOT** receive credit as supported. It is classified as `MISSING_INFO - UNJUSTIFIED_REFUSAL` (zero credit).
    3. **Hallucination on Deficient Context (`UNSUPPORTED` / `CONTRADICTED`):** If the supplied context lacks evidence but the model invents an answer, the generated claims are evaluated and classified as `UNSUPPORTED` (extrapolated) or `CONTRADICTED` (factually inverted).

### 6.7. Aggregation and Reproducibility Recording Schema
- Both claim-level granularity and answer-level summaries are preserved in the review artifact (`human_faithfulness_review.json` / markdown log).
- **Recorded Fields for Every Claim:**
  - `question_id`, `item_index`
  - `model_anonymized_id` (`Model_Alpha`, `Model_Beta`, `Model_Gamma`)
  - `claim_index`, `claim_text`
  - `assigned_label` (`SUPPORTED` | `UNSUPPORTED` | `CONTRADICTED`)
  - `evidence_excerpt` (verbatim excerpt from retrieved context, or empty if unsupported)
  - `reviewer_rationale` (short explanation justifying the label, especially for boundary cases)
- **Reported Aggregations:**
  1. Per-claim breakdown by model: Total claims, % Supported, % Unsupported, % Contradicted.
  2. Answer-level holistic classification counts across the evaluated questions per model.

### 6.8. Approved Reviewer Staffing Model and Validity Scope
- **Approved Reviewer Staffing:** Approved as a **single-reviewer descriptive audit** (Option A: 60 answers; Option B: 75 answers) preserving the four-category rubric (`SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `MISSING_INFO`).
- **Explicit Validity & Generalizability Boundaries:**
  - This single-reviewer audit serves exclusively as a qualitative descriptive diagnostic audit.
  - **The audit does NOT establish inter-rater reliability or definitive general faithfulness performance**, and must never be described, cited, or published as an inter-rater validated benchmark.
  - No second reviewer is assumed, and no reliability coefficients ($\kappa$) or completed annotations are invented.
  - All evaluated answers, segmented claims, verbatim prompt context excerpts, and reviewer rationales will be published in full transparency within the review log.

---

## 7. Latency and Memory Measurement Procedures

### 7.1. End-to-End Latency Measurement
- **Measurement Tool:** High-precision `time.perf_counter()` on the host AMD Ryzen 5 5600 CPU with fixed thread allocation `torch.set_num_threads(4)`.
- **Untimed Warm-Up:** Exactly **2 untimed warm-up queries** are executed on a discarded unexposed paper prior to timing the 500 benchmark queries (warming OS disk cache, Ollama runner RAM, and PyTorch/NumPy BLAS thread pools). Warm-up queries are strictly excluded from reported latency figures.
- **Per-Stage Latency Breakdown Per Query:**
  - $t_0 \to t_1$: Hybrid retrieval latency (BM25 + Dense E5 embedding + RRF fusion + Small-to-Big parent context expansion).
  - $t_1 \to t_2$: Prompt assembly and token budget formatting.
  - $t_2 \to t_3$: Ollama REST generation latency (time to complete generation).
  - $t_3 \to t_4$: Post-processing and citation coordinate mapping.
  - Total End-to-End Latency: $t_4 - t_0$ (ms).
- **Reporting:** Reported as P50 (median) and P95 percentiles across the 500 measured queries.

### 7.2. Peak Memory Measurement (Process-Tree RSS)
- **Planned Instrumentation:** A background monitoring thread samples memory usage every 100 ms using Python `psutil`.
- **Processes Monitored:**
  1. The Python/Django benchmark worker process (`psutil.Process(os.getpid())`).
  2. The external Ollama daemon and inference backend process (`ollama.exe` and `ollama_llama_server.exe`).
- **Reporting Rule & Technical Memory Caveat:**
  - Report **Python Process Peak RSS (MB)**.
  - Report **Ollama Runner Peak RSS (MB)**.
  - If their values are summed, label the result accurately as the **Sum of Measured Process RSS Values (Python RSS + Ollama Runner RSS)**.
  - **MANDATORY TERMINOLOGY RESTRICTION:** This sum must **NOT** be described as:
    1. true total physical memory;
    2. a guaranteed upper bound on actual memory usage; or
    3. a deduplicated process-tree memory measurement.
  - *Technical Reason:* On Windows, distinct processes frequently share dynamic-link libraries (e.g. C/C++ runtimes `ucrtbase.dll`, `vcruntime140.dll`), shared memory sections, and system pages. Summing individual process RSS values counts shared pages more than once, overstating physical RAM footprint.
- **Resumed Execution Boundary:**
  - In a resumed evaluation run, completed items bypass Ollama inference calls and are loaded from checkpoint. The Ollama runner process will be idle for cached queries.
  - Peak memory recorded during a resumed run captures idle/partial execution only and does **NOT** represent the peak memory of live inference across the full cohort.
- **Instrumentation Status:**
  - Implemented in `DualProcessMemoryMonitor` in `evaluate_rq5_llm_generation.py`.
- **Environment Documentation:** Record Windows OS version, Ollama version (`ollama --version`), CPU model, and host physical RAM.

---

## 8. Pipeline Freeze and Bug-Fix Protocol

- **Permanent Freeze:** Upon sample manifest generation, all pipeline components (retrieval parameters $k=60$, chunk size 1,600 tokens, prompt templates, decoding parameters `temperature=0.0`, `num_predict=256`) are permanently frozen.
- **Harness Crash / Bug Protocol:**
  - If a software crash occurs (e.g. Ollama HTTP timeout):
    1. The incident is recorded in an incident log with timestamp, question ID, error traceback, and model name.
    2. If a harness fix is unavoidable (e.g. increasing HTTP connection timeout), the exact diff and Git commit SHA must be recorded in [`PROTOCOL_AUDIT_CHANGELOG.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/PROTOCOL_AUDIT_CHANGELOG.md).
    3. The evaluation must be re-run from scratch using the exact same sample manifest and random seed.
    4. Tweaking prompts, retriever weights, or models under the pretext of a "bug fix" is strictly prohibited.

---

## 9. Pre-Evaluation Smoke-Test Procedure

Before executing the full 500-question evaluation, a **2-question smoke test** will be conducted:
- **Test Corpus:** 1 discarded paper from the unexposed Train set (a paper not included in the sampled 250 primary papers or 50 reserve papers).
- **Verification Target:** Verify end-to-end execution across: PDF section extraction, hierarchical chunking, Qdrant companion indexing, Ollama REST inference for each model, and `psutil` process-tree memory tracking.
- **Scoring Boundary:** Smoke-test results **will not contribute to final evaluation scores**.

---

## 10. Mandatory Experiment Provenance and Contamination Registry Protocol

To prevent accidental data leakage, unrecorded re-evaluation, or circular benchmarking:

1. **Pre-Sampling Overlap Verification:**
   Before any sample manifest is finalized for an evaluation, the proposed paper IDs must be audited against the canonical registry using the automated utility:
   ```powershell
   python eval/scripts/check_experiment_overlap.py --manifest <path_to_manifest>
   ```
   The script verifies that none of the sampled papers have prior conflicting exposure in the repository.
2. **Mandatory Event Registration:**
   Upon formal authorization and generation of the final 250-paper manifest, the evaluation cohort must be registered in [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json) with status `sampled` *prior* to executing inference or downloading PDFs.
3. **Immutability of Registry History:**
   Past exposure events are permanent and must never be deleted or overwritten. If an evaluation is amended or invalidated, a new event entry is appended with the appropriate status update (`invalidated`, `completed`).
4. **Pretraining Contamination Caveat:**
   The absence of repository-level experimental exposure guarantees that a paper was not used to tune retrieval or select models within this codebase. It does **not** prove that pre-trained large language models never observed the paper during public internet pretraining. All reporting must explicitly state this boundary.

---

## 11. Authoritative Methodological & Operational Caveats Inventory

To eliminate ambiguity and guarantee rigorous scientific reporting in downstream chapters, the evaluation harness and reporting pipelines are governed by the following six verified caveats:

### 11.1. Caveat 1: Generator Isolation vs. End-to-End RAG
- **Experimental Protocol:** The RQ5 evaluation harness supplies verbatim `ground_truth_evidence` paragraphs from the QASPER dataset directly into the prompt context.
- **Pipeline Bypass:** The evaluation strictly bypasses the upstream retrieval pipeline: dense `intfloat/e5-small-v2` vector search, BM25 keyword scoring, Reciprocal Rank Fusion (RRF $k=60$), and hierarchical Small-to-Big parent context expansion.
- **Scientific Role:** This design measures Small Language Model (SLM) generation capacity and evidence synthesis under controlled gold-evidence conditions, isolating generator comparisons from upstream retrieval errors (precision/recall failures).
- **Reporting Boundary:** RQ5 must **NEVER be characterized as an end-to-end RAG benchmark**, nor cited as measuring production retrieval performance.

### 11.2. Caveat 2: Automated Containment Proxy (Lexical Overlap) vs. Semantic Faithfulness
- **Implementation & Computation:** Computed via `compute_context_containment_proxy()` in `evaluate_rq5_llm_generation.py`. It measures the proportion of informative non-stopword tokens (length > 2, excluding 39 canonical stopwords) in the normalized prediction that appear verbatim in the normalized prompt context.
- **Refusal Convention:** Emitting `REFUSAL_MESSAGE` evaluates strictly to **0.0% containment** by code convention, preventing boilerplate refusal tokens from receiving accidental credit.
- **Methodological Limitation:** This metric is strictly an automated lexical containment heuristic. It **does NOT establish semantic entailment, factual correctness, valid mathematical reasoning, or correct handling of negation**. A model can achieve high containment by juxtaposing real keywords into false propositions; conversely, valid abstractive synthesis using synonyms receives a penalized score.
- **Mandatory Terminology:** All tables, scripts, and reports must use the canonical term **Automated Containment Proxy (Lexical Overlap)**. It must never be labeled as faithfulness, semantic grounding, or factual accuracy.
- **Role of Human Audit:** The planned 60-answer blinded claim-level human audit provides qualitative factual-support assessment. When conducted by a single reviewer, it must be reported strictly as a *single-reviewer expert qualitative audit*; Cohen's $\kappa$ inter-rater reliability must not be reported without an independent second reviewer.

### 11.3. Caveat 3: Answerable-Only Evaluation Cohort
- **Cohort Selection:** All 500 questions in `eval_sample_manifest_500q.json` are answerable under the project's eligibility criteria and possess usable non-float text evidence. Questions marked strictly unanswerable in QASPER were excluded during manifest generation because they lack reference answers required for Answer Token F1 scoring.
- **Scoring Behavior:**
  - A refusal emitted on an answerable question receives **Answer Token F1 = 0.0** and **Containment Proxy = 0.0%**.
  - In human review: Refusing despite sufficient evidence is categorized as an abstention defect (**`MISSING_INFO - UNJUSTIFIED_REFUSAL`**).
  - If the supplied evidence is genuinely insufficient, **`REFUSAL_VALID`** applies per rubric.
- **Scope Limitation:** This cohort cannot estimate appropriate refusal behavior on genuinely unanswerable questions or establish performance on the full QASPER question distribution. Findings must not be generalized to all QASPER questions.

### 11.4. Caveat 4: Repository Independence vs. Pretraining Contamination
- **Audit Verification & Exact Scope:** The automated overlap audit utility (`python eval/scripts/check_experiment_overlap.py --manifest eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json`) confirms `PASS_UNEXPOSED`. It audited all 250 primary papers and 500 questions against all recorded historical experiments in the registry:
  - `EXP-RQ1-EXTRACTION` (47 QASPER Dev papers)
  - `EXP-RQ2-CHUNKING` (47 QASPER Dev papers)
  - `EXP-RQ3-EMBEDDING-UNIFIED` (211 papers: 111 QASPER Train + 100 QASPER Dev)
  - `EXP-RQ4-HYBRID-DEV` (276 QASPER Dev papers)
  - `EXP-RQ4-HYBRID-TEST` (408 QASPER Test papers)
  - `EXP-RQ5-PILOT-SEED` (4 non-QASPER seed papers: ResNet, Attention, LoRA, RAG)
  - Official QASPER Partitions: Entire Dev partition (281 papers) and Test partition (416 total papers; 408 active text-retrieval papers in `EXP-RQ4-HYBRID-TEST` after excluding 8 papers with zero text evidence).
- **Scope Boundary (Absence of Prior Repository Exposure vs. Selection Bias):**
  - The verdict `PASS_UNEXPOSED` supports independence from recorded prior experimental exposure within the audited repository records.
  - It does **NOT** prove freedom from all methodological or selection bias (e.g. eligibility filtering requiring $\ge 2$ text-evidenced answerable questions inherently selects for information-dense papers).
  - Furthermore, repository-level unexposed status proves only the absence of in-house pipeline exposure; it **cannot prove that public arXiv preprints were absent from the public internet pretraining corpora** of Meta (Llama-3.2) or Alibaba (Qwen-2.5). The cohort must never be described as proven free of all bias or public-pretraining contamination.
- **Reporting Boundary:** The cohort must **NEVER be described as proven free of all bias or data contamination**.

### 11.5. Caveat 5: Human Review Design and Annotator Agreement
- **Frozen Review Sample:** Exactly 20 questions sampled by the frozen stride-25 rule (items 1, 26, 51, ..., 476) evaluated across 3 models = **60 answer outputs**.
- **Blinding & Rubric:** Model identities are blinded as `Model_Alpha`, `Model_Beta`, and `Model_Gamma`. Claims are decomposed and evaluated under the 4-category rubric (`SUPPORTED`, `UNSUPPORTED`, `CONTRADICTED`, `MISSING_INFO`).
- **Staffing & Validity:** Approved as a single-reviewer qualitative descriptive audit. It does **NOT establish inter-rater reliability**; Cohen's $\kappa$ must not be reported unless a second independent reviewer evaluates the items.
- **Audit Status:** The planned audit must be clearly distinguished from a completed audit.

### 11.6. Caveat 6: Runtime Arithmetic, Checkpointing, and Process Memory
- **Runtime Arithmetic & Overhead Decomposition:**
  - **Baseline Pure Generation Sum:**
    - `qwen2.5:0.5b`: ~3.50s $\times$ 500 questions = $1,750\text{ s}$ ($29.17\text{ min}$)
    - `llama3.2:1b`: ~5.50s $\times$ 500 questions = $2,750\text{ s}$ ($45.83\text{ min}$)
    - `llama3.2:3b`: ~8.50s $\times$ 500 questions = $4,250\text{ s}$ ($70.83\text{ min}$)
    - Pure generation total: $8,750\text{ s} = 145.83\text{ min} \approx \mathbf{146\text{ min}}$ ($2\text{h } 25\text{m } 50\text{s}$).
  - **Quantified Deterministic Overhead (~1.5 minutes / ~91 seconds):**
    - Initial model weight loading from NVMe disk into Ollama: 3 models $\times$ ~8.7s = ~26s.
    - HTTP REST localhost round-trips & JSON parsing: 1,500 calls $\times$ ~10 ms = ~15s.
    - Checkpoint serialization and incremental disk flush (`f.flush()`): 1,500 items $\times$ ~10 ms = ~15s.
    - In-memory scoring computation (Token F1 normalization & containment set operations): 1,500 items $\times$ ~10 ms = ~15s.
    - Paper-level paired statistical analysis & bootstrap resampling ($B=2,000$): ~20s.
    - Subtotal quantified deterministic overhead: **~91 s (~1.5 min)**, yielding a deterministic baseline of **~147.3 min** (~2h 27m 20s).
  - **Unquantified Operational & Contingency Allowance (~2.7 to 32.7 minutes):**
    - The remaining gap required to reach the 2.5 to 3.0-hour window (150 to 180 min) represents **unquantified operational contingency**, covering:
      1. Background memory monitoring thread (`DualProcessMemoryMonitor` 100 ms polling overhead and context switching);
      2. Host CPU thermal throttling and OS scheduler contention on the AMD Ryzen 5 5600 under continuous 100% thread load across 1,500 sequential prompts;
      3. Potential transient HTTP retry backoffs (`call_ollama_with_retry` exponential delay $2^a \times 1.0\text{s}$ on dropped sockets);
      4. Python garbage collection and memory reallocation.
  - **Provisional Estimate Status:**
    - The 2.5–3.0 hour wall-clock duration is a **provisional planning estimate** and is **not** claimed to be explicitly justified by the ~1.5 minutes of itemized deterministic overhead alone. Timing cannot be empirically finalized until live inference is authorized.
- **Checkpoint Manager Implementation & Recovery Behavior:**
  - Implemented in `CheckpointManager` in `evaluate_rq5_llm_generation.py`, writing incrementally to `rq5_inference_checkpoint.jsonl` in append mode (`"a"`) with immediate `f.flush()`.
  - **Duplicate Records:** Keyed on `(model, item_index)`. Duplicate entries overwrite earlier entries in memory (`loaded_records[key] = rec`), maintaining set membership in `completed_keys`. Resumed execution safely skips duplicate items without re-running inference.
  - **Malformed or Partial Lines / Interrupted Writes:** Evaluated under `try ... json.loads(line) ... except Exception as e`. Any partial or truncated line resulting from a process crash or interrupted write is logged and skipped. The key is **not** added to `completed_keys`, ensuring the incomplete item is cleanly re-evaluated upon restart.
  - **Persistence & Durability Limitation (Buffer Flush vs. Power Loss):** `f.flush()` flushes Python's user-space buffers into the host OS kernel file cache (`fflush()`); it does **not** invoke `os.fsync()` or Windows `FlushFileBuffers()` to force data onto physical non-volatile storage media. Consequently, while this protects against Python process-level crashes or unhandled exceptions, it does **not** guarantee physical persistence against sudden host power loss, hardware reset, or OS kernel crashes. Recovery guarantees are strictly limited to user-space process-level interruptions.
  - **Changed Manifest Mappings (Non-Universal Recovery Limitation):** Resumption keys strictly on `(model, item_index)`. The implementation does **not** validate `question_id` or `paper_arxiv_id` against the checkpoint record upon resumption. If the manifest order or composition changes, `item_index` will map to an entirely different paper/question, causing silent semantic misattribution. Therefore, safe recovery is **strictly conditional** upon using the permanently frozen manifest (`eval_sample_manifest_500q.json`). Universal safe recovery across arbitrary manifest changes is not supported.
- **Process Memory Measurement Nuances:**
  - `DualProcessMemoryMonitor` samples Python process RSS and Ollama runner RSS every 100 ms and records `sum_of_measured_process_rss_mb = py_rss + ol_rss`.
  - **Summed RSS vs. Actual Physical RAM Consumption:** On Windows, process RSS includes both private and shared working set memory pages (such as common C/C++ runtimes `ucrtbase.dll`, `vcruntime140.dll`, and shared OS libraries). Summing individual process RSS values counts these shared pages multiple times. Therefore, summed RSS is **higher than actual physical RAM consumption** and must **never** be labeled as true physical RAM usage, a guaranteed upper bound, or deduplicated process-tree memory.
  - **Resumed Run Peak Memory Clarification:** When resuming from a checkpoint, completed items are loaded directly from disk cache and skip the Ollama REST inference call. During a resumed run, Ollama processes remain idle for cached items. The background sampling thread in a resumed run will therefore **only capture idle/background memory**, which does **not** represent live inference-time peak memory. Peak inference memory measurements are only valid from full, contiguous inference executions.
  - **Ollama Process Keep-Alive:** The Ollama daemon's default 5-minute keep-alive applies (no custom `keep_alive` parameter is sent in the generation payload). Rapid transitions between candidate models may cause temporary overlap of resident model weights in host RAM until the previous model is evicted by the Ollama runner.
