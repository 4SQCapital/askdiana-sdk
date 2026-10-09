import os
import re
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path

from askdiana.cli import cmd_init
from askdiana.erp.pack import load_pack

SDK_ROOT = Path(__file__).resolve().parents[2]
PLACEHOLDER = re.compile(r"__(NAME|SLUG|PACK|COMPONENT|COLOR|TGZ)__")


def init(workdir: str, name: str, color: str | None = "#13B5EA") -> Path:
    cwd = os.getcwd()
    os.chdir(workdir)
    try:
        with redirect_stdout(StringIO()):
            cmd_init(Namespace(name=name, ui=None, erp=True, color=color))
    finally:
        os.chdir(cwd)
    return Path(workdir) / name


class InitErpTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.project = init(self._tmp.name, "acme-books")

    def test_files_are_created_with_names_filled_in(self):
        for rel in ("app.py", "manifest.json", ".env.example", ".gitignore", "demo_data.py",
                    "pack/acme_books.yaml", "tests/test_pack.py", "views/index.tsx", "package.json"):
            self.assertTrue((self.project / rel).is_file(), rel)
        for path in self.project.rglob("*"):
            if path.is_file() and path.suffix != ".tgz":
                self.assertIsNone(PLACEHOLDER.search(path.read_text(encoding="utf-8")), path)
        self.assertIn('BRAND_COLOR = "#13B5EA"', (self.project / "views/const/colors.ts").read_text(encoding="utf-8"))
        self.assertTrue((self.project / "views/features/dashboard/DashboardView.tsx").is_file())

    def test_starter_pack_is_valid(self):
        pack = load_pack(str(self.project / "pack" / "acme_books.yaml"))
        self.assertEqual((pack.id, pack.label), ("acme_books", "acme-books"))

    def test_starter_tests_pass(self):
        env = {**os.environ, "PYTHONPATH": str(SDK_ROOT)}
        result = subprocess.run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."],
                                cwd=self.project, env=env, capture_output=True, text=True, timeout=120)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_bad_colour_is_refused(self):
        with self.assertRaises(SystemExit), redirect_stdout(StringIO()):
            init(self._tmp.name, "other", color="blue")
        self.assertFalse((Path(self._tmp.name) / "other" / "app.py").exists())


if __name__ == "__main__":
    unittest.main()
