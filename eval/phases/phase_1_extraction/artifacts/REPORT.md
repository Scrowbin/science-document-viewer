# Phase 1 PDF Extraction Benchmark — OHR-Bench Results

- **Benchmark:** [OHR-Bench](https://github.com/opendatalab/OHR-Bench) (OpenDataLab, ICCV 2025)
- **Domain:** `all`
- **Documents scored:** 706 PDFs (up to 7500 pages extracted per extractor)
- **Scanned / no-text-layer PDFs:** 555 docs / 1540 questions excluded (no text layer, or GROBID found no text): DUDE_30608a90fc85ee4a76f322ea5e11de22, DUDE_3c4810cd3231673176c4c0d7531db7a2, DUDE_423bec13b660c77bff66faeda0c58e19, DUDE_83de527c915f2a4fc3e399bb5f58e293, DUDE_022e426491cae00aa10f1ff2fe5fec1f, DUDE_06a099741b8a087d4731575b6360fb0d, DUDE_0e255f0953fe55f0c1fe2f4152def74f, DUDE_10530f771a11f007ebd341f75215db61, DUDE_182228e839cfb822d19f389d502187be, DUDE_1991a329dc9557ff6aebf3a77354cc06 …
- **Questions in scope:** 6916 (each extractor averaged over the questions it processed)

## 1. Overall Performance Comparison

| Extractor | Qs | Docs OK | Evidence Recall (≥0.80) | Text LCS (%) | Hit@1 | Hit@2 | Hit@5 | Retrieval LCS (%) | Latency (ms/page) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **pymupdf_layout** | 6916 | 750/750 | 0.747 | 76.2% | 0.733 | 0.838 | 0.920 | 64.0% | 2.55 |
| **pymupdf_plain** | 6916 | 750/750 | 0.747 | 77.0% | 0.733 | 0.838 | 0.920 | 64.7% | 2.25 |
| **pypdf** | 6916 | 750/750 | 0.726 | 75.1% | 0.718 | 0.824 | 0.913 | 62.7% | 31.96 |
| **pdfminer.six** | 6916 | 750/750 | 0.717 | 72.5% | 0.715 | 0.819 | 0.909 | 60.7% | 53.56 |
| **pdfplumber** | 6916 | 750/750 | 0.705 | 73.9% | 0.711 | 0.817 | 0.907 | 61.2% | 88.86 |
| **grobid** | 6916 | 750/750 | 0.494 | 54.3% | 0.577 | 0.672 | 0.775 | 46.2% | 143.27 |

## 2. Performance Breakdown by Evidence Source (LCS Score %)

| Extractor | Plain Text | Table | Formula | Chart | Reading Order |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **pymupdf_layout** | 92.9% | 84.9% | 74.6% | 44.8% | 8.0% |
| **pymupdf_plain** | 93.1% | 86.3% | 75.3% | 45.9% | 9.6% |
| **pypdf** | 90.4% | 84.3% | 73.8% | 45.4% | 10.0% |
| **pdfminer.six** | 88.1% | 79.3% | 71.9% | 45.1% | 10.4% |
| **pdfplumber** | 90.9% | 82.0% | 70.1% | 44.6% | 6.6% |
| **grobid** | 74.9% | 48.2% | 52.8% | 28.7% | 7.5% |

## 3. Key Observations & Findings

1. **Best text fidelity:** `pymupdf_plain` (77.0% LCS, recall 0.747).
2. **Best BM25 retrieval:** `pymupdf_layout` (Hit@1 0.733, Hit@2 0.838).
3. **Speed:** fastest `pymupdf_plain` (2.25 ms/page), slowest `grobid` (143.27 ms/page).
