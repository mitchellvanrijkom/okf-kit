"""Unit tests for okf-kit. Standard library only: python3 -m unittest -v."""
import io
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import okfkit  # noqa: E402


def make_kb(root: Path):
    (root / "concepts").mkdir(parents=True)
    (root / "entities").mkdir()
    (root / "concepts" / "idempotency.md").write_text(
        "---\ntype: Concept\ntitle: Idempotency\ndescription: Safe to repeat.\ntags: [reliability, retries]\n---\n"
        "# Idempotency\nSee [retries](/concepts/retries.md).\n", encoding="utf-8")
    (root / "concepts" / "retries.md").write_text(
        "---\ntype: Concept\ntitle: Retries\ndescription: Re-attempt on failure.\ntags: [reliability, retries]\n---\n"
        "# Retries\nWorks with [idempotency](/concepts/idempotency.md). Missing: [x](/concepts/nope.md).\n", encoding="utf-8")
    (root / "entities" / "token-bucket.md").write_text(
        "---\ntype: Reference\ntitle: Token Bucket\ndescription: Rate-limit algorithm.\ntags: [throughput]\n---\n"
        "# Token Bucket\nA `[fake](/not/a/link.md)` in inline code and a fenced block:\n```\n[also](/nope.md)\n```\n",
        encoding="utf-8")
    (root / "log.md").write_text("# Log\n", encoding="utf-8")


class TestParse(unittest.TestCase):
    def test_valid(self):
        fm, body, ok = okfkit.parse("---\ntype: X\ntitle: T\n---\nhello")
        self.assertTrue(ok)
        self.assertEqual(fm["type"], "X")
        self.assertEqual(body, "hello")

    def test_unclosed_is_not_ok(self):
        fm, body, ok = okfkit.parse("---\ntype: X\nno closing fence")
        self.assertFalse(ok)

    def test_no_frontmatter(self):
        fm, body, ok = okfkit.parse("just text")
        self.assertTrue(ok)
        self.assertEqual(fm, {})

    def test_list_tags(self):
        fm, _, _ = okfkit.parse("---\ntags: [a, b, c]\ntype: X\n---\n")
        self.assertEqual(fm["tags"], ["a", "b", "c"])

    def test_nested_yaml(self):
        # the naive parser could not do this; PyYAML can
        fm, _, ok = okfkit.parse("---\ntype: X\nmeta:\n  owner: team\n  ids: [1, 2]\n---\n")
        self.assertTrue(ok)
        self.assertEqual(fm["meta"], {"owner": "team", "ids": [1, 2]})

    def test_malformed_yaml_is_not_ok(self):
        fm, _, ok = okfkit.parse("---\ntype: [a, b\n---\nbody\n")  # unclosed flow sequence
        self.assertFalse(ok)


class TestIsEmpty(unittest.TestCase):
    def test_empty_values(self):
        for v in (None, "", "   ", [], {}):
            self.assertTrue(okfkit.is_empty(v), v)

    def test_present_values(self):
        for v in ("x", "0", 0, False, ["a"]):
            self.assertFalse(okfkit.is_empty(v), v)


class TestLinks(unittest.TestCase):
    def test_ignores_code(self):
        body = "real [a](/x.md) then `[b](/y.md)` and\n```\n[c](/z.md)\n```\n"
        links = okfkit.outgoing_links(body)
        self.assertEqual(links, ["/x.md"])


class TestCommands(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.kb = Path(self.tmp.name) / "kb"
        make_kb(self.kb)

    def tearDown(self):
        self.tmp.cleanup()

    def run_cmd(self, fn, **kw):
        kw.setdefault("kb", str(self.kb))
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = fn(SimpleNamespace(**kw))
        return rc, buf.getvalue()

    def test_index_generates_files(self):
        rc, _ = self.run_cmd(okfkit.cmd_index)
        self.assertEqual(rc, 0)
        root_index = (self.kb / "index.md").read_text()
        self.assertIn('okf_version: "0.1"', root_index)
        self.assertTrue((self.kb / "concepts" / "index.md").exists())
        self.assertIn("Idempotency", (self.kb / "concepts" / "index.md").read_text())

    def test_lint_valid_is_conformant(self):
        rc, out = self.run_cmd(okfkit.cmd_lint, max_soft=50)
        self.assertEqual(rc, 0)
        self.assertIn("conformant", out)

    def test_lint_missing_type_is_hard_error(self):
        (self.kb / "concepts" / "idempotency.md").write_text(
            "---\ntitle: No Type\n---\nbody\n", encoding="utf-8")
        rc, out = self.run_cmd(okfkit.cmd_lint, max_soft=50)
        self.assertEqual(rc, 1)
        self.assertIn("type", out)
        self.assertIn("non-conformant", out)

    def test_lint_broken_link_is_soft(self):
        rc, out = self.run_cmd(okfkit.cmd_lint, max_soft=50)
        self.assertEqual(rc, 0)  # broken link must not fail the build
        self.assertIn("broken link", out)

    def test_link_is_idempotent(self):
        self.run_cmd(okfkit.cmd_link, top=5)
        self.run_cmd(okfkit.cmd_link, top=5)
        body = (self.kb / "concepts" / "idempotency.md").read_text()
        self.assertEqual(body.count("## Related"), 1)

    def test_link_adds_mutual_related(self):
        self.run_cmd(okfkit.cmd_link, top=5)
        body = (self.kb / "concepts" / "idempotency.md").read_text()
        self.assertIn("## Related", body)
        self.assertIn("Retries", body)  # shares tags reliability+retries

    def test_navigate_runs(self):
        rc, out = self.run_cmd(okfkit.cmd_navigate, query="how to retry safely")
        self.assertEqual(rc, 0)
        self.assertIn("STAP", out)

    def test_structure_writes_okf(self):
        # mock the LLM: no network, no key needed
        raw = self.kb.parent / "raw"
        raw.mkdir()
        (raw / "note.md").write_text("meeting braindump: idempotency matters for retries\n", encoding="utf-8")
        canned = '[{"type":"Concept","title":"Idempotency","description":"Safe to repeat.","tags":["reliability"],"body":"# Idempotency\\nBody."}]'
        orig = okfkit._llm_complete
        okfkit._llm_complete = lambda *a, **k: canned  # no CLI / no key in the test
        try:
            rc, _ = self.run_cmd(okfkit.cmd_structure, raw=str(raw), model=None, provider="claude")
        finally:
            okfkit._llm_complete = orig
        self.assertEqual(rc, 0)
        page = self.kb / "concepts" / "idempotency.md"
        self.assertTrue(page.exists())
        fm, _, ok = okfkit.parse(page.read_text())
        self.assertTrue(ok)
        self.assertEqual(fm["type"], "Concept")

    @unittest.skipUnless(__import__("shutil").which("okflint"), "okflint not installed")
    def test_validate_runs_okflint(self):
        rc, out = self.run_cmd(okfkit.cmd_validate)
        self.assertEqual(rc, 0)
        self.assertIn("okflint", out)


if __name__ == "__main__":
    unittest.main()
