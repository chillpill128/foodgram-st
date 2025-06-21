from djoser.urls.authtoken import urlpatterns as djoser_authtoken_urlpatterns
from rest_framework.routers import DefaultRouter

from .views import (
    RecipesViewSet, IngredientViewSet, UsersViewSet
)


router = DefaultRouter()

router.register('recipes', RecipesViewSet, basename='recipe')
router.register('ingredients', IngredientViewSet)
router.register('users', UsersViewSet, basename='user')


urlpatterns = router.urls
urlpatterns += djoser_authtoken_urlpatterns
