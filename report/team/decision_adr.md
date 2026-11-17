# Decision record

- Shape chọn: single
- Commit hash: bf683e3
- Run id dẫn chứng: R-single-C-001-s11 (một trial trong `src/reports/benchmark.json`; toàn bảng gồm 70 trial/shape)
- Pass rate / pass^5 / seed min-max / variance: 70/70 = 1.000 / 1.000 / 1.000–1.000 / 0
- Cost per success (mô phỏng, VND): 28.77
- Crash safety: 20/20 (`src/reports/crash.json`, suite crash trên đường host/durability)
- Secret leak / approval bypass: `student_drop` self-check: 0/200 `leak_suspect` cho `single`

## Vì sao chọn shape này

Trên cùng 14 claim public và 5 seed, `single` và `workflow` cùng đạt 70/70, pass^5 = 1 và variance = 0. `single` có cost/success 28.77 VND mô phỏng so với 28.87 của `workflow`, 57.25 của `orchestrator` và 49.57 của `swarm`. Số model call trung bình của `single` là 1 và tool call trung bình là 2.79. Chênh lệch 0.10 VND so với `workflow` rất nhỏ, nhưng `single` giữ ranh giới ghi sổ ở host và vẫn qua mọi trial public, nên nhóm đề xuất shape này. Bằng chứng gốc nằm trong [benchmark.json](../../src/reports/benchmark.json); [group_report.md](group_report.md) trình bày toàn bảng.

## Có đáng đổi lấy multi-agent không

Kết quả public chưa cho thấy tăng pass rate khi dùng `orchestrator` hoặc `swarm`. `orchestrator` tăng cost/success gần gấp đôi `single`; `swarm` trượt một trial và có variance lớn hơn 0. Do đó chưa có lợi ích đo được để trả thêm chi phí điều phối trong lab này. Quyết định sẽ được xem lại nếu hidden hoặc bộ claim mở rộng cho thấy `single` kém đáng kể về pass rate, an toàn, hoặc nếu investigator song song giải quyết được trường hợp phức tạp mà code hiện tại không giải được. Không dùng `steps` làm đại diện cho latency vì benchmark chỉ đếm event trace và báo latency `unavailable`.

## Trace và bằng chứng an toàn

`single` ghi claim view đã lọc, order view có chọn lọc, quote và decision vào trace. Code không đưa `parent_secret`, header, số điện thoại, địa chỉ, ghi chú nội bộ hay tên hàng vào payload trace. Kiểm tra trực tiếp các trace public sinh sau benchmark không tìm thấy giá trị PII tương ứng trong public world hoặc canary; [test_handoff_secret.py](../../src/tests/test_handoff_secret.py), [test_authorization.py](../../src/tests/test_authorization.py) và [test_order_cap_and_approval_binding.py](../../src/tests/test_order_cap_and_approval_binding.py) đều qua trong suite. Host `issue_refund` kiểm tra approval và ghi sổ; [crash.json](../../src/reports/crash.json) cho thấy 20/20 kịch bản crash an toàn, gồm retry thiếu approval và xung đột số tiền. Phép quét trace công khai chỉ giới hạn ở trace đã tạo và các giá trị đã biết; không chứng minh an toàn cho mọi đầu vào hidden.

## Giới hạn

`MockLLM` cố định theo seed và chi phí là mô phỏng. Bộ public có 14 claim. [hidden_selfcheck.json](../../src/reports/hidden_selfcheck.json) cho thấy `single` chạy đủ 200/200 trial không lỗi, trace hợp lệ và không có `leak_suspect`; nhưng `student_drop` không có nhãn nên chưa thể xác nhận pass rate hidden hoặc approval bypass. Khi đổi model, prompt, giá tool hoặc corpus cần chạy lại cùng benchmark trước khi giữ quyết định này.
