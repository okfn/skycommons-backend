"""Import the current static site JSON into the CMS models.

Reads content/*.json and data/*.json from the sky-commons static build
(../sky-commons/docs by default; override with --source or the
SKY_COMMONS_DOCS env var) and creates/updates the corresponding records.
Idempotent: re-running overwrites fields and recreates child rows, so it is
safe as a reset-to-site-state, but it will clobber CMS edits.
"""

import json
import os
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from observatory.compat import INDEX_SECTION_SLUGS, OBSERVATIONS_SLUG
from observatory.models import (
    ContentSection,
    ContentSectionCTA,
    Country,
    MapCountryName,
    ResearchDimension,
    ResearchIndicator,
    TimelineEntry,
)

DEFAULT_SOURCE = Path(
    os.environ.get(
        "SKY_COMMONS_DOCS", Path(settings.BASE_DIR).parent / "sky-commons" / "docs"
    )
)


class Command(BaseCommand):
    help = "Import content and country data from the sky-commons static build"

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            type=Path,
            default=DEFAULT_SOURCE,
            help=f"Path to the static build (default: {DEFAULT_SOURCE})",
        )

    def handle(self, *args, source, **options):
        if not source.is_dir():
            raise CommandError(f"Source directory not found: {source}")

        with transaction.atomic():
            self.import_sections(source)
            self.import_countries(source)
            self.import_map_names(source)

    def load(self, source, relpath):
        with open(source / relpath, encoding="utf-8") as f:
            return json.load(f)

    def import_sections(self, source):
        index = self.load(source, "content/index.json")
        observations = self.load(source, "content/countries.json")
        unknown = set(index) - set(INDEX_SECTION_SLUGS)
        if unknown:
            raise CommandError(f"Unexpected sections in content/index.json: {unknown}")

        for slug, data in list(index.items()) + [(OBSERVATIONS_SLUG, observations)]:
            section, _ = ContentSection.objects.update_or_create(
                slug=slug,
                defaults={
                    "section_label": data.get("section", ""),
                    "title": data["title"],
                    "subline": data.get("subline", ""),
                    "text": data.get("text", ""),
                },
            )
            ctas = data.get("ctas") or ([data["cta"]] if "cta" in data else [])
            section.ctas.all().delete()
            for i, cta in enumerate(ctas):
                ContentSectionCTA.objects.create(
                    section=section, sort_order=i, title=cta["title"], link=cta["link"]
                )
            self.stdout.write(f"section {slug}: ok ({len(ctas)} cta)")

    def import_countries(self, source):
        for path in sorted((source / "data").glob("country-*.json")):
            try:
                d = self.load(source, f"data/{path.name}")
                country, _ = Country.objects.update_or_create(
                    slug=d["id"],
                    defaults={
                        "name": d["name"],
                        "active": d["active"],
                        "iso_code": d["iso_code"],
                        "region": d["region"],
                        "report_date": d["report_date"],
                        "risk": d["risk"],
                        "providers_authorized": d["providers"]["authorized"],
                        "providers_operational": d["providers"]["operational"],
                        "population": d["population"],
                        "card_title": d["card_title"],
                        "card_blurb": d["card_blurb"],
                        "header_info": d["header_info"],
                        "key_finding": d["key_finding"],
                        "summary": d["summary"],
                        "primary_driver": d["primary_driver"],
                    },
                )
                country.research_dimensions.all().delete()
                for i, r in enumerate(d["research"]):
                    dimension = ResearchDimension.objects.create(
                        country=country,
                        sort_order=i,
                        name=r["name"],
                        risk=r["risk"],
                        text=r["text"],
                    )
                    for j, ind in enumerate(r.get("indicators", [])):
                        ResearchIndicator.objects.create(
                            dimension=dimension,
                            sort_order=j,
                            name=ind.get("name", ""),
                            info=ind["info"],
                        )
                country.timeline_entries.all().delete()
                for i, t in enumerate(d["timeline"]):
                    TimelineEntry.objects.create(
                        country=country,
                        sort_order=i,
                        provider=t["provider"],
                        info=t["info"],
                        date=t["date"],
                        category=t["category"],
                    )
            except KeyError as e:
                raise CommandError(
                    f"{path.name}: missing key {e} - the file format may have "
                    "changed; update the models/importer to match the current "
                    "frontend data schema."
                )
            self.stdout.write(
                f"country {d['id']}: ok ({len(d['research'])} research, "
                f"{len(d['timeline'])} timeline)"
            )

    def import_map_names(self, source):
        names = self.load(source, "data/countries-id-name.json")
        for i, (code, name) in enumerate(names.items()):
            MapCountryName.objects.update_or_create(
                code=code, defaults={"sort_order": i, "name": name}
            )
        MapCountryName.objects.exclude(code__in=names).delete()
        self.stdout.write(f"map names: ok ({len(names)})")
