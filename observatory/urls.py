"""Compatibility layer: same URLs and formats the SvelteKit frontend fetches
today as static files from sky-commons/docs. Keep these paths stable - the
goal is zero frontend changes beyond a base URL.
"""

from django.urls import path

from . import views

urlpatterns = [
    path("content/index.json", views.content_index, name="compat_content_index"),
    path("content/countries.json", views.content_countries, name="compat_content_countries"),
    path("data/country-<slug:slug>.json", views.country_detail, name="compat_country_detail"),
    path("data/countries-id-name.json", views.countries_id_name, name="compat_countries_id_name"),
]
