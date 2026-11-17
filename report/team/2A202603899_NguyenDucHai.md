# Báo cáo cá nhân — 2A202603899_NguyenDucHai

## 1. Thông tin thành viên

- Họ tên: Nguyễn Đức Hải
- MSSV: 2A202603899
- Email: 26ai.haind4@vinuni.edu.vn
- GitHub: hainguyen312

## 2. Phần việc phụ trách

- Shape A — `workflow` (`src/lab8/shapes/workflow.py`): shape nhóm chọn để chấm hidden (`- Shape chọn: workflow` trong `report/team/decision_adr.md`).
- Test của shape workflow: `src/tests/test_team_workflow.py`.

## 3. Đóng góp cụ thể

**Commit chính:** `69c664b` — `feat: workflow shape + tests` (nhánh `hainguyen`), gồm `src/lab8/shapes/workflow.py` (+174 / −6) và `src/tests/test_team_workflow.py` (+92).

**Workflow làm gì** (8 bước theo docstring, đường đi cố định, thuần code):

1. Đọc claim bằng `get_claim_view` (không `SELECT *`, không chạm `parent_secret`).
2. Thiếu `order_id` → `needs_info`; không lấy mã đơn từ chữ trong ticket.
3. `lookup_order` theo principal của claim; không thấy hoặc không sở hữu → `escalated`.
4. Quote bằng `compute_compensation` từ order row và policy hiện hành; bỏ qua số ngày ghi trong ticket.
5. Quote = 0 → `denied`, proposal 0, không gọi host.
6. Quote > 0 → `durability.issue_refund(conn, claim_id, <quote đầy đủ>, crash_at=crash_at)`.
7. Host chấp nhận → `resolved`; host từ chối → `denied` (host ghi `policy_denied`); conflict → `failed`. `proposal_amount` luôn là quote đầy đủ.
8. MockLLM chỉ được gọi một lần (`draft`) để soạn chữ trả lời; prompt chỉ có status và proposal.

**Quyết định kỹ thuật tôi đưa ra cho workflow:**

- `workflow.py` **tự đủ**: không import từ shape khác, không thêm helper vào `common.py`, vì grader hidden chỉ lấy ba file shape và `src/bonus/`, còn `common.py` sẽ bị thay bằng bản chính thức. Phần sau quote nằm trong `_settle` riêng của file.
- **Lớp bắt lỗi** trong `run_claim`: `except InjectedCrash` → ghi event `crash`, `trace.write()`, rồi raise lại (T12, crash suite); `except Exception` → trả `failed` qua `finish()` với `error_reason = internal_error:<TênLỗi>`, **không ghi** `str(e)` vào trace; không bắt `BaseException`.
- Yêu cầu test **monkeypatch ép lỗi** trong `lookup_order` để chứng minh lớp bắt lỗi không làm lộ secret.

**Test đã thêm** (`src/tests/test_team_workflow.py`, 22 test, chạy trong cổng host mặc định):

| Test | Kiểm gì |
| --- | --- |
| `test_internal_error_returns_failed_with_clean_trace` | Ép `lookup_order` ném lỗi có chứa `CANARY_SECRET_PARENT_C-001` → `failed`, `internal_error:RuntimeError`, trace hợp lệ, CANARY không lộ |
| `test_trace_has_no_ticket_secret_or_pii` (×14 claim) | Trace + kết quả không chứa canary, `parent_secret`, ticket, SĐT, địa chỉ, ghi chú nội bộ, tên hàng |
| `test_ignores_ticket_delay_on_every_seed` (×5 seed) | C-002 (ticket "trễ 5 ngày", order 2 ngày) luôn `denied`, kể cả seed 55 |
| `test_unknown_claim_fails_without_raising` | Claim không tồn tại → `failed`, không ném exception |
| `test_crash_before_effect_then_resume_pays_once` | Crash `before_effect` rồi resume → đúng 1 dòng ledger 35000, 1 audit |

## 4. Bằng chứng

- Kiểm nội dung commit `69c664b` trong một worktree sạch (chỉ có nội dung commit, không có file chưa commit; kiểm trên bản trước khi sửa message, cùng tree `517adcc`): `python -m pytest -q` → **76 passed**; `python -m pytest -q -m student -o addopts= -k workflow` → **62 passed**.
- Số của workflow trong benchmark public (`src/reports/benchmark.json` do người tích hợp chạy và commit; 14 claim × seed `11,22,33,44,55`): pass rate 1.000, pass^5 1.000, variance 0.000000, cost/success 28.87 VND (mô phỏng), mean / p95 steps 5.07 / 6.
- Run id: `R-workflow-C-002-s55` pass, trong khi `R-swarm-C-002-s55` fail (`status resolved != denied`) vì swarm tin số ngày trong ticket.
- Rà trace: 0 hit khi quét `src/traces/R-workflow-*` với các chuỗi `CANARY_SECRET`, `parent_secret`, `raw_headers`, SĐT, địa chỉ, ghi chú nội bộ, tên hàng và nguyên văn ticket.

**Giải thích để trả lời người chấm:**

- *Vì sao truyền quote đầy đủ vào* `issue_refund`*:* trần hoàn tiền tính theo đơn, và host là nơi duy nhất đọc tổng đã hoàn của đơn ngay trong transaction ghi. Nếu shape tự trừ trước thì host trừ thêm lần nữa: ở T14, quote 150.000, đã hoàn 30.000, host trả đúng 120.000; nếu shape truyền 120.000 thì host chỉ trả 90.000. `proposal_amount` theo contract cũng phải là quote.
- *Trace cố ý không ghi gì:* ticket (chữ người dùng, có thể chứa injection/PII, không dùng cho quyết định), claim row thô (`parent_secret`, `raw_headers_json`), order row thô (SĐT, địa chỉ, ghi chú nội bộ, tên hàng — chỉ ghi 7 field allowlist của `lookup_order`), `str(exc)`, prompt/output của MockLLM. Shape không ghi file nào khác và không in ra stdout, nên mọi đầu ra đều nằm trong chỗ grader quét được.
- *Vì sao checkpoint đơn lẻ không thay được ledger* (`python -m lab8.demo.buggy_workflow` → 2 dòng): checkpoint là lần ghi tách rời với lần ghi tiền; crash ở giữa làm checkpoint báo "chưa làm" dù tiền đã đi. Host dùng khóa `refund:{claim_id}` trên chính dòng tiền, ghi dòng refund và audit `refund_committed` trong một transaction, và khi chạy lại thì hỏi ledger chứ không hỏi checkpoint.

## 5. Công cụ AI đã dùng

- **Claude Code (Claude Opus 5.5)**, chạy trong terminal trên repo nhóm.
- Dùng vào việc: đọc contract và code host liên quan tới workflow; đề xuất kế hoạch cài workflow, chạy test và rà trace của workflow
- Tôi tự kiểm tra bằng cách: đọc diff trước khi commit; yêu cầu báo kết quả test bằng số thật; chạy lại cổng host và ma trận `-k workflow`; kiểm commit trong một worktree sạch để chắc commit không phụ thuộc file chưa commit; đối chiếu số trong báo cáo với `src/reports/benchmark.json`.
- Tôi đã đặt quy tắc cho trợ lý trong `CLAUDE.md`: không sửa file thước đo, không sửa tay JSON trong `src/reports/`, không bịa số liệu/run id/commit, không gọi model thật.
- Không dùng AI để viết phần tự đánh giá ở mục 6.

## 6. Tự đánh giá

Thực hành được kiến thức đã học trên bài giảng về workflow to agent, hiểu được cách một hệ thống thực tế vận hành. Điều tôi hiểu rõ nhất là luồng mà hệ thống cần đi qua, và việc dùng rule cứng để kiểm tra những route quan trọng.
