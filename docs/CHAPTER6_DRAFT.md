# CHƯƠNG 6. KẾT LUẬN VÀ HƯỚNG PHÁT TRIỂN

---

## 6.1. Tổng kết các Kết quả Đạt được của Đồ án

Đồ án tốt nghiệp *"Xây dựng hệ thống quản lý tài liệu nghiên cứu khoa học tích hợp trợ lý AI sử dụng RAG"* đã hoàn thành trọn vẹn cả hai mục tiêu nghiên cứu và kỹ thuật đề ra ban đầu:

### 6.1.1. Về mặt Xây dựng Sản phẩm Phần mềm (Engineering Deliverables)

Hệ thống ứng dụng web quản lý tài liệu học thuật đã được phân tích, thiết kế và xây dựng hoàn chỉnh theo phong cách kiến trúc Khối đơn mô-đun hóa (Modular Monolith), vận hành ổn định trên máy trạm cá nhân thông thường (CPU đa luồng, 16 GB RAM, không yêu cầu GPU) mà không phụ thuộc vào bất kỳ dịch vụ AI đám mây nào:
1. **Giao diện Người dùng Hiện đại và Chuyên nghiệp:** Tái hiện bố cục 3 cột kinh điển chuẩn mực của Zotero với React 19, TypeScript và CSS Modules; hỗ trợ quản lý cây thư mục phân cấp với thuật toán truy vấn $O(N)$ triệt tiêu lỗi $N+1$; quản lý và biên tập hướng dữ liệu đầy đủ 22 trường siêu dữ liệu học thuật; phân định rạch ròi giữa Thẻ từ khóa (Tags) và Lĩnh vực chuyên ngành (Domains); trang bị hệ thống phím tắt trình duyệt tiện dụng (`Ctrl+1..9`, `Ctrl+F`).
2. **Trình đọc PDF Tương tác và Đồng bộ Chú thích:** Tích hợp thư viện PDF.js với lớp văn bản TextLayer cho phép bôi đen tài liệu hai cột tự nhiên; hỗ trợ bôi đậm đa màu và ghim ghi chú nổi (Sticky Notes) tự do trên Canvas; tọa độ chú thích được chuẩn hóa theo tỷ lệ phần trăm trang và đồng bộ thời gian thực với cơ sở dữ liệu PostgreSQL.
3. **Quy trình Xử lý và Tra cứu Siêu dữ liệu Đa tầng:** Tự động trích xuất tiêu đề và định danh (arXiv ID, DOI) ngay khi người dùng kéo thả tệp PDF vào giao diện; kết nối tự động với Crossref API và cơ chế dự phòng OpenAlex API để điền tự động các trường siêu dữ liệu học thuật.
4. **Đường ống RAG Tiếp đất và Trợ lý AI Cục bộ:** Hiện thực hóa thành công đường ống xử lý luồng ngầm daemon thread kết hợp mô hình nhúng `intfloat/e5-small-v2` và kho vector nhúng Qdrant SQLite theo mô hình Hai Bộ sưu tập Song hành (Companion Vectorless Collections); áp dụng cơ chế truy xuất lai kết hợp Dense Cosine và Lexical BM25 qua thuật toán Reciprocal Rank Fusion ($k=60$); thực thi ngưỡng ngắt từ chối an toàn `0.80` loại bỏ hoàn toàn nguy cơ ảo giác khi câu hỏi lạc đề; tích hợp mô hình ngôn ngữ lớn `llama3.2:3b` cục bộ qua Ollama với cơ chế dự phòng tất định khi ngoại tuyến.
5. **Định vị và Bôi đậm Trích dẫn In-Canvas:** Mỗi câu trả lời của trợ lý AI được liên kết chính xác với số trang tài liệu; người dùng nhấp vào huy hiệu trích dẫn `[Page X]` sẽ kích hoạt cuộn trang mượt mà trên trình đọc PDF, hiển thị banner robot nổi (`🤖 Cited Section: <Title>`) và bôi đậm trực tiếp ranh giới đoạn văn bằng chứng trên trang văn bản.

Toàn bộ hệ thống phần mềm đã được kiểm chứng qua 42 bài kiểm thử tự động toàn diện tại `apps.documents.tests` và `apps.users.tests`, bảo đảm chất lượng mã nguồn và tính sẵn sàng vận hành thực tế.

---

### 6.1.2. Về mặt Nghiên cứu Thực nghiệm và Đóng góp Phương pháp luận (Scientific Deliverables)

Bám sát tinh thần trung thực học thuật và phân định rạch ròi phạm vi dữ liệu, đề tài đã hoàn tất quy trình thực nghiệm có kiểm soát đối với năm câu hỏi nghiên cứu thành phần (RQ1 đến RQ5):
1. **RQ1 (Bóc tách văn bản PDF):** Khẳng định tính ưu việt của pymupdf_layout khi kết hợp hài hòa giữa tốc độ xử lý hàng đầu của C-engine (26,16 ms/trang), chất lượng truy xuất hạ nguồn ổn định (nDCG@10 = 0,5100), và khả năng nhận diện tiêu đề đề mục chuẩn xác (Heading F1 = 48,01%), đồng thời làm rõ sự sụp đổ chất lượng của pdfplumber trên tài liệu hai cột ($p = 0,0010^*$).
2. **RQ2 (Chiến lược phân mảnh văn bản):** Chứng minh mô hình phân mảnh phân cấp Small-to-Big (hierarchical) tạo ra bước nhảy vọt chất lượng truy xuất ($\\text{nDCG@10} = 0,6880$, $\\Delta = +0,1225^*, p = 0,0010^*$) dưới cùng một ngân sách 1.600 tokens; giải phẫu sự thất bại của các đoạn con thiếu ngữ cảnh cha (hierarchical_child, nDCG = 0,4473); và xác lập cơ sở thực tiễn cho chiến lược section_overlap trong môi trường lưu trữ phẳng.
3. **RQ3 (Mô hình biểu diễn vector):** Đo đạc toàn diện 11 mô hình nhúng mã nguồn mở $\\le 335\\text{M}$ tham số trên tập dữ liệu hợp nhất 207 bài báo; xác định modernbert-embed-base là ứng viên chất lượng cao nhất (nDCG@10 = 0,5872), đồng thời chứng minh intfloat/e5-small-v2 là sự lựa chọn cân bằng tối ưu nhất cho máy trạm để bàn nhờ tốc độ mã hóa nhanh (30,26 ms), thông lượng ổn định (6,5 chunks/s) và bộ nhớ RAM thấp (659,8 MB). Nghiên cứu cũng đính chính sai số học thuật về ý nghĩa thống kê của BGE-Small ({\\text{raw}} = 0,0830 > 0,05$) sau khi kiểm soát sai số họ Holm-Bonferroni.
4. **RQ4 (Cơ chế truy xuất lai kết hợp phân mảnh phân cấp):** Hoàn thành đánh giá có kiểm soát trên tập kiểm thử độc lập (Held-Out Test: 408 bài báo, 1.310 câu hỏi, 14.035 đoạn con); chứng minh cơ chế kết hợp tuyến tính lồi (Convex Fusion, $\\alpha = 0,7$) mang lại cải thiện vượt trội có ý nghĩa thống kê so với Dense Only ($\\text{nDCG@10} = 0,5806, \\Delta = +0,0152^*$, 95% CI $[+0,0045; +0,0262]$, {\\text{adj}} = 0,0140 < 0,05$$). Đồng thời ghi nhận cơ chế kết hợp hạng nghịch đảo (RRF, $k=60$) đạt hiệu năng tương đương Dense Only ($\\text{nDCG@10} = 0,5662, p_{\\text{adj}} = 0,8696$), duy trì tính tiện lợi trong triển khai thực tế do không cần chuẩn hóa điểm số, trong khi hiệu quả tăng cường độ vững trước từ khóa vẫn cần được kiểm chứng thêm qua các truy vấn biệt ngữ chuyên biệt.
5. **RQ5 (Mô hình ngôn ngữ lớn cục bộ và Kiểm toán độ trung thực):** Hoàn thành quy trình thực nghiệm có kiểm soát hai tầng gồm tầng định lượng tự động trên 500 câu hỏi ($K=250$ cụm bài báo Train chưa từng phơi nhiễm) và tầng kiểm toán người mù đôi trên 60 câu trả lời. Thực nghiệm khẳng định llama3.2:3b là mô hình tối ưu cho môi trường máy trạm CPU 16 GB RAM (70,0% tuân thủ căn cứ, 15,0% ảo giác, 5,0% từ chối sai, 12,7 tokens/s, $\\Delta = +0,0687, p_{\\text{adj}} = 3,35 \\times 10^{-9}$ so với llama3.2:1b). Đồng thời, nghiên cứu giải mã hiện tượng nghịch lý Token F1 của qwen2.5:0.5b và chứng minh tính chất proxy bề mặt của Automated Containment Proxy, khẳng định proxy này không thể thay thế cho đánh giá tính trung thực ngữ nghĩa.

## 6.2. Những Điểm Hạn chế Còn Tồn đọng

Mặc dù đã đạt được các kết quả tích cực, đồ án ghi nhận một số hạn chế kỹ thuật và phương pháp luận cần được khắc phục trong tương lai:

1. **Phạm vi Hỏi đáp Đơn tài liệu:** Hệ thống hiện tại chỉ hỗ trợ đối thoại RAG trên từng bài báo khoa học đơn lẻ đang mở trong giao diện đọc. Nhu cầu phân tích đối chiếu, tổng hợp luận điểm chéo giữa nhiều bài báo cùng chủ đề trong một thư mục nghiên cứu chưa được đáp ứng.
2. **Rào cản Tính toán CPU khi Lập chỉ mục Quy mô lớn:** Việc nhúng vector trên CPU máy tính cá nhân bằng PyTorch/SentenceTransformers (đạt thông lượng 6,5 chunks/s với E5-Small-v2) tuy đáp ứng tốt cho từng bài báo đơn lẻ (5–10 giây/bài), nhưng sẽ tạo ra độ trễ đáng kể nếu người dùng nhập đồng loạt hàng trăm bài báo vào thư viện.
3. **Bộ nhớ Hội thoại Phiên (Session Scope):** Lịch sử hỏi đáp với AI hiện chỉ được lưu tạm thời trong trạng thái bộ nhớ của giao diện người dùng và tự động làm mới khi chuyển tài liệu (đáp ứng yêu cầu phi chức năng NFR-04 nhằm tránh ô nhiễm ngữ cảnh). Hệ thống chưa hỗ trợ lưu trữ dài hạn lịch sử trao đổi theo dạng các luồng hội thoại độc lập (Threaded Chats) trong cơ sở dữ liệu.
4. **Chưa Hoàn tất Thực nghiệm Toàn trình (End-to-End Evaluation):** Trong Chương 5, nghiên cứu đã hoàn thành việc đánh giá năm mắt xích thành phần độc lập (RQ1 đến RQ5). Một đợt đánh giá thực nghiệm có kiểm soát toàn trình (End-to-End RAG Combination Pipeline - RQ6) nối liền đồng thời từ bước nạp tài liệu, bóc tách, phân mảnh, truy xuất lai đến bước sinh câu trả lời cuối cùng trên cùng một tập dữ liệu lớn chưa từng phơi nhiễm vẫn là một hướng nghiên cứu mở cần được tiếp tục hoàn thiện.

---

## 6.3. Định hướng Phát triển trong Tương lai

Từ các kết quả và hạn chế đã xác định, tác giả đề xuất 5 định hướng nghiên cứu và hoàn thiện hệ thống trọng tâm trong giai đoạn tiếp theo:

### 6.3.1. Đánh giá Thực nghiệm Cấu hình RAG Kết hợp Toàn trình (End-to-End RAG Combination Benchmark - RQ6)
Xây dựng một bộ khung đánh giá tự động (Evaluation Harness) và kiểm toán chuyên gia toàn trình trên tập dữ liệu độc lập. Khảo sát đối sánh thiết kế giai thừa $2 \times 2$ ($\{\text{fixed\_size}, \text{section\_overlap}\} \times \{\text{MiniLM}, \text{E5}\}) cùng 4 cấu hình đường ống đại diện (Quality, Balanced, Efficiency, Exploratory) đã được thiết kế tại Chương 3, kết hợp truy xuất lai Small-to-Big với mô hình sinh llama3.2:3b nhằm đo lường sự tương tác qua lại giữa các mắt xích và xác lập cấu hình toàn trình tối ưu nhất cho máy trạm CPU.

### 6.3.2. Bổ sung Mô hình Xếp hạng lại Giai đoạn hai (Cross-Encoder Reranking)
Để nâng cao hơn nữa độ chính xác trong các tình huống truy vấn học thuật hẹp, hệ thống có thể tích hợp một mô hình Cross-Encoder gọn nhẹ (như `bge-reranker-base` hoặc `ms-marco-MiniLM-L-6-v2`) để chấm điểm lại Top-20 ứng viên sau bước kết hợp RRF/Convex trước khi đưa vào ngân sách ngữ cảnh.

### 6.3.3. Phát triển Cơ chế Hỏi đáp Tổng hợp Đa Tài liệu (Multi-Document Synthesis)
Mở rộng kiến trúc RAG từ mức độ bài báo đơn lẻ lên quy mô thư mục nghiên cứu (Collection-level RAG). Thiết kế cơ chế định tuyến truy vấn hai tầng (Two-Tier Routing):
- Tầng 1: Sử dụng vector tóm tắt tài liệu (Document-Level Embeddings) hoặc chỉ mục BM25 trên siêu dữ liệu để chọn lọc ra 3–5 bài báo liên quan nhất trong thư mục;
- Tầng 2: Thực hiện truy xuất phân cấp Small-to-Big trên các bài báo đã chọn, gom cụm các luận điểm tương đồng hoặc mâu thuẫn để nạp vào prompt yêu cầu LLM tổng hợp một bài luận so sánh có trích dẫn nguồn gốc bài báo rõ ràng.

### 6.3.4. Tích hợp Tìm kiếm Toàn văn Ngữ nghĩa và Đại lý AI (AI Search Agent)
Phát triển tính năng tìm kiếm ngữ nghĩa toàn bộ kho tài liệu cá nhân ở thanh công cụ chính (`MainToolbar`), cho phép người dùng tìm kiếm bài báo bằng các mô tả ngôn ngữ tự nhiên trừu tượng (ví dụ: *"Các bài báo sử dụng cơ chế self-attention cho dữ liệu chuỗi thời gian"*). Tích hợp đại lý AI có khả năng lập luận đa bước (Multi-Step Reasoning Agent) để tự động phân loại tài liệu vào các thư mục phù hợp dựa trên nội dung tóm tắt.

### 6.3.5. Module Phát hiện và Nhận diện Chữ dạng Ảnh (OCR Module cho Scanned PDFs)
Đối với các bài báo khoa học cũ dạng quét (Scanned PDFs) không có sẵn lớp văn bản số (TextLayer), hệ thống cần bổ sung một module phát hiện văn bản dạng ảnh sử dụng Tesseract hoặc Surya OCR để mở rộng phạm vi xử lý cho toàn bộ các tài liệu lịch sử.

---

## 6.4. Lời kết

Đồ án đã chứng minh tính khả thi hoàn toàn của việc xây dựng một phần mềm quản lý tài liệu học thuật thông minh, tích hợp trợ lý AI cục bộ với chi phí phần cứng tối thiểu nhưng vẫn bảo đảm tính an toàn dữ liệu tuyệt đối và độ tin cậy khoa học cao. Sự kết hợp chặt chẽ giữa kỹ thuật công nghệ phần mềm thực tế và phương pháp luận nghiên cứu thực nghiệm có kiểm soát không chỉ giải quyết một bài toán thực tiễn cấp thiết của cộng đồng nghiên cứu mà còn đóng góp các phân tích khoa học có giá trị tham khảo cho việc thiết kế các hệ thống RAG chuyên dụng trong tương lai.