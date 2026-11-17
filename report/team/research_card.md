# Research card — R2: lỗi kiểm chứng dữ kiện

Nhóm chọn câu R2 trong [bonus_topics.md](../../docs/bonus_topics.md) và thực hiện một ablation trên `swarm` tham chiếu. Bài nghiên cứu cung cấp khung phân loại lỗi; nhận định về trial của LogiX-VN bên dưới là suy luận của nhóm từ trace và mã lab.

| Câu | Nguồn (thư viện tham khảo, slide 68–69) | Câu hỏi gợi ý cho lab |
| --- | --- | --- |
| R1 · Scaling | Google Research 2026, *Towards a Science of Scaling Agent Systems* | Task claims chủ yếu tuần tự hay song song được? Dự đoán thêm investigator sẽ làm pass rate và cost/success thay đổi thế nào. |
| R2 · Failure taxonomy | MAST, NeurIPS 2025, *Why Do Multi-Agent LLM Systems Fail?* | Các trial fail của swarm (seed 55) thuộc nhóm nào: lỗi giao việc, lệch mục tiêu, hay lỗi kiểm chứng? |
| R3 · Architecture choices | AgentArch, AACL 2026 | Nếu đổi topology mà giữ nguyên mọi thứ khác, biến nào phải cố định để kết luận còn đúng? |
| R4 · Evaluation confounders | EMNLP 2026, *Rethinking Evaluation of MAS Efficiency* | Làm sao chứng minh chênh lệch giữa A/B/C/D là do topology, không phải do prompt, tool hay seed? |

## Phiếu của nhóm

| Field | Hướng dẫn | Nhóm điền |
| --- | --- | --- |
| CÂU | R1 / R2 / R3 / R4 | R2 · Failure taxonomy |
| SOURCE | Paper/blog, năm, URL, loại bằng chứng | Cemri et al., *Why Do Multi-Agent LLM Systems Fail?*, NeurIPS 2025, [paper chính thức](https://proceedings.neurips.cc/paper_files/paper/2025/hash/b1041e52d3be19f0a9bc491657488e4a-Abstract-Datasets_and_Benchmarks_Track.html); phân tích MAST-Data với hơn 1.600 trace của 7 hệ multi-agent. |
| CLAIM | Một kết luận gốc của nguồn | MAST phân loại 14 kiểu thất bại vào ba nhóm: thiết kế hệ thống, sai lệch giữa các agent, và kiểm chứng tác vụ. Trong nhóm cuối có thiếu kiểm chứng và kiểm chứng sai. |
| BOUNDARY | Model / dataset / setup giới hạn kết luận | Corpus và hệ multi-agent trong paper không phải `MockLLM` hay LogiX-VN. Gán C-002 seed 55 vào lỗi kiểm chứng là suy luận riêng dựa trên xung đột ticket và order, không phải kết quả trực tiếp của paper. |
| HYPOTHESIS | Hướng thay đổi metric và khoảng dự kiến | Nếu bỏ phép ghi đè `delay_days` từ ticket trong `swarm` tham chiếu, C-002 seed 55 sẽ pass; pass rate public tăng từ 69/70 lên 70/70 (+1,43 điểm phần trăm), pass^5 lên 1, variance về 0; model calls không đổi. |
| METHOD | Biến cố định và biến thay đổi | Cố định `MockLLM`, cùng danh sách tool, seed 11/22/33/44/55, 14 claim public, bảng giá, evaluator và mã `swarm` tham chiếu. Biến duy nhất: chặn hàm đọc số ngày trễ từ ticket trong [swarm_verified.py](../../src/bonus/swarm_verified.py), làm nguồn order có cấu trúc quyết định ngày trễ. |
| FAILURE / METRIC | Lỗi và cách đo | Lỗi mục tiêu: C-002 seed 55 fail do ticket ghi 5 ngày trong khi order ghi 2 ngày. Đo pass rate, pass^5, variance, cost/success và đối chiếu từng cặp `(claim_id, seed)` trong [ablation_swarm_verified.json](../../src/reports/ablation_swarm_verified.json). |

## Kết quả ablation

- Lệnh đã chạy từ [src/](../../src/): `python -m lab8.benchmark --extra-shape swarm_verified=bonus.swarm_verified:run_claim --shapes swarm,swarm_verified --cases data/public_claims.jsonl --seeds 11,22,33,44,55 --out reports/ablation_swarm_verified.json`.
- Bằng chứng: [ablation_swarm_verified.json](../../src/reports/ablation_swarm_verified.json); test tập trung [test_ablation_swarm_verified.py](../../src/tests/test_ablation_swarm_verified.py) qua 1/1.
- Kết quả phù hợp giả thuyết: `swarm` 69/70, pass^5 0,929, variance 0,000816, cost/success 49,57 VND; `swarm_verified` 70/70, pass^5 1, variance 0, cost/success 48,72 VND. Chỉ cặp C-002 seed 55 thay đổi kết quả. Model calls ở cặp đó đều là 3; tool calls giảm từ 6 xuống 5 như hệ quả của nhánh điều kiện không còn chạy.
- Giới hạn: can thiệp này sửa logic diễn giải dữ kiện của một shape, không cô lập tác động của topology. `MockLLM` và corpus public không đại diện production; latency `unavailable`. Kết quả trên một trial bị lỗi không chứng minh biến thể tốt hơn trên mọi bộ dữ liệu.
