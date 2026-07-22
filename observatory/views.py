from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from . import compat
from .models import Country, MapCountryName


def content_index(request):
    return JsonResponse(compat.serialize_content_index())


def content_countries(request):
    return JsonResponse(compat.serialize_content_countries())


def country_detail(request, slug):
    country = get_object_or_404(
        Country.objects.prefetch_related(
            "research_dimensions__indicators", "timeline_entries"
        ),
        slug=slug,
    )
    return JsonResponse(compat.serialize_country(country))


def countries_id_name(request):
    return JsonResponse({c.code: c.name for c in MapCountryName.objects.all()})
