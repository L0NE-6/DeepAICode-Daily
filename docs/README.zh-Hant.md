<div align="center">

# 🧠 DeepAI Code Daily

**每日 Theos 免費額度 · 多帳號 · 單次 /theos 觸發 + refresh_at 基線回讀**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

</div>

> [!IMPORTANT]
> 本專案永久免費。禁止倒賣、付費包裝、搬運引流、冒充作者或刪除版權資訊。完整規則見 [NOTICE.md](../NOTICE.md)。

## 功能

DeepAI Code 沒有獨立領取接口。當天第一次帶認證與設備指紋的請求會啟動每日簽到。本腳本只呼叫一次 `GET /deepai_code/theos`，檢查 `enabled`、`granted`、`balance`、`refresh_at`，並保存雜湊帳號基線。

| 項目 | 說明 |
| :--- | :--- |
| 輸入 | `DEEPAI_API_KEYS` 或 `DEEPAI_API_KEY` |
| 輸出 | 每帳號 JSON 與彙總 JSON |
| 執行環境 | Python 3.9+、`requests` |
| 成功 | `enabled=true`、`granted>0`、`refresh_at` 可讀 |

## 狀態語義

- 無基線：`GRANT_ACTIVE`
- `refresh_at` 相同：`ALREADY_GRANTED`
- `refresh_at` 前進：`CLAIMED`
- `granted=0`：`GRANT_PENDING`

腳本每帳號只發一次 Theos 請求，避免觸發上游重啟次數限制。狀態檔只保存 API Key SHA-256、額度值與 `refresh_at`。

## 憑據

```text
備註|API_KEY
```

單帳號：

```bash
export DEEPAI_API_KEY='<key>'
python deepaicode_daily.py
```

可選：`DEEPAI_LANE_VERSION`、`DEEPAI_MACHINE_ID`、`DEEPAI_STATE_FILE`。

請勿提交 API Key、狀態檔、報告或日誌。

## 青龍

1. 安裝 `requests`。
2. 上傳 `deepaicode_daily.py`。
3. 設定 `DEEPAI_API_KEYS` 或 `DEEPAI_API_KEY`。
4. 建立 `task deepaicode_daily.py`。
5. 建議北京時間每天 `08:37` 執行。

## GitHub Actions

工作流在 push 時測試，每日排程觸發一次額度並上傳 JSON 報告。未設定 Key 時，定時任務輸出 SKIPPED notice 並正常結束。

| Secret | 必填 | 值 |
| :--- | :---: | :--- |
| `DEEPAI_API_KEYS` | 二選一 | 多帳號 Key |
| `DEEPAI_API_KEY` | 二選一 | 單帳號 Key |

## 測試

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check deepaicode_daily.py tests
```

測試使用 fake session，不連線真實服務。

## 隱私

本倉庫不保存 API Key、設備 UUID、帳號資料、報告或日誌。

## 免責聲明

本專案供合法的個人自動化使用。活動規則、接口與額度口徑由服務方決定。

---

[返回簡體中文 README](../README.md) · [使用規則](../NOTICE.md) · [投喂與星軌](../README.md#star-trail)
