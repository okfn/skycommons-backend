"""Serializers for the frontend compatibility layer.

Each function reproduces, key for key and in the same order, the shape of one
of the JSON files the SvelteKit app consumes today from sky-commons/docs.
The contract tests in tests.py compare this output against those files.
"""

from .models import ContentSection, Country

# Section slugs composing content/index.json, in file order.
INDEX_SECTION_SLUGS = ["header", "introduction", "countries", "satellite", "information"]
# The one section serialized as content/countries.json.
OBSERVATIONS_SLUG = "observations"


def serialize_section(section: ContentSection) -> dict:
    data = {}
    if section.section_label:
        data["section"] = section.section_label
    data["title"] = section.title
    if section.subline:
        data["subline"] = section.subline
    data["text"] = section.text
    ctas = [{"title": c.title, "link": c.link} for c in section.ctas.all()]
    if ctas:
        # information carries a list ("ctas"); every other section a single
        # object ("cta") - the frontend expects exactly those keys.
        if section.slug == "information":
            data["ctas"] = ctas
        else:
            data["cta"] = ctas[0]
    return data


def serialize_content_index() -> dict:
    sections = ContentSection.objects.filter(slug__in=INDEX_SECTION_SLUGS).prefetch_related("ctas")
    by_slug = {s.slug: s for s in sections}
    return {
        slug: serialize_section(by_slug[slug])
        for slug in INDEX_SECTION_SLUGS
        if slug in by_slug
    }


def serialize_content_countries() -> dict:
    section = ContentSection.objects.prefetch_related("ctas").get(slug=OBSERVATIONS_SLUG)
    return serialize_section(section)


def serialize_research_dimension(dimension) -> dict:
    data = {"name": dimension.name, "risk": dimension.risk, "text": dimension.text}
    # optional keys are omitted entirely in the frontend files, never null:
    # an indicator's "name", and "indicators" itself when a dimension has none
    indicators = [
        ({"name": i.name, "info": i.info} if i.name else {"info": i.info})
        for i in dimension.indicators.all()
    ]
    if indicators:
        data["indicators"] = indicators
    return data


def serialize_country(country: Country) -> dict:
    return {
        "id": country.slug,
        "name": country.name,
        "active": country.active,
        "iso_code": country.iso_code,
        "region": country.region,
        "report_date": country.report_date,
        "risk": country.risk,
        "providers": {
            "authorized": country.providers_authorized,
            "operational": country.providers_operational,
        },
        "population": country.population,
        "card_title": country.card_title,
        "card_blurb": country.card_blurb,
        "header_info": country.header_info,
        "key_finding": country.key_finding,
        "summary": country.summary,
        "primary_driver": country.primary_driver,
        "research": [
            serialize_research_dimension(r) for r in country.research_dimensions.all()
        ],
        "timeline": [
            {
                "provider": t.provider,
                "info": t.info,
                "date": t.date,
                "category": t.category,
            }
            for t in country.timeline_entries.all()
        ],
    }
