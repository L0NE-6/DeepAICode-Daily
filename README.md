<div align="center">

<sub><strong>L0NE-6 · DEEPAI CODE SIGNAL</strong></sub>

# 🧠 DeepAI Code Daily

**DeepAI Code 每日 Theos 免费额度 · 多账号隔离 · /theos 触发 + refresh_at 基线回读**

> 当前版本：**v1.0.0**（2026-11-24） · 独立仓库维护版 · 单文件运行 · 不重复轮询

[简体中文](README.md) · [English](docs/README.en.md) · [繁體中文](docs/README.zh-Hant.md) · [日本語](docs/README.ja.md) · [한국어](docs/README.ko.md) · [Português (BR)](docs/README.pt-BR.md)

🔁 多账号隔离 · 🧾 JSON 报告 · ✅ Theos 状态回读 · 🛡️ Key 脱敏 · 🐧 青龙友好 · ☁️ GitHub Actions · 🧪 单元测试

<img src="https://img.shields.io/github/v/release/L0NE-6/DeepAICode-Daily?style=for-the-badge&label=Release&color=2ea44f&logo=github" />
<img src="https://img.shields.io/github/stars/L0NE-6/DeepAICode-Daily?style=for-the-badge&label=Stars&color=FFC75F&logo=github" />
<img src="https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white" />
<img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20%7C%20%E9%9D%92%E9%BE%99-4EAA25?style=for-the-badge&logo=linux&logoColor=white" />
<img src="https://img.shields.io/badge/License-MIT-F472B6?style=for-the-badge" />

[✨ 速览](#quick-overview) · [🔐 凭据](#credentials) · [🐧 青龙](#qinglong) · [☁️ Actions](#actions) · [✅ 判据](#success) · [🧠 原则](#design) · [📁 目录](#directory) · [🚫 边界](#usage-policy) · [✦ 星轨](#star-trail)

</div>

---

<a id="usage-policy"></a>
## 🚫 使用边界与转载声明

> [!IMPORTANT]
> **官方版本永久免费。禁止倒卖。** 未经作者书面许可，禁止付费包装、搬运引流、冒充作者，或使用作者身份与收款码制造官方授权假象。

本仓库、脚本、部署说明和 Release 下载始终免费公开。禁止把本项目包装为付费资源、内部版、独家版、会员权益、收费课程、代部署服务或包更新服务；禁止搬运到其他账号、群组、频道、网盘、电商和付费平台进行涨粉、截流、倒卖或引流。

完整规则见 **[NOTICE.md](NOTICE.md)**。

---

<a id="quick-overview"></a>
## ✨ 30 秒速览

| 维度 | 说明 |
| :--- | :--- |
| **做什么** | 用一次 `/deepai_code/theos` 请求触发并读取当天免费 Theos 额度。 |
| **输入** | `DEEPAI_API_KEYS` 多账号，或 `DEEPAI_API_KEY` 单账号。 |
| **输出** | 每账号一条 JSON、最后一条汇总 JSON、`granted`、`balance`、`refresh_at`。 |
| **部署** | Windows、Linux、青龙面板、GitHub Actions。 |
| **依赖** | Python 3.9+；运行时仅依赖 `requests`。 |
| **成功判据** | `enabled=true`、`granted>0`、`refresh_at` 可读取，并保存基线。 |

## 🔁 触发与回读

DeepAI Code 没有独立领取接口。当天第一次携带认证信息和设备指纹的请求会启动签到状态机，并发放免费 Theos。

```text
GET /deepai_code/theos
  |
  +-- enabled=false -> INACTIVE
  |
  +-- granted=0 -> GRANT_PENDING
  |
  +-- granted>0
        |
        +-- 无本地基线 -> GRANT_ACTIVE
        +-- refresh_at 未变 -> ALREADY_GRANTED
        +-- refresh_at 前进 -> CLAIMED
```

脚本只请求一次，不循环轮询。原因很明确：反复请求可能触发上游 `restarted its check-in too many times today`。

### 本地状态

脚本只保存：

- API Key 的 SHA-256；
- `refresh_at`；
- `granted`、`balance`；
- 观察时间。

状态文件默认 `~/.deepai-code-daily-state.json`，不包含原始 API Key。

---

<a id="credentials"></a>
## 🔐 凭据格式

### 多账号

`DEEPAI_API_KEYS` 每行一个账号：

```text
备注|API_KEY
```

示例：

```text
账号一|8a88d188-0000-4000-8000-000000000001
账号二|8a88d188-0000-4000-8000-000000000002
```

### 单账号

| 变量 | 必填 | 说明 |
| :--- | :---: | :--- |
| `DEEPAI_API_KEY` | ✅ | DeepAI Code API Key。 |
| `DEEPAI_API_KEYS` | 二选一 | 多账号 Key，优先于单账号变量。 |
| `DEEPAI_LANE_VERSION` | ⬜ | 计费车道版本，默认 `4`。 |
| `DEEPAI_MACHINE_ID` | ⬜ | 手工覆盖真实设备 UUID，仅用于无法自动识别时。 |
| `DEEPAI_STATE_FILE` | ⬜ | 自定义本地状态文件。 |
| `DEEPAI_BASE_URL` | ⬜ | 仅用于自建测试或接口迁移。 |

设备指纹会先转小写、去掉空白，再做 SHA-256。原始 UUID 不上传，也不写入状态文件。

---

## 🚀 本地快速开始

```powershell
python -m pip install -r requirements.txt
$env:DEEPAI_API_KEY = "<你的 API Key>"
python deepaicode_daily.py
```

多账号：

```powershell
$env:DEEPAI_API_KEYS = @"
账号一|<API Key 一>
账号二|<API Key 二>
"@
python deepaicode_daily.py
```

只运行第二个账号：

```powershell
python deepaicode_daily.py --only 2
```

---

<a id="qinglong"></a>
## 🐧 青龙面板部署

| 步骤 | 操作 |
| :---: | :--- |
| **1** | 依赖管理安装 `requests`。 |
| **2** | 上传 `deepaicode_daily.py`。 |
| **3** | 环境变量新增 `DEEPAI_API_KEYS` 或 `DEEPAI_API_KEY`。 |
| **4** | 新建定时任务，命令填 `task deepaicode_daily.py`。 |
| **5** | 建议北京时间每天 `08:37` 运行一次。 |

> 青龙任务优先使用 `task deepaicode_daily.py`，确保面板环境变量被注入。

---

<a id="actions"></a>
## ☁️ GitHub Actions 部署

本仓库内置 [`.github/workflows/deepaicode.yml`](.github/workflows/deepaicode.yml)。

| 事件 | 行为 |
| :--- | :--- |
| `push` 到 `main` | 运行 unittest、compileall 和 ruff。 |
| `schedule` | 每天先测试，再触发额度并上传 JSON 报告。 |
| `workflow_dispatch` | 手动执行同一套流程。 |

未配置 Key 时，定时任务输出明确 SKIPPED notice 并成功结束；配置 Key 后，脚本异常仍保持失败状态。

### Secrets

| Secret / Variable | 必填 | 值 |
| :--- | :---: | :--- |
| `DEEPAI_API_KEYS` | 二选一 | 多账号 API Key。 |
| `DEEPAI_API_KEY` | 二选一 | 单账号 API Key。 |
| `DEEPAI_LANE_VERSION` | ⬜ | 仓库 Variable，默认 `4`。 |

内置定时为北京时间 `08:37`，UTC cron `37 0 * * *`。

---

## ⌨️ 命令行与输出

```bash
python deepaicode_daily.py
python deepaicode_daily.py --only 1
```

| 退出码 | 含义 |
| :---: | :--- |
| `0` | 所有账号均读取到可信额度状态 |
| `1` | 至少一个账号失败或额度未激活 |
| `2` | 未配置凭据或配置格式错误 |

单账号结果字段：

| 字段 | 说明 |
| :--- | :--- |
| `account` | 掩码后的账号标签 |
| `result` | 结果码 |
| `ok` | 是否达到可信成功条件 |
| `enabled` | 每日额度是否启用 |
| `granted` | 当天发放总额 |
| `balance` | 当前剩余额度 |
| `refresh_at` | 下一次刷新时间 |
| `previous_refresh_at` | 上次保存的刷新时间 |
| `lane_version` | 上游计费车道 |

---

## 🧭 结果码

| 结果码 | 是否成功 | 含义 |
| :--- | :---: | :--- |
| `GRANT_ACTIVE` | ✅ | 首次运行读到有效额度并保存基线 |
| `CLAIMED` | ✅ | `refresh_at` 前进，确认进入新额度周期 |
| `ALREADY_GRANTED` | ✅ | `refresh_at` 与本地基线一致 |
| `GRANT_PENDING` | ❌ | `granted=0`，额度尚未激活 |
| `INACTIVE` | ❌ | 每日额度未启用 |
| `INELIGIBLE` | ❌ | 当日签到重启次数超限 |
| `AUTH_EXPIRED` | ❌ | Key 无效或返回登录页 |
| `LANE_UNSUPPORTED` | ❌ | 计费车道版本不受支持 |
| `STATUS_UNRECOGNIZED` | ❌ | 响应字段缺失或无法解析 |
| `RATE_LIMITED` | ❌ | HTTP 429 |
| `HTTP_ERROR` | ❌ | 非 2xx HTTP 错误 |
| `NETWORK_ERROR` | ❌ | 网络异常 |
| `INVALID_JSON` | ❌ | 回包不是 JSON |
| `CONFIG_ERROR` | ❌ | 环境变量、设备指纹或基址配置错误 |

---

<a id="success"></a>
## ✅ 成功判据

| 场景 | 必须满足 |
| :--- | :--- |
| 首次运行 | `enabled=true`、`granted>0`、`refresh_at` 可读取 |
| 后续运行 | `refresh_at` 与基线一致，或进入新周期 |
| 额度未发放 | `granted=0` 时明确返回 `GRANT_PENDING` |

脚本不会把一次普通 HTTP 200 或“请求成功”当成额度发放。

---

## 🧪 测试与静态检查

```powershell
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check deepaicode_daily.py tests
```

测试覆盖首次基线、重复周期、新周期、额度未发放、禁用、重启次数超限、登录失效、敏感值脱敏和多账号隔离。

---

<a id="design"></a>
## 🧠 设计原则

- **单次触发**：每个账号只请求一次 `/theos`，不通过轮询放大风控面；
- **设备指纹真实**：优先读取本机硬件标识，只上传 SHA-256，不伪造多设备；
- **基线可审计**：本地只保存 API Key 哈希、`refresh_at`、`granted` 和 `balance`；
- **不伪造领取**：`granted=0` 明确报告 `GRANT_PENDING`，不把请求成功当额度到账；
- **多账号隔离**：每个账号独立 Session、独立错误、独立基线；
- **最小依赖**：运行时仅依赖 `requests`；
- **敏感信息脱敏**：API Key、设备 UUID 和异常回包不进入日志与报告。

---

## 🔒 隐私说明

本仓库不包含任何 API Key、账号、设备 UUID、状态文件或运行日志。所有凭据均由环境变量、GitHub Secrets 或你自己的运行环境注入。

请勿提交 `deepaicode-report.json`、`deepaicode-report.jsonl`、Key 文件、状态文件和完整运行日志。

---

<a id="directory"></a>
## 📁 目录结构

```text
DeepAICode-Daily/
├── .github/workflows/deepaicode.yml
├── assets/
│   ├── donate-alipay.jpg
│   └── donate-wechat.png
├── docs/
│   ├── README.en.md
│   ├── README.zh-Hant.md
│   ├── README.ja.md
│   ├── README.ko.md
│   └── README.pt-BR.md
├── tests/test_deepaicode_daily.py
├── deepaicode_daily.py
├── CHANGELOG.md
├── LICENSE
├── NOTICE.md
├── THIRD_PARTY_NOTICES.md
├── pyproject.toml
├── requirements.txt
└── README.md
```

---

## 📦 版本与发布

- 当前版本：`v1.0.0`（2026-11-24）；
- 每次协议、脚本或行为变化单独发布版本，历史 Release 保留；
- Release 附带完整 ZIP、单文件脚本和 `SHA256SUMS.txt`；
- 公开包不包含 API Key、设备 UUID、状态文件和运行日志。

下载页：<https://github.com/L0NE-6/DeepAICode-Daily/releases>

---

## ☕ 支持与投喂

脚本完全免费，无广告、无功能限制。如果它确实帮你省了时间，欢迎自愿赞赏。

<p align="center">
  <img src="assets/donate-wechat.png" width="260" alt="微信赞赏码" />
  &nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;
  <img src="assets/donate-alipay.jpg" width="260" alt="支付宝收款码" />
</p>

---

## ⚠️ 免责声明

本项目用于个人学习和合法的个人自动化。DeepAI Code 的活动规则、接口、额度口径和账号资格由服务方决定；使用前请确认对应服务条款，并自行承担账号、网络、活动和接口变化带来的风险。

---

## 💬 反馈与贡献

- [提交 Issue](https://github.com/L0NE-6/DeepAICode-Daily/issues)
- [发起 Pull Request](https://github.com/L0NE-6/DeepAICode-Daily/pulls)

反馈问题时，请附脱敏后的 `enabled/granted/balance/refresh_at`、运行模式、Python 版本和复现步骤。不要上传真实 API Key、设备 UUID、状态文件或完整账号日志。

---

<a id="star-trail"></a>
## ✦ 星轨 Star Trail

<a href="https://star-history.com/#L0NE-6/DeepAICode-Daily&Date">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/svg?repos=L0NE-6/DeepAICode-Daily&type=Date&theme=dark" />
    <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/svg?repos=L0NE-6/DeepAICode-Daily&type=Date" />
    <img alt="DeepAI Code Daily Star Trail" src="https://api.star-history.com/svg?repos=L0NE-6/DeepAICode-Daily&type=Date" />
  </picture>
</a>

---

<div align="center">
  <sub>L0NE-6 · DEEPAI CODE SIGNAL &nbsp;|&nbsp; 点个 <b>Star</b>，让下一次额度触发有迹可循 ✨</sub>
</div>
