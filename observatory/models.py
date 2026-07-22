"""Editorial content and country dossiers for the SkyCommons Observatory.

The field structure mirrors the JSON files the SvelteKit frontend consumes
(sky-commons/docs/content/*.json and docs/data/country-*.json). The compat
views in views.py serialize these models back into those exact shapes, so
field additions/renames here must stay coordinated with that contract.
"""

from django.db import models
from modelcluster.fields import ParentalKey
from modelcluster.models import ClusterableModel
from wagtail.admin.panels import FieldPanel, FieldRowPanel, InlinePanel, MultiFieldPanel
from wagtail.models import Orderable
from wagtail.snippets.models import register_snippet


class RiskLevel(models.TextChoices):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class Severity(models.TextChoices):
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ProviderStatus(models.TextChoices):
    PROSPECTIVE = "prospective"
    AUTHORIZED = "authorized"
    OPERATIONAL = "operational"


class TimelineCategory(models.TextChoices):
    CONTACT = "contact"
    LICENSING = "licensing"
    AUTHORIZATION = "authorization"
    LAUNCH = "launch"


@register_snippet
class ContentSection(ClusterableModel):
    """One editorial section of the site (homepage sections, observations).

    Maps to the objects in content/index.json (keyed by slug) and to
    content/countries.json (slug "observations"). Empty optional fields are
    omitted from the serialized output, which is how the per-section shape
    differences (subline, section label, cta vs ctas) are reproduced.
    """

    slug = models.SlugField(
        unique=True,
        help_text="Key used by the frontend (header, introduction, countries, "
        "satellite, information, observations). Do not change without "
        "coordinating with the frontend.",
    )
    section_label = models.CharField(
        blank=True,
        max_length=255,
        help_text="Small label above the title (JSON field 'section').",
    )
    title = models.CharField(max_length=255)
    subline = models.TextField(blank=True)
    text = models.TextField(
        blank=True,
        help_text="Prose. Inline HTML (links, <br/>) is allowed and rendered "
        "verbatim by the frontend.",
    )

    panels = [
        FieldPanel("slug"),
        FieldPanel("section_label"),
        FieldPanel("title"),
        FieldPanel("subline"),
        FieldPanel("text"),
        InlinePanel("ctas", label="Call-to-action buttons"),
    ]

    class Meta:
        ordering = ["slug"]
        verbose_name = "content section"

    def __str__(self):
        return f"{self.slug}: {self.title}"


class ContentSectionCTA(Orderable):
    section = ParentalKey(ContentSection, on_delete=models.CASCADE, related_name="ctas")
    title = models.CharField(max_length=255)
    link = models.CharField(
        max_length=255, help_text="Internal path (/satellites) or full URL."
    )

    panels = [FieldPanel("title"), FieldPanel("link")]

    def __str__(self):
        return f"{self.title} -> {self.link}"


@register_snippet
class Country(ClusterableModel):
    """A per-country research dossier (data/country-<slug>.json)."""

    slug = models.SlugField(
        unique=True, help_text="URL id used by the frontend (e.g. 'brazil')."
    )
    name = models.CharField(max_length=100)
    iso_code = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 (e.g. BR).")
    region = models.CharField(max_length=50)
    report_date = models.CharField(
        max_length=50, help_text="Displayed as-is (e.g. 'March 2026')."
    )
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices)
    providers_authorized = models.PositiveIntegerField()
    providers_operational = models.PositiveIntegerField()

    card_title = models.CharField(max_length=255)
    card_blurb = models.TextField()
    header_info = models.TextField(
        help_text="One-line stats shown under the country header."
    )
    key_finding = models.TextField()

    # comparative_analysis: four fixed dimensions, label + description each
    primary_driver_label = models.CharField(max_length=100)
    primary_driver_description = models.TextField()
    local_presence_label = models.CharField(max_length=100)
    local_presence_description = models.TextField()
    competition_label = models.CharField(max_length=100)
    competition_description = models.TextField()
    key_gap_label = models.CharField(max_length=100)
    key_gap_description = models.TextField()

    quote = models.TextField(blank=True, null=True)
    quote_attribution = models.CharField(blank=True, null=True, max_length=255)
    summary = models.TextField()

    # market_structure (providers list lives in MarketProvider)
    licensing_pathway = models.CharField(
        max_length=100, help_text="Short label (e.g. 'Fast-tracked', 'Emergency')."
    )
    licensing_pathway_note = models.TextField()
    uso_rollout = models.TextField(
        blank=True,
        help_text="Universal service obligation rollout status, if any "
        "(only present for some countries).",
    )

    # governance_scorecard
    qos_obligations = models.BooleanField(default=False)
    outage_reporting_required = models.BooleanField(default=False)
    local_data_landing_mandate = models.BooleanField(default=False)
    local_partner_requirement = models.BooleanField(default=False)
    foreign_ownership_exception = models.BooleanField(default=False)
    public_consultation = models.BooleanField(default=False)
    cybersecurity_audit = models.BooleanField(default=False)
    scorecard_summary_note = models.TextField()

    panels = [
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("name"), FieldPanel("slug")]),
                FieldRowPanel([FieldPanel("iso_code"), FieldPanel("region")]),
                FieldRowPanel([FieldPanel("report_date"), FieldPanel("risk_level")]),
                FieldRowPanel(
                    [
                        FieldPanel("providers_authorized"),
                        FieldPanel("providers_operational"),
                    ]
                ),
            ],
            heading="Identity",
        ),
        MultiFieldPanel(
            [
                FieldPanel("card_title"),
                FieldPanel("card_blurb"),
                FieldPanel("header_info"),
                FieldPanel("key_finding"),
                FieldPanel("summary"),
                FieldPanel("quote"),
                FieldPanel("quote_attribution"),
            ],
            heading="Texts",
        ),
        MultiFieldPanel(
            [
                FieldPanel("primary_driver_label"),
                FieldPanel("primary_driver_description"),
                FieldPanel("local_presence_label"),
                FieldPanel("local_presence_description"),
                FieldPanel("competition_label"),
                FieldPanel("competition_description"),
                FieldPanel("key_gap_label"),
                FieldPanel("key_gap_description"),
            ],
            heading="Comparative analysis",
        ),
        MultiFieldPanel(
            [
                FieldPanel("licensing_pathway"),
                FieldPanel("licensing_pathway_note"),
                FieldPanel("uso_rollout"),
                InlinePanel("market_providers", label="Providers"),
            ],
            heading="Market structure",
        ),
        MultiFieldPanel(
            [
                FieldPanel("qos_obligations"),
                FieldPanel("outage_reporting_required"),
                FieldPanel("local_data_landing_mandate"),
                FieldPanel("local_partner_requirement"),
                FieldPanel("foreign_ownership_exception"),
                FieldPanel("public_consultation"),
                FieldPanel("cybersecurity_audit"),
                FieldPanel("scorecard_summary_note"),
            ],
            heading="Governance scorecard",
        ),
        InlinePanel("timeline_entries", heading="Timeline", label="Event"),
        InlinePanel("red_flags", heading="Red flags", label="Red flag"),
        InlinePanel("policy_levers", heading="Policy levers", label="Policy lever"),
    ]

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "countries"

    def __str__(self):
        return self.name


class TimelineEntry(Orderable):
    country = ParentalKey(
        Country, on_delete=models.CASCADE, related_name="timeline_entries"
    )
    provider = models.CharField(max_length=100)
    info = models.CharField(max_length=255)
    date = models.CharField(max_length=10, help_text="YYYY-MM")
    category = models.CharField(max_length=20, choices=TimelineCategory.choices)

    panels = [
        FieldRowPanel([FieldPanel("date"), FieldPanel("provider")]),
        FieldRowPanel([FieldPanel("info"), FieldPanel("category")]),
    ]

    def __str__(self):
        return f"{self.date} {self.provider}: {self.info}"


class MarketProvider(Orderable):
    country = ParentalKey(
        Country, on_delete=models.CASCADE, related_name="market_providers"
    )
    name = models.CharField(max_length=100)
    local_entity = models.CharField(
        blank=True,
        null=True,
        max_length=255,
        help_text="Local subsidiary/partner, if any.",
    )
    status = models.CharField(max_length=20, choices=ProviderStatus.choices)

    panels = [
        FieldRowPanel([FieldPanel("name"), FieldPanel("status")]),
        FieldPanel("local_entity"),
    ]

    def __str__(self):
        return f"{self.name} ({self.status})"


class RedFlag(Orderable):
    country = ParentalKey(Country, on_delete=models.CASCADE, related_name="red_flags")
    severity = models.CharField(max_length=10, choices=Severity.choices)
    text = models.TextField()

    panels = [FieldPanel("severity"), FieldPanel("text")]

    def __str__(self):
        return f"[{self.severity}] {self.text[:60]}"


class PolicyLever(Orderable):
    country = ParentalKey(
        Country, on_delete=models.CASCADE, related_name="policy_levers"
    )
    text = models.TextField()

    panels = [FieldPanel("text")]

    def __str__(self):
        return self.text[:60]


@register_snippet
class MapCountryName(models.Model):
    """ISO code -> display name lookup for the world map
    (data/countries-id-name.json). Rarely edited; kept in the CMS so map
    labels can be corrected without a data pipeline run.
    """

    sort_order = models.PositiveIntegerField(
        default=0, help_text="Preserves the original file order."
    )
    code = models.CharField(unique=True, max_length=8)
    name = models.CharField(max_length=100)

    panels = [FieldPanel("code"), FieldPanel("name")]

    class Meta:
        ordering = ["sort_order", "code"]
        verbose_name = "map country name"

    def __str__(self):
        return f"{self.code}: {self.name}"
