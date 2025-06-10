from rest_framework import routers
from .views import RecipesViewSet, IngredientViewSet


router = routers.DefaultRouter()
router.register('/recipes', RecipesViewSet)
router.register('/ingredients', IngredientViewSet)
urlpatterns = router.urls
