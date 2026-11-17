# Báo cáo cá nhân — người phụ trách kiểm thử và báo cáo


## 1. Thông tin thành viên

- Họ tên: **Trần Duy Thành**
- MSSV: **2A202603919**
- Email: **26ai.thanhtd2@vinuni.edu.vn**
- GitHub: **`thanh289`**
- Nhóm/lớp: Hihihaha / L3B 

## 2. Phần việc phụ trách

Tích hợp ba shape do các thành viên đẩy lên `main`; chạy bộ test tự động, benchmark bốn shape và crash suite; kiểm tra trace public; phân tích lỗi trial của `swarm` tham chiếu; thực hiện ablation; tổng hợp báo cáo nhóm, decision record và research card.

## 3. Đóng góp cụ thể

1. Cập nhật checkout đến `origin/main` để có đủ `workflow`, `single` và `orchestrator` trước khi đo.
2. Chạy `pytest` mặc định (76 passed trước khi thêm test; 77 passed sau khi thêm test), bộ `student` (250 passed), benchmark 14 claim × 5 seed và crash suite 20/20. Kết quả được lưu ở [benchmark.json](../../src/reports/benchmark.json) và [crash.json](../../src/reports/crash.json)
3. Phát hiện `swarm` tham chiếu fail C-002 seed 55: ticket ghi 5 ngày trễ, order ghi 2. Viết [swarm_verified.py](../../src/bonus/swarm_verified.py) để thử giả thuyết tắt phép ghi đè này, thêm [test_ablation_swarm_verified.py](../../src/tests/test_ablation_swarm_verified.py), chạy [ablation_swarm_verified.json](../../src/reports/ablation_swarm_verified.json). Biến thể cải thiện 69/70 lên 70/70 public trial; chỉ C-002 seed 55 đổi kết quả.


## 4. Bằng chứng

- `python -m pytest -q`: 77 passed, 250 deselected sau khi thêm test ablation.
- `python -m pytest -q -m student -o addopts=`: 250 passed, 76 deselected trước khi thêm test ablation (test mới không mang marker `student`).
- `python -m lab8.crash_test --count 20 --out reports/crash.json`: 20/20.
- `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`: `single`, `workflow`, `orchestrator` đều 70/70; `swarm` 69/70. Run id mẫu của shape đề xuất: `R-single-C-001-s11`.
- `python -m lab8.benchmark --extra-shape swarm_verified=bonus.swarm_verified:run_claim --shapes swarm,swarm_verified --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_swarm_verified.json`: biến thể 70/70. Các tham số cố định và giới hạn được ghi ở [research_card.md](research_card.md).
- Kiểm tra trace public sau benchmark: không thấy các giá trị PII từ public world hoặc canary trong trace sinh ra. Chưa có dữ liệu hidden để tự kiểm.

## 5. Công cụ AI đã dùng

- Dùng Codex để hỗ trợ đọc yêu cầu, tổ chức phép đo, viết mã ablation/test và soạn báo cáo.

## 6. Tự đánh giá

Phần tích hợp và đánh giá public đã có bằng chứng có thể chạy lại. Việc chọn `single` mới là đề xuất dựa trên bộ public; cần xác nhận shape nộp và bổ sung kết quả hidden nếu có.
