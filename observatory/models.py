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


class TimelineCategory(models.TextChoices):
    CONTACT = "contact"
    LICENSING = "licensing"
    AUTHORIZATION = "authorization"
    LAUNCH = "launch"
    OTHER = "other"


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
    active = models.BooleanField(
        default=True, help_text="Shown as active on the frontend."
    )
    iso_code = models.CharField(max_length=2, help_text="ISO 3166-1 alpha-2 (e.g. BR).")
    region = models.CharField(max_length=50)
    report_date = models.CharField(
        max_length=50, help_text="Displayed as-is (e.g. 'March 2026')."
    )
    risk = models.CharField(max_length=10, choices=RiskLevel.choices)
    providers_authorized = models.PositiveIntegerField()
    providers_operational = models.PositiveIntegerField()
    population = models.CharField(
        max_length=50, help_text="Displayed as-is (e.g. '213.7 million')."
    )

    card_title = models.CharField(max_length=255)
    card_blurb = models.TextField()
    header_info = models.TextField(
        help_text="One-line stats shown under the country header."
    )
    key_finding = models.TextField()
    summary = models.TextField()
    primary_driver = models.CharField(
        max_length=100, help_text="Short label (e.g. 'Executive Lobbying')."
    )

    panels = [
        MultiFieldPanel(
            [
                FieldRowPanel([FieldPanel("name"), FieldPanel("slug")]),
                FieldRowPanel([FieldPanel("iso_code"), FieldPanel("region")]),
                FieldRowPanel([FieldPanel("report_date"), FieldPanel("risk")]),
                FieldRowPanel(
                    [
                        FieldPanel("providers_authorized"),
                        FieldPanel("providers_operational"),
                    ]
                ),
                FieldRowPanel([FieldPanel("population"), FieldPanel("active")]),
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
                FieldPanel("primary_driver"),
            ],
            heading="Texts",
        ),
        InlinePanel("research_dimensions", heading="Research", label="Dimension"),
        InlinePanel("timeline_entries", heading="Timeline", label="Event"),
    ]

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "countries"

    def __str__(self):
        return self.name


class ResearchDimension(Orderable, ClusterableModel):
    """One scored research dimension of a country dossier (Competition,
    Governance, Accountability, Affordability, Accessibility)."""

    country = ParentalKey(
        Country, on_delete=models.CASCADE, related_name="research_dimensions"
    )
    name = models.CharField(max_length=100)
    risk = models.CharField(max_length=10, choices=RiskLevel.choices)
    text = models.TextField()

    panels = [
        FieldRowPanel([FieldPanel("name"), FieldPanel("risk")]),
        FieldPanel("text"),
        InlinePanel("indicators", label="Indicator"),
    ]

    def __str__(self):
        return f"{self.name} ({self.risk})"


class ResearchIndicator(Orderable):
    dimension = ParentalKey(
        ResearchDimension, on_delete=models.CASCADE, related_name="indicators"
    )
    name = models.CharField(
        blank=True, max_length=100, help_text="Optional label shown before the value."
    )
    info = models.TextField(
        help_text="Short value. Inline HTML (<br/>) is allowed for line breaks."
    )

    panels = [FieldPanel("name"), FieldPanel("info")]

    def __str__(self):
        return f"{self.name}: {self.info[:40]}"


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
