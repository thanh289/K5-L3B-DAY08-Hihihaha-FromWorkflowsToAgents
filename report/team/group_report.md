# Báo cáo nhóm — Lab 8 LogiX-VN

## 1. Thông tin nhóm

- Tên nhóm: Hihihaha (theo tên repository; cần xác nhận trong [TEAM.md](../../TEAM.md)).
- Lớp: cần xác nhận; tên repository ghi L3B, bản mẫu [TEAM.md](../../TEAM.md) ghi L3A.
- Thành viên và phân công: xem [TEAM.md](../../TEAM.md).
- Shape đề xuất cho cổng hidden: `single`; số liệu và giới hạn của quyết định xem [decision_adr.md](decision_adr.md).

## 2. Mục tiêu và cách tiếp cận

Lab mô phỏng xử lý khiếu nại bồi thường của LogiX-VN. Hệ thống phải đọc dữ kiện đơn hàng và chính sách, tính bồi thường bằng công cụ tin cậy, xin phê duyệt khi cần, ghi sổ an toàn và tránh lộ dữ liệu nhạy cảm. Nhóm triển khai ba kiến trúc `workflow`, `single`, `orchestrator`; `swarm` là mốc tham chiếu có sẵn. Mỗi thành viên ban đầu tự giải toàn bộ lab, sau đó nhóm tích hợp ba shape được đẩy lên repository và đánh giá trên cùng bộ public trước khi chốt kiến trúc.

Các phép đo dùng 14 claim public × 5 seed (11, 22, 33, 44, 55), cùng `MockLLM`, world, bảng giá và evaluator. Chúng tôi so kết quả lặp lại thay vì chọn một trace thuận lợi. `steps` trong benchmark là số event trace, không phải thời gian chạy hoặc số lệnh tool thực tế.

## 3. Giải pháp

| Shape | Luồng xử lý và ranh giới tin cậy |
| --- | --- |
| `workflow` | Luồng cố định đọc claim và đơn hàng, gọi `compute_compensation`, rồi chuyển nguyên quote sang host `issue_refund`. `MockLLM` chỉ soạn lời đáp. Trace lưu dữ kiện đơn hàng đã lọc, quote, kết quả host và quyết định. |
| `single` | Một agent chạy `run_react(max_steps=8)` để lựa chọn các công cụ đọc, sau đó tính quote và gọi host ghi sổ. Model chỉ soạn lời đáp; code/tool/host giữ quyền quyết định số tiền và phê duyệt. Trace lưu claim và order view có chọn lọc, quote và quyết định. |
| `orchestrator` | Điều phối viên tạo handoff giới hạn `facts` và `allowed_tools`, gọi các investigator chỉ đọc, nhận quote rồi gọi host `issue_refund`. Model tạo plan và lời đáp. Trace lưu handoff đã lọc, dữ kiện cần thiết, quote và quyết định. |
| `swarm` | Shape tham chiếu để đối chứng|

Ở cả ba shape nhóm viết, đường ghi sổ đi qua host và quote do tool tính, bao gồm trường hợp T13/T14 liên quan phê duyệt hoặc crash. Các field nhạy cảm như số điện thoại, địa chỉ và ghi chú nội bộ không cần cho quyết định và không được đưa vào trace công khai. Chi tiết ranh giới code/model nằm ở [architecture.md](../../docs/architecture.md).

## 4. Kết quả kiểm thử và benchmark

Lệnh thực thi từ [src/](../../src/): `python -m pytest -q` → **77 passed, 250 deselected** (chạy lại sau khi nhận `student_drop`); `python -m pytest -q -m student -o addopts=` → **250 passed, 76 deselected** ở lần chạy trước khi thêm test ablation. `python -m lab8.crash_test --count 20 --out reports/crash.json` → **20/20** crash-safe theo [crash.json](../../src/reports/crash.json). 

Benchmark: `python -m lab8.benchmark --shapes workflow,single,orchestrator,swarm --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/benchmark.json`. Số liệu đầy đủ ở [benchmark.json](../../src/reports/benchmark.json).

| Shape | Pass rate | Pass^5 | Seed min–max | Variance | Cost/success (VND mô phỏng) | Mean/p95 steps |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| workflow | 70/70 = 1.000 | 1.000 | 1.000–1.000 | 0 | 28.87 | 5.07/6 |
| single | 70/70 = 1.000 | 1.000 | 1.000–1.000 | 0 | 28.77 | 3.79/4 |
| orchestrator | 70/70 = 1.000 | 1.000 | 1.000–1.000 | 0 | 57.25 | 2.79/3 |
| swarm | 69/70 = 0.986 | 0.929 | 0.929–1.000 | 0.000816 | 49.57 | 2.80/3 |

Ba shape nhóm viết đều đạt 70/70 public trial. `single` có cost/success thấp nhất trong lần đo này, hơn `workflow` khoảng 0.10 VND mô phỏng; chênh lệch nhỏ nên không đủ để khẳng định ưu thế ngoài public corpus. `orchestrator` có ít event trace hơn nhưng tốn khoảng gấp đôi `single`; số event ít không đồng nghĩa độ trễ thấp. `swarm` trượt C-002 ở seed 55. Lý do đề xuất `single` và điều kiện đổi quyết định ghi ở [decision_adr.md](decision_adr.md).

Sau khi nhận `student_drop`, kết quả [hidden_selfcheck.json](../../src/reports/hidden_selfcheck.json) ghi **40 claim × 5 seed = 200 trial/shape**. Mỗi shape có **0 trial lỗi**, **200/200 trace đúng contract** (`reason=unlabeled`) và **0 `leak_suspect`** theo bộ dò canary của self-check. Cả ba cho cùng phân bố trạng thái: 95 `denied`, 90 `resolved`, 5 `needs_info`, 10 `escalated`. Bộ này không chứa nhãn đáp án: `graded_trials=0`, nên không thể tính pass rate, pass^5, approval bypass hoặc khẳng định đã qua ngưỡng hidden 0.75. Kết quả tự kiểm chỉ củng cố rằng ba shape chạy hết pack, giữ trace hợp lệ và không lộ canary qua phép dò hiện có.

## 5. Khó khăn, xử lý và thí nghiệm nghiên cứu

Đối với C-002 seed 55, `swarm` tham chiếu dùng số ngày trễ trong ticket (5) lấn át dữ kiện đơn hàng có cấu trúc (2), dẫn đến fail. Theo câu hỏi R2 về lỗi kiểm chứng trong bài MAST, chúng tôi tạo một ablation chỉ tắt phép ghi đè ngày trễ đó. Trên cùng 70 trial, biến thể đạt 70/70; chỉ C-002 seed 55 đổi từ fail sang pass, số model call giữ nguyên. Công cụ đọc gọi có điều kiện giảm từ 6 còn 5 ở trial này. Mã thí nghiệm và bằng chứng nằm ở [swarm_verified.py](../../src/bonus/swarm_verified.py), [test_ablation_swarm_verified.py](../../src/tests/test_ablation_swarm_verified.py), [ablation_swarm_verified.json](../../src/reports/ablation_swarm_verified.json) và [research_card.md](research_card.md). Đây là sửa một lỗi kiểm chứng cụ thể của shape đối chứng, không phải phép chứng minh mọi kiến trúc multi-agent đều kém hơn.

## 6. Tổng hợp đóng góp

 Bảng tên người, MSSV, vai trò và test của từng thành viên trong [TEAM.md](../../TEAM.md). 

## 7. Hạn chế và hướng cải thiện

`MockLLM`, 14 claim public và chi phí mô phỏng không đại diện đầy đủ cho model thực tế, ticket ngoài phân phối hoặc tải production. `student_drop` không có nhãn, nên kết quả đúng/sai hidden chỉ được biết qua grader chính thức. Latency hiện là `unavailable`; không được suy ra từ `steps`. Cần mở rộng claim có xung đột giữa ticket và dữ kiện cấu trúc, và so kết quả nhiều lần nếu đổi model, prompt hoặc giá tool.

## 8. Tài liệu tham khảo

- [architecture.md](../../docs/architecture.md), [SUBMISSION.md](../../SUBMISSION.md) và các file kết quả trong [src/reports/](../../src/reports/).
- Cemri et al., *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025, [bản công bố chính thức](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html).
