import copy
import json
import pathlib
import tempfile
import unittest
from unittest.mock import patch

import sync_board
from preparation import project_preparation


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.record = {
            "schemaVersion": 1, "phase": "awaiting_review",
            "updatedAt": "2026-09-07T16:09:45+08:00", "sampleCommit": "a" * 40,
            "counts": {"parentDrafts": 6, "atomicDrafts": 16,
                       "detailedSamples": 2, "selfCheckGroups": 7},
            "events": [{"at": "2026-09-07T16:09:45+08:00",
                        "kind": "revision_submitted", "commit": "a" * 40}],
        }

    def test_private_extra_fields_never_published(self):
        self.record["body"] = "PRIVATE_SECRET"
        self.record["sampleUrl"] = "https://PRIVATE_SECRET.example"
        self.record["counts"]["private"] = "PRIVATE_SECRET"
        self.record["events"][0]["body"] = "PRIVATE_SECRET"
        result = project_preparation(self.record, "b" * 40)
        self.assertNotIn("PRIVATE_SECRET", json.dumps(result))
        self.assertEqual(result["phase"], "awaiting_review")
        self.assertEqual(result["counts"]["atomicDrafts"], 16)
        self.assertIn("/blob/" + "b" * 40, result["recordUrl"])

    def test_invalid_state_or_provenance_rejected(self):
        for key, value in [("phase", "DONE"), ("sampleCommit", "abc1234"),
                           ("updatedAt", "2026-09-07T16:09:45")]:
            with self.subTest(key=key), self.assertRaises(ValueError):
                record = copy.deepcopy(self.record)
                record[key] = value
                project_preparation(record, "b" * 40)

    def test_invalid_counts_rejected(self):
        for value in [-1, True, "16", 10001]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                record = copy.deepcopy(self.record)
                record["counts"]["atomicDrafts"] = value
                project_preparation(record, "b" * 40)

    def test_no_issues_does_not_grant_readiness_or_gate(self):
        plan = json.loads(sync_board.PLAN.read_text())
        board = sync_board.build_board(plan, {}, [], [], "a" * 40,
                                       "2026-09-07", "2026-09-07 16:09")
        board["preparation"] = project_preparation(self.record, "b" * 40)
        self.assertEqual(len(board["tasks"]), 48)
        self.assertEqual({t["status"] for t in board["tasks"]}, {"PLANNED"})
        self.assertFalse(any(sync_board.gate_eligibility(board).values()))

    def test_unassigned_issue_needs_explicit_ready_label(self):
        issue = {"state": "OPEN", "labels": [], "assignees": []}
        self.assertEqual(sync_board.decide_task(issue, None, {})[0], "TRIAGED")
        issue["labels"] = [{"name": "status:ready"}]
        self.assertEqual(sync_board.decide_task(issue, None, {})[0], "READY")

    def test_failed_private_fetch_keeps_existing_snapshot(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = pathlib.Path(tmp)
            (root / ".git").mkdir()
            board = root / "board.json"
            board.write_text("original snapshot")
            with patch.object(sync_board, "ROOT", root), \
                 patch.object(sync_board, "BOARD", board), \
                 patch.object(sync_board.sys, "argv", ["sync_board.py"]), \
                 patch.object(sync_board, "fetch_all", return_value=([], [], "a" * 40, "main")), \
                 patch.object(sync_board, "fetch_preparation", side_effect=RuntimeError("offline")), \
                 self.assertRaises(SystemExit) as result:
                sync_board.main()
            self.assertEqual(result.exception.code, 2)
            self.assertEqual(board.read_text(), "original snapshot")


if __name__ == "__main__":
    unittest.main()
