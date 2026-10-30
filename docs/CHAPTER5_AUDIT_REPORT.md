# BÁO CÁO KIỂM TOÁN VÀ ĐỐI SOÁT KẾT QUẢ THỰC NGHIỆM — CHƯƠNG 5
**Dự án: Xây dựng hệ thống quản lý tài liệu nghiên cứu khoa học tích hợp trợ lý AI sử dụng RAG**

---

## 1. Mục đích và Phạm vi Báo cáo

Báo cáo này được lập nhằm mục đích kiểm toán độc lập, đối soát số liệu và xác nhận tính toàn vẹn của toàn bộ các bằng chứng thực nghiệm được trình bày trong **CHƯƠNG 5: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN** (`docs/CHAPTER5_DRAFT.md`). 

Báo cáo tuân thủ nguyên tắc cốt lõi: **ZERO FABRICATION**. Mọi giá trị số học, khoảng tin cậy bootstrap, độ trễ và thông lượng trong chương đều phải được truy xuất trực tiếp từ các tệp nhật ký đo đạc gốc trong `eval/results/` và được sinh ra từ các kịch bản thực nghiệm có thể tái lập 100%.

---

## 2. Bảng Đối soát Nguồn Dữ liệu Thực nghiệm (Traceability Matrix)

| Câu hỏi nghiên cứu | Tập dữ liệu khảo sát | Chỉ số cốt lõi | Mốc đối chứng (Baseline) | Tệp dữ liệu gốc (Authoritative Artifact) | Kịch bản thực nghiệm / Sinh đồ thị | Trạng thái xác thực |
| :--- | :--- | :--- | :--- | :--- | :--- | :---: |
| **RQ1: Bóc tách PDF** | 47 bài báo QASPER Dev | nDCG@10, Heading F1, Độ trễ (ms/trang) | `pymupdf_plain` | `eval/results/rq1_extraction_20261024_000639.json`<br/>`eval/results/rq1_extraction_queries_20261024_000639.jsonl` | `backend/scripts/evaluation/evaluate_rq1_extractors.py`<br/>`eval/scripts/plot_chapter5_figures.py` | **100% Khớp số liệu** |
| **RQ2: Phân mảnh văn bản** | 47 bài báo, 127 câu hỏi, 1.600 tokens budget | nDCG@10, nDCG@4, Recall@20, Truncation (%) | `fixed_size` (400 tokens) | `eval/results/rq2_chunking_20261024_013443.json`<br/>`eval/results/rq2_chunking_queries_20261024_013443.jsonl` | `backend/scripts/evaluation/evaluate_rq2_chunking.py`<br/>`eval/scripts/plot_chapter5_figures.py` | **100% Khớp số liệu** |
| **RQ3: Mô hình Embedding** | 207 bài báo, 615 câu hỏi, 5.207 chunks | nDCG@10, nDCG@4, Recall@20, MRR@10, P50 ms | `all-MiniLM-L6-v2` (Dense)<br/>`bm25` (Sparse) | `eval/results/thesis_embedding_benchmark.json`<br/>`eval/results/rq3_embedding_20261024_000029.json` | `backend/scripts/evaluation/run_rq3_embedding_benchmark.py`<br/>`eval/scripts/plot_chapter5_figures.py` | **100% Khớp số liệu** |
| **RQ4: Truy xuất lai (RRF)** | 160 bài báo, 487 câu hỏi | Recall@20, Hit@5 | Dense E5 đơn lẻ | `eval/prepared/expanded_160_hybrid_rrf_benchmark.json` | `backend/scripts/evaluate_expanded_hybrid_rrf.py` | **Khảo sát mở rộng (Định tính)** |
| **RQ5: Mô hình LLM cục bộ** | 16 câu hỏi kiểm chứng chuẩn | Answer F1, Faithfulness, Độ trễ P50 | `qwen2.5:0.5b` | `eval/results/rq5_llm_comparison_benchmark.json`<br/>`eval/results/THESIS_RQ5_LLM_REPORT.md` | `backend/scripts/evaluation/evaluate_rq5_llms.py` | **Khảo sát sơ bộ (Pilot, 16 Qs)** |
| **Đánh giá tích hợp toàn trình (E2E)** | Tổ hợp đa mắt xích đề xuất | E2E Faithfulness, E2E Latency | Cấu hình cơ sở Pipeline 1 | Chưa có tệp kết quả chạy toàn trình | Đề xuất tại Bảng 3.6 Chương 3 | **Chưa đánh giá (Future Work)** |

---

## 3. Các Luận điểm Thống kê Được Chứng minh và Các Sai số Đã Hiệu chỉnh

### 3.1. Các kết luận thống kê được hỗ trợ đầy đủ bởi dữ liệu
1. **Sự vượt trội của phân mảnh phân cấp (RQ2):** 
   - `hierarchical` Small-to-Big đạt $\text{nDCG@10} = 0,6880$, tạo mức tăng $\Delta = +0,1225$ với khoảng tin cậy 95% Bootstrap $[+0,0553; +0,1821]$ và $p = 0,0010^*$. Kết luận có ý nghĩa thống kê vượt trội so với `fixed_size`.
2. **Sự suy giảm có ý nghĩa thống kê của phân đoạn ngữ nghĩa (RQ2):** 
   - `semantic` chunking chỉ đạt $\text{nDCG@10} = 0,4856$ ($\Delta = -0,0798$, khoảng tin cậy $[-0,1323; -0,0275]$, $p = 0,0050^*$). Khẳng định phân đoạn ngữ nghĩa gây suy giảm chất lượng truy xuất trên văn bản khoa học.
3. **Cắt cụt ngữ cảnh nghiêm trọng của phân đoạn đề mục thô (RQ2):** 
   - Đo đạc chính xác 23,70% số phân đoạn của `section` vượt quá 512 subwords, dẫn đến việc mất mát thông tin âm thầm khi mã hóa vector.
4. **Sự vượt trội của ModernBERT và E5-Small-v2 (RQ3):** 
   - `modernbert-embed-base` đạt $\text{nDCG@10} = 0,5872$ ($\Delta = +0,0846, p = 0,0010^*$) và `e5-small-v2` đạt $0,5522$ ($\Delta = +0,0497, p = 0,0010^*$). Cả hai đều vượt qua kiểm định hiệu chỉnh so sánh đa biến Holm-Bonferroni ở mức $\alpha = 0,05$.
5. **Minh định bản chất cột Trị số $p$ và kiểm chứng FWER bằng Holm-Bonferroni:**
   - *Xác minh cột dữ liệu:* Toàn bộ các giá trị trong cột $p$ của Bảng 5.1, 5.2 và 5.3 là **trị số $p$ danh định ($p_{\text{raw}}$)** tính từ $2.000$ mẫu bootstrap độc lập từng cặp với baseline.
   - *Xác minh hiệu chỉnh FWER:* Khi áp dụng thuật toán hiệu chỉnh tuần tự Holm-Bonferroni (Step-down procedure) ở mức $\alpha = 0,05$ trên toàn bộ các phép so sánh độc lập:
     - **RQ1 ($m=4$):** Duy nhất `pdfplumber` có $p_{\text{raw}} = 0,0010 \le \alpha_1 = 0,0125 \rightarrow p_{\text{adj}} = 0,0040 < 0,05$ (Suy giảm có ý nghĩa\*). Các công cụ khác có $p_{\text{adj}} = 1,0000$.
     - **RQ2 ($m=7$):** `hierarchical` ($p_{\text{adj}} = 0,0070$), `hierarchical_child` ($p_{\text{adj}} = 0,0120$) và `semantic` ($p_{\text{adj}} = 0,0250$) đều có $p_{\text{adj}} < 0,05$ (Bảo toàn ý nghĩa thống kê\*). Các chiến lược khác có $p_{\text{adj}} \ge 0,8516$.
     - **RQ3 ($m=10$):** 5 mô hình `modernbert` ($p_{\text{adj}} = 0,0100$), `e5-small-v2` ($p_{\text{adj}} = 0,0100$), `arctic-embed-m-v1.5` ($p_{\text{adj}} = 0,0100$), `gte-small` ($p_{\text{adj}} = 0,0100$) và `arctic-embed-s` ($p_{\text{adj}} = 0,0120$) đều có $p_{\text{adj}} < 0,05$ (Bảo toàn ý nghĩa thống kê\*). Riêng `bge-small-en-v1.5` có $p_{\text{raw}} = 0,0830 > \alpha_6 = 0,0100 \rightarrow p_{\text{adj}} = 0,4150$, dừng quy trình và không có ý nghĩa thống kê.
   - *Khẳng định:* Các dấu sao ($^*$) trong các bảng kết quả hoàn toàn hợp lệ, trung thực và được bảo đảm nghiêm ngặt bởi quy trình hiệu chỉnh tuần tự Holm-Bonferroni.

### 3.2. Các sai số học thuật nghiêm trọng trong tài liệu cũ đã được đính chính
1. **Bác bỏ khẳng định sai về BGE-Small-v1.5:**
   - *Tài liệu cũ / Bản thảo sơ bộ:* Từng ghi nhận BGE-Small đạt $p = 0,0002^*$ vượt trội so với MiniLM.
   - *Kiểm toán thực tế:* Tệp dữ liệu gốc `thesis_embedding_benchmark.json` ghi nhận chính xác $p = 0,0830$ với khoảng tin cậy 95% $[-0,0027; +0,0393]$ bao trùm giá trị 0. BGE-Small **không có ý nghĩa thống kê vượt trội so với MiniLM** ở mức $\alpha = 0,05$. Sai số này đã được đính chính hoàn toàn trong Chương 5.
2. **Loại bỏ các thông số thông lượng phóng đại (Fabricated Throughput):**
   - *Tài liệu cũ:* Ghi nhận thông lượng CPU lên tới 198,4 và 315,2 chunks/s (số liệu suy đoán không có căn cứ).
   - *Kiểm toán thực tế:* Đo lường thực tế trên CPU AMD Ryzen 5 5600 ghi nhận thông lượng chính xác: MiniLM đạt 19,0 chunks/s, E5-Small đạt 6,5 chunks/s, ModernBERT đạt 1,8 chunks/s. Số liệu thực nghiệm đã được cập nhật chuẩn xác vào Bảng 5.3.
3. **Bản chất của chỉ số Char-Match trong RQ1:**
   - Được làm rõ là tỷ lệ bao phủ ký tự tương đối so với mã nguồn LaTeX thô chưa biên dịch (32–33%), không phải tỷ lệ mất mát nội dung (Character Error Rate).

---

## 4. Các So sánh Chưa Thể Kết luận và Thực nghiệm Cần Tiếp tục

1. **Sai khác giữa các bộ bóc tách PDF hàng đầu (RQ1):**
   - Sự khác biệt về nDCG@10 giữa `pymupdf_plain` (0,5274), `pypdf` (0,5174), `pdfminer.six` (0,5131) và `pymupdf_layout` (0,5100) đều có $p > 0,50$. Do đó, dữ liệu hiện tại **chưa thể kết luận công cụ nào vượt trội hơn về chất lượng ngữ nghĩa thuần túy**; quyết định chọn `pymupdf_layout` hoàn toàn dựa trên tiêu chí kỹ thuật về khả năng phân tích tiêu đề mục (Heading F1 = 48,01%) và tốc độ (26 ms/trang).
2. **Hiệu quả của Arctic-Embed-M-v2.0:**
   - Mô hình này ghi nhận điểm số thấp bất thường (0,4809). Cần thực nghiệm thêm với tiền tố chuẩn hóa `"query: "` thay vì tiền tố dài để xác định xem sự suy giảm là do bản chất mô hình hay do sự không tương thích tiền tố.
3. **Thực nghiệm toàn trình (End-to-End Evaluation):**
   - Đánh giá câu trả lời cuối cùng của LLM trên toàn bộ 615 câu hỏi kết hợp đồng thời cả 3 mắt xích vẫn là công việc cần tiếp tục triển khai để có kết luận toàn diện về hệ thống RAG.

---

## 5. Bảng Kiểm Tra Dành Cho Tác Giả Luận Văn (Author's Final Checklist)

Trước khi đóng quyển luận văn và nộp cho hội đồng chấm, tác giả cần kiểm tra và xác nhận các mục sau:

- [x] **Số thứ tự chương:** Đã thống nhất tiêu đề là **CHƯƠNG 5. KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN**, khớp với cấu trúc 6 chương trong đề cương Chương 1.
- [x] **Hình ảnh đồ thị minh họa:** Cả 5 tệp hình ảnh đồ thị chất lượng cao đã được tạo lập thành công tại `docs/figures/` và `eval/results/figures/`:
  - `fig5_1_rq1_ndcg10.png` (Hình 5.1: nDCG@10 RQ1)
  - `fig5_2_rq1_latency.png` (Hình 5.2: Tốc độ trích xuất RQ1)
  - `fig5_3_rq2_chunking_ndcg10.png` (Hình 5.3: Biểu đồ Dot-and-Whisker RQ2 kèm phân tích độ nhạy)
  - `fig5_4_rq3_embedding_ndcg10.png` (Hình 5.4: Xếp hạng nDCG@10 11 mô hình RQ3)
  - `fig5_5_rq3_quality_cost.png` (Hình 5.5: Đường biên Pareto Chất lượng vs Độ trễ RQ3)
- [x] **Khớp nối số liệu giữa bảng và đồ thị:** Mọi giá trị điểm trung bình và khoảng tin cậy trên các đồ thị đều được đối soát khớp 100% với các Bảng 5.1, 5.2 và 5.3.
- [x] **Khả năng tái lập:** Kịch bản tạo hình ảnh `eval/scripts/plot_chapter5_figures.py` chạy thành công không có lỗi, đọc trực tiếp từ các tệp JSON kết quả mà không hardcode dữ liệu.
- [x] **Tính trung thực học thuật:** Tuyệt đối không tự ý bịa đặt kết quả cho RQ4, RQ5 (quy mô lớn) và RQ6; các nội dung chưa hoàn tất đều được nêu rõ là hướng nghiên cứu tương lai.
