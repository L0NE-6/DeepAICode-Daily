#!/usr/bin/env python3
"""Trigger and verify the DeepAI Code daily Theos grant.

DeepAI Code has no separate claim endpoint. The first authenticated request
carrying a device fingerprint starts the daily check-in. This runner calls
GET /deepai_code/theos once, verifies granted/balance/refresh_at, and stores
only a hashed account id plus refresh_at baseline for honest next-run status.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping, Optional, Sequence

import requests


PROVIDER = "deepaicode"
DEFAULT_BASE_URL = "https://api.deepai.org"
BASE_URL_ENV = "DEEPAI_BASE_URL"
KEYS_ENV = "DEEPAI_API_KEYS"
KEY_ENV = "DEEPAI_API_KEY"
LANE_ENV = "DEEPAI_LANE_VERSION"
MACHINE_ENV = "DEEPAI_MACHINE_ID"
STATE_ENV = "DEEPAI_STATE_FILE"
DEFAULT_LANE = "4"
THEOS_PATH = "/deepai_code/theos"
REQUEST_TIMEOUT = 20
USER_AGENT = "L0NE-6-deepaicode-daily/1.0"


class ConfigError(ValueError):
    """Configuration or credential input error."""


class APIError(RuntimeError):
    """Classified API failure."""

    def __init__(
        self,
        result: str,
        message: str,
        *,
        http_status: Optional[int] = None,
    ) -> None:
        super().__init__(message)
        self.result = result
        self.message = message
        self.http_status = http_status


@dataclass(frozen=True)
class Account:
    note: str
    api_key: str


def emit(payload: Mapping[str, Any]) -> None:
    print(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str),
        flush=True,
    )


def _safe_label(raw: str, index: int) -> str:
    text = re.sub(r"[\x00-\x1f\x7f\u202a-\u202e\u2066-\u2069]", " ", raw)
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return "account_%d" % index
    if re.fullmatch(r"1\d{10}", text):
        return text[:3] + "****" + text[-4:]
    return text[:64]


def _redact(value: Any, secrets: Sequence[str]) -> str:
    text = str(value)
    for secret in sorted(
        {str(item) for item in secrets if item},
        key=len,
        reverse=True,
    ):
        text = text.replace(secret, "[REDACTED]")
    return text


def load_accounts(env: Optional[Mapping[str, str]] = None) -> list[Account]:
    values = os.environ if env is None else env
    raw = str(values.get(KEYS_ENV, "") or "").strip()
    if raw:
        lines = [line.strip() for line in re.split(r"[\r\n]+", raw) if line.strip()]
        accounts: list[Account] = []
        for index, line in enumerate(lines, 1):
            if "|" in line:
                label, key = line.split("|", 1)
            else:
                label, key = "account_%d" % index, line
            key = key.strip()
            if not key:
                raise ConfigError("account %d has an empty API key" % index)
            accounts.append(Account(_safe_label(label, index), key))
        return accounts

    key = str(values.get(KEY_ENV, "") or "").strip()
    if not key:
        raise ConfigError("DEEPAI_API_KEYS or DEEPAI_API_KEY is not configured")
    return [Account("account_1", key)]


def resolve_base_url(env: Optional[Mapping[str, str]] = None) -> str:
    values = os.environ if env is None else env
    text = str(values.get(BASE_URL_ENV, DEFAULT_BASE_URL) or "").strip().rstrip("/")
    if not text.startswith("https://") and not text.startswith("http://"):
        raise ConfigError("DEEPAI_BASE_URL must be an http(s) URL")
    return text


def resolve_lane(env: Optional[Mapping[str, str]] = None) -> str:
    values = os.environ if env is None else env
    lane = str(values.get(LANE_ENV, DEFAULT_LANE) or DEFAULT_LANE).strip()
    if not re.fullmatch(r"\d+", lane):
        raise ConfigError("DEEPAI_LANE_VERSION must be numeric")
    return lane


def _read_first(path: str) -> str:
    try:
        return Path(path).read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def detect_machine_id(env: Optional[Mapping[str, str]] = None) -> str:
    values = os.environ if env is None else env
    override = str(values.get(MACHINE_ENV, "") or "").strip()
    if override:
        return override

    system = platform.system().lower()
    if system == "windows":
        command = (
            "(Get-CimInstance Win32_ComputerSystemProduct "
            "-ErrorAction SilentlyContinue).UUID"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            value = result.stdout.strip()
            if value:
                return value
        except (OSError, subprocess.SubprocessError):
            pass
        try:
            import winreg

            with winreg.OpenKey(
                winreg.HKEY_LOCAL_MACHINE,
                r"SOFTWARE\Microsoft\Cryptography",
            ) as key:
                value = str(winreg.QueryValueEx(key, "MachineGuid")[0]).strip()
                if value:
                    return value
        except Exception:
            pass
    elif system == "darwin":
        try:
            result = subprocess.run(
                ["ioreg", "-rd1", "-c", "IOPlatformExpertDevice"],
                capture_output=True,
                text=True,
                timeout=8,
                check=False,
            )
            match = re.search(r'"IOPlatformUUID"\s*=\s*"([^"]+)"', result.stdout)
            if match:
                return match.group(1)
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        for path in ("/sys/class/dmi/id/product_uuid", "/etc/machine-id"):
            value = _read_first(path)
            if value:
                return value
    raise ConfigError(
        "cannot determine a machine id; set DEEPAI_MACHINE_ID explicitly"
    )


def machine_header(machine_id: str) -> str:
    normalized = re.sub(r"\s+", "", str(machine_id)).lower()
    if not normalized:
        raise ConfigError("machine id is empty")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def account_state_id(api_key: str) -> str:
    return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


def make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(
        {
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        }
    )
    return session


def _response_message(response: Any) -> str:
    text = str(getattr(response, "text", "") or "")
    try:
        payload = response.json()
    except Exception:
        return text[:240]
    if isinstance(payload, Mapping):
        error = payload.get("error")
        if isinstance(error, Mapping):
            return str(error.get("message") or error.get("code") or error)
        for key in ("message", "msg", "detail", "error"):
            value = payload.get(key)
            if value not in (None, "", False):
                return str(value)
    return text[:240]


def request_theos(
    session: requests.Session,
    base_url: str,
    account: Account,
    *,
    lane: str,
    machine_fp: str,
    instance_id: str,
) -> tuple[dict[str, Any], int]:
    headers = {
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "Api-Key": account.api_key,
        "X-DeepAI-Code-Theos": lane,
        "X-DeepAI-Code-Instance": instance_id,
        "X-DeepAI-Code-Machine": machine_fp,
    }
    try:
        response = session.get(
            base_url + THEOS_PATH,
            headers=headers,
            timeout=REQUEST_TIMEOUT,
            allow_redirects=False,
        )
    except requests.RequestException as exc:
        raise APIError(
            "NETWORK_ERROR",
            "network request failed: %s" % _redact(exc, [account.api_key]),
        ) from exc
    status = int(getattr(response, "status_code", 0) or 0)
    message = _response_message(response)
    if 300 <= status < 400:
        raise APIError(
            "AUTH_EXPIRED",
            "login session expired (HTTP %d redirect)" % status,
            http_status=status,
        )
    if status in (401, 403):
        result = (
            "INELIGIBLE"
            if re.search(r"restarted its check-in|too many times", message, re.I)
            else "AUTH_EXPIRED"
        )
        raise APIError(
            result,
            _redact(message or "login session expired", [account.api_key]),
            http_status=status,
        )
    if status == 426:
        raise APIError(
            "LANE_UNSUPPORTED",
            _redact(message or "lane version unsupported", [account.api_key]),
            http_status=status,
        )
    if status == 429:
        raise APIError(
            "RATE_LIMITED",
            _redact(message or "request was rate limited", [account.api_key]),
            http_status=status,
        )
    if not 200 <= status < 300:
        raise APIError(
            "HTTP_ERROR",
            _redact(message or "request failed (HTTP %d)" % status, [account.api_key]),
            http_status=status,
        )
    try:
        payload = response.json()
    except Exception as exc:
        raise APIError(
            "INVALID_JSON",
            "response is not JSON: %s" % _redact(exc, [account.api_key]),
            http_status=status,
        ) from exc
    if not isinstance(payload, Mapping):
        raise APIError(
            "INVALID_RESPONSE",
            "response is not a JSON object",
            http_status=status,
        )
    return dict(payload), status


def _number(value: Any) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if number != number or number in (float("inf"), float("-inf")):
        return None
    return int(number) if number.is_integer() else number


def parse_allowance(payload: Mapping[str, Any]) -> dict[str, Any]:
    enabled = payload.get("enabled")
    if not isinstance(enabled, bool):
        raise APIError("STATUS_UNRECOGNIZED", "theos.enabled is not boolean")
    granted = _number(payload.get("granted"))
    balance = _number(payload.get("balance"))
    refresh_at = str(payload.get("refresh_at", "") or "").strip()
    if granted is None or balance is None:
        raise APIError(
            "STATUS_UNRECOGNIZED",
            "theos.granted or theos.balance is not numeric",
        )
    if not refresh_at:
        raise APIError(
            "STATUS_UNRECOGNIZED",
            "theos.refresh_at is missing",
        )
    return {
        "enabled": enabled,
        "granted": granted,
        "balance": balance,
        "refresh_at": refresh_at,
        "lane_version": payload.get("lane_version"),
    }


def resolve_state_path(env: Optional[Mapping[str, str]] = None) -> Path:
    values = os.environ if env is None else env
    configured = str(values.get(STATE_ENV, "") or "").strip()
    if configured:
        return Path(configured).expanduser()
    return Path.home() / ".deepai-code-daily-state.json"


def load_state(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {"version": 1, "accounts": {}}
    if not isinstance(payload, Mapping):
        return {"version": 1, "accounts": {}}
    accounts = payload.get("accounts")
    if not isinstance(accounts, Mapping):
        accounts = {}
    return {"version": 1, "accounts": dict(accounts)}


def save_state(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(
        dir=str(path.parent),
        prefix=".deepai-state-",
        suffix=".tmp",
    )
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
        try:
            os.chmod(temporary, 0o600)
        except OSError:
            pass
        os.replace(temporary, path)
    except Exception:
        try:
            os.unlink(temporary)
        except OSError:
            pass
        raise


def _result(
    account: Account,
    result: str,
    ok: bool,
    message: str,
    *,
    http_status: Optional[int] = None,
    allowance: Optional[Mapping[str, Any]] = None,
    previous_refresh_at: str = "",
) -> dict[str, Any]:
    allowance = allowance or {}
    return {
        "account": account.note,
        "provider": PROVIDER,
        "result": result,
        "ok": ok,
        "message": message,
        "http_status": http_status,
        "enabled": allowance.get("enabled"),
        "granted": allowance.get("granted"),
        "balance": allowance.get("balance"),
        "refresh_at": allowance.get("refresh_at"),
        "previous_refresh_at": previous_refresh_at or None,
        "lane_version": allowance.get("lane_version"),
        "claimed": result in ("CLAIMED", "GRANT_ACTIVE"),
    }


def check_account(
    account: Account,
    *,
    base_url: str,
    lane: str,
    machine_fp: str,
    instance_id: str,
    state_path: Path,
    session_factory: Callable[[], requests.Session] = make_session,
) -> dict[str, Any]:
    session = None
    try:
        session = session_factory()
        payload, status = request_theos(
            session,
            base_url,
            account,
            lane=lane,
            machine_fp=machine_fp,
            instance_id=instance_id,
        )
        allowance = parse_allowance(payload)
        if not allowance["enabled"]:
            return _result(
                account,
                "INACTIVE",
                False,
                "daily Theos allowance is disabled for this account",
                http_status=status,
                allowance=allowance,
            )
        if allowance["granted"] <= 0:
            return _result(
                account,
                "GRANT_PENDING",
                False,
                "granted is 0; the daily allowance is not active yet",
                http_status=status,
                allowance=allowance,
            )

        state = load_state(state_path)
        state_id = account_state_id(account.api_key)
        previous = state["accounts"].get(state_id)
        previous_refresh = (
            str(previous.get("refresh_at", "") or "")
            if isinstance(previous, Mapping)
            else ""
        )
        changed = bool(previous_refresh and previous_refresh != allowance["refresh_at"])
        if previous_refresh == allowance["refresh_at"]:
            result = "ALREADY_GRANTED"
            message = "the active Theos grant matches the stored refresh_at baseline"
        elif changed:
            result = "CLAIMED"
            message = "the Theos grant is active and refresh_at advanced"
        else:
            result = "GRANT_ACTIVE"
            message = "the Theos grant is active; baseline stored for the next run"

        state["accounts"][state_id] = {
            "refresh_at": allowance["refresh_at"],
            "granted": allowance["granted"],
            "balance": allowance["balance"],
            "observed_at": _utc_now(),
        }
        save_state(state_path, state)
        return _result(
            account,
            result,
            True,
            message,
            http_status=status,
            allowance=allowance,
            previous_refresh_at=previous_refresh,
        )
    except APIError as exc:
        return _result(
            account,
            exc.result,
            False,
            exc.message,
            http_status=exc.http_status,
        )
    except Exception as exc:
        return _result(
            account,
            "UNEXPECTED_ERROR",
            False,
            "unexpected error: %s" % _redact(exc, [account.api_key]),
        )
    finally:
        close = getattr(session, "close", None)
        if callable(close):
            close()


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run_accounts(
    accounts: Sequence[Account],
    *,
    base_url: str,
    lane: str,
    machine_fp: str,
    instance_id: str,
    state_path: Path,
    session_factory: Callable[[], requests.Session] = make_session,
    output: Callable[[Mapping[str, Any]], None] = emit,
) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []
    for account in accounts:
        result = check_account(
            account,
            base_url=base_url,
            lane=lane,
            machine_fp=machine_fp,
            instance_id=instance_id,
            state_path=state_path,
            session_factory=session_factory,
        )
        results.append(result)
        output(result)
    return results


def build_summary(results: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    success = sum(1 for result in results if result.get("ok") is True)
    return {
        "provider": PROVIDER,
        "accounts": len(results),
        "success": success,
        "failed": len(results) - success,
        "claimed_now": sum(
            1 for result in results if result.get("result") == "CLAIMED"
        ),
        "already_granted": sum(
            1 for result in results if result.get("result") == "ALREADY_GRANTED"
        ),
        "results": [dict(result) for result in results],
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Trigger and verify the DeepAI Code daily Theos grant."
    )
    parser.add_argument("--only", type=int, default=0)
    return parser


def main(
    argv: Optional[Sequence[str]] = None,
    *,
    env: Optional[Mapping[str, str]] = None,
    session_factory: Callable[[], requests.Session] = make_session,
    output: Callable[[Mapping[str, Any]], None] = emit,
) -> int:
    args = build_parser().parse_args(argv)
    try:
        accounts = load_accounts(env)
        base_url = resolve_base_url(env)
        lane = resolve_lane(env)
        machine_fp = machine_header(detect_machine_id(env))
        state_path = resolve_state_path(env)
        if args.only:
            if args.only < 1 or args.only > len(accounts):
                raise ConfigError("--only is outside the configured account range")
            accounts = [accounts[args.only - 1]]
    except ConfigError as exc:
        result = _result(
            Account("config", ""),
            "CONFIG_ERROR",
            False,
            str(exc),
        )
        summary = build_summary([result])
        output(result)
        output(summary)
        return 2

    results = run_accounts(
        accounts,
        base_url=base_url,
        lane=lane,
        machine_fp=machine_fp,
        instance_id=os.urandom(16).hex(),
        state_path=state_path,
        session_factory=session_factory,
        output=output,
    )
    summary = build_summary(results)
    output(summary)
    return 0 if summary["failed"] == 0 else 1


def _configure_utf8_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            reconfigure(encoding="utf-8", errors="replace")


if __name__ == "__main__":
    _configure_utf8_stdio()
    sys.exit(main())
