# BIÊN BẢN KIỂM TOÁN VÀ ĐỐI SOÁT CHỨNG CỨ THỰC NGHIỆM — CHƯƠNG 5
**Dự án: Xây dựng hệ thống quản lý tài liệu nghiên cứu khoa học tích hợp trợ lý AI sử dụng RAG**

---

## 1. Mục Đích và Nguyên Tắc Kiểm Toán

Biên bản này ghi nhận toàn bộ kết quả kiểm toán độc lập về tính xác thực, độ tin cậy và nguồn gốc phát sinh của các số liệu thực nghiệm được trình bày trong Chương 5. 

**Nguyên tắc vận hành cốt lõi:**
1. **Zero Fabrication:** Mọi giá trị trung bình, khoảng tin cậy 95%, mức sai khác $\Delta$, trị số $p$, độ trễ và thông lượng đều bắt buộc phải truy vết được tới tệp kết quả gốc trên đĩa lưu trữ (`eval/results/*.json`).
2. **Reproducible Provenance:** Toàn bộ bảng dữ liệu và hình ảnh đồ thị phải được sinh tự động bằng mã nguồn từ tệp dữ liệu gốc, không sao chép thủ công.
3. **Transparent Limitations:** Không làm tròn số liệu để tạo kết luận phóng đại; các chỉ số chưa hoàn tất đo đạc hoặc các hạn chế của bộ thử nghiệm phải được ghi nhận minh bạch.

---

## 2. Bảng Danh Mục Chứng Cứ Thực Nghiệm (Internal Evidence Inventory)

### 2.0. Tiền Xử Lý & Khám Phá Dữ Liệu Toàn Phần (Full-Scale Benchmark EDA)
* **Tên thực nghiệm:** QASPER Full Benchmark EDA & Physical PDF Usability Audit.
* **Tệp dữ liệu gốc:** 
  - Toàn bộ Benchmark QASPER: [val/phases/phase_0_baseline/artifacts/qasper_full_corpus_eda.json](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/qasper_full_corpus_eda.json), [da_pilot_vs_full_comparison.csv](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_pilot_vs_full_comparison.csv), [da_question_distribution.csv](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_question_distribution.csv), [da_section_heading_distribution.csv](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_section_heading_distribution.csv).
  - Tệp chỉ mục truy vết từng câu hỏi: [val/phases/phase_0_baseline/artifacts/eda_corpus_traceability_index.jsonl](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_corpus_traceability_index.jsonl).
  - Kiểm toán PDF vật lý: [val/audit/pdf_availability_manifest.json](file:///c:/DACNTT/eval/audit/pdf_availability_manifest.json) & [val/audit/pdf_availability_summary.csv](file:///c:/DACNTT/eval/audit/pdf_availability_summary.csv).
* **Kịch bản thực thi:** val/phases/phase_0_baseline/scripts/run_full_qasper_eda.py và val/audit/audit_pdf_availability.py.
* **Quy mô khảo sát:** Toàn bộ 1.585 bài báo khoa học và 5.049 câu hỏi nghiên cứu (Train: 888 bài / 2.593 câu; Dev: 281 bài / 1.005 câu; Test: 416 bài / 1.451 câu).
* **Kiểm toán dữ liệu & Kết quả đối soát:**
  - 0 bài báo trùng lặp ID, 0 câu hỏi trùng lặp ID. 1 bài báo duy nhất thiếu văn bản thô do lỗi trích xuất upstream của S2ORC (rXiv:1801.07804, 0 sections).
  - Phân bố câu hỏi: Extractive 57,0% (2.878 câu), Abstractive 20,0% (1.011 câu), Yes/No 14,1% (710 câu), Unanswerable 8,9% (450 câu).
  - Độ dài bài báo (N=1.584): Trung bình 3.575,1 từ, P50 = 3.401,0 từ, P95 = 6.707,3 từ.
  - Cấu trúc đề mục (N=1.584): 21.909 đề mục, trung bình 13,83 đề mục/bài, độ dài trung bình 258,5 từ/đề mục. Tỷ lệ xuất hiện đề mục IMRaD: Introduction 97,47% (1.544 bài), Conclusion 90,78% (1.438 bài).
  - Bất đối xứng truy vấn/bằng chứng: Câu hỏi trung bình 8,14 từ vs Đoạn bằng chứng trung bình 175,5 từ (chênh lệch 21,6 lần). Độ trùng lặp từ vựng Jaccard đạt 0,0161 (1,61%) trên toàn bộ 5.049 câu hỏi và 0,0259 (2,59%) trên 4.303 câu hỏi có bằng chứng văn bản.
  - Kiểm toán PDF vật lý: 61 tệp PDF khả dụng cục bộ (100% mở thành công qua PyMuPDF, 100% bóc tách văn bản đạt chuẩn >100 từ, 100% [185/185 câu hỏi có bằng chứng] gióng hàng bằng chứng văn bản vào tệp PDF với độ khớp >= 70% từ nội dung).
  - Phân định rõ ràng: 1.524 bài báo chưa có PDF là **thiếu cục bộ trên đĩa** (chưa tải về), hoàn toàn khác với việc không khả dụng từ xa; kiểm tra từ xa trên arXiv endpoint ghi nhận 24/25 bài mẫu khả dụng bình thường (96%), đúng 1 bài rXiv:1802.00396 trả về HTTP 404 cho đường dẫn PDF mặc định do bản v2 bị tác giả rút lại (withdrawn).

---
### 2.1. RQ1 — Phương Pháp Bóc Tách Văn Bản PDF
* **Tên thực nghiệm:** `RQ1 PDF Extractor Evaluation`.
* **Tệp dữ liệu gốc:** [`eval/results/rq1_extraction_20261024_000639.json`](file:///c:/DACNTT/eval/results/rq1_extraction_20261024_000639.json) và tệp truy vấn [`rq1_extraction_queries_20261024_000639.jsonl`](file:///c:/DACNTT/eval/results/rq1_extraction_queries_20261024_000639.jsonl).
* **Kịch bản thực thi:** `backend/scripts/evaluation/evaluate_rq1_extractors.py`.
* **Tập dữ liệu & Quy mô:** 47 bài báo khoa học thuộc tập QASPER Development Split có tệp PDF vật lý nguyên bản trên đĩa (`eval/prepared/`).
* **Các cấu hình khảo sát:** 
  1. `pymupdf_plain`: Trích xuất khối văn bản thông thường (Mốc đối chứng / Baseline).
  2. `pymupdf_layout`: Trích xuất có phân tích kích thước và định dạng phông chữ để phát hiện đề mục.
  3. `pypdf`: Thư viện xử lý PDF thuần Python.
  4. `pdfminer.six`: Phân tích cú pháp bố cục dòng và ký tự chi tiết.
  5. `pdfplumber`: Bóc tách dựa trên đối tượng đồ họa và bảng biểu.
  6. `grobid`: Máy chủ phân tích TEI XML cấu trúc học thuật (Ghi nhận trạng thái: Offline / Unreachable).
* **Mốc chuẩn đối chứng (Baseline):** `pymupdf_plain`.
* **Chỉ số chính & Phụ:**
  - *Chính:* Downstream $\text{nDCG@10}$ (mô hình nhúng `e5-small-v2`, ngân sách 1.600 tokens), $\text{Heading F1}$ (đối chiếu danh mục tiêu đề chuẩn tác giả).
  - *Phụ:* Evidence Coverage (%), Char-Match (%), Reading Order Concordance, Downstream $\text{Recall@20}$, Độ trễ (ms/trang), Peak RAM (MB).
* **Phân tích thống kê:** Bootstrap theo cụm bài báo ($B=2.000$, seed=42) tính khoảng tin cậy 95% CI và trị số $p$ hai phía so với `pymupdf_plain`.
* **Giới hạn đã xác nhận:**
  - `Heading F1 = 0,0%` ở 4 công cụ (`pymupdf_plain`, `pypdf`, `pdfminer.six`, `pdfplumber`) là do bộ điều hợp của các thư viện này chỉ trích xuất văn bản phẳng mà không gắn thẻ đề mục, không phải do thư viện bị lỗi.
  - Điểm nDCG@10 giữa top 4 công cụ (`pymupdf_plain` 0,5274, `pypdf` 0,5174, `pdfminer.six` 0,5131, `pymupdf_layout` 0,5100) không có sự khác biệt mang ý nghĩa thống kê ($p > 0,50$).
  - Máy chủ GROBID cục bộ không khả dụng được ghi nhận rõ ràng là giới hạn hạ tầng thử nghiệm, không gán điểm 0 gây sai lệch.

---

### 2.2. RQ2 — Chiến Lược Phân Mảnh Văn Bản
* **Tên thực nghiệm:** `RQ2 Document Chunking Strategy Evaluation`.
* **Tệp dữ liệu gốc:** [`eval/results/rq2_chunking_20261024_013443.json`](file:///c:/DACNTT/eval/results/rq2_chunking_20261024_013443.json) và tệp truy vấn [`rq2_chunking_queries_20261024_013443.jsonl`](file:///c:/DACNTT/eval/results/rq2_chunking_queries_20261024_013443.jsonl).
* **Kịch bản thực thi:** `backend/scripts/evaluation/evaluate_rq2_chunking.py`.
* **Tập dữ liệu & Quy mô:** 47 bài báo khoa học, 127 câu hỏi nghiên cứu có bằng chứng xác thực, ngân sách ngữ cảnh cố định $\text{Budget} = 1.600\text{ tokens}$.
* **Mô hình embedding cố định:** `intfloat/e5-small-v2` (384 chiều, chuẩn hóa $L_2$).
* **Các chiến lược so sánh:**
  1. `fixed_size`: Cắt cố định 400 tokens không gối đầu (Mốc đối chứng / Baseline).
  2. `fixed_size_overlap`: Cắt 400 tokens kèm gối đầu 80 tokens.
  3. `semantic`: Phân đoạn dựa trên ngưỡng khoảng cách vector câu liên tiếp.
  4. `section`: Giữ nguyên từng đề mục làm một phân đoạn (đoạn thô).
  5. `section_token`: Cắt trong đề mục theo kích thước token 250 tokens.
  6. `section_overlap`: Cắt trong đề mục 400 tokens kèm gối đầu 80 tokens (Cấu hình hệ thống).
  7. `hierarchical`: Phân cấp Small-to-Big (tìm trên đoạn con 150 tokens, nạp cả đoạn cha vào ngữ cảnh).
  8. `hierarchical_child`: Nhánh kiểm chứng độc lập (ablation), chỉ dùng đoạn con nhỏ không mở rộng đoạn cha.
* **Ngưỡng liên quan & Phân tích độ nhạy:** Ngưỡng chính $\tau = 0,50$ (50% từ tố bằng chứng), kiểm tra độ nhạy tại $\tau = 0,30$.
* **Chỉ số chính & Phụ:**
  - *Chính:* $\text{nDCG@10}$ ($\tau=0,50$), Tỷ lệ cắt cụt Subword (%).
  - *Phụ:* $\text{nDCG@4}$, $\text{Recall@20}$, $\text{MRR@10}$, Ngân sách ngữ cảnh bao phủ (%), $\text{nDCG@10}$ ($\tau=0,30$).
* **Phân tích thống kê:** Bootstrap theo cụm bài báo ($B=2.000$, seed=42) tính khoảng tin cậy 95% CI và trị số $p$ so với `fixed_size`.
* **Kết luận thống kê đã xác nhận:**
  - `hierarchical` vượt trội có ý nghĩa thống kê so với baseline ($\Delta = +0,1225, 95\%\text{ CI } [+0,0553; +0,1821], p = 0,0010^*$).
  - `semantic` suy giảm có ý nghĩa thống kê so với baseline ($\Delta = -0,0798, 95\%\text{ CI } [-0,1323; -0,0275], p = 0,0050^*$).
  - `section` bị cắt cụt subword nghiêm trọng: 23,70% số đoạn vượt trần 512 subwords của mô hình embedding.

---

### 2.3. RQ3 — Mô Hình Biểu Diễn Vector (Embedding Models)
* **Tên thực nghiệm:** `Unified Open-Source Embedding Benchmark for Academic Passage Retrieval`.
* **Tệp dữ liệu gốc:** [`eval/results/thesis_embedding_benchmark.json`](file:///c:/DACNTT/eval/results/thesis_embedding_benchmark.json).
* **Kịch bản thực thi:** `backend/scripts/evaluation/run_rq3_embedding_benchmark.py`.
* **Tập dữ liệu & Quy mô:** Ngữ liệu hợp nhất gồm **207 bài báo khoa học, 615 câu hỏi và 5.207 phân đoạn văn bản** ($\tau = 0,55$).
* **Phương pháp tính tương đồng:** Exact Brute-Force Cosine Similarity (tích vô hướng NumPy BLAS trên FP32 sau chuẩn hóa $L_2$), loại trừ sai số xấp xỉ của đồ thị HNSW.
* **Phần cứng đo đạc:** AMD Ryzen 5 5600 6 nhân / 12 luồng, cố định `torch_threads = 4`.
* **Danh sách 11 mô hình khảo sát:**
  1. `bm25`: Mốc đối chứng từ khóa thưa (Sparse Baseline, WordPiece tokenization).
  2. `all-MiniLM-L6-v2`: 22,7M tham số, 384 chiều (Mốc đối chứng Dense Baseline).
  3. `e5-small-v2`: 33,4M tham số, 384 chiều (Mô hình được chọn cho hệ thống).
  4. `bge-small-en-v1.5`: 33,4M tham số, 384 chiều.
  5. `gte-small`: 33,4M tham số, 384 chiều.
  6. `snowflake-arctic-embed-s`: 33,2M tham số, 384 chiều.
  7. `snowflake-arctic-embed-m-v1.5`: 108,9M tham số, 768 chiều.
  8. `nomic-embed-text-v1.5`: 137,0M tham số, 768 chiều.
  9. `modernbert-embed-base`: 149,0M tham số, 768 chiều.
  10. `snowflake-arctic-embed-m-v2.0`: 305,0M tham số, 768 chiều.
  11. `mxbai-embed-large-v1`: 335,1M tham số, 1.024 chiều.
* **Chỉ số đo lường:**
  - *Chất lượng truy xuất:* $\text{nDCG@10}$ (kèm 95% CI Bootstrap), $\text{nDCG@4}$, $\text{Recall@20}$, $\text{MRR@10}$.
  - *Hiệu năng phần cứng:* Độ trễ truy vấn P50 và P95 (ms, $B=1$), Thông lượng lập chỉ mục (chunks/s, $B=32$), Bộ nhớ thường trú đỉnh Process Peak RSS (MB).
* **Đính chính sai số học thuật quan trọng:**
  - BGE-Small-v1.5 ghi nhận $p = 0,0830$ với 95% CI $[-0,0027; +0,0393]$ bao trùm giá trị 0. **BGE-Small không có ý nghĩa thống kê vượt trội so với MiniLM** ở mức $\alpha = 0,05$. Bản thảo cũ từng khẳng định $p < 0,001$ đã được đính chính hoàn toàn.
  - Thông lượng mã hóa CPU được đo đạc thực tế chính xác: MiniLM đạt 19,0 chunks/s, E5-Small đạt 6,5 chunks/s, ModernBERT đạt 1,8 chunks/s; loại bỏ hoàn toàn các con số suy đoán phóng đại (198 và 315 chunks/s) trong các ghi chú cũ.

---

## 3. Xác Nhận Kiểm Tra Tái Lập (Reproducibility Sign-off)

- [x] Lệnh gọi `python reports/chapter5/scripts/generate_tables_and_plots.py` thực thi thành công (Mã thoát: 0).
- [x] 4 tệp bảng `.csv` được xuất đúng vị trí tại `reports/chapter5/tables/`.
- [x] 5 tệp đồ thị `.png` được xuất đúng vị trí tại `reports/chapter5/figures/` và `docs/figures/`.
- [x] Mọi giá trị số trong bản thảo Chương 5 đã được đối soát khớp 100% với các tệp JSON và ma trận truy vết.
