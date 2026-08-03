# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Trần Minh Hạnh
**Mã sinh viên:** 2A202601232
**Nhóm:** G63
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai đoạn văn có cosine similarity cao khi vector embedding của chúng hướng gần giống nhau. Điều đó thường cho thấy chúng có chủ đề hoặc ý nghĩa tương tự, dù cách dùng từ có thể khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: Khách hàng có thể đổi trả sản phẩm trong bảy ngày.
- Câu B: Người mua được yêu cầu hoàn hàng trong vòng 7 ngày.
- Tại sao tương đồng: Hai câu cùng nói về quyền đổi trả và cùng một thời hạn, chỉ khác cách diễn đạt.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Chính sách hoàn tiền áp dụng cho hàng bị lỗi.
- Câu B: Trời hôm nay có mưa lớn ở Hà Nội.
- Tại sao khác: Một câu nói về chính sách thương mại điện tử, câu còn lại nói về thời tiết.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine tập trung vào hướng của vector thay vì độ lớn, nên ít bị ảnh hưởng bởi độ dài văn bản hoặc độ lớn embedding. Với văn bản, hướng thường thể hiện nội dung ngữ nghĩa hữu ích hơn khoảng cách tuyệt đối giữa hai vector.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Phép tính: `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = ceil(22.111...)`.
> Đáp án: **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Khi overlap bằng 100: `ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = 25`, tức tăng từ 23 lên **25 chunks**. Overlap lớn hơn giúp giữ ngữ cảnh ở ranh giới chunk, nhưng làm tăng dung lượng lưu trữ và chi phí embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Tôi dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng đứng sau dấu kết câu, sau đó loại phần rỗng và nhóm tối đa `max_sentences_per_chunk` câu. Văn bản rỗng hoặc chỉ có khoảng trắng trả về danh sách rỗng; tham số số câu được chặn tối thiểu là 1.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử lần lượt các separator `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là ký tự. Base case là đoạn không vượt `chunk_size`; nếu không còn separator thì cắt cứng theo kích thước. Các phần nhỏ được ghép gần kích thước mục tiêu và giữ dấu phân cách để không làm mất ngữ cảnh.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi tài liệu được sao chép metadata, bổ sung `doc_id`, tạo embedding và lưu bằng một ID nội bộ duy nhất, cho phép nhiều chunks cùng thuộc một tài liệu. Khi tìm kiếm, query được embed, tính dot product với các vector đã lưu, sắp score giảm dần và lấy `top_k`. Với embedding chuẩn hóa, dot product tương đương cosine similarity.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc metadata trước khi xếp hạng để kết quả ngoài phạm vi không chiếm chỗ trong top-k. `delete_document` xóa tất cả records có `metadata["doc_id"]` trùng ID tài liệu gốc và chỉ trả `True` khi có dữ liệu bị xóa.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent lấy top-k chunks, đánh số từng chunk và đưa nội dung cùng nguồn truy vết vào retrieved context. Prompt yêu cầu LLM chỉ dựa trên context, coi chunk là dữ liệu chứ không phải chỉ dẫn, trích dẫn số chunk và thừa nhận khi thiếu thông tin. Prompt được truyền qua `llm_fn` nên có thể thay mock bằng LLM thật mà không đổi agent.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
Ran 42 tests in 0.014s

OK
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

`python ingest.py` cũng đã self-check thành công và `main.py` chạy end-to-end qua ingest → search → agent.

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng có thể đổi trả sản phẩm trong bảy ngày. | Người mua được yêu cầu hoàn hàng trong vòng 7 ngày. | Cao | 0.061322 | Có, thuộc nhóm 3 cặp cao hơn |
| 2 | Người bán phải cung cấp mô tả sản phẩm chính xác. | Thông tin đăng bán cần phản ánh đúng sản phẩm. | Cao | 0.000899 | Có, thuộc nhóm 3 cặp cao hơn |
| 3 | Đơn hàng đang được vận chuyển đến người mua. | Bưu kiện đang trên đường giao tới khách hàng. | Cao | 0.223393 | Có, cao nhất trong 5 cặp |
| 4 | Chính sách hoàn tiền áp dụng cho hàng bị lỗi. | Trời hôm nay có mưa lớn ở Hà Nội. | Thấp | -0.185868 | Có, thuộc nhóm 2 cặp thấp hơn |
| 5 | Người bán không được đăng sản phẩm bị cấm. | Cách nấu món phở bò truyền thống. | Thấp | -0.182587 | Có, thuộc nhóm 2 cặp thấp hơn |

> Tôi embed từng câu bằng `_mock_embed`, sau đó gọi `compute_similarity(vector_a, vector_b)`. Cột “Đúng?” đánh giá theo thứ hạng tương đối giữa 5 cặp, không dùng một ngưỡng tuyệt đối.

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 2 gần như bằng 0 dù hai câu khá gần nghĩa. `_mock_embed` sinh vector xác định từ toàn bộ chuỗi nhưng không học ngữ nghĩa, nên thay cách diễn đạt sẽ tạo vector gần như ngẫu nhiên. Kết quả này chỉ xác minh pipeline cosine; thí nghiệm semantic chính thức cần local multilingual embedder.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Chờ câu hỏi benchmark chung của nhóm | — | — | Chưa đánh giá | — |
| 2 | Chờ câu hỏi benchmark chung của nhóm | — | — | Chưa đánh giá | — |
| 3 | Chờ câu hỏi benchmark chung của nhóm | — | — | Chưa đánh giá | — |
| 4 | Chờ câu hỏi benchmark chung của nhóm | — | — | Chưa đánh giá | — |
| 5 | Chờ câu hỏi benchmark chung của nhóm | — | — | Chưa đánh giá | — |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** Chưa thể chấm hợp lệ.

> **Trạng thái:** Repo hiện chỉ có hai tài liệu template dùng URL `example.com`, trong khi K4 yêu cầu corpus 5–10 nguồn thật và đúng 5 benchmark queries chung của nhóm. Phần này sẽ được chạy sau CP6–CP8 với `EMBEDDING_PROVIDER=local`; không dùng dữ liệu mẫu để tạo số liệu nộp chính thức.

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> Chưa có dữ liệu demo của thành viên hoặc nhóm khác; cần bổ sung sau buổi so sánh nhóm.

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | Chưa chấm / 10 |
| **Tổng phần cá nhân hiện xác minh được** | **50 / 60** |
