from django.conf import settings
from django.db import models

from wagtail.models import Page


class HomePage(Page):
    def get_context(self, request):
        context = super().get_context(request)
        context["frontend_url"] = settings.FRONTEND_URL
        return context
