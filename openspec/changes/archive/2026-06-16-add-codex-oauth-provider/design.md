## Context

commit-with-ai 以 `BaseProvider` 抽象介面支援多 provider，現有兩種實作模式：
- **SDK 模式**（`GeminiProvider`）：讀環境變數金鑰，用 SDK 呼叫，缺金鑰即 `sys.exit(1)`。
- **Subprocess 模式**（`ClaudeCliProvider`）：呼叫外部 CLI，把驗證與憑證管理交給該 CLI。

使用 ChatGPT 訂閱的使用者多半已透過 `codex` 完成 OAuth 登入，其憑證存於 `~/.codex/auth.json`：
- `auth_mode`: `"chatgpt"`（訂閱登入）或 `"apikey"`。
- `tokens.access_token`: OAuth JWT，含 `exp`，會過期；JWT claim 內含 `chatgpt_account_id`。
- `tokens.account_id`: 呼叫後端時需帶的帳號識別。
- `tokens.refresh_token`、`last_refresh`、`OPENAI_API_KEY`（僅 apikey 模式有值）。

本變更要新增第三種 provider，重用 codex 的 OAuth 憑證。設計討論已確認走「直讀 auth.json + 過期報錯」路線（見 Decisions）。

## Goals / Non-Goals

**Goals:**

- 新增 `codex-oauth` provider，重用 codex 既有 OAuth access token 產生 5 筆 commit 訊息。
- 在 `auth_mode == "chatgpt"` 下，以 access token + account id 呼叫 OpenAI 後端的 Responses 端點並取得結構化輸出。
- access token 過期時給出可操作的錯誤訊息（請使用者重跑 codex），以非零碼結束。
- 沿用既有 provider 選擇機制，`--provider codex-oauth` 與 `COMMIT_AI_PROVIDER=codex-oauth` 皆可用。

**Non-Goals:**

- **不自行實作 OAuth 登入流程**（browser/PKCE/device code）。登入由 codex 負責。
- **不自動刷新 token、不寫回 `~/.codex/auth.json`**（拒絕 D2 方案，理由見 Decisions）。
- **不開 subprocess 呼叫 `codex`**（拒絕 A 方案）。
- **不在本變更支援 `auth_mode == "apikey"` 的公開 API 路徑**；偵測到非 chatgpt 模式時報錯，留待後續變更。
- 不修改 Gemini 或 Claude CLI provider 的行為。

## Decisions

### 直讀 ~/.codex/auth.json，不透過 subprocess 呼叫 codex

直接讀取 codex 寫在本機的 OAuth token 並自行發 HTTP 請求，而非 `subprocess` 呼叫 `codex exec`。

- **理由**：啟動較快、不依賴 codex 的 exec 輸出格式、不需解析其 CLI 輸出。
- **取捨**：需自行複製 codex 的後端請求邏輯（endpoint、header、account id），耦合到未公開介面；官方改動可能弄壞（見 Risks）。
- **Alternatives considered**：
  - *A. subprocess 呼叫 `codex exec`*：endpoint/刷新全交給 codex，程式碼少、耦合面穩；但啟動較慢且依賴 exec 輸出格式。使用者已明確選擇直讀方案。

### access token 過期時報錯提示，不自動刷新

decode access token（JWT）的 `exp` claim；若 `exp` 已過期，印出錯誤請使用者先執行一次 `codex` 讓其刷新登入，並 `sys.exit(1)`。

- **理由**：避免寫回 codex 擁有的共用檔案 `~/.codex/auth.json` 帶來的 race condition 與格式相容風險；沿用 Gemini provider「缺憑證即 exit」的既有錯誤模式，行為可預期。
- **取捨**：token 過期時使用者需手動重跑一次 codex，偶爾造成中斷。
- **Alternatives considered**：
  - *D2. 用 refresh_token 自動換新 token 並寫回 auth.json*：體驗較佳，但需安全寫回 codex 共用檔，承擔 race 與格式漂移風險，已拒絕。

### 透過 codex backend Responses 端點呼叫，並帶 chatgpt-account-id

在 `auth_mode == "chatgpt"` 下，以 `Authorization: Bearer <access_token>` 與 `chatgpt-account-id: <account_id>` header 呼叫 codex 使用的 OpenAI 後端 Responses 端點（base 形如 `https://chatgpt.com/backend-api/codex`，路徑 `/responses`）。

- **理由**：chatgpt 模式的 OAuth token 無法用於公開的 `api.openai.com`；必須走 codex 後端並帶帳號 header。
- **取捨**：此端點與請求格式未公開，須以 POC 驗證後再固定（見下一個決策與 Open Questions）。

### 以 POC 腳本先驗證實際後端請求格式

實作 provider 前，先寫 `scripts/poc_codex_oauth.py` 對著本機真實 token 驗證 endpoint、必要 header（如 `originator`、`session_id`）、可用 model 名稱與 Responses API 的結構化輸出格式。

- **理由**：端點未公開，先以一次性 POC 腳本對真實 token 驗證，把不確定性收斂在 POC 階段，再進入正式實作。

### 結構化輸出沿用既有 5 筆 commit schema

以 Responses API 的 `text.format`（`type: json_schema`）強制輸出 `messages` 陣列（恰 5 筆，每筆含 `type`/`scope`/`description`/`full_message`），重用 Gemini/Claude 兩 provider 的同一份 schema 形狀。

- **理由**：與既有 provider 介面契約一致，`display_menu` 等下游程式碼無需改動。

### 新增 httpx 為直接相依

把 `httpx` 從 google-genai 的間接相依提升為 `pyproject.toml` 的直接相依，用於發 HTTP 請求。

- **理由**：本 provider 直接使用 httpx，依賴關係應顯式宣告，避免 google-genai 改動間接相依時破壞本功能。

## Implementation Contract

**Behavior**：使用者執行 `commit-with-ai --provider codex-oauth`（已 staged 變更、且 codex 已登入且 token 未過期）時，工具讀取 `~/.codex/auth.json`，呼叫 OpenAI 後端，顯示 5 筆 conventional commit 選項供選取，行為與其他 provider 一致。

**Interface / data shape**：
- 新增 `CodexOAuthProvider(BaseProvider)`，`default_model` 為固定字串（POC 驗證後決定，例如 `gpt-5`），`generate_commit_messages(diff_content: str) -> list[dict[str, str]]` 回傳恰 5 筆，每筆含 `type`、`scope`、`description`、`full_message`。
- `__main__.py` 的 `VALID_PROVIDERS` 加入 `"codex-oauth"`；`get_provider()` 新增對應分支，回傳 `CodexOAuthProvider(model=...)`。
- 憑證讀取：解析 `~/.codex/auth.json` 取得 `tokens.access_token`、`tokens.account_id` 與 `auth_mode`。

**Failure modes（皆 surface 給使用者並以非零碼結束）**：
- `~/.codex/auth.json` 不存在或無法解析 → 提示使用者先安裝並登入 codex。
- `auth_mode != "chatgpt"`（或缺 `tokens.access_token`）→ 提示目前僅支援 codex 的 ChatGPT 登入模式。
- access token 的 `exp` 已過期 → 提示先執行一次 `codex` 讓其刷新登入。
- 後端回應非 2xx 或輸出無法解析為預期結構 → 顯示後端錯誤摘要。

**Acceptance criteria**：
- `tests/test_providers_codex_oauth.py` 以 mock 涵蓋：成功路徑（回 5 筆）、auth.json 缺失、auth_mode 非 chatgpt、token 過期、後端非 2xx。測試僅針對本專案程式碼（讀檔/過期判斷/錯誤分支/回應解析），不測 httpx 或 OpenAI 後端本身行為。
- `commit-with-ai --provider codex-oauth`（token 有效時）能在真實環境產生並提交一筆訊息（手動驗證）。
- `--provider unknown` 仍正確列出含 `codex-oauth` 的合法值。

**Scope boundaries**：
- In scope：新 provider 實作、provider 註冊、POC 腳本、單元測試、README 與 spec 更新、httpx 相依宣告。
- Out of scope：apikey 模式公開 API 路徑、自動刷新/寫回 auth.json、修改其他 provider。

## Risks / Trade-offs

- [codex 後端端點與請求格式未公開，官方改動可能使本 provider 失效] → 以 POC 腳本驗證後固定；錯誤訊息明確（顯示後端回應），便於日後快速定位；於 README 註明此為非官方介面。
- [`~/.codex/auth.json` 路徑或欄位結構未來可能變動] → 集中於單一讀取函式解析，欄位缺失時給明確錯誤而非靜默失敗。
- [token 過期造成中斷] → 已知取捨（D1），錯誤訊息提供可操作的修復步驟（重跑 codex）。
- [可用 model 名稱可能受後端限制] → POC 階段確認；`default_model` 取 POC 驗證過的安全值，並允許 `--model` 覆寫。

## Open Questions

以下由 `scripts/poc_codex_oauth.py` 對本機真實 token 驗證後固定（POC 於 2026-06-16 通過）：

- **端點**：base URL `https://chatgpt.com/backend-api/codex`、路徑 `/responses`（即 `POST https://chatgpt.com/backend-api/codex/responses`）。
- **必要 header**：`Authorization: Bearer <access_token>`、`chatgpt-account-id: <account_id>`、`OpenAI-Beta: responses=experimental`、`originator: codex_cli_rs`、`session_id: <uuid>`、`Content-Type: application/json`、`Accept: text/event-stream`。
- **request body**：Responses API 形式 — `model`、`instructions`、`input`（`role: user` + `content[].type: input_text`）、`stream: true`、`store: false`、`text.format`（`type: json_schema`、`name`、`strict: true`、`schema`）。
- **可用 model 與 default_model**：chatgpt 模式拒絕 `gpt-5` / `gpt-5-codex`（回 400「model is not supported when using Codex with a ChatGPT account」）；codex `models_cache.json` 列出 `gpt-5.5`、`gpt-5.4`、`gpt-5.4-mini`、`codex-auto-review`。`gpt-5.5`/`gpt-5.4`/`gpt-5.4-mini` 皆驗證可用且回 5 筆。`default_model` 取 **`gpt-5.4-mini`**（最快、約 3.2s，足以產生 commit 訊息）。
- **輸出解析**：後端以 SSE 串流回應。因 `store: false`，`response.completed` 事件的 `output` 為空陣列；正解為累積 `response.output_text.delta` 的 `delta`，或讀取 `response.output_text.done` 事件的 `text`（完整 JSON 字串），再 `json.loads` 取 `messages`。
- **account id 來源**：以 `tokens.account_id` 為準，POC 帶此值呼叫成功，無需調整 spec。
