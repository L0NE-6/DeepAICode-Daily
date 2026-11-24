<div align="center">

# 🧠 DeepAI Code Daily

**毎日 Theos 無料枠 · 複数アカウント · 1 回の /theos と refresh_at 基準**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

</div>

> [!IMPORTANT]
> 本プロジェクトは無料です。転売、有料パッケージ化、作者の偽装、著作権表示の削除を禁止します。詳細は [NOTICE.md](../NOTICE.md) を参照してください。

## 機能

DeepAI Code には独立した claim エンドポイントがありません。認証済みでデバイス指紋付きの最初のリクエストが毎日チェックインを開始します。本スクリプトは `GET /deepai_code/theos` を 1 回だけ呼び、`enabled`、`granted`、`balance`、`refresh_at` を確認してハッシュ化したアカウント基準を保存します。

| 項目 | 内容 |
| :--- | :--- |
| 入力 | `DEEPAI_API_KEYS` または `DEEPAI_API_KEY` |
| 出力 | アカウント別 JSON と集計 JSON |
| 実行環境 | Python 3.9+、`requests` |
| 成功 | `enabled=true`、`granted>0`、`refresh_at` が読める |

## 状態

- 基準なし: `GRANT_ACTIVE`
- `refresh_at` が同じ: `ALREADY_GRANTED`
- `refresh_at` が進んだ: `CLAIMED`
- `granted=0`: `GRANT_PENDING`

1 アカウントにつき Theos リクエストは 1 回だけです。状態ファイルには API Key の SHA-256、枠情報、`refresh_at` のみを保存します。

## 認証情報

```text
label|API_KEY
```

```bash
export DEEPAI_API_KEY='<key>'
python deepaicode_daily.py
```

任意: `DEEPAI_LANE_VERSION`、`DEEPAI_MACHINE_ID`、`DEEPAI_STATE_FILE`。

API Key、状態ファイル、レポート、ログをコミットしないでください。

## Qinglong

1. `requests` をインストールします。
2. `deepaicode_daily.py` をアップロードします。
3. `DEEPAI_API_KEYS` または `DEEPAI_API_KEY` を設定します。
4. `task deepaicode_daily.py` をスケジュールします。
5. 北京時間 `08:37` に 1 日 1 回実行します。

## GitHub Actions

push 時にテストし、毎日 1 回枠を確認して JSON レポートをアップロードします。Key がない場合、定時実行は SKIPPED notice を出して正常終了します。

| Secret | 必須 | 値 |
| :--- | :---: | :--- |
| `DEEPAI_API_KEYS` | どちらか | 複数アカウント Key |
| `DEEPAI_API_KEY` | どちらか | 単一アカウント Key |

## テスト

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check deepaicode_daily.py tests
```

テストは fake session を使用し、実際のサービスへ接続しません。

## プライバシー

本リポジトリは API Key、デバイス UUID、アカウント情報、レポート、ログを保存しません。

## 免責事項

合法的な個人自動化のために使用してください。ルール、インターフェース、枠の意味はサービス提供者が管理します。

---

[中国語 README に戻る](../README.md) · [利用規則](../NOTICE.md) · [投げ銭と Star History](../README.md#star-trail)
