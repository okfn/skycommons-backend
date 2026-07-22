"""Contract tests: after importing the static site data, the compat views
must return JSON equal (modulo key order) to the original files in
sky-commons/docs. This is the guarantee that lets the frontend switch from
local files to the API with zero changes.

They are skipped automatically if the sky-commons checkout is not present
(e.g. in CI without the sibling repo).
"""

import json
import unittest

from django.core.management import call_command
from django.test import TestCase

from observatory.management.commands.import_site_data import DEFAULT_SOURCE

HAVE_SOURCE = DEFAULT_SOURCE.is_dir()


def load_original(relpath):
    with open(DEFAULT_SOURCE / relpath, encoding="utf-8") as f:
        return json.load(f)


@unittest.skipUnless(HAVE_SOURCE, f"static build not found at {DEFAULT_SOURCE}")
class CompatContractTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("import_site_data", verbosity=0)

    def fetch(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200, path)
        return response.json()

    def assert_matches_file(self, url, relpath):
        original = load_original(relpath)
        served = self.fetch(url)
        self.assertEqual(served, original, f"{url} differs from {relpath}")
        # dict equality ignores order, but the frontend build diffs are much
        # easier to review when key order also matches the original files
        self.assertEqual(
            list(served), list(original), f"{url}: top-level key order differs"
        )

    def test_content_index(self):
        self.assert_matches_file("/content/index.json", "content/index.json")

    def test_content_countries(self):
        self.assert_matches_file("/content/countries.json", "content/countries.json")

    def test_country_dossiers(self):
        for path in sorted((DEFAULT_SOURCE / "data").glob("country-*.json")):
            slug = path.stem.removeprefix("country-")
            self.assert_matches_file(f"/data/country-{slug}.json", f"data/{path.name}")

    def test_countries_id_name(self):
        self.assert_matches_file(
            "/data/countries-id-name.json", "data/countries-id-name.json"
        )

    def test_unknown_country_404(self):
        self.assertEqual(self.client.get("/data/country-nowhere.json").status_code, 404)
