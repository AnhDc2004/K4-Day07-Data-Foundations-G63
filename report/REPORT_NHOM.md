# Báo Cáo Nhóm — Lab 7: Embedding & Vector Store

**Nhóm:** [G63]
**Thành viên:** [Đinh Đức Anh, Phan Văn Phương, Nguyễn Thành Huy, Trần Minh Hạnh, Lê Huy Hoàng]
**Ngày:** [03/08/2026]

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
| | FixedSizeChunker (`fixed_size`) | | | |
| | SentenceChunker (`by_sentences`) | | | |
| | RecursiveChunker (`recursive`) | | | |

### Chiến lược của từng thành viên

> Mỗi thành viên điền một khối dưới đây (copy thêm nếu nhóm có nhiều hơn 3 người).

**Thành viên 1 — [Tên]**
- **Loại chiến lược:** [FixedSize / Sentence / Recursive / custom]
- **Mô tả & lý do chọn cho chủ đề này:** *(2-3 câu)*
- **Code snippet (nếu custom):**
```python
# Dán mã nguồn (implementation) vào đây
```

**Thành viên 2 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

**Thành viên 3 — [Tên]**
- **Loại chiến lược:**
- **Mô tả & lý do chọn:**
- **Code snippet (nếu custom):**

### So Sánh Giữa Các Thành Viên

| Thành viên | Chiến lược (Strategy) | Điểm truy xuất (/10) | Điểm mạnh | Điểm yếu |
|-----------|----------|----------------------|-----------|----------|
| | | | | |
| | | | | |
| | | | | |

**Chiến lược nào tốt nhất cho chủ đề này? Tại sao?**
> *Viết 2-3 câu — đây là phần được đánh giá cao nhất (khả năng suy nghĩ & giải thích):*

---

## 3. Câu hỏi đánh giá & Chất lượng truy xuất (Retrieval Quality) — Nhóm (10 điểm)

### Câu hỏi đánh giá & Câu trả lời chuẩn (nhóm thống nhất)

> **Đúng 5 câu hỏi**, đa dạng, có thể kiểm chứng; **ít nhất 1 câu** cần lọc metadata mới trả lời tốt. Đây là bộ câu hỏi chung cho mọi thành viên chạy.

| # | Câu hỏi (Query) | Câu trả lời chuẩn (Gold Answer) | Chunk nào chứa thông tin? |
|---|-------|-------------------------------|--------------------------|
| 1 | | | |
| 2 | | | |
| 3 | | | |
| 4 | | | |
| 5 | | | |

### Tổng hợp chất lượng truy xuất của nhóm

> Cách chấm (theo `docs/SCORING.md`): **2 điểm/câu** — top-3 chứa chunk liên quan + agent trả lời đúng (2), có liên quan nhưng thiếu/không ở top-1 (1), không có trong top-3 (0).

| # | Câu hỏi | Chiến lược tốt nhất cho câu này | Có chunk liên quan trong top-3? | Ghi chú |
|---|---------|-------------------------------|-------------------------------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |

**Lọc bằng metadata có giúp ích không? Ở câu hỏi nào?**
> *Viết 2-3 câu:*

---

## 4. Thuyết trình (Demo) & Bài học nhóm — Nhóm (5 điểm)

**Những phân tích (insights) hay nhất nhóm sẽ trình bày:**
> *Liệt kê 2-3 ý:*

**Bài học rút ra khi so sánh trong nhóm:**
> *Viết 2-3 câu — cùng tài liệu nhưng chiến lược khác nhau dẫn tới khác biệt gì?*

**Nếu làm lại, nhóm sẽ thay đổi gì trong chiến lược dữ liệu (data strategy)?**
> *Viết 2-3 câu:*

---

## Tự Đánh Giá (Phần Nhóm)

| Tiêu chí | Điểm tự đánh giá |
|----------|-------------------|
| Lựa chọn tài liệu (Document Set Quality) | / 10 |
| Thiết kế chiến lược (Strategy Design) | / 15 |
| Chất lượng truy xuất (Retrieval Quality) | / 10 |
| Thuyết trình (Demo) | / 5 |
| **Tổng phần nhóm** | **/ 40** |
