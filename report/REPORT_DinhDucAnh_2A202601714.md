# Báo Cáo Cá Nhân — Lab 7: Embedding & Vector Store

**Họ tên:** [Đinh Đức Anh]
**Nhóm:** [G63]
**Ngày:** [03/08/2026]

> **Nộp 1 bản / sinh viên.** Phần nhóm (lựa chọn tài liệu, thiết kế chiến lược, bộ câu hỏi đánh giá, demo) nộp chung 1 bản trong `REPORT_NHOM.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần cá nhân: 60** = Khởi động (5) + Hướng tiếp cận (10) + Hoàn thiện code (30) + Dự đoán độ tương tự (5) + Kết quả truy xuất của tôi (10).

---

## 1. Khởi động (Warm-up) — Cá nhân (5 điểm)

### Độ tương tự Cosine (Cosine Similarity) (Bài tập 1.1)

**Độ tương tự cosine cao (High cosine similarity) nghĩa là gì?**
> *Viết 1-2 câu:*

> Độ tương tự Cosine cao (tiệm cận 1.0) cho thấy hai vector văn bản chỉ cùng về một hướng trong không gian đa chiều, tức là hai câu/văn bản có sự tương đồng lớn về mặt ngữ nghĩa, bất kể độ dài ngắn khác nhau.

**Ví dụ có độ tương tự CAO:**
- Câu A: "Thời hạn đổi trả sản phẩm lỗi là 7 ngày kể từ khi nhận hàng."
- Câu B: "Khách hàng có thể trả lại hàng bị lỗi trong vòng một tuần sau khi giao thành công."
- Tại sao tương đồng: Cả hai câu đều diễn đạt cùng một chính sách về thời gian đổi trả hàng lỗi (7 ngày = 1 tuần) mặc dù sử dụng từ ngữ và từ vựng hoàn toàn khác nhau.

**Ví dụ có độ tương tự THẤP:**
- Câu A: "Khách hàng có thể thanh toán qua ví MoMo hoặc thẻ VISA."
- Câu B: "Chính sách bảo hành sản phẩm điện tử kéo dài 12 tháng."
- Tại sao khác: Hai câu đề cập đến hai chủ đề hoàn toàn độc lập (phương thức thanh toán vs thời gian bảo hành) nên hướng vector ngữ nghĩa hoàn toàn khác nhau.

**Tại sao độ tương tự cosine (cosine similarity) được ưu tiên hơn khoảng cách Euclid (Euclidean distance) cho text embeddings?**
> *Viết 1-2 câu:*

Độ tương tự Cosine chỉ đo góc giữa hai vector mà không bị ảnh hưởng bởi độ dài (magnitude) của vector. Khi so sánh hai đoạn văn có cùng nội dung nhưng một đoạn dài (chứa nhiều từ lặp lại) và một đoạn ngắn, khoảng cách Euclid sẽ rất lớn (do độ dài vector chênh lệch), trong khi độ tương tự Cosine vẫn phản ánh đúng độ tương đồng ngữ nghĩa.

### Bài toán tính toán Chunking (Bài tập 1.2)

**Tài liệu 10,000 ký tự, chunk_size=500, overlap=50. Bao nhiêu chunks?**
> *Trình bày phép tính:*

Step (bước tiến giữa các chunk) = chunk_size - overlap = 500 - 50 = 450 ký tự

chunk 1: [0:500]

chunk 2: [450:950]

...

Số bước tiến đầy đủ $k$ sao cho $\text{start} + 500 < 10,000$: $\lfloor (10,000 - 500) / 450 \rfloor = \lfloor 9500 / 450 \rfloor = 21$ bước tiến.

Điểm bắt đầu của chunk thứ 22: $21 \times 450 = 9450$. Chunk 22 covers $[9450 : 9950]$.

Điểm bắt đầu của chunk thứ 23: $22 \times 450 = 9900$. Chunk 23 covers $[9900 : 10000]$ (chứa 100 ký tự còn lại).

> *Đáp án:*

22 chunks (21 chunk độ dài 500 và 1 chunk cuối cùng chứa ký tự còn lại).

**Nếu độ chồng chéo (overlap) tăng lên 100, số lượng chunk thay đổi thế nào? Tại sao muốn độ chồng chéo nhiều hơn?**
> *Viết 1-2 câu:*

Khi overlap tăng lên 100, bước tiến (step) giảm xuống còn $400$ ký tự, dẫn đến số lượng chunk tăng lên thành $\lceil (10,000 - 100) / 400 \rceil = 25$ chunks. Tăng overlap giúp giữ lại ngữ cảnh liên tục giữa các đoạn văn giáp ranh, tránh việc câu hoặc ý nghĩa bị ngắt đôi ở ranh giới của chunk.

---

## 2. Hướng tiếp cận của tôi (My Approach) — Cá nhân (10 điểm)

Giải thích cách tiếp cận của bạn khi lập trình (implement) các phần chính trong gói `src`.

### Các hàm chia nhỏ (Chunking Functions)

**`SentenceChunker.chunk`** — hướng tiếp cận:
> *Viết 2-3 câu: dùng biểu thức chính quy (regex) gì để phát hiện câu? Xử lý trường hợp ngoại lệ (edge case) nào?*

Sử dụng regex re.split(r'(?<=[.!?])\s+|\n+', text.strip()) dựa trên Lookbehind để tách văn bản thành các câu riêng biệt tại dấu câu . ! ? hoặc ký tự xuống dòng mà không làm mất dấu câu. Sau đó, các câu rỗng được loại bỏ và gom thành từng nhóm tối đa max_sentences_per_chunk câu bằng vòng lặp step.

**`RecursiveChunker.chunk` / `_split`** — hướng tiếp cận:
> *Viết 2-3 câu: thuật toán hoạt động thế nào? Base case (trường hợp cơ sở) là gì?*

Thuật toán đệ quy thử nghiệm phân tách văn bản bằng danh sách ưu tiên ["\n\n", "\n", ". ", " ", ""]. Trường hợp cơ sở (base case) là khi văn bản nhỏ hơn hoặc bằng chunk_size thì giữ nguyên. Nếu tách ra các đoạn nhỏ hơn, hàm thực hiện gộp (merge) các mẩu nhỏ lại sao cho tổng độ dài kèm separator không vượt quá chunk_size để tránh làm vỡ vụn văn bản.

### Lớp EmbeddingStore

**`add_documents` + `search`** — hướng tiếp cận:
> *Viết 2-3 câu: lưu trữ thế nào? Tính độ tương tự ra sao?*

Hàm add_documents nhận danh sách Document, tính vector nhúng qua _embedding_fn và chuẩn hóa metadata (gắn tự động doc_id nếu thiếu) để lưu vào danh sách _store (hoặc ChromaDB). Hàm search nhúng câu truy vấn query, tính điểm similarity giữa vector query với toàn bộ các record trong kho lưu trữ qua hàm compute_similarity, sắp xếp giảm dần theo điểm số và cắt lấy top_k kết quả.

**`search_with_filter` + `delete_document`** — hướng tiếp cận:
> *Viết 2-3 câu: lọc (filter) trước hay sau? Xóa bằng cách nào?*

search_with_filter áp dụng pre-filtering: duyệt qua kho _store để lọc các record khớp toàn bộ cặp key-value trong metadata_filter trước, sau đó mới tính độ tương tự và xếp hạng. delete_document lọc bỏ các record có id hoặc metadata['doc_id'] trùng với doc_id cần xóa, trả về True nếu số lượng phần tử bị giảm đi.

### Tác tử KnowledgeBaseAgent

**`answer`** — hướng tiếp cận:
> *Viết 2-3 câu: cấu trúc prompt? Cách đưa ngữ cảnh (inject context) vào thế nào?*

Gọi self.store.search(question, top_k) để truy xuất top-k chunk liên quan nhất, trích xuất nội dung content và nối lại thành chuỗi ngữ cảnh context_str. Tạo prompt định dạng mẫu đặt ngữ cảnh và câu hỏi, sau đó chuyển prompt này cho self.llm_fn(prompt) để sinh ra câu trả lời dựa trên căn cứ dữ liệu.

---

## 3. Hoàn thiện code (Core Implementation) — Cá nhân (30 điểm)

Vượt qua bộ kiểm thử là điều kiện tính điểm phần này.

### Kết Quả Kiểm Thử (Test Results)

```
# Dán kết quả (output) của: pytest tests/ -v
======================================================================================================= test session starts ========================================================================================================
platform win32 -- Python 3.11.9, pytest-9.1.1, pluggy-1.6.0 -- E:\Lab1\K4-Day07-Data-Foundations-G63\.venv\Scripts\python.exe
cachedir: .pytest_cache
rootdir: E:\Lab1\K4-Day07-Data-Foundations-G63
plugins: anyio-4.14.2
collected 42 items                                                                                                                                                                                                                  

tests/test_solution.py::TestProjectStructure::test_root_main_entrypoint_exists PASSED                                                                                                                                        [  2%]
tests/test_solution.py::TestProjectStructure::test_src_package_exists PASSED                                                                                                                                               [  4%]
tests/test_solution.py::TestClassBasedInterfaces::test_chunker_classes_exist PASSED                                                                                                                                         [  7%]
tests/test_solution.py::TestClassBasedInterfaces::test_mock_embedder_exists PASSED                                                                                                                                          [  9%]
tests/test_solution.py::TestFixedSizeChunker::test_chunks_respect_size PASSED                                                                                                                                             [ 11%]
tests/test_solution.py::TestFixedSizeChunker::test_correct_number_of_chunks_no_overlap PASSED                                                                                                                             [ 14%]
tests/test_solution.py::TestFixedSizeChunker::test_empty_text_returns_empty_list PASSED                                                                                                                                   [ 16%]
tests/test_solution.py::TestFixedSizeChunker::test_no_overlap_no_shared_content PASSED                                                                                                                                    [ 19%]
tests/test_solution.py::TestFixedSizeChunker::test_overlap_creates_shared_content PASSED                                                                                                                                  [ 21%]
tests/test_solution.py::TestFixedSizeChunker::test_returns_list PASSED                                                                                                                                                   [ 23%]
tests/test_solution.py::TestFixedSizeChunker::test_single_chunk_if_text_shorter PASSED                                                                                                                                    [ 26%]
tests/test_solution.py::TestSentenceChunker::test_chunks_are_strings PASSED                                                                                                                                              [ 28%]
tests/test_solution.py::TestSentenceChunker::test_respects_max_sentences PASSED                                                                                                                                           [ 30%]
tests/test_solution.py::TestSentenceChunker::test_returns_list PASSED                                                                                                                                                      [ 33%]
tests/test_solution.py::TestSentenceChunker::test_single_sentence_max_gives_many_chunks PASSED                                                                                                                            [ 35%]
tests/test_solution.py::TestRecursiveChunker::test_chunks_within_size_when_possible PASSED                                                                                                                                [ 38%]
tests/test_solution.py::TestRecursiveChunker::test_empty_separators_falls_back_gracefully PASSED                                                                                                                         [ 40%]
tests/test_solution.py::TestRecursiveChunker::test_handles_double_newline_separator PASSED                                                                                                                                [ 42%]
tests/test_solution.py::TestRecursiveChunker::test_returns_list PASSED                                                                                                                                                     [ 45%]
tests/test_solution.py::TestEmbeddingStore::test_add_documents_increases_size PASSED                                                                                                                                      [ 47%]
tests/test_solution.py::TestEmbeddingStore::test_add_more_increases_further PASSED                                                                                                                                        [ 50%]
tests/test_solution.py::TestEmbeddingStore::test_initial_size_is_zero PASSED                                                                                                                                               [ 52%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_content_key PASSED                                                                                                                                   [ 54%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_have_score_key PASSED                                                                                                                                      [ 57%]
tests/test_solution.py::TestEmbeddingStore::test_search_results_sorted_by_score_descending PASSED                                                                                                                         [ 59%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_at_most_top_k PASSED                                                                                                                                      [ 61%]
tests/test_solution.py::TestEmbeddingStore::test_search_returns_list PASSED                                                                                                                                              [ 64%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_non_empty PASSED                                                                                                                                              [ 66%]
tests/test_solution.py::TestKnowledgeBaseAgent::test_answer_returns_string PASSED                                                                                                                                         [ 69%]
tests/test_solution.py::TestComputeSimilarity::test_identical_vectors_return_1 PASSED                                                                                                                                     [ 71%]
tests/test_solution.py::TestComputeSimilarity::test_opposite_vectors_return_minus_1 PASSED                                                                                                                                [ 73%]
tests/test_solution.py::TestComputeSimilarity::test_orthogonal_vectors_return_0 PASSED                                                                                                                                    [ 76%]
tests/test_solution.py::TestComputeSimilarity::test_zero_vector_returns_0 PASSED                                                                                                                                          [ 78%]
tests/test_solution.py::TestCompareChunkingStrategies::test_counts_are_positive PASSED                                                                                                                                    [ 80%]
tests/test_solution.py::TestCompareChunkingStrategies::test_each_strategy_has_count_and_avg_length PASSED                                                                                                                       [ 83%]
tests/test_solution.py::TestCompareChunkingStrategies::test_returns_three_strategies PASSED                                                                                                                               [ 85%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_filter_by_department PASSED                                                                                                                             [ 88%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_no_filter_returns_all_candidates PASSED                                                                                                                  [ 90%]
tests/test_solution.py::TestEmbeddingStoreSearchWithFilter::test_returns_at_most_top_k PASSED                                                                                                                             [ 92%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_reduces_collection_size PASSED                                                                                                                      [ 95%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_false_for_nonexistent_doc PASSED                                                                                                           [ 97%]
tests/test_solution.py::TestEmbeddingStoreDeleteDocument::test_delete_returns_true_for_existing_doc PASSED                                                                                                                [100%]

======================================================================================================== 42 passed in 0.80s ========================================================================================================
```

**Số lượng bài test vượt qua (pass):** 42 / 42

---

## 4. Dự đoán độ tương tự (Similarity Predictions) — Cá nhân (5 điểm)

| Cặp | Câu A | Câu B | Dự đoán | Điểm thực tế | Đúng? |
|------|-----------|-----------|---------|--------------|-------|
| 1 | Khách hàng được đổi trả trong 7 ngày. | Sản phẩm bị lỗi có thể hoàn trả trong vòng 1 tuần. | cao | 0.88 | Đúng |
| 2 | Hướng dẫn thanh toán qua ví điện tử. | Quy định đóng gói và vận chuyển hàng hóa. | thấp | 0.21 | Đúng |
| 3 | Người bán phải cung cấp mã vận đơn trong 24h. | Seller cần cập nhật tracking number trong ngày. | cao | 0.82 | Đúng |
| 4 | Chính sách bảo mật thông tin người dùng. | Điều khoản dịch vụ dành cho người mua hàng. | cao | 0.65 | Đúng |
| 5 | Giao hàng không thành công do sai địa chỉ. | Đơn hàng bị hủy do hết hàng trong kho. | thấp | 0.43 | Đúng |

**Kết quả nào bất ngờ nhất? Điều này nói gì về cách embeddings biểu diễn ý nghĩa?**
> *Viết 2-3 câu:*

Kết quả ở cặp số 3 gây ấn tượng nhất vì mô hình nhúng đa ngữ xử lý rất tốt các từ mượn tiếng Anh lẫn thuật ngữ chuyên ngành (Seller, tracking number) tương đồng nghĩa với tiếng Việt (Người bán, mã vận đơn). Điều này chứng minh embeddings biểu diễn ngữ nghĩa vượt qua ranh giới ngôn ngữ bề mặt, tập trung vào bản chất khái niệm.

---

## 5. Kết quả truy xuất của tôi (Competition Results) — Cá nhân (10 điểm)

Chạy **5 câu hỏi đánh giá của nhóm** trên mã nguồn cá nhân của bạn trong gói `src`. **5 câu hỏi này phải trùng với các thành viên cùng nhóm** (xem `REPORT_NHOM.md`).

| # | Câu hỏi (Query) | Top-1 Chunk truy xuất được (tóm tắt) | Điểm Score | Có liên quan không? (Relevant) | Câu trả lời của Agent (tóm tắt) |
|---|-------|--------------------------------|-------|-----------|------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng đối với đơn thường và thực phẩm tươi sống? | "Đơn hàng thông thường có 15 ngày kể từ khi giao hàng thành công. Đối với thực phẩm tươi sống hoặc đông lạnh, thời hạn gửi yêu cầu là 24 giờ..." | 0.87 | Có | Đơn thường có thời hạn 15 ngày kể từ khi giao thành công, còn thực phẩm tươi sống/đông lạnh là 24 giờ. |
| 2 | Quy định thời gian tối đa để người bán chuẩn bị hàng là bao lâu? (filter: customer_role="seller") | "Người bán có nghĩa vụ xác nhận đơn hàng và giao cho đơn vị vận chuyển trong tối đa 24 giờ làm việc..." | 0.89 | Có | Người bán cần chuẩn bị và bàn giao hàng cho bên vận chuyển trong vòng 24 giờ làm việc. |
| 3 | Phương thức thanh toán nào được áp dụng cho đơn hàng COD? | "Đơn hàng ship COD hỗ trợ thanh toán tiền mặt trực tiếp cho shipper khi nhận hàng..." | 0.81 | Có | Thanh toán tiền mặt trực tiếp khi shipper giao hàng được áp dụng cho đơn COD. |
| 4 | Khi nào shop bị tính phí phạt hủy đơn tự động? | "Shop bị tính phạt hủy đơn tự động nếu không giao hàng sau 48h hoặc tự ý bấm hủy do hết hàng..." | 0.84 | Có | Shop bị phạt hủy đơn nếu tự ý hủy hoặc quá 48h không chuyển hàng cho đơn vị vận chuyển. |
| 5 | Quyền riêng tư đối với thông tin số điện thoại người mua được xử lý ra sao? | "Số điện thoại của người mua được ẩn dạng *** trên mã vận đơn nhằm bảo vệ quyền riêng tư..." | 0.79 | Có | Số điện thoại được che mờ dưới dạng *** trên nhãn vận chuyển để bảo mật thông tin cá nhân. |

**Bao nhiêu câu hỏi trả về chunk có liên quan trong top-3?** 5 / 5

**Điều hay nhất tôi học được từ thành viên khác / nhóm khác (qua demo):**
> *Viết 2-3 câu:*

Nhóm bạn sử dụng chiến lược RecursiveChunker kết hợp cắt theo tiêu đề Markdown (#, ##) giữ được ngữ cảnh ngữ pháp trọn vẹn hơn SentenceChunker. Ngoài ra việc bổ sung trường metadata category phối hợp với customer_role giúp lọc bỏ hoàn toàn nhiễu từ các văn bản chính sách chung.

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
