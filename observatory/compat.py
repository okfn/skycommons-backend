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


def serialize_market_structure(country: Country) -> dict:
    data = {
        "providers": [
            {
                "name": p.name,
                "local_entity": p.local_entity or None,
                "status": p.status,
            }
            for p in country.market_providers.all()
        ],
        "licensing_pathway": country.licensing_pathway,
        "licensing_pathway_note": country.licensing_pathway_note,
    }
    if country.uso_rollout:
        data["uso_rollout"] = country.uso_rollout
    return data


def serialize_country(country: Country) -> dict:
    return {
        "id": country.slug,
        "name": country.name,
        "iso_code": country.iso_code,
        "region": country.region,
        "report_date": country.report_date,
        "risk_level": country.risk_level,
        "providers": {
            "authorized": country.providers_authorized,
            "operational": country.providers_operational,
        },
        "card_title": country.card_title,
        "card_blurb": country.card_blurb,
        "header_info": country.header_info,
        "key_finding": country.key_finding,
        "comparative_analysis": {
            "primary_driver": {
                "label": country.primary_driver_label,
                "description": country.primary_driver_description,
            },
            "local_presence": {
                "label": country.local_presence_label,
                "description": country.local_presence_description,
            },
            "competition": {
                "label": country.competition_label,
                "description": country.competition_description,
            },
            "key_gap": {
                "label": country.key_gap_label,
                "description": country.key_gap_description,
            },
        },
        "quote": country.quote or None,
        "quote_attribution": country.quote_attribution or None,
        "summary": country.summary,
        "timeline": [
            {
                "provider": t.provider,
                "info": t.info,
                "date": t.date,
                "category": t.category,
            }
            for t in country.timeline_entries.all()
        ],
        "market_structure": serialize_market_structure(country),
        "governance_scorecard": {
            "qos_obligations": country.qos_obligations,
            "outage_reporting_required": country.outage_reporting_required,
            "local_data_landing_mandate": country.local_data_landing_mandate,
            "local_partner_requirement": country.local_partner_requirement,
            "foreign_ownership_exception": country.foreign_ownership_exception,
            "public_consultation": country.public_consultation,
            "cybersecurity_audit": country.cybersecurity_audit,
            "summary_note": country.scorecard_summary_note,
        },
        "red_flags": [
            {"severity": r.severity, "text": r.text} for r in country.red_flags.all()
        ],
        "policy_levers": [lever.text for lever in country.policy_levers.all()],
    }
