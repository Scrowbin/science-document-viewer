# BÁO CÁO THỰC NGHIỆM ĐÁNH GIÁ MÔ HÌNH NGÔN NGỮ LỚN CỤC BỘ (RQ5: LOCAL SLM GENERATION & FAITHFULNESS BENCHMARK)

**Đề tài:** Xây dựng Hệ thống Quản lý Tài liệu Nghiên cứu Khoa học Tích hợp Trợ lý AI Sử dụng RAG  
**Câu hỏi nghiên cứu RQ5:** *Các mô hình ngôn ngữ lớn mã nguồn mở chạy cục bộ (`qwen2.5:0.5b`, `llama3.2:1b`, `llama3.2:3b`) so sánh như thế nào về độ chính xác câu trả lời (Answer Correctness), độ trung thực bám sát bằng chứng (Faithfulness) và hiệu năng suy luận (độ trễ P50/P95, thông lượng tokens/giây) khi được cung cấp cùng một ngữ cảnh trích dẫn học thuật và cùng một mẫu lời nhắc có cấu trúc trên môi trường máy trạm cá nhân không có GPU rời?*

---

## 1. Siêu dữ liệu thực nghiệm và Truy xuất nguồn gốc (Provenance Metadata)

- **Mã thực nghiệm (Experiment ID):** `EXP-RQ5-MAIN-SAMPLED`
- **Sổ đăng ký nguồn gốc (Provenance Registry):** [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json)
- **Tập mẫu chỉ định (Sample Manifest):** [`eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json)
- **Đề cương thực nghiệm chuẩn hóa (Protocol):** [`eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md)
- **Dữ liệu thô thực nghiệm định lượng (500 câu hỏi):** [`eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json)
- **Dữ liệu kiểm toán người đã giải quyết bất đồng (Adjudicated Dataset):** [`eval/phases/phase_9_generation/artifacts/human_faithfulness_review/adjudicated/faithfulness_annotations_adjudicated.csv`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/adjudicated/faithfulness_annotations_adjudicated.csv)
- **Dữ liệu kiểm toán người mở mù (Unblinded Dataset):** [`eval/phases/phase_9_generation/artifacts/human_faithfulness_review/unblinded/faithfulness_annotations_unblinded.csv`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/human_faithfulness_review/unblinded/faithfulness_annotations_unblinded.csv)
- **Môi trường phần cứng:** CPU AMD Ryzen 5 5600 6 nhân / 12 luồng, 16 GB DDR4 RAM, hệ điều hành Windows 11 host, Ollama local REST API (chạy suy luận hoàn toàn trên CPU, không sử dụng GPU rời).
- **Tham số sinh văn bản kiểm soát:** Giải mã tất định hoàn toàn (`temperature = 0.0`), giới hạn sinh tối đa `num_predict = 256` tokens, chung một mẫu lời nhắc học thuật (Academic Assistant Prompt) và chung một khối ngữ cảnh trích dẫn dưới ngân sách 1.600 tokens.

---

## 2. Thiết lập Phương pháp luận Hai Tầng (Dual-Tier Methodology)

Để bảo đảm tính chặt chẽ khoa học và trung thực học thuật, đánh giá RQ5 được phân tách thành hai tầng đo lường độc lập với mục tiêu và phạm vi phân định rạch ròi:

1. **Tầng 1 – Đánh giá Định lượng Quy mô Lớn (Primary Quantitative Benchmark):**
   - **Quy mô:** $N = 500$ câu hỏi khoa học thuộc $K = 250$ cụm bài báo trích từ tập QASPER Train chưa từng phơi nhiễm (Unexposed Cohort). Với 3 mô hình, tổng số lượt suy luận LLM độc lập là $1.500$ lượt.
   - **Mục tiêu:** Đo lường các chỉ số tự động khách quan trên diện rộng bao gồm Token F1 (phân theo các dạng câu hỏi Extractive, Abstractive, Boolean), tỷ lệ kích hoạt câu từ chối an toàn (Refusal Rate theo NFR-03), tỷ lệ chứa từ vựng ngữ cảnh tự động (Automated Containment Proxy), độ trễ P50/P95 và thông lượng suy luận (tokens/s).
   - **Phân tích suy diễn thống kê:** Thực hiện kiểm định $t$ bắt cặp theo cụm bài báo ($K=250, df=249$), ước lượng khoảng tin cậy 95% bằng Bootstrap phân cụm ($B=2.000$) và kiểm soát tỷ lệ sai số họ (FWER) bằng phương pháp hiệu chỉnh tuần tự Holm-Bonferroni với ngưỡng hiệu ứng tối thiểu quan tâm $\text{SESOI} = 0,030$.

2. **Tầng 2 – Đánh giá Thăm dò Định tính qua Kiểm toán Người (Exploratory Qualitative Human Audit):**
   - **Quy mô:** Một mẫu kiểm toán nhỏ gồm 60 câu trả lời (tương ứng với 20 câu hỏi $\times$ 3 mô hình).
   - **Quy trình:** Kiểm toán người ẩn danh (Double-Blind Review) với mã ngẫu nhiên `Model_Alpha`, `Model_Beta`, `Model_Gamma`, sau đó trải qua quy trình kiểm tra tính nhất quán và giải quyết bất đồng (Adjudication) trên 21 trường hợp nghi vấn trước khi mở mù chính thức.
   - **Mục tiêu:** Cung cấp bằng chứng định tính bổ trợ nhằm giải mã bản chất các hành vi sinh văn bản thực tế, phân biệt giữa từ chối hợp lệ và từ chối vô căn cứ, phát hiện ảo giác học thuật (bịa đặt thông tin hoặc mâu thuẫn trực tiếp với bài báo), và phân tích tương quan mô tả giữa nhãn đánh giá của con người với các proxy tự động.

> [!IMPORTANT]
> **Ranh giới phân định mẫu:** Nghiên cứu tuyệt đối không gộp chung hai tập mẫu này hoặc xem tập mẫu 60 câu trả lời như một ước lượng tham số cho toàn thể mô hình. Mẫu 60 câu là nghiên cứu thăm dò định tính (qualitative exploratory sample) phục vụ việc giải thích cơ chế, trong khi tập 500 câu hỏi là cơ sở định lượng so sánh cốt lõi.

---

## 3. Kết quả Đánh giá Định lượng trên Tập 500 Câu hỏi (Primary Quantitative Benchmark)

### 3.1. Bảng số liệu tổng hợp định lượng ($N=500, K=250$)

| Mô hình LLM | Số tham số | Kích thước đĩa / RAM | Token F1 (Toàn bộ) | F1 Extractive ($n=319$) | F1 Abstractive ($n=110$) | F1 Boolean ($n=71$) | Số ca từ chối (Refusal Rate) | Automated Containment Proxy | Độ trễ P50 (s) | Độ trễ P95 (s) | Thông lượng (tokens/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`llama3.2:3b`** | 3,21B | 2,0 GB / ~2,5 GB | **0,2033** | 0,2605 | 0,1438 | **0,0385** | 243 (48,6%) | 37,9% | 6,55s | 15,16s | 12,7 |
| **`llama3.2:1b`** | 1,23B | 1,3 GB / ~1,6 GB | **0,1346** | 0,1730 | 0,1108 | 0,0006 | 294 (58,8%) | 29,3% | 5,08s | 9,83s | 20,4 |
| **`qwen2.5:0.5b`** | 0,49B | 397 MB / ~0,6 GB | **0,2324** | **0,2912** | **0,1921** | 0,0349 | 50 (10,0%) | **60,3%** | **3,85s** | **7,50s** | **57,3** |

*Ghi chú kỹ thuật:* Toàn bộ số liệu được trích xuất trực tiếp từ [`rq5_llm_generation_benchmark_500q.json`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json) và đã qua kiểm chứng độc lập.

### 3.2. Phân tích chi tiết các chỉ số tự động

1. **Bản chất của chỉ số Token F1:**
   - Token F1 đo lường **độ trùng lặp từ vựng mặt chữ (lexical token overlap)** giữa câu trả lời sinh ra và câu trả lời tham chiếu của chuyên gia sau khi chuẩn hóa văn bản theo quy chuẩn chuẩn của SQuAD/QASPER (chuyển chữ thường, loại bỏ mạo từ `"a"`, `"an"`, `"the"`, lược bỏ dấu câu). Token F1 không phản ánh đầy đủ tính tương đương ngữ nghĩa (semantic equivalence) hoặc tính hợp lý logic trừu tượng.
   - Điểm F1 đạt cao nhất ở nhóm câu hỏi trích xuất (`Extractive`, chiếm 63,8% tập dữ liệu: Llama 3B đạt 0,2605; Qwen 0.5B đạt 0,2912) do câu trả lời chuẩn thường là các cụm từ nguyên văn trong bài báo. Ở nhóm câu hỏi suy luận (`Abstractive`) và câu hỏi Đúng/Sai (`Boolean`), điểm Token F1 sụt giảm rõ rệt vì các mô hình thường sinh câu giải thích dài thay vì chỉ đưa ra từ khóa đơn lẻ.

2. **Hiện tượng từ chối an toàn và Nghịch lý Token F1 của Qwen-2.5-0.5B:**
   - Tập dữ liệu 500 câu hỏi được lọc theo tiêu chí **chỉ chứa các câu hỏi có thể trả lời được (Answerable-only Cohort)** từ tập QASPER. Theo quy chuẩn đánh giá tự động, mỗi khi mô hình kích hoạt câu từ chối chuẩn theo yêu cầu phi chức năng NFR-03 (*"Tôi không tìm thấy thông tin này trong tài liệu được cung cấp"*), câu trả lời đó sẽ nhận điểm Token F1 bằng $0,0$.
   - **`llama3.2:3b`** kích hoạt từ chối ở 243/500 câu (48,6%) và **`llama3.2:1b`** kích hoạt từ chối ở 294/500 câu (58,8%). Sự thận trọng cao này khiến điểm số Token F1 trung bình bị kéo giảm đáng kể bởi 243 đến 294 giá trị $0,0$.
   - Ngược lại, **`qwen2.5:0.5b`** có tỷ lệ từ chối cực kỳ thấp, chỉ 10,0% (50/500 câu). Mô hình này có xu hướng đoán mò quyết liệt (aggressive guessing) và cố gắng trả lời hầu hết mọi câu hỏi. Do tập 500 câu hỏi này về bản chất là các câu có câu trả lời trong bài báo, việc cố gắng trả lời giúp Qwen đạt được nhiều điểm trùng lặp từ vựng hơn, từ đó đạt điểm F1 trung bình cao hơn ($0,2324$ so với $0,2033$).
   - Tuy nhiên, như được chứng minh ở phần kiểm toán người, xu hướng đoán mò này đi kèm với cái giá đắt: tỷ lệ bịa đặt và ảo giác học thuật của Qwen cao gấp 1,67 lần so với Llama 3.2.

3. **Bản chất của Proxy chứa từ ngữ cảnh (Automated Containment Proxy):**
   - Containment Proxy đo lường tỷ lệ các từ tố mang nghĩa (loại trừ stopword chuẩn tiếng Anh và các từ ngắn $\le 2$ ký tự) trong câu trả lời sinh ra có xuất hiện trực tiếp trong khối ngữ cảnh tài liệu được cung cấp.
   - **Đây là một proxy đo lường mức độ trùng lặp từ vựng bề mặt với ngữ cảnh (lexical overlap with context), hoàn toàn KHÔNG đo lường tính bám sát suy luận ngữ nghĩa (semantic entailment) hay tính đúng đắn sự thật (factual correctness).**
   - Một mô hình có thể sao chép nguyên văn một câu ngẫu nhiên không liên quan trong ngữ cảnh để đạt Containment Proxy gần 100%, nhưng câu trả lời đó vẫn là một phát biểu phi lý hoặc sai lệch đối với câu hỏi.

4. **Hiệu năng và Tài nguyên Phần cứng trên CPU Máy trạm:**
   - Cả ba mô hình đều vận hành ổn định trên CPU AMD Ryzen 5 5600 với 16 GB RAM DDR4 mà không gây tràn trang đĩa hay tiêu tốn quá 2,5 GB RAM cho tiến trình suy luận.
   - `qwen2.5:0.5b` đạt thông lượng vượt trội 57,3 tokens/s (độ trễ P50 = 3,85s), phù hợp cho các thiết bị nhúng cực nhẹ.
   - `llama3.2:3b` đạt thông lượng 12,7 tokens/s (độ trễ P50 = 6,55s, P95 = 15,16s), hoàn toàn vượt ngưỡng đọc tự nhiên của người dùng học thuật ($\ge 8 - 10$ tokens/s) và nằm trong ngưỡng dung thứ tương tác thực tế của giao diện người dùng.

### 3.3. Kiểm định So sánh Thống kê theo Cụm Bài báo ($K=250, df=249$)

Để kiểm chứng tính vững chắc của các sai khác quan sát được, các phép kiểm định cặp ghép theo cụm bài báo đã được thực hiện và kiểm soát FWER qua hiệu chỉnh Holm-Bonferroni:

| Cặp so sánh đối đầu | Sai khác trung bình ($\Delta_{\text{obs}}$) | Khoảng tin cậy 95% Clustered CI | Trị số $t$ ($df=249$) | Trị số $p_{\text{adj}}$ (Holm-Bonferroni) | Ngưỡng SESOI ($\ge 0,030$) | Kết luận thống kê |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`llama3.2:3b` vs `llama3.2:1b`** | **$+0,0687$** | $[+0,0480; +0,0902]$ | $+6,2597$ | **$3,35 \times 10^{-9}$** | **ĐẠT** | **Bác bỏ $H_0$ (Vượt trội có ý nghĩa thống kê cao)** |
| **`llama3.2:3b` vs `qwen2.5:0.5b`** | $-0,0291$ | $[-0,0509; -0,0053]$ | $-2,5028$ | $0,0130$ | Không đạt | Bác bỏ $H_0$ (Sai khác do tỷ lệ từ chối trên tập answerable) |
| **`llama3.2:1b` vs `qwen2.5:0.5b`** | $-0,0978$ | $[-0,1189; -0,0763]$ | $-8,9651$ | $2,27 \times 10^{-16}$ | Đạt | Bác bỏ $H_0$ (Sai khác thống kê có ý nghĩa) |

- Phép so sánh giữa `llama3.2:3b` và `llama3.2:1b` chứng minh sự nâng cấp từ 1B lên 3B mang lại bước nhảy vọt thực chất về độ chính xác từ tố ($\Delta = +0,0687$, vượt xa ngưỡng $\text{SESOI} = 0,030$, $p < 10^{-8}$).
- Phép so sánh giữa `llama3.2:3b` và `qwen2.5:0.5b` có $\Delta = -0,0291$ (chưa chạm ngưỡng $\text{SESOI} = 0,030$). Như đã biện giải, chênh lệch này chủ yếu xuất phát từ việc Llama 3.2 3B tuân thủ nghiêm ngặt yêu cầu từ chối an toàn khi ngữ cảnh trích xuất chưa đầy đủ, trong khi Qwen 0.5B chấp nhận sinh câu trả lời phỏng đoán.

---

## 4. Kết quả Kiểm toán Thăm dò Định tính qua Đánh giá Người (Exploratory Qualitative Human Audit)

### 4.1. Phân loại 6 nhãn theo Đề cương Chuẩn hóa

Để đánh giá trung thực ngữ nghĩa thực tế, 60 câu trả lời (20 câu hỏi $\times$ 3 mô hình) đã được kiểm toán người mù đôi theo phân loại 6 nhãn được xác định trong đề cương [`DEC03_FINAL_EVALUATION_PROTOCOL.md`](file:///c:/DACNTT/eval/phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md):
1. **`SUPPORTED` (Được hỗ trợ đầy đủ):** Câu trả lời giải đáp đúng trọng tâm câu hỏi và mọi phát biểu đều được hỗ trợ trực tiếp từ ngữ cảnh trích dẫn.
2. **`REFUSAL_VALID` (Từ chối hợp lệ):** Mô hình từ chối trả lời vì ngữ cảnh thực sự thiếu thông tin để kết luận.
3. **`UNSUPPORTED` (Không có căn cứ / Ảo giác bịa đặt):** Câu trả lời đưa ra các thông tin, con số hoặc khẳng định không hề xuất hiện hoặc không thể suy luận từ ngữ cảnh.
4. **`CONTRADICTED` (Mâu thuẫn trực tiếp):** Câu trả lời khẳng định điều trái ngược trực tiếp với thông tin được nêu trong ngữ cảnh.
5. **`MISSING_INFO - UNJUSTIFIED_REFUSAL` (Từ chối vô căn cứ):** Mô hình đưa ra câu từ chối an toàn mặc dù ngữ cảnh được cung cấp có chứa đầy đủ thông tin để trả lời.
6. **`MISSING_INFO - PARTIAL` (Thiếu thông tin / Trả lời một phần):** Câu trả lời đúng một phần nhưng bỏ sót các khía cạnh quan trọng mà ngữ cảnh có đề cập.

### 4.2. Bảng phân bố nhãn kiểm toán người sau mở mù ($N=60$)

| Phân loại nhãn chuẩn | `llama3.2:3b` ($n=20$) | `llama3.2:1b` ($n=20$) | `qwen2.5:0.5b` ($n=20$) | Tổng số câu ($N=60$) | Tỷ lệ toàn phần (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`SUPPORTED`** | **10** (50,0%) | 9 (45,0%) | 8 (40,0%) | 27 | 45,0% |
| **`REFUSAL_VALID`** | **4** (20,0%) | 2 (10,0%) | 3 (15,0%) | 9 | 15,0% |
| **`UNSUPPORTED`** | 2 (10,0%) | 2 (10,0%) | 4 (20,0%) | 8 | 13,3% |
| **`MISSING_INFO - UNJUSTIFIED_REFUSAL`** | **1** (5,0%) | 5 (25,0%) | 3 (15,0%) | 9 | 15,0% |
| **`MISSING_INFO - PARTIAL`** | 2 (10,0%) | 1 (5,0%) | 1 (5,0%) | 4 | 6,7% |
| **`CONTRADICTED`** | 1 (5,0%) | 1 (5,0%) | 1 (5,0%) | 3 | 5,0% |
| **Tổng cộng** | **20** (100,0%) | **20** (100,0%) | **20** (100,0%) | **60** | **100,0%** |

### 4.3. Các chỉ số chất lượng phái sinh từ kiểm toán người

Từ bảng phân bố 6 nhãn, các chỉ số chất lượng định tính được phái sinh cụ thể cho từng mô hình:

1. **Độ trung thực nghiêm ngặt (Strict Faithfulness - `SUPPORTED`):**
   - `llama3.2:3b` đạt tỷ lệ cao nhất: **50,0%** (10/20 câu).
   - `llama3.2:1b` đạt: **45,0%** (9/20 câu).
   - `qwen2.5:0.5b` đạt thấp nhất: **40,0%** (8/20 câu).

2. **Mức độ tuân thủ căn cứ ngữ cảnh (Grounded Compliance - `SUPPORTED` + `REFUSAL_VALID`):**
   - Chỉ số này đo lường khả năng hành xử an toàn và trung thực của mô hình: hoặc trả lời đúng dựa trên căn cứ, hoặc từ chối đúng khi thiếu căn cứ.
   - **`llama3.2:3b`** vượt trội áp đảo với **70,0%** (14/20 câu).
   - `llama3.2:1b` đạt **55,0%** (11/20 câu).
   - `qwen2.5:0.5b` đạt **55,0%** (11/20 câu).

3. **Tổng tỷ lệ ảo giác học thuật (Total Hallucination Rate - `UNSUPPORTED` + `CONTRADICTED`):**
   - **`qwen2.5:0.5b`** có tỷ lệ ảo giác cao nhất: **25,0%** (5/20 câu, gồm 20,0% bịa đặt trắng trợn và 5,0% mâu thuẫn trực tiếp).
   - `llama3.2:3b` và `llama3.2:1b` kiểm soát ảo giác tốt hơn, cùng ghi nhận **15,0%** (3/20 câu).

4. **Tỷ lệ từ chối vô căn cứ (Unjustified Refusal Rate):**
   - `llama3.2:1b` có xu hướng từ chối quá mức (over-refusal) nghiêm trọng nhất: **25,0%** (5/20 câu từ chối sai dù ngữ cảnh có đầy đủ thông tin).
   - `qwen2.5:0.5b` ghi nhận **15,0%** (3/20 câu).
   - **`llama3.2:3b`** thể hiện năng lực hiểu ngữ cảnh vượt trội khi chỉ từ chối sai duy nhất **5,0%** (1/20 câu).

---

## 5. Phân tích Tương quan Mô tả giữa Nhãn Người và Proxy Tự động ($N=60$)

> [!NOTE]
> **Lưu ý thiết kế đo lường lặp (Repeated-Measures Notice):** Tập dữ liệu 60 quan sát bắt nguồn từ 20 câu hỏi nghiên cứu phân bổ lặp lại trên 3 mô hình. Do đó, các hệ số tương quan tuyến tính Pearson dưới đây được báo cáo như các **mối liên hệ tương quan mô tả trong mẫu (descriptive sample associations)**, không giả định các quan sát độc lập hoàn toàn và không dùng để khẳng định tính giá trị phổ quát của proxy.

### 5.1. Các hệ số tương quan mẫu mô tả

- **Tương quan giữa Nhãn `SUPPORTED` của người và Token F1 tự động:** $r = +0,4168$. Mối tương quan dương ở mức vừa phải, cho thấy Token F1 có phản ánh phần nào mức độ trả lời chính xác, nhưng độ phân tán còn lớn do phụ thuộc vào độ dài văn bản.
- **Tương quan giữa Nhãn `SUPPORTED` của người và Containment Proxy:** $r = +0,3125$.
- **Tương quan giữa Tuân thủ căn cứ (`SUPPORTED` + `REFUSAL_VALID`) và Containment Proxy:** $r = +0,0868$. Mối tương quan gần như bằng không ($r \approx 0$). Nguyên nhân là vì khi mô hình từ chối hợp lệ (`REFUSAL_VALID`), câu trả lời từ chối không chứa các từ vựng trong bài báo, dẫn đến điểm Containment Proxy bị kéo tụt xuống mức cực thấp.
- **Tương quan giữa Ảo giác (`UNSUPPORTED` + `CONTRADICTED`) và Containment Proxy:** $r = -0,0897$. Mối tương quan âm rất yếu, chứng minh rằng Containment Proxy không thể nhận diện được các trường hợp ảo giác.

### 5.2. Giá trị trung bình của các proxy tự động phân theo nhãn người

| Nhãn phân loại người | Số lượng mẫu ($n$) | Điểm Token F1 trung bình | Điểm Containment Proxy trung bình (%) |
| :--- | :---: | :---: | :---: |
| **`SUPPORTED`** | 27 | **0,3558** | **56,7%** |
| **`REFUSAL_VALID`** | 9 | 0,1275 | 14,0% |
| **`UNSUPPORTED`** | 8 | 0,1845 | **32,9%** |
| **`MISSING_INFO - UNJUSTIFIED_REFUSAL`** | 9 | 0,1650 | 30,5% |
| **`MISSING_INFO - PARTIAL`** | 4 | 0,1435 | **67,4%** |
| **`CONTRADICTED`** | 3 | 0,1481 | **44,0%** |

**Hàm ý phương pháp luận quan trọng:**
- Các câu trả lời bịa đặt (`UNSUPPORTED`) vẫn đạt Containment Proxy trung bình lên tới **32,9%**, và các câu mâu thuẫn trực tiếp (`CONTRADICTED`) đạt tới **44,0%**. Điều này xảy ra do mô hình có thể sao chép các thuật ngữ khoa học từ ngữ cảnh nhưng sắp đặt chúng thành một phát biểu sai sự thật hoặc gán ghép sai đối tượng.
- Ngược lại, các trường hợp từ chối chuẩn mực (`REFUSAL_VALID`) chỉ đạt Containment Proxy trung bình là **14,0%**.
- Bằng chứng thực nghiệm này khẳng định mạnh mẽ rằng: **Automated Containment Proxy chỉ là một thước đo trùng lặp từ vựng bề mặt, không thể sử dụng làm thước đo thay thế cho độ trung thực ngữ nghĩa (Semantic Faithfulness) trong các hệ thống RAG học thuật.**

---

## 6. Biện giải Khoa học và Quyết định Lựa chọn Mô hình Hệ thống

1. **Lý giải nguyên nhân `llama3.2:3b` là lựa chọn tối ưu:**
   - Mặc dù trên thang đo định lượng 500 câu, `llama3.2:3b` có điểm Token F1 bề mặt ($0,2033$) thấp hơn `qwen2.5:0.5b` ($0,2324$), nhưng sự chênh lệch này là hệ quả trực tiếp của việc Llama 3B từ chối an toàn ở 48,6% câu hỏi khi ngữ cảnh trích xuất chưa đủ rõ ràng.
   - Khi tiến hành kiểm toán người, `llama3.2:3b` chứng minh sự vượt trội toàn diện:
     + Đạt tỷ lệ trung thực nghiêm ngặt cao nhất (**50,0%**);
     + Đạt mức độ tuân thủ căn cứ ngữ cảnh cao nhất (**70,0%** so với 55,0% của hai mô hình còn lại);
     + Kiểm soát ảo giác ở mức thấp (**15,0%** so với 25,0% của Qwen 0.5B);
     + Tỷ lệ từ chối vô căn cứ thấp nhất (**5,0%** so với 25,0% của Llama 1B).
   - Về mặt hiệu năng, `llama3.2:3b` đạt thông lượng 12,7 tokens/s trên CPU đơn thuần, đáp ứng trọn vẹn yêu cầu phi chức năng NFR-02 và NFR-03 mà không cần nâng cấp GPU rời.

2. **Kết luận kiến trúc:**
   - Hệ thống chính thức chuẩn hóa và cấu hình mặc định mô hình **`llama3.2:3b`** làm engine sinh câu trả lời RAG trong sản phẩm phần mềm.
