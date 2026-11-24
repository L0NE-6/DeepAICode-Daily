import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import deepaicode_daily


class FakeResponse:
    def __init__(self, payload=None, *, status_code=200, text=None):
        self.status_code = status_code
        self.payload = payload
        self.text = (
            text
            if text is not None
            else json.dumps(payload, ensure_ascii=False) if payload is not None else ""
        )

    def json(self):
        return self.payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.closed = False

    def get(self, url, **kwargs):
        self.calls.append(("GET", url, kwargs))
        if not self.responses:
            raise AssertionError("unexpected GET")
        return self.responses.pop(0)

    def close(self):
        self.closed = True


class SessionFactory:
    def __init__(self, groups):
        self.groups = [list(group) for group in groups]
        self.sessions = []

    def __call__(self):
        session = FakeSession(self.groups.pop(0))
        self.sessions.append(session)
        return session


def allowance(
    *,
    enabled=True,
    granted="200",
    balance="200",
    refresh_at="2026-11-25T04:03:00Z",
):
    return FakeResponse(
        {
            "enabled": enabled,
            "granted": granted,
            "balance": balance,
            "refresh_at": refresh_at,
            "lane_version": "4",
        }
    )


def account(key="8a88d188-0000-4000-8000-000000000001"):
    return deepaicode_daily.load_accounts({"DEEPAI_API_KEY": key})[0]


class DeepAICodeDailyTests(unittest.TestCase):
    def test_load_multi_account_and_machine_header(self):
        accounts = deepaicode_daily.load_accounts(
            {
                "DEEPAI_API_KEYS": (
                    "13800138000|key-one\n"
                    "second|key-two"
                )
            }
        )
        self.assertEqual(2, len(accounts))
        self.assertEqual("138****8000", accounts[0].note)
        self.assertEqual("second", accounts[1].note)
        first = deepaicode_daily.machine_header(" ABCD-1234 ")
        second = deepaicode_daily.machine_header("abcd-1234")
        self.assertEqual(first, second)
        self.assertEqual(64, len(first))

    def test_first_grant_stores_baseline(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            factory = SessionFactory([[allowance()]])
            result = deepaicode_daily.check_account(
                account(),
                base_url="https://example.test",
                lane="4",
                machine_fp="machine-fp",
                instance_id="instance-id",
                state_path=state,
                session_factory=factory,
            )
            self.assertEqual("GRANT_ACTIVE", result["result"])
            self.assertTrue(result["ok"])
            payload = json.loads(state.read_text(encoding="utf-8"))
            self.assertEqual(1, len(payload["accounts"]))
            self.assertNotIn(account().api_key, state.read_text(encoding="utf-8"))
            headers = factory.sessions[0].calls[0][2]["headers"]
            self.assertEqual("4", headers["X-DeepAI-Code-Theos"])
            self.assertEqual("machine-fp", headers["X-DeepAI-Code-Machine"])
            self.assertEqual("instance-id", headers["X-DeepAI-Code-Instance"])

    def test_same_refresh_is_already_granted(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            factory = SessionFactory([[allowance()], [allowance()]])
            kwargs = {
                "base_url": "https://example.test",
                "lane": "4",
                "machine_fp": "machine-fp",
                "instance_id": "instance-id",
                "state_path": state,
                "session_factory": factory,
            }
            first = deepaicode_daily.check_account(account(), **kwargs)
            second = deepaicode_daily.check_account(account(), **kwargs)
            self.assertEqual("GRANT_ACTIVE", first["result"])
            self.assertEqual("ALREADY_GRANTED", second["result"])
            self.assertTrue(second["ok"])

    def test_changed_refresh_is_claimed(self):
        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory) / "state.json"
            factory = SessionFactory(
                [
                    [allowance(refresh_at="2026-11-25T04:03:00Z")],
                    [allowance(refresh_at="2026-11-26T04:03:00Z")],
                ]
            )
            kwargs = {
                "base_url": "https://example.test",
                "lane": "4",
                "machine_fp": "machine-fp",
                "instance_id": "instance-id",
                "state_path": state,
                "session_factory": factory,
            }
            deepaicode_daily.check_account(account(), **kwargs)
            second = deepaicode_daily.check_account(account(), **kwargs)
            self.assertEqual("CLAIMED", second["result"])
            self.assertTrue(second["claimed"])
            self.assertEqual(
                "2026-11-25T04:03:00Z",
                second["previous_refresh_at"],
            )

    def test_granted_zero_is_pending(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = SessionFactory([[allowance(granted="0", balance="0")]])
            result = deepaicode_daily.check_account(
                account(),
                base_url="https://example.test",
                lane="4",
                machine_fp="machine-fp",
                instance_id="instance-id",
                state_path=Path(directory) / "state.json",
                session_factory=factory,
            )
            self.assertEqual("GRANT_PENDING", result["result"])
            self.assertFalse(result["ok"])

    def test_disabled_is_inactive(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = SessionFactory([[allowance(enabled=False)]])
            result = deepaicode_daily.check_account(
                account(),
                base_url="https://example.test",
                lane="4",
                machine_fp="machine-fp",
                instance_id="instance-id",
                state_path=Path(directory) / "state.json",
                session_factory=factory,
            )
            self.assertEqual("INACTIVE", result["result"])

    def test_restart_limit_is_ineligible(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = SessionFactory(
                [
                    [
                        FakeResponse(
                            {"error": "restarted its check-in too many times today"},
                            status_code=403,
                        )
                    ]
                ]
            )
            result = deepaicode_daily.check_account(
                account(),
                base_url="https://example.test",
                lane="4",
                machine_fp="machine-fp",
                instance_id="instance-id",
                state_path=Path(directory) / "state.json",
                session_factory=factory,
            )
            self.assertEqual("INELIGIBLE", result["result"])

    def test_redirect_is_auth_expired(self):
        with tempfile.TemporaryDirectory() as directory:
            factory = SessionFactory([[FakeResponse({}, status_code=302)]])
            result = deepaicode_daily.check_account(
                account(),
                base_url="https://example.test",
                lane="4",
                machine_fp="machine-fp",
                instance_id="instance-id",
                state_path=Path(directory) / "state.json",
                session_factory=factory,
            )
            self.assertEqual("AUTH_EXPIRED", result["result"])

    def test_multi_account_isolation_and_redaction(self):
        accounts = deepaicode_daily.load_accounts(
            {"DEEPAI_API_KEYS": "one|secret-one\ntwo|secret-two"}
        )
        with tempfile.TemporaryDirectory() as directory:
            factory = SessionFactory(
                [
                    [allowance()],
                    [FakeResponse({"message": "bad secret-two"}, status_code=500)],
                ]
            )
            results = deepaicode_daily.run_accounts(
                accounts,
                base_url="https://example.test",
                lane="4",
                machine_fp="machine-fp",
                instance_id="instance-id",
                state_path=Path(directory) / "state.json",
                session_factory=factory,
                output=lambda _: None,
            )
            rendered = json.dumps(results, ensure_ascii=False)
        self.assertEqual("GRANT_ACTIVE", results[0]["result"])
        self.assertEqual("HTTP_ERROR", results[1]["result"])
        self.assertNotIn("secret-two", rendered)
        self.assertIn("[REDACTED]", rendered)
        self.assertIsNot(factory.sessions[0], factory.sessions[1])
        self.assertTrue(all(session.closed for session in factory.sessions))

    def test_config_error_summary(self):
        output = []
        code = deepaicode_daily.main(
            [],
            env={},
            session_factory=SessionFactory([]),
            output=output.append,
        )
        self.assertEqual(2, code)
        self.assertEqual("CONFIG_ERROR", output[0]["result"])
        self.assertEqual("deepaicode", output[-1]["provider"])


if __name__ == "__main__":
    unittest.main()
