# Khung slide bảo vệ đồ án (23 slide, khoảng 20 phút)

Đề tài: **Xây dựng hệ thống quản lý tài liệu nghiên cứu khoa học tích hợp trợ lý AI sử dụng RAG**

Mỗi slide gồm: nội dung trên slide (ngắn), hình hoặc bảng nên dùng (tệp trong `reports/thesis_figures/`), và lời nói gợi ý. Số liệu lấy từ `eval/README.md` và Chương 5; không thêm số ngoài các nguồn này.

Phân bổ thời gian gợi ý: mở đầu 2 phút, hệ thống 6 phút, demo 4 phút, thực nghiệm 6 phút, kết luận 2 phút.

---

## Phần 1. Mở đầu (slide 1–4)

### Slide 1. Tiêu đề
- Tên đề tài, khoa, chuyên ngành, sinh viên thực hiện, giảng viên hướng dẫn.
- **Lời nói:** giới thiệu bản thân, tên đề tài, nói thẳng một câu: "Nhóm xây dựng một ứng dụng kiểu Zotero có trợ lý AI trả lời câu hỏi về bài báo và chỉ ra đoạn trích dẫn trên trang PDF."

### Slide 2. Vấn đề
- Bài báo khoa học dài 8–30 trang, nhiều cột, bảng, công thức; tìm một chi tiết phải đọc quét thủ công.
- Zotero, Mendeley, EndNote quản lý thư viện tốt nhưng không hiểu nội dung.
- Dịch vụ AI đám mây gặp ba rào cản: rò rỉ bản thảo chưa công bố, ảo giác (bịa trích dẫn), chi phí API hoặc GPU.
- **Lời nói:** nêu một câu hỏi ví dụ ("Hàm mất mát nào được dùng?") để hội đồng hình dung nhu cầu.

### Slide 3. Mục tiêu và phạm vi
- Mục tiêu 1: ứng dụng quản lý tài liệu bố cục 3 cột, đọc PDF và chú thích, chia sẻ.
- Mục tiêu 2: trợ lý AI hỏi đáp, tóm tắt, **từ chối khi không đủ căn cứ**, trích dẫn tới trang.
- Mục tiêu 3: đánh giá đường ống RAG theo bốn giai đoạn và chọn phương pháp bằng kết quả, lý thuyết và chi phí.
- Phạm vi: **bản thử nghiệm khái niệm chạy cục bộ trên một máy**, không phục vụ nhiều người dùng.
- **Lời nói:** nhấn mạnh phạm vi ngay từ đầu để tránh câu hỏi về khả năng mở rộng.

### Slide 4. RAG là gì (cơ sở lý thuyết)
- Sơ đồ: PDF → trích xuất → phân mảnh → nhúng → truy xuất → ghép ngữ cảnh → LLM trả lời.
- Ý chính: LLM chỉ trả lời từ đoạn được truy xuất, nên trả lời có nguồn và giảm ảo giác.
- **Hình:** vẽ lại sơ đồ đường ống (hoặc `fig4_03_rag_activity.png`).
- **Lời nói:** giới thiệu sơ đồ này là "bản đồ" cho cả phần thực nghiệm phía sau, mỗi khâu là một giai đoạn đánh giá.

---

## Phần 2. Hệ thống (slide 5–10)

### Slide 5. Yêu cầu và use case
- Sáu use case chính: đăng nhập, tải PDF và trích metadata, nhập bằng DOI, đọc và chú thích, chia sẻ, hỏi đáp AI có trích dẫn.
- 12 yêu cầu chức năng, 6 yêu cầu phi chức năng (chạy trên CPU 16 GB RAM, truy vết nguồn, bảo mật).
- **Hình:** `fig4_01_use_case.png`.

### Slide 6. Kiến trúc
- React 19 + TypeScript (giao diện) → REST/JWT → Django 5 + DRF, PostgreSQL 16 → đường ống RAG trong cùng tiến trình: Qdrant nhúng, Ollama.
- Chia sẻ kiểu Google Drive (chủ sở hữu, VIEW, COMMENT, EDIT); PDF phục vụ qua API có kiểm tra quyền.
- **Hình:** `fig4_02_components.png`.

### Slide 7. Triển khai
- Mọi thành phần chạy trên một máy; khi demo, mô hình sinh chạy trên GPU của Kaggle qua đường hầm ngrok, máy cục bộ dùng `llama3.2:3b` làm dự phòng.
- Truy xuất luôn chạy trên CPU cục bộ; chỉ bước sinh câu trả lời chạy trên Kaggle.
- **Hình:** `fig4_04_deployment.png`.

### Slide 8. Lập chỉ mục một tài liệu
- Tải lên → hàng đợi nền → PyMuPDF tách mục theo đề mục → phân mảnh phân cấp (đoạn con 200 token, chồng 40; mục cha là đơn vị ngữ cảnh) → embeddinggemma-300m → Qdrant (vector con + bộ sưu tập mục cha).
- Trạng thái: PENDING → INDEXING → INDEXED / FAILED, có khôi phục khi khởi động lại.
- **Hình:** `fig4_07_upload_sequence.png` hoặc `fig4_08_index_state.png`.

### Slide 9. Trả lời một câu hỏi
- Ngưỡng liên quan: câu hỏi lạc đề bị từ chối ngay, không gọi LLM.
- Truy xuất `convex`: 0,7 × điểm dense + 0,3 × điểm BM25 → mở rộng sang mục cha trong ngân sách 1.600 token (tối đa 5 đơn vị) → LLM trả lời kèm `[Page N]`.
- Trích dẫn trỏ tới đoạn con khớp nhất với câu trả lời.
- **Hình:** `fig4_09_question_activity_slide.png` (bản nằm ngang cho slide; bản dọc trong luận văn là `fig4_09_question_activity.png`).

### Slide 10. Giao diện
- Bố cục 3 cột kiểu Zotero: thư mục và thẻ, bảng tài liệu, bảng siêu dữ liệu; tab kiểu trình duyệt; phím tắt.
- Trình đọc PDF: tô sáng, ghi chú; bảng trợ lý AI cạnh tài liệu.
- **Hình:** ảnh chụp giao diện thật (lấy từ Chương 4 bản Word).

---

## Phần 3. Demo (slide 11)

### Slide 11. Demo trực tiếp
- Kịch bản theo `demo/DEMO_CHECKLIST.md`: đăng nhập → mở bài đã lập chỉ mục sẵn → hỏi 2–3 câu → bấm chip trích dẫn để nhảy tới đoạn được tô sáng → hỏi một câu lạc đề để thấy từ chối.
- **Chuẩn bị:** tải và lập chỉ mục bài demo trước (lập chỉ mục trên CPU mất khoảng 2 phút cho bài Attention); bật notebook Kaggle và khởi động trước một câu.
- **Phương án dự phòng:** nếu Kaggle không phản hồi, ứng dụng tự chuyển sang `llama3.2:3b` cục bộ (chậm hơn, khoảng 30–60 giây mỗi câu); có sẵn video quay trước.

---

## Phần 4. Thực nghiệm (slide 12–20)

### Slide 12. Thiết kế thực nghiệm
- Bốn giai đoạn nối tiếp, mỗi giai đoạn bắt đầu từ lựa chọn của giai đoạn trước: (1) trích xuất, (2) phân mảnh × mô hình nhúng, (3) BM25, kết hợp và xếp hạng lại, (4) mô hình sinh.
- Dữ liệu: OHR-Bench (706 tài liệu, 6.916 câu hỏi), QASPER/C-RET (335 bài, 567 câu), PeerQA (107 bài, 288 câu).
- Chỉ số mô tả (trung bình, chênh lệch, chi phí); không kiểm định thống kê.
- **Lời nói:** nói rõ phương pháp được chọn và đánh giá trên cùng dữ liệu, nên đây không phải tập kiểm tra độc lập.

### Slide 13. Giai đoạn 1: trích xuất PDF
- Độ phủ bằng chứng: PyMuPDF 0,747, pypdf 0,726, pdfminer.six 0,717, pdfplumber 0,705, GROBID 0,494.
- Tốc độ: PyMuPDF khoảng 2,5 ms/trang, GROBID 143 ms/trang.
- Lý thuyết dự đoán GROBID tốt trên bài báo khoa học, nhưng nó thấp nhất, kể cả trên tập con học thuật: GROBID bỏ hoặc tách nhiều nội dung ngoài thân bài (bảng, công thức), nơi OHR-Bench đặt nhiều câu hỏi (giải thích hợp lý, chưa kiểm chứng riêng).
- **Chọn:** PyMuPDF có nhận diện đề mục.
- **Hình:** `fig5_2_extraction_ohr.png`.

### Slide 14. Giai đoạn 2: phân mảnh × mô hình nhúng
- 3 cách phân mảnh × 5 mô hình nhúng, nDCG@10.
- Phân mảnh phân cấp tốt nhất với mọi mô hình: +0,06 đến +0,08 trên C-RET, +0,18 đến +0,24 trên PeerQA.
- Với phân mảnh phân cấp, các mô hình nhúng chênh nhau ít (0,041 trên C-RET): **cách phân mảnh quan trọng hơn mô hình nhúng.**
- Bất ngờ: phân mảnh theo đề mục không vượt phân mảnh kích thước cố định.
- **Hình:** `fig5_3_retrieval_grid.png` (và `fig5_4_retrieval_grid_peerqa.png`).

### Slide 15. Giai đoạn 3: BM25, kết hợp, xếp hạng lại
- BM25 riêng: thấp hơn dense trên C-RET (0,646), ngang dense trên PeerQA (0,718), đúng như lý thuyết.
- `convex` không bao giờ thấp hơn dense; `rrf` có lúc thấp hơn (gemma −0,013 trên C-RET).
- Reranker bge-m3 cao nhất (đến 0,757) nhưng tốn khoảng 1,5–2 giây mỗi câu trên GPU.
- **Hình:** `fig5_5_phase3_tradeoff.png`.

### Slide 16. Lựa chọn truy xuất: embeddinggemma + convex
- nDCG@10: C-RET 0,744, PeerQA 0,742 (+0,023 so với dense trên PeerQA), chỉ thêm khoảng 1 ms.
- Phù hợp lý thuyết: từ khóa bổ sung tên riêng, số liệu, thuật ngữ hiếm và giảm phụ thuộc vào mô hình nhúng (Thakur và cộng sự, 2021; Bruch và cộng sự, 2023). Trọng số 0,3 cố định từ trước, không tinh chỉnh.
- Không dùng reranker: lợi ích nhỏ so với chi phí, nhất là trên CPU nơi ứng dụng truy xuất.
- **Lời nói:** đây là ví dụ cho nguyên tắc chọn bằng kết quả + lý thuyết + chi phí, không chỉ điểm cao nhất.

### Slide 17. Giai đoạn 4: mô hình sinh, cách đánh giá
- 5 mô hình chạy qua Ollama: llama3.2:3b, qwen2.5:1.5b, phi4-mini, qwen3:4b-instruct-2507, gemma3:4b.
- Hai điều kiện: bằng chứng chuẩn (gold) và ngữ cảnh truy xuất; chênh lệch giữa hai là tổn thất do truy xuất.
- Chỉ số: Token F1, tỷ lệ từ chối, nhãn căn cứ do Claude Opus 5.5 chấm (khớp người chấm 80/100 trên 6 nhãn, 93/100 trên 3 lớp); 18.700 câu trả lời.
- **Lời nói:** Token F1 không phải độ đúng sự thật, nên cần thêm nhãn căn cứ.

### Slide 18. Giai đoạn 4: kết quả
- qwen3:4b có tỷ lệ câu trả lời có căn cứ cao nhất khi dùng ngữ cảnh truy xuất: 62,1% (C-RET), 34,8% (PeerQA); không có căn cứ chỉ 7,6% / 7,2%.
- qwen2.5:1.5b có Token F1 cao nhất nhưng nhiều câu không có căn cứ nhất (23,6% / 50,8%): **F1 không phản ánh độ có căn cứ.**
- gemma3:4b từ chối 64–86%; thử nới câu lệnh từ chối thì tỷ lệ giảm từ 72% xuống 52%.
- **Hình:** `fig5_12_phase4_labels.png`, `fig5_13_phase4_gold_vs_retrieved.png`.

### Slide 19. Lựa chọn mô hình sinh và chi phí
- **Chọn:** qwen3:4b-instruct-2507 trên GPU Kaggle (P50 khoảng 2 giây).
- Trên CPU cục bộ: qwen3:4b trung vị 56 giây, llama3.2:3b trung vị 34 giây (10 câu C-RET), nên llama3.2:3b là dự phòng cục bộ.
- Lập chỉ mục bằng embeddinggemma trên CPU: khoảng 4,5 phút cho bài 149 đoạn con.

### Slide 20. Ngưỡng từ chối trong ứng dụng
- Hiệu chuẩn lại khi đổi sang embeddinggemma (điểm tương đồng thấp hơn e5 nhiều): ngưỡng 0,30.
- Trên bộ câu viết tay (6 bài, không phải tập kiểm tra độc lập): cho qua 34/35 câu có đáp án, chỉ 1/90 câu lạc đề.
- **Lời nói:** từ chối đúng lúc là một phần của "không bịa", liên hệ lại vấn đề ở slide 2.

---

## Phần 5. Kết luận (slide 21–23)

### Slide 21. Kết quả đạt được
- Ứng dụng hoàn chỉnh: thư viện, đọc PDF và chú thích, chia sẻ, trợ lý AI có trích dẫn tới trang, từ chối khi không đủ căn cứ; 277 kiểm thử backend.
- Đường ống được chọn bằng thực nghiệm: PyMuPDF → phân mảnh phân cấp → embeddinggemma → convex → qwen3:4b (llama3.2:3b dự phòng).
- Bài học: cách phân mảnh quan trọng hơn mô hình nhúng; Token F1 cần đi kèm đánh giá căn cứ.

### Slide 22. Hạn chế và hướng phát triển
- Hạn chế: chọn và đánh giá trên cùng dữ liệu (QASPER chỉ NLP/ML); giám khảo LLM chỉ kiểm chứng trên 100 câu của một người; CPU chậm; chỉ chạy trên một máy.
- Hướng phát triển: hiệu chuẩn ngưỡng trên tập lớn hơn; mở rộng ngữ cảnh khi thiếu căn cứ; hỏi đáp nhiều tài liệu và OCR; lập chỉ mục hai giai đoạn (e5 nhanh trước, embeddinggemma sau); mô hình ứng dụng máy tính + máy chủ dùng chung.

### Slide 23. Cảm ơn và hỏi đáp
- Cảm ơn hội đồng và giảng viên hướng dẫn; mời câu hỏi.

---

## Câu hỏi hội đồng có thể hỏi (chuẩn bị trước)

1. **Vì sao không dùng reranker khi nó cho điểm cao nhất?** Lợi ích 0,003 trên C-RET và khoảng 0,015 trên PeerQA so với convex, nhưng tốn khoảng 1,5–2 giây mỗi câu trên GPU, chậm hơn nhiều trên CPU (slide 15–16).
2. **Kết quả có tổng quát hóa không?** Không chứng minh được: chọn và đánh giá trên cùng bài QASPER; PeerQA chỉ là kiểm tra nhỏ với kiểu câu hỏi khác.
3. **Giám khảo LLM có đáng tin không?** Khớp người chấm 80/100 (6 nhãn), 93/100 (3 lớp); có xu hướng coi các câu từ chối ranh giới là từ chối không đáng.
4. **Vì sao có "chạy cục bộ" mà demo lại dùng Kaggle?** Truy xuất và dữ liệu vẫn ở máy cục bộ; chỉ mô hình sinh chạy trên GPU để demo nhanh, và có llama3.2:3b dự phòng hoàn toàn cục bộ.
5. **Câu hỏi tiếng Việt?** Câu lệnh yêu cầu trả lời theo ngôn ngữ của câu hỏi, nhưng các thực nghiệm chỉ dùng câu hỏi tiếng Anh.
