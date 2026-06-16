## Why

目前 commit-with-ai 只支援 Gemini（API key）與 Claude CLI（subprocess）兩種 provider，使用 ChatGPT 訂閱（codex）登入的使用者無法直接使用。許多開發者已透過 `codex` 完成 OAuth 登入，其 access token 就存在本機 `~/.codex/auth.json`，可直接重用來呼叫 OpenAI 後端，省去額外申請 API key 或設定環境變數的步驟。

## What Changes

- 新增 `codex-oauth` provider：直接讀取 `~/.codex/auth.json` 內 codex 已登入的 OAuth access token，呼叫 OpenAI 後端產生 5 筆 conventional commit 訊息。
- 不開 subprocess、不自行實作 OAuth 登入流程：token 的取得與刷新責任完全留在 codex；本工具只「讀取並使用」既有 token。
- access token 過期處理採「報錯提示」策略：偵測 JWT `exp` 已過期時，印出清楚錯誤訊息請使用者先執行一次 `codex` 讓其刷新登入，並以非零碼結束（沿用 Gemini provider「缺憑證即 exit」的既有錯誤模式）。
- 在 provider 選擇機制中註冊新值：`--provider codex-oauth` 與 `COMMIT_AI_PROVIDER=codex-oauth` 皆可選用。
- 沿用既有 model 覆寫機制：`codex-oauth` 提供一個 POC 驗證過的 `default_model`，並接受 `--model` 與 `COMMIT_AI_MODEL` 覆寫。
- 新增 HTTP 相依（`httpx`）至 `pyproject.toml`（目前僅為 google-genai 的間接相依，需提升為直接相依）。

## Non-Goals (optional)

<!-- design.md 將建立，Non-Goals 移至 design.md 的 Goals/Non-Goals 區段 -->

## Capabilities

### New Capabilities

- `codex-oauth-provider`: 透過讀取 codex 本機 OAuth 憑證（`~/.codex/auth.json`）呼叫 OpenAI 後端產生 commit 訊息的 provider，包含憑證讀取、過期偵測、後端呼叫與結構化輸出解析。

### Modified Capabilities

- `provider-system`: provider 選擇的合法值集合新增 `codex-oauth`（`--provider` 與 `COMMIT_AI_PROVIDER` 兩條選擇路徑皆受影響）。

## Impact

- Affected specs:
  - New: `codex-oauth-provider`
  - Modified: `provider-system`
- Affected code:
  - New:
    - commit_with_ai/providers/codex_oauth.py
    - tests/test_providers_codex_oauth.py
    - scripts/poc_codex_oauth.py
  - Modified:
    - commit_with_ai/__main__.py
    - pyproject.toml
    - README.md
  - Removed: (none)
- Dependencies: 新增直接相依 `httpx`
