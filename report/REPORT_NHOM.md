# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** G63

**Thành viên:** Phan Văn Phương, Nguyễn Thành Huy, Đinh Đức Anh, Lê Huy Hoàng, Trần Minh Hạnh

**Ngày:** 03/08/2026

> **Nộp 1 bản / nhóm.** Phần cá nhân (hướng tiếp cận, kết quả riêng, dự đoán…) mỗi thành viên nộp riêng trong `REPORT_CANHAN.md`. Chi tiết thang điểm: `docs/SCORING.md`.

**Tổng điểm phần nhóm: 40** = Lựa chọn tài liệu (10) + Thiết kế chiến lược (15) + Chất lượng truy xuất (10) + Thuyết trình (5).

---

## 1. Lựa chọn tài liệu (Document Set Quality) — Nhóm (10 điểm)

### Phạm vi bộ tài liệu (Scope)

**Chủ đề (cố định theo lớp K4):** Chính sách thương mại điện tử / hỗ trợ khách hàng (thanh toán, đổi trả, giao hàng, quyền riêng tư, điều kiện người bán…).

**Phạm vi cụ thể nhóm tập trung:**
> Chính sách hỗ trợ người mua và người bán trên Shopee, tập trung vào đổi trả, đăng bán, vận chuyển, thanh toán và quyền riêng tư.

### Danh sách tài liệu (Data Inventory)

| # | Tên tài liệu | Nguồn (Source URL) | Ngày lấy / Phiên bản | Số ký tự | Metadata đã gán |
|---|--------------|------------|--------------------|----------|-----------------|
| 1 | Chính sách trả hàng và hoàn tiền | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77251?seo=1) | 03/08/2026 / hiệu lực 11/03/2026 | 1.476 | `customer_role=both`, `category=returns` |
| 2 | Quy định đăng bán sản phẩm | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77246) | 03/08/2026 / bản truy xuất | 1.408 | `customer_role=seller`, `category=listing` |
| 3 | Chính sách vận chuyển | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77250) | 03/08/2026 / đăng 20/03/2026 | 1.308 | `customer_role=both`, `category=shipping` |
| 4 | Chính sách bảo mật | [Shopee Help Center](https://help.shopee.vn/portal/4/article/77244) | 03/08/2026 / hiệu lực 11/06/2026 | 1.312 | `customer_role=both`, `category=privacy` |
| 5 | Các phương thức thanh toán | [Shopee Help Center](https://help.shopee.vn/portal/4/article/79198-) | 03/08/2026 / bản truy xuất | 1.346 | `customer_role=buyer`, `category=payment` |
| 6 | Hướng dẫn và giới hạn COD | [Shopee Help Center](https://help.shopee.vn/portal/4/article/79295-) | 03/08/2026 / bản truy xuất | 1.147 | `customer_role=buyer`, `category=payment` |

**Danh sách kiểm tra quản trị dữ liệu (Data governance checklist):**
- [x] Tập tài liệu chỉ chứa bản tóm lược từ Trung tâm trợ giúp công khai của Shopee; không chứa dữ liệu cá nhân, thông tin đăng nhập hoặc tài liệu nội bộ.
- [x] Mỗi tài liệu có `source_url`, `retrieved_at`, `document_version` và ánh xạ tương ứng trong `sources.csv`.

### Cấu trúc Metadata (Metadata Schema)

| Trường metadata | Kiểu | Ví dụ giá trị | Tại sao hữu ích cho truy xuất (retrieval)? |
|----------------|------|---------------|-------------------------------|
| `doc_id` | string | `shopee-returns-refunds` | Định danh duy nhất và liên kết các chunks để xóa/truy vết. |
| `customer_role` | enum string | `buyer`, `seller`, `both` | Lọc chính sách theo đối tượng người dùng theo yêu cầu K4. |
| `category` | enum string | `returns`, `listing`, `shipping`, `privacy`, `payment` | Thu hẹp retrieval theo nghiệp vụ. |
| `platform` | string | `shopee` | Cho phép mở rộng corpus sang nền tảng khác mà vẫn lọc được. |
| `language` | string | `vi` | Chọn tài liệu theo ngôn ngữ và embedding phù hợp. |
| `source_url` | URL string | `https://help.shopee.vn/...` | Truy vết và kiểm chứng câu trả lời tại nguồn chính thức. |
| `retrieved_at` | date | `2026-08-03` | Đánh giá độ mới của dữ liệu được thu thập. |
| `document_version` | string | `effective-2026-03-11` | Phân biệt phiên bản/ngày hiệu lực của chính sách. |

---

## 2. Thiết kế chiến lược (Strategy Design) — Nhóm (15 điểm)

> Mỗi thành viên thử **một chiến lược khác nhau** trên cùng bộ tài liệu; nhóm tổng hợp và so sánh ở đây.

### Phân tích đường cơ sở (Baseline Analysis)

Chạy `ChunkingStrategyComparator().compare()` trên 2-3 tài liệu:

| Tài liệu | Chiến lược (Strategy) | Số lượng Chunk | Độ dài trung bình | Giữ được ngữ cảnh không? |
|-----------|----------|-------------|------------|-------------------|
| Chính sách trả hàng và hoàn tiền | FixedSizeChunker (`fixed_size`) | 3 | 363.0 | Có, nhưng có thể cắt giữa ý khi chạm giới hạn ký tự. |
| Chính sách trả hàng và hoàn tiền | SentenceChunker (`by_sentences`) | 3 | 361.3 | Có, giữ được ranh giới câu. |
| Chính sách trả hàng và hoàn tiền | RecursiveChunker (`recursive`) | 4 | 270.8 | Có, ưu tiên đoạn/câu trước khi cắt theo ký tự. |
| Chính sách cấm/hạn chế sản phẩm | FixedSizeChunker (`fixed_size`) | 2 | 446.0 | Có, nhưng phụ thuộc vị trí cắt cố định. |
| Chính sách cấm/hạn chế sản phẩm | SentenceChunker (`by_sentences`) | 2 | 444.5 | Có, phù hợp khi câu không quá dài. |
| Chính sách cấm/hạn chế sản phẩm | RecursiveChunker (`recursive`) | 3 | 296.0 | Có, tách nhỏ hơn theo cấu trúc văn bản. |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — Phan Văn Phương**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=500)`.
- **Mô tả & lý do chọn cho chủ đề này:** Chiến lược ưu tiên ngắt tại đoạn, dòng mới, kết thúc câu và khoảng trắng trước khi cắt cứng theo ký tự. Chính sách TMĐT thường có điều kiện, ngoại lệ và trách nhiệm trong cùng một đoạn; cách này hạn chế cắt giữa ý so với fixed-size chunking.
- **Code snippet (nếu custom):** Không dùng custom chunker; dùng `RecursiveChunker` đã hoàn thiện trong package cá nhân.

**Thành viên 2 — Nguyễn Thành Huy**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=50)`.
- **Mô tả & lý do chọn:** Đây là baseline đơn giản, tạo các chunk có kích thước ổn định và giữ 50 ký tự overlap để giảm mất ngữ cảnh ở ranh giới. Kết quả của chiến lược này là mốc đối chiếu cho hai chiến lược còn lại.
- **Code snippet (nếu custom):** Không dùng custom chunker; dùng `FixedSizeChunker` có sẵn.

**Thành viên 3 — Đinh Đức Anh**
- **Loại chiến lược:** `RecursiveChunker(chunk_size=350)`.
- **Mô tả & lý do chọn:** Dùng cùng thứ tự separator nhưng giảm kích thước mục tiêu xuống 350 ký tự để các điều kiện và ngoại lệ ngắn dễ đứng gần nhau hơn khi retrieval. Đánh đổi là tăng số chunk và số vector cần lưu.
- **Code snippet (nếu custom):** Không dùng custom chunker; dùng `RecursiveChunker` với tham số khác.

**Thành viên 4 — Lê Huy Hoàng**
- **Loại chiến lược:** `FixedSizeChunker(chunk_size=500, overlap=100)`.
- **Mô tả & lý do chọn:** Tăng overlap so với baseline để giữ nhiều ngữ cảnh hơn tại ranh giới chunk, phù hợp với nội dung quy định có điều kiện kéo dài qua nhiều câu. Đánh đổi là có nội dung lặp giữa các chunks.
- **Code snippet (nếu custom):** Không dùng custom chunker; dùng `FixedSizeChunker` có sẵn.

**Thành viên 5 — Trần Minh Hạnh**
- **Loại chiến lược:** `SentenceChunker(max_sentences_per_chunk=3)`.
- **Mô tả & lý do chọn:** Chính sách hỗ trợ thường được viết thành các câu điều kiện, trách nhiệm và ngoại lệ. Gom tối đa ba câu giúp chunk không bị cắt giữa câu, đồng thời vẫn giữ kích thước vừa phải cho retrieval.
- **Code snippet (nếu custom):** Không dùng custom chunker; dùng `SentenceChunker` đã hoàn thiện.

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| Phan Văn Phương | RecursiveChunker (`chunk_size=500`) | Top-3: 5/5 | Giữ ngữ cảnh theo đoạn/câu trước khi cắt cứng. | 19 chunks, chi phí index cao hơn fixed-size. |
| Nguyễn Thành Huy | FixedSizeChunker (`chunk_size=500`, `overlap=50`) | Top-3: 5/5 | Kích thước chunk ổn định, dễ làm baseline. | Top-1 nhiễu ở query thời hạn đổi trả và quyền riêng tư. |
| Đinh Đức Anh | RecursiveChunker (`chunk_size=350`) | Top-3: 5/5 | Top-1 đúng ở cả query thời hạn đổi trả và quyền riêng tư. | 24 chunks, nhiều nhất trong năm cấu hình. |
| Lê Huy Hoàng | FixedSizeChunker (`chunk_size=500`, `overlap=100`) | Top-3: 5/5 | Overlap giữ thêm ngữ cảnh tại ranh giới. | Top-1 nhiễu ở query thời hạn đổi trả. |
| Trần Minh Hạnh | SentenceChunker (`max_sentences_per_chunk=3`) | Top-3: 5/5 | Bảo toàn ranh giới câu. | Top-1 nhiễu ở query thời hạn đổi trả và quyền riêng tư. |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> Cả năm cấu hình đều đạt 5/5 gold document trong top-3. Recursive `chunk_size=350` và `500` tốt hơn về độ chính xác top-1 ở các query dài, trong khi FixedSize là baseline đơn giản hơn và ít chunk hơn. Kết luận này chỉ đo retrieval; cần chạy LLM thật trên từng package cá nhân trước khi quy đổi thành điểm `/10` chính thức.

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | Người mua có bao lâu để gửi yêu cầu trả hàng đối với đơn thường và thực phẩm tươi sống? | Đơn thường: 15 ngày từ khi giao thành công; thực phẩm tươi sống/đông lạnh: 24 giờ. | `shopee-returns-refunds-policy` |
| 2 | Người bán phải tuân thủ điều gì khi đăng sản phẩm bị cấm hoặc hạn chế? | Tuân thủ pháp luật, điều khoản và chính sách Shopee; cập nhật danh sách cấm/hạn chế. | `shopee-prohibited-restricted-products` |
| 3 | Cần có bằng chứng gì khi khiếu nại đơn giao không thành công? | Video đóng gói có mã đơn/vận đơn, tình trạng sản phẩm và bao bì; video/biên bản đồng kiểm; vận đơn hoặc hóa đơn giao hàng. | `shopee-shipping-policy` |
| 4 | Vì sao thanh toán COD có thể không khả dụng? | Có thể do shop/kênh vận chuyển không hỗ trợ COD, hàng điện tử, tài khoản vượt giới hạn COD hoặc có nhiều đơn COD giao không thành công. | `shopee-cod-guide` |
| 5 | Liên hệ đầu mối nào để khiếu nại về quyền riêng tư? | Gửi tới đầu mối bảo vệ dữ liệu Shopee Việt Nam: `dpo.vn@shopee.com`. | `shopee-privacy-policy` |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | Thời hạn trả hàng/hoàn tiền | Recursive 350 hoặc Recursive 500 | Có | Hai cấu hình Recursive đưa đúng tài liệu lên top-1; các cấu hình khác vẫn có trong top-3. |
| 2 | Trách nhiệm người bán với hàng cấm/hạn chế | Cả 5 cấu hình | Có | `customer_role=seller` giúp chỉ còn candidate phù hợp. |
| 3 | Bằng chứng khiếu nại vận chuyển | Cả 5 cấu hình | Có | `shopee-shipping-policy` đứng top-1 ở cả 5 cấu hình. |
| 4 | Điều kiện COD không khả dụng | Cả 5 cấu hình | Có | `customer_role=buyer` giúp ưu tiên tài liệu COD/thanh toán. |
| 5 | Đầu mối quyền riêng tư | Recursive 350, Recursive 500 hoặc FixedSize overlap 100 | Có | Ba cấu hình này đưa đúng tài liệu lên top-1. |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> Có. Query 2 dùng `metadata_filter={"customer_role": "seller"}` nên chỉ tìm trong chính sách dành cho người bán; query 4 dùng `metadata_filter={"customer_role": "buyer"}` để giới hạn vào các tài liệu thanh toán/COD. Filter làm giảm nhiễu, nhưng contract hiện tại là match chính xác nên tài liệu có `customer_role=both` không xuất hiện khi lọc `seller` hoặc `buyer`.

> **Phạm vi đo:** Chạy cùng corpus 6 nguồn chính thức, OpenRouter `openai/text-embedding-3-small` và một package triển khai thống nhất để so sánh các cấu hình chunking. Kết quả xác minh retrieval top-3, chưa xác minh câu trả lời của LLM thật trên từng package thành viên.

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
- Metadata filter theo `customer_role` giúp tập trung retrieval cho truy vấn dành riêng cho buyer hoặc seller.
- Tất cả cấu hình tìm được gold document trong top-3, nhưng top-1 vẫn có nhiễu ở query dài có từ vựng chung giữa các chính sách.
- Recursive chunking tăng số chunk nhưng cải thiện top-1 ở query thời hạn đổi trả và đầu mối quyền riêng tư.

**Bài học rút ra khi so sánh trong nhóm:**
> Cùng corpus và embedding model, thay đổi chunking vẫn làm thay đổi thứ hạng top-1 dù top-3 recall giữ nguyên. Fixed-size cho baseline đơn giản, còn Recursive tách theo cấu trúc văn bản tốt hơn nhưng tạo nhiều chunk hơn. Vì vậy nhóm cần nhìn cả top-k relevance, số chunk và chi phí index thay vì chỉ nhìn score cao nhất.

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> Nhóm sẽ thay các bản tóm lược bằng nhiều nguồn/phiên bản chính thức hơn và tách theo heading hoặc điều khoản để giữ nguyên từng quy định. Metadata nên mở rộng cách lọc `customer_role=both` khi query theo `buyer` hoặc `seller`, thay vì chỉ match chính xác. Cuối cùng, nhóm sẽ chạy LLM thật và đối chiếu câu trả lời với gold answer trước khi chấm điểm chính thức.

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | 10 / 10 |
| Thiết kế chiến lược (Strategy Design) | 15 / 15 |
| Chất lượng truy xuất (Retrieval Quality) | 10 / 10 |
| Thuyết trình (Demo) | 5/5 |
| **Tổng phần nhóm hiện có** | **40 / 40** |
