"""Offline regression tests for credential storage and authenticated transport."""

import contextlib
import importlib.machinery
import importlib.util
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests


loader = importlib.machinery.SourceFileLoader(
    "onedns_cli", str(Path(__file__).resolve().parents[1] / "onedns")
)
spec = importlib.util.spec_from_loader(loader.name, loader)
cli = importlib.util.module_from_spec(spec)
loader.exec_module(cli)


class CredentialStorageTests(unittest.TestCase):
    def test_new_and_existing_credentials_are_private_and_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "config"
            with patch.object(cli, "CONFIG_PATH", path):
                for key in ("first-key", "replacement%key"):
                    if path.exists():
                        path.chmod(0o644)
                    previous_umask = os.umask(0)
                    try:
                        cli.save_config(key)
                    finally:
                        os.umask(previous_umask)
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                    with patch.dict(os.environ, {}, clear=True):
                        self.assertEqual(cli.load_api_key(), key)

    def test_failed_replace_preserves_previous_key_and_cleans_temp_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config"
            with patch.object(cli, "CONFIG_PATH", path):
                cli.save_config("previous-key")
                with patch.object(cli.os, "replace", side_effect=OSError("disk failure")):
                    with self.assertRaises(OSError):
                        cli.save_config("new-key")
                self.assertEqual(cli._read_config().get("default", "api_key"), "previous-key")
                self.assertEqual(list(Path(directory).iterdir()), [path])


class TransportTests(unittest.TestCase):
    @patch.object(cli.requests, "request")
    def test_authenticated_request_verifies_tls_and_bounds_waits(self, request):
        request.return_value = Mock(status_code=200, content=b"{}")
        request.return_value.json.return_value = {"zones": []}
        self.assertEqual(cli.api("GET", "/zones", api_key="secret"), {"zones": []})
        options = request.call_args.kwargs
        self.assertIs(options["verify"], True)
        self.assertIs(options["allow_redirects"], False)
        self.assertEqual(options["timeout"], (10, 30))
        self.assertEqual(options["headers"]["X-API-Key"], "secret")

    @patch.object(cli.requests, "request")
    def test_redirects_fail_without_sending_another_request(self, request):
        for status in (301, 302, 303, 307, 308):
            with self.subTest(status=status):
                request.reset_mock()
                request.return_value = Mock(status_code=status)
                with contextlib.redirect_stderr(io.StringIO()) as output:
                    with self.assertRaises(SystemExit) as error:
                        cli.api("POST", "/zones", api_key="secret")
                self.assertEqual(error.exception.code, 1)
                self.assertIn("redirect refused", output.getvalue())
                request.assert_called_once()

    @patch.object(cli.requests, "request")
    def test_transport_errors_fail_cleanly_without_leaking_exception_details(self, request):
        for error, message in (
            (requests.exceptions.SSLError, "TLS certificate verification failed"),
            (requests.exceptions.Timeout, "timed out"),
            (requests.exceptions.ConnectionError, "Could not connect"),
        ):
            with self.subTest(error=error):
                request.side_effect = error("sensitive upstream details")
                with contextlib.redirect_stderr(io.StringIO()) as output:
                    with self.assertRaises(SystemExit):
                        cli.api("GET", "/zones", api_key="secret")
                self.assertIn(message, output.getvalue())
                self.assertNotIn("sensitive upstream details", output.getvalue())


if __name__ == "__main__":
    unittest.main()
