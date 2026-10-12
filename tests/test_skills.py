"""Hermetic security and behavior tests for the pinned Agent Skills installer."""
import copy
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts import skills


def fixture():
    text = b"---\nname: sample-skill\ndescription: A fixture\n---\n\n# Sample\n\nOnly instructions.\n"
    reference = b"# Reference\n\nNever execute fetched code.\n"
    blocked = b"#!/bin/sh\nexit 0\n"
    blobs = {
        "skills/sample-skill/SKILL.md": text,
        "skills/sample-skill/reference/guide.md": reference,
        "skills/sample-skill/scripts/run.sh": blocked,
        "skills/sample-skill/scripts/data/huge-index.json": b"{}" * 500_000,
    }
    entries = [
        {"path": path, "type": "blob", "mode": "100644",
         "size": len(content), "sha": skills.blob_sha(content)}
        for path, content in blobs.items()
    ]
    entries[2]["mode"] = "100755"
    commit = "a" * 40
    catalog = {"version": 1, "profiles": {"core": ["sample-skill"]},
               "skills": [{"id": "sample-skill", "source": "example/skills",
                           "revision": commit, "directory": "skills/sample-skill",
                           "license": "MIT", "description": "Test skill"}]}
    def fetch(url, limit):
        if "/git/trees/" in url:
            return json.dumps({"tree": entries, "truncated": False}).encode()
        for path, value in blobs.items():
            if url.endswith("/" + path):
                assert len(value) <= limit
                return value
        raise AssertionError("Unexpected fetch: " + url)
    return catalog, fetch, blobs


class SkillCatalogTests(unittest.TestCase):
    def test_real_catalog(self):
        catalog = skills.load()
        self.assertGreaterEqual(len(catalog["skills"]), 15)
        self.assertTrue({"core", "web", "security", "writing", "authoring"} <= set(catalog["profiles"]))
        self.assertTrue({"impeccable", "design-taste-frontend", "web-design-guidelines",
                         "vercel-react-best-practices", "humanizer", "skill-creator"} <=
                        {x["id"] for x in catalog["skills"]})

    def test_selection_deduplicates_across_profiles_and_explicit_skills(self):
        catalog = skills.load()
        records = skills.selected(catalog, ["web", "core"], ["impeccable"])
        self.assertEqual(len(records), len({r["id"] for r in records}))

    def test_no_selection_or_unknown_profile(self):
        catalog = skills.load()
        with self.assertRaises(skills.SkillError):
            skills.selected(catalog)
        with self.assertRaisesRegex(skills.SkillError, "unknown profile"):
            skills.selected(catalog, ["everything"])

    def test_reject_duplicate_ids_and_invalid_pin(self):
        catalog, _, _ = fixture()
        bad = copy.deepcopy(catalog)
        bad["skills"][0]["revision"] = "main"
        with self.assertRaises(skills.SkillError):
            skills.validate(bad)
        bad = copy.deepcopy(catalog)
        bad["skills"].append(copy.deepcopy(bad["skills"][0]))
        with self.assertRaises(skills.SkillError):
            skills.validate(bad)

    def test_reject_unsafe_paths(self):
        for name in ("../x", "x/../y", "/etc/passwd", "x//y", "x\\y", "./x"):
            with self.subTest(name=name), self.assertRaises(skills.SkillError):
                skills.check_path(name)

    def test_reject_unclosed_frontmatter(self):
        with self.assertRaisesRegex(skills.SkillError, "unclosed"):
            skills.inspect_skill(b"---\nname: sample-skill\ndescription: valid\n", "sample-skill")

    def test_reject_missing_description(self):
        with self.assertRaisesRegex(skills.SkillError, "description"):
            skills.inspect_skill(b"---\nname: sample-skill\n---\nHi\n", "sample-skill")

    def test_reject_empty_body(self):
        with self.assertRaisesRegex(skills.SkillError, "empty skill"):
            skills.inspect_skill(b"---\nname: sample-skill\ndescription: valid\n---\n", "sample-skill")

    def test_reject_overlong_description(self):
        payload = ("---\nname: sample-skill\ndescription: " + "a"*1025 + "\n---\n# Instructions").encode()
        with self.assertRaisesRegex(skills.SkillError, "description length"):
            skills.inspect_skill(payload, "sample-skill")

    def test_multiline_frontmatter_description(self):
        skill = b"---\nname: sample-skill\ndescription: |\n  Writes a good\n  explanation.\n---\n# Do the thing"
        self.assertTrue(skills.inspect_skill(skill, "sample-skill"))

    def test_reject_mismatched_frontmatter(self):
        with self.assertRaises(skills.SkillError):
            skills.inspect_skill(b"---\nname: different\n---\n", "sample-skill")


class SkillInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.catalog, self.fetch, self.blobs = fixture()
        (self.root / "integrations").mkdir()
        (self.root / "integrations" / "skills.lock.json").write_text(json.dumps(self.catalog))

    def tearDown(self):
        self.temp.cleanup()

    def test_installer_uses_pins_and_never_fetches_executable(self):
        result = skills.install(self.catalog["skills"], self.root, self.fetch)
        self.assertEqual(result, ["sample-skill"])
        root = self.root / ".agents/skills/sample-skill"
        self.assertTrue((root / "SKILL.md").exists())
        self.assertTrue((root / "reference/guide.md").exists())
        self.assertFalse((root / "scripts/run.sh").exists())
        self.assertFalse((root / "scripts/data/huge-index.json").exists())
        self.assertEqual(skills.audit(self.root), ["sample-skill"])
        stamp = json.loads((root / ".open-ass-source.json").read_text())
        self.assertEqual(stamp["revision"], "a" * 40)

    def test_modified_content_rejected(self):
        skills.install(self.catalog["skills"], self.root, self.fetch)
        path = self.root / ".agents/skills/sample-skill/SKILL.md"
        path.write_text(path.read_text() + "unexpected")
        with self.assertRaisesRegex(skills.SkillError, "modified"):
            skills.audit(self.root)

    def test_untracked_payload_rejected(self):
        skills.install(self.catalog["skills"], self.root, self.fetch)
        (self.root / ".agents/skills/sample-skill/evil.sh").write_text("#!/bin/sh\n")
        with self.assertRaisesRegex(skills.SkillError, "untracked"):
            skills.audit(self.root)

    def test_catalog_version_change_rejected(self):
        skills.install(self.catalog["skills"], self.root, self.fetch)
        updated = copy.deepcopy(self.catalog)
        updated["skills"][0]["revision"] = "b" * 40
        (self.root / "integrations/skills.lock.json").write_text(json.dumps(updated))
        with self.assertRaisesRegex(skills.SkillError, "pinned catalog"):
            skills.audit(self.root)

    def test_partial_or_tampered_download_fails_without_install(self):
        def tampered(url, limit):
            if "/git/trees/" in url:
                return self.fetch(url, limit)
            return b"tampered!"
        with self.assertRaisesRegex(skills.SkillError, "blob verification"):
            skills.install(self.catalog["skills"], self.root, tampered)
        self.assertFalse((self.root / ".agents/skills/sample-skill").exists())

    def test_existing_unmanaged_skill_is_preserved(self):
        root = self.root / ".agents/skills/sample-skill"
        root.mkdir(parents=True)
        (root / "SKILL.md").write_text("my work")
        with self.assertRaisesRegex(skills.SkillError, "unmanaged"):
            skills.install(self.catalog["skills"], self.root, self.fetch)
        self.assertEqual((root / "SKILL.md").read_text(), "my work")

    def test_never_overwrites_installed_skill(self):
        skills.install(self.catalog["skills"], self.root, self.fetch)
        with self.assertRaisesRegex(skills.SkillError, "already installed"):
            skills.install(self.catalog["skills"], self.root, self.fetch)

    def test_symlink_upstream_is_excluded(self):
        entries = [
            {"path": "skills/sample-skill/SKILL.md", "type": "blob", "mode": "120000",
             "size": 10, "sha": "0"*40},
        ]
        def mocked(url, limit):
            return json.dumps({"tree": entries, "truncated": False}).encode()
        with self.assertRaisesRegex(skills.SkillError, "entrypoint missing"):
            skills.install(self.catalog["skills"], self.root, mocked)

    def test_reject_truncated_remote_tree(self):
        def mocked(url, limit):
            return json.dumps({"tree": [], "truncated": True}).encode()
        with self.assertRaisesRegex(skills.SkillError, "truncated"):
            skills.install(self.catalog["skills"], self.root, mocked)


if __name__ == "__main__":
    unittest.main()
