# Hướng Dẫn Tái Lập Bảng Số Liệu và Đồ Thị — Chương 5

Thư mục này chứa toàn bộ các tạo phẩm số liệu, bảng kết quả định dạng CSV, đồ thị chất lượng cao và kịch bản tái lập cho **CHƯƠNG 5: KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN**.

---

## 1. Cấu Trúc Thư Mục

```text
reports/chapter5/
├── CHAPTER5.md                       # Bản thảo đầy đủ Chương 5 bằng tiếng Việt học thuật
├── EVIDENCE_AUDIT.md                 # Biên bản kiểm toán đối soát nguồn dữ liệu gốc
├── TRACEABILITY_MAP.md               # Bản đồ truy vết số liệu chi tiết tới từng trường JSON
├── README.md                         # Hướng dẫn tái lập quy trình (tệp này)
├── scripts/
│   └── generate_tables_and_plots.py  # Kịch bản Python đọc JSON sinh bảng CSV và hình ảnh PNG
├── tables/
│   ├── table_5_1_rq1_extraction.csv  # Bảng 5.1: Kết quả bóc tách PDF (RQ1)
│   ├── table_5_2_rq2_chunking.csv    # Bảng 5.2: So sánh 8 chiến lược phân mảnh (RQ2)
│   ├── table_5_3_rq3_embedding.csv   # Bảng 5.3: Bảng xếp hạng 11 mô hình embedding (RQ3)
│   └── table_5_4_summary_rq1_rq3.csv # Bảng 5.4: Bảng tổng hợp đối sánh RQ1–RQ3
└── figures/
    ├── fig5_1_rq1_ndcg10.png         # Hình 5.1: nDCG@10 RQ1 (Mean ± 95% CI)
    ├── fig5_2_rq1_latency.png        # Hình 5.2: Tốc độ trích xuất PDF ms/trang (RQ1)
    ├── fig5_3_rq2_chunking_ndcg10.png# Hình 5.3: Biểu đồ Dot-and-Whisker nDCG@10 (RQ2)
    ├── fig5_4_rq3_embedding_ndcg10.png# Hình 5.4: Xếp hạng nDCG@10 11 mô hình (RQ3)
    └── fig5_5_rq3_quality_cost.png   # Hình 5.5: Không gian Pareto Chất lượng vs Độ trễ (RQ3)
```

---

## 2. Nguồn Dữ Liệu Thực Nghiệm Gốc (Authoritative Artifacts)

Kịch bản đọc trực tiếp dữ liệu từ các tệp kết quả JSON đã được kiểm toán và lưu trữ cố định tại `eval/results/`:
1. **RQ1:** `eval/results/rq1_extraction_20261024_000639.json` (47 bài báo QASPER Dev, 5 công cụ bóc tách + GROBID offline).
2. **RQ2:** `eval/results/rq2_chunking_20261024_013443.json` (47 bài báo, 127 câu hỏi, 8 chiến lược, context budget 1.600 tokens).
3. **RQ3:** `eval/results/thesis_embedding_benchmark.json` (207 bài báo, 615 câu hỏi, 5.207 chunks, 11 mô hình embedding + BM25).

---

## 3. Lệnh Tái Lập Sạch (Clean Execution)

Để tạo lập lại toàn bộ các bảng CSV và hình ảnh đồ thị từ một lời gọi sạch:

```powershell
# Từ thư mục gốc của repository (c:\DACNTT)
.\backend\venv\Scripts\python.exe reports/chapter5/scripts/generate_tables_and_plots.py
```

### Kết Quả Đầu Ra Khi Thực Thi
- 4 tệp bảng dữ liệu định dạng `.csv` được xuất vào `reports/chapter5/tables/`.
- 5 tệp hình ảnh đồ thị độ phân giải cao (300 DPI, phông chữ khoa học) được xuất đồng thời vào:
  - `reports/chapter5/figures/`
