from django.urls import path
from django.conf import settings

from .views import short_link_redirect_view


urlpatterns = [
    path(f'{settings.RECIPE_SHORT_LINK_BASE_PATH}/<int:recipe_id>',
         short_link_redirect_view, name='recipe-short-link-redirect'),
]
