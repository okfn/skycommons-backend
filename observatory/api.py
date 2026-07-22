"""Plain DRF read-only API for the observatory models, mounted at /api/.

This is the "normal" API surface (default DRF conventions: router, nested
model serializers, browsable API). The Svelte compatibility layer in
urls.py/compat.py is a separate, additional surface with its own contract.
"""

from rest_framework import serializers, viewsets
from rest_framework.routers import DefaultRouter

from .models import (
    ContentSection,
    ContentSectionCTA,
    Country,
    MapCountryName,
    MarketProvider,
    PolicyLever,
    RedFlag,
    TimelineEntry,
)


class ContentSectionCTASerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentSectionCTA
        fields = ["title", "link"]


class ContentSectionSerializer(serializers.ModelSerializer):
    ctas = ContentSectionCTASerializer(many=True, read_only=True)

    class Meta:
        model = ContentSection
        fields = ["id", "slug", "section_label", "title", "subline", "text", "ctas"]


class TimelineEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = TimelineEntry
        fields = ["provider", "info", "date", "category"]


class MarketProviderSerializer(serializers.ModelSerializer):
    class Meta:
        model = MarketProvider
        fields = ["name", "local_entity", "status"]


class RedFlagSerializer(serializers.ModelSerializer):
    class Meta:
        model = RedFlag
        fields = ["severity", "text"]


class PolicyLeverSerializer(serializers.ModelSerializer):
    class Meta:
        model = PolicyLever
        fields = ["text"]


class CountrySerializer(serializers.ModelSerializer):
    timeline_entries = TimelineEntrySerializer(many=True, read_only=True)
    market_providers = MarketProviderSerializer(many=True, read_only=True)
    red_flags = RedFlagSerializer(many=True, read_only=True)
    policy_levers = PolicyLeverSerializer(many=True, read_only=True)

    class Meta:
        model = Country
        fields = "__all__"


class CountryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = [
            "id",
            "slug",
            "name",
            "iso_code",
            "region",
            "report_date",
            "risk_level",
        ]


class MapCountryNameSerializer(serializers.ModelSerializer):
    class Meta:
        model = MapCountryName
        fields = ["code", "name"]


class ContentSectionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ContentSection.objects.prefetch_related("ctas")
    serializer_class = ContentSectionSerializer
    lookup_field = "slug"


class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Country.objects.prefetch_related(
        "timeline_entries", "market_providers", "red_flags", "policy_levers"
    )
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return CountryListSerializer
        return CountrySerializer


class MapCountryNameViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MapCountryName.objects.all()
    serializer_class = MapCountryNameSerializer
    lookup_field = "code"
    pagination_class = None


router = DefaultRouter()
router.register("sections", ContentSectionViewSet)
router.register("countries", CountryViewSet)
router.register("map-country-names", MapCountryNameViewSet)
