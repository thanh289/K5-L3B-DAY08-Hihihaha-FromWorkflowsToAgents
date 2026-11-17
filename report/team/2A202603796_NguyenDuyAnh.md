# Báo cáo cá nhân — MSSV_HoTen

Đổi tên file theo quy tắc `MSSV_HoTen.md`.

Ví dụ: `20241234_NguyenVanAn.md`.

## 1. Thông tin thành viên

- Họ tên: Nguyễn Duy Anh
- MSSV: 2A202603796
- Email: 26ai.anhnd15@vinuni.edu.vn
- GitHub: Danh1126

## 2. Phần việc phụ trách

Shape, module hoặc phần báo cáo bạn phụ trách.
- Shape C và phần test cho nó, lẫn handoff và kiểm thử chống rò rỉ dữ liệu

## 3. Đóng góp cụ thể

Commit chính (hash), test đã thêm hoặc sửa, quyết định kỹ thuật bạn đưa ra.
- hash: 9d837be
- đã add src/tests/test_orchestrator_handoff.py
- Phân tách rành mạch vai trò Orchestrator và investigator, investigator chỉ được cấp quyền gọi các tool chỉ đọc
 (lookup_order, lookup_policy, lookup_shipment) trong phạm vi allowed_tools, không được truy cập issue_refund

## 4. Bằng chứng

Link commit, tên test, run id hoặc trích đoạn report liên quan.
- https://github.com/thanh289/K5-L3B-DAY08-Hihihaha-FromWorkflowsToAgents/commit/9d837bec2569d4e094d264c0d31179406b1c60be
- test_public_matrix.py
- R-orchestrator-C-001-s11` (Claim hợp lệ): `passed: true`, `status: "resolved"`, `steps: 3`, `model_calls: 2`, `tool_calls: 6`, `cost_estimate: 61.54 VND`.

## 5. Công cụ AI đã dùng

Công cụ, dùng vào việc gì, và bạn đã tự kiểm tra kết quả thế nào (xem [RULES.md](../../RULES.md)).
- Công cụ sử dụng: Gemini
- Hỏi làm rõ cơ chế hoạt động của `make_handoff` và cách phân tách vai trò giữa Orchestrator, hỗ trợ quy trình Git
- *Tự rà soát và tinh chỉnh code:** Đọc hiểu toàn bộ luồng xử lý trong `src/lab8/shapes/orchestrator.py` và `src/tests/test_orchestrator_handoff.py`; tự điều chỉnh các assertion kiểm tra ngoại lệ `HandoffError` khi truyền tool ghi (`issue_refund`) và đảm bảo không để lọt khóa bí mật ra log trace.
  - Chạy kiểm thử tự động (pytest): Thực thi `python -m pytest -k "orchestrator" -v -o addopts=` và xác nhận tất cả unit test (bao gồm test_orchestrator_handoff.py đều đạt `PASSED`.
  
## 6. Tự đánh giá

...
