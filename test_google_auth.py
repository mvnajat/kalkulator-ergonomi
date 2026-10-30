"""Security and configuration checks for optional Google OIDC + project storage."""

import sys
import types
import unittest
from unittest.mock import patch

from utils.workspace import google_auth_is_ready, oidc_subject, cloud_list, cloud_load


class FakeUser(dict):
    def __init__(self, logged_in: bool, **claims):
        super().__init__(claims)
        self.is_logged_in = logged_in


class GoogleAuthTests(unittest.TestCase):
    def test_auth_requires_all_oidc_settings(self):
        valid = {"auth": {
            "redirect_uri": "https://example.streamlit.app/oauth2callback",
            "cookie_secret": "secret-value",
            "client_id": "id",
            "client_secret": "secret",
            "server_metadata_url": "https://accounts.google.com/.well-known/openid-configuration",
        }}
        self.assertTrue(google_auth_is_ready(valid))
        for missing in list(valid["auth"]):
            incomplete = {"auth": {k: v for k, v in valid["auth"].items() if k != missing}}
            with self.subTest(missing=missing):
                self.assertFalse(google_auth_is_ready(incomplete))
        self.assertFalse(google_auth_is_ready({}))

    def test_owner_is_google_sub_never_email(self):
        account = FakeUser(True, sub="google-immutable-123", email="user@example.com")
        self.assertEqual(oidc_subject(account), "google-immutable-123")
        self.assertEqual(oidc_subject(FakeUser(False, sub="google-immutable-123")), "")
        self.assertEqual(oidc_subject(FakeUser(True, email="user@example.com")), "")
        self.assertEqual(oidc_subject(None), "")

    def test_cloud_list_filters_by_authenticated_owner(self):
        executed = []

        class Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def execute(self, query, params=None):
                executed.append((query, params))

            def fetchall(self):
                return [("Proyek A",)]

        class Conn:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def cursor(self):
                return Cursor()

        fake_psycopg = types.ModuleType("psycopg")
        fake_psycopg.connect = lambda *_a, **_kw: Conn()
        with patch.dict(sys.modules, {"psycopg": fake_psycopg}):
            self.assertEqual(cloud_list("postgresql://example", "user-a"), ["Proyek A"])
        query, args = executed[-1]
        self.assertIn("WHERE owner_sub = %s", query)
        self.assertEqual(args, ("user-a",))
        self.assertEqual(cloud_list("", "user-a"), [])

    def test_cloud_load_filters_by_owner_and_project(self):
        executed = []

        class Cursor:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def execute(self, query, params):
                executed.append((query, params))

            def fetchone(self):
                return ({"identitas": {}},)

        class Conn:
            def __enter__(self):
                return self

            def __exit__(self, *_):
                return False

            def cursor(self):
                return Cursor()

        fake_psycopg = types.ModuleType("psycopg")
        fake_psycopg.connect = lambda *_a, **_kw: Conn()
        with patch.dict(sys.modules, {"psycopg": fake_psycopg}), patch(
            "utils.workspace.restore_session_from_json", return_value=None
        ):
            cloud_load("postgresql://example", "user-b", "Praktikum B")
        query, args = executed[-1]
        self.assertIn("WHERE owner_sub = %s AND name = %s", query)
        self.assertEqual(args, ("user-b", "Praktikum B"))


if __name__ == "__main__":
    unittest.main()
