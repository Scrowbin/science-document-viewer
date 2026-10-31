# RQ1-v2: PDF Extractors on Fresh Papers (original frozen Phase C run)

**Protocol:** `reports/revalidation/protocol/rq1_rq4.json` "RQ1-v2", frozen before Gate B.
**Role:** selection (C-RET).
**Script:** `eval/phases/phase_1_extraction/scripts/rq1v2_extractors.py`. Outputs: `summary.json`, `per_query.jsonl`.
**Bootstrap:** paper-cluster paired, B = 10,000, seed 42. Holm correction over the 4 challengers.

## Counts
- **Primary set:** C-RET, 335 papers, one evidence-recall value per paper.
- **Sensitivity set:** 363 opened reservoir papers (C-INT excluded), i.e. the papers before the version-check exclusion.
- **Downstream set:** C-RET-150, 150 papers, 249 questions.
- **Descriptive:** PeerQA-PDF, 107 papers.
- **Failures:** none, for any extractor (0 failed extractions).
- **GROBID:** not part of this family. It ran as a separate add-on (see `../rq1v2_grobid_addon/REPORT.md`).

## Primary: evidence recall (C-RET)

| Extractor | Mean evidence recall | Δ vs pymupdf_layout [95% CI] | Holm p | CI half-width |
|---|---|---|---|---|
| pymupdf_layout (production) | 0.9848 | — | — | — |
| pymupdf_plain | 0.9851 | +0.0003 [−0.0009, +0.0017] | 1.00 | 0.001 |
| pypdf | 0.9823 | −0.0025 [−0.0064, +0.0006] | 0.41 | 0.004 |
| pdfminer.six | 0.9851 | +0.0003 [−0.0009, +0.0017] | 1.00 | 0.001 |
| pdfplumber (as configured; see note) | 0.5583 | −0.4265 [−0.4735, −0.3788] | 0.0008 | 0.047 |

- **Decision (rule: a challenger must win by ≥ 0.03 with CI lower bound > 0):** **keep `pymupdf_layout`.** No challenger comes close.
- **The decision is the same on all 363 opened papers.** Largest positive Δ = 0.0000; pdfplumber Δ = −0.407.
- **Precision:**
  - Every half-width except pdfplumber's is ≤ 0.004, far inside the planned < 0.03.
  - pdfplumber's is 0.047, above the plan. Its CI lies entirely below −0.37, so the conclusion is unaffected and no expansion is warranted.

**Note on pdfplumber.** The frozen adapter calls `page.extract_text(layout=True)`. On two-column papers this reproduces the page as a character grid: it interleaves lines from both columns and often runs words together. Example from 1602.01208: "(SpCoA)thatintegratesthegenerativemodel…". The low recall measures **this configuration**, not pdfplumber's best capability. The thesis must not state that "pdfplumber loses 43% of the text". No corrected pdfplumber arm was run: four extractors already tie at about 0.985, so a fixed pdfplumber could not change the decision.

## Secondary: structure, speed, memory, downstream retrieval

| Extractor | Heading F1 | ms per page (P50) | Working-set increase (peak) | Downstream CEC@0.5 | Downstream nDCG@10 |
|---|---|---|---|---|---|
| pymupdf_layout | 0.466 | 12.3 | +2.7 MB (446 MB) | **0.739** | **0.454** |
| pymupdf_plain | 0 (no headings) | 7.2 | +3.6 MB (448 MB) | 0.699 | 0.421 |
| pypdf | 0 | 48.2 | +155 MB (598 MB) | 0.659 | 0.396 |
| pdfminer.six | 0 | 94.4 | +535 MB (978 MB) | 0.687 | 0.414 |
| pdfplumber | 0 | 185.1 | +1,184 MB (1,627 MB) | 0.651 | 0.379 |

- **Measurements:**
  - **Timings:** from the version-check extraction run, one subprocess per extractor, on this laptop.
  - **Memory:** peak Windows working set of that subprocess. pypdf's peak covers only the resumed portion of its run (the last ~328 papers).
- **Downstream retrieval** (C-RET-150, 249 questions; each extractor's sections → hierarchical chunking → e5 dense → production context), CEC@0.5 against `pymupdf_layout`, with Holm p:
  - pypdf −0.080 [−0.139, −0.024], p 0.022
  - pdfplumber −0.088 [−0.148, −0.029], p 0.016
  - pymupdf_plain −0.040 [−0.095, +0.012], p 0.16
  - pdfminer −0.052 [−0.108, +0.004], p 0.14
- **Takeaway:** text recovery is equal, but `pymupdf_layout`'s heading-based sections give the best downstream context of the five. Extractors without headings fall back to one section per page.
- **GROBID (separate add-on, not in this family):** downstream CEC 0.823, higher than `pymupdf_layout`. See its report.

## Descriptive: PeerQA-PDF (107 papers, reported separately; not pooled)
| Extractor | Evidence recall |
|---|---|
| pymupdf_layout | 0.933 |
| pymupdf_plain | 0.978 |
| pypdf | 0.980 |
| pdfminer.six | 0.977 |
| pdfplumber | 0.399 |

On PeerQA's PDFs, which are mostly OpenReview single-column, `pymupdf_layout` recovers about 4.5 points less evidence than the plain extractors. That is a hint that its layout and heading logic loses some text on non-arXiv layouts. It is descriptive only.

## Does this support the intended claim?
- **Supported:**
  - On fresh QASPER papers, the production extractor recovers evidence text as well as any tested alternative (all within ±0.003, except the mis-configured pdfplumber).
  - It is the fastest extractor that detects headings, with the smallest memory footprint.
  - Its sections give the best downstream retrieval among the five frozen extractors.
- **Not supported:**
  - "`pymupdf_layout` extracts text better." It is equal on recovery, not better.
  - "`pymupdf_layout` is the best extractor overall." GROBID's downstream result and the PeerQA gap qualify that claim.

## Deviations
None from the frozen protocol. The pdfplumber configuration problem is a property of the frozen adapter; it is documented here, not fixed.
