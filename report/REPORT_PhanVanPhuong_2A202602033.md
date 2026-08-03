# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phan Văn Phương
**Nhóm:** G63
**Ngày:** 03/08/2026

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Hai vector có hướng gần nhau. Với text embeddings, điều này thường cho thấy hai câu có nội dung hoặc ý định tương tự.

**Ví dụ có độ tương tự CAO:**
- Câu A: Người mua muốn đổi trả sản phẩm bị lỗi.
- Câu B: Khách hàng gửi yêu cầu hoàn trả hàng bị lỗi.
- Tại sao tương đồng: Cùng nói về yêu cầu đổi trả do sản phẩm lỗi.

**Ví dụ có độ tương tự THẤP:**
- Câu A: Người mua cần nộp bằng chứng khi đổi trả.
- Câu B: Người bán cập nhật mô tả sản phẩm.
- Tại sao khác: Hai câu thuộc hai tác vụ khác nhau: đổi trả và đăng bán.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Cosine so sánh hướng của vector nên ít bị ảnh hưởng bởi độ lớn vector. Điều này phù hợp khi cần so sánh mức gần nhau về ngữ nghĩa giữa các embedding.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:* `ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450)`
> *Đáp án:* **23 chunks**.

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Số chunk là `ceil((10,000 - 100) / (500 - 100)) = 25`, nên tăng từ 23 lên 25. Overlap lớn hơn giữ ngữ cảnh ở ranh giới chunk tốt hơn, đổi lại tốn thêm dung lượng và chi phí embedding.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+` để tách tại khoảng trắng sau dấu kết thúc câu. Các câu được `strip()` rồi gom theo `max_sentences_per_chunk`; text rỗng trả về list rỗng.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán thử separator theo thứ tự `\n\n`, `\n`, `. `, khoảng trắng và cuối cùng là cắt theo ký tự. Base case là đoạn không vượt `chunk_size`; nếu không còn separator thì cắt cứng để bảo đảm luôn tạo được chunk hợp lệ.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi document được lưu thành record gồm id, content, metadata và embedding. Query cũng được embedding; kết quả được tính cosine similarity, sắp xếp giảm dần theo score và giới hạn bởi `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> Filter metadata được áp dụng trước khi search để chỉ xếp hạng các candidate đúng điều kiện. `delete_document` xóa mọi record có cùng `metadata["doc_id"]`, đồng thời xóa trên ChromaDB khi backend này hoạt động.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Agent lấy top-k chunk rồi ghép thành phần `Ngữ cảnh` có đánh số. Prompt yêu cầu LLM chỉ trả lời từ context; khi không có chunk phù hợp, prompt yêu cầu nêu rõ thiếu thông tin.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```text
Ran 42 tests in 0.039s

OK
```

**Số lượng bài test vượt qua (pass):** **42 / 42**

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|-----------|-----------|---------|--------------|-------|
| 1 | Người mua muốn đổi trả hàng lỗi. | Khách hàng gửi yêu cầu hoàn trả sản phẩm bị lỗi. | Cao | 0.369 | Có |
| 2 | Người bán phải mô tả sản phẩm chính xác. | Người bán cần cung cấp giá và tình trạng hàng đúng. | Cao | 0.577 | Có |
| 3 | Sản phẩm bị cấm không được đăng bán. | Không được niêm yết hàng hóa bị hạn chế. | Cao | 0.528 | Có |
| 4 | Người mua cần nộp bằng chứng khi đổi trả. | Nhà bán hàng cập nhật mô tả sản phẩm. | Thấp | 0.487 | Có |
| 5 | Chính sách đổi trả dành cho người mua. | Quy định đăng bán áp dụng cho người bán. | Thấp | 0.418 | Có |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Cặp 4 vẫn có score dương tương đối cao dù hai ý định khác nhau. Vì cùng miền TMĐT và cùng chứa các từ liên quan đến người mua/người bán, embedding vẫn nhận một phần ngữ cảnh chung; không nên dùng một ngưỡng score cố định để kết luận độ liên quan.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | | | | | |
| 2 | | | | | |
| 3 | | | | | |
| 4 | | | | | |
| 5 | | | | | |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** __ / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | / 5 |
| Hướng tiếp cận của tôi (My Approach) | / 10 |
| Hoàn thiện code (Core Implementation — tests) | / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | / 5 |
| Kết quả truy xuất của tôi (Competition Results) | / 10 |
| **Tổng phần cá nhân** | **/ 60** |