# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Phan Văn Phương
**Nhóm:** G63
**Ngày:** 03/08/2026

> Báo cáo này ghi nhận phần code và thử nghiệm cá nhân. Phần benchmark chính thức phải dùng đúng 5 câu hỏi mà nhóm thống nhất trong `REPORT_NHOM.md`.

## 1. Khởi động (Warm-up)

### Độ tương tự cosine

Cosine similarity cao nghĩa là hai embedding có hướng gần nhau; với text, điều đó thường cho thấy hai câu có ngữ nghĩa hoặc chủ đề tương tự. Điểm này không tự nó chứng minh hai câu hoàn toàn đồng nghĩa.

**Ví dụ tương tự cao**

- Câu A: `Người mua muốn đổi trả sản phẩm bị lỗi.`
- Câu B: `Khách hàng gửi yêu cầu hoàn trả hàng bị lỗi.`
- Lý do: cùng ý định đổi trả do lỗi sản phẩm.

**Ví dụ tương tự thấp**

- Câu A: `Người mua cần nộp bằng chứng khi đổi trả.`
- Câu B: `Nhà bán hàng cập nhật mô tả sản phẩm.`
- Lý do: một câu nói về bằng chứng đổi trả, câu còn lại nói về nội dung đăng bán.

Cosine phù hợp với text embedding vì so sánh hướng của vector, giảm ảnh hưởng của độ lớn vector. Khoảng cách Euclid dễ thay đổi theo magnitude nên thường kém trực quan hơn khi chỉ cần so sánh ngữ nghĩa.

### Bài toán chunking

Với `length=10,000`, `chunk_size=500`, `overlap=50`:

```text
ceil((10,000 - 50) / (500 - 50)) = ceil(9,950 / 450) = 23 chunks
```

Nếu `overlap=100` thì:

```text
ceil((10,000 - 100) / (500 - 100)) = ceil(9,900 / 400) = 25 chunks
```

Overlap lớn hơn tạo nhiều chunk hơn vì bước trượt nhỏ đi. Đổi lại, ngữ cảnh ở ranh giới chunk được giữ tốt hơn, nhưng index tốn dung lượng và chi phí embedding hơn.

## 2. Hướng tiếp cận của tôi

### Chunking

`SentenceChunker.chunk()` dùng regex `(?<=[.!?])\s+` để tách sau dấu kết thúc câu, bỏ khoảng trắng dư và gom tối đa `max_sentences_per_chunk` câu. Chuỗi rỗng trả về list rỗng, còn một câu không bị tách thêm.

`RecursiveChunker` ưu tiên `\n\n`, `\n`, `. `, khoảng trắng rồi đến cắt theo ký tự. Base case là text không vượt `chunk_size`; nếu không còn separator phù hợp thì cắt cứng theo kích thước để luôn kết thúc.

### EmbeddingStore

`add_documents()` tạo record gồm `id`, `content`, `metadata` và embedding; `doc_id` được bổ sung vào metadata để hỗ trợ delete/filter. `search()` embedding query, tính cosine similarity với từng record, rồi sắp xếp giảm dần theo `score`.

`search_with_filter()` lọc metadata trước khi xếp hạng, giúp không trộn tài liệu khác vai trò người dùng. `delete_document()` xác định các record có cùng `metadata["doc_id"]` và xóa chúng khỏi in-memory store; nếu ChromaDB khởi tạo được thì cũng xóa cùng các id đó khỏi collection.

### KnowledgeBaseAgent

`answer()` lấy top-k chunk, gắn đánh số vào phần `Ngữ cảnh`, sau đó tạo prompt yêu cầu LLM chỉ trả lời từ bằng chứng đã truy xuất. Nếu store không trả chunk nào, prompt yêu cầu mô hình nói rõ là thiếu thông tin.

### Cấu hình embedding

`OpenAIEmbedder` dùng OpenAI SDK nhưng chỉ truyền `base_url` khi `OPENAI_BASE_URL` có giá trị. Vì vậy `.env` có thể đặt `OPENAI_BASE_URL=https://openrouter.ai/api/v1` và `OPENAI_EMBEDDING_MODEL=openai/text-embedding-3-small` để dùng OpenRouter; bỏ `OPENAI_BASE_URL` thì vẫn dùng endpoint OpenAI mặc định.

## 3. Hoàn thiện code

Đã hoàn thành `SentenceChunker`, `RecursiveChunker`, `compute_similarity`, `ChunkingStrategyComparator`, `EmbeddingStore` và `KnowledgeBaseAgent` trong package cá nhân. Code có fallback in-memory; ChromaDB chỉ được dùng khi import và tạo collection thành công.

### Kết quả kiểm thử

Lệnh chạy:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

Kết quả: `Ran 42 tests ... OK`.

**Số lượng bài test vượt qua:** **42 / 42**

Đã smoke-test OpenRouter với `main.py`: backend `openai/text-embedding-3-small` nạp thành công 3 chunks và trả kết quả retrieval. Không ghi API key vào report.

## 4. Dự đoán độ tương tự

Embedding: `openai/text-embedding-3-small` qua OpenRouter. Các giá trị là cosine similarity từ lần chạy ngày 03/08/2026; chỉ dùng để so sánh tương đối trong tập câu nhỏ này.

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|---|---|---|---|---:|---|
| 1 | Người mua muốn đổi trả hàng lỗi. | Khách hàng gửi yêu cầu hoàn trả sản phẩm bị lỗi. | Cao | 0.369 | Có |
| 2 | Người bán phải mô tả sản phẩm chính xác. | Người bán cần cung cấp giá và tình trạng hàng đúng. | Cao | 0.577 | Có |
| 3 | Sản phẩm bị cấm không được đăng bán. | Không được niêm yết hàng hóa bị hạn chế. | Cao | 0.528 | Có |
| 4 | Người mua cần nộp bằng chứng khi đổi trả. | Nhà bán hàng cập nhật mô tả sản phẩm. | Thấp | 0.487 | Có, thấp hơn các cặp cùng chủ đề gần nhất |
| 5 | Chính sách đổi trả dành cho người mua. | Quy định đăng bán áp dụng cho người bán. | Thấp | 0.418 | Có |

Kết quả đáng chú ý là cặp 4 vẫn có score dương khá cao. Điều này cho thấy không nên dùng một ngưỡng cố định để kết luận “liên quan”; câu ngắn cùng miền TMĐT có thể dùng từ vựng gần nhau dù ý định khác nhau. Cần so sánh thứ hạng giữa các candidate và kiểm tra bằng chứng gốc.

## 5. Kết quả truy xuất của tôi

### Thử nghiệm sơ bộ trên corpus khởi động

Corpus `data/k4_ecommerce/` hiện chỉ có 2 tài liệu mẫu, tạo thành 3 chunks. Nó chưa đáp ứng yêu cầu corpus nhóm 5-10 nguồn công khai, còn `REPORT_NHOM.md` chưa có 5 benchmark chung. Vì vậy bảng dưới đây là thử nghiệm cá nhân sơ bộ, **không phải kết quả benchmark chính thức của nhóm**.

| # | Câu hỏi | Top-1 chunk | Score | Có chunk liên quan trong top-3? | Ghi chú về agent |
|---|---|---|---:|---|---|
| 1 | Người mua gửi yêu cầu đổi trả khi nào? | `k4-returns-policy` | 0.302 | Có | `demo_llm` chỉ hiển thị prompt preview, không dùng để chấm factual answer |
| 2 | Đổi trả hàng lỗi cần kèm theo gì? | `k4-returns-policy` | 0.332 | Có | Tài liệu có nội dung về bằng chứng phù hợp |
| 3 | Người bán phải làm gì khi có yêu cầu đổi trả? | `k4-returns-policy` | 0.252 | Có | Tài liệu nêu người bán phản hồi theo quy trình sàn |
| 4 | Thông tin nào người bán cần cung cấp khi đăng sản phẩm? | `k4-returns-policy` | 0.362 | Có, nhưng không ở top-1 | `k4-seller-listing` ở top-2; corpus nhỏ gây nhiễu xếp hạng |
| 5 | Sản phẩm bị cấm có được đăng bán không? | `k4-returns-policy` | 0.311 | Có, nhưng không ở top-1 | `k4-seller-listing` ở top-2; cần thêm nguồn và chunk theo heading |

**Chunk liên quan trong top-3:** **5 / 5** trong thử nghiệm sơ bộ. Tuy nhiên top-1 chỉ đúng rõ ràng ở 3/5 câu, nên không thể dùng kết quả này để tuyên bố chất lượng retrieval tốt.

Để hoàn tất phần thi chính thức, nhóm cần thay dữ liệu mẫu bằng 5-10 nguồn được phép có metadata hợp lệ, thống nhất đúng 5 query/gold answer trong `REPORT_NHOM.md`, rồi chạy lại bảng này trên cùng corpus. Agent hiện dùng `demo_llm`; chỉ nên chấm “agent answer chính xác” khi nhóm cấu hình LLM sinh câu trả lời thật và đối chiếu với gold answer.

## Tự đánh giá

| Tiêu chí | Điểm tự đánh giá |
|---|---:|
| Khởi động | 5 / 5 |
| Hướng tiếp cận của tôi | 10 / 10 |
| Hoàn thiện code (42/42 tests) | 30 / 30 |
| Dự đoán độ tương tự | 5 / 5 |
| Kết quả truy xuất chính thức | 0 / 10 (chờ benchmark chung và corpus hợp lệ) |
| **Tổng hiện có** | **50 / 60** |
