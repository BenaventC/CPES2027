"""Regression checks for R05 annotation safety and export contracts."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import pandas as pd
import requests

import R05_political_references_mistral_job as job


class AnnotationTests(unittest.TestCase):
    """Check that invalid output and unavailable servers remain explicit failures."""

    def test_valid_reference_and_empty_list(self):
        reference = {
            "type": "figure_politique", "mention": "Macron",
            "reference": "Emmanuel Macron", "extrait": "Macron",
        }
        self.assertEqual(job.parse_references_response(json.dumps([reference]), "Macron"), [reference])
        self.assertEqual(job.parse_references_response("```json\n[]\n```", "Macron"), [])

    def test_missing_evidence_is_rejected(self):
        response = [{
            "type": "figure_politique", "mention": "Macron",
            "reference": "Emmanuel Macron", "extrait": "Macron",
        }]
        with self.assertRaisesRegex(ValueError, "not present"):
            job.parse_references_response(json.dumps(response), "Un texte sans nom politique")

    @patch("requests.post", side_effect=requests.ConnectionError("Connection refused"))
    def test_server_loss_aborts_corpus(self, post):
        frame = pd.DataFrame([{"doc_id": 1, "lyrics": "Macron"}])
        with self.assertRaises(job.EndpointUnavailableError):
            job.annotate_corpus(frame, "http://127.0.0.1:8015")
        self.assertEqual(post.call_count, 1)

    @patch("requests.post")
    def test_truncated_response_is_rejected(self, post):
        response = Mock()
        response.json.return_value = {
            "choices": [{"finish_reason": "length", "message": {"content": "[]"}}],
        }
        post.return_value = response
        with self.assertRaisesRegex(job.AnnotationError, "truncated"):
            job.annotate_song("Macron", "http://127.0.0.1:8015", job.MODEL_NAME, 10, 0)

    @patch("requests.post")
    def test_validation_failure_is_recorded_per_song(self, post):
        response = Mock()
        response.json.return_value = {"choices": [{"message": {"content": "not JSON"}}]}
        post.return_value = response
        rows = job.annotate_corpus(
            pd.DataFrame([{"doc_id": 1, "lyrics": "Macron"}]),
            "http://127.0.0.1:8015", max_retries=0,
        )
        self.assertEqual(rows[0]["annotation_status"], "failed")
        self.assertTrue(rows[0]["annotation_error"])

    def test_exports_and_performance(self):
        rows = [{
            "doc_id": 1, "artist": "A", "title": "T", "year": 2020,
            "references": [], "annotation_status": "success", "annotation_error": None,
        }]
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            json_path, csv_path, errors_path = job.export_results(rows, output, "fixture")
            metrics_path = job.export_annotation_metrics(rows, output, "fixture", 2.0)
            self.assertEqual(len(json.loads(json_path.read_text())), 1)
            self.assertTrue(pd.read_csv(csv_path).empty)
            self.assertTrue(pd.read_csv(errors_path).empty)
            self.assertEqual(pd.read_csv(metrics_path).iloc[0]["songs_per_second"], 0.5)

    def test_sample_has_exact_size_and_stable_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "corpus.csv"
            pd.DataFrame({
                "doc_id": range(120), "lyrics": ["un texte de dix mots pour tester le filtre ici"] * 120,
            }).to_csv(path, index=False)
            first, label = job.load_corpus(path, "test", 0.01, 42, 10, 4000, sample_size=100)
            second, _ = job.load_corpus(path, "test", 0.01, 42, 10, 4000, sample_size=100)
            self.assertEqual(len(first), 100)
            self.assertEqual(first.doc_id.tolist(), second.doc_id.tolist())
            self.assertEqual(label, "100songs_10to4000w")

    def test_person_guard_distinguishes_given_names(self):
        marine = job._person_name_tokens("Marine Le Pen")
        jean_marie = job._person_name_tokens("Jean-Marie Le Pen")
        self.assertFalse(marine <= jean_marie or jean_marie <= marine)
        self.assertEqual(job._person_name_tokens("Président Macron"), {"macron"})

    def test_empty_canonical_table_preserves_schema(self):
        frame = pd.DataFrame(columns=["type", "reference"])
        enriched, mapping, metrics = job.canonicalize_references(frame)
        self.assertIn("reference_canon", enriched.columns)
        self.assertTrue(enriched.empty)
        self.assertTrue(mapping.empty)
        self.assertEqual(metrics["label_count"], 0)

    def test_canonical_input_validation(self):
        frame = pd.DataFrame([{"type": "figure_politique", "reference": "Macron"}])
        with self.assertRaises(ValueError):
            job.canonicalize_references(frame, similarity_threshold=1.1)
        with self.assertRaises(ValueError):
            job.canonicalize_references(frame, embedding_batch_size=0)
        invalid = frame.assign(reference="")
        with self.assertRaisesRegex(ValueError, "non-empty"):
            job.canonicalize_references(invalid)


if __name__ == "__main__":
    unittest.main()
