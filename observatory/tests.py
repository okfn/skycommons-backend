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
        # no key-order assertion: the source files themselves are not
        # internally consistent about it (e.g. active/iso_code position
        # varies between country files) and JSON consumers don't rely on it

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


@unittest.skipUnless(HAVE_SOURCE, f"static build not found at {DEFAULT_SOURCE}")
class ObservatoryApiTests(TestCase):
    """Smoke tests for the plain DRF API at /api/ (imported site data)."""

    @classmethod
    def setUpTestData(cls):
        call_command("import_site_data", verbosity=0)

    def test_country_list(self):
        data = self.client.get("/api/countries/").json()
        self.assertEqual(data["count"], 6)
        slugs = {c["slug"] for c in data["results"]}
        self.assertIn("brazil", slugs)

    def test_country_detail_nested(self):
        data = self.client.get("/api/countries/brazil/").json()
        self.assertEqual(data["name"], "Brazil")
        self.assertEqual(len(data["research_dimensions"]), 5)
        by_name = {r["name"]: r for r in data["research_dimensions"]}
        self.assertEqual(len(by_name["Competition"]["indicators"]), 2)
        self.assertEqual(by_name["Accountability"]["indicators"], [])
        self.assertGreater(len(data["timeline_entries"]), 0)
        self.assertEqual(data["risk"], "high")

    def test_section_detail(self):
        data = self.client.get("/api/sections/header/").json()
        self.assertEqual(data["title"], "Who controls satellite internet?")
        self.assertEqual(len(data["ctas"]), 1)

    def test_map_country_names(self):
        data = self.client.get("/api/map-country-names/").json()
        self.assertEqual(len(data), 176)

    def test_api_is_read_only(self):
        response = self.client.post("/api/countries/", {})
        self.assertEqual(response.status_code, 405)


class FixtureTests(TestCase):
    """The bundled fixture must stay loadable into a fresh database
    (it is the prod bootstrap path, see README)."""

    def test_fixture_loads(self):
        call_command("loaddata", "observatory", verbosity=0)
        from .models import ContentSection, Country, MapCountryName

        self.assertEqual(Country.objects.count(), 6)
        self.assertEqual(ContentSection.objects.count(), 6)
        self.assertEqual(MapCountryName.objects.count(), 176)
        brazil = Country.objects.get(slug="brazil")
        self.assertEqual(brazil.research_dimensions.count(), 5)


class WagtailApiTests(TestCase):
    """The standard Wagtail API v2 endpoints are mounted at /api/v2/."""

    def test_pages_endpoint(self):
        data = self.client.get("/api/v2/pages/").json()
        self.assertIn("meta", data)

    def test_images_and_documents_endpoints(self):
        for name in ("images", "documents"):
            data = self.client.get(f"/api/v2/{name}/").json()
            self.assertEqual(data["meta"]["total_count"], 0, name)
