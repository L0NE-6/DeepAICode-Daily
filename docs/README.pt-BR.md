<div align="center">

# 🧠 DeepAI Code Daily

**Cota diária de Theos · várias contas · uma chamada `/theos` + baseline refresh_at**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

</div>

> [!IMPORTANT]
> Este projeto é gratuito. É proibido revender, colocar atrás de pagamento,
> fingir ser o autor ou remover avisos de copyright. Consulte
> [NOTICE.md](../NOTICE.md).

## Função

DeepAI Code não tem um endpoint de claim separado. A primeira requisição
autenticada com fingerprint do dispositivo inicia o check-in diário. Este
runner chama `GET /deepai_code/theos` uma vez, confirma `enabled`, `granted`,
`balance` e `refresh_at`, e salva uma baseline com hash da conta.

| Item | Descrição |
| :--- | :--- |
| Entrada | `DEEPAI_API_KEYS` ou `DEEPAI_API_KEY` |
| Saída | JSON por conta e JSON agregado |
| Ambiente | Python 3.9+ com `requests` |
| Sucesso | `enabled=true`, `granted>0`, `refresh_at` legível |

## Estados

- Sem baseline: `GRANT_ACTIVE`
- Mesmo `refresh_at`: `ALREADY_GRANTED`
- Novo `refresh_at`: `CLAIMED`
- `granted=0`: `GRANT_PENDING`

O script faz apenas uma chamada Theos por conta. O arquivo de estado guarda
somente SHA-256 da API Key, valores da cota e `refresh_at`.

## Credenciais

```text
label|API_KEY
```

```bash
export DEEPAI_API_KEY='<key>'
python deepaicode_daily.py
```

Opcional: `DEEPAI_LANE_VERSION`, `DEEPAI_MACHINE_ID`,
`DEEPAI_STATE_FILE`.

Nunca envie API Keys, estado, relatórios ou logs ao Git.

## Qinglong

1. Instale `requests`.
2. Envie `deepaicode_daily.py`.
3. Configure `DEEPAI_API_KEYS` ou `DEEPAI_API_KEY`.
4. Crie `task deepaicode_daily.py`.
5. Execute uma vez por dia às 08:37 de Pequim.

## GitHub Actions

O workflow testa em push e executa uma tentativa diária, enviando um relatório
JSON. Sem key, a execução agendada é ignorada com notice explícito.

| Secret | Obrigatório | Valor |
| :--- | :---: | :--- |
| `DEEPAI_API_KEYS` | Um dos dois | Keys de várias contas |
| `DEEPAI_API_KEY` | Um dos dois | Key de uma conta |

## Testes

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check deepaicode_daily.py tests
```

Os testes usam fake sessions e não acessam o serviço real.

## Privacidade

O repositório não armazena API Keys, UUID do dispositivo, dados de conta,
relatórios ou logs.

## Aviso

Use apenas para automação pessoal lícita. Regras, interfaces e semântica da cota
são controladas pelo provedor.

---

[README chinês](../README.md) · [Política de uso](../NOTICE.md) · [Doação e Star History](../README.md#star-trail)
