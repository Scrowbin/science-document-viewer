# KIỂM TRA BẢN WORD CỦA ĐỒ ÁN

- **Tệp kiểm tra:** `DACNTT_RAG_RESEARCH_WEB.dotx.docx` (bản sửa lần cuối lúc 15:01 ngày 14/11/2026). Tệp xuất ra PDF có 83 trang và khoảng 20.500 từ.
- **Đối chiếu với:** [`QUY_TAC_TRINH_BAY.md`](QUY_TAC_TRINH_BAY.md), tổng hợp từ QĐ 2284, Hướng dẫn trình bày, Template Khoa và Slide.

**Cách ghi số trang.** "tr. N" là số in trên đầu trang của **phần nội dung**: Chương 1 là tr. 1, Tài liệu tham khảo bắt đầu ở tr. 66. "tr. đầu N" là số in ở **phần đầu quyển**, từ Lời cảm ơn đến Danh mục chữ viết tắt.

---

## Những điểm đã đạt

- **Trang giấy:** khổ A4 đứng; lề 3,5 / 3 / 3,5 / 2 cm; font mặc định Times New Roman 13; giãn dòng 1.5; thân bài căn đều hai bên, thụt đầu dòng 1,27 cm.
- **Số trang:** đặt ở giữa đầu trang; Chương 1 bắt đầu lại từ trang 1.
- **Độ dài:** phần nội dung có 65 trang, nằm trong khoảng 40–80 theo quy định.
- **Đề mục:** mỗi nhóm có ít nhất 2 mục; không có mục nào sâu quá 3 cấp.
- **Tài liệu tham khảo:** đủ 39 mục, theo chuẩn APA, xếp ABC. Mọi mục đều được trích trong bài, và mọi trích dẫn đều có trong danh mục.
- **Hình:** không hình nào bị méo; cả 22 hình giữ đúng tỷ lệ.
- **Bảng:** mọi bảng đều lặp lại hàng tiêu đề khi sang trang.
- **Ngôn ngữ trình bày:** chương 4–6 viết mạch lạc, có số liệu cụ thể, phân biệt rõ kết quả đã có với phần [Chờ kết quả].

---

## A. Lỗi nghiêm trọng, phải sửa trước khi nộp

| # | Vấn đề | Vị trí | Quy tắc |
|---|---|---|---|
| A1 | **Không có bản Abstract tiếng Anh.** Chỉ có TÓM TẮT tiếng Việt. | tr. đầu 3 | QĐ mục 3 (6): Tóm tắt phải có cả tiếng Việt và tiếng Anh, dài 1–2 trang |
| A2 | **TÓM TẮT đã cũ và sai so với nội dung.** Xem chi tiết dưới bảng. | tr. đầu 3 | QĐ: nêu "một số kết quả đạt được, những phát hiện cơ bản" |
| A3 | **Bảng 5.5 bị vỡ bố cục.** Cột quá hẹp nên chữ và số bị ngắt giữa chừng: "hierarchi/cal", "fixed_siz/e", "0,/713", "n/DCG@1/0". Cột phân mảnh dùng font monospace, các ô bị thụt đầu dòng. Bảng kéo dài 3 trang, gần như không đọc được. | tr. 54–56 | Slide: lỗi trình bày bảng |
| A4 | **Đoạn văn sau Bảng 5.4 bị sai định dạng.** Một đoạn ở mục 5.2.3 dùng font monospace; đoạn tiếp theo ("PyMuPDF Layout và PyMuPDF thường…") bị **in đậm toàn bộ**. Cột tên bộ trích xuất của Bảng 5.4 cũng dùng font monospace. | tr. 52–53 | Font Times New Roman thống nhất |
| A5 | **Danh mục hình vẽ đã cũ.** Danh mục vẫn ghi "Hình 4.9. Giao diện trợ lý AI và các nguồn trích dẫn", trong khi thân bài đã đổi thành Hình 4.9.a, 4.9.b, 4.9.c. Ngoài ra, đoạn chứa ảnh của Hình 4.9.c đang mang style FigureCaption, nên khi cập nhật danh mục sẽ sinh ra một dòng trống. | tr. đầu 8–9; tr. 41–42 | Danh mục phải khớp với chú thích |
| A6 | **Chú thích của cả 22 hình đang nằm phía trên hình.** | toàn bài | QĐ mục 2.3 và Template: chú thích hình đặt **phía dưới** hình (đã chốt) |
| A7 | **Trích dẫn trong câu dùng "et al." (31 chỗ) và "&" (5 chỗ).** | toàn bài | Đã chốt theo QĐ: dùng "và cộng sự" và "và" |
| A8 | **Phần đầu quyển đánh số trang bằng số Ả Rập** (1–11). | tr. đầu 1–11 | Template: phần đầu đánh số La Mã thường (i, ii, …) |
| A9 | **Còn sót một bình luận (comment) của Word**, giải thích ngưỡng 0,80. Nội dung bình luận có công thức LaTeX và một khẳng định chưa kiểm chứng ("mathematically principled boundary"). | mục 3.3 | Không để chú thích nháp trong bản nộp |
| A10 | **Nhiều hình không đọc được khi in.** Xem chi tiết dưới bảng. | | QĐ: hình phải rõ nét, cỡ chữ trong hình xấp xỉ cỡ chữ văn bản |
| A11 | **Tham chiếu sai mục.** Hai chỗ ghi "(Mục 6.2)" khi nói về hướng mở rộng, nhưng 6.2 là *Hạn chế*; hướng mở rộng nằm ở **6.3**. | mục 1.3 (ý B.5); mục 4.3.3 | |
| A12 | **Còn ký hiệu Markdown.** Có 14 dấu backtick (`` ` ``) quanh tên hàm và tham số, ví dụ `` `extract_sections_from_pdf` ``, `` `hierarchical` ``, `` `query: ` ``. | Bảng 3.2 và một số đoạn | Văn bản Word không được chứa cú pháp Markdown |

**Chi tiết A2 – TÓM TẮT sai lệch:**
- Tóm tắt viết rằng đề tài đánh giá "truy xuất kết hợp (hybrid search)" và rằng "các thành phần tối ưu được lựa chọn để hoàn thiện cấu hình RAG". Thực tế, ứng dụng dùng truy xuất dense, và giai đoạn 3–4 chưa có kết quả.
- Tóm tắt không có kết quả nào: không có con số, không có phát hiện.
- Tóm tắt không nhắc đến việc hệ thống chạy cục bộ, cũng không nhắc OHR-Bench hay QASPER.

**Chi tiết A10 – các hình khó đọc:**

| Hình | Vấn đề |
|---|---|
| 3.1a, 3.1b | Dải hình 15,5 × 1,8 cm và 15,5 × 2,2 cm; chữ trong hình chỉ khoảng 3–4 pt |
| 4.2 (sơ đồ thành phần) | Chữ trong các khối rất nhỏ |
| 4.4, 4.5 (sơ đồ tuần tự) | Chữ rất nhỏ |
| 4.6, 4.7, 4.8, 4.9.a–c (ảnh chụp màn hình) | Thu nhỏ cả màn hình nên chữ không đọc được |

---

## B. Lỗi định dạng theo quy định Khoa

### B1. Ngắt trang và bố cục trang
- **Chương 2–6 không bắt đầu ở trang mới.** Tiêu đề chương nằm giữa trang:
  - Chương 2 ở tr. 5;
  - Chương 3 ở tr. 9;
  - Chương 4 nằm sát cuối tr. 18, cùng với tiêu đề 4.1;
  - Chương 5 ở tr. 48;
  - Chương 6 ở tr. 61.
- **Tiêu đề treo ở cuối trang** (Slide: lỗi "Treo tiêu đề"). Tiêu đề nằm cuối trang còn nội dung sang trang sau ở:
  - 3.3.2 (tr. 13);
  - 4.1.3 (tr. 21);
  - 4.2 và 4.2.1 (tr. 22);
  - 4.2.2 (tr. 23);
  - "1. Luồng nạp tài liệu…" (tr. 29);
  - 4.4.2 (tr. 32);
  - 4.5.2 (tr. 35);
  - 5.1.3 (tr. 50);
  - 5.2.2 (tr. 51);
  - 5.4.3 (tr. 57);
  - 5.7 (tr. 60);
  - 6.1.1 (tr. 61).

  Cách sửa: bật *Keep with next* cho các style Heading 1–4.
- **Khoảng trống lớn giữa chương** (Slide: lỗi "Để trống trang"), do hình lớn bị đẩy sang trang sau: tr. 23 (nửa trang trống trước Hình 4.1), tr. 38, 39, 40, 46 và 47.
- **Có 43 đoạn văn rỗng dùng để tạo khoảng cách.** Đây là nguyên nhân chính khiến bố cục xô lệch khi nội dung thay đổi.
- **Một số hàng bảng bị chia đôi qua hai trang**: Bảng 3.1 (tr. 11–12), Bảng 4.2 (FR-09), Bảng 4.5 (UC-03, UC-06). Cách sửa: tắt tùy chọn *Allow row to break across pages*.

### B2. Đề mục
- **1.5.1 và 1.5.2 dùng sai style.** Đây là mục cấp 3 nhưng đang dùng Heading 4, nên:
  - không xuất hiện trong Mục lục;
  - số không có dấu chấm cuối ("1.5.1" so với "1.2.1.");
  - tiêu đề có dấu hai chấm thừa ("Ý nghĩa khoa học:").
- **3.2.1 có ba tiêu đề con a., b., c. (OHR-Bench, QASPER, PeerQA)** dùng Heading 4 với font khác (Cambria) và đánh số tự động. Các tiêu đề này không theo kiểu số của các mục khác.
- **Số đề mục vừa tự động vừa gõ tay.** "CHƯƠNG N." được đánh tự động, còn "1.1.", "1.2.1." gõ tay. Cần chọn một cách và dùng thống nhất toàn bài.

### B3. Hình, bảng, phương trình
- **Kiểu đánh số hình không thống nhất:** "Hình 3.1a" nhưng lại "Hình 4.9.a". Nên đổi thành Hình 3.1/3.2 và 4.9/4.10/4.11 rồi đánh lại số các hình sau, hoặc thống nhất một kiểu a/b.
- **Dấu câu cuối chú thích không thống nhất:** có chú thích kết thúc bằng dấu chấm (Bảng 3.1–3.3, Hình 4.6–4.8), có chú thích thì không. Template dùng mẫu "Hình 2.1: Tên".
- **Chú thích Bảng 4.9 định dạng khác các bảng còn lại** (đậm, không nghiêng).
- **28 hình và bảng không được nhắc trong văn bản**, chỉ có chú thích. Quy định yêu cầu văn bản phải nhắc số hình hoặc bảng, ví dụ "xem Hình 4.4". Danh sách:
  - Hình 3.1a, 3.1b, 4.2–4.9c, 5.2, 5.3, 5.4;
  - Bảng 4.1–4.6, 4.8, 4.9, 5.3–5.7.
- **Phương trình không được đánh số.** Công thức DCG và nDCG ở mục 2.4 thiếu số (2.1) đặt sát lề phải. Ký hiệu *rel_i* và *IDCG@k* chưa được giải thích.
- **Chữ trong bảng căn đều hai bên** (kế thừa mặc định của thân bài). Trong cột hẹp, cách căn này tạo khoảng trắng lớn giữa các chữ (Bảng 4.2, 4.5, 4.6, 4.7). Nên căn trái, dùng style "Bảng biểu - nội dung" của template.

### B4. Phần đầu quyển
- **Tên đề tài trên bìa phụ bị ngắt dòng sai:** dòng cuối chỉ còn chữ "RAG" (Slide: lỗi "Xuống dòng tên đề tài"). Cần ngắt dòng chủ động ở chỗ có nghĩa.
- **Danh mục hình vẽ và danh mục bảng biểu bị in đậm nghiêng và thụt đầu dòng 1,27 cm.** Vì vậy số trang bị đẩy xuống dòng riêng ("28", "35", "37", "52", "54"). Mục lục cũng có dòng chương bị ngắt ("…NGHIÊN CỨU / 5").
- **Lời cam đoan dùng "tôi" và "của mình"** trong khi có hai tác giả. Nên sửa thành "chúng tôi". Các chỗ khác đã dùng "Chúng em".
- **Danh mục chữ viết tắt chưa khớp với bài:**
  - Nên bỏ: RSS (chỉ dùng 1 lần); IR và EDA dùng 2–3 lần.
  - Còn thiếu các chữ viết tắt dùng nhiều lần: AI, LCS, CSDL, HTTP, REST, JSON, RAM, MAP. Các chữ sau có mặt nhưng không được giải thích: OCR, NLP/ML, FR/NFR/UC, ORM, ACID, SQL.
  - Hoặc viết đầy đủ các thuật ngữ trên thay vì viết tắt.

### B5. Tài liệu tham khảo
- **Mục tham khảo căn đều hai bên làm giãn dòng có URL**, ví dụ "Artifex Software.  (2024).  PyMuPDF  documentation." (tr. 66). Nên căn trái và giữ thụt treo.
- **"Vera, H. S., Dua, S., et al. (2025)" không đúng chuẩn APA.** APA liệt kê đến 20 tác giả, không dùng "et al." trong danh mục.

### B6. Thuật ngữ trộn Anh và Việt
Nhiều thuật ngữ khi viết tiếng Việt, khi viết tiếng Anh, và đổi qua lại ngay trong một chương:
- metadata / siêu dữ liệu;
- chunk / đoạn;
- pipeline / đường ống;
- Highlight / bôi đậm;
- usecase / use case / ca sử dụng;
- "thực hiện inference" (chú thích Hình 4.9.a).

Nên chọn một từ cho mỗi khái niệm, giới thiệu thuật ngữ tiếng Anh trong ngoặc ở lần đầu, rồi dùng thống nhất.

---

## C. Độ mạch lạc với người đọc độc lập

1. **Thứ tự chương làm người đọc gặp thuật ngữ trước khi được giải thích.**
   - Chương 3 (thiết kế thực nghiệm) đứng trước Chương 4 (hệ thống). Bảng 3.2 đã dùng "đoạn cha", "ngưỡng từ chối 0,80", "Ollama", "num_ctx", trong khi các khái niệm này đến Chương 4 mới được giải thích.
   - Cách sửa: đổi vị trí Chương 3 và Chương 4 (hệ thống → thiết kế thực nghiệm → kết quả), hoặc thêm một đoạn tổng quan hệ thống ở đầu Chương 3.
2. **Lặp nội dung.**
   - Danh sách hạn chế xuất hiện **4 lần** với nội dung chồng lấn: 3.5, 4.9, 5.7 và 6.2.
   - Luồng nạp tài liệu và luồng hỏi đáp được mô tả hai lần: ở 4.3.2 (cụ thể) và ở 4.5.1–4.5.2 (chung chung, ví dụ "theo phương pháp chunking đang được sử dụng").
   - Nên gộp: giữ một mô tả cụ thể đi kèm sơ đồ tuần tự, và một mục hạn chế ở Chương 6 có tham chiếu ngược.
3. **Khái niệm dùng nhưng chưa định nghĩa.**
   - MAP@k và P@k (dùng ở 3.3.2 và Bảng 3.3) không có trong 2.4.
   - Không giải thích tên "C-RET" có nghĩa gì.
   - "expert agreement solvable" (5.1.1) không được giải thích. Chỉ số này không dùng ở đâu khác, nên bỏ.
4. **Chương 2 (Tổng quan) còn mỏng.**
   - Mục 2.1 chỉ nói về Zotero, Mendeley, EndNote. Mục này chưa phân tích các công cụ hỏi đáp tài liệu bằng AI hiện có (ví dụ ChatPDF, SciSpace, Elicit, PaperQA, các plugin AI cho Zotero) và chưa nêu khoảng trống mà đề tài lấp vào.
   - QĐ yêu cầu phần Tổng quan "phân tích, đánh giá các công trình… nêu những vấn đề còn tồn tại".
5. **Mô tả kết quả hơi quá so với thực tế.**
   - 6.1.1 ghi "chia sẻ theo quyền" như một kết quả đã đạt, trong khi FR-10 mới hoàn thành một phần (chưa có giao diện).
   - 4.7.1 nhắc đến "các bài kiểm thử tự động" nhưng không có phần nào trình bày việc kiểm thử.
6. **Phần còn chờ kết quả.** Có khoảng 15 chỗ [Chờ kết quả]; mục 5.4 hoàn toàn là chỗ trống. Đánh dấu như vậy là đúng cho bản nháp, nhưng cần điền hết trước khi nộp. Tóm tắt, Chương 6 và Bảng 6.1 phải cập nhật theo.

---

## D. Bảng và hình còn thiếu

| # | Đề xuất | Đặt ở | Lý do |
|---|---|---|---|
| D1 | **Bảng so sánh các hệ thống liên quan**, gồm Zotero, Mendeley, công cụ hỏi đáp PDF bằng AI và hệ thống của đề tài. Tiêu chí: quản lý thư viện, hỏi đáp, trích dẫn trang, chạy cục bộ, mã nguồn mở. | 2.1 hoặc 2.5 | Làm rõ khoảng trống nghiên cứu (yêu cầu của phần Tổng quan) |
| D2 | **Mục kiểm thử**: chiến lược kiểm thử, số bài kiểm thử tự động của backend, các nhóm được kiểm thử (xác thực, phân quyền, tải lên, thao tác hàng loạt) và kết quả. | Chương 4 | Đồ án phần mềm hiện không có minh chứng kiểm thử nào |
| D3 | **Sơ đồ triển khai** (một máy: trình duyệt, Django, PostgreSQL, Qdrant nhúng, Ollama; chỉ tra cứu DOI đi ra ngoài). Bản Markdown có hình này, bản Word không có. | 4.3.3 | Mục này hiện chỉ có văn bản |
| D4 | **Bảng chi phí giai đoạn 2**: tham số, thời gian lập chỉ mục, độ trễ mã hóa câu hỏi theo từng mô hình nhúng. | 5.3 | Văn bản dựa vào con số "1.650 s và 120 s, ước lượng từ nhật ký"; phương pháp đánh giá cũng yêu cầu báo cáo chi phí |
| D5 | **Bảng kết quả giai đoạn 1 theo loại nguồn bằng chứng** (văn bản, bảng, công thức, biểu đồ, thứ tự đọc) **và theo nhóm học thuật**. | 5.2.3 | Các con số 84,9 / 48,2 / 74,6 / 52,8 / 0,629 / 0,391 hiện chỉ có trong văn bản |
| D6 | **Một ví dụ hỏi đáp đầy đủ**: câu hỏi, các đoạn được truy xuất, câu trả lời và trích dẫn trang. | 4.5.2 hoặc 4.8 | Giúp người đọc ngoài ngành hình dung đường ống RAG |
| D7 | **Sơ đồ trạng thái lập chỉ mục** (PENDING → INDEXING → INDEXED/FAILED). Không bắt buộc, vì Bảng 4.9 đã mô tả phần lớn. | 4.4.3 | Bản Markdown có hình này |
| D8 | **Bảng và biểu đồ của giai đoạn 2 trên PeerQA, giai đoạn 3 và giai đoạn 4.** | 5.3.3, 5.4, 5.5.2 | Đang chờ kết quả |

---

## E. Thứ tự sửa đề xuất

1. **Sửa nhanh và cơ học (không đổi nội dung):**
   - A3, A4: định dạng lại Bảng 5.5, Bảng 5.4 và các đoạn lỗi font hoặc in đậm.
   - A9: xóa comment.
   - A11: sửa tham chiếu Mục 6.2 → 6.3.
   - A12: bỏ backtick.
   - B1: bật Keep with next, xóa đoạn rỗng, mỗi chương sang trang mới, không chia hàng bảng.
   - B2: đổi 1.5.1 và 1.5.2 sang Heading 3.
   - B3: căn trái chữ trong bảng, đánh số phương trình.
   - B4: sửa định dạng danh mục.
   - B5: căn trái tài liệu tham khảo, ghi đủ tác giả Vera.
2. **Áp dụng các quy tắc vừa chốt:**
   - A6: chuyển chú thích hình xuống dưới.
   - A7: đổi "et al." thành "và cộng sự".
   - A8: số trang La Mã cho phần đầu.
   - Đánh số hình thống nhất, rồi cập nhật Mục lục và các danh mục (A5).
3. **Nội dung:**
   - A1, A2: viết lại Tóm tắt và thêm Abstract.
   - A10: làm lại các hình khó đọc.
   - C1–C5 và các bảng D1–D5.
4. **Sau khi có kết quả giai đoạn 3–4:** điền các chỗ [Chờ kết quả], cập nhật Bảng 5.7, Bảng 6.1, Tóm tắt và Abstract, rồi cập nhật Mục lục và danh mục (F9) một lần cuối.
