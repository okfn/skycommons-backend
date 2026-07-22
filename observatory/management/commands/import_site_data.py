"""Import the current static site JSON into the CMS models.

Reads content/*.json and data/*.json from the sky-commons static build
(../sky-commons/docs by default) and creates/updates the corresponding
records. Idempotent: re-running overwrites fields and recreates child rows,
so it is safe as a reset-to-site-state, but it will clobber CMS edits.
"""

import json
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
    MarketProvider,
    PolicyLever,
    RedFlag,
    TimelineEntry,
)

DEFAULT_SOURCE = Path(settings.BASE_DIR).parent / "sky-commons" / "docs"


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
            d = self.load(source, f"data/{path.name}")
            ca = d["comparative_analysis"]
            ms = d["market_structure"]
            gs = d["governance_scorecard"]
            country, _ = Country.objects.update_or_create(
                slug=d["id"],
                defaults={
                    "name": d["name"],
                    "iso_code": d["iso_code"],
                    "region": d["region"],
                    "report_date": d["report_date"],
                    "risk_level": d["risk_level"],
                    "providers_authorized": d["providers"]["authorized"],
                    "providers_operational": d["providers"]["operational"],
                    "card_title": d["card_title"],
                    "card_blurb": d["card_blurb"],
                    "header_info": d["header_info"],
                    "key_finding": d["key_finding"],
                    "primary_driver_label": ca["primary_driver"]["label"],
                    "primary_driver_description": ca["primary_driver"]["description"],
                    "local_presence_label": ca["local_presence"]["label"],
                    "local_presence_description": ca["local_presence"]["description"],
                    "competition_label": ca["competition"]["label"],
                    "competition_description": ca["competition"]["description"],
                    "key_gap_label": ca["key_gap"]["label"],
                    "key_gap_description": ca["key_gap"]["description"],
                    "quote": d["quote"],
                    "quote_attribution": d["quote_attribution"],
                    "summary": d["summary"],
                    "licensing_pathway": ms["licensing_pathway"],
                    "licensing_pathway_note": ms["licensing_pathway_note"],
                    "uso_rollout": ms.get("uso_rollout", ""),
                    "qos_obligations": gs["qos_obligations"],
                    "outage_reporting_required": gs["outage_reporting_required"],
                    "local_data_landing_mandate": gs["local_data_landing_mandate"],
                    "local_partner_requirement": gs["local_partner_requirement"],
                    "foreign_ownership_exception": gs["foreign_ownership_exception"],
                    "public_consultation": gs["public_consultation"],
                    "cybersecurity_audit": gs["cybersecurity_audit"],
                    "scorecard_summary_note": gs["summary_note"],
                },
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
            country.market_providers.all().delete()
            for i, p in enumerate(ms["providers"]):
                MarketProvider.objects.create(
                    country=country,
                    sort_order=i,
                    name=p["name"],
                    local_entity=p["local_entity"],
                    status=p["status"],
                )
            country.red_flags.all().delete()
            for i, r in enumerate(d["red_flags"]):
                RedFlag.objects.create(
                    country=country, sort_order=i, severity=r["severity"], text=r["text"]
                )
            country.policy_levers.all().delete()
            for i, text in enumerate(d["policy_levers"]):
                PolicyLever.objects.create(country=country, sort_order=i, text=text)
            self.stdout.write(
                f"country {d['id']}: ok ({len(d['timeline'])} timeline, "
                f"{len(ms['providers'])} providers, {len(d['red_flags'])} red flags)"
            )

    def import_map_names(self, source):
        names = self.load(source, "data/countries-id-name.json")
        for i, (code, name) in enumerate(names.items()):
            MapCountryName.objects.update_or_create(
                code=code, defaults={"sort_order": i, "name": name}
            )
        MapCountryName.objects.exclude(code__in=names).delete()
        self.stdout.write(f"map names: ok ({len(names)})")
