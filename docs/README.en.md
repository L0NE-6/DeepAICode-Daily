<div align="center">

# 🧠 DeepAI Code Daily

**Daily Theos grant · multi-account · one `/theos` request + refresh_at baseline**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

</div>

> [!IMPORTANT]
> This project is free. Resale, paywalling, author impersonation, and removal of
> copyright notices are prohibited. See [NOTICE.md](../NOTICE.md).

## What It Does

DeepAI Code has no separate claim endpoint. The first authenticated request
with a device fingerprint starts the daily check-in. This runner calls
`GET /deepai_code/theos` once, verifies `enabled`, `granted`, `balance`, and
`refresh_at`, then stores a hashed account baseline.

| Item | Description |
| :--- | :--- |
| Input | `DEEPAI_API_KEYS` or `DEEPAI_API_KEY` |
| Output | Per-account JSON and aggregate JSON |
| Runtime | Python 3.9+ with `requests` |
| Success | `enabled=true`, `granted>0`, readable `refresh_at` |

## State Semantics

- No local baseline: `GRANT_ACTIVE`
- Same `refresh_at`: `ALREADY_GRANTED`
- New `refresh_at`: `CLAIMED`
- `granted=0`: `GRANT_PENDING`

The script makes only one Theos request per account to avoid service-side
restart limits. It stores only the API key SHA-256, allowance values, and
`refresh_at`.

## Credentials

```text
label|API_KEY
```

Single account:

```bash
export DEEPAI_API_KEY='<key>'
python deepaicode_daily.py
```

Optional:

- `DEEPAI_LANE_VERSION`, default `4`
- `DEEPAI_MACHINE_ID`, explicit device UUID override
- `DEEPAI_STATE_FILE`, custom local state path

Never commit API keys, state files, reports, or logs.

## Qinglong

1. Install `requests`.
2. Upload `deepaicode_daily.py`.
3. Set `DEEPAI_API_KEYS` or `DEEPAI_API_KEY`.
4. Create `task deepaicode_daily.py`.
5. Run once per day at 08:37 Beijing time.

## GitHub Actions

The workflow tests on push and runs one scheduled grant attempt per day. Without
a key, the scheduled run is skipped with an explicit notice.

| Secret | Required | Value |
| :--- | :---: | :--- |
| `DEEPAI_API_KEYS` | Either one | Multi-account keys |
| `DEEPAI_API_KEY` | Either one | Single-account key |

## Test

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check deepaicode_daily.py tests
```

Tests use fake sessions and never contact the live service.

## Privacy

No API keys, device UUIDs, account data, reports, or logs are stored in the
repository.

## Disclaimer

Use this project for lawful personal automation. Rules, interfaces, and quota
semantics are controlled by the service provider.

---

[Chinese README](../README.md) · [Usage policy](../NOTICE.md) · [Donation and Star History](../README.md#star-trail)
