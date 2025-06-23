from django.urls import path
from django.conf import settings

from .views import short_link_view

_short_url = settings.RECIPE_SHORT_LINK_BASE_PATH.rstrip('/') + '/<str:short_code>'

urlpatterns = [
    path(_short_url, short_link_view),
]
