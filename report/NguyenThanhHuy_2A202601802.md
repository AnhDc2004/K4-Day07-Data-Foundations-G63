# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Nguyễn Thành Huy]
**Nhóm:** [G63]
**Ngày:** [3/8/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Độ tương tự cosine cao nghĩa là hai vector embedding có hướng gần nhau trong không gian vector. Với text embeddings, điều này thường cho thấy hai câu có nội dung hoặc ngữ nghĩa tương đồng.

**Ví dụ có độ tương tự CAO:**
- Câu A: Chính sách đổi trả hàng áp dụng trong 7 ngày.
- Câu B: Khách hàng có thể hoàn trả sản phẩm trong vòng 7 ngày.
- Tại sao tương đồng: Cả hai câu đều nói về chính sách và thời hạn đổi trả sản phẩm.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Chính sách đổi trả hàng áp dụng trong 7 ngày.
- Câu B: Thời tiết hôm nay có mưa lớn.
- Tại sao khác: Hai câu đề cập đến hai chủ đề không liên quan: chính sách thương mại điện tử và thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine similarity đo góc giữa hai vector nên tập trung vào hướng biểu diễn ngữ nghĩa, ít bị ảnh hưởng bởi độ lớn của vector. Text embeddings thường được chuẩn hóa, vì vậy cosine similarity là thước đo phù hợp để so sánh mức độ liên quan của văn bản.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* Bước nhảy = 500 - 50 = 450 ký tự. Số chunk = ceil((10.000 - 500) / 450) + 1 = ceil(21,11) + 1 = 23.
> *Đáp án:* 23 chunks.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap = 100, bước nhảy còn 400 ký tự và số chunk là ceil((10.000 - 500) / 400) + 1 = 25 chunks, tức tăng từ 23 lên 25. Overlap lớn hơn giữ được ngữ cảnh ở ranh giới hai chunk tốt hơn, nhưng làm tăng số vector cần lưu và chi phí tìm kiếm.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi tách văn bản tại chỗ kết thúc câu, tức sau các dấu `.`, `!` hoặc `?`, và vẫn giữ dấu câu ở cuối mỗi câu. Sau đó tôi bỏ khoảng trắng thừa rồi gom một số câu liên tiếp vào cùng một chunk theo giá trị `max_sentences_per_chunk`. Nếu văn bản rỗng hoặc chỉ có khoảng trắng, hàm trả về danh sách rỗng để tránh tạo chunk không có nội dung.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán lần lượt thử các separator theo mức ưu tiên: đoạn trống, xuống dòng, kết thúc câu, khoảng trắng, rồi mới tách theo số ký tự. Các phần nhỏ được gộp đến giới hạn `chunk_size`; phần quá dài tiếp tục được tách đệ quy với separator kế tiếp. Base case là khi đoạn đã không dài hơn `chunk_size`; nếu không còn separator phù hợp thì cắt cố định theo `chunk_size`.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuyển thành một record gồm id duy nhất, content, metadata và embedding; `doc_id` gốc được giữ trong metadata để truy vết các chunk của cùng tài liệu. Khi tìm kiếm, query cũng được embed và được so sánh với các vector đã lưu bằng tích vô hướng, sau đó các kết quả được sắp xếp giảm dần theo score và lấy `top_k`. Store hỗ trợ ChromaDB nếu khởi tạo được, đồng thời có phương án dự phòng lưu trong bộ nhớ.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc metadata trước, sau đó chỉ chạy similarity search trên các chunk thỏa mọi điều kiện của filter; khi không có filter, hàm gọi lại `search`. `delete_document` tìm các chunk có `metadata["doc_id"]` trùng với id cần xóa và loại bỏ tất cả các chunk đó. Hàm trả về `True` nếu có ít nhất một chunk bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent gọi `store.search(question, top_k)` để lấy các chunk liên quan nhất, rồi ghép content của chúng thành phần `Context` có đánh số. Prompt gồm yêu cầu chỉ sử dụng context, phần context, câu hỏi và vị trí trả lời; khi không tìm được context, prompt nêu rõ điều đó. Cuối cùng, prompt được truyền vào `llm_fn` để sinh câu trả lời.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
pytest tests/ -v
======================== 42 passed, 1 warning in 0.14s ========================
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Chính sách đổi trả áp dụng trong 7 ngày. | Khách hàng có thể hoàn trả sản phẩm trong vòng 7 ngày. | cao | -0,1017 | Không |
| 2 | Chính sách đổi trả áp dụng trong 7 ngày. | Thời tiết hôm nay có mưa lớn. | thấp | 0,1222 | Có |
| 3 | Phí giao hàng được thông báo trước khi đặt hàng. | Người mua xem được chi phí vận chuyển trước khi thanh toán. | cao | -0,1945 | Không |
| 4 | Khách hàng có thể thanh toán bằng thẻ tín dụng. | Mật khẩu tài khoản cần được bảo mật. | thấp | -0,2562 | Có |
| 5 | Đơn hàng được giao trong 3 đến 5 ngày làm việc. | Thời gian vận chuyển dự kiến là từ 3 đến 5 ngày làm việc. | cao | -0,0439 | Không |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 5 có ý nghĩa gần như tương đương nhưng lại nhận điểm âm, nên là kết quả bất ngờ nhất. Nguyên nhân là bài chạy bằng `MockEmbedder`: vector được sinh xác định từ toàn bộ chuỗi ký tự chứ không học ngữ nghĩa. Vì vậy mock embedding phù hợp để kiểm tra luồng chương trình, nhưng không phù hợp để đánh giá chất lượng truy xuất hoặc chiến lược chunking theo ngữ nghĩa.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua cần làm gì khi yêu cầu đổi trả? | Chunk `returns-policy` nêu người mua phải gửi yêu cầu trong thời hạn quy định. | 0,464 | Có (top-1) | `demo_llm` chỉ trả preview của prompt có context; chưa sinh câu trả lời ngữ nghĩa. |
| 2 | Khi hàng lỗi hoặc không đúng mô tả, yêu cầu đổi trả cần kèm gì? | Chunk `returns-policy` nêu yêu cầu phải kèm bằng chứng phù hợp. | 0,107 | Có (top-1) | `demo_llm` chỉ trả preview của prompt có context; chưa sinh câu trả lời ngữ nghĩa. |
| 3 | Người bán phải phản hồi yêu cầu đổi trả như thế nào? | Top-1 là chunk `seller-listing` không liên quan; chunk `returns-policy` liên quan xuất hiện ở top-3. | 0,149 | Có (top-3) | `demo_llm` chỉ trả preview của prompt có context; chưa sinh câu trả lời ngữ nghĩa. |
| 4 | Thông tin nào người bán phải cung cấp khi đăng bán sản phẩm? | Top-1 là chunk `returns-policy` không liên quan; chunk `seller-listing` chứa giá, mô tả và tình trạng hàng ở top-3. | 0,164 | Có (top-3) | `demo_llm` chỉ trả preview của prompt có context; chưa sinh câu trả lời ngữ nghĩa. |
| 5 | Những sản phẩm nào không được đăng bán? | Top-1 là chunk `returns-policy` không liên quan; chunk `seller-listing` nêu hàng hạn chế hoặc bị cấm ở top-3. | -0,012 | Có (top-3) | `demo_llm` chỉ trả preview của prompt có context; chưa sinh câu trả lời ngữ nghĩa. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** **5 / 5**

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Qua demo, tôi nhận ra việc đánh giá không nên chỉ nhìn score hoặc top-1: cần kiểm tra chunk liên quan có trong top-3 và đối chiếu với gold answer. Metadata như `customer_role`, `category` và `doc_id` cũng rất hữu ích để lọc đúng nhóm người dùng/tài liệu trước khi xếp hạng.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | Chưa tự chấm — chờ benchmark nhóm và LLM thực |
| **Tổng phần cá nhân tạm tính** | **50 / 60** |
