"""Unit 9: HTTP request instrumentation tests for The Unofficial Guide."""

import sys
import unittest
from datetime import datetime
from types import ModuleType
from unittest.mock import patch

from serve import app


class RequestLoggingTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def assert_common_fields(self, record, status, outcome, path="/ask"):
        self.assertEqual(record["http_status"], status)
        self.assertEqual(record["outcome"], outcome)
        self.assertEqual(record["path"], path)
        self.assertTrue(record["request_id"])
        self.assertIsNotNone(datetime.fromisoformat(record["timestamp"]))
        self.assertGreaterEqual(record["duration_ms"], 0)

    @patch("serve.log_request")
    @patch("app.ask_pipeline")
    def test_answered_request_logs_sources_and_distance(self, mock_pipeline, mock_log):
        question = "Is the housing lottery random?"
        mock_pipeline.return_value = {
            "answer": "Yes, according to the guide.",
            "refused": False,
            "sources": ["housing.md", "lottery.md"],
            "best_distance": 0.234567,
            "threshold": 0.5,
        }

        response = self.client.post("/ask", json={"question": question})
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.get_json()["refused"])
        mock_pipeline.assert_called_once()
        mock_log.assert_called_once()

        record = mock_log.call_args.args[0]
        self.assert_common_fields(record, 200, "answered")
        self.assertEqual(record["method"], "POST")
        self.assertEqual(record["question_length"], len(question))
        self.assertEqual(record["n_sources"], 2)
        self.assertEqual(record["best_distance"], 0.2346)
        self.assertIsNone(record["error_type"])
        # input, output and cost fields
        self.assertEqual(record["question"], question)
        self.assertEqual(record["answer"], "Yes, according to the guide.")
        self.assertEqual(record["sources"], ["housing.md", "lottery.md"])
        self.assertEqual(record["prompt_tokens"], 0)  # pipeline is mocked: no Gemini call
        self.assertEqual(record["output_tokens"], 0)
        self.assertFalse(record["cache_hit"])

    @patch("serve.log_request")
    @patch("app.ask_pipeline")
    def test_refusal_is_logged_not_treated_as_error(self, mock_pipeline, mock_log):
        mock_pipeline.return_value = {
            "answer": "I cannot answer that from the guide.",
            "refused": True,
            "sources": [],
            "best_distance": 0.876543,
            "threshold": 0.5,
        }

        response = self.client.post("/ask", json={"question": "Unrelated topic?"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.get_json()["refused"])
        record = mock_log.call_args.args[0]
        self.assert_common_fields(record, 200, "refused")
        self.assertEqual(record["n_sources"], 0)
        self.assertEqual(record["best_distance"], 0.8765)
        self.assertIsNone(record["error_type"])

    @patch("serve.log_request")
    @patch("app.ask_pipeline")
    def test_missing_question_is_bad_request(self, mock_pipeline, mock_log):
        response = self.client.post("/ask", json={})
        self.assertEqual(response.status_code, 400)
        mock_pipeline.assert_not_called()

        record = mock_log.call_args.args[0]
        self.assert_common_fields(record, 400, "bad_request")
        self.assertEqual(record["question_length"], 0)
        self.assertIsNone(record["n_sources"])
        self.assertIsNone(record["best_distance"])
        self.assertIsNone(record["error_type"])

    @patch("serve.log_request")
    @patch("app.ask_pipeline", side_effect=RuntimeError("test failure"))
    def test_pipeline_exception_is_logged(self, mock_pipeline, mock_log):
        question = "What is the application deadline?"
        response = self.client.post("/ask", json={"question": question})
        self.assertEqual(response.status_code, 500)

        record = mock_log.call_args.args[0]
        self.assert_common_fields(record, 500, "error")
        self.assertEqual(record["question_length"], len(question))
        self.assertEqual(record["error_type"], "RuntimeError")
        self.assertIsNone(record["n_sources"])
        self.assertIsNone(record["best_distance"])

    def test_health_check_is_logged(self):
        fake_store = ModuleType("store")
        fake_store.index_exists = lambda corpus: True

        with (
            patch.dict(sys.modules, {"store": fake_store}),
            patch("serve.log_request") as mock_log,
        ):
            client = app.test_client()
            response = client.get("/health")

        self.assertEqual(response.status_code, 200)

        payload = response.get_json()
        self.assertEqual(payload["status"], "ok")
        self.assertTrue(payload["index_ready"])

        mock_log.assert_called_once()
        record = mock_log.call_args.args[0]

        self.assertEqual(record["method"], "GET")
        self.assertEqual(record["path"], "/health")
        self.assertEqual(record["http_status"], 200)
        self.assertEqual(record["outcome"], "completed")
        self.assertIsNone(record["question_length"])
        self.assertIsNone(record["n_sources"])
        self.assertIsNone(record["best_distance"])
        self.assertGreaterEqual(record["duration_ms"], 0)



if __name__ == "__main__":
    unittest.main()
