# BÁO CÁO THỰC NGHIỆM RQ5: MÔ HÌNH NGÔN NGỮ LỚN CỤC BỘ (LOCAL SLM GENERATION & FAITHFULNESS)

**Đề tài:** Xây dựng Hệ thống Quản lý Tài liệu Nghiên cứu Khoa học Tích hợp Trợ lý AI Sử dụng RAG
**Nguồn nội dung:** Mục 5.6 của luận văn [`DU_AN_CNTT_TOAN_VAN.md`](../../DU_AN_CNTT_TOAN_VAN.md); tệp này được tái tạo từ mục đó và phải được giữ đồng bộ.
**Cập nhật:** 29/10/2026. Số liệu kiểm toán người đã được hiệu chỉnh phép gán mô hình (xem [`CORRECTED_HUMAN_FAITHFULNESS_REPORT.md`](../phases/phase_9_generation/artifacts/human_faithfulness_review/correction/CORRECTED_HUMAN_FAITHFULNESS_REPORT.md)); phiên bản trước của tệp này dùng phép gán sai.

## 1. Truy xuất nguồn gốc (Provenance)

- **Mã thực nghiệm:** `EXP-RQ5-MAIN-SAMPLED` trong [`eval/experiment_provenance_registry.json`](../experiment_provenance_registry.json)
- **Tập mẫu:** [`eval_sample_manifest_500q.json`](../phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json) (250 bài báo, 500 câu hỏi từ QASPER Train chưa phơi nhiễm)
- **Đề cương:** [`DEC03_FINAL_EVALUATION_PROTOCOL.md`](../phases/phase_9_generation/artifacts/DEC03_FINAL_EVALUATION_PROTOCOL.md)
- **Kết quả định lượng 500 câu hỏi:** [`rq5_llm_generation_benchmark_500q.json`](../phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json), checkpoint [`rq5_inference_checkpoint.jsonl`](../phases/phase_9_generation/artifacts/rq5_inference_checkpoint.jsonl)
- **Kiểm toán người (60 câu trả lời):** phiếu đã ký [`review_and_signed.md`](../phases/phase_9_generation/artifacts/review_and_signed.md); nhãn đã phân xử [`faithfulness_annotations_adjudicated.csv`](../phases/phase_9_generation/artifacts/human_faithfulness_review/audit/faithfulness_annotations_adjudicated.csv); dữ liệu mở mù đã hiệu chỉnh [`faithfulness_annotations_unblinded_corrected.csv`](../phases/phase_9_generation/artifacts/human_faithfulness_review/correction/faithfulness_annotations_unblinded_corrected.csv)
- **Tập lệnh:** `eval/phases/phase_9_generation/scripts/evaluate_rq5_llm_generation.py` (suy luận và thống kê), `remap_human_labels_by_answer.py` (hiệu chỉnh phép gán nhãn)
- **Phần cứng:** CPU AMD Ryzen 5 5600, 16 GB RAM, Ollama cục bộ, không dùng GPU.

## 2. Kết quả (đồng bộ từ Mục 5.6 của luận văn)

### 5.6.1. Thiết lập thực nghiệm có kiểm soát và Phương pháp luận Hai Tầng

Câu hỏi nghiên cứu RQ5 được thiết lập nhằm khảo sát giai đoạn sinh lời đáp (Generation Phase) trong đường ống RAG học thuật:

> **RQ5:** *Các mô hình ngôn ngữ lớn mã nguồn mở chạy cục bộ (`qwen2.5:0.5b`, `llama3.2:1b`, `llama3.2:3b`) so sánh như thế nào về độ chính xác câu trả lời (Answer Correctness), độ trung thực bám sát bằng chứng (Faithfulness) và hiệu năng suy luận (độ trễ P50/P95, thông lượng tokens/giây) khi được cung cấp cùng một ngữ cảnh trích dẫn học thuật và cùng một mẫu lời nhắc có cấu trúc trên môi trường máy trạm cá nhân không có GPU rời?*

Để bảo đảm tính chặt chẽ khoa học, kiểm soát nghiêm ngặt hiện tượng thiên lệch và phân định rõ ranh giới phương pháp luận, đánh giá RQ5 được vận hành theo cơ chế **Hai Tầng Độc lập (Dual-Tier Methodology)**:

1. **Tầng 1 – Đánh giá Định lượng Quy mô Lớn (Primary Quantitative Benchmark):**
   - **Tập mẫu:** $N = 500$ câu hỏi khoa học thuộc $K = 250$ cụm bài báo trích từ tập QASPER Train chưa từng phơi nhiễm (Unexposed Cohort, mã thực nghiệm `EXP-RQ5-MAIN-SAMPLED` đăng ký trong [`eval/experiment_provenance_registry.json`](../../eval/experiment_provenance_registry.json)). Toàn bộ câu hỏi đều thuộc nhóm có thể trả lời được (`answerable-only`). Với 3 mô hình, hệ thống thực thi tổng cộng $1.500$ lượt suy luận độc lập.
   - **Điều kiện kiểm soát:** Giải mã tất định (`temperature = 0.0`), giới hạn sinh tối đa `num_predict = 256` tokens, chung một mẫu lời nhắc học thuật (Academic Assistant Prompt). Ngữ cảnh là các đoạn bằng chứng chuẩn (gold evidence) của QASPER cho từng câu hỏi, ghép nối lại; không dùng ngữ cảnh do bộ truy xuất trả về. Như vậy RQ5 đo năng lực của khâu sinh khi đã có ngữ cảnh đúng, không đo chất lượng toàn trình.
   - **Thước đo tự động:** Token F1 (toàn phần và phân rã theo 3 loại câu hỏi: Extractive, Abstractive, Boolean); tỷ lệ kích hoạt câu từ chối chuẩn theo yêu cầu phi chức năng NFR-03 (Refusal Rate); tỷ lệ chứa từ vựng ngữ cảnh tự động (Automated Containment Proxy); độ trễ P50/P95 và thông lượng suy luận (tokens/s).
   - **Kiểm định suy diễn thống kê:** Thực hiện kiểm định $t$ ghép cặp theo cụm bài báo ($K=250, df=249$), ước lượng khoảng tin cậy 95% bằng Bootstrap phân cụm ($B=2.000$) và kiểm soát tỷ lệ sai số họ (FWER) bằng hiệu chỉnh tuần tự Holm-Bonferroni với ngưỡng hiệu ứng tối thiểu quan tâm $\text{SESOI} = 0,030$.

2. **Tầng 2 – Đánh giá Thăm dò Định tính qua Kiểm toán Người (Exploratory Qualitative Human Audit):**
   - **Tập mẫu:** Một mẫu kiểm toán nhỏ gồm 60 câu trả lời (tương ứng với 20 câu hỏi $\times$ 3 mô hình).
   - **Quy trình:** Một người đánh giá duy nhất gán nhãn các câu trả lời với định danh mô hình được ẩn bằng mã ngẫu nhiên `Model_Alpha`, `Model_Beta`, `Model_Gamma`. Sau đó, 21 trường hợp nghi vấn được rà soát và phân xử (adjudication; 11 nhãn được điều chỉnh) trước khi mở mù. Không có người đánh giá thứ hai, nên không có chỉ số đồng thuận giữa người đánh giá.
   - **Hiệu chỉnh khi mở mù (kiểm toán độc lập, 29/10/2026):** Phiếu đánh giá đã ký (`review_and_signed.md`) sắp xếp ba câu trả lời của nhiều câu hỏi theo thứ tự khác với tệp ánh xạ mã mù. Lần mở mù ban đầu ghép nhãn theo mã mù nên 26/45 câu trả lời phân biệt được đã bị gán cho sai mô hình. Nhãn được gán lại bằng cách đối chiếu nguyên văn từng câu trả lời với đầu ra của mô hình trong tệp checkpoint suy luận (60/60 khớp chính xác, phép gán một-một trên mỗi câu hỏi). Toàn bộ số liệu kiểm toán người trong mục này là số liệu đã hiệu chỉnh (`eval/phases/phase_9_generation/artifacts/human_faithfulness_review/correction/`).
   - **Mục tiêu:** Cung cấp bằng chứng định tính bổ trợ nhằm giải mã bản chất các hành vi sinh văn bản thực tế, phân biệt giữa từ chối hợp lệ và từ chối vô căn cứ, phát hiện ảo giác học thuật (bịa đặt thông tin hoặc mâu thuẫn trực tiếp với bài báo), và phân tích tương quan mô tả giữa nhãn đánh giá của con người với các proxy tự động.

*Ranh giới phân định mẫu:* Nghiên cứu tuyệt đối không gộp chung hai tập mẫu này hoặc xem tập mẫu 60 câu trả lời như một ước lượng tham số cho toàn thể mô hình. Mẫu 60 câu là nghiên cứu thăm dò định tính (qualitative exploratory sample) phục vụ việc giải thích cơ chế, trong khi tập 500 câu hỏi là cơ sở định lượng so sánh cốt lõi.

### 5.6.2. Kết quả đo lường định lượng trên tập 500 câu hỏi (Primary Quantitative Results)

Bảng 5.6 trình bày kết quả đo lường khách quan tự động trên toàn bộ 500 câu hỏi ($K=250$ bài báo, $1.500$ lượt suy luận) cho 3 mô hình ngôn ngữ lớn ứng viên.

*Bảng 5.6: Kết quả đánh giá định lượng mô hình ngôn ngữ lớn cục bộ (RQ5) trên 500 câu hỏi ($K=250$ cụm bài báo).*

| Mô hình LLM | Tham số | Kích thước tệp mô hình (Ollama) | Token F1 (Toàn bộ) | F1 Extractive | F1 Abstractive | F1 Boolean | Số ca từ chối (Refusal Rate) | Automated Containment Proxy | Độ trễ P50 (s) | Độ trễ P95 (s) | Thông lượng (tokens/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`llama3.2:3b`** | 3,21B | 2,0 GB | **0,2033** | 0,2605 | 0,1438 | **0,0385** | 243 (48,6%) | 37,9% | 6,55s | 15,16s | 12,7 |
| **`llama3.2:1b`** | 1,23B | 1,3 GB | **0,1346** | 0,1730 | 0,1108 | 0,0006 | 294 (58,8%) | 29,3% | 5,08s | 9,83s | 20,4 |
| **`qwen2.5:0.5b`** | 0,49B | 397 MB | **0,2324** | **0,2912** | **0,1921** | 0,0349 | 50 (10,0%) | **60,3%** | **3,85s** | **7,50s** | **57,3** |

*Ghi chú Bảng 5.6 (nguồn: `eval/phases/phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json`):* Theo phân loại của tệp manifest, 500 câu hỏi gồm 319 Extractive, 109 Abstractive và 72 Boolean. F1 theo loại được tính theo quy ước của bộ đánh giá QASPER (lấy đáp án tham chiếu cho F1 cao nhất trong số các người gán nhãn), nên với 2 câu hỏi có đáp án tham chiếu khác loại, loại câu hỏi phụ thuộc vào mô hình (số câu Abstractive/Boolean: 3b 110/71, 1b 109/72, qwen 108/73). Bộ nhớ RAM của tiến trình Ollama **không được đo thành công** trong lượt chạy này (0 mẫu cho `llama3.2:3b`, 1 mẫu không đại diện cho hai mô hình còn lại), vì vậy bảng chỉ báo cáo kích thước tệp mô hình. P50/P95 được tính theo thống kê thứ tự trên 500 lượt suy luận.

*Phân tích các chỉ số tự động và hiện tượng quan sát được:*

1. **Bản chất của chỉ số Token F1:**
   Chỉ số Token F1 đo lường mức độ trùng lặp từ tố mặt chữ (lexical token overlap) giữa văn bản sinh ra và đáp án chuẩn sau khi chuẩn hóa văn bản (chuyển chữ thường, loại bỏ mạo từ và dấu câu). Token F1 thể hiện rõ nét tính chất bề mặt này khi đạt điểm cao nhất ở nhóm câu hỏi trích xuất (`Extractive`, chiếm 63,8% tập mẫu: Llama 3B đạt 0,2605; Qwen 0.5B đạt 0,2912) nhờ việc sao chép chính xác cụm từ nguyên văn. Ở nhóm câu hỏi suy luận (`Abstractive`) và câu hỏi Đúng/Sai (`Boolean`), điểm Token F1 sụt giảm mạnh do mô hình thường sinh câu văn giải thích ngữ nghĩa thay vì chỉ đưa ra từ khóa đơn lẻ.

2. **Nghịch lý Token F1 của Qwen-2.5-0.5B và Hiện tượng Từ chối An toàn:**
   Dữ liệu ghi nhận một hiện tượng tưởng chừng nghịch lý: mô hình siêu nhỏ `qwen2.5:0.5b` (0,49B tham số) đạt điểm Token F1 ($0,2324$) cao hơn cả `llama3.2:3b` ($0,2033$). Khi phân tích sâu vào hành vi của mô hình, nguyên nhân căn bản xuất phát từ **tỷ lệ kích hoạt câu từ chối an toàn (Refusal Rate)**:
   - Theo yêu cầu phi chức năng NFR-03, lời nhắc yêu cầu mô hình phát câu từ chối chuẩn (*"The document does not contain sufficient relevant information to answer this question."*) khi ngữ cảnh không chứa câu trả lời. Câu từ chối được nhận diện bằng đối khớp chuỗi con; trên tập dữ liệu này (gồm toàn bộ các câu hỏi có thể trả lời được), câu từ chối thường nhận Token F1 bằng $0,0$.
   - `llama3.2:3b` kích hoạt từ chối ở **48,6%** (243/500 câu) và `llama3.2:1b` từ chối tới **58,8%** (294/500 câu). Số lượng lớn các điểm $0,0$ này đã kéo tụt đáng kể điểm F1 trung bình của họ mô hình Llama.
   - Ngược lại, `qwen2.5:0.5b` có tỷ lệ từ chối chỉ **10,0%** (50/500 câu) và hầu như luôn cố gắng trả lời. Do toàn bộ 500 câu hỏi về bản chất là có đáp án, việc luôn trả lời giúp Qwen thu thập được nhiều từ tố trùng khớp hơn và nâng điểm F1 trung bình.
   - *Phân tích bổ sung (hậu kiểm, mô tả, không kiểm định):* Trên 244 câu hỏi mà cả `llama3.2:3b` và `qwen2.5:0.5b` đều không từ chối, Token F1 trung bình của `llama3.2:3b` là 0,3797 so với 0,3002 của `qwen2.5:0.5b`. Điều này phù hợp với giải thích rằng lợi thế F1 của Qwen chủ yếu đến từ việc ít từ chối, không phải từ chất lượng câu trả lời cao hơn khi cả hai cùng trả lời.
   - *Giới hạn của bộ nhận diện từ chối:* Phép đối khớp chuỗi bỏ sót 13 câu từ chối được diễn đạt lại (4 của `llama3.2:1b`, 9 của `qwen2.5:0.5b`; 0,87% tổng số 1.500 đầu ra). Số liệu được giữ nguyên như khi chạy và giới hạn này được công bố minh bạch.

3. **Bản chất của Automated Containment Proxy:**
   Chỉ số Automated Containment Proxy đo tỷ lệ phần trăm các từ tố mang nghĩa (loại bỏ stopword tiếng Anh và từ ngắn $\le 2$ ký tự) trong câu trả lời có xuất hiện trực tiếp trong khối ngữ cảnh tài liệu được cung cấp. Nghiên cứu nhấn mạnh rằng **đây là một proxy đo lường độ trùng lặp từ vựng bề mặt với ngữ cảnh (lexical overlap with context), hoàn toàn KHÔNG đo lường tính bám sát suy luận ngữ nghĩa (semantic entailment) hay tính đúng đắn sự thật (factual correctness)**. Một mô hình có thể sao chép nguyên văn một câu ngẫu nhiên không liên quan trong ngữ cảnh để đạt Containment Proxy gần 100%, nhưng câu trả lời đó vẫn là một phát biểu phi lý hoặc sai lệch đối với câu hỏi.

4. **Hiệu năng và Tài nguyên Phần cứng trên CPU Máy trạm:**
   - Cả ba mô hình đều hoàn thành 500 lượt suy luận trên CPU AMD Ryzen 5 5600 với 16 GB RAM DDR4 mà không có lỗi (0 lỗi trong 1.500 lượt). Mức RAM thực tế của tiến trình Ollama không được đo thành công trong lượt chạy này nên không được báo cáo; kích thước tệp mô hình (0,4–2,0 GB) chỉ là cận dưới gợi ý.
   - `qwen2.5:0.5b` đạt thông lượng vượt trội 57,3 tokens/s (độ trễ P50 = 3,85s), phù hợp cho các thiết bị nhúng cực nhẹ.
   - `llama3.2:3b` đạt thông lượng 12,7 tokens/s (độ trễ P50 = 6,55s, P95 = 15,16s), hoàn toàn vượt ngưỡng đọc tự nhiên của người dùng học thuật ($\ge 8 - 10$ tokens/s) và nằm trong ngưỡng dung thứ tương tác thực tế của giao diện người dùng.

### 5.6.3. Kiểm định So sánh Thống kê theo Cụm Bài báo ($K=250, df=249$)

Để kiểm chứng tính vững chắc của các phát hiện định lượng, các phép kiểm định cặp ghép theo cụm bài báo ($K=250, df=249$) đã được thực thi và kiểm soát FWER qua hiệu chỉnh tuần tự Holm-Bonferroni (Bảng 5.7a).

*Bảng 5.7a: Kết quả kiểm định thống kê cặp ghép theo cụm bài báo ($K=250, df=249$).*

| Cặp so sánh đối đầu | Sai khác trung bình ($\Delta_{\text{obs}}$) | Khoảng tin cậy 95% Clustered CI | Trị số $t$ ($df=249$) | Trị số $p_{\text{adj}}$ (Holm-Bonferroni) | Ngưỡng SESOI ($\ge 0,030$) | Quyết định thống kê |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`llama3.2:3b` vs `llama3.2:1b`** | **$+0,0687$** | $[+0,0480; +0,0902]$ | $+6,2597$ | **$3,35 \times 10^{-9}$** | **ĐẠT** | **Bác bỏ $H_0$ (Vượt trội có ý nghĩa thống kê cao)** |
| **`llama3.2:3b` vs `qwen2.5:0.5b`** | $-0,0291$ | $[-0,0509; -0,0053]$ | $-2,5028$ | $0,0130$ | Không đạt | Bác bỏ $H_0$ (`qwen2.5:0.5b` cao hơn; mức chênh dưới SESOI) |
| **`llama3.2:1b` vs `qwen2.5:0.5b`** | $-0,0978$ | $[-0,1189; -0,0763]$ | $-8,9651$ | $2,27 \times 10^{-16}$ | Đạt | Bác bỏ $H_0$ (Sai khác thống kê có ý nghĩa) |

- So sánh giữa `llama3.2:3b` và `llama3.2:1b`: Mô hình 3B thể hiện sự vượt trội có ý nghĩa thống kê áp đảo so với 1B ($\Delta = +0,0687$, khoảng tin cậy 95% hoàn toàn tách rời 0, $p_{\text{adj}} = 3,35 \times 10^{-9}$, thỏa mãn trọn vẹn tiêu chuẩn $\text{SESOI} \ge 0,030$). Điều này khẳng định việc nâng cấp quy mô tham số từ 1,2B lên 3,2B mang lại bước tiến chất lượng thực chất cho năng lực sinh lời đáp.
- So sánh giữa `llama3.2:3b` và `qwen2.5:0.5b`: `qwen2.5:0.5b` có Token F1 cao hơn có ý nghĩa thống kê ($\Delta = -0,0291$, $p_{\text{adj}} = 0,0130$), nhưng mức chênh nhỏ hơn ngưỡng $\text{SESOI} = 0,030$ nên không được xem là khác biệt có ý nghĩa thực tiễn. Phân tích mô tả ở Mục 5.6.2 cho thấy chênh lệch này phần lớn gắn với tỷ lệ từ chối thấp hơn của Qwen trên tập câu hỏi có đáp án.

### 5.6.4. Đánh giá Thăm dò Định tính qua Kiểm toán Người (Exploratory Qualitative Audit)

Nhằm thấu hiểu bản chất ngữ nghĩa và kiểm tra tính trung thực thực tế, mẫu kiểm toán 60 câu trả lời (20 câu hỏi $\times$ 3 mô hình) đã được một người đánh giá gán nhãn khi định danh mô hình được ẩn, theo hệ thống 6 nhãn chuẩn hóa của đề cương:
- `SUPPORTED`: Câu trả lời đúng trọng tâm và hoàn toàn được hỗ trợ từ ngữ cảnh.
- `REFUSAL_VALID`: Mô hình từ chối hợp lệ vì ngữ cảnh thực sự thiếu thông tin.
- `UNSUPPORTED`: Ảo giác bịa đặt thông tin không có trong ngữ cảnh.
- `CONTRADICTED`: Câu trả lời mâu thuẫn trực tiếp với thông tin trong bài báo.
- `MISSING_INFO - UNJUSTIFIED_REFUSAL`: Từ chối vô căn cứ dù ngữ cảnh có đủ thông tin.
- `MISSING_INFO - PARTIAL`: Trả lời đúng một phần nhưng bỏ sót chi tiết quan trọng.

Bảng 5.7 trình bày phân bố 6 nhãn sau khi phân xử và mở mù, với phép gán mô hình đã được hiệu chỉnh theo nguyên văn câu trả lời (xem Mục 5.6.1).

*Bảng 5.7: Phân bố nhãn kiểm toán người (ẩn danh mô hình, một người đánh giá) về độ trung thực (Faithfulness) trên 60 câu trả lời.*

| Phân loại nhãn chuẩn | `llama3.2:3b` ($n=20$) | `llama3.2:1b` ($n=20$) | `qwen2.5:0.5b` ($n=20$) | Tổng số câu ($N=60$) | Tỷ lệ toàn phần (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`SUPPORTED`** | 10 (50,0%) | 7 (35,0%) | 10 (50,0%) | 27 | 45,0% |
| **`REFUSAL_VALID`** | 5 (25,0%) | 4 (20,0%) | 0 (0,0%) | 9 | 15,0% |
| **`UNSUPPORTED`** | 0 (0,0%) | 2 (10,0%) | 6 (30,0%) | 8 | 13,3% |
| **`MISSING_INFO - UNJUSTIFIED_REFUSAL`** | 3 (15,0%) | 6 (30,0%) | 0 (0,0%) | 9 | 15,0% |
| **`MISSING_INFO - PARTIAL`** | 1 (5,0%) | 0 (0,0%) | 3 (15,0%) | 4 | 6,7% |
| **`CONTRADICTED`** | 1 (5,0%) | 1 (5,0%) | 1 (5,0%) | 3 | 5,0% |
| **Tổng cộng** | **20** (100,0%) | **20** (100,0%) | **20** (100,0%) | **60** | **100,0%** |

*\*(Nguồn: `eval/phases/phase_9_generation/artifacts/human_faithfulness_review/correction/corrected_human_review_summary.json`). Kiểm tra nhất quán: số nhãn từ chối (`REFUSAL_VALID` + `UNJUSTIFIED_REFUSAL`) của từng mô hình (8 / 10 / 0) trùng khớp với số câu từ chối do bộ nhận diện tự động ghi nhận trên cùng 20 câu hỏi.*

*Các chỉ số mô tả phái sinh từ kiểm toán người (mẫu nhỏ, $n=20$ mỗi mô hình; chênh lệch vài câu không có ý nghĩa thống kê):*

1. **Tỷ lệ được ngữ cảnh hỗ trợ hoàn toàn (`SUPPORTED`):**
   `llama3.2:3b` và `qwen2.5:0.5b` cùng đạt 10/20 câu (50,0%), `llama3.2:1b` đạt 7/20 câu (35,0%).
2. **Mức độ tuân thủ căn cứ ngữ cảnh (Grounded Compliance - `SUPPORTED` + `REFUSAL_VALID`):**
   Đo hành vi an toàn học thuật (hoặc trả lời đúng có căn cứ, hoặc từ chối đúng khi thiếu căn cứ): `llama3.2:3b` đạt 15/20 câu (75,0%), `llama3.2:1b` đạt 11/20 (55,0%), `qwen2.5:0.5b` đạt 10/20 (50,0%).
3. **Câu trả lời không được ngữ cảnh hỗ trợ (`UNSUPPORTED` + `CONTRADICTED`):**
   `qwen2.5:0.5b` có nhiều nhất: 7/20 câu (35,0%; 6 bịa đặt, 1 mâu thuẫn), so với 3/20 (15,0%) của `llama3.2:1b` và 1/20 (5,0%) của `llama3.2:3b`. Quan sát này phù hợp với việc Qwen ít từ chối: mô hình trả lời nhiều hơn, nhưng một phần đáng kể câu trả lời không có căn cứ trong ngữ cảnh.
4. **Từ chối vô căn cứ (Unjustified Refusals):**
   `llama3.2:1b` từ chối quá mức nhiều nhất với 6/20 câu (30,0%), `llama3.2:3b` 3/20 câu (15,0%), `qwen2.5:0.5b` không có trường hợp nào. Như vậy, điểm yếu chính của họ Llama là từ chối khi ngữ cảnh thực ra có câu trả lời, còn điểm yếu chính của Qwen là trả lời không có căn cứ.

### 5.6.5. Phân tích Tương quan Mô tả giữa Nhãn Người và Proxy Tự động ($N=60$)

*Lưu ý thiết kế đo lường lặp (Repeated Measures):* Tập mẫu 60 câu trả lời bắt nguồn từ 20 câu hỏi độc lập được phân bổ lặp lại trên 3 mô hình. Do đó, các hệ số tương quan tuyến tính Pearson dưới đây được xem xét như **các mối liên hệ tương quan mô tả trong mẫu (descriptive sample associations)**, không giả định các quan sát độc lập và không dùng để khẳng định tính giá trị phổ quát tuyệt đối của các proxy.

- **Tương quan giữa Nhãn `SUPPORTED` của người và Token F1:** $r = +0,644$.
- **Tương quan giữa Nhãn `SUPPORTED` của người và Containment Proxy:** $r = +0,591$.
- **Tương quan giữa Tuân thủ căn cứ (`SUPPORTED` + `REFUSAL_VALID`) và Token F1 / Containment Proxy:** $r = +0,366$ / $+0,260$. Tương quan yếu hơn vì các câu từ chối hợp lệ được tính là tuân thủ nhưng có Token F1 và Containment gần bằng 0.
- **Tương quan giữa Ảo giác (`UNSUPPORTED` + `CONTRADICTED`) và Containment Proxy:** $r = -0,043$, tức gần như không có liên hệ: Containment Proxy không phân biệt được câu trả lời bịa đặt với các câu trả lời khác.

Cần lưu ý rằng các tương quan dương với nhãn `SUPPORTED` phần lớn đến từ các câu từ chối (nhận điểm gần 0 ở cả hai proxy và không bao giờ được gán `SUPPORTED`), nên không nên hiểu đây là bằng chứng rằng các proxy đo được độ trung thực.

Bảng 5.7b đối chiếu giá trị trung bình của các proxy tự động theo từng nhãn phân loại người:

*Bảng 5.7b: Giá trị trung bình của các proxy tự động phân theo nhãn kiểm toán người ($N=60$, số liệu đã hiệu chỉnh).*

| Nhãn phân loại người | Số lượng mẫu ($n$) | Điểm Token F1 trung bình | Điểm Containment Proxy trung bình (%) |
| :--- | :---: | :---: | :---: |
| **`SUPPORTED`** | 27 | **0,4159** | 68,7% |
| **`REFUSAL_VALID`** | 9 | 0,0207 | 0,0% |
| **`UNSUPPORTED`** | 8 | 0,1812 | 38,2% |
| **`MISSING_INFO - UNJUSTIFIED_REFUSAL`** | 9 | 0,0376 | 0,0% |
| **`MISSING_INFO - PARTIAL`** | 4 | 0,2713 | **75,9%** |
| **`CONTRADICTED`** | 3 | 0,1481 | 44,0% |

*Ý nghĩa phương pháp luận:* Các câu trả lời bịa đặt (`UNSUPPORTED`) vẫn đạt Containment Proxy trung bình **38,2%**, các câu mâu thuẫn trực tiếp (`CONTRADICTED`) đạt **44,0%**, và các câu trả lời thiếu ý (`PARTIAL`) thậm chí đạt **75,9%**, cao hơn cả nhóm `SUPPORTED`, do mô hình sử dụng lại các thuật ngữ có sẵn trong ngữ cảnh. Các câu từ chối nhận 0,0% theo định nghĩa. Bằng chứng này, dù chỉ từ một mẫu nhỏ, cho thấy **Automated Containment Proxy không thể thay thế cho đánh giá tính trung thực ngữ nghĩa trong RAG học thuật.**

### 5.6.6. Kết luận Lựa chọn Mô hình cho Hệ thống Phần mềm

Từ bằng chứng định lượng trên 500 câu hỏi và phân tích thăm dò trên 60 câu kiểm toán người:
1. **`llama3.2:3b`** được chọn làm mô hình mặc định của hệ thống, với các căn cứ và giới hạn sau:
   - Vượt trội có ý nghĩa thống kê so với mô hình cùng họ `llama3.2:1b` ($\Delta = +0,0687, p_{\text{adj}} = 3,35 \times 10^{-9}$, vượt SESOI);
   - Có Token F1 thấp hơn `qwen2.5:0.5b` ($\Delta = -0,0291$, $p_{\text{adj}} = 0,013$, dưới SESOI), chủ yếu do từ chối nhiều hơn (48,6% so với 10,0%). Trên các câu hỏi cả hai mô hình cùng trả lời, F1 trung bình của `llama3.2:3b` cao hơn (0,380 so với 0,300; phân tích mô tả);
   - Trong mẫu kiểm toán người, có ít câu trả lời không được ngữ cảnh hỗ trợ nhất (1/20, so với 7/20 của `qwen2.5:0.5b`) và tỷ lệ tuân thủ căn cứ cao nhất (15/20). Đổi lại, mô hình vẫn từ chối vô căn cứ 3/20 câu. Do mẫu chỉ có 20 câu mỗi mô hình và một người đánh giá, các con số này mang tính định hướng, không phải ước lượng tỷ lệ cho toàn bộ tập câu hỏi;
   - Thông lượng 12,7 tokens/s và độ trễ P50 6,55s trên CPU AMD Ryzen 5 5600, đáp ứng ngưỡng tương tác đặt ra (dù chậm hơn đáng kể so với `qwen2.5:0.5b`).
2. Lựa chọn này ưu tiên việc hạn chế câu trả lời bịa đặt hơn là tối đa hóa Token F1. Đây là một đánh đổi có chủ đích cho ứng dụng đọc tài liệu khoa học, nơi một câu từ chối ít gây hại hơn một câu trả lời sai nhưng trôi chảy. Hệ thống cấu hình mặc định **`llama3.2:3b`** làm engine sinh lời đáp (`OLLAMA_MODEL`).
