## 1. 前置驗證與相依

- [x] 1.1 [P] 依「以 POC 腳本先驗證實際後端請求格式」決策，撰寫 `scripts/poc_codex_oauth.py`，對本機真實 token 驗證 codex backend Responses 端點 base URL/路徑、必要 header、可用 model 名稱與 json_schema 結構化輸出格式。驗證：手動執行 `uv run scripts/poc_codex_oauth.py` 能回傳含 5 筆 messages 的結構化輸出，並把確認後的端點/header/model 記錄於 design.md 的 Open Questions。
- [x] 1.2 [P] 依「新增 httpx 為直接相依」決策，將 `httpx` 加入 `pyproject.toml` 的 `dependencies`。驗證：`uv sync` 成功且 `uv run python -c "import httpx"` 無誤。

## 2. Provider 實作

- [x] 2.1 依「直讀 ~/.codex/auth.json，不透過 subprocess 呼叫 codex」決策，在 `commit_with_ai/providers/codex_oauth.py` 新增 `CodexOAuthProvider(BaseProvider)` 骨架（`default_model` 先以暫定值，最終值由 task 2.6 依 POC 結果固定），`__init__(self, model: str | None = None)` MUST 採 `self.model = model or self.default_model`（對齊 `GeminiProvider`/`ClaudeCliProvider`），以容忍 `__main__.py` main() 先以 `model=""` 建構再回填的流程。並實作 Codex OAuth credential reading：讀取 `~/.codex/auth.json` 取出 `tokens.access_token`、`tokens.account_id`、`auth_mode`，檔案缺失或無法解析時 `sys.exit(1)` 並印可操作錯誤。驗證：`tests/test_providers_codex_oauth.py` 斷言 `CodexOAuthProvider(model="").model == default_model`，且 credential reading 與檔案缺失/格式錯誤分支測試通過。
- [x] 2.2 實作 ChatGPT auth mode requirement：`auth_mode != "chatgpt"` 時 `sys.exit(1)` 並提示僅支援 codex ChatGPT 登入模式。驗證：auth_mode 為 apikey 的測試案例導致非零結束碼。
- [x] 2.3 依「access token 過期時報錯提示，不自動刷新」決策，實作 Access token expiry detection：decode JWT 的 `exp` claim，過期時印出「請重跑 codex 刷新登入」並 `sys.exit(1)`，且不寫回 `~/.codex/auth.json`。驗證：過期 token 測試案例導致非零結束碼且未觸發檔案寫入。
- [x] 2.4 依「透過 codex backend Responses 端點呼叫，並帶 chatgpt-account-id」決策，實作 Commit message generation via codex backend：以 `httpx` 帶 `Authorization: Bearer <access_token>` 與 `chatgpt-account-id` header 呼叫 Responses 端點送出 diff，非 2xx 或無法解析回應時 surface 後端錯誤並 `sys.exit(1)`。驗證：mock 成功路徑回 5 筆、mock 非 2xx 路徑非零結束的測試通過。
- [x] 2.5 依「結構化輸出沿用既有 5 筆 commit schema」決策，實作 Structured output with exactly five messages：以 json_schema 強制 `messages` 恰 5 筆（含 `type`/`scope`/`description`/`full_message`），`generate_commit_messages` 回傳解析後的 5 筆 list。驗證：成功路徑測試斷言回傳長度為 5 且欄位齊全。
- [x] 2.6 實作 Model selection with default：將 task 2.1 的暫定 `default_model` 換為 task 1.1 POC 記錄於 design.md Open Questions 的安全值，並透過既有機制接受 `--model` / `COMMIT_AI_MODEL` 覆寫。驗證：以自訂 model 建構 provider 時請求使用該 model 的測試通過。

## 3. Provider 註冊

- [x] 3.1 實作 Provider selection via CLI flag 的擴充：在 `commit_with_ai/__main__.py` 的 `VALID_PROVIDERS` 加入 `"codex-oauth"`（argparse `choices` 自動隨之擴充），並於 `get_provider()` 新增回傳 `CodexOAuthProvider` 的分支。驗證：`tests/test_cli.py` 斷言 `parse_args(["--provider", "codex-oauth"])` 成功（choices 接受新值）；另測 `get_provider("unknown", "")` 走入未知 provider 分支時錯誤訊息含 `codex-oauth`（此分支經 `COMMIT_AI_PROVIDER` 等非 `--provider` 路徑觸發，因 argparse `choices` 會先攔截 `--provider unknown`）。

## 4. 文件

- [x] 4.1 更新 `README.md`：新增 `codex-oauth` provider 的使用說明、前置條件（需先安裝並登入 codex）、token 過期需重跑 codex，並註明此走 codex 非官方後端介面。驗證：內容審查確認上述四點皆已記載。
- [x] 4.2 更新 `pyproject.toml` 的封裝中介資料以與新 provider 一致：`description` 與 `keywords` 納入 OpenAI/codex。驗證：內容審查確認 `description`／`keywords` 已提及 codex/openai（版本號交由既有發版流程處理，不在本變更調整）。
