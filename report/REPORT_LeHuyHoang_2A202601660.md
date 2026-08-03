# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** Lê Huy Hoàng
**Nhóm:** G63
**Ngày:** 2026-08-03

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> Cosine similarity đo góc giữa hai vector embedding, không quan tâm độ dài (magnitude) của chúng. Giá trị càng gần 1 nghĩa là hai đoạn văn bản càng "cùng hướng" trong không gian embedding — tức càng gần nhau về mặt ý nghĩa/ngữ cảnh, dù cách diễn đạt câu chữ có thể khác nhau hoàn toàn.

**Ví dụ có độ tương tự CAO (đã đo bằng `compute_similarity()` + OpenAI embeddings thật):**
- Câu A: "Người mua có thể trả hàng trong vòng 15 ngày kể từ khi nhận sản phẩm."
- Câu B: "Khách hàng được quyền hoàn trả sản phẩm trong 15 ngày sau khi giao hàng thành công."
- Điểm đo được: **0.818**
- Tại sao tương đồng: hai câu diễn đạt khác từ ngữ ("người mua" ↔ "khách hàng", "trả hàng" ↔ "hoàn trả sản phẩm") nhưng cùng một sự kiện/ý nghĩa (thời hạn trả hàng 15 ngày).

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Con mèo đang ngủ trên ghế sofa."
- Câu B: "Thời tiết Hà Nội hôm nay rất đẹp."
- Điểm đo được: **0.334**
- Tại sao khác: hai câu không liên quan cả về chủ đề lẫn ý nghĩa, không chia sẻ thực thể hay ngữ cảnh nào.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> Embedding của các câu dài/ngắn khác nhau có thể có magnitude (độ lớn vector) khác nhau dù cùng ý nghĩa; Euclidean distance bị ảnh hưởng bởi magnitude này nên dễ đánh giá sai. Cosine similarity chuẩn hóa theo độ dài vector, chỉ so sánh **hướng** — phản ánh đúng hơn sự tương đồng về ngữ nghĩa, bất kể độ dài văn bản gốc.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> Công thức: `số lượng chunk = ceil((10000 - 50) / (500 - 50))`
>
> Trình bày phép tính: `ceil(9950 / 450) = ceil(22.11) = 23`
>
> **Đáp án: 23 chunks**

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> Với overlap=100: `ceil((10000 - 100) / (500 - 100)) = ceil(9900 / 400) = ceil(24.75) = 25` chunks — tăng từ 23 lên 25 chunk (bước nhảy `step = chunk_size - overlap` nhỏ lại nên cần nhiều chunk hơn để phủ hết văn bản). Muốn overlap lớn hơn để giữ ngữ cảnh liên tục qua ranh giới chunk — tránh trường hợp một câu/ý quan trọng bị cắt đứt ngay giữa hai chunk, đánh đổi bằng việc tốn thêm dung lượng lưu trữ do nội dung bị lặp.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> Dùng regex `(?<=[.!?])\s+` (lookbehind) để tách câu ngay sau dấu `.`, `!`, `?` theo sau bởi khoảng trắng/xuống dòng — cách này gộp được cả 3 trường hợp `". "`, `"! "`, `"? "`, `".\n"` trong cùng một pattern thay vì phải xử lý riêng từng loại. Sau khi tách, loại bỏ chuỗi rỗng và strip khoảng trắng thừa, rồi gom nhóm `max_sentences_per_chunk` câu liên tiếp nối lại bằng dấu cách. Edge case xử lý: text rỗng trả về `[]` ngay từ đầu; nếu số câu không chia hết cho nhóm thì nhóm cuối chứa phần dư (ít câu hơn).

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> Thuật toán đệ quy theo kiểu "ưu tiên tách bằng separator lớn trước": nếu văn bản đã ngắn hơn `chunk_size` thì trả về nguyên (base case). Nếu không, tách bằng separator đầu tiên trong danh sách (`\n\n` → `\n` → `. ` → `" "` → `""`), rồi ghép các phần lại bằng thuật toán tham lam (greedy) cho tới khi gần đầy `chunk_size`; phần nào vẫn còn quá dài sau khi tách thì gọi đệ quy `_split` với separator kế tiếp (danh sách separator còn lại rút ngắn dần — đây là điều kiện dừng thứ hai). Nếu hết separator (`remaining_separators` rỗng) hoặc gặp separator rỗng `""`, fallback về cắt cứng theo `chunk_size` ký tự.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> Mỗi `Document` được chuẩn hóa qua `_make_record` thành 1 dict `{id, content, embedding, metadata}` (embedding gọi qua `embedding_fn` được inject — mock hoặc thật đều dùng chung interface). Lưu trong `self._store` (list, nếu không có ChromaDB) hoặc `collection.add(...)` (nếu có ChromaDB — đã implement thêm nhánh này dù máy tôi không cài chromadb nên chỉ chạy nhánh in-memory). Tính độ tương tự bằng **dot product** (`_dot`) chứ không dùng lại `compute_similarity` chuẩn hóa — vì các embedder (Mock + OpenAI) đều trả vector đã chuẩn hóa (norm=1), nên dot product tương đương cosine nhưng rẻ hơn. Kết quả sort giảm dần theo `score` rồi cắt `top_k`.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> `search_with_filter` lọc **trước** (metadata match tất cả key/value trong `metadata_filter`), rồi mới chạy lại đúng hàm `_search_records` dùng chung với `search` — tránh lặp code tính similarity. `delete_document` xóa bằng cách giữ lại các record có `metadata['doc_id'] != doc_id` (mọi record đều được gán `doc_id` mặc định bằng `id` của Document nếu metadata gốc không có sẵn, nhờ vậy vừa hỗ trợ case đơn giản — 1 Document = 1 chunk — vừa hỗ trợ case ingest pipeline gắn nhiều chunk chung 1 `doc_id`). Trả `True`/`False` dựa trên so sánh độ dài store trước/sau khi lọc.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> Retrieve `top_k` chunk liên quan nhất bằng `store.search(question, top_k=top_k)`, nối nội dung các chunk lại (ngăn cách bằng dòng trống) làm phần `Context`. Prompt dựng theo cấu trúc RAG tối giản: `Context: ... \n\n Question: ... \n Answer:` — chỉ đạo rõ "chỉ trả lời dựa trên context" để hạn chế hallucination. Cuối cùng gọi `llm_fn(prompt)` (được inject từ bên ngoài — có thể là hàm demo giả lập hoặc lời gọi OpenAI chat completion thật) và trả thẳng kết quả.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
$ pytest tests/ -v
...
tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED
tests/test_solution.py::TestFixedSizeChunker (7 tests) PASSED
tests/test_solution.py::TestSentenceChunker (4 tests) PASSED
tests/test_solution.py::TestRecursiveChunker (4 tests) PASSED
tests/test_solution.py::TestEmbeddingStore (8 tests) PASSED
tests/test_solution.py::TestKnowledgeBaseAgent (2 tests) PASSED
tests/test_solution.py::TestComputeSimilarity (4 tests) PASSED
tests/test_solution.py::TestCompareChunkingStrategies (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter (3 tests) PASSED
tests/test_solution.py::TestEmbeddingStoreDeleteDocument (3 tests) PASSED

============================= 42 passed in 0.16s ==============================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

Chạy `compute_similarity()` với embedding **thật** (OpenAI `text-embedding-3-small`) trên 5 cặp câu lấy từ chính bộ tài liệu K4 (Shopee returns-policy + seller-listing):

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | "Người mua có thể trả hàng trong vòng 15 ngày..." | "Khách hàng được quyền hoàn trả sản phẩm trong 15 ngày..." (paraphrase) | cao | 0.818 | ✓ |
| 2 | "Người mua có thể trả hàng trong vòng 15 ngày..." | "Người bán phải đăng ít nhất một ảnh thật do chính mình chụp sản phẩm." | thấp | 0.446 | ✓ |
| 3 | "Sản phẩm khi giao phải còn ít nhất 30% hạn sử dụng." | "Hàng hóa giao tới tay khách phải còn tối thiểu 30 phần trăm thời hạn sử dụng." (paraphrase) | cao | 0.783 | ✓ |
| 4 | "Sản phẩm khi giao phải còn ít nhất 30% hạn sử dụng." | "Tên sản phẩm phải viết tiếng Việt có dấu, không dùng từ ngữ dung tục." | thấp | 0.419 | ✓ |
| 5 | "Con mèo đang ngủ trên ghế sofa." | "Thời tiết Hà Nội hôm nay rất đẹp." | thấp | 0.334 | ✓ |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> Bất ngờ nhất là cặp 2 và 4: dù nội dung hai câu hoàn toàn khác chủ đề (thời hạn trả hàng vs. yêu cầu ảnh sản phẩm/đặt tên sản phẩm), điểm vẫn ở mức 0.42–0.45 — cao hơn hẳn cặp 5 (hai câu chung chung, không liên quan gì tới thương mại điện tử, chỉ đạt 0.334). Điều này cho thấy embedding không chỉ nắm bắt ý nghĩa sâu mà còn phản ánh **sự trùng lặp về chủ đề/từ vựng lĩnh vực** (cùng nói về "sản phẩm", "Shopee", quy định mua bán) — nên hai câu "khác ý nhưng cùng miền chủ đề" vẫn có điểm cosine cao hơn hai câu hoàn toàn khác miền, dù cả hai đều được xem là "thấp" so với các cặp paraphrase thực sự.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy trên `src` cá nhân, dùng **embedder thật** (`EMBEDDING_PROVIDER=openai`, model `text-embedding-3-small`) và **LLM thật** (`gpt-4o-mini`) qua `KnowledgeBaseAgent`, trên bộ dữ liệu thật `data/k4_ecommerce/` (2 tài liệu Shopee: chính sách trả hàng + quy định đăng bán, 24 chunk sau khi `build_knowledge_base` chunk bằng `FixedSizeChunker` mặc định).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao nhiêu ngày để yêu cầu trả hàng kể từ khi nhận hàng? | Đoạn "Thời hạn gửi yêu cầu: trong vòng 15 ngày..." (returns-policy.md) | 0.586 | Có | "15 ngày, riêng thực phẩm tươi sống/đông lạnh chỉ 24 giờ." |
| 2 | Người bán có bao nhiêu ngày để phản hồi yêu cầu trả hàng của Shopee? | Đoạn "Người Bán có 2 ngày lịch để phản hồi..." (returns-policy.md) | 0.660 | Có | "Người Bán có 2 ngày lịch để phản hồi." |
| 3 | Mỹ phẩm cần giấy tờ gì để được phép đăng bán trên Shopee? *(dùng `metadata_filter={"customer_role":"seller"}`)* | Đoạn "Mỹ phẩm: ... cần đăng kèm phiếu công bố mỹ phẩm và chứng từ nhập hàng hợp lệ." (seller-listing.md) | 0.647 | Có | "Cần phiếu công bố mỹ phẩm và chứng từ nhập hàng hợp lệ." |
| 4 | Ai phải chịu phí vận chuyển khi việc trả hàng là do lỗi của đơn vị vận chuyển? | Đoạn nêu các trường hợp "lỗi thuộc về đơn vị vận chuyển..." (returns-policy.md) | 0.608 | Có | "Người Bán phải chịu phí vận chuyển trong trường hợp này." |
| 5 | Ảnh sản phẩm khi đăng bán phải đáp ứng yêu cầu gì? *(dùng `metadata_filter={"customer_role":"seller"}`)* | Đoạn "Hình ảnh: phải là ảnh thật, rõ nét, tối thiểu một ảnh tự chụp..., chiếm ít nhất 40% diện tích ảnh..." (seller-listing.md) | 0.608 | Có | "Ảnh thật, rõ nét, ≥40% diện tích ảnh là sản phẩm, không chèn thông tin liên hệ, không phản cảm." |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5 (cả 5 câu đều đúng ngay ở top-1)

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *[Nhóm chưa demo — điền phần này sau khi nghe các thành viên/nhóm khác trình bày chiến lược chunking và so sánh kết quả của họ.]*

---

## Tự Đánh Giá (Phần Cá Nhân)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Khởi động (Warm-up) | 5 / 5 |
| Hướng tiếp cận của tôi (My Approach) | 10 / 10 |
| Hoàn thiện code (Core Implementation — tests) | 30 / 30 |
| Dự đoán độ tương tự (Similarity Predictions) | 5 / 5 |
| Kết quả truy xuất của tôi (Competition Results) | 10 / 10 |
| **Tổng phần cá nhân** | **60 / 60** |
