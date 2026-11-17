# Báo cáo cá nhân — 2A202603927_DamHongThai

## 1. Thông tin thành viên

- Họ tên: Đàm Hồng Thái
- MSSV: 2A202603927
- Email: 26ai.thaidh@vinuni.edu.vn
- GitHub: https://github.com/itsbra1vo

## 2. Phần việc phụ trách

Phụ trách Shape B — single agent, triển khai trong [`src/lab8/shapes/single.py`](../../src/lab8/shapes/single.py). Shape dùng vòng lặp ReAct có giới hạn 8 bước để đọc thông tin claim/đơn hàng và tính mức bồi thường; phần host xử lý quyết định refund, durability và trace.

## 3. Đóng góp cụ thể

- Commit hash : 9094d4f1526b426ec7991f5ad48a3f8b8a4e4c9c
- Sửa `src/lab8/shapes/single.py` để thực hiện luồng single-agent: đọc claim, tra cứu đơn hàng, gọi công cụ tính compensation và xử lý kết quả.
- Giữ quyết định refund ở phía host qua `issue_refund`, truyền tiếp `crash_at`, giới hạn số bước và hoàn tất kết quả/trace theo contract.

## 4. Bằng chứng

- Link commit : https://github.com/thanh289/K5-L3B-DAY08-Hihihaha-FromWorkflowsToAgents/pull/1/changes/9094d4f1526b426ec7991f5ad48a3f8b8a4e4c9c
- [`test_public_single_run_cases`](../../src/tests/test_public_matrix.py): kiểm tra các claim đơn với nhiều seed; ma trận được tham số hóa cho các shape, trong đó có `single`.
- [`test_t11_retry_keeps_one_refund`](../../src/tests/test_public_matrix.py): kiểm tra retry không tạo refund trùng.
- [`test_t12_crash_before_checkpoint_does_not_double_pay`](../../src/tests/test_public_matrix.py): kiểm tra crash rồi chạy tiếp không trả refund hai lần.
- Kết quả xác thực trong workspace: `62 passed, 186 deselected` khi chạy ma trận chỉ với tham số shape `single`.

## 5. Công cụ AI đã dùng

- Copilot trong VS Code hỗ trợ rà soát nội dung `single.py`.

- Tham khảo [RULES.md](../../RULES.md).

## 6. Tự đánh giá

Phần `single.py` có luồng xử lý tách biệt giữa agent và host, giới hạn số bước, xử lý refund qua durability và có trace. Ma trận kiểm tra hiện có cho `single` đạt 62/62. Trước khi nộp cần bổ sung thông tin cá nhân và commit hash thật; đồng thời xác nhận commit đã được push lên repo nhóm.
