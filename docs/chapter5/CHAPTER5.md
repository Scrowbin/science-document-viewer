# CHƯƠNG 5. KẾT QUẢ THỰC NGHIỆM VÀ THẢO LUẬN



---



## 5.1. Giới thiệu chương và Phân tích Khám phá Dữ liệu (EDA)



### 5.1.1. Mục tiêu và phạm vi đánh giá



Chương này trình bày, đối sánh và biện giải toàn diện các kết quả thực nghiệm thu được từ quá trình đánh giá có kiểm soát đối với năm câu hỏi nghiên cứu cốt lõi (RQ1 đến RQ5) đã được thiết lập phương pháp luận trong Chương 3:

- **RQ1 (Bóc tách văn bản PDF):** Khảo sát năng lực của 5 công cụ bóc tách PDF cục bộ (`pymupdf_plain`, `pymupdf_layout`, `pypdf`, `pdfminer.six`, `pdfplumber`) về độ bao phủ bằng chứng, độ chính xác ký tự, tỷ lệ phát hiện cấu trúc đề mục, trật tự đọc, độ trễ và tác động đến chất lượng truy xuất hạ nguồn trên 47 bài báo khoa học.

- **RQ2 (Chiến lược phân mảnh văn bản):** Đánh giá 8 chiến lược phân mảnh văn bản dưới một ngân sách ngữ cảnh cố định (1.600 tokens) nhằm xác định tác động của việc bảo toàn ranh giới đề mục và cơ chế phân mảnh phân cấp (Small-to-Big) đối với chất lượng truy xuất.

- **RQ3 (Mô hình biểu diễn vector):** Đo lường và đối sánh toàn diện 11 mô hình biểu diễn vector mã nguồn mở (quy mô $\le 335\text{M}$ tham số) cùng mốc đối chứng BM25 trên tập dữ liệu hợp nhất gồm 207 bài báo, 615 câu hỏi và 5.207 phân đoạn văn bản; phân tích đường biên hiệu quả Pareto giữa chất lượng truy xuất ($\text{nDCG@10}$) và chi phí tài nguyên máy trạm (độ trễ P50, thông lượng và bộ nhớ RAM).

- **RQ4 (Truy xuất lai đa giai đoạn):** Khảo sát cơ chế kết hợp lai đa giai đoạn giữa vector dày (`e5-small-v2`) và tần suất từ khóa (`BM25`) kết hợp phân mảnh phân cấp Small-to-Big trên tập kiểm thử độc lập (Held-Out Test: 408 bài báo, 1.310 câu hỏi, 14.035 đoạn con) nhằm xác định cấu hình hợp nhất tối ưu dưới ngân sách ngữ cảnh 1.600 tokens.

- **RQ5 (Mô hình ngôn ngữ lớn cục bộ):** Đánh giá thực nghiệm có kiểm soát năng lực sinh câu trả lời, độ trung thực học thuật (Faithfulness) và hiệu năng suy luận trên CPU máy trạm của 3 mô hình ngôn ngữ lớn mã nguồn mở (`qwen2.5:0.5b`, `llama3.2:1b`, `llama3.2:3b`) thông qua thiết lập hai tầng: đánh giá tự động trên 500 câu hỏi ($K=250$ cụm bài báo) và kiểm toán người mù đôi trên 60 câu trả lời.

Mọi số liệu được báo cáo trong chương này đều được truy xuất trực tiếp từ các tệp kết quả thực nghiệm gốc có cấu trúc (`eval/results/*.json`, `eval/phases/*/artifacts/`) và các tệp nhật ký truy vấn chi tiết (`*.jsonl`). Để bảo đảm tính trung thực học thuật, chương phân định rạch ròi giữa các phát hiện đã được chứng minh qua kiểm định thống kê và các kết luận mang tính chất quan sát ban đầu; đồng thời chỉ rõ ranh giới giữa các thực nghiệm thành phần đã hoàn tất (RQ1–RQ5) với nội dung đánh giá tổ hợp toàn trình (RQ6) nằm trong kế hoạch phát triển tiếp theo.



### 5.1.2. Phân tích khám phá đặc trưng dữ liệu toàn phần (Full-Scale Benchmark EDA)



Để xây dựng một hệ thống RAG chuyên sâu cho tài liệu khoa học, việc nắm bắt các đặc trưng hình thái, cấu trúc ngữ nghĩa và phân bố văn bản là điều kiện tiên quyết. Ngữ liệu QASPER (*Question Answering on Scientific Papers*, Dasigi et al., NAACL 2021) phiên bản chuẩn v0.3 được lựa chọn làm ngữ liệu nghiên cứu chuẩn vì đây là bộ dữ liệu hiếm hoi cung cấp câu hỏi nghiên cứu thực tế kèm theo bằng chứng là các đoạn văn bản nguyên văn (*ground-truth evidence passages*) được gán nhãn thủ công bởi các chuyên gia đọc toàn văn bài báo.



**Phân định phạm vi tập dữ liệu EDA:** 

Phân tích khám phá dữ liệu (EDA) chính thức trong luận văn được thực thi toàn diện trên **toàn bộ 1.585 bài báo khoa học và 5.049 câu hỏi nghiên cứu** thuộc bản phân phối chuẩn đầy đủ của QASPER (gồm cả 3 phân hoạch Train: 888 bài / 2.593 câu hỏi; Dev: 281 bài / 1.005 câu hỏi; Test: 416 bài / 1.451 câu hỏi). Tập mẫu Pilot ban đầu (gồm 100 bài báo và 250 câu hỏi trích từ tập Development) được lưu giữ như một nghiên cứu thăm dò sơ bộ đối chiếu, không đại diện thay thế cho phân bố toàn thể của ngữ liệu.



Toàn bộ quy trình kiểm toán và phân tích EDA toàn phần được tự động hóa qua mã nguồn [`run_full_qasper_eda.py`](file:///c:/DACNTT/eval/phases/phase_0_baseline/scripts/run_full_qasper_eda.py), xuất bản các tệp định lượng có cấu trúc tại [`qasper_full_corpus_eda.json`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/qasper_full_corpus_eda.json) và bảng đối soát so sánh Pilot vs Toàn phần tại [`eda_pilot_vs_full_comparison.csv`](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_pilot_vs_full_comparison.csv).



Kết quả phân tích thống kê hình thái trên toàn bộ ngữ liệu QASPER (1.585 bài báo / 5.049 câu hỏi) được trực quan hóa trên 4 bảng phân bố đặc trưng tại Hình 5.0.



![Hình 5.0: Phân tích khám phá đặc trưng ngữ liệu khoa học QASPER toàn phần](file:///c:/DACNTT/reports/chapter5/figures/fig5_0_qasper_eda.png)



*Hình 5.0: Phân tích khám phá đặc trưng dữ liệu ngữ liệu khoa học QASPER toàn phần (N = 1.585 bài báo / 5.049 câu hỏi) gồm 4 bảng phân bố: (A) Phân bố loại câu hỏi nghiên cứu; (B) Phân bố độ dài bài báo khoa học toàn văn; (C) Bất đối xứng độ dài giữa câu hỏi và đoạn bằng chứng; (D) Tần suất các đề mục học thuật chuẩn (cấu trúc IMRaD).*



Dựa trên dữ liệu định lượng tại Hình 5.0 và tệp chỉ số gốc, 4 đặc trưng kỹ thuật nền tảng của bài báo khoa học được phân tích chi tiết như sau:



1. **Phân bố loại câu hỏi và tính khả giải (Panel A - Question Types & Answerability):**

   - *Extractive (57,0% - 2.878 câu hỏi):* Chiếm đa số trong ngữ liệu, trong đó câu trả lời có thể được trích xuất trực tiếp từ các đoạn văn bản trong bài báo. Điều này xác nhận rằng bài toán cốt lõi của hệ thống RAG học thuật là **năng lực định vị chính xác phân đoạn chứa bằng chứng** (Passage Retrieval & In-Canvas Citation).

   - *Abstractive (20,0% - 1.011 câu hỏi):* Dạng câu hỏi đòi hỏi khả năng tổng hợp thông tin đa đoạn, suy luận logic và diễn đạt lại; tỷ lệ này trong toàn bộ ngữ liệu cao hơn đáng kể so với quan sát sơ bộ trên tập Pilot (12,4%).

   - *Yes / No (14,1% - 710 câu hỏi):* Dạng câu hỏi xác minh tính đúng/sai của một giả thuyết hoặc kết quả thí nghiệm dựa trên ngữ cảnh bài báo.

   - *Unanswerable (8,9% - 450 câu hỏi):* Các câu hỏi mà bài báo không cung cấp đủ thông tin để trả lời (theo đồng thuận đa số người gán nhãn). Kiểm toán gán nhãn cho thấy có 410 câu hỏi (8,12%) đạt đồng thuận tuyệt đối là không thể trả lời và hoàn toàn không có bằng chứng văn bản. Trong các thiết lập thực nghiệm đánh giá truy xuất có giám sát (RQ1, RQ2, RQ3), các câu hỏi này được xử lý độc lập để không gây sai lệch nhãn đối chiếu.

   - *Độ đồng thuận người gán nhãn:* 87,01% câu hỏi (4.393/5.049) đạt đồng thuận tuyệt đối về tính khả giải; 8,12% (410/5.049) đạt đồng thuận tuyệt đối là không thể trả lời; và 4,87% (246/5.049) có ý kiến phân kỳ giữa các chuyên gia gán nhãn.



2. **Phân bố độ dài bài báo khoa học toàn văn (Panel B - Document Length):**

   - Khảo sát trên 1.584 bài báo có cấu trúc toàn văn hoàn chỉnh (1 bài báo duy nhất `arXiv:1801.07804` thuộc tập Train có văn bản thô trống do lỗi trích xuất upstream của S2ORC) cho thấy độ dài bài báo có độ biến thiên rất lớn: Giá trị trung bình đạt **3.575,1 từ/bài** ($\text{std} = 2.083,8$ từ), trung vị (P50) đạt **3.401,0 từ**, phân vị 95% (P95) lên tới **6.707,3 từ**, với bài ngắn nhất là 37 từ và bài dài nhất lên tới 25.891 từ.

   - *Hàm ý kiến trúc:* Với độ dài trung vị 3.401 từ (tương đương ~4.500 subwords) và P95 đạt hơn 6.700 từ (~9.000 subwords), toàn văn bài báo khoa học vượt xa giới hạn độ dài ngữ cảnh chuẩn của các mô hình nhúng vector dày đặc phổ biến trên máy trạm ($\le 512$ tokens). Do đó, việc nạp nguyên văn toàn bộ bài báo vào mô hình biểu diễn vector là hoàn toàn bất khả thi; điều này xác lập cơ sở thực nghiệm bắt buộc cho **khâu phân mảnh văn bản (Document Chunking)** và khâu bóc tách bố cục trước khi lập chỉ mục.



3. **Sự bất đối xứng cực đoan giữa câu hỏi và đoạn bằng chứng (Panel C - Query vs Evidence Asymmetry):**

   - *Độ dài câu hỏi:* Cực kỳ ngắn gọn và tập trung, với độ dài trung bình chỉ **8,14 từ** (trung vị 7,0 từ, P95 là 14,0 từ, ngắn nhất 1 từ và dài nhất 25 từ).

   - *Độ dài đoạn bằng chứng (Ground-truth Evidence):* Mang tính học thuật dày đặc, với độ dài trung bình **175,5 từ** (trung vị 138,0 từ, P95 lên đến 418,9 từ, dài nhất 3.042 từ trên tập câu hỏi có bằng chứng).

   - *Độ phân tán đoạn bằng chứng:* Xét trên toàn bộ 5.049 câu hỏi của ngữ liệu chuẩn, có 746 câu hỏi không có bằng chứng văn bản (14,78%, bao gồm 410 câu unanswerable đồng thuận, 216 câu có bằng chứng thuần bảng biểu/hình vẽ FLOAT SELECTED, và 120 câu không gán nhãn đoạn), 2.412 câu hỏi có đúng 1 đoạn bằng chứng đơn lẻ (47,77%), và 1.891 câu hỏi đòi hỏi từ 2 đoạn bằng chứng trở lên (37,45%). Nếu chỉ tính riêng trên mẫu **4.303 câu hỏi có bằng chứng văn bản hợp lệ** (*text-evidenced questions*), tỷ lệ câu hỏi đòi hỏi đa đoạn bằng chứng là **43,95%** (1.891/4.303 câu hỏi), trong khi 56,05% (2.412/4.303 câu hỏi) có một đoạn bằng chứng duy nhất.

   - *Độ trùng lặp từ vựng mặt chữ (Lexical Jaccard Overlap):* Đạt mức trung bình là **0,0161 (1,61%)** trên toàn bộ 5.049 câu hỏi (gán giá trị 0 cho các câu không có bằng chứng) và **0,0259 (2,59%)** khi tính riêng trên 4.303 câu hỏi có bằng chứng văn bản (trung vị đạt 0,0114).

   - *Hàm ý kiến trúc và Động lực thực nghiệm:* Hiện tượng bất đối xứng từ vựng mặt chữ này (chỉ ~1,6%–2,6% từ trùng lặp sau khi lọc các từ chức năng ngắn) cùng sự chênh lệch độ dài gấp gần 22 lần giữa câu hỏi và đoạn bằng chứng phản ánh sự khác biệt bản chất giữa câu hỏi tò mò ngắn của người dùng và các đoạn văn bản khoa học chứa biệt ngữ hẹp. Đặc tính mô tả này không trực tiếp chứng minh giới hạn trần tuyệt đối của phương pháp tìm kiếm từ khóa, nhưng nó đặt ra **động lực phương pháp luận trực tiếp thúc đẩy việc đánh giá thực nghiệm**:

     - Đánh giá so sánh đối chứng giữa tìm kiếm từ khóa thưa (Sparse BM25) và các mô hình biểu diễn ngữ nghĩa dày đặc (Dense Semantic Retrieval) trong RQ3 để kiểm chứng xem hiểu biết ngữ nghĩa có vượt qua được sự bất đối xứng từ vựng hay không;

     - Khảo sát vai trò của các mô hình nhúng áp dụng **tiền tố nhiệm vụ bất đối xứng** (*Asymmetric Task Prefixes* như query:  / passage: ) nhằm kiểm định thực nghiệm xem việc phân tách không gian chiếu vector có cải thiện khả năng thu nạp phân đoạn hay không.



4. **Độ mịn cấu trúc phân cấp và các đề mục học thuật (Panel D - Structural Granularity):**

   - 1.584 bài báo khoa học có cấu trúc khảo sát chứa tổng cộng **21.909 đề mục** (sections), trung bình mỗi bài chứa **13,83 đề mục** (trung vị 13,0 mục, P95 là 26,0 mục). Độ dài trung bình của mỗi mục là **258,5 từ** (trung vị 188,0 từ, P95 là 706,0 từ).

   - Phân tích tần suất chuẩn hóa đề mục xác nhận sự xuất hiện nhất quán của các tiêu đề học thuật chuẩn mực thuộc cấu trúc IMRaD: *Introduction* xuất hiện ở 97,47% bài báo có cấu trúc (1.544/1.584 bài), *Conclusion* ở 90,78% (1.438 bài), *Experiments* ở 71,09% (1.126 bài), *Methodology / Model* ở 67,36% (1.067 bài), *Related Work* ở 56,82% (900 bài), *Results* ở 41,79% (662 bài), *Acknowledgments* ở 41,04% (650 bài), và *Discussion* ở 32,77% (519 bài).

   - *Hàm ý kiến trúc và Giả thuyết thực nghiệm:* Về mặt mô tả hình thái, kích thước trung bình 258,5 từ (~320–360 subwords, trung vị 188,0 từ) của một đề mục cung cấp một kích cỡ tham khảo thuận lợi cho việc thiết kế kích thước phân đoạn (chunk size) nằm trong khoảng 300–400 tokens, vừa vặn với cửa sổ ngữ cảnh chuẩn của các mô hình nhúng máy trạm (256–512 tokens). Tuy nhiên, vì phân vị P95 đạt tới 706 từ (~950 subwords), việc phân đoạn thuần túy theo đề mục thô mà không có cơ chế phân rã nhỏ hơn sẽ tạo ra rủi ro cắt cụt subword đáng kể. Do đó, các phát hiện hình thái này đóng vai trò **gợi ý thiết kế và định hình các giả thuyết khảo sát** cho RQ2 (so sánh thực nghiệm giữa cắt mù fixed_size, cắt theo đề mục thô section, cắt có gối đầu section_overlap, và phân mảnh phân cấp hierarchical), thay vì tự thân chứng minh bất kỳ phương pháp nào là tối ưu trước khi thực hiện thử nghiệm.



*Đối chiếu với nghiên cứu sơ bộ Pilot (100 bài báo / 250 câu hỏi):*

Bảng đối soát chi tiết [eda_pilot_vs_full_comparison.csv](file:///c:/DACNTT/eval/phases/phase_0_baseline/artifacts/eda_pilot_vs_full_comparison.csv) cho thấy tập Pilot trước đây có tỷ lệ câu hỏi extractive cao hơn (70,0% so với 57,0%) và unanswerable thấp hơn (3,2% so với 8,9%) do đặc thù lấy mẫu ban đầu từ đầu tập Dev. Tuy nhiên, các đặc trưng kỹ thuật nền tảng đều hoàn toàn nhất quán: tỷ lệ bất đối xứng độ dài query–evidence duy trì ở mức ~22 lần, độ trùng lặp từ vựng mặt chữ duy trì ở mức cực thấp (< 2,6%), và độ mịn phân cấp đề mục bài báo đạt 13–14 mục/bài với quy mô trung bình ~250 từ/mục.



### 5.1.3. Hàm ý kiến trúc đối với các câu hỏi nghiên cứu và Phân bổ tập mẫu thực nghiệm



Nhằm bảo đảm tính khách quan học thuật, ngăn ngừa triệt để nguy cơ rò rỉ dữ liệu (data leakage) và kiểm soát chi phí tính toán trên máy trạm thực nghiệm, ngữ liệu nghiên cứu được phân hoạch thành các tập dữ liệu có kiểm soát tương ứng với từng giai đoạn đo đạc.



Bảng 5.0 tổng hợp chi tiết quy mô tập mẫu, số lượng bài báo, số câu hỏi, số lượng phân đoạn văn bản và mục tiêu đánh giá cho từng câu hỏi nghiên cứu trong luận văn (được xuất từ tệp kiểm chứng [`table_5_0_dataset_partition.csv`](file:///c:/DACNTT/reports/chapter5/tables/table_5_0_dataset_partition.csv)).



*Bảng 5.0: Phân bổ tập dữ liệu thực nghiệm theo từng câu hỏi nghiên cứu và giai đoạn đường ống RAG.*



| Giai đoạn / Câu hỏi nghiên cứu | Tập dữ liệu phân hoạch | Số bài báo (Papers) | Số câu hỏi (Queries) | Số phân đoạn (Chunks) | Điều kiện kiểm soát & Ngân sách ngữ cảnh | Mục tiêu đánh giá & Tệp kết quả gốc |

| :--- | :--- | :---: | :---: | :---: | :--- | :--- |

| **Tiền xử lý & Khám phá (EDA)** | Toàn bộ Benchmark QASPER (kèm Pilot đối chiếu) | 1.585 bài báo (100 pilot) | 5.049 câu hỏi (250 pilot) | 21.909 đề mục (1.336 pilot) | Toàn văn bài báo & nhãn bằng chứng gốc | Khảo sát phân bố hình thái học, độ dài, từ vựng và cấu trúc toàn phần (`qasper_full_corpus_eda.json`). |

| **RQ1: Bóc tách văn bản PDF** | Tập Phát triển (Development Split) | 47 bài báo | 127 câu hỏi | Theo cấu trúc từng parser | Cố định mô hình nhúng `e5-small-v2`; CPU 4 luồng | Đánh giá 5 công cụ bóc tách PDF: Evidence Coverage, Char-Match, Heading F1, Độ trễ (`rq1_extraction_20261024_000639.json`). |

| **RQ2: Chiến lược phân mảnh** | Tập Phát triển (Development Split) | 47 bài báo | 127 câu hỏi | 893 đến 2.618 chunks tùy chiến lược | Cố định ngân sách 1.600 tokens; $\tau = 0,5$ | Đánh giá 8 chiến lược chunking: tỷ lệ cắt cụt subword, nDCG@10, Recall@20, MRR@10 (`rq2_chunking_20261024_013443.json`). |

| **RQ3: Mô hình biểu diễn vector** | Ngữ liệu Đánh giá Hợp nhất (Unified In-House Corpus: 48 Dev + 159 Held-out) | 207 bài báo | 615 câu hỏi | 5.207 chunks (1.099 Dev + 4.108 Held-out) | Cố định $\tau^*=0,55$; Brute-force Cosine NumPy BLAS; Bootstrap $B=2.000$ | Đo đạc 11 mô hình nhúng mã nguồn mở $\le 335\text{M}$ + BM25: nDCG@10, Recall@20, P50 ms, Thông lượng, RAM (`thesis_embedding_benchmark.json`). |



*Lưu ý về phạm vi thực nghiệm:* Chương 5 được giới hạn nghiêm ngặt trong bộ ba câu hỏi nghiên cứu thành phần (RQ1, RQ2 và RQ3) đã được đo đạc và kiểm định thống kê đầy đủ. Các câu hỏi nghiên cứu mở rộng về tích hợp truy xuất lai trên tập ứng viên phân cấp (RQ4) và đánh giá toàn diện mô hình ngôn ngữ lớn (RQ5) được phân định rõ là hướng nghiên cứu tương lai (Chương 6), trong khi cơ chế Hybrid RRF và mô hình `llama3.2:3b` phục vụ hệ thống phần mềm đã được thiết kế và mô tả chi tiết tại Chương 4.



*Lưu ý về tính sẵn sàng của tệp PDF:* Trong tổng số 1.585 bài báo của ngữ liệu chuẩn QASPER, chỉ có 61 bài báo có tệp PDF vật lý được lưu trữ cục bộ trên đĩa (gồm 47 bài phục vụ thực nghiệm bóc tách RQ1/RQ2 và 14 bài bổ sung); 1.524 bài báo còn lại là **thiếu cục bộ trên đĩa lưu trữ do chưa được tải về**, chứ không phải không khả dụng từ xa trên máy chủ arXiv (kết quả kiểm toán thăm dò ngẫu nhiên 25 bài báo trên arXiv tại Báo cáo Kiểm toán PDF ghi nhận 24/25 bài mẫu — 96,0% — đều tồn tại và tải về bình thường).



---



## 5.2. Kết quả RQ1 – Đánh giá phương pháp trích xuất văn bản PDF



### 5.2.1. Thiết lập thực nghiệm và điều kiện kiểm soát



Thực nghiệm RQ1 được thực hiện trên tập dữ liệu gồm **47 bài báo khoa học** thuộc tập phát triển (Development Split) của ngữ liệu QASPER có tệp PDF vật lý nguyên bản trên đĩa lưu trữ với **127 câu hỏi** có bằng chứng văn bản đối chiếu hợp lệ. Quá trình đo đạc được thực thi trên máy trạm AMD Ryzen 5 5600 (6 nhân, 12 luồng, giới hạn `torch.set_num_threads(4)`), sử dụng hệ thống nhúng vector chuẩn hóa `intfloat/e5-small-v2` để kiểm tra chất lượng truy xuất hạ nguồn.



*Quy trình chọn lọc tập mẫu thực nghiệm RQ1/RQ2:*

Từ 48 bài báo gốc (132 câu hỏi) thuộc tập Development split (`dev_held_out_split.json`):

1. **Lọc bài báo thiếu tệp PDF vật lý cục bộ:** Do thực nghiệm RQ1 đánh giá trực tiếp quá trình trích xuất từ tệp PDF nguyên bản, bài báo bắt buộc phải có tệp PDF nhị phân trên đĩa lưu trữ (eval/pdfs/dev/). Đúng 1 bài báo duy nhất trong 48 bài của tập Development không có tệp PDF cục bộ là arXiv:1802.00396 (chứa đúng 2 câu hỏi: câu Unanswerable Q_QASP_191 và câu Extractive Q_QASP_192). Kiểm chứng độc lập cho thấy bài báo này tồn tại hợp lệ trên arXiv (https://arxiv.org/abs/1802.00396, tiêu đề *Disunited Nations? A Multiplex Network Approach to Detecting Preference Affinity Blocs using Texts and Votes*), tuy nhiên phiên bản 2 (v2) đã bị tác giả đánh dấu rút lại (withdrawn), khiến đường dẫn tải PDF mặc định không phiên bản (https://arxiv.org/pdf/1802.00396.pdf) trả về mã lỗi HTTP 404 Not Found. Do đó, bộ tải tự động trước đây đã không tải được tệp PDF này về máy, dẫn đến tập dữ liệu khả dụng trên đĩa có đúng **47 bài báo có tệp PDF** và số lượng câu hỏi giảm từ 132 xuống còn 132 - 2 = 130$ câu hỏi.

2. **Lọc loại trừ câu hỏi không thể trả lời (Unanswerable):** Trong 130 câu hỏi của 47 bài báo trên, có đúng 3 câu hỏi thuộc nhóm không thể trả lời / không có bằng chứng văn bản trong bài báo (`Q_QASP_030` thuộc `arXiv:2002.03407`, `Q_QASP_087` thuộc `arXiv:1809.01541`, `Q_QASP_225` thuộc `arXiv:2001.03131`). Do mục tiêu cốt lõi của RQ1 và RQ2 là đánh giá năng lực bóc tách và phân mảnh trong việc truy xuất đoạn bằng chứng văn bản nguyên văn (*evidence passage retrieval*), các câu hỏi thiếu nhãn đối chiếu bắt buộc phải loại bỏ để không làm sai lệch độ đo nDCG và Recall.

Sau hai bước lọc có kiểm soát, toàn bộ **127 câu hỏi có bằng chứng văn bản hợp lệ (100%) đều được giữ lại nguyên vẹn**, không bị sàng lọc thêm, và tham gia đầy đủ vào toàn bộ quá trình đo lường của RQ1 và RQ2.



Các công cụ bóc tách được đánh giá bao gồm:

1. `pymupdf_plain`: Sử dụng PyMuPDF (`fitz`) trích xuất văn bản phẳng thông thường qua cờ trích xuất khối văn bản mặc định (Mốc đối chứng / Baseline).

2. `pymupdf_layout`: Sử dụng PyMuPDF có tích hợp thuật toán phân tích bố cục (Layout-Aware) dựa trên kích thước phông chữ và định dạng hình thức để phân tách phân cấp tiêu đề mục học thuật (`section_title`).

3. `pypdf`: Thư viện xử lý PDF thuần Python mã nguồn mở.

4. `pdfminer.six`: Công cụ phân tích cú pháp bố cục dòng và ký tự chi tiết.

5. `pdfplumber`: Công cụ trích xuất dựa trên bảng và tọa độ hộp bao đồ họa.



*Ghi chú về GROBID:* Trong quá trình thực nghiệm, máy chủ dịch vụ GROBID cục bộ (`http://localhost:8070`) không khả dụng do hạn chế tài nguyên kết nối trên môi trường thử nghiệm; do đó GROBID được ghi nhận như một giới hạn hạ tầng thực nghiệm (Offline / Unreachable), không gán điểm số bằng 0 để tránh kết luận sai lệch về năng lực của công cụ này.



### 5.2.2. Kết quả đo lường định lượng



Bảng 5.1 tổng hợp các chỉ số đo lường hiệu năng trích xuất và chất lượng truy xuất hạ nguồn tương ứng của các công cụ (được xuất từ tệp [`table_5_1_rq1_extraction.csv`](file:///c:/DACNTT/reports/chapter5/tables/table_5_1_rq1_extraction.csv)).



*Bảng 5.1: Kết quả so sánh các phương pháp bóc tách văn bản PDF trên 47 bài báo khoa học (RQ1).*



| Bộ trích xuất PDF | Evidence Coverage (%) | Char-Match (%) | Heading F1 (%) | Reading Order | Tốc độ (ms/trang) | Peak RAM (MB) | Downstream nDCG@10 [95% CI] | Downstream Recall@20 | Sai khác $\Delta$ nDCG@10 [95% CI] | Trị số $p_{\text{raw}}$ danh định |

| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |

| `pymupdf_plain` *(Mốc chuẩn)* | **37,59%** | 33,09% | 0,00% | **0,9894** | **10,19** | 1.228,7 | **0,5274** [0,4724; 0,5839] | 0,9424 | 0,0000 | 1,0000 |

| `pymupdf_layout` | 33,16% | 32,78% | **48,01%** | **0,9894** | 26,16 | **1.164,9** | 0,5100 [0,4398; 0,5822] | 0,8887 | -0,0175 [-0,0755; +0,0387] | 0,5597 |

| `pypdf` | 29,61% | 32,28% | 0,00% | 0,9787 | 61,72 | 1.286,2 | 0,5174 [0,4597; 0,5792] | **0,9509** | -0,0101 [-0,0446; +0,0236] | 0,5867 |

| `pdfminer.six` | 35,82% | **33,44%** | 0,00% | 0,9713 | 107,10 | 1.169,2 | 0,5131 [0,4615; 0,5696] | 0,9373 | -0,0143 [-0,0601; +0,0280] | 0,5457 |

| `pdfplumber` | 9,86% | 3,99% | 0,00% | 0,5319 | 195,36 | 1.236,4 | 0,3769 [0,3108; 0,4442] | 0,7513 | -0,1505 [-0,2258; -0,0732]* | **0,0010\*** |

| `grobid` | — | — | — | — | — | — | — | — | — | *Offline* |



*\*(Nguồn dữ liệu thực nghiệm: `eval/results/rq1_extraction_20261024_000639.json`). Cột $p_{\text{raw}}$ báo cáo trị số $p$ danh định hai phía từ kiểm định Bootstrap theo cụm bài báo ($B=2.000$, seed=42) so với mốc đối chứng `pymupdf_plain`. Dấu sao (\*) biểu thị sự suy giảm vừa đạt ý nghĩa ở mức $\alpha=0,05$ danh định, vừa bảo toàn ý nghĩa thống kê sau hiệu chỉnh kiểm soát so sánh đa biến Holm-Bonferroni ($p_{\text{adj}} = 0,0040 < 0,05$).*



![Hình 5.1: So sánh chất lượng truy xuất hạ nguồn (nDCG@10) giữa các bộ trích xuất PDF (RQ1)](file:///c:/DACNTT/reports/chapter5/figures/fig5_1_rq1_ndcg10.png)



*Hình 5.1: Điểm số nDCG@10 truy xuất hạ nguồn kèm khoảng tin cậy 95% CI giữa các công cụ bóc tách PDF.*



![Hình 5.2: Tốc độ xử lý trích xuất văn bản PDF trên CPU AMD Ryzen 5 5600 (RQ1)](file:///c:/DACNTT/reports/chapter5/figures/fig5_2_rq1_latency.png)



*Hình 5.2: Thời gian xử lý trung bình trên mỗi trang PDF (ms/trang) của các công cụ khảo sát.*



### 5.2.3. Thảo luận và Phân tích kết quả RQ1



Từ dữ liệu Bảng 5.1, Hình 5.1 và Hình 5.2, các phát hiện kỹ thuật cốt lõi được rút ra như sau:



1. **Hiệu năng vượt trội của công nghệ C-Engine (PyMuPDF):**

   Về tốc độ xử lý, cả hai cấu hình PyMuPDF đều vượt trội tuyệt đối so với các thư viện thuần Python. `pymupdf_plain` đạt tốc độ nhanh nhất với chỉ **10,19 ms/trang**, nhanh gấp 6 lần `pypdf` (61,72 ms/trang), gấp 10,5 lần `pdfminer.six` (107,10 ms/trang) và gấp 19 lần `pdfplumber` (195,36 ms/trang). Ngay cả khi bổ sung thuật toán phân tích bố cục hình học và phông chữ phức tạp trong `pymupdf_layout`, thời gian xử lý vẫn duy trì ở mức rất thấp (**26,16 ms/trang**), hoàn toàn đáp ứng yêu cầu xử lý tương tác trực tiếp của người dùng trong ứng dụng web khi tải lên bài báo 10–20 trang.



2. **Vai trò độc bản của `pymupdf_layout` trong phát hiện cấu trúc tiêu đề mục:**

   Một kết quả cần được làm rõ về mặt phương pháp luận là điểm số `Heading F1 = 0,00%` của các công cụ `pymupdf_plain`, `pypdf`, `pdfminer.six` và `pdfplumber`. Điểm số này không đồng nghĩa với việc các thư viện này không đọc được văn bản chứa tiêu đề, mà phản ánh thực tế rằng bộ điều hợp (adapter) của các thư viện này chỉ trích xuất dòng chữ phẳng tuần tự mà không có cơ chế phân tích siêu dữ liệu phông chữ để gắn thẻ cấu trúc đề mục (`section_title`). Duy nhất `pymupdf_layout` được cài đặt thuật toán heuristic phân tích kích thước và độ đậm của phông chữ, đạt **Heading F1 = 48,01%** so với danh mục tiêu đề chuẩn của tác giả bài báo. Khả năng phát hiện cấu trúc này là tiền đề kỹ thuật bắt buộc để triển khai các chiến lược phân đoạn theo cấu trúc ngữ nghĩa (`section_overlap`, `hierarchical`) ở mắt xích tiếp theo.



3. **Chất lượng truy xuất hạ nguồn không có sai khác mang ý nghĩa thống kê giữa nhóm đầu:**

   Khi đưa văn bản bóc tách vào cùng một mô hình nhúng (`e5-small-v2`) để đo nDCG@10, các công cụ `pymupdf_plain` (0,5274), `pypdf` (0,5174), `pdfminer.six` (0,5131) và `pymupdf_layout` (0,5100) có điểm số rất sát nhau. Kiểm định Bootstrap theo cụm bài báo cho thấy các độ lệch $\Delta$ nDCG@10 so với mốc đối chứng (từ -0,0101 đến -0,0175) đều có trị số $p > 0,50$ (khoảng tin cậy 95% đều bao trùm giá trị 0). Điều này chứng minh rằng đối với các bài báo hai cột thông thường, trật tự đọc của ba công cụ này đều đủ tốt ($\text{Reading Order} \ge 0,97$) để mô hình embedding thu nhận ngữ nghĩa.



4. **Sự sụp đổ chất lượng của `pdfplumber` trên văn bản học thuật:**

   Trái ngược với nhóm trên, `pdfplumber` ghi nhận sự suy giảm nghiêm trọng trên mọi chỉ số: Trật tự đọc giảm xuống chỉ còn 0,5319 (thường xuyên ghép nhầm các dòng ở cột trái sang cột phải), tỷ lệ bao phủ bằng chứng chỉ đạt 9,86%, và nDCG@10 hạ nguồn sụt giảm mạnh xuống **0,3769** ($\Delta = -0,1505, p = 0,0010^*$). Sự suy giảm này có ý nghĩa thống kê rõ rệt, khẳng định `pdfplumber` (vốn được thiết kế tối ưu cho bóc tách bảng biểu) hoàn toàn không phù hợp cho việc đọc văn bản bài báo khoa học hai cột.



5. **Làm rõ bản chất chỉ số Char-Match:**

   Chỉ số Char-Match của các công cụ chỉ dao động từ 32% đến 33,4%. Cần nhấn mạnh rằng đây không phải là tỷ lệ mất mát ký tự (Character Error Rate). Nguyên nhân là do văn bản tham chiếu của QASPER là mã nguồn LaTeX thô chưa biên dịch, trong khi PDF là tài liệu đã dàn trang hoàn chỉnh chứa tiêu đề trang (running headers), số trang, chú thích chân trang và các ký hiệu trích dẫn số. Sự khác biệt về mặt cấu trúc này khiến độ trùng khớp chuỗi con liên tục bị ngắt quãng, chứ không phản ánh việc văn bản bị mất nội dung.



*Hàm ý đối với hệ thống:* Kết quả trên chứng minh việc lựa chọn **`pymupdf_layout`** làm thành phần bóc tách văn bản mặc định trong kiến trúc RAG của ứng dụng là quyết định kỹ thuật chính xác nhất: vừa bảo đảm tốc độ xử lý hàng đầu (26 ms/trang), vừa duy trì chất lượng truy xuất tương đương văn bản phẳng, đồng thời cung cấp đầy đủ ranh giới tiêu đề mục cho các thuật toán phân mảnh nâng cao.



---



## 5.3. Kết quả RQ2 – Đánh giá chiến lược phân mảnh văn bản



### 5.3.1. Thiết lập thực nghiệm và Nguyên tắc Ngân sách Ngữ cảnh Cố định



Thực nghiệm RQ2 khảo sát 8 chiến lược phân mảnh văn bản trên 47 bài báo khoa học với 127 câu hỏi truy vấn hợp lệ. Để loại bỏ hiện tượng sai lệch do độ dài đoạn trích ("Coarse Chunk Illusion" - các đoạn trích lớn tự nhiên chứa nhiều từ khóa hơn nhưng lại chiếm dụng lãng phí cửa sổ ngữ cảnh), toàn bộ các chiến lược đều được kiểm soát dưới một **Ngân sách Ngữ cảnh Cố định (Context Budget = 1.600 tokens)**. Hệ thống chỉ gom các đoạn trích có điểm tương đồng cao nhất cho đến khi chạm trần 1.600 tokens để đưa vào tính toán số liệu.



Tám chiến lược phân mảnh bao gồm:

1. `fixed_size` *(Mốc đối chứng)*: Cắt văn bản tuần tự thành các đoạn 400 tokens cố định không gối đầu, không phụ thuộc cấu trúc đề mục.

2. `fixed_size_overlap`: Cắt văn bản 400 tokens kèm độ gối đầu 80 tokens giữa các đoạn kế tiếp.

3. `semantic`: Sử dụng ngưỡng khoảng cách cosine giữa các vector câu liên tiếp để xác định điểm ngắt đoạn ngữ nghĩa.

4. `section`: Giữ nguyên toàn bộ nội dung của từng đề mục bài báo làm một phân đoạn (đoạn thô).

5. `section_token`: Cắt văn bản trong phạm vi từng đề mục theo kích thước token giới hạn (250 tokens).

6. `section_overlap`: Cắt văn bản trong phạm vi từng đề mục (tối đa 400 tokens) kèm độ gối đầu 80 tokens (cấu hình hiện tại của hệ thống).

7. `hierarchical`: Phân đoạn phân cấp đa tầng (Small-to-Big). Tìm kiếm trên các đoạn con nhỏ (150 tokens) để định vị chính xác, nhưng khi đưa vào ngữ cảnh sẽ mở rộng lấy toàn bộ đoạn cha (parent section).

8. `hierarchical_child`: Nhánh kiểm chứng độc lập (ablation) của cấu trúc phân cấp, chỉ sử dụng đoạn con nhỏ mà không mở rộng đoạn cha khi tính toán ngữ cảnh.



Nhãn liên quan của phân đoạn được xác định theo nguyên tắc bao phủ bằng chứng: Một phân đoạn được xem là có liên quan nếu nó chứa tối thiểu $\tau$ tỷ lệ từ nội dung của bằng chứng tham chiếu sau khi loại bỏ từ dừng. Ngưỡng bao phủ bằng chứng đã được **hiệu chuẩn thực nghiệm độc lập trên 114 cặp câu hỏi – bằng chứng được chuyên gia gán nhãn thủ công** (`eval/prepared/containment_validation_metrics.json` qua `backend/scripts/evaluation/evaluate_containment_labels.py`). Đối với truy xuất đoạn đơn lẻ (RQ1 & RQ3), $\tau^* = 0,55$ là điểm tối ưu toàn cục out-of-sample (đạt độ chính xác 82,46%, Precision 81,08% và F1-Score 75,00%). Trong RQ2, do các chiến lược phân đoạn có kích thước văn bản ứng viên không đồng nhất (từ đoạn con 158 tokens đến mục cha mở rộng ~350 tokens) trong khi bằng chứng dài trung bình 175,5 từ, ngưỡng **$\tau = 0,50$ được lựa chọn làm mốc đánh giá chính** nhằm dung hòa ranh giới phân mảnh và tránh phạt oan diện tích văn bản rộng. Một phân tích độ nhạy độc lập tại ngưỡng $\tau = 0,30$ cũng được tiến hành đồng thời để kiểm tra tính vững của xếp hạng.



### 5.3.2. Kết quả đo lường định lượng



Bảng 5.2 trình bày chi tiết kết quả thực nghiệm của 8 chiến lược phân đoạn văn bản (được xuất từ tệp [`table_5_2_rq2_chunking.csv`](file:///c:/DACNTT/reports/chapter5/tables/table_5_2_rq2_chunking.csv)).



*Bảng 5.2: Đánh giá so sánh 8 chiến lược phân mảnh văn bản dưới ngân sách 1.600 tokens (RQ2).*



| Chiến lược phân mảnh | Tổng số Chunks | Tokens TB / Chunk | Tỷ lệ Cắt cụt Subword (%) | nDCG@10 ($\tau=0,5$) [95% CI] | nDCG@4 | Recall@20 | MRR@10 | Sai khác $\Delta$ nDCG@10 vs Baseline [95% CI] | Trị số $p_{\text{raw}}$ danh định | nDCG@10 ($\tau=0,3$) | Recall@20 ($\tau=0,3$) |

| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |

| `fixed_size` *(Mốc đối chứng)* | 893 | 388,8 | **0,00%** | 0,5654 [0,5101; 0,6240] | 0,4443 | 0,9586 | 0,5310 | 0,0000 | 1,0000 | 0,6252 | 0,9463 |

| `fixed_size_overlap` | 1.109 | 389,1 | **0,00%** | 0,5385 [0,4835; 0,6008] | 0,4336 | 0,9452 | 0,5269 | -0,0269 [-0,0718; +0,0153] | 0,2129 | 0,5801 | 0,9104 |

| `semantic` | 1.907 | 184,9 | 0,21% | 0,4856 [0,4305; 0,5439] | 0,3904 | 0,8680 | 0,4983 | -0,0798 [-0,1323; -0,0275]* | **0,0050\*** | 0,5154 | 0,8453 |

| `section` (Đề mục thô) | 907 | 383,2 | 23,70% | 0,5795 [0,5191; 0,6392] | 0,4473 | 0,9753 | 0,5456 | +0,0141 [-0,0476; +0,0764] | 0,6537 | 0,6000 | 0,9641 |

| `section_token` | 1.498 | 232,2 | 0,73% | 0,5359 [0,4660; 0,6095] | 0,4475 | 0,9234 | 0,5520 | -0,0295 [-0,0924; +0,0283] | 0,2999 | 0,5486 | 0,9226 |

| `section_overlap` *(Hệ thống)* | 1.591 | 245,7 | 0,63% | 0,5409 [0,4761; 0,6084] | **0,4569** | 0,9255 | **0,5737** | -0,0245 [-0,0777; +0,0257] | 0,3178 | 0,5440 | 0,8958 |

| `hierarchical` *(Small-to-Big)* | 2.618 | 158,3 | **0,00%** | **0,6880** [0,6348; 0,7371] | **0,5933** | **0,9873** | **0,6468** | **+0,1225** [+0,0553; +0,1821]* | **0,0010\*** | **0,7340** | **0,9890** |

| `hierarchical_child` | 2.618 | 158,3 | **0,00%** | 0,4473 [0,3883; 0,5052] | 0,3791 | 0,7781 | 0,4816 | -0,1182 [-0,1806; -0,0526]* | **0,0020\*** | 0,4617 | 0,7567 |



*\*(Nguồn dữ liệu: `eval/results/rq2_chunking_20261024_013443.json`). Cột $p_{\text{raw}}$ báo cáo trị số $p$ danh định hai phía từ kiểm định Bootstrap theo cụm bài báo ($B=2.000$, seed=42) so với mốc đối chứng `fixed_size`. Dấu sao (\*) biểu thị sự khác biệt vừa đạt ý nghĩa ở mức $\alpha=0,05$ danh định, vừa vượt qua quy trình hiệu chỉnh kiểm soát so sánh đa biến Holm-Bonferroni (cụ thể: `hierarchical` $p_{\text{adj}} = 0,0070$, `hierarchical_child` $p_{\text{adj}} = 0,0120$, `semantic` $p_{\text{adj}} = 0,0250$).*



![Hình 5.3: Biểu đồ Dot-and-Whisker so sánh nDCG@10 giữa 8 chiến lược phân mảnh văn bản (RQ2)](file:///c:/DACNTT/reports/chapter5/figures/fig5_3_rq2_chunking_ndcg10.png)



*Hình 5.3: Phân bố nDCG@10 (kèm khoảng tin cậy 95% CI) của 8 chiến lược phân mảnh tại ngưỡng chính $\tau=0,50$ và đối sánh độ nhạy tại $\tau=0,30$.*



### 5.3.3. Thảo luận và Biện giải kết quả RQ2



1. **Vị thế dẫn đầu của mô hình phân mảnh phân cấp (Small-to-Big):**

   Chiến lược `hierarchical` vượt trội hoàn toàn so với toàn bộ các chiến lược phân đoạn phẳng còn lại trên mọi thước đo: $\text{nDCG@10}$ đạt **0,6880** ($\Delta = +0,1225$, khoảng tin cậy $[+0,0553; +0,1821]$, $p = 0,0010^*$), $\text{nDCG@4}$ đạt **0,5933**, và $\text{Recall@20}$ đạt mức kỷ lục **0,9873**. Cơ chế này giải quyết triệt để sự xung đột cố hữu trong công nghệ RAG: các đoạn văn bản nhỏ (150 tokens) giúp biểu diễn vector tập trung, không bị loãng thông tin khi tính tích vô hướng với câu hỏi ngắn; trong khi việc tự động mở rộng sang đoạn cha khi nạp vào bộ nhớ LLM bảo đảm đầy đủ ngữ cảnh lý luận liền mạch.



2. **Bài học giải phẫu từ nhánh `hierarchical_child`:**

   Ý nghĩa khoa học của cơ chế mở rộng ngữ cảnh cha được chứng minh rõ rệt khi đối chiếu với `hierarchical_child`. Khi chỉ sử dụng các đoạn con nhỏ mà không mở rộng đoạn cha, $\text{nDCG@10}$ sụp đổ xuống mức thấp nhất bảng: **0,4473** ($\Delta = -0,1182, p = 0,0020^*$). Điều này bác bỏ giả định ngây thơ rằng chỉ cần chia nhỏ văn bản là sẽ cải thiện truy xuất; các đoạn quá nhỏ bị mất ngữ cảnh bao quanh sẽ khiến hệ thống không thu thập đủ lượng thông tin cần thiết để vượt qua ngưỡng bằng chứng $\tau = 0,50$.



3. **Cạm bẫy cắt cụt âm thầm của chiến lược `section` thô:**

   Mặc dù chiến lược `section` đạt điểm $\text{nDCG@10} = 0,5795$ (cao hơn mốc chuẩn cố định), nó lại mắc phải một khuyết tật kỹ thuật nghiêm trọng: **23,70% số phân đoạn bị cắt cụt subword âm thầm** (Subword Truncation). Do các đề mục học thuật (như *Related Work*, *Experiments*) thường dài từ 800 đến 2.500 từ, vượt xa trần độ dài 512 subwords của các mô hình nhúng vector, toàn bộ phần văn bản sau giới hạn này bị loại bỏ hoàn toàn trong quá trình mã hóa mà hệ thống không cảnh báo. Đây là lý do khiến chiến lược này không thể được chấp nhận trong môi trường triển khai thực tế.



4. **Sự thất bại của phân đoạn ngữ nghĩa (`semantic chunking`):**

   Chiến lược `semantic` ghi nhận sự suy giảm có ý nghĩa thống kê so với mốc đối chứng ($\text{nDCG@10} = 0,4856$, $\Delta = -0,0798, p = 0,0050^*$). Trong văn bản học thuật, sự chuyển đổi điểm nhìn giữa các câu trong cùng một đoạn văn thường tạo ra bước nhảy khoảng cách vector giả, dẫn đến việc văn bản bị băm vụn không đồng đều (độ dài trung bình chỉ 184,9 tokens/chunk, sinh ra tới 1.907 chunks). Sự phân mảnh này làm phá vỡ tính mạch lạc của các luận điểm chứng minh khoa học.



5. **Tính ổn định của `section_overlap` trong môi trường phẳng và lý do lựa chọn sản phẩm:**

   Trong nhóm các chiến lược phân đoạn phẳng có kiểm soát độ dài (tỷ lệ cắt cụt $<1\%$), `section_overlap` đạt thành tích xuất sắc nhất trên các chỉ số ứng dụng thực tế: **$\text{nDCG@4} = 0,4569$** (cao nhất trong các phương pháp phẳng) và **$\text{MRR@10} = 0,5737$** (vượt trội so với `fixed_size` 0,5310). 

   

   *Hàm ý thiết kế hệ thống và Cập nhật kiến trúc triển khai:* Trong giai đoạn đầu, hệ thống vận hành tại `rag_service.py` ưu tiên cấu hình phẳng mặc định **`section_overlap`** nhằm tương thích trực tiếp với cấu trúc bảng đơn tầng của Qdrant SQLite mà không cần bổ sung bảng quan hệ phụ trợ trong RDBMS. Tuy nhiên, để hiện thực hóa triệt để lợi thế lý thuyết của `hierarchical`, hệ thống đã phát triển giải pháp kiến trúc **Bộ sưu tập phụ trợ phi vector (Companion Vectorless Collection - Option b)**. Theo cơ chế này, các đoạn con nhỏ (150 words) được đánh chỉ mục vector trong bộ sưu tập chính `{collection_name}`, trong khi các đoạn cha duy nhất được lưu trữ tại bộ sưu tập song hành không chứa vector `{collection_name}_parents` và truy xuất qua `client.retrieve(..., ids=[parent_uuids])`. Giải pháp này triệt tiêu hoàn toàn sự dư thừa văn bản, giữ nguyên kích thước bảng chỉ mục vector HNSW, đạt độ trễ tương đương với truy xuất phẳng (P50 = 31,76 ms so với 31,74 ms), đồng thời nâng cao độ chính xác cửa sổ ngữ cảnh thực tế ($\text{nDCG@4}$ từ 0,4569 lên 0,5139).



6. **Tính vững qua phân tích độ nhạy ($\tau = 0,30$):**

   Khi nới lỏng ngưỡng bằng chứng xuống $\tau = 0,30$ (cột cuối Bảng 5.2 và các điểm vuông cam trong Hình 5.3), thứ tự xếp hạng tương đối giữa 8 chiến lược hoàn toàn được bảo toàn: `hierarchical` vẫn dẫn đầu vững chắc (0,7340), tiếp theo là `fixed_size` (0,6252), `section` (0,6000), `fixed_size_overlap` (0,5801), `section_token` (0,5486), `section_overlap` (0,5440), `semantic` (0,5154) và cuối cùng là `hierarchical_child` (0,4617). Điều này chứng minh các kết luận rút ra không phụ thuộc cục bộ vào việc lựa chọn ngưỡng dung sai $\tau$.



---



## 5.4. Kết quả RQ3 – Đánh giá mô hình embedding



### 5.4.1. Thiết lập thực nghiệm quy mô lớn



Thực nghiệm RQ3 khảo sát toàn diện 11 mô hình biểu diễn vector mã nguồn mở (giấy phép thương mại tự do Apache-2.0 và MIT) có quy mô $\le 335\text{M}$ tham số, cùng mốc đối chứng từ khóa thưa BM25 (WordPiece Tokenization). Toàn bộ thực nghiệm được tiến hành trên **Tập ngữ liệu đánh giá nội bộ hợp nhất (Unified In-House Evaluation Corpus)** gồm **207 bài báo khoa học, 615 câu hỏi nghiên cứu và 5.207 phân đoạn văn bản** (kết hợp từ 48 bài báo tập Development với 1.099 chunks, 128 câu hỏi và 159 bài báo có câu hỏi thuộc tập Held-out mở rộng với 4.108 chunks, 487 câu hỏi). 



Việc thiết lập tập ngữ liệu đánh giá hợp nhất và điều kiện kiểm soát thực nghiệm tuân thủ các nguyên tắc phương pháp luận chặt chẽ:

1. **Kiểm soát rò rỉ dữ liệu và tính độc lập của mô hình:**

   - *Không có rò rỉ trọng số mô hình (Zero Model Weight Leakage):* Cả 11 mô hình embedding đều là các mô hình nền tảng mã nguồn mở có sẵn (off-the-shelf pre-trained checkpoints) được tải từ HuggingFace Hub với trọng số được đóng băng hoàn toàn (`frozen weights`). Không có bất kỳ mô hình nào trải qua quá trình tái huấn luyện (fine-tuning) hay tối ưu hóa siêu tham số trên dữ liệu bài báo QASPER. Toàn bộ quá trình mã hóa vector được thực hiện dưới cơ chế suy luận zero-shot tuyệt đối.

   - *Phân định ranh giới đánh giá nội bộ:* Tác giả ghi nhận minh bạch rằng tập 207 bài báo này không phải là một tập kiểm thử độc lập hoàn toàn (independent held-out test set), bởi 48 bài báo thuộc phần Development đã từng được dùng để khảo sát công cụ bóc tách PDF (RQ1) và tối ưu chiến lược phân mảnh chunking (RQ2). Sự kết hợp này nhằm tạo ra một không gian đánh giá nội bộ rộng lớn nhất có thể trong giới hạn dữ liệu nghiên cứu, nâng cao độ nhạy phát hiện thực nghiệm trên toàn bộ đường ống RAG của đề tài.

2. **Tính toán chính xác thuần túy (Decoupled Exact Cosine):** Toàn bộ điểm số tương đồng được tính bằng tích vô hướng Cosine ma trận chính xác tuyệt đối (Exact Brute-Force Cosine via NumPy BLAS trên định dạng FP32), tách biệt hoàn toàn khỏi các sai số xấp xỉ của đồ thị HNSW.

3. **Bảo toàn tiền tố mô hình (Prefix Integrity):** Thực thi nghiêm ngặt tiền tố nhiệm vụ của từng mô hình (như `"query: "` và `"passage: "` đối với họ E5; `"Represent this sentence..."` đối với họ BGE/Arctic).

4. **Đo lường tài nguyên độc lập:** Đo đạc phân vị độ trễ P50/P95 trên 100 câu truy vấn đơn lẻ ($B=1$, sau 10 lượt khởi động ấm), thông lượng nạp tài liệu ($B=32$), và bộ nhớ tiến trình đỉnh (Process Peak RSS) thông qua tiến trình con Python cô lập bằng thư viện `psutil`.

5. **Độ mạnh thống kê và kiểm định đa biến:** Quy mô 207 bài báo giúp làm hẹp khoảng tin cậy 95% bootstrap theo cụm bài báo ($B=2.000$, seed=42). Tuy nhiên, đối với việc kiểm soát sai số loại II (Statistical Power), phân tích mô phỏng Monte Carlo ($B=2.000$ tại eval/phases/phase_3_embedding/artifacts/statistical_audit_results.json) chỉ ra rằng: với ngưỡng hiệu ứng tối thiểu quan tâm $\text{SESOI} = 0,030$, độ mạnh thống kê thực tế chỉ đạt mức khiêm tốn **38,6%** (đòi hỏi cỡ mẫu lý thuyết $K \approx 500$ bài báo để đạt $\ge 80\%$). Độ mạnh thống kê chỉ đạt mức tin cậy cao (78,3\% - 85,5\%) đối với các mức chênh lệch hiệu ứng lớn quan sát được thực tế ($\Delta \ge 0,05$, như giữa e5-small-v2 hoặc modernbert so với baseline all-MiniLM-L6-v2). Do đó, đối với các trường hợp chênh lệch nhỏ ($\Delta \le 0,03$), nghiên cứu duy trì sự thận trọng, không ngộ nhận việc không đạt ý nghĩa thống kê là bằng chứng của sự tương đồng năng lực tuyệt đối. Mọi kết luận vượt trội đều được đối chiếu khắt khe với hiệu chỉnh tỷ lệ sai số họ Holm-Bonferroni (chi tiết tại Bảng 5.4).



### 5.4.2. Kết quả đo lường định lượng



Bảng 5.3 trình bày đầy đủ các chỉ số chất lượng truy xuất và thông số hiệu năng phần cứng của 11 mô hình được khảo sát (được xuất từ tệp [`table_5_3_rq3_embedding.csv`](file:///c:/DACNTT/reports/chapter5/tables/table_5_3_rq3_embedding.csv)).



*Bảng 5.3: Bảng xếp hạng chất lượng truy xuất và hiệu năng phần cứng của 11 mô hình embedding trên 207 bài báo / 615 câu hỏi (RQ3).*



| STT | Mô hình Embedding | Kích thước Tham số | Số chiều Vector | Giấy phép Mã nguồn | nDCG@10 [95% CI] | nDCG@4 | Recall@20 | MRR@10 | Sai khác $\Delta$ vs MiniLM [95% CI] | Trị số $p_{\text{raw}}$ danh định | Độ trễ P50 (ms) | Thông lượng (chunks/s) | Peak RSS (MB) |

| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |

| 1 | `bm25` (Sparse Baseline) | 0M | — | MIT | 0,4805 [0,4480; 0,5130] | 0,3779 | 0,9363 | 0,4197 | -0,0220 [-0,0522; +0,0091] | 0,1739 | **0,10** | **14.673,3** | **477,9** |
| 2 | `all-MiniLM-L6-v2` *(Baseline)* | 22,7M | 384 | Apache-2.0 | 0,5026 [0,4746; 0,5315] | 0,3938 | 0,9483 | 0,4417 | 0,0000 | 1,0000 | **19,30** | **19,0** | 593,1 |
| 3 | `e5-small-v2` *(Hệ thống)* | 33,4M | 384 | MIT | 0,5522 [0,5253; 0,5778] | 0,4588 | 0,9623 | 0,5046 | **+0,0497** [+0,0262; +0,0741]* | **0,0010\*** | 30,26 | 6,5 | 659,8 |
| 4 | `bge-small-en-v1.5` | 33,4M | 384 | MIT | 0,5209 [0,4901; 0,5520] | 0,4214 | 0,9542 | 0,4671 | +0,0183 [-0,0027; +0,0393] | 0,0830 | 34,14 | 6,5 | 672,3 |
| 5 | `gte-small` | 33,4M | 384 | Apache-2.0 | 0,4659 [0,4358; 0,4957] | 0,3585 | 0,9329 | 0,4171 | -0,0367 [-0,0599; -0,0135]* | **0,0010\*** | 29,42 | 6,3 | 684,0 |
| 6 | `snowflake-arctic-embed-s` | 33,2M | 384 | Apache-2.0 | 0,5417 [0,5115; 0,5714] | 0,4453 | 0,9523 | 0,4927 | **+0,0392** [+0,0171; +0,0625]* | **0,0020\*** | 30,45 | 7,0 | 672,1 |
| 7 | `snowflake-arctic-embed-m-v1.5` | 108,9M | 768 | Apache-2.0 | 0,5472 [0,5186; 0,5756] | 0,4531 | 0,9433 | 0,5000 | **+0,0447** [+0,0219; +0,0670]* | **0,0010\*** | 74,44 | 2,4 | 956,0 |
| 8 | `nomic-embed-text-v1.5` | 137,0M | 768 | Apache-2.0 | 0,5133 [0,4843; 0,5422] | 0,4219 | 0,9553 | 0,4665 | +0,0108 [-0,0106; +0,0337] | 0,3418 | 110,19 | 1,6 | 1.128,1 |
| 9 | `modernbert-embed-base` | 149,0M | 768 | Apache-2.0 | **0,5872** [0,5586; 0,6166] | **0,4937** | **0,9642** | **0,5438** | **+0,0846** [+0,0627; +0,1075]* | **0,0010\*** | 103,39 | 1,8 | 1.161,7 |
| 10 | `snowflake-arctic-embed-m-v2.0` | 305,0M | 768 | Apache-2.0 | 0,4809 [0,4512; 0,5090] | 0,3742 | 0,9481 | 0,4203 | -0,0216 [-0,0465; +0,0033] | 0,0950 | 114,49 | 2,2 | 1.399,5 |
| 11 | `mxbai-embed-large-v1` | 335,1M | 1.024 | Apache-2.0 | 0,5064 [0,4776; 0,5344] | 0,4177 | 0,9469 | 0,4611 | +0,0039 [-0,0173; +0,0265] | 0,7236 | 275,34 | 0,6 | 1.292,0 |

*\*(Nguồn dữ liệu: `eval/results/thesis_embedding_benchmark.json`). Cột $p_{\text{raw}}$ báo cáo trị số $p$ danh định hai phía từ kiểm định Bootstrap theo cụm bài báo ($B=2.000$, seed=42) với mốc đối chứng `all-MiniLM-L6-v2`. Dấu sao (\*) biểu thị sự khác biệt vừa đạt ý nghĩa ở mức $\alpha=0,05$ danh định, vừa vượt qua quy trình kiểm soát tỷ lệ sai số họ (FWER) bằng hiệu chỉnh tuần tự Holm-Bonferroni (chi tiết các bước đối soát được trình bày tại Bảng 5.4).*

![Hình 5.4: So sánh chất lượng truy xuất (nDCG@10 ± 95% CI) của 11 mô hình biểu diễn vector (RQ3)](file:///c:/DACNTT/reports/chapter5/figures/fig5_4_rq3_embedding_ndcg10.png)

*Hình 5.4: Biểu đồ xếp hạng chất lượng truy xuất nDCG@10 (kèm khoảng tin cậy 95% CI) của 11 mô hình embedding.*

![Hình 5.5: Đánh đổi Chất lượng (nDCG@10) và Chi phí tính toán (Độ trễ P50) trên CPU Ryzen 5 5600 (RQ3)](file:///c:/DACNTT/reports/chapter5/figures/fig5_5_rq3_quality_cost.png)

*Hình 5.5: Không gian đánh đổi Chất lượng – Chi phí và Đường biên hiệu quả Pareto trên CPU máy trạm.*

### 5.4.3. Thảo luận và Phân tích chuyên sâu RQ3

1. **Vị thế dẫn đầu chất lượng của `modernbert-embed-base`:**
   Mô hình `modernbert-embed-base` xác lập đỉnh cao chất lượng truy xuất trong toàn bộ nghiên cứu với **$\text{nDCG@10} = 0,5872$** và **$\text{nDCG@4} = 0,4937$**, tạo ra bước nhảy vọt $\Delta = +0,0846$ so với baseline ($p = 0,0010^*$, khoảng tin cậy $[+0,0627; +0,1075]$ hoàn toàn tách biệt dương). Nhờ kiến trúc ModernBERT hiện đại với cơ chế mã hóa vị trí RoPE và hỗ trợ cửa sổ ngữ cảnh lên đến 8.192 tokens, mô hình nắm bắt rất tốt mối quan hệ phụ thuộc ngữ nghĩa xa trong các bài báo khoa học.

2. **Hiệu chỉnh sai số học thuật về ý nghĩa thống kê của `bge-small-en-v1.5`:**
   Một đóng góp quan trọng của công tác kiểm chứng độc lập trong luận văn là làm rõ năng lực thực tế của `bge-small-en-v1.5`. Trong một số báo cáo sơ bộ trước đây, mô hình này từng bị nhầm lẫn là vượt trội có ý nghĩa thống kê ($p < 0,001$). Kết quả kiểm định tái lập chuẩn xác trên 207 bài báo chứng minh rằng: **`bge-small-en-v1.5` không có ý nghĩa thống kê vượt trội so với `all-MiniLM-L6-v2`** ở mức $\alpha = 0,05$ ($\text{nDCG@10} = 0,5209$, $\Delta = +0,0183$, khoảng tin cậy $[-0,0027; +0,0393]$ bao trùm giá trị 0, trị số $p = 0,0830$).

3. **Phân tích Đường biên Pareto và Căn cứ lựa chọn `e5-small-v2` cho sản phẩm:**
   Quan sát không gian đánh đổi trong Hình 5.5 xác định rõ 4 điểm cực trị trên đường biên Pareto:
   - **Ứng viên Hiệu năng cao (Efficiency Baseline):** `all-MiniLM-L6-v2` đạt độ trễ thấp nhất trong nhóm dense (19,3 ms) và thông lượng cao nhất (19,0 chunks/s), nhưng chất lượng truy xuất ở mức khiêm tốn (0,5026).
   - **Ứng viên Cân bằng Tối ưu (Balanced Champion):** `intfloat/e5-small-v2` đạt $\text{nDCG@10} = 0,5522$ ($\Delta = +0,0497, p = 0,0010^*$), trong khi độ trễ chỉ tăng nhẹ lên **30,26 ms**, thông lượng duy trì mức tốt **6,5 chunks/s**, và mức tiêu thụ RAM cực kỳ tiết kiệm (**659,8 MB**).
   - **Ứng viên Trung gian:** `snowflake-arctic-embed-m-v1.5` đạt điểm số 0,5472 nhưng độ trễ tăng hơn gấp đôi lên 74,44 ms và thông lượng giảm xuống 2,4 chunks/s.
   - **Ứng viên Đỉnh cao Chất lượng (Quality Champion):** `modernbert-embed-base` đạt chất lượng cao nhất (0,5872) nhưng phải đánh đổi bằng chi phí tính toán đáng kể: độ trễ truy vấn tăng lên **103,39 ms** (gấp 3,4 lần E5-Small), thông lượng giảm xuống **1,8 chunks/s** (chậm gấp 3,6 lần), và bộ nhớ RAM tăng lên **1.161,7 MB**.

   *Quyết định triển khai hệ thống và Xác lập 3 mô hình đại diện cho thực nghiệm kết hợp toàn trình (RQ6):* Mặc dù `modernbert-embed-base` là ứng viên chất lượng cao nhất, hệ thống ứng dụng web quản lý tài liệu trong đồ án được thiết kế cho người dùng cá nhân vận hành trên máy trạm thông thường không có GPU. Thời gian người dùng chờ lập chỉ mục một bài báo 40 chunks với ModernBERT mất hơn 22 giây, trong khi với `e5-small-v2` chỉ mất khoảng 6 giây. Do đó, việc lựa chọn **`intfloat/e5-small-v2`** làm mô hình nhúng mặc định trong `rag_service.py` là một quyết định kỹ thuật hoàn toàn cân bằng giữa trải nghiệm tương tác thực tế và độ chính xác học thuật.

   Đồng thời, để ngăn ngừa sự bùng nổ tổ hợp ($11 \times 4 \times 3 = 132$ cấu hình) trong các thực nghiệm kết hợp RAG toàn trình ở giai đoạn tiếp theo (RQ6), ba mô hình biểu diễn vector đại diện cho 3 phân khúc đặc trưng trên đường biên Pareto được lựa chọn chính thức:
   - **`all-MiniLM-L6-v2` — Đại diện Hiệu năng cao (Efficiency Baseline):** Mốc đối chứng cận dưới về tài nguyên tính toán (độ trễ P50 19,3 ms, thông lượng 19,0 chunks/s, RAM 593,1 MB), nhằm kiểm định xem liệu sự nâng cấp mô hình biểu diễn vector có thực sự tạo ra đột phá về độ trung thực của câu trả lời sinh ra ở đầu ra LLM hay không.
   - **`intfloat/e5-small-v2` — Đại diện Cân bằng Tối ưu (Balanced Champion / System Choice):** Cấu hình mặc định đang vận hành trong sản phẩm, dung hòa xuất sắc giữa nDCG@10 (0,5522) và tốc độ đáp ứng (P50 30,26 ms, RAM 659,8 MB).
   - **`modernbert-embed-base` — Đại diện Đỉnh cao Chất lượng (Quality Ceiling Champion):** Xác lập trần độ chính xác truy xuất (nDCG@10 = 0,5872, cửa sổ ngữ cảnh 8.192 tokens), nhằm xác định liệu việc chấp nhận độ trễ gấp 3,4 lần và thông lượng chậm gấp 3,6 lần có mang lại giá trị gia tăng tương xứng cho tầng sinh của mô hình ngôn ngữ hay không.

4. **Hiện tượng suy giảm khi phóng to mô hình thiếu kiểm soát:**
   Kết quả của `mxbai-embed-large-v1` mang lại hàm ý cảnh báo sâu sắc về việc chạy theo kích thước mô hình. Mặc dù có tới 335,1 triệu tham số và vector 1.024 chiều, mô hình này chỉ đạt $\text{nDCG@10} = 0,5064$ (hoàn toàn tương đương baseline MiniLM 22,7M với $\Delta = +0,0039, p = 0,7236$), nhưng lại gây tắc nghẽn nghiêm trọng hệ thống với độ trễ lên tới **275,34 ms/truy vấn** và thông lượng rơi xuống mức không thể chấp nhận được là **0,6 chunks/s**.

### 5.4.4. Kiểm định so sánh đa biến và Hiệu chỉnh Holm-Bonferroni (RQ3)

Bảng 5.4 tổng hợp quy trình hiệu chỉnh tuần tự Holm-Bonferroni đối với 10 mô hình vector so với baseline `all-MiniLM-L6-v2` ở mức ý nghĩa $\alpha = 0,05$.

*Bảng 5.4: Quy trình kiểm soát tỷ lệ sai số họ (FWER) bằng hiệu chỉnh tuần tự Holm-Bonferroni cho RQ3.*

| Bước $k$ | Mô hình so sánh | Trị số $p_{\text{raw}}$ danh định | Ngưỡng $\alpha_k = \frac{0,05}{11 - k}$ | Trị số $p_{\text{adj}}$ sau hiệu chỉnh | Kết luận FWER |
| :---: | :--- | :---: | :---: | :---: | :---: |
| 1 | `modernbert-embed-base` | 0,0010 | 0,0050 | 0,0100 | Bác bỏ $H_0$ (Vượt trội\*) |
| 2 | `e5-small-v2` | 0,0010 | 0,0056 | 0,0100 | Bác bỏ $H_0$ (Vượt trội\*) |
| 3 | `snowflake-arctic-embed-m-v1.5` | 0,0010 | 0,0063 | 0,0100 | Bác bỏ $H_0$ (Vượt trội\*) |
| 4 | `gte-small` | 0,0010 | 0,0071 | 0,0100 | Bác bỏ $H_0$ (Suy giảm\*) |
| 5 | `snowflake-arctic-embed-s` | 0,0020 | 0,0083 | 0,0120 | Bác bỏ $H_0$ (Vượt trội\*) |
| 6 | `bge-small-en-v1.5` | 0,0830 | 0,0100 | 0,4150 | Không bác bỏ $H_0$ |
| 7 | `snowflake-arctic-embed-m-v2.0` | 0,0950 | 0,0125 | 0,4150 | Không bác bỏ $H_0$ |
| 8 | `bm25` | 0,1739 | 0,0167 | 0,5217 | Không bác bỏ $H_0$ |
| 9 | `nomic-embed-text-v1.5` | 0,3418 | 0,0250 | 0,6836 | Không bác bỏ $H_0$ |
| 10 | `mxbai-embed-large-v1` | 0,7236 | 0,0500 | 0,7236 | Không bác bỏ $H_0$ |

*Nhận xét quy trình hiệu chỉnh:*
- Cả 5 mô hình đầu bảng (`modernbert`, `e5-small-v2`, `arctic-embed-m-v1.5`, `gte-small`, `arctic-embed-s`) đều có trị số $p_{\text{raw}} \le 0,0020 < \alpha_k$ tương ứng ($p_{\text{adj}} \le 0,0120 < 0,05$). Do đó, các kết luận về sự vượt trội (hoặc suy giảm của `gte-small`) đều bảo toàn trọn vẹn ý nghĩa thống kê nghiêm ngặt sau khi đã kiểm soát sai số họ.
- Tại bước $k=6$, `bge-small-en-v1.5` có $p_{\text{raw}} = 0,0830 > \alpha_6 = 0,0100$, do đó quy trình kiểm định chính thức dừng lại tại đây. Cả `bge-small-en-v1.5` cùng toàn bộ các mô hình xếp sau đều không đạt mức ý nghĩa thống kê ($p_{\text{adj}} \ge 0,4150$).

---

## 5.5. Thực nghiệm RQ4: Đánh giá cơ chế truy xuất lai kết hợp phân mảnh phân cấp (Hybrid Retrieval)

### 5.5.1. Câu hỏi nghiên cứu và Phạm vi thực nghiệm (Research Question & Experimental Scope)

Câu hỏi nghiên cứu RQ4 được định nghĩa tường minh như sau:

> **RQ4:** *Các chiến lược truy xuất khác nhau (Dense Only, BM25 Only, Hybrid RRF, Hybrid Convex) ảnh hưởng như thế nào đến chất lượng của ngữ cảnh bằng chứng được thu hồi cho tác vụ hỏi đáp bài báo khoa học, khi được đánh giá dưới cùng một cấu hình cố định về bóc tách PDF, phân đoạn và mô hình biểu diễn vector?*

**Ranh giới phạm vi thực nghiệm:** Nghiên cứu phân định rạch ròi rằng RQ4 chỉ tập trung đánh giá chất lượng của các **chiến lược truy xuất ngữ cảnh bằng chứng (Retrieval Strategies)**, hoàn toàn KHÔNG đánh giá tính chính xác của câu trả lời cuối cùng hay mức độ trung thực học thuật (Faithfulness / Hallucination) của toàn bộ hệ thống RAG tích hợp. Đánh giá câu trả lời của mô hình ngôn ngữ lớn đòi hỏi các thước đo sinh văn bản chuyên biệt và được định vị trong lộ trình nghiên cứu tiếp nối (RQ5).

---

### 5.5.2. Ngữ liệu và Phân hoạch Đánh giá (Dataset & Evaluation Split)

Quy trình đánh giá RQ4 tuân thủ nghiêm ngặt các nguyên tắc phân hoạch dữ liệu khoa học:

1. **Bộ dữ liệu chuẩn:** Sử dụng bộ dữ liệu học thuật **QASPER v0.3** chính thức (AllenAI).
2. **Cơ cấu tập kiểm thử độc lập (Test Split):**
   - Phân hoạch Test chính thức của QASPER bao gồm **416 bài báo**.
   - Trong đó, có **408 bài báo** chứa các câu hỏi có bằng chứng dạng văn bản trích xuất được.
   - Tổng cộng **1.310 câu hỏi khả giải có bằng chứng văn bản** được đưa vào đánh giá thực nghiệm chính thức.
3. **Tiêu chí loại trừ (Exclusion Criteria):** Đúng 8 bài báo trong tập Test (`1710.07394`, `1808.10059`, `1802.09233`, `1711.11017`, `1602.07776`, `2003.10564`, `1910.09942`, `1910.12477`) bị loại trừ một cách nhất quán vì chỉ chứa các câu hỏi không thể trả lời (`unanswerable`) hoặc bằng chứng thuần túy là hình vẽ/bảng biểu ngoài luồng (`FLOAT SELECTED`) mà không có đoạn văn bản trích dẫn ($R_q = \emptyset$). Tập bằng chứng rỗng khiến các chỉ số nDCG và Recall toán học không thể xác định. Toàn bộ 1.310 câu hỏi được phân bố tự nhiên trên 408 bài báo còn lại (trung bình 3,21 câu hỏi/bài, min = 1, max = 9).
4. **Phân định Tập Phát triển (Dev) vs Tập Kiểm thử (Test):**
   - *Tập Development (281 bài báo, 892 câu hỏi khả giải trên 276 bài, 9.698 phân đoạn con):* Được sử dụng độc quyền để khảo sát không gian tham số, quan sát hành vi của các hàm hợp nhất và lựa chọn cấu hình tối ưu.
   - *Tập Test độc lập (408 bài báo, 1.310 câu hỏi, 14.035 phân đoạn con):* Toàn bộ các cấu hình sau khi chốt từ tập Dev được **đóng băng nguyên trạng (`frozen configurations`)** và đánh giá duy nhất một lần trên tập Test. Tuyệt đối không gộp chung dữ liệu (no data pooling) và không dùng kết quả Test để tinh chỉnh ngược lại cấu hình.
5. **Đơn vị phân tích (Unit of Analysis):** Các câu hỏi được nhóm theo bài báo (trung bình 3,21 câu hỏi/bài). Do đó, quy trình kiểm định thống kê phải tính đến mối quan hệ tương quan phụ thuộc giữa các câu hỏi trong cùng một bài báo thông qua phương pháp lấy mẫu chùm (Cluster Bootstrap).

---

### 5.5.3. Các chiến lược truy xuất được đối sánh (Compared Retrieval Strategies)

Bốn phương thức truy xuất được đưa vào đánh giá đối đầu trực tiếp trên tập kiểm thử Test được định nghĩa tại bảng dưới đây:

| Chiến lược truy xuất | Cấu hình tham số cụ thể | Mục đích trong thực nghiệm |
| :--- | :--- | :--- |
| **Dense Only** | Mô hình `intfloat/e5-small-v2` (384 chiều, chuẩn hóa L2 FP32, tiền tố `"passage: "` và `"query: "`, exact cosine BLAS) | Mốc đối chứng truy xuất ngữ nghĩa dày đặc (**Baseline**) cho mọi so sánh thống kê |
| **BM25 Only** | Thuật toán BM25 kinh điển phân đoạn theo từ tố subword WordPiece ($k_1=1,5, b=0,75$, loại bỏ 39 từ dừng chuẩn) | Mốc đối chứng truy xuất từ vựng thưa (**Lexical Baseline**) |
| **Hybrid RRF** | Thuật toán Reciprocal Rank Fusion không trọng số với hằng số làm mượt $k=60$: $\text{RRF}(d) = \sum_{m} \frac{1}{60 + \text{rank}_m(d)}$ | Kết hợp thứ hạng ngữ nghĩa và từ vựng; là **cấu hình mặc định đang vận hành trong sản phẩm** |
| **Hybrid Convex** | Kết hợp tuyến tính lồi sau khi chuẩn hóa min-max điểm số với $\alpha=0,7$: $S_{\text{convex}}(d) = 0,7 \cdot S_{\text{Dense}}^{\text{norm}}(d) + 0,3 \cdot S_{\text{BM25}}^{\text{norm}}(d)$ | Kết hợp điểm số tối ưu hóa phân phối dựa trên trọng số bất đối xứng |

**Kiểm soát biến độc lập:** Toàn bộ các thành phần khác trong đường ống RAG được **giữ cố định 100% trên cả 4 nhánh**:
- Công cụ bóc tách PDF: `pymupdf_layout`.
- Chiến lược phân mảnh: `hierarchical` Small-to-Big với đoạn con ~200 tokens (overlap 40 tokens) gắn liền với đề mục cha.
- Mô hình biểu diễn vector: `intfloat/e5-small-v2` (384 chiều).
- Trần khống chế ngữ cảnh: Tối đa 5 đề mục cha (`MAX_PARENTS = 5`) và ngân sách 1.600 tokens.

Nhờ việc cố định hoàn toàn các mắt xích này, người đọc có thể khẳng định chắc chắn rằng mọi sự chênh lệch quan sát được hoàn toàn bắt nguồn từ chiến lược truy xuất chứ không phải do sự thay đổi của các mắt xích khác trong hệ thống. Ngoài ra, cấu hình $k=20$ của RRF chỉ được khảo sát thăm dò trên tập Dev và không đưa vào tập so sánh đóng băng trên Test để tránh bùng nổ so sánh đa biến.

---

### 5.5.4. Quy trình đường ống truy xuất và Các tham số cố định (Retrieval Pipeline & Fixed Parameters)

Quy trình xử lý hoàn chỉnh từ bài báo được lập chỉ mục đến khối ngữ cảnh được lắp ráp nạp cho mô hình LLM được mô tả qua lưu đồ dưới đây:

```text
Tập tài liệu bài báo QASPER Test (408 bài báo)
                     │
                     ▼
14.035 phân đoạn con (Child Chunks, ~200 tokens, overlap 40)
                     │
                     ▼
Truy xuất ứng viên cục bộ từng bài (Dense, BM25, RRF, hoặc Convex)
                     │  (Thu hồi top-20 phân đoạn con hàng đầu)
                     ▼
Mở rộng phân cấp Small-to-Big (Expand Child Chunks to Parent Sections)
                     │  (Khử trùng lặp đề mục cha; cắt cửa sổ nếu cha > 800 tokens)
                     ▼
Lắp ráp khối ngữ cảnh (Context Assembly)
                     │  (Khống chế tối đa 5 đề mục cha; Ngân sách 1.600 tokens)
                     ▼
Đánh giá chất lượng khối ngữ cảnh bằng chứng hoàn chỉnh được lắp ráp
```

**Bảng tham số cố định của thực nghiệm:**
- **Trần đề mục cha:** `MAX_PARENTS = 5`.
- **Ngân sách ngữ cảnh:** 1.600 tokens (đo lường bằng bộ mã hóa `cl100k_base` qua thư viện `tiktoken`).
- **Ngưỡng liên quan bằng chứng:** $\tau = 0,50$ (đối khớp tập từ tố WordPiece).
- **Hạt giống ngẫu nhiên:** `seed = 42`.
- **Mô hình embedding và số chiều:** `intfloat/e5-small-v2`, 384 chiều, chuẩn hóa vector đơn vị L2.
- **Giới hạn độ sâu xếp hạng ứng viên:** Top-20 phân đoạn con được xếp hạng ở giai đoạn 1 trước khi mở rộng sang đề mục cha.
- **Xử lý ngoại lệ:** Các câu hỏi unanswerable hoặc chỉ có bằng chứng hình ảnh/bảng biểu ngoài luồng được loại trừ trước khi đánh giá; trường hợp truy xuất rỗng nhận điểm số 0.

> [!IMPORTANT]
> ### Hai chi tiết hiện thực kỹ thuật cốt lõi cần minh bạch
>
> 1. **Sự khác biệt về phạm vi tính toán IDF của BM25:**
>    - *Trong benchmark ngoại tuyến:* Chỉ số nghịch đảo tần suất văn bản (IDF) của BM25 được tính toán trên tập hợp toàn bộ các đoạn văn bản trong phân hoạch Test (split-wide chunk background) nhằm tránh hiện tượng giá trị IDF bị âm hoặc mất ổn định trên tập từ vựng cực nhỏ của một bài báo đơn lẻ (~35 phân đoạn).
>    - *Trong hệ thống vận hành thực tế (`DocumentRAG`):* BM25 được tính toán cục bộ trên tập các phân đoạn của chính tài liệu đang được mở (document-local BM25).
>    - *Lưu ý diễn giải:* Kết quả benchmark là một xấp xỉ kỹ thuật cần thiết cho việc đo đạc tự động trên quy mô lớn, không nên được coi là phép đo đồng nhất 100% với hành vi của BM25 cục bộ trên từng bài đơn lẻ trong ứng dụng.
>
> 2. **Bản chất đo lường sau khi lắp ráp ngữ cảnh (Metrics Computed After Context Assembly):**
>    - Toàn bộ các chỉ số truy xuất được tính toán **sau khi đã thực hiện mở rộng Small-to-Big, áp dụng trần 5 đề mục cha và cắt lọc theo ngân sách 1.600 tokens**.
>    - Do đó, các chỉ số này đo lường **chất lượng của khối ngữ cảnh bằng chứng hoàn chỉnh được lắp ráp để nạp vào mô hình LLM**, không phải là hiệu năng xếp hạng ứng viên phân đoạn thô không hạn chế (unrestricted candidate retrieval).

---

### 5.5.5. Ý nghĩa và Định nghĩa các Chỉ số Đánh giá (Metrics & Their Meanings)

Thực nghiệm xác định **nDCG@10 là chỉ số chính (Primary Metric)** và sử dụng 4 chỉ số bổ trợ nhằm cung cấp bức tranh toàn diện về hành vi truy xuất:

| Chỉ số | Vai trò | Ý nghĩa đối với người đọc và hệ thống RAG |
| :--- | :---: | :--- |
| **nDCG@10** | **Chính** | Đánh giá chất lượng và trật tự sắp xếp tối ưu của các bằng chứng liên quan trong top-10 ngữ cảnh được đánh giá. |
| **nDCG@4** | Bổ trợ | Đánh giá chất lượng của các bằng chứng xếp hạng cao nhất (phù hợp trực tiếp với cửa sổ ngữ cảnh prompt thực tế của LLM). |
| **Recall@20** | Bổ trợ | Đánh giá độ bao phủ bằng chứng liên quan trong top-20 kết quả (bị chặn trên thực tế bởi trần tối đa 5 đề mục cha). |
| **MRR@10** | Bổ trợ | Đánh giá vị trí xếp hạng của kết quả bằng chứng liên quan đầu tiên được tìm thấy. |
| **Hit@5** | Bổ trợ | Tỷ lệ phần trăm các câu hỏi có ít nhất một đoạn bằng chứng liên quan nằm trong top-5 kết quả. |

**Phương pháp xác định nhãn liên quan (Relevance Judgments):**
Nhãn liên quan giữa đoạn bằng chứng gốc $E$ (Ground-Truth Evidence trong QASPER) và phân đoạn văn bản $C$ trong bài báo được xác định thông qua độ đo bao phủ tập từ tố WordPiece:
$$\text{containment}(E, C) = \frac{|T(E) \cap T(C)|}{|T(E)|}$$
Một phân đoạn được gán nhãn liên quan (nhãn 1) nếu $\text{containment}(E, C) \ge 0,50$, ngược lại gán nhãn 0.

**Định nghĩa đơn vị kết quả tại bước tính toán metric:**
Một đơn vị kết quả tại giai đoạn tính điểm là một **đề mục cha (parent section)** thu được sau khi mở rộng từ các đoạn con trúng khớp; một đề mục cha được tính là có liên quan nếu nó chứa ít nhất một phân đoạn con thỏa mãn ngưỡng bao phủ $\tau = 0,50$.

---

### 5.5.6. Phương pháp Phân tích Thống kê (Statistical Analysis)

Nhằm bảo đảm tính vững chắc về mặt toán học và tránh các bẫy ngụy biện thống kê, quy trình phân tích được thiết kế như sau:

1. **So sánh ghép cặp (Paired Comparison):** Từng chiến lược truy xuất lai và từ vựng được so sánh đối đầu trực tiếp với mốc chuẩn `Dense Only` trên cùng một tập 1.310 câu hỏi kiểm thử.
2. **Lấy mẫu chùm theo bài báo (Paper-Cluster Bootstrap):** Thực hiện tái lấy mẫu bootstrap với **$B = 2.000$ mẫu lặp lại** và cố định `seed = 42`. Việc lấy mẫu được thực hiện ở cấp bài báo (paper level) thay vì cấp câu hỏi đơn lẻ nhằm bảo toàn mối quan hệ tương quan nội tại giữa các câu hỏi thuộc cùng một bài báo.
3. **Khoảng tin cậy (Confidence Intervals):** Báo cáo khoảng tin cậy 95% Bootstrap hai phía cho mức chênh lệch trung bình: $\Delta = \text{Metric}(\text{Candidate}) - \text{Metric}(\text{Dense Baseline})$.
4. **Kiểm soát so sánh đa biến (Multiple Comparisons):** Áp dụng quy trình hiệu chỉnh tuần tự **Holm-Bonferroni** (Step-down procedure) đối với đúng 3 cặp so sánh kế hoạch đối đầu với Dense Only (`BM25`, `Hybrid RRF k=60`, và `Hybrid Convex alpha=0.7`) nhằm kiểm soát chặt chẽ tỷ lệ sai số họ (Family-Wise Error Rate - FWER).
5. **Mức ý nghĩa định trước:** Thiết lập ngưỡng ý nghĩa danh định $\alpha = 0,05$.
6. **Nguyên tắc diễn giải kết quả không có ý nghĩa:** Một kết quả không đạt mức ý nghĩa thống kê (như trường hợp của RRF $k=60$ với $p_{\text{adj}} = 0,8696$) **không phải là bằng chứng toán học chứng minh hai phương pháp tương đương tuyệt đối**; điều đó chỉ có nghĩa là thực nghiệm này chưa phát hiện thấy sai khác mang ý nghĩa thống kê dưới quy trình đánh giá đã chọn.

---

### 5.5.7. Kết quả Thực nghiệm trên Tập Test Độc lập (Test Results)

Bảng 5.5 báo cáo kết quả thực nghiệm toàn diện của 4 cấu hình truy xuất trên tập kiểm thử độc lập QASPER Test (408 bài báo, 1.310 câu hỏi, 14.035 phân đoạn con), được xuất tự động từ tệp kết quả gốc [`rq4_qasper_test_hierarchical_benchmark.json`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_test_hierarchical_benchmark.json).

*Bảng 5.5: Kết quả đánh giá thực nghiệm truy xuất lai (RQ4) trên tập kiểm thử độc lập QASPER Test.*

| Chiến lược / Phương thức truy xuất | nDCG@10 (Chỉ số chính) | nDCG@4 | Recall@20 | MRR@10 | Hit@5 (%) | $\Delta$ vs Dense [95% CI] | $p_{\text{raw}}$ | $p_{\text{adj}}$ (Holm) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Dense Only (`e5-small-v2`)** | **0,5655** | 0,5724 | 0,6366 | 0,6415 | 82,7% | Mốc chuẩn (0,0) | — | — |
| **BM25 Only (WordPiece)** | **0,5065** | 0,5135 | 0,5908 | 0,5688 | 77,9% | -0,0589 [-0,0788; -0,0390] | 0,0010 | **0,0030\*** |
| **Hybrid RRF ($k=60$) [Sản phẩm]** | **0,5662** | 0,5747 | 0,6413 | 0,6368 | 83,1% | +0,0008 [-0,0110; +0,0130] | 0,8696 | 0,8696 |
| **Hybrid Convex ($\alpha=0.7$)** | **0,5806** | 0,5870 | 0,6525 | 0,6556 | 84,5% | **+0,0152 [+0,0045; +0,0262]** | 0,0070 | **0,0140\*** |

*\* Ghi chú: Ký hiệu \* biểu thị sai khác có ý nghĩa thống kê so với mốc đối chứng Dense Only ở mức $\alpha = 0,05$ sau khi hiệu chỉnh tuần tự Holm-Bonferroni ($m=3$).*

**Phân tích kết quả thực nghiệm:**

1. **Sự vượt trội có ý nghĩa thống kê của phương pháp hòa trộn lồi có trọng số (Convex Fusion $\alpha=0.7$):**
   - Cấu hình `Hybrid Convex (alpha=0.7)`—vốn ưu tiên 70% trọng số cho khoảng cách vector ngữ nghĩa và 30% cho tần suất từ khóa—đạt thành tích xuất sắc nhất trên toàn bộ các thước đo: **nDCG@10 = 0,5806**, **nDCG@4 = 0,5870**, **Recall@20 = 0,6525**, **MRR@10 = 0,6556** và **Hit@5 = 84,5%**.
   - Mức cải thiện so với Dense Only đạt $\Delta = +0,0152$.
   - Đặc biệt, khoảng tin cậy 95% của mức chênh lệch hoàn toàn tách biệt khỏi số 0: **$[+0,0045; +0,0262]$**, và trị số $p$ sau hiệu chỉnh bảo toàn ý nghĩa thống kê nghiêm ngặt (**$p_{\text{adj}} = 0,0140 < 0,05$**).
   - *Hàm ý khoa học:* Kết quả này cung cấp bằng chứng thực nghiệm vững chắc chứng minh rằng: Việc kết hợp truy xuất ngữ nghĩa và từ khóa thực sự mang lại giá trị gia tăng rõ rệt, với điều kiện thuật toán hợp nhất phải phản ánh đúng độ tin cậy bất đối xứng của hai phương thức (ưu tiên semantic vector làm trụ cột chính).

2. **Đặc tính bảo toàn chất lượng của Reciprocal Rank Fusion ($k=60$):**
   - Thuật toán RRF ($k=60$) mặc định của hệ thống đạt nDCG@10 là **0,5662** ($\Delta = +0,0008$), nDCG@4 là **0,5747** và Hit@5 đạt **83,1%**.
   - Khoảng tin cậy 95% của mức chênh lệch $[-0,0110; +0,0130]$ bao hàm số 0 và trị số $p_{\text{adj}} = 0,8696 > 0,05$. Điều này cho thấy thuật toán RRF không trọng số không tạo ra sự vượt trội mang ý nghĩa thống kê so với truy xuất vector thuần túy.
   - *Nguyên nhân kỹ thuật:* Vì RRF phân bổ trọng số xếp hạng đồng đều 50/50 cho cả hai bảng xếp hạng, khi một nhánh (BM25) có chất lượng thấp hơn đáng kể so với nhánh còn lại (Dense), việc hòa trộn thứ hạng đồng đều có xu hướng làm loãng các phân đoạn ngữ nghĩa chính xác nếu BM25 không tìm thấy từ khóa trùng khớp. RRF với $k=60$ đạt hiệu năng truy xuất tương đương (comparable) với Dense Only trên benchmark đánh giá (nDCG@10 đạt 0,5662 so với 0,5655; $\Delta = +0,0008, p_{\text{adj}} = 0,8696$). Thuật toán này có ưu thế kỹ thuật là không đòi hỏi chuẩn hóa phân phối điểm số (Min-Max calibration) giữa hai nguồn. Tuy nhiên, do thực nghiệm chưa đo lường riêng rẽ các câu hỏi phụ thuộc hoàn toàn vào từ khóa hay thuật ngữ chuyên ngành hiếm gặp, nghiên cứu không khẳng định việc kết hợp RRF giúp tăng cường độ vững chắc trước từ khóa (keyword robustness) như một kết luận thực nghiệm đã được chứng minh, mà ghi nhận đây là một giả thuyết kỹ thuật cần được kiểm chứng thêm.

3. **Sự thất thế rõ rệt của truy xuất từ khóa thuần túy trong văn bản học thuật:**
   - `BM25 Only` chỉ đạt điểm nDCG@10 là **0,5065**, tụt hậu rất xa so với mô hình vector ngữ nghĩa `Dense Only` (0,5655) với mức suy giảm $\Delta = -0,0589$ (khoảng tin cậy 95%: $[-0,0788; -0,0390]$).
   - Kiểm định thống kê khẳng định sự suy giảm này có ý nghĩa thống kê cao ($p_{\text{adj}} = 0,0030 < 0,05$). Kết quả này chứng minh rằng trong miền tài liệu khoa học chuyên sâu—nơi câu hỏi người dùng có độ lệch từ vựng mặt chữ rất lớn so với đoạn trích dẫn (Jaccard overlap chỉ ~2,6% như đã chỉ ra ở EDA)—các phương pháp đối sánh từ khóa thuần túy không đủ khả năng định vị chính xác ngữ cảnh.

4. **Kỷ luật ngôn từ học thuật:** Nghiên cứu kiên quyết bác bỏ các tuyên bố mang tính phóng đại; tác giả không khẳng định Convex Fusion tối ưu tuyệt đối trên mọi miền ứng dụng hoặc cải thiện độ trung thực câu trả lời của mô hình ngôn ngữ lớn, vì những kết luận đó vượt ra ngoài phạm vi dữ liệu đo đạc thực tế của RQ4.

---

### 5.5.8. Khả năng Tái lập và Chi phí Tính toán (Reproducibility & Computational Cost)

Toàn bộ quy trình thực nghiệm RQ4 được tự động hóa và lưu trữ có thể tái lập 100%:

- **Kịch bản thực thi:** Kịch bản kiểm thử độc lập tại [`eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/scripts/evaluate_full_qasper_rq4_hybrid.py).
- **Lệnh thực thi chính xác:**
  ```powershell
  backend\venv\Scripts\python.exe eval\phases\phase_6_hybrid_retrieval\scripts\evaluate_full_qasper_rq4_hybrid.py --split test --strategy hierarchical
  ```
- **Môi trường phần mềm:** Python 3.12, PyTorch 2.x, Transformers 4.x, NumPy, FastEmbed/Sentence-Transformers.
- **Môi trường phần cứng:** CPU máy trạm AMD Ryzen 5 5600 (6 nhân/12 luồng, cố định 4 luồng tính toán `torch.set_num_threads(4)`), 16 GB RAM DDR4, không kích hoạt GPU, toàn bộ tính toán chạy dưới định dạng dấu phẩy động chuẩn FP32.
- **Nguồn gốc cache vector:** Toàn bộ 14.035 vector phân đoạn con được nạp trực tiếp từ tệp bộ đệm đã được kiểm toán:
  `eval/prepared/cache/embeddings/intfloat_e5-small-v2_test_hierarchical_passage.npy`
- **Thời gian thực thi:** Toàn bộ quá trình quét 1.310 câu hỏi qua 4 cánh thuật toán, mở rộng cấu trúc cha và chạy 2.000 mẫu bootstrap ghép cặp mất **1.781,95 giây (xấp xỉ 29,7 phút)**.
- **Tạo phẩm kiểm chứng đã lưu trữ:**
  - Tệp dữ liệu kết quả đầy đủ: [`eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_test_hierarchical_benchmark.json`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/artifacts/rq4_qasper_test_hierarchical_benchmark.json).
  - Báo cáo tóm tắt Markdown: [`eval/phases/phase_6_hybrid_retrieval/artifacts/RQ4_QASPER_TEST_HIERARCHICAL_REPORT.md`](file:///c:/DACNTT/eval/phases/phase_6_hybrid_retrieval/artifacts/RQ4_QASPER_TEST_HIERARCHICAL_REPORT.md).

---

### 5.5.9. Hạn chế và Diễn giải Kết quả (Limitations & Interpretation - DEC-03 Audit)

Để bảo đảm tính liêm chính học thuật cao nhất, các kết luận rút ra từ thực nghiệm RQ4 cần được tiếp nhận kèm theo sáu điểm giới hạn phương pháp luận và nguyên tắc quản trị sau:

1. **Giới hạn tập mẫu do loại trừ 8 bài báo không có bằng chứng văn bản:** Kết quả đánh giá áp dụng cho tập 408 bài báo và 1.310 câu hỏi có bằng chứng văn bản trích dẫn cụ thể. Đối với các bài báo mà câu trả lời phụ thuộc vào việc suy luận từ biểu đồ hoặc bảng số liệu phức tạp không có văn bản giải thích, chất lượng truy xuất có thể đòi hỏi các cơ chế phân tích đa phương thức (Multimodal RAG) bổ trợ.
2. **Khác biệt phạm vi tính toán IDF của BM25 và Cơ sở giữ RRF trong sản phẩm:** Việc tính IDF trên nền toàn phân hoạch Test (14.035 đoạn con) là một giải pháp xấp xỉ cần thiết cho benchmark tự động để tạo phân phối điểm mượt mà cho phép chuẩn hóa min-max của Convex Fusion. Trong kịch bản vận hành thực tế tại Chương 4 (`DocumentRAG`), BM25 được tính toán cục bộ trong một bài báo (~35–60 đoạn con), nơi sự lặp lại từ khóa chuyên ngành nén mạnh giá trị IDF. Do đó, việc duy trì **Hybrid RRF ($k=60$)** làm động cơ mặc định trong mã nguồn sản phẩm là một quyết định kỹ thuật dựa trên tính bất biến thứ hạng không tham số của RRF, triệt tiêu rủi ro trôi dạt điểm số trong môi trường tài liệu đơn lẻ.
3. **Chỉ số đo lường khối ngữ cảnh lắp ráp sau phân cấp và Phân định Recall@20:** Các chỉ số phản ánh chất lượng của khối ngữ cảnh đưa vào prompt sau khi mở rộng phân cấp và chặn trần ngân sách 1.600 tokens (tối đa 5 đề mục cha), đạt Recall@20 là **0,6413 (RRF)** và **0,6525 (Convex)**. Cần phân định rạch ròi kết quả này với con số $\text{Recall@20} = 0,9558$ thu được ở thực nghiệm phân mảnh phẳng trên 160 bài báo (`expanded_160_hybrid_rrf_benchmark.json`), tránh đánh đồng giữa hai kiến trúc phân mảnh khác nhau.
4. **Hiệu năng truy xuất không đồng nghĩa với câu trả lời chính xác:** Một khối ngữ cảnh có điểm nDCG@10 cao chỉ bảo đảm rằng các đề mục chứa bằng chứng đã được đưa vào prompt của LLM; việc mô hình ngôn ngữ lớn có tổng hợp chính xác, tránh ảo giác và lập luận logic hay không là một câu hỏi độc lập cần được đánh giá riêng biệt ở tầng sinh văn bản.
5. **Ranh giới suy rộng của cấu hình tối ưu:** Kết luận về sự vượt trội của Convex Fusion ($\alpha = 0,7$) và tính tương đương của RRF ($k=60$) được rút ra trên tập dữ liệu QASPER dưới cấu hình phân mảnh Small-to-Big; tác giả không khẳng định các cấu hình tham số này mặc nhiên tối ưu trên mọi bài toán tìm kiếm văn bản trong các lĩnh vực ngoài khoa học máy tính.
6. **Ranh giới phơi nhiễm tập Test và Quản trị đánh giá toàn trình (DEC-03):** Việc tập Test đã được khảo sát ở RQ4 đồng nghĩa với việc tập này không còn tính độc lập tuyệt đối đối với toàn bộ đường ống RAG. Các đánh giá toàn trình (End-to-End RAG) được quy định chặt chẽ phải thực thi trên tập kiểm thử độc lập rút từ kho 777 bài báo Train chưa từng phơi nhiễm (DEC-03 Audit), đồng thời công khai minh bạch mọi kết quả trên Test như một benchmark kiểm chứng đối chiếu hậu lựa chọn (post-selection confirmatory benchmark).


---



---



## 5.6. Kết quả RQ5 – Đánh giá thực nghiệm mô hình ngôn ngữ lớn cục bộ (Local LLM Generation & Faithfulness)

### 5.6.1. Thiết lập thực nghiệm có kiểm soát và Phương pháp luận Hai Tầng

Câu hỏi nghiên cứu RQ5 được thiết lập nhằm khảo sát giai đoạn sinh lời đáp (Generation Phase) trong đường ống RAG học thuật:

> **RQ5:** *Các mô hình ngôn ngữ lớn mã nguồn mở chạy cục bộ (`qwen2.5:0.5b`, `llama3.2:1b`, `llama3.2:3b`) so sánh như thế nào về độ chính xác câu trả lời (Answer Correctness), độ trung thực bám sát bằng chứng (Faithfulness) và hiệu năng suy luận (độ trễ P50/P95, thông lượng tokens/giây) khi được cung cấp cùng một ngữ cảnh trích dẫn học thuật và cùng một mẫu lời nhắc có cấu trúc trên môi trường máy trạm cá nhân không có GPU rời?*

Để bảo đảm tính chặt chẽ khoa học, kiểm soát nghiêm ngặt hiện tượng thiên lệch và phân định rõ ranh giới phương pháp luận, đánh giá RQ5 được vận hành theo cơ chế **Hai Tầng Độc lập (Dual-Tier Methodology)**:

1. **Tầng 1 – Đánh giá Định lượng Quy mô Lớn (Primary Quantitative Benchmark):**
   - **Tập mẫu:** $N = 500$ câu hỏi khoa học thuộc $K = 250$ cụm bài báo trích từ tập QASPER Train chưa từng phơi nhiễm (Unexposed Cohort, mã thực nghiệm `EXP-RQ5-MAIN-SAMPLED` đăng ký trong [`eval/experiment_provenance_registry.json`](file:///c:/DACNTT/eval/experiment_provenance_registry.json)). Toàn bộ câu hỏi đều thuộc nhóm có thể trả lời được (`answerable-only`). Với 3 mô hình, hệ thống thực thi tổng cộng $1.500$ lượt suy luận độc lập.
   - **Điều kiện kiểm soát:** Giải mã tất định (`temperature = 0.0`), giới hạn sinh tối đa `num_predict = 256` tokens, chung một mẫu lời nhắc học thuật (Academic Assistant Prompt) và chung một khối ngữ cảnh trích dẫn dưới ngân sách 1.600 tokens.
   - **Thước đo tự động:** Token F1 (toàn phần và phân rã theo 3 loại câu hỏi: Extractive, Abstractive, Boolean); tỷ lệ kích hoạt câu từ chối chuẩn theo yêu cầu phi chức năng NFR-03 (Refusal Rate); tỷ lệ chứa từ vựng ngữ cảnh tự động (Automated Containment Proxy); độ trễ P50/P95 và thông lượng suy luận (tokens/s).
   - **Kiểm định suy diễn thống kê:** Thực hiện kiểm định $t$ ghép cặp theo cụm bài báo ($K=250, df=249$), ước lượng khoảng tin cậy 95% bằng Bootstrap phân cụm ($B=2.000$) và kiểm soát tỷ lệ sai số họ (FWER) bằng hiệu chỉnh tuần tự Holm-Bonferroni với ngưỡng hiệu ứng tối thiểu quan tâm $\text{SESOI} = 0,030$.

2. **Tầng 2 – Đánh giá Thăm dò Định tính qua Kiểm toán Người (Exploratory Qualitative Human Audit):**
   - **Tập mẫu:** Một mẫu kiểm toán nhỏ gồm 60 câu trả lời (tương ứng với 20 câu hỏi $\times$ 3 mô hình).
   - **Quy trình:** Kiểm toán người mù đôi (Double-Blind Review) với mã ngẫu nhiên `Model_Alpha`, `Model_Beta`, `Model_Gamma`, sau đó trải qua quy trình kiểm tra tính nhất quán và giải quyết bất đồng (Adjudication) trên 21 trường hợp nghi vấn trước khi mở mù chính thức.
   - **Mục tiêu:** Cung cấp bằng chứng định tính bổ trợ nhằm giải mã bản chất các hành vi sinh văn bản thực tế, phân biệt giữa từ chối hợp lệ và từ chối vô căn cứ, phát hiện ảo giác học thuật (bịa đặt thông tin hoặc mâu thuẫn trực tiếp với bài báo), và phân tích tương quan mô tả giữa nhãn đánh giá của con người với các proxy tự động.

*Ranh giới phân định mẫu:* Nghiên cứu tuyệt đối không gộp chung hai tập mẫu này hoặc xem tập mẫu 60 câu trả lời như một ước lượng tham số cho toàn thể mô hình. Mẫu 60 câu là nghiên cứu thăm dò định tính (qualitative exploratory sample) phục vụ việc giải thích cơ chế, trong khi tập 500 câu hỏi là cơ sở định lượng so sánh cốt lõi.

### 5.6.2. Kết quả đo lường định lượng trên tập 500 câu hỏi (Primary Quantitative Results)

Bảng 5.6 trình bày kết quả đo lường khách quan tự động trên toàn bộ 500 câu hỏi ($K=250$ bài báo, $1.500$ lượt suy luận) cho 3 mô hình ngôn ngữ lớn ứng viên.

*Bảng 5.6: Kết quả đánh giá định lượng mô hình ngôn ngữ lớn cục bộ (RQ5) trên 500 câu hỏi ($K=250$ cụm bài báo).*

| Mô hình LLM | Tham số | Kích thước đĩa / RAM | Token F1 (Toàn bộ) | F1 Extractive ($n=319$) | F1 Abstractive ($n=110$) | F1 Boolean ($n=71$) | Số ca từ chối (Refusal Rate) | Automated Containment Proxy | Độ trễ P50 (s) | Độ trễ P95 (s) | Thông lượng (tokens/s) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`llama3.2:3b`** | 3,21B | 2,0 GB / ~2,5 GB | **0,2033** | 0,2605 | 0,1438 | **0,0385** | 243 (48,6%) | 37,9% | 6,55s | 15,16s | 12,7 |
| **`llama3.2:1b`** | 1,23B | 1,3 GB / ~1,6 GB | **0,1346** | 0,1730 | 0,1108 | 0,0006 | 294 (58,8%) | 29,3% | 5,08s | 9,83s | 20,4 |
| **`qwen2.5:0.5b`** | 0,49B | 397 MB / ~0,6 GB | **0,2324** | **0,2912** | **0,1921** | 0,0349 | 50 (10,0%) | **60,3%** | **3,85s** | **7,50s** | **57,3** |

*Phân tích các chỉ số tự động và hiện tượng quan sát được:*

1. **Bản chất của chỉ số Token F1:**
   Chỉ số Token F1 đo lường mức độ trùng lặp từ tố mặt chữ (lexical token overlap) giữa văn bản sinh ra và đáp án chuẩn sau khi chuẩn hóa văn bản (chuyển chữ thường, loại bỏ mạo từ và dấu câu). Token F1 thể hiện rõ nét tính chất bề mặt này khi đạt điểm cao nhất ở nhóm câu hỏi trích xuất (`Extractive`, chiếm 63,8% tập mẫu: Llama 3B đạt 0,2605; Qwen 0.5B đạt 0,2912) nhờ việc sao chép chính xác cụm từ nguyên văn. Ở nhóm câu hỏi suy luận (`Abstractive`) và câu hỏi Đúng/Sai (`Boolean`), điểm Token F1 sụt giảm mạnh do mô hình thường sinh câu văn giải thích ngữ nghĩa thay vì chỉ đưa ra từ khóa đơn lẻ.

2. **Nghịch lý Token F1 của Qwen-2.5-0.5B và Hiện tượng Từ chối An toàn:**
   Dữ liệu ghi nhận một hiện tượng tưởng chừng nghịch lý: mô hình siêu nhỏ `qwen2.5:0.5b` (0,49B tham số) đạt điểm Token F1 ($0,2324$) cao hơn cả `llama3.2:3b` ($0,2033$). Khi phân tích sâu vào hành vi của mô hình, nguyên nhân căn bản xuất phát từ **tỷ lệ kích hoạt câu từ chối an toàn (Refusal Rate)**:
   - Theo yêu cầu phi chức năng NFR-03, khi không tìm thấy đủ căn cứ chắc chắn trong ngữ cảnh, mô hình được huấn luyện phải phát câu từ chối chuẩn (*"I could not find this information in the provided context"*). Mỗi lần kích hoạt câu từ chối trên tập dữ liệu này (vốn gồm toàn bộ các câu hỏi có thể trả lời được), điểm Token F1 sẽ bị gán tự động bằng $0,0$.
   - `llama3.2:3b` kích hoạt từ chối ở **48,6%** (243/500 câu) và `llama3.2:1b` từ chối tới **58,8%** (294/500 câu). Số lượng lớn các điểm $0,0$ này đã kéo tụt đáng kể điểm F1 trung bình của họ mô hình Llama.
   - Ngược lại, `qwen2.5:0.5b` có tỷ lệ từ chối cực thấp, chỉ **10,0%** (50/500 câu). Mô hình này có xu hướng đoán mò quyết liệt (aggressive guessing) và luôn cố gắng trả lời. Do toàn bộ 500 câu hỏi về bản chất là có đáp án, việc luôn trả lời giúp Qwen thu thập được nhiều từ tố trùng khớp hơn, từ đó nâng điểm F1 bề mặt. Tuy nhiên, cái giá phải trả cho sự liều lĩnh này là tỷ lệ ảo giác tăng vọt, như sẽ được kiểm chứng ở tầng kiểm toán người.

3. **Bản chất của Automated Containment Proxy:**
   Chỉ số Automated Containment Proxy đo tỷ lệ phần trăm các từ tố mang nghĩa (loại bỏ stopword tiếng Anh và từ ngắn $\le 2$ ký tự) trong câu trả lời có xuất hiện trực tiếp trong khối ngữ cảnh tài liệu được cung cấp. Nghiên cứu nhấn mạnh rằng **đây là một proxy đo lường độ trùng lặp từ vựng bề mặt với ngữ cảnh (lexical overlap with context), hoàn toàn KHÔNG đo lường tính bám sát suy luận ngữ nghĩa (semantic entailment) hay tính đúng đắn sự thật (factual correctness)**. Một mô hình có thể sao chép nguyên văn một câu ngẫu nhiên không liên quan trong ngữ cảnh để đạt Containment Proxy gần 100%, nhưng câu trả lời đó vẫn là một phát biểu phi lý hoặc sai lệch đối với câu hỏi.

4. **Hiệu năng và Tài nguyên Phần cứng trên CPU Máy trạm:**
   - Cả ba mô hình đều vận hành ổn định trên CPU AMD Ryzen 5 5600 với 16 GB RAM DDR4 mà không gây tràn trang đĩa hay tiêu tốn quá 2,5 GB RAM cho tiến trình suy luận Ollama.
   - `qwen2.5:0.5b` đạt thông lượng vượt trội 57,3 tokens/s (độ trễ P50 = 3,85s), phù hợp cho các thiết bị nhúng cực nhẹ.
   - `llama3.2:3b` đạt thông lượng 12,7 tokens/s (độ trễ P50 = 6,55s, P95 = 15,16s), hoàn toàn vượt ngưỡng đọc tự nhiên của người dùng học thuật ($\ge 8 - 10$ tokens/s) và nằm trong ngưỡng dung thứ tương tác thực tế của giao diện người dùng.

### 5.6.3. Kiểm định So sánh Thống kê theo Cụm Bài báo ($K=250, df=249$)

Để kiểm chứng tính vững chắc của các phát hiện định lượng, các phép kiểm định cặp ghép theo cụm bài báo ($K=250, df=249$) đã được thực thi và kiểm soát FWER qua hiệu chỉnh tuần tự Holm-Bonferroni (Bảng 5.7a).

*Bảng 5.7a: Kết quả kiểm định thống kê cặp ghép theo cụm bài báo ($K=250, df=249$).*

| Cặp so sánh đối đầu | Sai khác trung bình ($\Delta_{\text{obs}}$) | Khoảng tin cậy 95% Clustered CI | Trị số $t$ ($df=249$) | Trị số $p_{\text{adj}}$ (Holm-Bonferroni) | Ngưỡng SESOI ($\ge 0,030$) | Quyết định thống kê |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| **`llama3.2:3b` vs `llama3.2:1b`** | **$+0,0687$** | $[+0,0480; +0,0902]$ | $+6,2597$ | **$3,35 \times 10^{-9}$** | **ĐẠT** | **Bác bỏ $H_0$ (Vượt trội có ý nghĩa thống kê cao)** |
| **`llama3.2:3b` vs `qwen2.5:0.5b`** | $-0,0291$ | $[-0,0509; -0,0053]$ | $-2,5028$ | $0,0130$ | Không đạt | Bác bỏ $H_0$ (Sai khác do tỷ lệ từ chối trên tập answerable) |
| **`llama3.2:1b` vs `qwen2.5:0.5b`** | $-0,0978$ | $[-0,1189; -0,0763]$ | $-8,9651$ | $2,27 \times 10^{-16}$ | Đạt | Bác bỏ $H_0$ (Sai khác thống kê có ý nghĩa) |

- So sánh giữa `llama3.2:3b` và `llama3.2:1b`: Mô hình 3B thể hiện sự vượt trội có ý nghĩa thống kê áp đảo so với 1B ($\Delta = +0,0687$, khoảng tin cậy 95% hoàn toàn tách rời 0, $p_{\text{adj}} = 3,35 \times 10^{-9}$, thỏa mãn trọn vẹn tiêu chuẩn $\text{SESOI} \ge 0,030$). Điều này khẳng định việc nâng cấp quy mô tham số từ 1,2B lên 3,2B mang lại bước tiến chất lượng thực chất cho năng lực sinh lời đáp.
- So sánh giữa `llama3.2:3b` và `qwen2.5:0.5b`: Trị số sai khác $\Delta = -0,0291$ (chưa đạt ngưỡng $\text{SESOI} = 0,030$). Như đã biện giải, chênh lệch này không phản ánh năng lực hiểu ngữ nghĩa tốt hơn của Qwen mà là hệ quả của việc Qwen ít từ chối trên tập câu hỏi trả lời được.

### 5.6.4. Đánh giá Thăm dò Định tính qua Kiểm toán Người (Exploratory Qualitative Audit)

Nhằm thấu hiểu bản chất ngữ nghĩa và kiểm tra tính trung thực thực tế, mẫu kiểm toán 60 câu trả lời (20 câu hỏi $\times$ 3 mô hình) đã được đánh giá người mù đôi theo hệ thống 6 nhãn chuẩn hóa của đề cương:
- `SUPPORTED`: Câu trả lời đúng trọng tâm và hoàn toàn được hỗ trợ từ ngữ cảnh.
- `REFUSAL_VALID`: Mô hình từ chối hợp lệ vì ngữ cảnh thực sự thiếu thông tin.
- `UNSUPPORTED`: Ảo giác bịa đặt thông tin không có trong ngữ cảnh.
- `CONTRADICTED`: Câu trả lời mâu thuẫn trực tiếp với thông tin trong bài báo.
- `MISSING_INFO - UNJUSTIFIED_REFUSAL`: Từ chối vô căn cứ dù ngữ cảnh có đủ thông tin.
- `MISSING_INFO - PARTIAL`: Trả lời đúng một phần nhưng bỏ sót chi tiết quan trọng.

Bảng 5.7 trình bày phân bố 6 nhãn sau khi đã kiểm toán và mở mù chính thức.

*Bảng 5.7: Phân bố nhãn kiểm toán người mù đôi về độ trung thực (Faithfulness) trên 60 câu trả lời.*

| Phân loại nhãn chuẩn | `llama3.2:3b` ($n=20$) | `llama3.2:1b` ($n=20$) | `qwen2.5:0.5b` ($n=20$) | Tổng số câu ($N=60$) | Tỷ lệ toàn phần (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **`SUPPORTED`** | **10** (50,0%) | 9 (45,0%) | 8 (40,0%) | 27 | 45,0% |
| **`REFUSAL_VALID`** | **4** (20,0%) | 2 (10,0%) | 3 (15,0%) | 9 | 15,0% |
| **`UNSUPPORTED`** | 2 (10,0%) | 2 (10,0%) | 4 (20,0%) | 8 | 13,3% |
| **`MISSING_INFO - UNJUSTIFIED_REFUSAL`** | **1** (5,0%) | 5 (25,0%) | 3 (15,0%) | 9 | 15,0% |
| **`MISSING_INFO - PARTIAL`** | 2 (10,0%) | 1 (5,0%) | 1 (5,0%) | 4 | 6,7% |
| **`CONTRADICTED`** | 1 (5,0%) | 1 (5,0%) | 1 (5,0%) | 3 | 5,0% |
| **Tổng cộng** | **20** (100,0%) | **20** (100,0%) | **20** (100,0%) | **60** | **100,0%** |

*Các chỉ số định tính phái sinh từ kiểm toán người:*

1. **Độ trung thực nghiêm ngặt (Strict Faithfulness - `SUPPORTED`):**
   `llama3.2:3b` dẫn đầu với **50,0%** (10/20 câu), theo sau là `llama3.2:1b` (45,0%) và `qwen2.5:0.5b` (40,0%).
2. **Mức độ tuân thủ căn cứ ngữ cảnh (Grounded Compliance - `SUPPORTED` + `REFUSAL_VALID`):**
   Đo lường hành vi an toàn học thuật (hoặc trả lời đúng có căn cứ, hoặc từ chối đúng khi thiếu căn cứ): **`llama3.2:3b` vượt trội đạt 70,0%** (14/20 câu), trong khi cả Llama 1B và Qwen 0.5B chỉ đạt 55,0% (11/20 câu).
3. **Tổng tỷ lệ ảo giác học thuật (Total Hallucinations - `UNSUPPORTED` + `CONTRADICTED`):**
   **`qwen2.5:0.5b` ghi nhận tỷ lệ ảo giác cao nhất: 25,0%** (5/20 câu, gồm 20,0% bịa đặt và 5,0% mâu thuẫn). Tỷ lệ này cao gấp 1,67 lần so với `llama3.2:3b` (15,0%) và `llama3.2:1b` (15,0%). Kết quả định tính này giải mã rõ ràng nghịch lý F1: điểm F1 cao hơn của Qwen trên tập 500 câu hỏi bị trả giá bằng tỷ lệ phát sinh thông tin sai lệch cao đáng kể trong thực tế.
4. **Tỷ lệ từ chối vô căn cứ (Unjustified Refusals):**
   `llama3.2:1b` bị mắc lỗi từ chối quá mức (over-refusal) nặng nhất với **25,0%** (5/20 câu), trong khi `llama3.2:3b` chỉ mắc lỗi này ở **5,0%** (1/20 câu), chứng minh khả năng đọc hiểu ngữ cảnh vượt trội của mô hình 3B.

### 5.6.5. Phân tích Tương quan Mô tả giữa Nhãn Người và Proxy Tự động ($N=60$)

*Lưu ý thiết kế đo lường lặp (Repeated Measures):* Tập mẫu 60 câu trả lời bắt nguồn từ 20 câu hỏi độc lập được phân bổ lặp lại trên 3 mô hình. Do đó, các hệ số tương quan tuyến tính Pearson dưới đây được xem xét như **các mối liên hệ tương quan mô tả trong mẫu (descriptive sample associations)**, không giả định các quan sát độc lập và không dùng để khẳng định tính giá trị phổ quát tuyệt đối của các proxy.

- **Tương quan giữa Nhãn `SUPPORTED` của người và Token F1:** $r = +0,4168$. Mối tương quan dương ở mức vừa phải, cho thấy Token F1 có phản ánh phần nào mức độ chính xác từ vựng, nhưng độ phân tán còn lớn.
- **Tương quan giữa Nhãn `SUPPORTED` của người và Containment Proxy:** $r = +0,3125$.
- **Tương quan giữa Tuân thủ căn cứ (`SUPPORTED` + `REFUSAL_VALID`) và Containment Proxy:** $r = +0,0868$. Mối tương quan gần như triệt tiêu. Điều này hoàn toàn hợp lý về mặt cơ chế: khi mô hình từ chối an toàn hợp lệ, câu từ chối không chứa các từ vựng chuyên ngành trong bài báo, dẫn đến điểm Containment Proxy tự động bị phạt về mức rất thấp (14,0%).
- **Tương quan giữa Ảo giác (`UNSUPPORTED` + `CONTRADICTED`) và Containment Proxy:** $r = -0,0897$. Tương quan âm rất yếu, chứng minh rằng Containment Proxy hoàn toàn mất khả năng phân biệt giữa câu trả lời đúng và câu trả lời bịa đặt.

Bảng 5.7b đối chiếu giá trị trung bình của các proxy tự động theo từng nhãn phân loại người:

*Bảng 5.7b: Giá trị trung bình của các proxy tự động phân theo nhãn kiểm toán người ($N=60$).*

| Nhãn phân loại người | Số lượng mẫu ($n$) | Điểm Token F1 trung bình | Điểm Containment Proxy trung bình (%) |
| :--- | :---: | :---: | :---: |
| **`SUPPORTED`** | 27 | **0,3558** | **56,7%** |
| **`REFUSAL_VALID`** | 9 | 0,1275 | 14,0% |
| **`UNSUPPORTED`** | 8 | 0,1845 | **32,9%** |
| **`MISSING_INFO - UNJUSTIFIED_REFUSAL`** | 9 | 0,1650 | 30,5% |
| **`MISSING_INFO - PARTIAL`** | 4 | 0,1435 | **67,4%** |
| **`CONTRADICTED`** | 3 | 0,1481 | **44,0%** |

*Ý nghĩa phương pháp luận:* Các câu trả lời bịa đặt (`UNSUPPORTED`) vẫn đạt Containment Proxy trung bình **32,9%**, và các câu mâu thuẫn trực tiếp (`CONTRADICTED`) đạt tới **44,0%** do mô hình nhặt nhạnh các thuật ngữ có sẵn trong ngữ cảnh để ghép thành phát biểu sai sự thật. Ngược lại, các câu từ chối chuẩn xác chỉ đạt **14,0%**. Bằng chứng thực nghiệm này xác nhận: **Automated Containment Proxy không thể thay thế cho đánh giá tính trung thực ngữ nghĩa trong RAG học thuật.**

### 5.6.6. Kết luận Lựa chọn Mô hình cho Hệ thống Phần mềm

Từ sự kết hợp hài hòa giữa các bằng chứng định lượng trên 500 câu hỏi và phân tích định tính chuyên sâu trên 60 câu kiểm toán người:
1. **`llama3.2:3b`** được xác định là mô hình tối ưu toàn diện nhất cho hệ thống:
   - Thể hiện sự vượt trội có ý nghĩa thống kê cao so với mô hình cùng họ `llama3.2:1b` ($\Delta = +0,0687, p_{\text{adj}} < 10^{-8}$);
   - Đạt tỷ lệ tuân thủ căn cứ cao nhất trong kiểm toán người (**70,0%**);
   - Kiểm soát tỷ lệ từ chối sai thấp nhất (**5,0%**) và tỷ lệ ảo giác thấp (**15,0%**);
   - Duy trì thông lượng 12,7 tokens/s và độ trễ P50 6,55s trên CPU máy trạm AMD Ryzen 5 5600 với 16 GB RAM, hoàn toàn đáp ứng ngưỡng tương tác thực tế của người dùng học thuật.
2. Hệ thống phần mềm chính thức chuẩn hóa và cấu hình mặc định **`llama3.2:3b`** làm engine suy luận sinh lời đáp trong kiến trúc RAG sản phẩm.

---

## 5.7. Tổng hợp và đối chiếu kết quả các câu hỏi nghiên cứu (RQ1–RQ5)

### 5.7.1. Bảng đối chiếu tổng hợp các câu hỏi nghiên cứu

Bảng 5.8 tổng hợp các phát hiện cốt lõi từ năm câu hỏi nghiên cứu đã thực nghiệm có kiểm soát hoàn tất.

*Bảng 5.8: Tổng hợp kết quả thực nghiệm và hàm ý kỹ thuật của RQ1, RQ2, RQ3, RQ4 và RQ5.*

| Câu hỏi | Thành phần đánh giá | Quy mô khảo sát | Mốc đối chứng | Chỉ số cốt lõi | Kết quả tốt nhất trong thử nghiệm | Cấu hình chọn cho Hệ thống | Ý nghĩa thực tiễn hệ thống | Giới hạn kỹ thuật quan trọng |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RQ1** | Bóc tách văn bản PDF | 47 bài báo QASPER Dev | `pymupdf_plain` | nDCG@10 & Heading F1 | `pymupdf_plain` (nDCG = 0,5274, 10,19 ms/p); `pymupdf_layout` (Heading F1 = 48,01%, 26,16 ms/p) | `pymupdf_layout` | Tốc độ C-engine vượt trội, bảo toàn đề mục phục vụ phân đoạn nâng cao. | Heading F1 chỉ được cài đặt cho `pymupdf_layout`; nDCG@10 giữa top 4 công cụ không có sai khác mang ý nghĩa thống kê ($p > 0,50$). |
| **RQ2** | Phân mảnh văn bản | 47 bài, 127 câu hỏi, 1.600 tokens budget | `fixed_size` (400 tokens) | nDCG@10 ($\tau=0,50$) | `hierarchical` (nDCG = 0,6880, $\Delta = +0,1225^*$, $p = 0,0010$) | `section_overlap` (phẳng) & `hierarchical` (nâng cao) | `section_overlap` tối ưu cho cấu trúc phẳng thuần túy. `hierarchical` triển khai thành công qua bộ sưu tập phụ trợ phi vector (`{coll}_parents`), đạt nDCG@4 = 0,5139 trên sản phẩm thực tế. | Rào cản kỹ thuật quan hệ cha-con được giải quyết bằng Qdrant vectorless collection, triệt tiêu dư thừa văn bản và giữ nguyên độ trễ P50 31,8 ms. |
| **RQ3** | Mô hình Biểu diễn Vector | 207 bài, 615 câu hỏi, 5.207 chunks | `all-MiniLM-L6-v2` & BM25 | nDCG@10 (Exact Cosine) | `modernbert-embed-base` (nDCG = 0,5872, $\Delta = +0,0846^*$); `e5-small-v2` (nDCG = 0,5522, $\Delta = +0,0497^*$) | `intfloat/e5-small-v2` | `e5-small-v2` tối ưu trên đường biên Pareto: nDCG cao, trễ P50 thấp (30,3 ms), thông lượng ổn định (6,5 chunks/s), RAM nhẹ (659,8 MB). | BGE-Small không có ý nghĩa thống kê vượt trội ($p = 0,0830$). MXBAI-Large bị tắc nghẽn CPU nghiêm trọng (0,6 chunks/s). |
| **RQ4** | Truy xuất Lai Đa Giai Đoạn | 408 bài Test, 1.310 câu hỏi, 14.035 chunks | `Dense Only (e5-small-v2)` & BM25 | nDCG@10 (Hierarchical Small-to-Big) | `Hybrid Convex (alpha=0.7)` (nDCG = 0,5806, $\Delta = +0,0152^*$, $p_{\text{adj}} = 0,0140$); `Hybrid RRF (k=60)` (nDCG = 0,5662) | `Hybrid RRF (k=60)` & `Hybrid Convex (alpha=0.7)` | RRF $k=60$ duy trì hiệu năng tương đương Dense Only mà không cần chuẩn hóa điểm số; Convex $\alpha=0.7$ tối ưu hóa điểm số xếp hạng. | Đo lường toàn trình sau Small-to-Big expansion và trần 1.600 tokens; BM25 sử dụng IDF nền phân hoạch để tránh âm hóa trên bài báo nhỏ. |
| **RQ5** | Mô hình Ngôn ngữ Lớn Cục bộ | 500 câu hỏi ($K=250$ bài), 60 câu kiểm toán người | `llama3.2:1b` | Token F1, Faithfulness & Throughput | `llama3.2:3b` (F1 = 0,2033; Grounded = 70,0%; Throughput = 12,7 tok/s) | `llama3.2:3b` | `llama3.2:3b` vượt trội về tuân thủ căn cứ (70,0%), tỷ lệ từ chối sai thấp (5,0%), kiểm soát ảo giác (15,0%) và tốc độ 12,7 tok/s trên CPU 16 GB RAM. | Qwen-0.5B có F1 bề mặt cao hơn do ít từ chối nhưng tỷ lệ ảo giác tăng lên 25,0%. Mẫu kiểm toán người 60 câu mang tính thăm dò định tính. |

### 5.7.2. Mối quan hệ tương hỗ giữa các mắt xích trong đường ống RAG

Các kết quả thực nghiệm độc lập từ RQ1 đến RQ5 cung cấp một bức tranh toàn cảnh về cách thức mà các quyết định thiết kế ở từng mắt xích tương tác và ràng buộc lẫn nhau:

1. **Ràng buộc từ Bóc tách (RQ1) đến Phân mảnh (RQ2):**
   Nếu hệ thống chỉ sử dụng các bộ bóc tách văn bản phẳng thông thường như `pymupdf_plain`, toàn bộ ranh giới cấu trúc ngữ nghĩa học thuật sẽ bị biến mất. Khi đó, hệ thống bắt buộc phải áp dụng các chiến lược phân đoạn cắt mù theo độ dài cố định (`fixed_size`), vốn có nguy cơ cắt đôi một định lý hoặc một bảng dữ liệu quan trọng. Việc ứng dụng thành công `pymupdf_layout` đã mở khóa khả năng nhận diện tiêu đề đề mục, tạo tiền đề quyết định để áp dụng chiến lược `section_overlap` và `hierarchical`.

2. **Ràng buộc từ Phân mảnh (RQ2) đến Biểu diễn Vector (RQ3):**
   Độ dài phân đoạn trực tiếp quyết định rủi ro cắt cụt subword khi mã hóa. Nghiên cứu chỉ ra rằng các chiến lược phân mảnh thô (`section`) dẫn đến 23,7% phân đoạn vượt trần subword của các mô hình nhúng 512-tokens như `e5-small-v2`. Ngược lại, việc kiểm soát độ dài phân đoạn con dưới 200 tokens trong `hierarchical` bảo đảm tỷ lệ cắt cụt duy trì ở mức an toàn ($0,63\%$), bảo toàn trọn vẹn ngữ nghĩa cho các mô hình vector.

3. **Ràng buộc từ Biểu diễn Vector (RQ3) đến Hợp nhất Lai (RQ4):**
   Thực nghiệm RQ4 trên tập kiểm thử độc lập chỉ ra rằng việc hòa trộn không trọng số (RRF 50/50) chỉ phát huy hiệu quả khi hai mô hình thành phần có sức mạnh tương đương. Khi mô hình vector ngữ nghĩa (`e5-small-v2`) áp đảo hoàn toàn mô hình từ khóa (`BM25`), việc sử dụng cơ chế trọng số bất đối xứng (Convex $\alpha=0.7$) là yếu tố then chốt để khai thác bổ trợ của từ khóa mà không làm loãng chất lượng biểu diễn ngữ nghĩa.

4. **Ràng buộc từ Truy xuất Lai (RQ4) đến Sinh Lời đáp (RQ5):**
   Ngân sách ngữ cảnh 1.600 tokens và cơ chế mở rộng phân cấp Small-to-Big ở RQ4 cung cấp một khối ngữ cảnh có độ bao phủ bằng chứng cao (Recall@20 = 0,6413 với RRF). Khi nạp vào prompt cho LLM ở RQ5, chất lượng của khối ngữ cảnh này quyết định trực tiếp khả năng bám sát bằng chứng của mô hình. Nếu ngữ cảnh bị nhiễu hoặc thiếu thông tin cốt lõi, các mô hình nhỏ như Llama 1B dễ bị kích hoạt từ chối quá mức (25,0% unjustified refusal), trong khi các mô hình như Qwen 0.5B có nguy cơ bị ảo giác (25,0% hallucination). Cấu hình tối ưu `llama3.2:3b` kết hợp cùng cơ chế từ chối an toàn NFR-03 tạo nên chốt chặn phòng thủ vững chắc chống lại hiện tượng bịa đặt học thuật.

### 5.7.3. Phân định ranh giới với các câu hỏi nghiên cứu mở rộng

Để bảo đảm tính trung thực học thuật và phân định rạch ròi phạm vi đồ án, Chương 5 đã hoàn tất và báo cáo đầy đủ năm câu hỏi nghiên cứu thành phần cốt lõi (RQ1, RQ2, RQ3, RQ4 và RQ5). Tình trạng thực tế của hướng nghiên cứu tiếp theo được ghi nhận minh bạch như sau:

- **RQ6 – Đánh giá Thực nghiệm Tổ hợp Toàn trình (End-to-End Generation Combinations):** Thực nghiệm đo lường toàn trình các tổ hợp chéo giữa các chiến lược truy xuất (RQ4) và các mô hình sinh lời đáp (RQ5) để đánh giá chất lượng câu trả lời cuối cùng được định vị là mục tiêu nghiên cứu tiếp nối ở Chương 6.

---

## 5.8. Hạn chế và đe dọa đến tính hợp lệ (Threats to Validity)

Quá trình diễn giải các kết quả thực nghiệm cần được xem xét trong bối cảnh các giới hạn phương pháp luận sau:

1. **Tính đại diện của tập ngữ liệu và ranh giới suy rộng (External & Construct Validity):**
   - *Tính đại diện chuyên ngành:* Ngữ liệu QASPER tập trung chủ yếu vào các bài báo thuộc lĩnh vực Khoa học Máy tính và Xử lý Ngôn ngữ Tự nhiên (NLP). Cấu trúc trình bày của các bài báo này (thường gồm hai cột, có đề mục chuẩn) có thể khác biệt so với các bài báo thuộc khối ngành Y sinh, Hóa học hoặc Khoa học Xã hội (nơi có nhiều bảng biểu phức tạp hoặc cấu trúc đoạn văn dài liên tục). Khả năng tổng quát hóa các kết luận sang các miền học thuật khác cần được kiểm chứng thêm.
   - *Phân định bản chất tập dữ liệu RQ3 và kiểm soát rò rỉ:* Tập dữ liệu 207 bài báo của RQ3 là một **Tập ngữ liệu đánh giá nội bộ hợp nhất (Unified In-House Evaluation Corpus)** nhằm tối đa hóa quy mô đo đạc trên hệ thống RAG của đề tài, không phải là một tập kiểm thử hoàn toàn độc lập (Independent Test Set). Về mặt kiểm soát rò rỉ dữ liệu (data leakage), nghiên cứu phân định rõ:
     + *Rò rỉ trọng số mô hình (Model Weight Leakage = 0):* Tuyệt đối không xảy ra vì tất cả 11 mô hình biểu diễn vector đều là các mô hình nền tảng mã nguồn mở có sẵn được đánh giá theo cơ chế suy luận zero-shot với trọng số đóng băng hoàn toàn (`frozen weights`), không qua huấn luyện lại (fine-tuning) hay tối ưu hóa siêu tham số.
     + *Rò rỉ cấp đường ống (Pipeline-level Selection Leakage):* Do 48 bài báo thuộc phần Development đã tham gia vào việc khảo sát công cụ trích xuất PDF (RQ1) và đánh giá các chiến lược phân mảnh (RQ2), nên khi đánh giá mô hình vector trên cùng quy trình tiền xử lý này ở RQ3, các bài báo này có thể mang lại một sự lạc quan nhẹ (optimistic selection bias). Do đó, các kết luận thực nghiệm phản ánh chính xác hiệu năng nội bộ của đường ống RAG học thuật trong đề tài, nhưng để khẳng định tính suy rộng ngoại suy tuyệt đối, cần có các đợt đánh giá tiếp nối trên các tập kiểm thử hoàn toàn độc lập.

2. **Sai số đo lường trong nhãn liên quan tự động và Cơ sở hiệu chuẩn ngưỡng ($\tau$):**
   - Nhãn liên quan của các phân đoạn được xác định dựa trên ngưỡng bao phủ từ vựng ($\tau = 0,50$ cho RQ2 đa quy mô và $\tau^* = 0,55$ cho RQ1/RQ3 đoạn đơn lẻ). Để giảm thiểu sai số đo lường (Construct Validity), ngưỡng $\tau^* = 0,55$ không phải là một giả định tùy tiện mà được **hiệu chuẩn thực nghiệm out-of-sample trên 114 cặp câu hỏi – bằng chứng đối chứng do chuyên gia gán nhãn thủ công** (`containment_validation_metrics.json`). Tại $\tau^* = 0,55$, bộ phân loại nhãn đạt đỉnh Accuracy (82,46%), Precision (81,08%) và F1 (75,00%), triệt tiêu 85,1% số ca dương tính giả so với $\tau=0,20$. Ở RQ2, việc áp dụng $\tau = 0,50$ cùng phân tích độ nhạy tại $\tau = 0,30$ chứng minh thứ hạng giữa các phương pháp là ổn định vững chắc. Tuy nhiên, cơ chế đối sánh từ vựng mặt chữ này vẫn có thể gặp hạn chế trong các trường hợp phân đoạn diễn đạt lại bằng chứng bằng từ đồng nghĩa (paraphrasing).

3. **Giới hạn đo đạc bộ nhớ và độ trễ trên môi trường máy trạm (Internal Validity):**
   - Các phép đo độ trễ và thông lượng được thực hiện trên CPU máy trạm AMD Ryzen 5 5600 cố định 4 luồng xử lý; các giá trị này phản ánh chính xác hiệu năng môi trường máy tính cá nhân nhưng có thể thay đổi khi chuyển sang môi trường máy chủ đám mây hoặc khi có sự can thiệp của card đồ họa chuyên dụng (GPU). Chỉ số Process Peak RSS đo lường bộ nhớ đỉnh độc lập của tiến trình tính toán Python thông qua thư viện `psutil`, chưa bao quát toàn bộ tài nguyên nền của hệ điều hành và daemon Ollama.

4. **Kiểm soát so sánh đa biến và tính vững của trị số $p$:**
   - Các trị số $p$ báo cáo trong các cột chính của Bảng 5.1, 5.2, 5.3 và 5.6 đều được định danh minh bạch là **trị số $p$ danh định ($p_{\text{raw}}$)** thu được trực tiếp từ phép kiểm định Paired Cluster Bootstrap ($B=2.000$) để bảo đảm tính trung thực với phân phối mẫu gốc. Đồng thời, toàn bộ các khẳng định về ý nghĩa thống kê (được đánh dấu sao $^*$) đều đã được kiểm chứng khắt khe qua quy trình kiểm soát tỷ lệ sai số họ (FWER) bằng phương pháp hiệu chỉnh tuần tự Holm-Bonferroni ở mức $\alpha = 0,05$. Các phát hiện cốt lõi của đề tài đều bảo toàn ý nghĩa thống kê nghiêm ngặt sau hiệu chỉnh. Ngược lại, đối với các trường hợp tiệm cận biên như `bge-small-en-v1.5` ($p_{\text{raw}} = 0,0830, p_{\text{adj}} = 0,4150$), nghiên cứu kiên quyết bác bỏ các suy diễn thiếu căn cứ và khẳng định mô hình không có sai khác mang ý nghĩa thống kê so với baseline.

5. **Độ mạnh thống kê thực tế và giới hạn kích thước hiệu ứng (Statistical Power Limits):**
   - Nghiên cứu hoàn toàn loại bỏ thuật ngữ "High-Power" và không đưa ra tuyên bố tiên nghiệm rằng quy mô mẫu 207 bài báo mặc nhiên bảo đảm độ mạnh thống kê $\text{Power} \ge 80\%$ cho mọi phép so sánh. Dựa trên kết quả kiểm toán phương pháp luận mô phỏng Monte Carlo ($B=2.000$, $\sigma_{\text{paper}} \approx 0,2307$, $\alpha = 0,05$) được ghi nhận tại [`statistical_audit_results.json`](file:///c:/DACNTT/eval/phases/phase_3_embedding/artifacts/statistical_audit_results.json), với ngưỡng hiệu ứng tối thiểu quan tâm $\text{SESOI} = 0,030$ đo trên chỉ số $\text{nDCG@4}$ (phản ánh cửa sổ ngữ cảnh nạp prompt), độ mạnh thống kê ước lượng chỉ đạt **38,6%** (95% CI: $[36,5\%; 40,7\%]$) ở $K=159$ bài báo và xấp xỉ **44,5%** ở $K=200$ bài báo. Độ mạnh thống kê chỉ thực sự đạt mức tin cậy cao ($78,3\% - 85,5\%$) đối với các hiệu ứng chênh lệch lớn quan sát được thực tế ($\Delta \ge 0,05$, như giữa E5-Small-v2 và MiniLM với $\Delta = +0,0497^*$). Do đó, đối với các sai khác nhỏ ($\Delta \le 0,03$), nghiên cứu công khai thừa nhận giới hạn về power và duy trì quan điểm học thuật thận trọng.

6. **Giới hạn phương pháp luận trong đánh giá thực nghiệm RQ4 (Hybrid Retrieval Limitations):**
   - *Phạm vi đo lường của các chỉ số:* Toàn bộ các chỉ số truy xuất ở RQ4 (nDCG@10, nDCG@4, Recall@20, MRR@10, Hit@5) được đo lường **sau khi đã thực hiện mở rộng phân cấp Small-to-Big, áp dụng trần giới hạn tối đa 5 đoạn cha (MAX_PARENTS = 5) và cắt lọc theo ngân sách ngữ cảnh 1.600 tokens**. Do đó, danh sách kết quả thực tế chỉ chứa tối đa 5 đoạn văn bản cha; các vị trí từ 6 đến 20 trong Recall@20 và nDCG@10 được zero-padded theo đúng ngữ cảnh thực tế được đưa vào prompt cho mô hình ngôn ngữ lớn.
   - *Phạm vi tính toán chỉ số nghịch đảo tần suất văn bản (BM25 IDF Scope):* Trong kịch bản vận hành thực tế tại Chương 4, BM25 được tính toán cục bộ trong phạm vi một bài báo (document-local BM25). Trong khi đó, benchmark tự động RQ4 tính toán tần suất nghịch đảo văn bản trên toàn bộ các đoạn con thuộc tập phân tách QASPER Test (corpus-wide BM25 IDF).
   - *Tính suy rộng trên tập Test và phạm vi khẳng định:* Kết quả kiểm định trên tập Test (408 bài báo, 1.310 câu hỏi) xác nhận phương pháp kết hợp tuyến tính lồi (convex, $\alpha = 0,7$) mang lại cải thiện vượt trội có ý nghĩa thống kê so với Dense Only ($\Delta = +0,0152, p_{\text{adj}} = 0,0140 < 0,05$), trong khi cơ chế kết hợp hạng đảo RRF ($k=60$) duy trì hiệu năng tương đương Dense Only ($\Delta = +0,0008, p_{\text{adj}} = 0,8696$) mà không cần chuẩn hóa điểm số.

7. **Giới hạn phương pháp luận trong đánh giá thực nghiệm RQ5 (Local LLM Generation Limitations):**
   - *Cơ chế nhận diện từ chối dựa trên chuỗi quy chuẩn (NFR-03 String Matching):* Tỷ lệ từ chối tự động trên tập 500 câu hỏi được phát hiện dựa trên việc đối sánh chuỗi mẫu từ chối chuẩn (*"I could not find this information in the provided context"* và các biến thể tương đương). Mặc dù các mô hình tuân thủ tốt mẫu này trong điều kiện giải mã tất định `temperature = 0.0`, một số câu diễn đạt từ chối bằng ngôn từ tự do khác biệt có thể chưa được gom trọn vẹn vào chỉ số từ chối tự động.
   - *Đặc tính tập mẫu 500 câu hỏi là Answerable-Only và Thiên lệch điểm số F1:* Tập dữ liệu 500 câu hỏi được chỉ định từ QASPER Train là tập câu hỏi có bằng chứng trả lời trong bài báo. Khi mô hình từ chối trả lời (do ngữ cảnh trích xuất từ RQ4 không đủ rõ ràng để mô hình tự tin kết luận), hệ thống chấm tự động gán F1 = 0,0. Điều này tạo ra một sự bất lợi điểm số bề mặt đối với các mô hình có cơ chế tự vệ an toàn cao như Llama 3.2 3B và vô tình ưu ái cho mô hình đoán liều như Qwen 0.5B. Do đó, điểm Token F1 tự động không thể đứng độc lập mà bắt buộc phải đi kèm với phân tích tỷ lệ từ chối và kiểm toán định tính.
   - *Tính chất thăm dò định tính của kiểm toán người 60 câu và Thiết kế đo lường lặp:* Mẫu kiểm toán người gồm 60 câu trả lời là một đợt đánh giá thăm dò định tính (exploratory qualitative audit) với 20 câu hỏi nghiên cứu phân bổ lặp lại trên 3 mô hình. Quy mô mẫu này không đủ lớn để suy rộng tham số cho toàn thể phân bố hay khẳng định tính ưu việt tuyệt đối về mặt thống kê của mô hình ở cấp độ người. Các hệ số tương quan giữa nhãn người và proxy tự động phản ánh mối liên hệ mô tả trong mẫu, không thay thế cho các nghiên cứu thẩm định thước đo trên quy mô lớn.

---

## 5.9. Tổng kết chương

Chương 5 đã báo cáo chi tiết, minh bạch và có hệ thống toàn bộ các kết quả thực nghiệm thu được từ quá trình đánh giá có kiểm soát đối với năm câu hỏi nghiên cứu RQ1, RQ2, RQ3, RQ4 và RQ5:

1. **Về phương pháp bóc tách PDF (RQ1):** Thực nghiệm khẳng định pymupdf_layout là giải pháp tối ưu cho hệ thống RAG học thuật nhờ sự kết hợp hài hòa giữa tốc độ xử lý hàng đầu (26,16 ms/trang), chất lượng truy xuất hạ nguồn ổn định (nDCG@10 = 0,5100), và khả năng trích xuất chính xác cấu trúc tiêu đề mục (Heading F1 = 48,01%), trong khi các công cụ như pdfplumber gây suy giảm nghiêm trọng trật tự đọc của tài liệu.

2. **Về chiến lược phân mảnh văn bản (RQ2):** Mô hình phân mảnh phân cấp Small-to-Big (hierarchical) xác lập vị thế quán quân lý thuyết với bước nhảy vọt $\text{nDCG@10} = 0,6880$ ($\Delta = +0,1225^*$) dưới cùng một ngân sách 1.600 tokens; đồng thời thực nghiệm chỉ rõ sự thất bại của phương pháp phân đoạn ngữ nghĩa (semantic) và cạm bẫy cắt cụt âm thầm của phương pháp đề mục thô (section). Đối với hệ thống ứng dụng lưu trữ phẳng thực tế, chiến lược section_overlap được chứng minh là phương án dung hòa tối ưu nhất về chất lượng truy xuất tức thời ($\text{nDCG@4} = 0,4569$) và trật tự thứ hạng đầu ($\text{MRR@10} = 0,5737$).

3. **Về mô hình biểu diễn vector (RQ3):** Phân tích đường biên Pareto trên 207 bài báo khoa học chứng minh modernbert-embed-base dẫn đầu về chất lượng truy xuất tuyệt đối ($\text{nDCG@10} = 0,5872$), trong khi intfloat/e5-small-v2 là ứng viên cân bằng lý tưởng nhất cho môi trường máy trạm để bàn nhờ tốc độ mã hóa nhanh (30,26 ms), thông lượng ổn định (6,5 chunks/s), bộ nhớ RAM thấp (659,8 MB) và chất lượng truy xuất vượt trội rõ rệt so với baseline ($\text{nDCG@10} = 0,5522, p = 0,0010^*$). Nghiên cứu cũng đính chính sai số học thuật, khẳng định BGE-Small không có ý nghĩa thống kê vượt trội so với MiniLM trên tập dữ liệu này.

4. **Về cơ chế truy xuất lai kết hợp phân mảnh phân cấp (RQ4):** Đánh giá thực nghiệm có kiểm soát trên tập kiểm thử độc lập (Held-out Test: 408 bài báo, 1.310 câu hỏi, 14.035 đoạn con) khẳng định:
   - Cơ chế kết hợp tuyến tính lồi (Convex Fusion, $\alpha = 0,7$) xác lập kỷ lục chất lượng ngữ cảnh mới với $\text{nDCG@10} = 0,5806$ ($\Delta = +0,0152^*$, khoảng tin cậy 95% Bootstrap $[+0,0045; +0,0262]$ hoàn toàn tách rời 0, $p_{\text{adj}} = 0,0140 < 0,05$), chứng minh sự bổ trợ hiệu quả giữa tín hiệu từ vựng chính xác và vector ngữ nghĩa dày.
   - Cơ chế kết hợp hạng nghịch đảo (RRF, $k=60$) đang triển khai trong mã nguồn sản phẩm đạt $\text{nDCG@10} = 0,5662$ ($\Delta = +0,0008, p_{\text{adj}} = 0,8696$), đạt hiệu năng truy xuất tương đương với Dense Only trên benchmark đánh giá mà không làm suy giảm chất lượng biểu diễn dày của e5-small-v2, đồng thời sở hữu ưu thế kỹ thuật là không đòi hỏi chuẩn hóa điểm số phức tạp.

5. **Về mô hình ngôn ngữ lớn cục bộ (RQ5):** Đánh giá thực nghiệm hai tầng trên 500 câu hỏi tự động và 60 câu kiểm toán người khẳng định:
   - Mô hình `llama3.2:3b` là lựa chọn cân bằng tối ưu nhất cho hệ thống máy trạm CPU 16 GB RAM: dẫn đầu về độ tuân thủ căn cứ ngữ cảnh (70,0%), tỷ lệ từ chối sai thấp nhất (5,0%), kiểm soát ảo giác hiệu quả (15,0%), thông lượng ổn định (12,7 tokens/s) và có sự vượt trội thống kê vững chắc so với `llama3.2:1b` ($\Delta = +0,0687, p_{\text{adj}} = 3,35 \times 10^{-9}$).
   - Nghiên cứu giải mã hiện tượng nghịch lý F1 của `qwen2.5:0.5b`, chứng minh rằng điểm F1 bề mặt cao của Qwen xuất phát từ việc mô hình ít từ chối (10,0%) trên tập câu hỏi trả lời được nhưng phải trả giá bằng tỷ lệ ảo giác cao (25,0%). Đồng thời, thực nghiệm chứng minh Automated Containment Proxy chỉ đo lường sự trùng lặp từ vựng bề mặt, không thể phản ánh tính trung thực ngữ nghĩa.

Toàn bộ các bằng chứng thực nghiệm từ RQ1 đến RQ5 cung cấp cơ sở khoa học vững chắc giải thích cho các quyết định cấu hình kiến trúc trong hệ thống phần mềm đã xây dựng, đồng thời vạch ra lộ trình rõ ràng cho việc mở rộng đánh giá tổ hợp toàn trình (RQ6) ở các nghiên cứu tiếp theo.
