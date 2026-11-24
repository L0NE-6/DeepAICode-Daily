<div align="center">

# 🧠 DeepAI Code Daily

**일일 Theos 무료 할당량 · 다중 계정 · 단일 /theos 요청 + refresh_at 기준**

[简体中文](../README.md) · [English](README.en.md) · [繁體中文](README.zh-Hant.md) · [日本語](README.ja.md) · [한국어](README.ko.md) · [Português (BR)](README.pt-BR.md)

</div>

> [!IMPORTANT]
> 이 프로젝트는 무료입니다. 재판매, 유료 패키징, 작성자 사칭, 저작권 표시 제거를 금지합니다. 자세한 내용은 [NOTICE.md](../NOTICE.md)를 확인하세요.

## 기능

DeepAI Code에는 별도 claim 엔드포인트가 없습니다. 인증과 장치 지문을 포함한 당일 첫 요청이 일일 체크인을 시작합니다. 이 스크립트는 `GET /deepai_code/theos`를 한 번 호출하고 `enabled`, `granted`, `balance`, `refresh_at`을 확인한 뒤 해시된 계정 기준을 저장합니다.

| 항목 | 설명 |
| :--- | :--- |
| 입력 | `DEEPAI_API_KEYS` 또는 `DEEPAI_API_KEY` |
| 출력 | 계정별 JSON과 집계 JSON |
| 실행 환경 | Python 3.9+, `requests` |
| 성공 | `enabled=true`, `granted>0`, 읽을 수 있는 `refresh_at` |

## 상태 의미

- 기준 없음: `GRANT_ACTIVE`
- `refresh_at` 동일: `ALREADY_GRANTED`
- `refresh_at` 증가: `CLAIMED`
- `granted=0`: `GRANT_PENDING`

계정마다 Theos 요청은 한 번뿐입니다. 상태 파일에는 API Key SHA-256, 할당량, `refresh_at`만 저장합니다.

## 자격 증명

```text
label|API_KEY
```

```bash
export DEEPAI_API_KEY='<key>'
python deepaicode_daily.py
```

선택: `DEEPAI_LANE_VERSION`, `DEEPAI_MACHINE_ID`, `DEEPAI_STATE_FILE`.

API Key, 상태 파일, 보고서, 로그를 커밋하지 마세요.

## Qinglong

1. `requests`를 설치합니다.
2. `deepaicode_daily.py`를 업로드합니다.
3. `DEEPAI_API_KEYS` 또는 `DEEPAI_API_KEY`를 설정합니다.
4. `task deepaicode_daily.py`를 예약합니다.
5. 베이징 시간 `08:37`에 하루 한 번 실행합니다.

## GitHub Actions

push 시 테스트하고 매일 한 번 할당량을 확인한 뒤 JSON 보고서를 업로드합니다. Key가 없으면 예약 실행은 SKIPPED notice를 남기고 정상 종료합니다.

| Secret | 필수 | 값 |
| :--- | :---: | :--- |
| `DEEPAI_API_KEYS` | 둘 중 하나 | 다중 계정 Key |
| `DEEPAI_API_KEY` | 둘 중 하나 | 단일 계정 Key |

## 테스트

```bash
python -m unittest discover -s tests -v
python -m compileall -q .
python -m ruff check deepaicode_daily.py tests
```

테스트는 fake session을 사용하며 실제 서비스에 연결하지 않습니다.

## 개인정보

이 저장소는 API Key, 장치 UUID, 계정 정보, 보고서, 로그를 저장하지 않습니다.

## 면책

합법적인 개인 자동화에 사용하세요. 규칙, 인터페이스, 할당량 의미는 서비스 제공자가 관리합니다.

---

[중국어 README로 돌아가기](../README.md) · [사용 규칙](../NOTICE.md) · [후원 및 Star History](../README.md#star-trail)
