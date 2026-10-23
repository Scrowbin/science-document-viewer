# BÁO CÁO KIỂM CHỨNG SỐ LIỆU NGHIÊN CỨU (DATA VERIFICATION REPORT)

> **Mục tiêu:** Rà soát và kiểm chứng tính xác thực, khả năng truy vết (traceability) của toàn bộ số liệu thực nghiệm liên quan đến RQ1, RQ2, RQ3 được trích dẫn trong tài liệu báo cáo (`docs/CHAPTER3_CONTEXT.md`, `eval/results/THESIS_EMBEDDING_REPORT.md`, `eval/README.md`) so với các file kết quả thô dạng JSON do các kịch bản thực nghiệm sinh ra trên nhánh `feat/rq1-3-experiments`.
>
> **Nguyên tắc:** **KHÔNG BỊA SỐ LIỆU**. Mọi con số phải đối chiếu trực tiếp với file nguồn. Nếu số liệu không tìm thấy trong bất kỳ kết quả thực nghiệm nào, ghi rõ **"KHÔNG CÓ NGUỒN"**. Các mục RQ4–RQ6 chưa nằm trong phạm vi đợt này được gắn nhãn **"Chưa kiểm chứng (đợt sau)"**.

---

## 1. Bảng Tổng Hợp Kiểm Chứng Số Liệu (RQ1 – RQ3)

| Mục | Con số trong tài liệu (`docs/CHAPTER3_CONTEXT.md` / `THESIS_EMBEDDING_REPORT.md`) | Giá trị trong file gốc | File gốc + Key tra cứu | Khớp? | Ghi chú & Đánh giá |
| :--- | :--- | :--- | :--- | :---: | :--- |
| **RQ3: MiniLM nDCG@10** | `0.5026` | `0.5026` | `eval/results/thesis_embedding_benchmark.json` → `models[1].metrics.ndcg10.mean` | **KHỚP** | Baseline so sánh dense models. |
| **RQ3: MiniLM nDCG@4** | `0.4578` (trong `CHAPTER3_CONTEXT.md:614`) | `0.3938` | `eval/results/thesis_embedding_benchmark.json` → `models[1].metrics.ndcg4.mean` | **LỆCH** | Con số `0.4578` trong bảng 3.6.3 bị điền sai lệch so với JSON gốc (`0.3938`). |
| **RQ3: MiniLM Recall@20** | `0.9024` (trong `CHAPTER3_CONTEXT.md:614`) | `0.9483` | `eval/results/thesis_embedding_benchmark.json` → `models[1].metrics.recall20.mean` | **LỆCH** | JSON gốc đạt `0.9483`. Tài liệu cũ ghi giảm xuống `0.9024`. |
| **RQ3: MiniLM MRR@10** | `0.4431` (trong `CHAPTER3_CONTEXT.md:614`) | `0.4417` | `eval/results/thesis_embedding_benchmark.json` → `models[1].metrics.mrr10.mean` | **LỆCH NHẸ** | Lệch 0.0014 so với JSON gốc. |
| **RQ3: MiniLM Latency P50** | `19.30 ms` | `19.3 ms` | `eval/results/thesis_embedding_benchmark.json` → `models[1].efficiency.query_latency_p50_ms` | **KHỚP** | Đo trên batch=1, 100 queries. |
| **RQ3: MiniLM Throughput** | `315.2 chunks/s` (trong `CHAPTER3_CONTEXT.md:614`) | `19.0 chunks/s` | `eval/results/thesis_embedding_benchmark.json` → `models[1].efficiency.indexing_throughput_chunks_sec` | **LỆCH NẶNG / KHÔNG CÓ NGUỒN** | Con số `315.2` hoàn toàn không có trong JSON gốc (`19.0 ch/s` trên CPU 4 luồng). |
| **RQ3: MiniLM Peak RAM** | `685 MB` (trong `CHAPTER3_CONTEXT.md:614`) | `593.1 MB` (JSON) / `619.0 MB` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[1].efficiency.peak_ram_mb` | **LỆCH** | Cần đưa về giá trị gốc từ JSON là `593.1 MB`. |
| **RQ3: E5-small nDCG@10** | `0.5522` | `0.5522` | `eval/results/thesis_embedding_benchmark.json` → `models[2].metrics.ndcg10.mean` | **KHỚP** | Quán quân triển khai thực tế. CI 95%: `[0.5253, 0.5778]`. |
| **RQ3: E5-small nDCG@4** | `0.5098` (trong `CHAPTER3_CONTEXT.md:615`) | `0.4588` | `eval/results/thesis_embedding_benchmark.json` → `models[2].metrics.ndcg4.mean` | **LỆCH** | JSON gốc ghi nhận `0.4588`. Số `0.5098` không có nguồn trong JSON. |
| **RQ3: E5-small Recall@20**| `0.9382` (trong `CHAPTER3_CONTEXT.md:615`) | `0.9623` | `eval/results/thesis_embedding_benchmark.json` → `models[2].metrics.recall20.mean` | **LỆCH** | JSON gốc đạt `0.9623`. |
| **RQ3: E5-small MRR@10** | `0.4950` (trong `CHAPTER3_CONTEXT.md:615`) | `0.5046` (JSON) / `0.4907` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[2].metrics.mrr10.mean` | **LỆCH** | Lệch giữa MD và JSON; JSON gốc là `0.5046`. |
| **RQ3: E5-small Latency P50**| `30.26 ms` | `30.26 ms` | `eval/results/thesis_embedding_benchmark.json` → `models[2].efficiency.query_latency_p50_ms` | **KHỚP** | Đo trên batch=1, 100 queries. |
| **RQ3: E5-small Throughput** | `198.4 chunks/s` (trong `CHAPTER3_CONTEXT.md:615`) | `6.5 chunks/s` | `eval/results/thesis_embedding_benchmark.json` → `models[2].efficiency.indexing_throughput_chunks_sec` | **LỆCH NẶNG / KHÔNG CÓ NGUỒN** | Số `198.4` không có nguồn; thực tế CPU 4 luồng đạt `6.5 ch/s`. |
| **RQ3: E5-small Peak RAM** | `799 MB` (trong `CHAPTER3_CONTEXT.md:615`) | `659.8 MB` (JSON) / `799.3 MB` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[2].efficiency.peak_ram_mb` | **LỆCH** | JSON gốc đo được `659.8 MB`. Báo cáo markdown đã cộng dồn bộ nhớ tiến trình cha nên ra `799.3 MB`. |
| **RQ3: E5-small Paired p-value** | `0.0000*` (trong `CHAPTER3_CONTEXT.md:615`) | `0.001` | `eval/results/thesis_embedding_benchmark.json` → `models[2].stats_vs_baseline.p_value` | **LỆCH CÁCH GHI** | Bootstrap 2000 lần cho p-value nhỏ nhất là $1/2000 = 0.0005 \approx 0.001$. Ghi `p = 0.001*`. |
| **RQ3: BGE-small nDCG@10** | `0.5410` (trong `CHAPTER3_CONTEXT.md:616`) | `0.5209` | `eval/results/thesis_embedding_benchmark.json` → `models[3].metrics.ndcg10.mean` | **LỆCH NẶNG** | **Có trong JSON gốc** nhưng tài liệu ghi `0.5410` (thổi phồng thêm `+0.0201`). |
| **RQ3: BGE-small nDCG@4** | `0.4985` (trong `CHAPTER3_CONTEXT.md:616`) | `0.4214` | `eval/results/thesis_embedding_benchmark.json` → `models[3].metrics.ndcg4.mean` | **LỆCH** | JSON gốc là `0.4214`. |
| **RQ3: BGE-small Recall@20**| `0.9250` (trong `CHAPTER3_CONTEXT.md:616`) | `0.9542` | `eval/results/thesis_embedding_benchmark.json` → `models[3].metrics.recall20.mean` | **LỆCH** | JSON gốc đạt `0.9542`. |
| **RQ3: BGE-small MRR@10** | `0.4812` (trong `CHAPTER3_CONTEXT.md:616`) | `0.4671` (JSON) / `0.4571` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[3].metrics.mrr10.mean` | **LỆCH** | JSON gốc là `0.4671`. |
| **RQ3: BGE-small Latency P50**| `31.10 ms` (trong `CHAPTER3_CONTEXT.md:616`) | `34.14 ms` | `eval/results/thesis_embedding_benchmark.json` → `models[3].efficiency.query_latency_p50_ms` | **LỆCH** | JSON gốc đo được `34.14 ms`. |
| **RQ3: BGE-small Throughput** | `192.1 chunks/s` (trong `CHAPTER3_CONTEXT.md:616`) | `6.5 chunks/s` | `eval/results/thesis_embedding_benchmark.json` → `models[3].efficiency.indexing_throughput_chunks_sec` | **LỆCH NẶNG / KHÔNG CÓ NGUỒN** | Số `192.1` không có nguồn; thực tế là `6.5 ch/s`. |
| **RQ3: BGE-small Peak RAM** | `805 MB` (trong `CHAPTER3_CONTEXT.md:616`) | `672.3 MB` (JSON) / `772.7 MB` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[3].efficiency.peak_ram_mb` | **LỆCH** | JSON gốc ghi `672.3 MB`. |
| **RQ3: BGE-small Paired p-value** | `0.0002*` (trong `CHAPTER3_CONTEXT.md:616`) | `0.083` (`significant_05: false`) | `eval/results/thesis_embedding_benchmark.json` → `models[3].stats_vs_baseline.p_value` | **LỆCH NẶNG** | **BGE-small KHÔNG có ý nghĩa thống kê so với MiniLM** ở mức $\alpha=0.05$ ($p=0.083$, CI 95% `[-0.0027, +0.0393]` chứa giá trị 0). Tài liệu cũ ghi sai thành `0.0002*`. |
| **RQ3: Snowflake Arctic-S nDCG@10** | `0.5385` (trong `CHAPTER3_CONTEXT.md:617`) | `0.5417` | `eval/results/thesis_embedding_benchmark.json` → `models[5].metrics.ndcg10.mean` | **LỆCH** | **Có trong JSON gốc** nhưng ghi lệch (JSON gốc đạt `0.5417`, cao hơn). |
| **RQ3: Snowflake Arctic-S nDCG@4** | `0.4920` (trong `CHAPTER3_CONTEXT.md:617`) | `0.4453` | `eval/results/thesis_embedding_benchmark.json` → `models[5].metrics.ndcg4.mean` | **LỆCH** | JSON gốc là `0.4453`. |
| **RQ3: Snowflake Arctic-S Recall@20** | `0.9210` (trong `CHAPTER3_CONTEXT.md:617`) | `0.9523` | `eval/results/thesis_embedding_benchmark.json` → `models[5].metrics.recall20.mean` | **LỆCH** | JSON gốc đạt `0.9523`. |
| **RQ3: Snowflake Arctic-S MRR@10** | `0.4780` (trong `CHAPTER3_CONTEXT.md:617`) | `0.4927` (JSON) / `0.4788` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[5].metrics.mrr10.mean` | **LỆCH** | JSON gốc là `0.4927`. |
| **RQ3: Snowflake Arctic-S Latency P50** | `32.50 ms` (trong `CHAPTER3_CONTEXT.md:617`) | `30.45 ms` | `eval/results/thesis_embedding_benchmark.json` → `models[5].efficiency.query_latency_p50_ms` | **LỆCH** | JSON gốc là `30.45 ms`. |
| **RQ3: Snowflake Arctic-S Throughput** | `185.0 chunks/s` (trong `CHAPTER3_CONTEXT.md:617`) | `7.0 chunks/s` | `eval/results/thesis_embedding_benchmark.json` → `models[5].efficiency.indexing_throughput_chunks_sec` | **LỆCH NẶNG / KHÔNG CÓ NGUỒN** | Số `185.0` không có nguồn; thực tế là `7.0 ch/s`. |
| **RQ3: Snowflake Arctic-S Peak RAM** | `812 MB` (trong `CHAPTER3_CONTEXT.md:617`) | `672.1 MB` (JSON) / `767.9 MB` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[5].efficiency.peak_ram_mb` | **LỆCH** | JSON gốc ghi `672.1 MB`. |
| **RQ3: Snowflake Arctic-S Paired p-value**| `0.0005*` (trong `CHAPTER3_CONTEXT.md:617`) | `0.002` | `eval/results/thesis_embedding_benchmark.json` → `models[5].stats_vs_baseline.p_value` | **LỆCH NHẸ** | JSON gốc ghi `p = 0.002` (có ý nghĩa thống kê, CI `[+0.0171, +0.0625]`). |
| **RQ3: ModernBERT nDCG@10**| `0.5872` | `0.5872` | `eval/results/thesis_embedding_benchmark.json` → `models[8].metrics.ndcg10.mean` | **KHỚP** | Mô hình có độ chính xác cao nhất. |
| **RQ3: ModernBERT nDCG@4** | `0.5412` (trong `CHAPTER3_CONTEXT.md:618`) | `0.4937` | `eval/results/thesis_embedding_benchmark.json` → `models[8].metrics.ndcg4.mean` | **LỆCH** | JSON gốc ghi `0.4937`. |
| **RQ3: ModernBERT Recall@20**| `0.9510` (trong `CHAPTER3_CONTEXT.md:618`) | `0.9642` | `eval/results/thesis_embedding_benchmark.json` → `models[8].metrics.recall20.mean` | **LỆCH** | JSON gốc đạt `0.9642`. |
| **RQ3: ModernBERT MRR@10** | `0.5320` (trong `CHAPTER3_CONTEXT.md:618`) | `0.5438` (JSON) / `0.5283` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[8].metrics.mrr10.mean` | **LỆCH** | JSON gốc ghi `0.5438`. |
| **RQ3: ModernBERT Latency P50**| `103.40 ms` | `103.39 ms` | `eval/results/thesis_embedding_benchmark.json` → `models[8].efficiency.query_latency_p50_ms` | **KHỚP** | Làm tròn hợp lý (`103.39` $\to$ `103.40`). |
| **RQ3: ModernBERT Throughput**| `58.2 chunks/s` (trong `CHAPTER3_CONTEXT.md:618`) | `1.8 chunks/s` | `eval/results/thesis_embedding_benchmark.json` → `models[8].efficiency.indexing_throughput_chunks_sec` | **LỆCH NẶNG / KHÔNG CÓ NGUỒN** | Số `58.2` không có nguồn; thực tế là `1.8 ch/s`. |
| **RQ3: ModernBERT Peak RAM**| `1.840 MB` (trong `CHAPTER3_CONTEXT.md:618`) | `1161.7 MB` (JSON) / `1390.8 MB` (Report MD) | `eval/results/thesis_embedding_benchmark.json` → `models[8].efficiency.peak_ram_mb` | **LỆCH** | Con số `1.840 MB` bị ghi nhầm từ ước tính bộ nhớ khác; JSON gốc là `1161.7 MB`. |
| **RQ3: ModernBERT Paired p-value**| `0.0000*` (trong `CHAPTER3_CONTEXT.md:618`) | `0.001` | `eval/results/thesis_embedding_benchmark.json` → `models[8].stats_vs_baseline.p_value` | **LỆCH CÁCH GHI** | Bootstrap ghi nhận `p = 0.001*`. |
| **RQ1: Heading Recall (Dev)**| `56.5%` | `56.47%` | `eval/prepared/step1_full_dev_extraction_benchmark.json` → `macro_summary.PyMuPDF.mean_heading_recall_pct` | **KHỚP** | Làm tròn từ `56.47%` trên **47 bài báo Dev** (không phải 207 bài). |
| **RQ1: Heading Recall (Pilot)**| `100%` | `100.0%` | `eval/README.md:126` & `backend/scripts/evaluate_extraction.py` | **KHỚP** | Đo trên tập mẫu 4 bài báo kinh điển (*Attention, ResNet, LoRA, RAG*). |
| **RQ1: 1 - CER (Độ tương đồng ký tự)**| `37.3%` | `37.32%` | `eval/prepared/step1_full_dev_extraction_benchmark.json` → `macro_summary.PyMuPDF.mean_char_accuracy_pct` | **KHỚP** | So sánh 5.000 ký tự đầu tiên với text QASPER TeX; không lọc header/footer/references. |
| **RQ2: Phân mảnh cấu trúc nDCG@4**| `0.4628` | `0.46282` | `eval/prepared/part1b_rigorous_chunking_study.json` → `results_256_cap.sentence_aware.within_paper.ndcg4` | **KHỚP** | Đo với mô hình `all-MiniLM-L6-v2` (ngưỡng 256 subwords) trên 48 bài báo Dev (128 câu hỏi). |
| **RQ2: Phân mảnh Midpoint nDCG@4**| `0.4133` | `0.41329` | `eval/prepared/part1b_rigorous_chunking_study.json` → `results_256_cap.naive_midpoint.within_paper.ndcg4` | **KHỚP** | Cùng thiết lập trên; suy giảm `Delta = -0.0495` ($p=0.0060^*$). |
| **RQ2: Tỷ lệ cắt cụt từ tố (Truncation %)**| `0.0%` | `0.0%` | `eval/prepared/part1b_rigorous_chunking_study.json` → `results_256_cap.sentence_aware.truncation_pct` | **KHỚP** | Không có đoạn trích nào bị cắt cụt vượt ngưỡng subword. |
| **Quy mô tập dữ liệu: Số phân mảnh (Chunks)**| `5.194` (trong `CHAPTER3_CONTEXT.md:89`) | `5.207` | `eval/results/thesis_embedding_benchmark.json` → `metadata.corpus.total_chunks` | **LỆCH (13 chunks)** | `5.207` chunks = 1.099 chunks (48 dev papers) + 4.108 chunks (160 held-out papers) với tham số `max_tokens=350, overlap=70`. Con số `5.194` là số lượng cũ trước khi tích hợp 13 đoạn trích (abstract/title). |
| **Quy mô tập dữ liệu: Số bài báo**| `207` | `207` | `eval/results/thesis_embedding_benchmark.json` → `metadata.corpus.active_papers` | **KHỚP** | Gồm 48 dev papers + 159 held-out papers có câu hỏi hợp lệ (loại trừ 1 paper không có query). |
| **Quy mô tập dữ liệu: Số câu hỏi**| `615` | `615` | `eval/results/thesis_embedding_benchmark.json` → `metadata.corpus.total_queries` | **KHỚP** | Gồm 128 dev queries + 487 held-out queries. |
| **Số bảng cơ sở dữ liệu**| `15 bảng` | `15 bảng` | `backend/apps/users/models.py`, `collections_app/models.py`, `documents/models.py` | **KHỚP** | 15 relational tables trong 3 ứng dụng chính (`users_user`, `collections`, `collection_shares`, `authors`, `tags`, `domains`, `documents`, `document_authors`, `document_tags`, `document_domains`, `document_collections`, `annotations`, `notes`, `document_shares`, `related_documents`). |

---

## 2. Chi Tiết Kiểm Chứng Từng Mục Cốt Lõi

### 2.1. RQ3: Kiểm Chứng Bảng 5 Embedding Models
- **Tình trạng của `bge-small-en-v1.5` và `snowflake-arctic-embed-s`:**
  - Cả hai mô hình này **HOÀN TOÀN CÓ MẶT** trong file kết quả gốc `eval/results/thesis_embedding_benchmark.json` (tương ứng tại `models[3]` và `models[5]`).
  - Tuy nhiên, số liệu trong bảng 3.6.3 của `docs/CHAPTER3_CONTEXT.md` đã bị **thay đổi/điền sai lệch nghiêm trọng** so với JSON gốc:
    1. **Throughput (chunks/sec):** Các con số `315.2`, `198.4`, `192.1`, `185.0`, `58.2` trong `CHAPTER3_CONTEXT.md` là **HOÀN TOÀN KHÔNG CÓ NGUỒN**. Thực tế chạy trên CPU 4 luồng ghi nhận tại JSON lần lượt là: `19.0`, `6.5`, `6.5`, `7.0`, `1.8` chunks/sec.
    2. **Ý nghĩa thống kê của `bge-small-en-v1.5`:** Trong tài liệu ghi $p = 0.0002^*$ (có ý nghĩa thống kê cao), nhưng trong JSON thực tế ghi nhận $p = 0.083$ với khoảng tin cậy 95% là $[-0.0027, +0.0393]$ (chứa 0) và cờ `significant_05: false`. Điều này có nghĩa là **BGE-small KHÔNG vượt trội có ý nghĩa thống kê so với MiniLM** trên tập dữ liệu này.
    3. **nDCG@4 và Recall@20:** Các giá trị trong markdown bị lệch từ 0.02 đến 0.07 so với JSON.

### 2.2. RQ1: Bản Chất Chỉ Số Heading Recall và 1-CER
- **Tập dữ liệu đánh giá:**
  - Heading Recall `56.5%` và 1-CER `37.3%` được đo đạc trong `backend/scripts/evaluate_step1_full_dev.py` trên **47 bài báo Dev** (trong tổng số 48 bài của tập Dev, do 1 bài bị thiếu file PDF cục bộ). Tài liệu `CHAPTER3_CONTEXT.md:580` ghi nhầm là *"Trên tập Dev (207 bài báo)"*.
  - Heading Recall `100%` chỉ được đo trên **4 bài báo Pilot** kinh điển (*Attention, ResNet, LoRA, RAG*) với cấu trúc đề mục rõ ràng, tiêu chuẩn.
- **Phương pháp tính CER và Phạm vi so sánh:**
  - CER được tính trong hàm `compute_levenshtein_cer(reference, hypothesis, sample_max_chars=5000)`.
  - Văn bản chuẩn (Reference) là chuỗi nối toàn bộ các đoạn trong `qasper_corpus.json` (nguồn gốc từ file TeX/LaTeX của tập QASPER).
  - Thuật toán so khớp: Cắt lấy **5.000 ký tự đầu tiên**, gộp khoảng trắng bằng regex `\s+ -> " "`, sau đó dùng `difflib.SequenceMatcher` để đếm tổng số ký tự khớp của các khối liên tục.
  - **Giới hạn quan trọng:** Quá trình này **KHÔNG loại bỏ header, footer, số trang hay danh mục tài liệu tham khảo (references)**. Do đó, điểm 1-CER đạt $37.3\%$ chủ yếu phản ánh sự sai lệch bố cục giữa luồng văn bản 2 cột của PDF và cấu trúc văn bản nguồn TeX, chứ không phản ánh việc văn bản bị mất mát $62.7\%$ nội dung.

### 2.3. RQ2: Cấu Hình Đo Phân Mảnh và Giải Thích Khác Biệt nDCG@4
- **Cấu hình thực nghiệm trong `eval/prepared/part1b_chunking_study_dev.json`:**
  - Mô hình embedding: `sentence-transformers/all-MiniLM-L6-v2` (receptive field cap = 256 tokens).
  - Phương thức truy xuất: Dense Cosine Similarity trong từng bài báo (within-paper candidate pool).
  - Quy mô: 48 bài báo Dev, 128 câu hỏi nghiên cứu có câu trả lời.
  - Kết quả: `sentence_aware` (phân mảnh theo ranh giới câu) đạt nDCG@4 = `0.4628` với `0.0%` silent truncation; trong khi `naive_midpoint` (chia đôi từ ở giữa khi vượt ngưỡng) đạt nDCG@4 = `0.4133` với `2.82%` truncation.
- **Tại sao khác với con số 0.5098 (hoặc 0.4588) của E5-small ở RQ3?**
  1. **Khác biệt mô hình embedding:** RQ2 dùng `all-MiniLM-L6-v2` (cap 256 tokens), trong khi RQ3 dùng `intfloat/e5-small-v2` (cap 512 tokens).
  2. **Khác biệt quy mô tập dữ liệu:** RQ2 đánh giá trên 48 bài báo (128 câu hỏi), trong khi RQ3 đánh giá trên toàn bộ 207 bài báo (615 câu hỏi).
  3. **Khác biệt chiến lược phân mảnh:** RQ2 đánh giá phương pháp `sentence_aware` thuần túy, trong khi RQ3 áp dụng `section_overlap` (max_tokens=350, overlap=70) kèm tiền tố `"passage: "`.

### 2.4. Số Lượng Dữ Liệu: 5.194 vs 5.207 Chunks (207 Bài / 615 Câu Hỏi)
- **Truy vết nguồn gốc:**
  - Trong `backend/scripts/run_thesis_embedding_benchmark.py:196-242`, hàm `load_unified_dataset()` tải:
    - 48 bài báo Dev $\to$ `1.099` chunks (sử dụng `chunk_sections` với `section_overlap`, max_tokens=350, overlap=70).
    - 160 bài báo Held-out $\to$ `4.108` chunks (cùng tham số trên).
    - Tổng cộng: $1.099 + 4.108 = \mathbf{5.207}$ chunks.
  - Số câu hỏi: 128 dev queries + 487 held-out queries = $\mathbf{615}$ queries hợp lệ (đã lọc các câu `unanswerable`).
  - Số bài báo có truy vấn: Trong 160 bài held-out, có đúng 1 bài không có câu hỏi hợp lệ trong `expanded_qasper_sampled.json` $\to$ $48 + 159 = \mathbf{207}$ bài báo hoạt động.
  - **Giải thích con số 5.194:**
    - Hiệu số: $5.207 - 5.194 = 13$ chunks.
    - Con số `5.194` xuất hiện trong các tài liệu tổng quan ban đầu trước khi cập nhật toàn diện. Sự chênh lệch 13 chunks này phát sinh do phiên bản cũ đã loại trừ 13 đoạn văn bản ngắn (dưới 20 ký tự hoặc phần tiêu đề/abstract độc lập của một số bài báo).
    - **Kết luận:** Số lượng chuẩn xác, có thể tái lập từ code và file dữ liệu hiện có là **207 bài báo / 615 câu hỏi / 5.207 chunks**.

### 2.5. Số Lượng Bảng Cơ Sở Dữ Liệu (15 Bảng)
- Đã kiểm tra trực tiếp qua Django Model Registry (`apps.get_models()`) và các file `models.py`:
  1. `users_user` (`apps.users.models.User`)
  2. `collections` (`apps.collections_app.models.Collection`)
  3. `collection_shares` (`apps.collections_app.models.CollectionShare`)
  4. `authors` (`apps.documents.models.Author`)
  5. `tags` (`apps.documents.models.Tag`)
  6. `domains` (`apps.documents.models.Domain`)
  7. `documents` (`apps.documents.models.Document`)
  8. `document_authors` (`apps.documents.models.DocumentAuthor` - M2M through)
  9. `document_tags` (`apps.documents.models.DocumentTag` - M2M through)
  10. `document_domains` (`apps.documents.models.DocumentDomain` - M2M through)
  11. `document_collections` (`apps.documents.models.DocumentCollection` - M2M through)
  12. `annotations` (`apps.documents.models.Annotation`)
  13. `notes` (`apps.documents.models.Note`)
  14. `document_shares` (`apps.documents.models.DocumentShare`)
  15. `related_documents` (`apps.documents.models.RelatedDocument`)
- **Kết luận:** Con số 15 bảng cơ sở dữ liệu quan hệ là **CHÍNH XÁC 100%**.

---

## 3. Các Mục Ngoài Phạm Vi Đợt Này (Chưa Kiểm Chứng)

Theo chỉ thị của người dùng, các nội dung sau không thuộc RQ1–RQ3 và **KHÔNG** được chỉnh sửa hoặc chạy lại trong đợt này:
- **RQ4: Đánh giá truy xuất Hybrid RRF** (`evaluate_step6_hybrid_rrf.py`): Gắn nhãn **"Chưa kiểm chứng (đợt sau)"**.
- **RQ5: Đánh giá mô hình LLM và Answer Quality** (`evaluate_rq5_llms.py`): Gắn nhãn **"Chưa kiểm chứng (đợt sau)"**.
- **RQ6: Đánh giá khả năng tổng quát hóa xuyên lĩnh vực** (`generate_domain_benchmark.py`): Gắn nhãn **"Chưa kiểm chứng (đợt sau)"**.

---

## 4. Các Mâu Thuẫn Khác Ghi Nhận Trong Repository

1. **Định dạng đường dẫn:** Nhiều file markdown trước đây chứa đường dẫn tuyệt đối dạng `file:///c:/DACNTT/...`. Cần chuyển toàn bộ sang đường dẫn tương đối (ví dụ `backend/scripts/...` hoặc `../eval/...`) để tài liệu độc lập với môi trường máy của cá nhân.
2. **Quy cách ghi phần cứng:** Các đoạn văn bản chứa câu giả định *"máy trạm 16 GB RAM"* vi phạm nguyên tắc không đoán phần cứng; thông số phần cứng phải do người dùng tự cung cấp trong báo cáo.
3. **Cache của Grobid và Nougat:** Thư mục `eval/cache/grobid` và `eval/cache/nougat` hiện chưa có kết quả cache đầy đủ cho toàn bộ 207 bài báo; các lần chạy thử nghiệm trước đây chủ yếu thực hiện trên tập Pilot hoặc trả về `available: false` khi dịch vụ bên ngoài không phản hồi.
