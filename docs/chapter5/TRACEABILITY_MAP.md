# BẢN ĐỒ TRUY VẾT DỮ LIỆU THỰC NGHIỆM (TRACEABILITY MAP) — CHƯƠNG 5
**Dự án: Xây dựng hệ thống quản lý tài liệu nghiên cứu khoa học tích hợp trợ lý AI sử dụng RAG**

Bản đồ này kết nối từng khẳng định định lượng, chỉ số đo lường, khoảng tin cậy và giá trị kiểm định thống kê trong Chương 5 tới chính xác trường dữ liệu trong các tệp kết quả JSON gốc.

---

## 0. Truy Vết Phân Tích Khám Phá Dữ Liệu (EDA), Kiểm Toán PDF và Phân Hoạch Ngữ Liệu

*Tệp nguồn:*
- **Toàn bộ Benchmark QASPER (Full Benchmark N=1.585 bài báo, 5.049 câu hỏi):**
  - Trích xuất & phân phối chính: [`eval/phases/phase_0_baseline/artifacts/qasper_full_corpus_eda.json`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/qasper_full_corpus_eda.json)
  - Đối chiếu Pilot vs Toàn bộ: [`eval/phases/phase_0_baseline/artifacts/eda_pilot_vs_full_comparison.csv`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_pilot_vs_full_comparison.csv)
  - Bảng phân phối câu hỏi: [`eval/phases/phase_0_baseline/artifacts/eda_question_distribution.csv`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_question_distribution.csv)
  - Bảng phân phối tiêu đề đề mục: [`eval/phases/phase_0_baseline/artifacts/eda_section_heading_distribution.csv`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_section_heading_distribution.csv)
  - Chỉ mục truy vết từng câu hỏi: [`eval/phases/phase_0_baseline/artifacts/eda_corpus_traceability_index.jsonl`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_corpus_traceability_index.jsonl)
- **Kiểm toán tính khả dụng tệp PDF vật lý:**
  - Bản kê kiểm toán: [`eval/audit/pdf_availability_manifest.json`](file:///c:/DACNTT/eval/audit/pdf_availability_manifest.json)
  - Bảng tổng hợp độ khả dụng: [`eval/audit/pdf_availability_summary.csv`](file:///c:/DACNTT/eval/audit/pdf_availability_summary.csv)
- **Mẫu Pilot thăm dò sơ bộ (Pilot N=100 bài báo, 250 câu hỏi):**
  - Tệp JSON gốc: [`eval/phases/phase_0_baseline/artifacts/qasper_comprehensive_eda.json`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/qasper_comprehensive_eda.json)
- **Phân hoạch ngữ liệu thực nghiệm:**
  - Bảng phân hoạch: [`reports/chapter5/tables/table_5_0_dataset_partition.csv`](file:///c:/DACNTT/reports/chapter5/tables/table_5_0_dataset_partition.csv)

### 0.1. Toàn bộ Benchmark QASPER (N = 1.585 bài báo, 5.049 câu hỏi)

| Khẳng định số học / Chỉ số | Giá trị báo cáo | Vị trí trong tệp JSON gốc (JSON Pointer / Field) | Phương pháp kiểm chứng | Trạng thái đối soát |
| :--- | :---: | :--- | :--- | :---: |
| Tổng số bài báo toàn benchmark | **1.585 bài** | `qasper_full_corpus_eda.json` -> `corpus_overview.total_papers` | Đếm unique paper ID (Train 888 + Dev 281 + Test 416) | 100% Khớp |
| Tổng số câu hỏi toàn benchmark | **5.049 câu** | `corpus_overview.total_questions` | Đếm unique question ID (Train 2.593 + Dev 1.005 + Test 1.451) | 100% Khớp |
| Tỷ lệ câu hỏi Extractive (Toàn văn) | **57,0%** (57,00% / 2.878 câu) | `question_distribution.counts.extractive` & `.percentages.extractive` | $2.878 / 5.049$ câu hỏi có nhãn trích xuất | 100% Khớp |
| Tỷ lệ câu hỏi Abstractive (Toàn văn) | **20,0%** (20,02% / 1.011 câu) | `question_distribution.counts.abstractive` & `.percentages.abstractive` | $1.011 / 5.049$ câu hỏi diễn giải tự do | 100% Khớp |
| Tỷ lệ câu hỏi Yes/No (Toàn văn) | **14,1%** (14,06% / 710 câu) | `question_distribution.counts.yes_no` & `.percentages.yes_no` | $710 / 5.049$ câu hỏi xác nhận nhị phân | 100% Khớp |
| Tỷ lệ câu hỏi Không thể trả lời (Unanswerable) | **8,9%** (8,91% / 450 câu) | `question_distribution.counts.unanswerable` & `.percentages.unanswerable` | $450 / 5.049$ câu (410 đồng thuận tuyệt đối) | 100% Khớp |
| Số từ trung bình / bài báo | **3.575,1 từ** | `paper_length_distribution.mean_words` | Trung bình trên 1.585 bài báo | 100% Khớp |
| Số từ trung vị (P50) / bài báo | **3.401,0 từ** | `paper_length_distribution.p50_words` | Phân vị thứ 50 | 100% Khớp |
| Phân vị 95% (P95) số từ / bài báo | **6.707,3 từ** | `paper_length_distribution.p95_words` | Phân vị thứ 95 (vượt 9.000 subwords) | 100% Khớp |
| Số đề mục trung bình / bài báo | **13,83 đề mục** | `document_structure.mean_sections_per_paper` | Tổng 21.909 đề mục / 1.584 bài có cấu trúc | 100% Khớp |
| Số từ trung bình / đề mục | **258,5 từ** | `document_structure.mean_words_per_section` | Trung bình độ dài 21.905 đề mục (P50 = 188 từ) | 100% Khớp |
| Tiêu đề Introduction phổ biến nhất | **97,47%** (1.544 bài) | `document_structure.canonical_heading_frequencies.introduction.paper_pct` | Tỷ lệ bài báo xuất hiện đề mục Introduction | 100% Khớp |
| Tiêu đề Conclusion phổ biến thứ hai | **90,78%** (1.438 bài) | document_structure.canonical_heading_frequencies.conclusion.paper_pct | Tỷ lệ bài báo xuất hiện đề mục Conclusion | 100% Khớp |
| Độ dài câu hỏi trung bình | **8,14 từ** | `query_evidence_relationship.query_length.mean_words` | Trung bình số từ trên 5.049 câu hỏi (P50 = 7 từ) | 100% Khớp |
| Độ dài đoạn bằng chứng trung bình | **175,5 từ** | `query_evidence_relationship.evidence_passage_length.mean_words` | Trung bình số từ trên 7.464 đoạn bằng chứng văn bản | 100% Khớp |
| Tỷ lệ câu hỏi đa đoạn bằng chứng | **43,95%** (1.891 / 4.303 câu có bằng chứng) | `query_evidence_relationship.multi_passage_evidence_count` | 1.891 câu / 4.303 câu hỏi có bằng chứng văn bản | 100% Khớp |
| Độ trùng lặp từ vựng Jaccard | **0,0161 (1,61%)** (toàn bộ 5.049 câu) / **0,0259 (2,59%)** (4.303 câu có bằng chứng) | `query_evidence_relationship.lexical_jaccard_overlap.mean_overlap` | Độ tương đồng từ vựng lọc stopwords trên 4.303 câu | 100% Khớp |
| Tỷ lệ PDF vật lý cục bộ khả dụng | **61 / 61 (100,0%)** mở & bóc tách thành công | `pdf_availability_manifest.json` -> `summary` | 61 PDF hiện hữu mở không lỗi, bóc tách văn bản đạt 100% | 100% Khớp |
| Tỷ lệ bằng chứng khớp PDF vật lý | **100,0% (185 / 185 câu hỏi)** | `pdf_availability_manifest.json` -> `summary.evidence_aligned_rate` | Khớp >=70% từ nội dung bằng chứng vào PDF | 100% Khớp |

### 0.2. Mẫu Pilot Sơ Bộ & Ngữ Liệu Thực Nghiệm (RQ1–RQ3)

| Khẳng định số học / Chỉ số | Giá trị báo cáo | Vị trí trong tệp JSON gốc (JSON Pointer / Field) | Phương pháp kiểm chứng | Trạng thái đối soát |
| :--- | :---: | :--- | :--- | :---: |
| Tỷ lệ câu hỏi Extractive (Pilot) | **70,0%** (175 câu) | `question_statistics.type_percentages.extractive` | Đếm trực tiếp trong tập câu hỏi Pilot | 100% Khớp |
| Tỷ lệ câu hỏi Yes/No (Pilot) | **14,4%** (36 câu) | `question_statistics.type_percentages.yes_no` | Đếm trực tiếp trong tập câu hỏi Pilot | 100% Khớp |
| Tỷ lệ câu hỏi Abstractive (Pilot) | **12,4%** (31 câu) | `question_statistics.type_percentages.abstractive` | Đếm trực tiếp trong tập câu hỏi Pilot | 100% Khớp |
| Tỷ lệ câu hỏi Unanswerable (Pilot) | **3,2%** (8 câu) | `question_statistics.type_percentages.unanswerable` | Đếm trực tiếp trong tập câu hỏi Pilot | 100% Khớp |
| Số từ trung bình / bài báo (Pilot) | **3.257,2 từ** | `document_statistics.mean_words_per_doc` | Tính trung bình số từ trên toàn văn Pilot | 100% Khớp |
| Độ lệch chuẩn số từ / bài (Pilot) | **1.593,4 từ** | `document_statistics.std_words_per_doc` | Tính độ lệch chuẩn | 100% Khớp |
| Số từ trung vị (P50) / bài (Pilot) | **2.980,5 từ** | `document_statistics.p50_words_per_doc` | Tính phân vị thứ 50 | 100% Khớp |
| Phân vị 95% (P95) số từ / bài (Pilot) | **5.843,6 từ** | `document_statistics.p95_words_per_doc` | Tính phân vị thứ 95 | 100% Khớp |
| Độ dài câu hỏi trung bình (Pilot) | **7,95 từ** | `question_statistics.mean_words_per_question` | Tính trung bình số từ câu hỏi Pilot | 100% Khớp |
| Độ dài bằng chứng trung bình (Pilot) | **190,9 từ** | `evidence_statistics.mean_evidence_words` | Tính trung bình số từ đoạn bằng chứng Pilot | 100% Khớp |
| Tỷ lệ câu hỏi đa đoạn bằng chứng (Pilot) | **52,0%** (130/250 câu) / **53,7%** (130/242 câu có bằng chứng) | `evidence_statistics.multi_passage_evidence_count` | 130 / 250 câu hỏi tổng thể (130 / 242 câu có nhãn) | 100% Khớp |
| Độ trùng lặp từ vựng Jaccard (Pilot) | **0,0158 (1,58%)** | `evidence_statistics.mean_lexical_jaccard_overlap` | Độ tương đồng tập từ vựng $>3$ ký tự | 100% Khớp |
| Số đề mục trung bình / bài báo (Pilot) | **13,36 mục** | `document_statistics.mean_sections_per_doc` | 1.336 mục / 100 bài báo Pilot | 100% Khớp |
| Số từ trung bình / đề mục (Pilot) | **243,8 từ** | `document_statistics.mean_words_per_section` | Trung bình trên 1.336 đề mục Pilot | 100% Khớp |
| Tiêu đề mục Introduction phổ biến nhất (Pilot) | **98 bài** | `top_10_section_headings.introduction` | Tần suất xuất hiện đề mục Pilot | 100% Khớp |
| Quy mô tập Dev (có PDF vật lý) | **47 bài báo** | `eval/prepared/dev_held_out_split.json` & `eval/pdfs/dev/` | Lọc trừ đúng 1 bài `arXiv:1802.00396` thiếu PDF vật lý (48 - 1 = 47) | 100% Khớp |
| Quy mô câu hỏi có bằng chứng RQ1 & RQ2 | **127 câu hỏi** | `eval/prepared/dev_held_out_split.json` & `qasper_sampled.json` | 132 gốc - 2 (bài thiếu PDF) = 130; 130 - 3 (Unanswerable) = 127 câu hỏi | 100% Khớp |
| Tỷ lệ giữ lại câu hỏi hợp lệ RQ1 & RQ2 | **100% (127/127 câu)** | `rq1_extraction_20261024_000639.json` | Toàn bộ 127 câu hỏi có bằng chứng đều tham gia thực nghiệm | 100% Khớp |
| Quy mô ngữ liệu nội bộ hợp nhất RQ3 | **207 bài báo, 615 câu hỏi, 5.207 chunks** | `table_5_0_dataset_partition.csv` & `thesis_embedding_benchmark.json` | 48 Dev (1.099 chunks, 128 câu hỏi) + 159 Held-out (4.108 chunks, 487 câu hỏi) | 100% Khớp |
| Độ mạnh thống kê ước tính tại SESOI=0,030 | **38,6%** (K=159) / **44,5%** (K=200) | `eval/phases/phase_3_embedding/artifacts/statistical_audit_results.json` | Mô phỏng Monte Carlo B=2.000; cần K~500 để đạt Power >= 80% ở Delta=0,030 | 100% Khớp |
| Độ mạnh thống kê quan sát tại Delta >= 0,05 | **78,3% - 85,5%** | `statistical_audit_results.json` (lines 439-462) | Đạt độ mạnh cao cho mức khác biệt lớn (như E5 vs MiniLM/BGE) | 100% Khớp |
| Rò rỉ trọng số mô hình (Model Weight Leakage) | **0% (Zero)** | `thesis_embedding_benchmark.json` | 11 mô hình nền tảng tải từ HF Hub với frozen weights, zero-shot | 100% Khớp |

---

## 1. Truy Vết RQ1 — Phương Pháp Bóc Tách Văn Bản PDF

*Tệp nguồn:* [`eval/results/rq1_extraction_20261024_000639.json`](file:///c:/DACNTT/eval/results/rq1_extraction_20261024_000639.json) (47 bài báo QASPER Dev).

| Khẳng định số học / Chỉ số | Giá trị báo cáo | Vị trí trong tệp JSON gốc (JSON Pointer / Field) | Phương pháp kiểm chứng | Trạng thái đối soát |
| :--- | :---: | :--- | :--- | :---: |
| Quy mô số lượng bài báo đánh giá | **47 bài báo** | `metadata.papers_evaluated` | Đếm số phần tử tệp JSON | 100% Khớp |
| Tốc độ xử lý của `pymupdf_plain` | **10,19 ms/trang** | `summary[0].latency_per_page_ms` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Bộ nhớ đỉnh của `pymupdf_plain` | **1.228,7 MB** | `summary[0].peak_ram_mb` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 của `pymupdf_plain` | **0,5274** [0,4724; 0,5839] | `summary[0].downstream_ndcg10.mean` & `.ci_95` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Recall@20 của `pymupdf_plain` | **0,9424** | `summary[0].downstream_recall20` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Heading F1 của `pymupdf_layout` | **48,01%** | `summary[1].heading_f1` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Tốc độ xử lý của `pymupdf_layout` | **26,16 ms/trang** | `summary[1].latency_per_page_ms` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Bộ nhớ đỉnh của `pymupdf_layout` | **1.164,9 MB** | `summary[1].peak_ram_mb` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 của `pymupdf_layout` | **0,5100** [0,4398; 0,5822] | `summary[1].downstream_ndcg10.mean` & `.ci_95` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và trị số $p$ của `pymupdf_layout` | $\Delta = -0,0175, p = 0,5597$ | `summary[1].stats_vs_baseline.diff_ndcg10` & `.p_value` | Bootstrap theo cụm bài báo ($B=2.000$) | 100% Khớp |
| Tốc độ xử lý của `pypdf` | **61,72 ms/trang** | `summary[2].latency_per_page_ms` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 của `pypdf` | **0,5174** [0,4597; 0,5792] | `summary[2].downstream_ndcg10.mean` & `.ci_95` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Recall@20 của `pypdf` | **0,9509** | `summary[2].downstream_recall20` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Tốc độ xử lý của `pdfminer.six` | **107,10 ms/trang** | `summary[3].latency_per_page_ms` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 của `pdfminer.six` | **0,5131** [0,4615; 0,5696] | `summary[3].downstream_ndcg10.mean` & `.ci_95` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Trật tự đọc của `pdfplumber` | **0,5319** | `summary[4].reading_order_concordance` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Tốc độ xử lý của `pdfplumber` | **195,36 ms/trang** | `summary[4].latency_per_page_ms` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 của `pdfplumber` | **0,3769** [0,3108; 0,4442] | `summary[4].downstream_ndcg10.mean` & `.ci_95` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `pdfplumber` | $\Delta = -0,1505, p = 0,0010^*$ | `summary[4].stats_vs_baseline.diff_ndcg10` & `.p_value` | Bootstrap theo cụm bài báo ($B=2.000$) | 100% Khớp |
| Trạng thái của máy chủ `grobid` | **Offline / Unreachable** | `summary[5].available: false` | Ghi nhận ngoại lệ mạng | 100% Khớp |

---

## 2. Truy Vết RQ2 — Chiến Lược Phân Mảnh Văn Bản

*Tệp nguồn:* [`eval/results/rq2_chunking_20261024_013443.json`](file:///c:/DACNTT/eval/results/rq2_chunking_20261024_013443.json) (47 bài báo, 127 câu hỏi, ngân sách 1.600 tokens).

| Khẳng định số học / Chỉ số | Giá trị báo cáo | Vị trí trong tệp JSON gốc (JSON Pointer / Field) | Phương pháp kiểm chứng | Trạng thái đối soát |
| :--- | :---: | :--- | :--- | :---: |
| Ngân sách ngữ cảnh danh nghĩa | **1.600 tokens** | `metadata.context_budget_tokens` | Đọc trực tiếp từ metadata | 100% Khớp |
| Tổng số Chunks của `fixed_size` | **893 chunks** | `summary[0].total_chunks` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Tokens TB / Chunk của `fixed_size` | **388,8 tokens** | `summary[0].avg_tokens_per_chunk` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Tỷ lệ cắt cụt subword `fixed_size` | **0,00%** | `summary[0].subword_truncation_rate_pct` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 ($\tau=0,5$) của `fixed_size` | **0,5654** [0,5101; 0,6240] | `summary[0].primary_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@4 của `fixed_size` | **0,4443** | `summary[0].primary_metrics.ndcg4` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Recall@20 của `fixed_size` | **0,9586** | `summary[0].primary_metrics.recall20` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| MRR@10 của `fixed_size` | **0,5310** | `summary[0].primary_metrics.mrr10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 ($\tau=0,3$) của `fixed_size` | **0,6252** | `summary[0].sensitivity_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 của `fixed_size_overlap` | **0,5385** [0,4835; 0,6008] | `summary[1].primary_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `fixed_size_overlap` | $\Delta = -0,0269, p = 0,2129$ | `summary[1].stats_vs_baseline` | Bootstrap theo cụm bài báo | 100% Khớp |
| nDCG@10 ($\tau=0,5$) của `semantic` | **0,4856** [0,4305; 0,5439] | `summary[2].primary_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `semantic` | $\Delta = -0,0798, p = 0,0050^*$ | `summary[2].stats_vs_baseline` | Bootstrap theo cụm ($p \le 0,005$) | 100% Khớp |
| Tỷ lệ cắt cụt subword của `section` | **23,70%** | `summary[3].subword_truncation_rate_pct` | Đếm số đoạn vượt 512 subwords | 100% Khớp |
| nDCG@10 ($\tau=0,5$) của `section` | **0,5795** [0,5191; 0,6392] | `summary[3].primary_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `section` | $\Delta = +0,0141, p = 0,6537$ | `summary[3].stats_vs_baseline` | Bootstrap theo cụm ($p > 0,05$) | 100% Khớp |
| nDCG@4 của `section_overlap` | **0,4569** | `summary[5].primary_metrics.ndcg4` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| MRR@10 của `section_overlap` | **0,5737** | `summary[5].primary_metrics.mrr10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 của `section_overlap` | **0,5409** [0,4761; 0,6084] | `summary[5].primary_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 ($\tau=0,5$) của `hierarchical` | **0,6880** [0,6348; 0,7371] | `summary[6].primary_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@4 của `hierarchical` | **0,5933** | `summary[6].primary_metrics.ndcg4` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Recall@20 của `hierarchical` | **0,9873** | `summary[6].primary_metrics.recall20` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| MRR@10 của `hierarchical` | **0,6468** | `summary[6].primary_metrics.mrr10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `hierarchical` | $\Delta = +0,1225, p = 0,0010^*$ | `summary[6].stats_vs_baseline` | Bootstrap theo cụm ($p \le 0,001$) | 100% Khớp |
| nDCG@10 ($\tau=0,3$) của `hierarchical` | **0,7340** | `summary[6].sensitivity_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@10 của `hierarchical_child` | **0,4473** [0,3883; 0,5052] | `summary[7].primary_metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `hierarchical_child` | $\Delta = -0,1182, p = 0,0020^*$ | `summary[7].stats_vs_baseline` | Bootstrap theo cụm ($p \le 0,002$) | 100% Khớp |

---

## 3. Truy Vết RQ3 — Mô Hình Biểu Diễn Vector (Embedding Benchmark)

*Tệp nguồn:* [`eval/results/thesis_embedding_benchmark.json`](file:///c:/DACNTT/eval/results/thesis_embedding_benchmark.json) (207 bài báo, 615 câu hỏi, 5.207 chunks, $\tau = 0,55$).

| Khẳng định số học / Chỉ số | Giá trị báo cáo | Vị trí trong tệp JSON gốc (JSON Pointer / Field) | Phương pháp kiểm chứng | Trạng thái đối soát |
| :--- | :---: | :--- | :--- | :---: |
| Số bài báo / câu hỏi / chunks | **207 bài / 615 Q / 5.207 C** | `metadata.corpus` | Đếm phần tử thực nghiệm | 100% Khớp |
| nDCG@10 của `bm25` | **0,4805** [0,4480; 0,5130] | `models[0].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Độ trễ P50 của `bm25` | **0,10 ms** | `models[0].efficiency.query_latency_p50_ms` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Thông lượng của `bm25` | **14.673,3 chunks/s** | `models[0].efficiency.indexing_throughput_chunks_sec` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Peak RAM của `bm25` | **477,9 MB** | `models[0].efficiency.peak_ram_mb` | Đo đạc qua `psutil.Process` | 100% Khớp |
| nDCG@10 của `all-MiniLM-L6-v2` | **0,5026** [0,4746; 0,5315] | `models[1].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Độ trễ P50 của `all-MiniLM-L6-v2` | **19,30 ms** | `models[1].efficiency.query_latency_p50_ms` | Phân vị P50 qua 100 truy vấn B=1 | 100% Khớp |
| Thông lượng của `all-MiniLM-L6-v2` | **19,0 chunks/s** | `models[1].efficiency.indexing_throughput_chunks_sec` | Đo đạc thực nghiệm B=32 CPU | 100% Khớp |
| Peak RAM của `all-MiniLM-L6-v2` | **593,1 MB** | `models[1].efficiency.peak_ram_mb` | Đo đạc qua `psutil.Process` | 100% Khớp |
| nDCG@10 của `intfloat/e5-small-v2` | **0,5522** [0,5253; 0,5778] | `models[2].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `e5-small-v2` | $\Delta = +0,0497, p = 0,0010^*$ | `models[2].stats_vs_baseline` | Bootstrap theo cụm ($p \le 0,001$) | 100% Khớp |
| Độ trễ P50 của `e5-small-v2` | **30,26 ms** | `models[2].efficiency.query_latency_p50_ms` | Phân vị P50 qua 100 truy vấn B=1 | 100% Khớp |
| Thông lượng của `e5-small-v2` | **6,5 chunks/s** | `models[2].efficiency.indexing_throughput_chunks_sec` | Đo đạc thực nghiệm B=32 CPU | 100% Khớp |
| Peak RAM của `e5-small-v2` | **659,8 MB** | `models[2].efficiency.peak_ram_mb` | Đo đạc qua `psutil.Process` | 100% Khớp |
| nDCG@10 của `bge-small-en-v1.5` | **0,5209** [0,4901; 0,5520] | `models[3].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `bge-small-en-v1.5` | $\Delta = +0,0183, p = 0,0830$ | `models[3].stats_vs_baseline` | Bootstrap theo cụm ($p > 0,05$) | 100% Khớp (Đính chính) |
| Độ trễ P50 của `bge-small-en-v1.5` | **34,14 ms** | `models[3].efficiency.query_latency_p50_ms` | Phân vị P50 qua 100 truy vấn B=1 | 100% Khớp |
| nDCG@10 của `gte-small` | **0,4659** [0,4358; 0,4957] | `models[4].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `gte-small` | $\Delta = -0,0367, p = 0,0010^*$ | `models[4].stats_vs_baseline` | Bootstrap theo cụm | 100% Khớp |
| nDCG@10 của `arctic-embed-s` | **0,5417** [0,5115; 0,5714] | `models[5].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `arctic-embed-s` | $\Delta = +0,0392, p = 0,0020^*$ | `models[5].stats_vs_baseline` | Bootstrap theo cụm | 100% Khớp |
| nDCG@10 của `arctic-embed-m-v1.5` | **0,5472** [0,5186; 0,5756] | `models[6].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Độ trễ P50 của `arctic-embed-m-v1.5` | **74,44 ms** | `models[6].efficiency.query_latency_p50_ms` | Phân vị P50 qua 100 truy vấn B=1 | 100% Khớp |
| Thông lượng của `arctic-embed-m-v1.5` | **2,4 chunks/s** | `models[6].efficiency.indexing_throughput_chunks_sec` | Đo đạc thực nghiệm B=32 CPU | 100% Khớp |
| Peak RAM của `arctic-embed-m-v1.5` | **956,0 MB** | `models[6].efficiency.peak_ram_mb` | Đo đạc qua `psutil.Process` | 100% Khớp |
| nDCG@10 của `nomic-embed-text-v1.5` | **0,5133** [0,4843; 0,5422] | `models[7].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Độ trễ P50 của `nomic-embed-text-v1.5` | **110,19 ms** | `models[7].efficiency.query_latency_p50_ms` | Phân vị P50 qua 100 truy vấn B=1 | 100% Khớp |
| nDCG@10 của `modernbert-embed-base` | **0,5872** [0,5586; 0,6166] | `models[8].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| nDCG@4 của `modernbert-embed-base` | **0,4937** | `models[8].metrics.ndcg4.mean` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Recall@20 của `modernbert-embed-base` | **0,9642** | `models[8].metrics.recall20.mean` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| MRR@10 của `modernbert-embed-base` | **0,5438** | `models[8].metrics.mrr10.mean` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `modernbert` | $\Delta = +0,0846, p = 0,0010^*$ | `models[8].stats_vs_baseline` | Bootstrap theo cụm ($p \le 0,001$) | 100% Khớp |
| Độ trễ P50 của `modernbert-embed-base` | **103,39 ms** | `models[8].efficiency.query_latency_p50_ms` | Phân vị P50 qua 100 truy vấn B=1 | 100% Khớp |
| Thông lượng của `modernbert-embed-base` | **1,8 chunks/s** | `models[8].efficiency.indexing_throughput_chunks_sec` | Đo đạc thực nghiệm B=32 CPU | 100% Khớp |
| Peak RAM của `modernbert-embed-base` | **1.161,7 MB** | `models[8].efficiency.peak_ram_mb` | Đo đạc qua `psutil.Process` | 100% Khớp |
| nDCG@10 của `arctic-embed-m-v2.0` | **0,4809** [0,4512; 0,5090] | `models[9].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Độ trễ P50 của `arctic-embed-m-v2.0` | **114,49 ms** | `models[9].efficiency.query_latency_p50_ms` | Phân vị P50 qua 100 truy vấn B=1 | 100% Khớp |
| Peak RAM của `arctic-embed-m-v2.0` | **1.399,5 MB** | `models[9].efficiency.peak_ram_mb` | Đo đạc qua `psutil.Process` | 100% Khớp |
| nDCG@10 của `mxbai-embed-large-v1` | **0,5064** [0,4776; 0,5344] | `models[10].metrics.ndcg10` | Đọc trực tiếp từ trường dữ liệu | 100% Khớp |
| Sai khác $\Delta$ và $p$ của `mxbai-large` | $\Delta = +0,0039, p = 0,7236$ | `models[10].stats_vs_baseline` | Bootstrap theo cụm ($p > 0,05$) | 100% Khớp |
| Độ trễ P50 của `mxbai-large` | **275,34 ms** | `models[10].efficiency.query_latency_p50_ms` | Phân vị P50 qua 100 truy vấn B=1 | 100% Khớp |
| Thông lượng của `mxbai-large` | **0,6 chunks/s** | `models[10].efficiency.indexing_throughput_chunks_sec` | Đo đạc thực nghiệm B=32 CPU | 100% Khớp |
| Peak RAM của `mxbai-large` | **1.292,0 MB** | `models[10].efficiency.peak_ram_mb` | Đo đạc qua `psutil.Process` | 100% Khớp |

---

## 4. Ma Trận Truy Vết Luồng Dữ Liệu Toàn Trình (End-to-End Pipeline Traceability)

| Câu hỏi | Tập dữ liệu đầu vào | Mã nguồn thực thi đánh giá | Tệp kết quả JSON gốc | Bảng CSV ấn phẩm | Đồ thị PNG ấn phẩm | Mục tương ứng trong Chương 5 | Cấu phần tương ứng trong Chương 4 |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RQ1** | 47 bài báo QASPER Dev | `backend/scripts/evaluation/evaluate_rq1_extractors.py` | `eval/results/rq1_extraction_20261024_000639.json`<br/>`rq1_extraction_queries_20261024_000639.jsonl` | `reports/chapter5/tables/table_5_1_rq1_extraction.csv` | `fig5_1_rq1_ndcg10.png`<br/>`fig5_2_rq1_latency.png` | **Mục 5.2** (Bảng 5.1, Hình 5.1, 5.2) | `chunking_utils.py` (`extract_sections_from_pdf`)<br/>Mục 4.7.2 |
| **RQ2** | 47 bài báo, 127 câu hỏi, 1.600 tokens | `backend/scripts/evaluation/evaluate_rq2_chunking.py` | `eval/results/rq2_chunking_20261024_013443.json`<br/>`rq2_chunking_queries_20261024_013443.jsonl` | `reports/chapter5/tables/table_5_2_rq2_chunking.csv` | `fig5_3_rq2_chunking_ndcg10.png` | **Mục 5.3** (Bảng 5.2, Hình 5.3) | `chunking_utils.py` (`chunk_sections`, `section_overlap`)<br/>Mục 4.7.5 |
| **RQ3** | 207 bài báo, 615 câu hỏi, 5.207 chunks | `backend/scripts/evaluation/run_thesis_embedding_benchmark.py` | `eval/results/thesis_embedding_benchmark.json` | `reports/chapter5/tables/table_5_3_rq3_embedding.csv` | `fig5_4_rq3_embedding_ndcg10.png`<br/>`fig5_5_rq3_quality_cost.png` | **Mục 5.4** (Bảng 5.3, Hình 5.4, 5.5) | `rag_service.py` (`intfloat/e5-small-v2`, `MODEL_PREFIX_SPECS`)<br/>Mục 4.7.5 |
| **Tổng hợp** | Toàn bộ RQ1–RQ3 | `reports/chapter5/scripts/generate_tables_and_plots.py` | Các tệp kết quả trên | `reports/chapter5/tables/table_5_4_summary_rq1_rq3.csv` | Toàn bộ 5 đồ thị | **Mục 5.5** (Bảng 5.4) | Bảng kiểm kê tính năng Mục 4.7.6 & Kiến trúc Mục 4.3 |
